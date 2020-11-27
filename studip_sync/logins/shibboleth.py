from bs4 import BeautifulSoup

from studip_sync.logins import LoginBase, LoginError
from studip_sync.parsers import ParserError


class ShibbolethLogin(LoginBase):
    @staticmethod
    def name():
        return "Shibboleth SSO"

    @staticmethod
    def config_creator_get_auth_data():
        sso_base_url = input("SSO URL: ")
        return {"sso_url": sso_base_url}

    @staticmethod
    def login(session, username, password, auth_type_data):
        login_data = {
            "j_username": username,
            "j_password": password,
            "donotcache": 1,
            "_eventId_proceed": ""
        }

        with session.session.post(auth_type_data["sso_url"], data=login_data) as response:
            if not response.ok:
                raise LoginError("Cannot access SSO server")
            saml_data = ShibbolethLogin.extract_saml_data(response.text)

        with session.session.post(session.url.studip_main(), data=saml_data) as response:
            if not response.ok:
                raise LoginError("Cannot access Stud.IP main page")

    @staticmethod
    def extract_saml_data(html):
        soup = BeautifulSoup(html, 'lxml')

        def _extract_value(name):
            names = soup.find_all(attrs={"name": name})

            if len(names) != 1:
                raise ParserError("Could not parse SAML form")

            return names.pop().attrs.get("value", "")

        return {
            "RelayState": _extract_value("RelayState"),
            "SAMLResponse": _extract_value("SAMLResponse")
        }
