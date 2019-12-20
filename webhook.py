#!/usr/bin/env python

import json
import os
import time
from flask import Flask, request, abort
from plex import DecoraPlexHook
from datetime import datetime, timedelta

VERSION = 'v0.3'
DEBUG = True

app = Flask(__name__)


def is_time_to_run(start_time, end_time):
    """
    Check if the current time is within the run-time range.
    Args:
        start_time: in HH:MM format
        end_time: in HH:MM format

    Returns:
        True if current time is within the range.
        False if the current time is NOT within the range.
    """
    # If start/end are blank, assume true
    if start_time.upper() == 'ANY' or end_time.upper() == 'ANY':
        return True

    now_dt_obj = datetime.now()

    # Parse the time passed as date/time objects
    start_dt_obj = datetime.strptime(now_dt_obj.strftime("%Y%m%d") + ' ' + start_time, '%Y%m%d %H:%M')
    end_dt_obj = datetime.strptime(now_dt_obj.strftime("%Y%m%d") + ' ' + end_time, '%Y%m%d %H:%M')

    print('Current time: {:%H:%M:%S} - (Run Range: {:%H:%M} - {:%H:%M})'.format(now_dt_obj, start_dt_obj, end_dt_obj))

    if start_dt_obj <= end_dt_obj:
        return start_dt_obj <= now_dt_obj <= end_dt_obj
    else:  # past midnight e.g., 17:00-09:00 (5pm - 9am)
        return start_dt_obj <= now_dt_obj or now_dt_obj <= end_dt_obj


def calculate_ending_wait(duration, last_sec):
    # Determine duration in seconds
    duration_sec = duration / 1000
    a = timedelta(seconds=duration_sec)
    print('Duration Timecode: ' + str(a))

    # Determine duration mark subtracting requested last seconds
    mark_sec = duration_sec - last_sec
    a = timedelta(seconds=mark_sec)
    print('Mark Timecode: ' + str(a))

    # We know that scrobble is at 90% mark
    scrobble_sec = duration_sec * .9
    a = timedelta(seconds=scrobble_sec)
    print('Scrobble Timecode: ' + str(a))

    # Given the scrobble mark, now we know how much more time to wait since receiving the "media.scrobble" event.
    wait_time = mark_sec - scrobble_sec
    if wait_time < 0:
        wait_time = 0
    return wait_time


def log_action(log_str):
    dt_obj = datetime.now()
    timestamp = dt_obj.strftime("%d-%b-%Y (%H:%M:%S)")
    print('{} - {}'.format(timestamp, log_str))


