import readline
import getpass
import json
import os
from studip_sync import CONFIG_PATH
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
        username = input("Username: ")
        password = getpass.getpass()
        self._session.login(username, password)

        courses = list(self._session.get_couses())
        destination = input("Sync to directory: ")
        save_login = input("Save username and password? [y/N]: ").lower() in ("y", "yes")

        config = {}
        config["courses"] = courses

        if destination:
            config["destination"] = destination

        if save_login:
            config["user"] = {
                "login":  username,
                "password": password
            }

        path = CONFIG_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as config_file:
            print("Writing new config to '{}'".format(path))
            json.dump(config, config_file, ensure_ascii=False, indent=4)
