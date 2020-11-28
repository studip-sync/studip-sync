import urllib.parse

from bs4 import BeautifulSoup

from studip_sync.logins import LoginBase, LoginError
from studip_sync.parsers import ParserError


class ShibbolethLogin(LoginBase):
    @staticmethod
    def name():
        return "Shibboleth SSO"

    @staticmethod
    def config_creator_get_auth_data():
        login_url = input("Login URL: ")
        sso_post_url = input("SSO Post URL: ")

        return {
            "login_url": login_url,
            "sso_post_url": sso_post_url
        }

    @staticmethod
    def login(session, username, password, auth_type_data):
        with session.session.get(auth_type_data["login_url"]) as response:
            if not response.ok:
                raise LoginError("Cannot access Stud.IP login page")
            sso_url_relative = ShibbolethLogin.extract_sso_url(response.text)
            sso_url = urllib.parse.urljoin(response.url, sso_url_relative)

        login_data = {
            "j_username": username,
            "j_password": password,
            "donotcache": 1,
            "_eventId_proceed": ""
        }

        with session.session.post(sso_url, data=login_data) as response:
            if not response.ok:
                raise LoginError("Cannot access SSO server")
            saml_data = ShibbolethLogin.extract_saml_data(response.text)

        with session.session.post(auth_type_data["sso_post_url"], data=saml_data) as response:
            if not response.ok:
                raise LoginError("Cannot access Stud.IP main page")

    @staticmethod
    def extract_sso_url(html):
        soup = BeautifulSoup(html, 'lxml')

        for form in soup.find_all('form'):
            if 'action' in form.attrs:
                return form.attrs['action']

        raise ParserError("Could not find login form")

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
