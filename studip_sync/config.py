import getpass
import os
import shlex
import subprocess

from studip_sync import get_config_file
from studip_sync.arg_parser import ARGS
from studip_sync.config_creator import ConfigCreator
from studip_sync.constants import URL_BASEURL_DEFAULT, AUTHENTICATION_TYPE_DEFAULT, \
    AUTHENTICATION_TYPE_DATA_DEFAULT, AUTHENTICATION_TYPES, HTTP_REQUEST_TIMEOUT, \
    HTTP_RETRY_TOTAL, HTTP_RETRY_BACKOFF_FACTOR
from studip_sync.helpers import JSONConfig, ConfigError


class Config(JSONConfig):

    def __init__(self):
        self.args = ARGS

        config_path = get_config_file()

        self.config_dir = os.path.dirname(config_path)

        self._username = None
        self._password = None

        super(Config, self).__init__(config_path)

    def _check(self):
        if not self.files_destination and not self.media_destination:
            raise ConfigError(
                "Both target directories are missing. You can specify the target directories "
                "via the commandline or the JSON config file!")

        if not self.username:
            raise ConfigError("Username is missing")

        if not self.password:
            raise ConfigError("Password is missing")

        if self.auth_type not in AUTHENTICATION_TYPES:
            raise ConfigError("Invalid auth type!")

        if self.http_request_timeout <= 0:
            raise ConfigError("http_timeout must be > 0")

        if self.http_retry_total < 0:
            raise ConfigError("http_retries must be >= 0")

        if self.http_retry_backoff_factor < 0:
            raise ConfigError("http_retry_backoff_factor must be >= 0")

    @property
    def last_sync(self):
        if not self.config:
            return 0

        last_sync = self.config.get("last_sync")
        if last_sync:
            return last_sync
        else:
            return 0

    def update_last_sync(self, last_sync):
        if not self.config:
            return

        new_config = self.config
        new_config["last_sync"] = last_sync
        ConfigCreator.replace_config(new_config)

    @property
    def plugins(self):
        if not self.config:
            return []

        return self.config.get("plugins", [])

    def update_plugins(self, plugins):
        if not self.config:
            return

        new_config = self.config
        new_config["plugins"] = plugins
        ConfigCreator.replace_config(new_config)

    def user_property(self, prop):
        if not self.config:
            return None

        user = self.config.get("user")

        if not user:
            return None

        return user.get(prop)

    @staticmethod
    def _cast_numeric(value, cast_type, key_name):
        try:
            return cast_type(value)
        except (TypeError, ValueError) as e:
            raise ConfigError("{} has an invalid value".format(key_name)) from e

    @property
    def username(self):
        if self._username:
            return self._username

        self._username = self.user_property("login") or input("Username: ")
        return self._username

    def _get_password_command(self):
        password_command = self.user_property("password_command")
        if not password_command:
            return None

        print("Loading password from command...")
        command_list = shlex.split(password_command)
        command_output = subprocess.check_output(command_list)
        if not command_output:
            return None

        return command_output.decode("utf-8").strip()

    @property
    def password(self):
        if self._password:
            return self._password

        self._password = self.user_property(
            "password") or self._get_password_command() or getpass.getpass()
        return self._password

    @property
    def base_url(self):
        if not self.config:
            return URL_BASEURL_DEFAULT

        return self.config.get("base_url", URL_BASEURL_DEFAULT)

    @property
    def auth_type(self):
        if not self.config:
            return AUTHENTICATION_TYPE_DEFAULT

        return self.config.get("auth_type", AUTHENTICATION_TYPE_DEFAULT)

    @property
    def auth_type_data(self):
        if not self.config:
            return AUTHENTICATION_TYPE_DATA_DEFAULT

        return self.config.get("auth_type_data", AUTHENTICATION_TYPE_DATA_DEFAULT)

    @property
    def files_destination(self):
        if self.args.destination is not None:
            files_destination = self.args.destination
        else:
            if not self.config:
                return None

            files_destination = self.config.get("files_destination", "")

        return os.path.expanduser(files_destination)

    @property
    def media_destination(self):
        if self.args.media is not None:
            media_destination = self.args.media
        else:
            if not self.config:
                return None

            media_destination = self.config.get("media_destination", "")

        return os.path.expanduser(media_destination)

    @property
    def use_new_file_structure(self):
        if not self.config:
            return False

        return self.config.get("use_new_file_structure", False)

    @property
    def http_request_timeout(self):
        if self.args.http_timeout is not None:
            value = self.args.http_timeout
        elif not self.config:
            value = HTTP_REQUEST_TIMEOUT
        else:
            value = self.config.get("http_timeout", HTTP_REQUEST_TIMEOUT)

        return self._cast_numeric(value, float, "http_timeout")

    @property
    def http_retry_total(self):
        if self.args.http_retries is not None:
            value = self.args.http_retries
        elif not self.config:
            value = HTTP_RETRY_TOTAL
        else:
            value = self.config.get("http_retries", HTTP_RETRY_TOTAL)

        return self._cast_numeric(value, int, "http_retries")

    @property
    def http_retry_backoff_factor(self):
        if self.args.http_retry_backoff is not None:
            value = self.args.http_retry_backoff
        elif not self.config:
            value = HTTP_RETRY_BACKOFF_FACTOR
        else:
            value = self.config.get("http_retry_backoff_factor", HTTP_RETRY_BACKOFF_FACTOR)

        return self._cast_numeric(value, float, "http_retry_backoff_factor")


try:
    CONFIG = Config()
except ConfigError as err:
    print(str(err))
    print("Aborting...")
    exit(1)
