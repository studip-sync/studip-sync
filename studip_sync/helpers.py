import json
import os


class ConfigError(Exception):
    pass

class JSONConfig(object):
    def __init__(self, config_path=None):
        super(JSONConfig, self).__init__()

        try:
            config_file = open(config_path)
        except FileNotFoundError:
            raise ConfigError("Config file missing! Run 'studip-sync --init' to create a new "
                              "config file")

        if config_file:
            self.config = json.load(config_file)
        else:
            self.config = None

        self._check()

    def _check(self):
        pass

    @staticmethod
    def save_config(path, config):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as config_file:
            print("Writing new config to '{}'".format(path))
            json.dump(config, config_file, ensure_ascii=False, indent=4)
