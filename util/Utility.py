# -*- coding: utf-8 -*-

import base64
import datetime
import getpass
import json
import logging
import os
import re
import subprocess
import traceback
import pdb
from logging.handlers import RotatingFileHandler
from logging import handlers
import socket

from Crypto.Cipher import XOR


class Utility:
    """
    This class is a collection of utility methods static and otherwise.
    """
    CIPHER_KEY = '#$a%7_(1FSa!@WsfjWE<><!@#$W%_;-!'
    DEFAULT_SSH_PATH = '/usr/bin/ssh'
    DEFAULT_SCP_PATH = '/usr/bin/scp'
    LOG_UDP = 'UDP'
    LOG_TCP = 'TCP'

    # By default, don't validate hosts and timeout in 5 seconds if unable to connect.
    # Override this by overriding 'ssh_options'.
    DEFAULT_SSH_OPTIONS = '-o StrictHostKeyChecking=no -o ConnectTimeout=5'

    class SSHException(Exception):
        pass

    class SCPException(SSHException):
        pass

    class SSHConnectionException(SSHException):
        pass

    class SSHInvalidHostException(SSHException):
        pass

    class SSHAuthenticationException(SSHException):
        pass

    def __init__(self, *args, **kwargs):
        """
        Class constructor
        """

        self.debug = False
        """Debug flag"""

        self.last_command = None
        """Last command run using run_os_command()"""

        self.last_command_output = None
        """Last command output from using run_os_command()"""

        self.last_command_error = None
        """Last command error from using run_os_command()"""

        self.starttime = datetime.datetime.utcnow()
        """Start time recorded since this class was instantiated"""

        self.timer_start = self.starttime
        """Individual start time used for stop_timer() """

        self.local_logger = None
        self.remote_logger = None
        self.log_handler = None
        self.log_to_screen = False

        # SSH related variables
        self.scp_path = Utility.DEFAULT_SCP_PATH
        self.ssh_path = Utility.DEFAULT_SSH_PATH
        self.ssh_options = Utility.DEFAULT_SSH_OPTIONS
        self.ssh_proxy_user = None
        self.ssh_proxy_server = None
        self.ssh_log_commands = False
        self.invalid_ssh_hosts = []  # Track invalid hosts for this instance

    def ssh_cmd(self, user, server, cmd):
        """
        Run an SSH command against a server.  This assumes password-less (RSA keys) logins.
        Note that during the life of the Utility instance, this will track all invalid hosts (hosts that either
        do not resolve, or unable to connect) so that it doesn't waste connection time trying to connect.

        You may override default variables to suit:
            self.ssh_path
            self.ssh_options
            self.ssh_proxy_user
            self.ssh_proxy_server
            self.ssh_log_commands

        Args:
            user (str): SSH user name.
            server (str): SSH server.
            cmd (str): SSH command.

        Returns:
            str: Output of command Or None if command is invalid.

        Raises:
            SSHException: If server is invalid either during prior execution or current.
            SSHInvalidHostException: If server name/IP is invalid.
            SSHConnectionException: If unable to connect to the server.
        """
        # Limitation of this method is that you can't chain commands on the remote host with ";" character.

        # Don't make any connection attempts if this host was found to be invalid for this instance.
        if server in self.invalid_ssh_hosts:
            raise Utility.SSHException(
                "Host %s previously invalid. No connections will be made for this instance." % server)

        if self.ssh_proxy_user and self.ssh_proxy_server:
            proxy_prefix = '%s %s %s@%s' % (self.ssh_path, self.ssh_options, self.ssh_proxy_user, self.ssh_proxy_server)
            tmp_cmd = "%s %s %s %s@%s %s" % (proxy_prefix, self.ssh_path, self.ssh_options, user, server, cmd)
        else:
            tmp_cmd = '%s %s %s@%s %s' % (self.ssh_path, self.ssh_options, user, server, cmd)

        if self.ssh_log_commands:
            self.log_info('Ran SSH command: ==>%s<==' % tmp_cmd)

        output = self.run_os_command(tmp_cmd)

        # Check for errors before calling it good...
        return self.__check_ssh_output(output, server)

        # # Sift through output and omit unwanted lines
        # omit_lines = ['Warning: ', 'Connection to ']
        # output = ""
        #
        # lineiterator = iter(get_last_command_output().splitlines(True))
        #
        # for line in lineiterator:
        #     if not any(omit_line in line for omit_line in omit_lines):
        #         output = output + line
        # return output

    def __check_ssh_output(self, output, server, check_scp_output=False):
        host_is_valid = False  # Assume host is not valid until proven otherwise.
        try:
            if 'Name or service not known' in output or 'Could not resolve hostname' in output:
                raise Utility.SSHInvalidHostException("Invalid host: %s" % server)
            elif 'timed out' in output or 'closed by remote host' in output:
                raise Utility.SSHConnectionException("Unable to connect to host: %s" % server)
            else:
                host_is_valid = True

            if check_scp_output:
                file_errors = ['No such file or directory', 'Permission denied']
                for msg in file_errors:
                    if msg in output:
                        self.log_error(output)
                        raise Utility.SCPException(output)
                if output:  # No output is expected from SCP so log as an error here but don't raise an exception.
                    self.log_error(output)
        finally:
            if not host_is_valid:
                self.invalid_ssh_hosts.append(server)
                self.log_error(output)
            else:
                if output and not check_scp_output:
                    self.log_info("Output: ==>%s<==" % output)
        return output

    def scp_send_file(self, user, server, src_file, dst_path, silent=True):
        """
        Send a file or directory (recursive) to a server via SCP. This assumes password-less (RSA keys) logins.

        You may override default variables to suit:
            self.scp_path
            self.ssh_options
            self.ssh_proxy_user
            self.ssh_proxy_server

        Args:
            user:
            server:
            src_file:
            dst_path:

        Returns:

        """
        # ToDo: Create utility scp method that filters extraneous output in verbose mode.
        # ToDo: Delete file/dir from proxy if proxy host is used.
        proxy_used = False

        if self.ssh_proxy_user and self.ssh_proxy_server:
            proxy_used = True

            if src_file.endswith('/'):
                print("Error: Source file/path may not end with a '/'")
                return (1)
            src_file_only = os.path.basename(src_file)

            # Use /tmp as the proxy destination
            proxy_file = '%s/%s' % ('/tmp', src_file_only)
            proxy_prefix = '%s %s %s@%s' % (self.ssh_path, self.ssh_options, self.ssh_proxy_user, self.ssh_proxy_server)

            # Using proxy. Transfer to proxy first
            r_cmd = '%s -p -r %s %s %s@%s:%s' % (
                self.scp_path, self.ssh_options, src_file, self.ssh_proxy_user, self.ssh_proxy_server, proxy_file)

            self.log_info("Send to proxy, execute ==>%s<==" % r_cmd)
            self.__check_ssh_output(self.run_os_command(r_cmd), self.ssh_proxy_server, check_scp_output=True)

            # Send from proxy to intended destination
            r_cmd = '%s %s -p -r %s %s %s@%s:%s' % (
                proxy_prefix, self.scp_path, self.ssh_options, proxy_file, user, server, dst_path)

            self.log_info("Send from proxy to server, execute ==>%s<==" % r_cmd)
            self.__check_ssh_output(self.run_os_command(r_cmd), server, check_scp_output=True)
        else:
            r_cmd = '%s -p -r %s %s %s@%s:%s' % (
                self.scp_path, self.ssh_options, src_file, user, server, dst_path)

            self.log_info("Execute ==>%s<==" % r_cmd)
            self.__check_ssh_output(self.run_os_command(r_cmd), server, check_scp_output=True)

        status = None
        if proxy_used:
            status = "Sent file/dir: %s to %s:%s via proxy: %s@%s" % (
                src_file, server, dst_path, self.ssh_proxy_user, self.ssh_proxy_server)
        else:
            status = "Sent file/dir: %s to %s:%s" % (src_file, server, dst_path)

        self.log_info(status)
        if not silent:
            print(status)

    # ToDo: Combine scp_get_file and scp_send_file into one method to minimize repeated code.
    def scp_get_file(self, user, server, src_file, dst_path, silent=True):
        """
        Get a file or directory (recursive) to a server via SCP. This assumes password-less (RSA keys) logins.

        You may override default variables to suit:
            self.scp_path
            self.ssh_options
            self.ssh_proxy_user
            self.ssh_proxy_server

        Args:
            user:
            server:
            src_file:
            dst_path:

        Returns:

        """
        # ToDo: Create utility scp method that filters extraneous output in verbose mode.
        # ToDo: Delete file/dir from proxy if proxy host is used.
        proxy_used = False
        if src_file.endswith('/'):
            print("Error: Source file/path may not end with a '/'")
            return (1)
        src_file_only = os.path.basename(src_file)

        if not dst_path:
            dst_path = '.'

        if self.ssh_proxy_user and self.ssh_proxy_server:
            proxy_used = True

            # Use /tmp as the proxy destination
            proxy_file = '%s/%s' % ('/tmp', src_file_only)
            proxy_prefix = '%s %s %s@%s' % (self.ssh_path, self.ssh_options, self.ssh_proxy_user, self.ssh_proxy_server)

            # Using proxy. Get from server to proxy first
            r_cmd = '%s %s -p -r %s %s@%s:%s %s' % (
                proxy_prefix, self.scp_path, self.ssh_options, user, server, src_file, proxy_file)

            self.log_info("Get from server to proxy, execute ==>%s<==" % r_cmd)
            self.__check_ssh_output(self.run_os_command(r_cmd), server, check_scp_output=True)

            # Get from proxy.
            r_cmd = '%s -p -r %s %s@%s:%s %s' % (
                self.scp_path, self.ssh_options, self.ssh_proxy_user, self.ssh_proxy_server, proxy_file, dst_path)

            self.log_info("Get from proxy, execute ==>%s<==" % r_cmd)
            self.__check_ssh_output(self.run_os_command(r_cmd), self.ssh_proxy_server, check_scp_output=True)
        else:
            r_cmd = '%s -p -r %s %s@%s:%s %s' % (
                self.scp_path, self.ssh_options, user, server, src_file, dst_path)

            self.log_info("Execute ==>%s<==" % r_cmd)
            self.__check_ssh_output(self.run_os_command(r_cmd), server, check_scp_output=True)

        status = None
        if proxy_used:
            status = "Received file/dir: %s in: %s from %s:%s via proxy: %s@%s" % (
                src_file, dst_path, server, src_file, self.ssh_proxy_user, self.ssh_proxy_server)
        else:
            status = "Received file: %s in: %s from %s:%s" % (src_file, dst_path, server, src_file)

        self.log_info(status)
        if not silent:
            print(status)

    def get_current_duration(self):
        """
        Return current duration since last get.
        :return: Duration
        """
        end_time = datetime.datetime.utcnow()
        return end_time - self.starttime

    def start_timer(self):
        """
        Set the start timer for later calculation
        :return: None
        """
        self.timer_start = datetime.datetime.utcnow()

    def stop_timer(self):
        """
        Stop the timer and return the duration since start time.
        :return: Duration
        """
        end_time = datetime.datetime.utcnow()
        return end_time - self.timer_start

    def get_last_command(self):
        """
        Get last system command run from run_os_command()
        :return: Last command string.
        """
        return self.last_command

    def get_last_command_output(self):
        """
        Get the last command's output.
        :return: Command output
        """
        return self.last_command_output

    def get_last_command_error(self):
        """
        Get the last command's error.
        :return: Command output
        """
        return self.last_command_error

    def print_debug(self, s, desc=None, force=False, log=False):
        """
        Print formatted debug string
        :param s: String to print
        :param desc: Descriptive text about string to print
        :return: None
        """
        if self.debug or force:
            if not s:
                s = 'None'
            if desc:
                msg = ("[ DEBUG ] " + desc + ': ==>' + str(s) + '<==')
            else:
                msg = ("[ DEBUG ] " + str(s))
            print(msg)
            if log and self.local_logger:
                self.local_logger.debug(msg.replace('[ DEBUG ] ', ''))

    @classmethod
    def print_stack(cls):
        """
        Print the stack trace.
        :return: None
        """
        traceback.print_stack()

    @classmethod
    def key_interrupt(cls):
        """
        Display keyboard interrupt message
        :return: None
        """
        print("\n\nAw shucks, Ctrl-C detected. Exiting...\n")
        exit()

    def run_os_command(self, c):
        """
        Execute a system command
        :param c: Command to execute
        :return: Output of command
        """

        try:
            self.print_debug(c, 'Command')
            temp = subprocess.Popen([c], stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT, )
            (output, errput) = temp.communicate()
            temp.wait()
            self.print_debug(output, 'Output')
            self.last_command = c
        except KeyboardInterrupt:
            self.key_interrupt()
            exit(1)

        try:
            if errput:
                self.last_command_error = errput.decode("utf-8").strip()
            self.last_command_output = output.decode("utf-8").strip()
        except Exception as e:
            error_fixed = False
            try:
                self.last_command_output = output.decode("utf-8", "replace").strip()
                error_fixed = True
            except Exception as x:
                self.print_debug(str(x), '2nd Exception')
            finally:
                if error_fixed:
                    self.print_debug(c, 'Command causing error (AVERTED)')
                else:
                    self.print_debug(c, 'Command causing error')

                self.print_debug(output, 'Output causing error')
                self.print_debug(str(e), 'Exception')
                if self.local_logger:
                    if error_fixed:
                        self.log_error("(AVERTED) %s executing '%s'" % (str(e), c))
                    else:
                        self.log_error("%s executing '%s'" % (str(e), c))
        return self.last_command_output

    @classmethod
    def is_number(cls, s):
        """
        Check if string is a valid number.
        :param s: String to check
        :return: True if is a number, False otherwise
        """
        return re.match(r"[-+]?\d+", s) is not None

    @classmethod
    def query_yes_no(cls, question, default=None):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        """ Code copied from:
        http://code.activestate.com/recipes/577058
        with minor modifications
        """

        valid = {"yes": True, "y": True, "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("Invalid default answer: '%s'" % default)

        while True:
            print()
            question + prompt,
            choice = input().lower()
            if default is not None and choice == '':
                print()
                ""  # Display blank line
                return valid[default]
            elif choice in valid:
                print()
                ""  # Display blank line
                return valid[choice]
            else:
                print()
                "Please respond with 'yes' or 'no' (or 'y' or 'n')"

    @classmethod
    def encrypt_str(cls, i_str, c_key=None):
        """
        Change text to cipher text. Not meant to be secure but at least prevent opportunity
        theft of sensitive text such as passwords.
        :param i_str: String to encrypt
        :param c_key: Cipher to use
        :return: Encrypted string
        """
        if not c_key:
            cipher = XOR.new(Utility.CIPHER_KEY)
        else:
            cipher = XOR.new(c_key)
        return base64.b64encode(cipher.encrypt(i_str)).decode('utf-8')

    @classmethod
    def decrypt_str(cls, e_str, c_key=None):
        """
        Decrypt string. Only works if strng was encrypted by this class
        :param e_str: Encrypted string
        :param c_key: Cipher to use
        :return: Decrypted string
        """
        if not c_key:
            cipher = XOR.new(Utility.CIPHER_KEY)
        else:
            cipher = XOR.new(c_key)
        return cipher.decrypt(base64.b64decode(e_str)).decode('utf-8')

    @classmethod
    def escape_string(cls, e_str):
        """
        Escape special characters in string
        :param e_str: String to process
        :return: Escaped string
        """
        return json.dumps(e_str)

    @classmethod
    def trim_quotes(cls, q_str):
        """
        This is primarily used for strings quoted in Excel.  If double quotes encountered, replace
        with one, and trim outer quotes.
        :param q_str: String to process
        :return: Processed string
        """
        retval = q_str
        double_quotes = "\"\""
        if double_quotes in q_str:
            retval = q_str.replace(double_quotes, '"')
            if retval.startswith('"'):
                retval = retval[1:]  # Remove first character
            if retval.endswith('"'):
                retval = retval[:-1]  # Remove last character
        return retval

    @classmethod
    def prompt_user_password(cls, description='', user_prompt=True, password_prompt=True):
        """
        Prompt for username and password.
        :return: None
        """
        username = ''
        password = ''
        if description:
            description = description + ' '

        if user_prompt:
            while not username:
                print(description + "User Name: ", end=" ")
                username = input()

        if password_prompt:
            pwdprompt = lambda: (
                getpass.getpass(prompt=description + 'Password: '), getpass.getpass('Retype password: '))

            p1, p2 = pwdprompt()
            while p1 != p2:
                print('Passwords do not match. Try again')
                p1, p2 = pwdprompt()
            password = p1

        return username, password

    def get_remote_logger(self, log_name, syslog_host, syslog_port=514, syslog_proto=LOG_UDP, level=logging.INFO):
        """

        Args:
            log_name:
            syslog_host:
            syslog_port:
            syslog_proto:
            level:

        Returns:

        """
        if not self.remote_logger:
            if self.debug:
                level = logging.DEBUG

            self.remote_logger = logging.getLogger(log_name)
            self.remote_logger.setLevel(level)

            if syslog_proto.upper() == Utility.LOG_UDP:
                log_protocol = socket.SOCK_DGRAM
            else:
                log_protocol = socket.SOCK_STREAM

            handler = handlers.SysLogHandler((syslog_host, syslog_port), socktype=log_protocol)
            handler.formatter = logging.Formatter("%(name)s: LVL:%(levelname)s FUNC:%(funcName)s() %(message)s")
            self.remote_logger.addHandler(handler)

        return self.remote_logger

    def get_local_logger(self, log_file, level=logging.INFO, module_info=False):
        """
        Get/create a logger instance.
        :param module_info: True to set the module info in the file, False otherwise
        :param log_file: Log file.
        :param level:  Logger level (verbosity)
        :return: Logger instance
        """

        if not self.local_logger:
            if self.debug:
                level = logging.DEBUG

            # Check existing of log directory, if it doesn't exist, create it.
            log_dir = os.path.dirname(log_file)
            if not os.path.isdir(log_dir):
                try:
                    os.makedirs(log_dir)
                except Exception as e:
                    print("Log location (%s) not found, attempted to create: %s" % (log_dir, str(e)))
                    exit(1)

            # Note that if module info is True, then logging should be done directly, NOT via the helper methods.
            if module_info:
                log_formatter = logging.Formatter(
                    "%(asctime)s,%(name)s,%(levelname)s,%(funcName)s(%(lineno)d),%(message)s", "%Y-%m-%d %H:%M:%S")
            else:
                log_formatter = logging.Formatter("%(asctime)s,%(levelname)s,%(message)s", "%Y-%m-%d %H:%M:%S")

            my_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024,
                                             backupCount=10, encoding=None, delay=0)
            my_handler.setFormatter(log_formatter)
            my_handler.setLevel(level)
            app_log = logging.getLogger(__name__)
            app_log.setLevel(level)
            app_log.addHandler(my_handler)
            self.local_logger = app_log
            self.log_handler = my_handler
        return self.local_logger

    def set_log_level(self, level):
        self.log_handler.setLevel(level)
        self.local_logger.setLevel(level)

    def log_warn(self, message):
        if self.log_to_screen:
            print(message)
        if self.local_logger:
            self.local_logger.warn(message)

    def log_info(self, message, log_id):
        if self.log_to_screen:
            print(message)
        if self.local_logger:
            if not log_id:
                log_id = ''
            self.local_logger.info("ID: {} MSG: {}".format(log_id, message))

    def log_error(self, message):
        if self.log_to_screen:
            print(message)
        if self.local_logger:
            self.local_logger.error(message)

    def log_debug(self, message):
        if self.debug:
            if self.log_to_screen:
                print(message)
            if self.local_logger:
                self.local_logger.debug(message)

    def log_debug_var(self, var, title=None):
        """
        Logging mechanism if defined.
        :param title: String descriptor
        :param message: Message
        :return:
        """
        if self.debug:
            if self.log_to_screen:
                self.print_debug(var, desc=title)
            if self.local_logger:
                self.set_log_level(logging.DEBUG)
                self.local_logger.debug(title + ': ' + var)

    @classmethod
    def get_string_from_file(cls, f):
        """
        Read a single line from file.
        Args:
            f:  Input file
        Returns:
            None
        """
        infile = open(f, 'r')
        lines = infile.readlines()
        tpwd = ''
        for line in lines:
            tpwd = line.strip()
            if not tpwd:
                continue
            else:
                break  # found the password

        infile.close()
        return tpwd

    @classmethod
    def get_parser_config(cls, section, parser, upper_case_options=True, force=False):
        """
        Get parser section as a dict.
        Args:
            section (str): String section name.
            parser (ConfigParser): Parser object.
            upper_case_options (True): Set values to upper_case. False, leave it as-is.
            force (bool): Set to true to force upper_case_options (True to set the values to upper, False to lower)

        Returns:
            dict: Dict object of key/value pairs from section in parser.
        """
        return_dict = {}
        options = parser.options(section)
        for option in options:
            if force:
                if upper_case_options:
                    option = option.upper()
                else:
                    option = option.lower()
            elif upper_case_options:
                option = option.upper()
            else:
                # For clarity only, leave option as-is (no case change).
                pass
            try:
                return_dict[option] = parser.get(section, option)
            except:
                return_dict[option] = None
        return return_dict

    @classmethod
    def string_to_bool(cls, in_str, allow_none=False):
        """
        Function to convert Yes/No, True/False strings into a boolean.
        Args:
            in_str: case-insensitive input string.
            allow_none: if set to True, None is returned if input is None.

        Returns:
            If input is Yes/True, this returns True, all else is False.
        """
        retval = None
        if in_str is not None:
            if in_str.upper() == 'TRUE' or in_str.upper() == 'YES':
                retval = True
            else:
                retval = False

        # Return False if None is not allowed.
        if not allow_none:
            if not retval:
                retval = False

        return retval

    @classmethod
    def get_api_creds(cls, user_env, token_env, cipher_file_env, force=False):
        """
        Password obfuscation utility for password/keys
        Args:
            user_env: Environment variable containing user name/account name.
            token_env: Environment variable containing password/key value to obfuscate.
            cipher_file_env: Environment variable containing path to 32 char key file.
            force: By default, if the environment variable is found, it will be used as-is, to ignore
               any environment variables found, set this to True (that is, force a user/pass prompt).
        Returns:
            Tuple (api_user, api_passwd/key that is obfuscated)
        """
        cls.__set_api_creds(user_env, token_env, cipher_file_env, force)
        api_user = os.environ.get(user_env, None)
        cipher_key_file = os.environ.get(cipher_file_env, None)
        cipher_key = cls.get_string_from_file(cipher_key_file)
        api_token = os.environ[token_env]
        api_passwd = cls.decrypt_str(api_token, cipher_key)
        return api_user, api_passwd

    @classmethod
    def __set_api_creds(cls, user_env, token_env, cipher_file_env, force=False):
        """
        Private helper for get_api_creds
        Args:
            user_env: see get_api_creds()
            token_env: see get_api_creds()
            cipher_file_env: see get_api_creds()
            force: see get_api_creds()

        Returns:
            see get_api_creds()
        """
        # Check if environment vars are set
        api_user = os.environ.get(user_env, None)
        api_token = os.environ.get(token_env, None)
        cipher_key_file = os.environ.get(cipher_file_env, None)

        if not cipher_key_file:
            raise EnvironmentError("Required environment variable: %s not defined." % cipher_file_env)

        if not (api_user and api_token) or force:
            try:
                print("Common API credentials not defined. Prompting for user/pass...")
                (api_user, api_password) = cls.prompt_user_password('API Auth')

                # Convert password into a token
                cipher_key = cls.get_string_from_file(cipher_key_file)
                api_token = cls.encrypt_str(api_password, cipher_key)

                credentials = ('%s:%s' % (api_user, api_password))
                encoded_str = base64.b64encode(credentials.encode('utf-8'))

                print('For future execution, you can add the following to your user profile')
                print('  (not root) to suppress prompting for API credentials:')
                print('Cipher key file used: %s' % cipher_key_file)

                print('')
                print("export %s='%s'" % (user_env, api_user))
                print("export %s='%s'" % (token_env, api_token))
                print('')
                print('Alternatively, if you are only using for REST (Basic Auth) purposes, use:')
                print("export SCOUT_BASIC_AUTH_TOKEN='%s'" % encoded_str.decode("utf-8"))
                print('')

                # Set the environment variable for this session only
                os.environ[user_env] = api_user
                os.environ[token_env] = api_token

            except KeyboardInterrupt:
                cls.key_interrupt()
