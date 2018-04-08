import json
import os
import getpass
from studip_sync.arg_parser import ARGS
from studip_sync import CONFIG_PATH


class ConfigError(Exception):
    pass


class Config(object):

    def __init__(self):
        super(Config, self).__init__()
        self.args = ARGS
        if self.args.config:
            config_file = self.args.config
        else:
            try:
                config_file = open(CONFIG_PATH)
            except FileNotFoundError:
                raise ConfigError("Config file missing! Run 'studip-sync --init' to create a new "
                                  "config file")

        self.config = json.load(config_file)
        self._username = None
        self._password = None

        self._check()

    def _check(self):
        if not self.target:
            raise ConfigError("Target directory is missing. You can specify the target directory "
                              "via the commandline or the JSON config file!")

        if not self.username:
            raise ConfigError("Username is missing")

        if not self.password:
            raise ConfigError("Password is missing")

        if not self.courses:
            raise ConfigError("No courses are available. Add courses to your config file!")

    def user_property(self, prop):
        user = self.config.get("user")
        if user:
            return user.get(prop)
        return None

    @property
    def username(self):
        if self._username:
            return self._username

        if self.args.interactive:
            self._username = input("Username: ")
            return self._username

        return self.user_property("login")

    @property
    def password(self):
        if self._password:
            return self._password

        if self.args.interactive:
            self._password = getpass.getpass()
            return self._password

        return self.user_property("password")

    @property
    def courses(self):
        return self.config.get("courses")

    @property
    def target(self):
        if self.args.destination:
            destination = self.args.destination
        else:
            destination = self.config.get("destination", "")

        return os.path.expanduser(destination)


try:
    CONFIG = Config()
except ConfigError as err:
    print(str(err))
    print("Aborting...")
    exit(1)
