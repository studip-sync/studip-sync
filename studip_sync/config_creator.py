import getpass

from studip_sync import get_config_file
from studip_sync.constants import LOGIN_PRESETS, AUTHENTICATION_TYPES
from studip_sync.helpers import JSONConfig
from studip_sync.session import Session


def choose_authentication_type():
    print("Supported authentication methods:")
    i = 1
    auth_list = list(AUTHENTICATION_TYPES.items())
    for auth_key, auth_value in auth_list:
        print("{}) {}".format(i, auth_value.name()))
        i += 1

    print()

    try:
        auth_id = int(input("Choose an authentication method: "))
    except ValueError:
        raise ValueError("Please enter a valid number!")

    if auth_id <= 0 or auth_id > len(auth_list):
        raise ValueError("Please enter a valid number!")

    return auth_list[auth_id - 1]


def choose_preset():
    print("Supported universities:")
    i = 1
    for preset in LOGIN_PRESETS:
        print("{}) {}".format(i, preset.name, preset.base_url))
        i += 1

    print("{}) Custom server".format(i))
    print()

    try:
        preset_id = int(input("Choose a server: "))
    except ValueError:
        print("Invalid input! Defaulting to custom server...")
        return None

    if preset_id == i:
        return None

    if preset_id <= 0 or preset_id > len(LOGIN_PRESETS):
        print("Invalid input! Defaulting to custom server...")
        return None

    return LOGIN_PRESETS[preset_id - 1]


def get_url_and_auth_type():
    selected_preset = choose_preset()

    if selected_preset is not None:
        return selected_preset.base_url, selected_preset.auth_type, selected_preset.auth_data

    # Otherwise ask for them interactively
    base_url = input("URL of StudIP: ")
    auth_key, auth_type = choose_authentication_type()
    auth_data = auth_type.config_creator_get_auth_data()

    return base_url, auth_key, auth_data


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
        base_url, auth_key, auth_data = get_url_and_auth_type()
        username = input("Username: ")
        password = getpass.getpass()

        if base_url:
            self._session.set_base_url(base_url)

        print("Logging in...")
        self._session.login(auth_key, auth_data, username, password)

        save_password = input("Save password (in clear text)? [y/N]: ").lower() in ("y", "yes")
        files_destination = input("Sync files to directory (leave empty to disable): ")
        media_destination = input("Sync media to directory (leave empty to disable): ")

        config = {
            "user": {
                "login": username
            }
        }

        if base_url:
            config["base_url"] = base_url

        if auth_key:
            config["auth_type"] = auth_key

        if auth_data:
            config["auth_type_data"] = auth_data

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
