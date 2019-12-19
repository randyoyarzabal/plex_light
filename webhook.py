#!/usr/bin/env python

import json
import os
import time
from flask import Flask, request, abort
from plex import DecoraPlexHook
from datetime import datetime

VERSION = 'v0.3'

app = Flask(__name__)


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
        advanced_control = os.environ.get('ADVANCED_CONTROL').upper()

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

        # Determine media type for future handling of various types.
        if media_type == 'clip':
            if 'preroll' in payload['Metadata'].get('guid', ''):
                media_type = 'pre-roll'
            elif 'trailer' in payload['Metadata'].get('subtype', ''):
                media_type = 'trailer'
            else:
                media_type = 'unknown'

        log_action('Media ({}): {} - {}'.format(media_type, media_title, event))

        # Only perform actions for a particular player playing on the local network.
        if local and device == plex_player:
            # Basic Plex event detection (no trailers/pre-roll)
            if advanced_control == 'FALSE':
                if event == 'media.play' or event == 'media.resume':
                    log_action('Action play_action() invoked (lights off).')
                    decora_api.play_action()  # Turn-off the lights

                if event == 'media.pause':
                    log_action('Action pause_action() invoked (dim lights).')
                    decora_api.pause_action()  # Dim the lights

                    # This event is for when 90% of the movie is reached.
                if event == 'media.scrobble':
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
                    log_action('Action play_action (pre-roll done) invoked (lights off).')
                    decora_api.play_action()  # Turn-off the lights
                # Detect media stop when skipping or when trailers transition automatically.
                elif event == 'media.stop':
                    # This delay is to prevent stop_action() from invoking in between trailers/pre-roll
                    os.environ['PENDING_STOP'] = 'True'
                    log_action('Stop delay activated for {} secs.'.format(stop_action_delay))
                    time.sleep(stop_action_delay)
                    if os.environ.get('PENDING_STOP', '') == 'True':
                        os.environ['PENDING_STOP'] = ''
                        log_action('Action stop_action() invoked (lights on).')
                        decora_api.stop_action()  # Turn-on the lights
                # If playing trailers/pre-roll only invoke one action clip_action()
                elif media_type in ('trailer', 'pre-roll'):
                    if event == 'media.play' or event == 'media.resume' or event == 'media.pause':
                        os.environ['PENDING_STOP'] = ''
                        os.environ['PENDING_PLAY'] = ''
                        log_action('Action clip_action() invoked (dim lights).')
                        decora_api.clip_action()  # Dim the lights
                elif media_type in ('movie', 'episode'):
                    if event == 'media.play' or event == 'media.resume':
                        os.environ['PENDING_STOP'] = ''

                        # Dim the lights at the same level as trailers
                        decora_api.clip_action()  # Dim the lights

                        # This delay prevents the play_action() if followed by trailers/pre-roll
                        os.environ['PENDING_PLAY'] = 'True'
                        log_action('Play delay activated for {} secs.'.format(play_action_delay))
                        time.sleep(play_action_delay)
                        if os.environ.get('PENDING_PLAY', '') == 'True':
                            os.environ['PENDING_PLAY'] = ''
                            log_action('Action play_action() invoked (lights off).')
                            decora_api.play_action()  # Turn-off the lights

                    if event == 'media.pause':
                        log_action('Action pause_action() invoked (dim lights).')
                        decora_api.pause_action()  # Dim the lights

                    # This event is for when 90% of the movie is reached.
                    if event == 'media.scrobble':
                        log_action('Action end_action() invoked (dim lights).')
                        decora_api.end_action()  # Dim the lights
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
    app.run(debug=True, host='0.0.0.0')