@app.route('/webhook', methods=['POST'])
def webhook():
    # This object instantiates a Leviton Decora dimmer/switch control.
    # If you want to control other lights, you'll have to implement/use a different concrete
    # subclass of the PlexHook abstract class and change here.
    decora_api = DecoraPlexHook()

    if request.method == 'POST':
        plex_player = os.environ.get('PLEX_PLAYER')
        stop_action_delay = int(os.environ.get('PLEX_STOP_ACTION_DELAY'))
        play_action_delay = int(os.environ.get('PLEX_PLAY_ACTION_DELAY'))
        end_action_delay = int(os.environ.get('PLEX_END_ACTION_DELAY'))
        control_mode = os.environ.get('CONTROL_MODE').upper()
        time_to_run = is_time_to_run(os.environ.get('RUN_TIME_START'), os.environ.get('RUN_TIME_END'))

        # Get the payload from Plex's post.
        plex_dict = request.form.to_dict()
        payload = plex_dict['payload']
        payload = json.loads(payload)

        # Decipher the payload information
        event = payload['event']
        media_type = payload['Metadata']['type']
        local = payload['Player']['local']
        device = payload['Player']['title']
        media_title = payload['Metadata']['title']

        # Use this to calculate optional last # of minutes of a movie Or past the 'media.scrobble' 90% mark.
        duration = payload['Metadata'].get('duration', '')

        # Determine media type for future handling of various types.
        if media_type == 'clip':
            if 'preroll' in payload['Metadata'].get('guid', ''):
                media_type = 'pre-roll'
            elif 'trailer' in payload['Metadata'].get('subtype', ''):
                media_type = 'trailer'
            else:
                media_type = 'unknown'

        log_action('Media ({}): {} - {}'.format(media_type, media_title, event))

        # if DEBUG:
        #     print('Duration: ' + str(duration))
        #     # print(json.dumps(payload, indent=4, sort_keys=True))

        # Only perform actions for a particular player playing on the local network.
        if local and device == plex_player and time_to_run:
            # Reset delay markers, action invoked while previous request is sleeping.
            os.environ['PENDING_END'] = ''
            os.environ['PENDING_STOP'] = ''
            os.environ['PENDING_PLAY'] = ''

            # Basic Plex event detection (no trailers/pre-roll)
            if control_mode == 'BASIC':
                if event == 'media.play' or event == 'media.resume':
                    log_action('Action play_action() invoked (lights off).')
                    decora_api.play_action()  # Turn-off the lights

                if event == 'media.pause':
                    log_action('Action pause_action() invoked (dim lights).')
                    decora_api.pause_action()  # Dim the lights

                # This event is for when 90% of the movie is reached.
                if event == 'media.scrobble':
                    os.environ['PENDING_END'] = 'True'
                    time.sleep(end_action_delay)
                    # Check if we need to continue (i.e. another action happened while asleep)
                    if os.environ.get('PENDING_END', '') == 'True':
                        os.environ['PENDING_END'] = ''
                        log_action('Action end_action() invoked (dim lights).')
                        decora_api.end_action()  # Dim the lights

                if event == 'media.stop':
                    log_action('Action stop_action() invoked (lights on).')
                    decora_api.stop_action()  # Turn-on the lights

            # Advanced event detection (trailers AND pre-roll enabled)
            else:
                # This is an artificial detection of movie start since Plex doesn't send a new 'media.play' event
                # when trailers/pre-roll are enabled.
                if media_type == 'pre-roll' and event == 'media.stop':
                    log_action('Action play_action (pre-roll done, movie starting...) invoked (lights off).')
                    decora_api.play_action()  # Turn-off the lights
                # Detect media stop when skipping or when trailers transition automatically.
                elif event == 'media.stop':
                    # This delay is to prevent stop_action() from invoking in between trailers/pre-roll
                    os.environ['PENDING_STOP'] = 'True'
                    log_action('Stop delay activated for {} secs.'.format(stop_action_delay))
                    time.sleep(stop_action_delay)
                    # Check if we need to continue (i.e. another action happened while asleep)
                    if os.environ.get('PENDING_STOP', '') == 'True':
                        os.environ['PENDING_STOP'] = ''
                        log_action('Action stop_action() invoked (lights on).')
                        decora_api.stop_action()  # Turn-on the lights
                # If playing trailers/pre-roll only invoke one action clip_action()
                elif media_type in ('trailer', 'pre-roll'):
                    if event == 'media.play' or event == 'media.resume' or event == 'media.pause':
                        log_action('Action clip_action() invoked (dim lights).')
                        decora_api.clip_action()  # Dim the lights
                elif media_type in ('movie', 'episode'):
                    if event == 'media.play' or event == 'media.resume':
                        # Dim the lights at the same level as trailers
                        decora_api.clip_action()  # Dim the lights

                        # This delay prevents the play_action() if followed by trailers/pre-roll
                        os.environ['PENDING_PLAY'] = 'True'
                        log_action('Play delay activated for {} secs.'.format(play_action_delay))
                        time.sleep(play_action_delay)
                        # Check if we need to continue (i.e. another action happened while asleep)
                        if os.environ.get('PENDING_PLAY', '') == 'True':
                            os.environ['PENDING_PLAY'] = ''
                            log_action('Action play_action() invoked (lights off).')
                            decora_api.play_action()  # Turn-off the lights

                    if event == 'media.pause':
                        log_action('Action pause_action() invoked (dim lights).')
                        decora_api.pause_action()  # Dim the lights

                    # This event is for when 90% of the movie is reached.
                    if event == 'media.scrobble':
                        os.environ['PENDING_END'] = 'True'
                        time.sleep(end_action_delay)
                        # Check if we need to continue (i.e. another action happened while asleep)
                        if os.environ.get('PENDING_END', '') == 'True':
                            os.environ['PENDING_END'] = ''
                            log_action('Action end_action() invoked (dim lights).')
                            decora_api.end_action()  # Dim the lights

        else:
            if (not time_to_run) and device == plex_player:
                log_action('NOT TIME TO RUN: Device: {}, Local: {}, {}'.format(device, local, event))
            else:
                log_action('Post IGNORED: Device: {}, Local: {}, {}'.format(device, local, event))
        return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    # CAUTION: Any IP can access your webhook server!  You may want to add your own OS firewall
    #    rule to restrict access only to the Plex Media Player box.
    # For a simple webhook running internally, the Flask dev server is fine.
    print('plex-light_switch {}'.format(VERSION))
    app.run(debug=DEBUG, host='0.0.0.0')
