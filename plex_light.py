#!/usr/bin/env python

import json
import os
from flask import Flask, request, abort
from plex import WebHookReceiver
from plex.Utiliy import *
from dotenv import load_dotenv

# Make sure a config file ".env" exists in the config dir.
load_dotenv("config/.env")

app = Flask(__name__)
receiver = WebHookReceiver(debug_mode)


@app.route('/webhook', methods=['POST'])
def plex_light():
    if request.method == 'POST':
        plex_dict = request.form.to_dict()
        payload = json.loads(plex_dict['payload'])
        return receiver.process_payload(payload)
    else:
        abort(400)


if __name__ == '__main__':
    # CAUTION: Any IP can access your webhook server!  You may want to add your own OS firewall
    #    rule to restrict access only to the Plex Media Player box.
    # For a simple webhook running internally, the Flask dev server is fine.
    app.run(debug=True, host='0.0.0.0')
