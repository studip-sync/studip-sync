import re
import urllib
from bs4 import BeautifulSoup
import cgi
import json


class ParserError(Exception):
    pass


def extract_files_flat_last_edit(html):
    soup = BeautifulSoup(html, 'lxml')

    form = soup.find('form', id="files_table_form")

    if not form:
        raise ParserError("last_edit: files_table_form not found")

    if not "data-files" in form.attrs:
        raise ParserError("last_edit: Missing data-files attribute in form")

    form_data_files = json.loads(form.attrs["data-files"])

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
            r"https://.*seminar_main.php\?auswahl=[0-9a-f]*$")
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
    def extract_table(html, soup):
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

    def extract_iframe(html, soup):
        iframe = soup.find("iframe", id="framed_player")
        if not iframe:
            raise ParserError("media_download_link: No iframe found")

        if not "src" in iframe.attrs:
            raise ParserError("media_download_link: src is missing from iframe")

        return iframe.attrs["src"]

    def extract_video(html, soup):
        video = soup.find("video", id="mediaplayer_html5_api")
        if not video:
            raise ParserError("media_download_link: No video item found")

        if not "src" in video.attrs:
            raise ParserError("media_download_link: src is missing from video item")

        return video.attrs["src"]

    def extract_video_regex(html, soup):

        matcher = re.compile(
            r"\/plugins.php\/mediacastplugin\/media\/check\/.+\.mp4")
        links = matcher.findall(html)

        if len(links) < 1:
            raise ParserError("media_download_link: links < 1")

        return links[len(links)-1]

    soup = BeautifulSoup(html, 'lxml')

    func_attempts = [extract_table, extract_iframe, extract_video, extract_video_regex]

    for func_attempt in func_attempts:
        try:
            return func_attempt(html, soup)
        except ParserError:
            continue

    # Debug statement to identify parser errors
    print("----------- DEBUG -----------")
    print(html)

    raise ParserError("media_download_link: all attempts to extract url failed")


def extract_filename_from_headers(headers):
    if not "Content-Disposition" in headers:
        raise ParserError(
            "media_filename_headers: \"Content-Disposition\" is missing")

    content_disposition = headers["Content-Disposition"]

    header_value, header_params = cgi.parse_header(content_disposition)

    if not "filename" in header_params:
        raise ParserError("media_filename_headers: \"filename\" is missing")

    if header_params["filename"] == "":
        raise ParserError("media_filename_headers: filename value is empty")

    return header_params["filename"]
