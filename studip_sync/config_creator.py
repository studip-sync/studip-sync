import getpass

from studip_sync import get_config_file
from studip_sync.helpers import JSONConfig
from studip_sync.session import Session


class ConfigCreator(object):
    """Create a new config file interactively"""

    def __init__(self):
        super(ConfigCreator, self).__init__()
        self._session = Session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._session.__exit__(exc_type, exc_value, traceback)

    def new_config(self):
        base_url = input("URL of StudIP (leave empty for default server): ")
        username = input("Username: ")
        password = getpass.getpass()

        if base_url:
            self._session.set_base_url(base_url)

        self._session.login(username, password)

        save_password = input("Save password (in clear text)? [y/N]: ").lower() in ("y", "yes")
        files_destination = input("Sync files to directory (leave empty to disable): ")
        media_destination = input("Sync media to directory (leave empty to disable): ")

        config = {}
        config["user"] = {"login": username}

        if base_url:
            config["base_url"] = base_url

        if save_password:
            config["user"]["password"] = password

        if files_destination:
            config["files_destination"] = files_destination

        if media_destination:
            config["media_destination"] = media_destination

        path = get_config_file()

        JSONConfig.save_config(path, config)

    @staticmethod
    def replace_config(config):
        path = get_config_file()

        JSONConfig.save_config(path, config)

