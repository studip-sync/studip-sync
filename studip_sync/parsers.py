import re
import urllib
from bs4 import BeautifulSoup
import cgi
import json


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

    form = soup.find('form', id="files_table_form")

    if not "data-files" in form.attrs:
        raise ParserError("last_edit: Missing data-files attribute in form")

    form_data_files = json.loads(form["data-files"])

    file_timestamps = []

    for file_data in form_data_files:
        if not "chdate" in file_data:
            raise ParserError("last_edit: No chdate: " + str(file_data.keys()))

        file_timestamps.append(file_data["chdate"])

    if len(file_timestamps) > 0:
        return max(file_timestamps)
    else:
        return 0


def extract_files_index_data(html):
    soup = BeautifulSoup(html, 'lxml')

    form = soup.find('form', id="files_table_form")

    if not "data-files" in form.attrs:
        raise ParserError("index_data: Missing data-files attribute in form")

    if not "data-folders" in form.attrs:
        raise ParserError("index_data: Missing data-folders attribute in form")

    form_data_files = json.loads(form["data-files"])
    form_data_folders = json.loads(form["data-folders"])

    return form_data_files, form_data_folders


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


def extract_courses(html, only_recent_semester):
    soup = BeautifulSoup(html, 'lxml')

    div = soup.find("div", id="my_seminars")
    tables = div.find_all("table")

    for i in range(0, len(tables)):
        if only_recent_semester and i > 0:
            continue

        table = tables[i]

        caption = table.find("caption").string.strip()

        matcher = re.compile(
            r"https://studip.uni-goettingen.de/seminar_main.php\?auswahl=[0-9a-f]*$")
        links = table.find_all("a", href=matcher)

        for link in links:
            href = link.attrs.get("href", "")
            query = urllib.parse.urlsplit(href).query
            course_id = urllib.parse.parse_qs(query).get("auswahl", [""])[0]

            save_as = re.sub(r"\s\s+", " ", link.get_text(strip=True))
            save_as = save_as.replace("/", "--")

            yield {
                "course_id": course_id,
                "save_as": save_as,
                "semester": caption
            }


def extract_media_list(html):
    soup = BeautifulSoup(html, 'lxml')

    media_files = []

    for table in soup.find_all("table", class_="media-table"):
        if not "id" in table.attrs:
            raise ParserError("media_list: 'id' is missing from table")

        media_hash = table["id"]

        a_element = table.select_one("div.overlay-curtain > a")

        if not a_element:
            raise ParserError("media_list: a_element is missing")

        if not "href" in a_element.attrs:
            raise ParserError("media_list: 'href' is missing from a_element")

        media_url = a_element["href"]

        if not media_hash or not media_url:
            raise ParserError("media_list: hash or url is empty")

        media_files.append((media_hash, media_url))

    return media_files


def extract_media_best_download_link(html):
    soup = BeautifulSoup(html, 'lxml')

    download_options = soup.select("table#dllist tr td")

    if not download_options or len(download_options) <= 1:
        raise ParserError("media_download_link: No download options found")

    # Always select the first result as the best result
    # (skip first "Download" td, so instead of 0 select 1)

    download_td = download_options[1]

    download_a = download_td.find("a")

    if not "href" in download_a.attrs:
        raise ParserError("media_download_link: href is missing from download_a")

    return download_a["href"]


def extract_filename_from_headers(headers):
    if not "Content-Disposition" in headers:
        raise ParserError(
            "media_filename_headers: \"Content-Disposition\" is missing: " + media_hash)

    content_disposition = headers["Content-Disposition"]

    header_value, header_params = cgi.parse_header(content_disposition)

    if not "filename" in header_params:
        raise ParserError("media_filename_headers: \"filename\" is missing: " + media_hash)

    if header_params["filename"] == "":
        raise ParserError("media_filename_headers: filename value is empty: " + media_hash)

    return header_params["filename"]
