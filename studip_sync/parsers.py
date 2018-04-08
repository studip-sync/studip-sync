import re
import urllib
from bs4 import BeautifulSoup


class ParserError(Exception):
    pass


def extract_sso_url(html):
    soup = BeautifulSoup(html, 'lxml')

    for form in soup.find_all('form'):
        if 'action' in form.attrs:
            return form.attrs['action']

    raise ParserError("Could not find login form")


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


def extract_parent_folder_id(html):
    soup = BeautifulSoup(html, 'lxml')
    folder_ids = soup.find_all(attrs={"name": "parent_folder_id"})

    if len(folder_ids) != 1:
        raise ParserError("Could not find parent folder ID")

    return folder_ids.pop().attrs.get("value", "")


def extract_csrf_token(html):
    soup = BeautifulSoup(html, 'lxml')
    tokens = soup.find_all("input", attrs={"name": "security_token"})

    if len(tokens) < 1:
        raise ParserError("Could not find CSRF token")

    return tokens.pop().attrs.get("value", "")


def extract_courses(html):
    soup = BeautifulSoup(html, 'lxml')
    matcher = re.compile(
        r"https://studip.uni-passau.de/studip/seminar_main.php\?auswahl=[0-9a-f]*$")
    links = soup.find_all("a", href=matcher)

    for link in links:
        href = link.attrs.get("href", "")
        query = urllib.parse.urlsplit(href).query
        course_id = urllib.parse.parse_qs(query).get("auswahl", [""])[0]

        save_as = re.sub(r"\s\s+", " ", link.get_text(strip=True))
        save_as = save_as.replace("/", "--")

        yield {
            "course_id": course_id,
            "save_as": save_as
        }
