import json
import re
from email.message import EmailMessage

from functools import wraps
from bs4 import BeautifulSoup
from studip_sync.log import get_logger

LOGGER = get_logger(__name__)

def log_html_on_exception():
    def decorator(func):
        @wraps(func)
        def inner(html, *args, **kwargs):
            try:
                return func(html, *args, **kwargs)
            except Exception as e:
                LOGGER.debug("Parser failed in %s, html excerpt=%r", func.__name__, html[:2000])

                raise

        return inner

    return decorator


def try_parser_functions(html, func_attempts):
    soup = BeautifulSoup(html, 'lxml')

    for func_attempt in func_attempts:
        try:
            return func_attempt(html, soup)
        except ParserError:
            continue

    raise ParserError("all attempts to parse data failed")


class ParserError(Exception):
    pass


COURSES_DATA_REGEX = re.compile(r"MyCoursesData\s*=\s*(\{.+?\})\s*;", re.DOTALL)
COURSES_URL_REGEX = re.compile(r"""["']([^"']*dispatch\.php/my_courses[^"']*)["']""")
SEMESTER_NAME_REGEX = re.compile(
    r"(?:WiSe|SoSe|Wintersemester|Sommersemester|WS|SS|\b20\d{2}\b)",
    re.IGNORECASE
)


def _normalize_course_name(name):
    save_as = (name or "").strip()
    save_as = re.sub(r"\s\s+", " ", save_as)
    save_as = save_as.replace("/", "--")
    return save_as


def _normalize_semester_name(name):
    semester = (name or "").strip()
    semester = re.sub(r"\s\s+", " ", semester)
    semester = semester.replace("/", "--")
    return semester


def _looks_like_semester(name):
    if not name:
        return False
    return SEMESTER_NAME_REGEX.search(name) is not None


def _extract_courses_data(html):
    matcher = COURSES_DATA_REGEX.search(html)
    if matcher is None:
        raise ParserError("Could not find courses")

    try:
        return json.loads(matcher.group(1))
    except json.JSONDecodeError as e:
        raise ParserError("Could not parse courses JSON") from e


def _extract_semester_groups(courses):
    semester_groups = []

    for group in courses.get("groups", []):
        group_name = _normalize_semester_name(group.get("name"))
        group_data = group.get("data") or []

        if not isinstance(group_data, list):
            continue

        for item in group_data:
            if not isinstance(item, dict):
                continue

            course_ids = item.get("ids")
            if not isinstance(course_ids, list) or not course_ids:
                continue

            data_name = _normalize_semester_name(item.get("name"))

            if _looks_like_semester(data_name):
                semester_name = data_name
            elif _looks_like_semester(group_name):
                semester_name = group_name
            elif data_name:
                semester_name = data_name
            elif group_name:
                semester_name = group_name
            else:
                semester_name = "Unknown Semester"

            semester_groups.append({
                "semester": semester_name,
                "ids": course_ids
            })

    if not semester_groups:
        raise ParserError("Could not find semesters in course data")

    return semester_groups


@log_html_on_exception()
def extract_files_flat_last_edit(html):
    def extract_json(_, s):
        form = s.find('form', id="files_table_form")

        if not form:
            raise ParserError("last_edit: files_table_form not found")

        if "data-files" not in form.attrs:
            raise ParserError("last_edit: Missing data-files attribute in form")

        form_data_files = json.loads(form.attrs["data-files"])

        file_timestamps = []

        for file_data in form_data_files:
            if "chdate" not in file_data:
                raise ParserError("last_edit: No chdate: " + str(file_data.keys()))

            file_timestamps.append(file_data["chdate"])

        if len(file_timestamps) > 0:
            return max(file_timestamps)
        else:
            return 0

    def extract_html_table(_, s):
        for form in s.find_all('form'):
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
                        raise ParserError(
                            "last_edit: Couldn't find td object with data-sort-value")
                elif len(tds) == 1 and "Keine Dateien vorhanden." in str(tds[0]):
                    return 0  # No files, so no information when was the last time a file was edited
                else:
                    raise ParserError("last_edit: row doesn't have expected length of cells")

        raise ParserError("last_edit: Found no valid form")


    return try_parser_functions(html, [extract_json, extract_html_table])


@log_html_on_exception()
def extract_files_index_data(html):
    soup = BeautifulSoup(html, 'lxml')

    form = soup.find('form', id="files_table_form")

    if "data-files" not in form.attrs:
        raise ParserError("index_data: Missing data-files attribute in form")

    if "data-folders" not in form.attrs:
        raise ParserError("index_data: Missing data-folders attribute in form")

    form_data_files = json.loads(form["data-files"])
    form_data_folders = json.loads(form["data-folders"])

    return form_data_files, form_data_folders


@log_html_on_exception()
def extract_parent_folder_id(html):
    soup = BeautifulSoup(html, 'lxml')
    folder_ids = soup.find_all(attrs={"name": "parent_folder_id"})

    if len(folder_ids) != 1:
        raise ParserError("Could not find parent folder ID")

    return folder_ids.pop().attrs.get("value", "")


