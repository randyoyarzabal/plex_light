import os, logging
import logging
from logging import handlers
from datetime import datetime
import socket
from dotenv import load_dotenv

load_dotenv()

LOG_UDP = 'UDP'
LOG_TCP = 'TCP'
debug_mode = True if os.environ.get('DEBUG_MODE').upper() == 'TRUE' else False

remote_logger = None
log_id = None

# Log remotely as well if necessary
syslog_server = os.environ.get('PLEX_LIGHT_SYSLOG_SERVER')
syslog_port = int(os.environ.get('PLEX_LIGHT_SYSLOG_PORT'))
syslog_proto = os.environ.get('PLEX_LIGHT_SYSLOG_PROTO')

if syslog_server != '':
    syslog_level = logging.INFO if debug_mode else logging.DEBUG
    remote_logger = logging.getLogger('plex_light')
    remote_logger.setLevel(syslog_level)
    remote_logger.propagate = False

    if syslog_proto.upper() == LOG_UDP:
        log_protocol = socket.SOCK_DGRAM
    else:
        log_protocol = socket.SOCK_STREAM

    handler = handlers.SysLogHandler((syslog_server, syslog_port), socktype=log_protocol)
    handler.formatter = logging.Formatter("%(name)s LVL:%(levelname)s FUNC:%(funcName)s() %(message)s")
    remote_logger.addHandler(handler)


def log_action(log_id, log_str):
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

    if remote_logger:
        remote_logger.info("ID:{} MSG:{}".format(log_id, log_str))
