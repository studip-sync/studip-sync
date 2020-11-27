

class LoginError(Exception):
    pass


class LoginBase:
    @staticmethod
    def login(session, username, password, auth_type_data):
        raise NotImplemented()


class LoginPreset:

    def __init__(self, name, base_url, auth_type, auth_data):
        self.name = name
        self.base_url = base_url
        self.auth_type = auth_type
        self.auth_data = auth_data
