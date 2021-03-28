from bs4 import BeautifulSoup

from studip_sync.logins import LoginBase, LoginError
from studip_sync.parsers import ParserError


class GeneralLogin(LoginBase):
    @staticmethod
    def name():
        return "General"

    @staticmethod
    def config_creator_get_auth_data():
        return {}

    @staticmethod
    def login(session, username, password, auth_type_data):
        with session.session.get(session.url.login_page()) as response:
            if not response.ok:
                raise LoginError("Cannot access Stud.IP login page")
            login_data = GeneralLogin.extract_login_data(response.text)

        login_params_auth = {
            "loginname": username,
            "password": password
        }

        login_params = {**login_params_auth, **login_data['params']}

        with session.session.post(login_data['action'], data=login_params) as response:
            if not response.ok:
                raise LoginError("Cannot post login data")
            elif "messagebox_error" in response.text:
                raise LoginError("Wrong credentials, cannot login")

        # Test if logged in
        with session.session.post(session.url.studip_main()) as response:
            if not response.ok or "Veranstaltungen" not in response.text:
                raise LoginError("Cannot access Stud.IP main page")

    @staticmethod
    def extract_login_data(html):
        soup = BeautifulSoup(html, 'lxml')

        response = {}

        for form in soup.find_all('form'):
            if 'action' in form.attrs:
                response['action'] = form.attrs['action']
                response['params'] = {}

                needed_vars = [
                    'security_token',
                    'login_ticket',
                    'resolution',
                    'device_pixel_ratio'
                ]

                for form_input in form.find_all('input'):
                    if 'name' in form_input.attrs and form_input.attrs['name'] in needed_vars:
                        if 'value' in form_input.attrs:
                            response['params'][form_input.attrs['name']] = form_input.attrs[
                                'value']
                        else:
                            response['params'][form_input.attrs['name']] = ''

                return response

        raise ParserError("login: Couldn't find login data! Is the base url correct?")
