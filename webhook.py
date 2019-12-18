#!/usr/bin/env python

import json
import os
import time
from flask import Flask, request, abort
from plex import DecoraPlexHook

VERSION = 'v0.1'
plex_player = os.environ.get('PLEX_PLAYER')

app = Flask(__name__)


def log_action(*items):
    print(','.join(items))


@app.route('/webhook', methods=['POST'])
def webhook():
    # This object instantiates a Leviton Decora dimmer/switch control.
    # If you want to control other lights, you'll have to implement/use a different concrete
    # subclass of the PlexHook abstract class and change here.
    decora_api = DecoraPlexHook(activity=True)

    if request.method == 'POST':
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

        print('Media ({}): {} - {}'.format(media_type, media_title, event))

        # if event == 'media.stop':
        #     print(json.dumps(payload, indent=4, sort_keys=True))

        # This prevents lights from turning off during transition from trailer/pre-roll to movie.
        # Note that this does have a known side-effect of the lights not turning on if trailers
        # or pre-roll media is abruptly stopped (which is an uncommon action, but obviously possible).
        # Normal trailer/pre-roll events such as pause and play are unaffected.

        if media_type == 'pre-roll' and local and device == plex_player and event == 'media.stop':
            print('Action play_movie (pre-roll done) invoked (lights off).')
            decora_api.play_movie()  # Turn-off the lights
            # print('Action ignored as requested.')
        elif event == 'media.stop' and local and device == plex_player:
            print('Action pending stop()')
            os.environ['PENDING_STOP'] = 'TRUE'
            time.sleep(2)
            if os.environ.get('PENDING_STOP', '') == 'TRUE':
                print('Action stop_movie invoked (lights on).')
                decora_api.stop_movie()  # Turn-on the lights
                os.environ['PENDING_STOP'] = ''

        # elif media_type in ('trailer', 'pre-roll') and local and device == plex_player and event == 'media.stop':
        #     print('Action ignored as requested.')


        # If playing trailers/preroll or movies, adhere to the normal events.
        elif media_type in ('trailer', 'pre-roll') and local and device == plex_player:
            if event == 'media.play' or event == 'media.resume' or event == 'media.pause':
                os.environ['PENDING_STOP'] = ''
                os.environ['PENDING_PLAY'] = ''
                print('Action pause_movie invoked (dim lights).')
                decora_api.pause_movie()  # Dim the lights
        elif media_type == 'movie' and local and device == plex_player:
            if event == 'media.play' or event == 'media.resume':
                os.environ['PENDING_STOP'] = ''

                # Dim the lights at the same level as trailers
                decora_api.pause_movie()  # Dim the lights

                os.environ['PENDING_PLAY'] = 'TRUE'
                time.sleep(2)
                if os.environ.get('PENDING_PLAY', '') == 'TRUE':
                    os.environ['PENDING_PLAY'] = ''
                    print('Action play_movie invoked (lights off).')
                    decora_api.play_movie()  # Turn-off the lights

            if event == 'media.pause':
                print('Action pause_movie invoked (dim lights).')
                decora_api.pause_movie()  # Dim the lights

            if event == 'media.scrobble':
                print('Action pause_movie invoked (dim lights).')
                decora_api.pause_movie()  # Dim the lights

            # if event == 'media.stop':
            #     print('Action stop_movie invoked (lights on).')
            #     decora_api.stop_movie()  # Turn-on the lights
        else:
            print('Post IGNORED: Device: {}, Local: {}, {}'.format(device, local, event))
        return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    # CAUTION: Any IP can access your webhook server!  You may want to add your own OS firewall
    #    rule to restrict access only to the Plex Media Player box.
    # For a simple webhook running internally, the Flask dev server is fine.
    print('plex-light_switch {}'.format(VERSION))
    app.run(debug=True, host='0.0.0.0')
