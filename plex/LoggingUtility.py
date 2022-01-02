import socket, shortuuid, logging
from logging import handlers
from datetime import datetime


class LoggingUtility:
    def __init__(self, debug):
        self.log_id = None
        self.remote_logger = None
        self.debug = debug

    def get_new_id(self):
        self.log_id = shortuuid.ShortUUID().random(length=8)

    def start_logger(self, log_name, syslog_server=None, syslog_port=None, syslog_proto=None):
        self.get_new_id()
        if syslog_server:
            syslog_level = logging.INFO if self.debug else logging.DEBUG
            self.remote_logger = logging.getLogger(log_name)
            self.remote_logger.setLevel(syslog_level)
            self.remote_logger.propagate = False

            if syslog_proto.upper() == 'UDP':
                log_protocol = socket.SOCK_DGRAM
            else:
                log_protocol = socket.SOCK_STREAM

            handler = handlers.SysLogHandler((syslog_server, syslog_port), socktype=log_protocol)
            # Note the ":" after the name.  This is important for rsyslog to parse properly.
            handler.formatter = logging.Formatter("%(name)s: LVL:%(levelname)s %(message)s")
            self.remote_logger.addHandler(handler)

    def write(self, log_str):
        """
        Wrapper logging function, so we can log anywhere in the future.
        Args:
            log_str: String to log.

        Returns:
            None.
        """
        dt_obj = datetime.now()
        timestamp = dt_obj.strftime("%d-%b-%Y (%H:%M:%S)")
        print('{} - {}'.format(timestamp, log_str))

        if self.remote_logger:
            self.remote_logger.info("ID:{} MSG:{}".format(self.log_id, log_str))

    def close_logger(self):
        try:
            # Silently close logging handlers if necessary.
            if self.remote_logger:
                for handler in self.remote_logger.handlers:
                    handler.close()
        except:
            pass
