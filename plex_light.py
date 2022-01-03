#!/usr/bin/env python

import json
import os
from plex import LoggingUtility, WebHookReceiver
from flask import Flask, request, abort
from dotenv import load_dotenv

app = Flask(__name__)

# Load configuration file...
config_file = os.environ.get('PL_CONFIG_FILE', None)

if config_file:
    load_dotenv(config_file)
else:
    print("Env. var \"PL_CONFIG_FILE\" must be defined to point to a valid config file.")
    exit(1)

debug_mode = True if os.environ.get('DEBUG_MODE').upper() == 'TRUE' else False
log_name = os.environ.get('LOG_NAME')

# These are optional parameters for remote logging...
syslog_server = os.environ.get('PLEX_LIGHT_SYSLOG_SERVER', None)
syslog_port = int(os.environ.get('PLEX_LIGHT_SYSLOG_PORT', None))
syslog_proto = os.environ.get('PLEX_LIGHT_SYSLOG_PROTO', None)

# Create logging instance...
logger = None
try:
    logger = LoggingUtility(debug_mode)
    logger.start_logger(log_name, syslog_server, syslog_port, syslog_proto)
    logger.write("Config file read from: {}".format(config_file))

    # Get the webhook receiver and login to light switch
    receiver = WebHookReceiver(logger)
    receiver.get_switch()
except Exception as e:
    print(e)
    exit(1)


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
    version = '1.0'
    logger.write("Starting plex_light v.{}".format(version))
    logger.write("Ready to process Plex events.".format(config_file))
    app.run(debug=debug_mode, host='0.0.0.0')
