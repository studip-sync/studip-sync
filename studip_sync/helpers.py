import json
import os
import tempfile

from studip_sync.log import get_logger

LOGGER = get_logger(__name__)


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
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)
        atomic_write_json(path, config)
        LOGGER.info("Writing new config to '%s'", path)


def atomic_write_json(path, data):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory,
                                         prefix=".tmp-", suffix=".json", delete=False) as temp_file:
            json.dump(data, temp_file, ensure_ascii=False, indent=4)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = temp_file.name

        os.replace(temp_path, path)
    except Exception:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise
