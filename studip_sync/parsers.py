import re
import urllib
from bs4 import BeautifulSoup


class ParserError(Exception):
    pass


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
                        response['params'][form_input.attrs['name']] = form_input.attrs['value']
                    else:
                        response['params'][form_input.attrs['name']] = ''

            return response


def extract_files_flat_last_edit(html):
    soup = BeautifulSoup(html, 'lxml')

    for form in soup.find_all('form'):
        if 'action' in form.attrs:
            tds = form.find('table').find('tbody').find_all('tr')[0].find_all('td')
            if len(tds) == 8:
                td = tds[6]
                if 'data-sort-value' in td.attrs:
                    try:
                        return int(td.attrs['data-sort-value'])
                    except:
                        raise ParserError("last_edit: Couldn't convert data-sort-value to int")
                else:
                    raise ParserError("last_edit: Couldn't find td object with data-sort-value")
            elif len(tds) == 1 and "Keine Dateien vorhanden." in str(tds[0]):
                return 0 #No files, so no information when was the last time a file was edited
            else:
                raise ParserError("last_edit: row doesn't have expected length of cells")
    return 0


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
        r"https://studip.uni-goettingen.de/seminar_main.php\?auswahl=[0-9a-f]*$")
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