@log_html_on_exception()
def extract_csrf_token(html):
    soup = BeautifulSoup(html, 'lxml')
    tokens = soup.find_all("input", attrs={"name": "security_token"})

    if len(tokens) < 1:
        raise ParserError("Could not find CSRF token")

    return tokens.pop().attrs.get("value", "")


@log_html_on_exception()
def extract_courses(html, only_recent_semester):
    courses = _extract_courses_data(html)
    semester_groups = _extract_semester_groups(courses)
    course_data = courses.get("courses", {})

    semester_order = []
    semester_seen = set()
    seen_courses = set()
    parsed_courses = []

    for group in semester_groups:
        semester_name = group["semester"]

        if semester_name not in semester_seen:
            semester_seen.add(semester_name)
            semester_order.append(semester_name)

        for course_id in group["ids"]:
            course_id_str = str(course_id)
            course = course_data.get(course_id_str)
            if course is None:
                course = course_data.get(course_id)
            if course is None:
                continue

            dedupe_key = (course_id_str, semester_name)
            if dedupe_key in seen_courses:
                continue
            seen_courses.add(dedupe_key)

            parsed_courses.append({
                "course_id": course_id_str,
                "save_as": _normalize_course_name(course.get("name", "")),
                "semester": semester_name
            })

    if only_recent_semester and semester_order:
        recent_semester = next((s for s in semester_order if _looks_like_semester(s)),
                               semester_order[0])
        parsed_courses = [course for course in parsed_courses
                          if course["semester"] == recent_semester]

    semester_ids = {
        semester_name: len(semester_order) - i for i, semester_name in enumerate(semester_order)
    }

    for course in parsed_courses:
        course["semester_id"] = semester_ids.get(course["semester"], 0)
        yield course


@log_html_on_exception()
def extract_my_courses_semester_urls(html):
    urls = []
    seen = set()

    for match in COURSES_URL_REGEX.findall(html):
        url = match.replace("\\/", "/")
        if "dispatch.php/my_courses" not in url:
            continue
        if "set_semester" not in url and "sem_select" not in url and "semester=" not in url:
            continue
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)

    return urls


@log_html_on_exception()
def extract_media_list(html):
    soup = BeautifulSoup(html, 'lxml')

    media_files = []

    for table in soup.find_all("table", class_="media-table"):
        if "id" not in table.attrs:
            raise ParserError("media_list: 'id' is missing from table")

        media_hash = table["id"]

        a_element_overlay_curtain = table.select_one("div.overlay-curtain > a")
        a_element_media_table_infos = table.select_one("div.media-table-infos > div > a")

        if not a_element_media_table_infos:
            raise ParserError("media_list: a_element_media_table_infos is missing")

        if "href" not in a_element_media_table_infos.attrs:
            raise ParserError("media_list: 'href' is missing from a_element_media_table_infos")

        media_url = a_element_media_table_infos["href"]

        if not media_hash or not media_url:
            raise ParserError("media_list: hash or url is empty")

        media_files.append({
            "hash": media_hash,
            "media_url": media_url,
            "type": "direct_download" if a_element_overlay_curtain is None else "player"
        })

    return media_files


@log_html_on_exception()
def extract_media_best_download_link(html):
    def extract_table(_, s):
        download_options = s.select("table#dllist tr td")

        if not download_options or len(download_options) <= 1:
            raise ParserError("media_download_link: No download options found")
        # Always select the first result as the best result
        # (skip first "Download" td, so instead of 0 select 1)

        download_td = download_options[1]

        download_a = download_td.find("a")

        if "href" not in download_a.attrs:
            raise ParserError("media_download_link: href is missing from download_a")

        return download_a["href"]

    def extract_iframe(_, s):
        iframe = s.find("iframe", id="framed_player")
        if not iframe:
            raise ParserError("media_download_link: No iframe found")

        if "src" not in iframe.attrs:
            raise ParserError("media_download_link: src is missing from iframe")

        return iframe.attrs["src"]

    def extract_video(_, s):
        video = s.find("video", id="mediaplayer_html5_api")
        if not video:
            raise ParserError("media_download_link: No video item found")

        if "src" not in video.attrs:
            raise ParserError("media_download_link: src is missing from video item")

        return video.attrs["src"]

    def extract_video_regex(h, _):

        matcher = re.compile(r"/plugins.php/mediacastplugin/media/check/.+\.mp4")
        links = matcher.findall(h)

        if len(links) < 1:
            raise ParserError("media_download_link: links < 1")

        return links[len(links) - 1]


    return try_parser_functions(html, [extract_table, extract_iframe, extract_video, extract_video_regex])


@log_html_on_exception()
def extract_filename_from_headers(headers):
    if "Content-Disposition" not in headers:
        raise ParserError(
            "media_filename_headers: \"Content-Disposition\" is missing")

    msg = EmailMessage()
    msg['Content-Disposition'] = headers["Content-Disposition"]
    header_params = msg["Content-Disposition"].params

    if "filename" not in header_params:
        raise ParserError("media_filename_headers: \"filename\" is missing")

    if header_params["filename"] == "":
        raise ParserError("media_filename_headers: filename value is empty")

    return header_params["filename"]
