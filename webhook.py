#!/usr/bin/env python

import json
import os
from flask import Flask, request, abort
from plex import WebHookReceiver
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
debug_mode = True if os.environ.get('DEBUG_MODE').upper() == 'TRUE' else False
receiver = WebHookReceiver(debug_mode)

@app.route('/webhook', methods=['POST'])
def webhook():
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
