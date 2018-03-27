import json
import argparse
import os
import getpass


class ConfigError(Exception):
    pass


class Config(object):

    def __init__(self):
        super(Config, self).__init__()
        parser = argparse.ArgumentParser(description="Synchronize Stud.IP files")

        parser.add_argument("-i", "--interactive", action="store_true",
                            help="read username and password from stdin (and not from config "
                            "file)")

        parser.add_argument("-c", "--config", type=argparse.FileType('r'), metavar="FILE",
                            default=None,
                            help="set the path to the config file (Default is "
                            "'~/.config/studip-sync/config.json')")

        parser.add_argument("destination", nargs="?", metavar="DIR", default=None,
                            help="synchronize the files to the given destination directory")

        self.args = parser.parse_args()

        config_file = self.args.config or \
            open(os.path.expanduser("~/.config/studip-sync/config.json"))

        self.config = json.load(config_file)
        self._username = None
        self._password = None

        self._check()

    def _check(self):
        if not self.username:
            raise ConfigError("Username is missing")

        if not self.password:
            raise ConfigError("Password is missing")

        if not self.courses:
            raise ConfigError("No courses are available. Add courses to your config file!")

        if not self.target:
            raise ConfigError("Target directory is missing. You can specify the target directory "
                              "via the commandline or the JSON config file!")

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
            destination = self.config.get("destination")

        return os.path.expanduser(destination)


try:
    CONFIG = Config()
except ConfigError as err:
    print(str(err))
    print("Aborting...")
    exit(1)
