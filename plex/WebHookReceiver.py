#!/usr/bin/env python

import json
import os
import time
from plex import DecoraPlexHook
from datetime import datetime, timedelta


class WebHookReceiver:

    def __init__(self, debug):
        self.version = '0.4'
        self.debug = debug

        # This object is an instance of a Leviton Decora dimmer/switch control implementation of the PlexHook class.
        # If you want to control other lights, you'll have to implement/use a different concrete subclass of the
        # PlexHook abstract class and change here.
        self.light_switch = DecoraPlexHook()

    def __del__(self):
        pass

    def is_time_to_run(self, start_time, end_time):
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

        if self.debug:
            self.log_action(
                'Current time: {:%H:%M:%S} - (Run Range: {:%H:%M} - {:%H:%M})'.format(now_dt_obj,
                                                                                      start_dt_obj,
                                                                                      end_dt_obj
                                                                                      ))
        if start_dt_obj <= end_dt_obj:
            return start_dt_obj <= now_dt_obj <= end_dt_obj
        else:  # past midnight e.g., 17:00-09:00 (5pm - 9am)
            return start_dt_obj <= now_dt_obj or now_dt_obj <= end_dt_obj

    def log_action(self, log_str):
        """
        Wrapper logging function so we can log anywhere in the future.
        Args:
            log_str: String to log.

        Returns:
            None.
        """
        dt_obj = datetime.now()
        timestamp = dt_obj.strftime("%d-%b-%Y (%H:%M:%S)")
        print('{} - {}'.format(timestamp, log_str))

    def scrobble_delay(self, delay, duration):
        """
        Check then delay ending action if necessary.
        Args:
            delay: in seconds.
            duration: length of media in seocnds.
        Returns:
            None.
        """
        if delay > 0:
            scrobble_mark = duration * .9
            play_time_left = duration - scrobble_mark
            # Only invoke delay if delay requested is < than the left over duration of the media.
            if delay < play_time_left:
                self.log_action('End delay activated for {} secs.'.format(delay))
                time.sleep(delay)
            else:
                self.log_action('Content is too short to impose ending delay.')

    def process_payload(self, payload):
        """
        The "brains" of the the operation. Act on events received in Plex payload.
        Args:
            payload: payload of Plex server post.
        Returns:
            None.
        """
        plex_player = os.environ.get('PLEX_PLAYER')
        stop_action_delay = int(os.environ.get('PLEX_STOP_ACTION_DELAY'))
        play_action_delay = int(os.environ.get('PLEX_PLAY_ACTION_DELAY'))
        end_action_delay = int(os.environ.get('PLEX_END_ACTION_DELAY'))
        control_mode = os.environ.get('CONTROL_MODE').upper()
        time_to_run = self.is_time_to_run(os.environ.get('RUN_TIME_START'), os.environ.get('RUN_TIME_END'))

        # Decipher the payload information
        event = payload['event']
        media_type = payload['Metadata']['type']
        local = payload['Player']['local']
        device = payload['Player']['title']
        media_title = payload['Metadata']['title']

        # Use this to calculate optional last # of minutes of a movie Or past the 'media.scrobble' 90% mark.
        duration = payload['Metadata'].get('duration', 0)
        duration = duration / 1000  # Convert from milliseconds to seconds.

        # Determine media type for future handling of various types.
        if media_type == 'clip':
            if 'preroll' in payload['Metadata'].get('guid', ''):
                media_type = 'pre-roll'
            elif 'trailer' in payload['Metadata'].get('subtype', ''):
                media_type = 'trailer'
            else:
                media_type = 'unknown'

        self.log_action('Media ({}): {} - {}'.format(media_type, media_title, event))

        if self.debug:
            self.log_action('Duration: {}'.format(timedelta(seconds=duration)))
            self.log_action('Scrobble Mark: {}'.format(timedelta(seconds=duration * .9)))
            #print(json.dumps(payload, indent=4, sort_keys=True))

        # Only perform actions for a particular player playing on the local network.
        if local and device == plex_player and time_to_run:
            # Reset delay markers, action invoked while previous request is sleeping.
            os.environ['PENDING_END'] = ''
            os.environ['PENDING_STOP'] = ''
            os.environ['PENDING_PLAY'] = ''

            # Basic Plex event detection (no trailers/pre-roll)
            if control_mode == 'BASIC':
                if event == 'media.play' or event == 'media.resume':
                    self.log_action('Action play_action() invoked (lights off).')
                    self.light_switch.play_action()  # Turn-off the lights

                if event == 'media.pause':
                    self.log_action('Action pause_action() invoked (dim lights).')
                    self.light_switch.pause_action()  # Dim the lights

                # This event is for when 90% of the movie is reached.
                if media_type not in ('pre-roll', 'trailer'):
                    if event == 'media.scrobble':
                        os.environ['PENDING_END'] = 'True'

                        # Optional delay so that we can be closer to the credits.
                        self.scrobble_delay(end_action_delay, duration)

                        # Check if we need to continue (i.e. another action happened while asleep)
                        if os.environ.get('PENDING_END', '') == 'True':
                            os.environ['PENDING_END'] = ''
                            self.log_action('Action end_action() invoked (dim lights).')
                            self.light_switch.end_action()  # Dim the lights

                if event == 'media.stop':
                    self.log_action('Action stop_action() invoked (lights on).')
                    self.light_switch.stop_action()  # Turn-on the lights

            # Advanced event detection (trailers AND pre-roll enabled)
            else:
                # This is an artificial detection of movie start since Plex doesn't send a new 'media.play' event
                # when trailers/pre-roll are enabled.
                if media_type == 'pre-roll' and event == 'media.stop':
                    self.log_action('Action play_action (pre-roll done, movie starting...) invoked (lights off).')
                    self.light_switch.play_action()  # Turn-off the lights
                # Detect media stop when skipping or when trailers transition automatically.
                elif event == 'media.stop':
                    # This delay is to prevent stop_action() from invoking in between trailers/pre-roll
                    os.environ['PENDING_STOP'] = 'True'
                    self.log_action('Stop delay activated for {} secs.'.format(stop_action_delay))
                    time.sleep(stop_action_delay)
                    # Check if we need to continue (i.e. another action happened while asleep)
                    if os.environ.get('PENDING_STOP', '') == 'True':
                        os.environ['PENDING_STOP'] = ''
                        self.log_action('Action stop_action() invoked (lights on).')
                        self.light_switch.stop_action()  # Turn-on the lights
                # If playing trailers/pre-roll only invoke one action clip_action()
                elif media_type in ('trailer', 'pre-roll'):
                    if event == 'media.play' or event == 'media.resume' or event == 'media.pause':
                        self.log_action('Action clip_action() invoked (dim lights).')
                        self.light_switch.clip_action()  # Dim the lights
                elif media_type in ('movie', 'episode'):
                    if event == 'media.play' or event == 'media.resume':
                        # This delay prevents the play_action() if followed by trailers/pre-roll
                        os.environ['PENDING_PLAY'] = 'True'
                        self.log_action('Play delay activated for {} secs.'.format(play_action_delay))
                        time.sleep(play_action_delay)
                        # Check if we need to continue (i.e. another action happened while asleep)
                        if os.environ.get('PENDING_PLAY', '') == 'True':
                            os.environ['PENDING_PLAY'] = ''
                            self.log_action('Action play_action() invoked (lights off).')
                            self.light_switch.play_action()  # Turn-off the lights

                    if event == 'media.pause':
                        self.log_action('Action pause_action() invoked (dim lights).')
                        self.light_switch.pause_action()  # Dim the lights

                    # This event is for when 90% of the movie is reached.
                    if event == 'media.scrobble':
                        os.environ['PENDING_END'] = 'True'

                        # Optional delay so that we can be closer to the credits.
                        self.scrobble_delay(end_action_delay, duration)

                        # Check if we need to continue (i.e. another action happened while asleep)
                        if os.environ.get('PENDING_END', '') == 'True':
                            os.environ['PENDING_END'] = ''
                            self.log_action('Action end_action() invoked (dim lights).')
                            self.light_switch.end_action()  # Dim the lights

        else:
            if (not time_to_run) and device == plex_player:
                self.log_action('NOT TIME TO RUN: Device: {}, Local: {}, {}'.format(device, local, event))
            else:
                self.log_action('Post IGNORED: Device: {}, Local: {}, {}'.format(device, local, event))
        return '', 200
