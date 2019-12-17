#!/usr/bin/env python

import json
import os
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
        clip_type = ''

        # Determine media type for future handling of various types.
        if media_type == 'clip':
            if 'preroll' in payload['Metadata'].get('guid', ''):
                clip_type = 'pre-roll'
            elif 'trailer' in payload['Metadata'].get('subtype', ''):
                clip_type = 'trailer'
            else:
                clip_type = 'unknown'
            print('Clip ({}): {} - {}'.format(clip_type, media_title, event))
        else:
            print('Media ({}): {} - {}'.format(media_type, media_title, event))

        # This prevents lights from turning off during transition from trailer/pre-roll to movie.
        # Note that this does have a known side-effect of the lights not turning on if trailers
        # or pre-roll media is interrupted and stopped (which is uncommon).
        # Normal events such as pause and play are unaffected.
        if media_type == 'clip' and local and device == plex_player and event == 'media.stop':
            print('Action ignored as requested.')
            pass

        # If playing trailers/preroll or movies, adhere to the normal events.
        elif (media_type == 'clip' or media_type == 'movie') and local and device == plex_player:
            if event == 'media.play' or event == 'media.resume':
                decora_api.play_movie()
            if event == 'media.pause':
                decora_api.pause_movie()
            if event == 'media.stop':  # This code won't be reached by clips by design.
                decora_api.stop_movie()
        else:
            print('Post IGNORED: Device: {}, Local: {}, Media ({}): {} - {}'.format(device, local, media_type,
                                                                                    media_title,
                                                                                    event))
        return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    # CAUTION: Any IP can access your webhook server!  You may want to add your own OS firewall
    #    rule to restrict access only to the Plex Media Player box.
    # For a simple webhook running internally, the Flask dev server is fine.
    print('plex-light_switch {}'.format(VERSION))
    app.run(debug=True, host='0.0.0.0')
