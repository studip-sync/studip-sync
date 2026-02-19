from datetime import datetime
import os
import shutil
import tempfile
import time
import unicodedata
import string

from studip_sync.arg_parser import ARGS
from studip_sync.config import CONFIG
from studip_sync.course_list_store import save_course_list
from studip_sync.course_paths import get_course_save_as
from studip_sync.logins import LoginError
from studip_sync.log import get_logger
from studip_sync.plugins.plugins import PLUGINS
from studip_sync.session import Session, DownloadError, MissingFeatureError, \
    MissingPermissionFolderError, SessionError
from studip_sync.parsers import ParserError

LOGGER = get_logger(__name__)


class StudIPRSync(object):

    def __init__(self):
        super(StudIPRSync, self).__init__()
        self.workdir = tempfile.mkdtemp(prefix="studip-sync")
        self.files_destination_dir = CONFIG.files_destination
        self.media_destination_dir = CONFIG.media_destination

        if self.files_destination_dir:
            os.makedirs(self.files_destination_dir, exist_ok=True)
        if self.media_destination_dir:
            os.makedirs(self.media_destination_dir, exist_ok=True)

    def sync(self, sync_fully=False, sync_recent=False, use_api=True):
        PLUGINS.hook("hook_start")
        stats = {
            "courses_total": 0,
            "courses_file_synced": 0,
            "courses_file_skipped": 0,
            "files_downloaded": 0,
            "media_downloaded": 0,
            "errors": 0
        }

        with Session(
                base_url=CONFIG.base_url,
                plugins=PLUGINS,
                request_timeout=CONFIG.http_request_timeout,
                retry_total=CONFIG.http_retry_total,
                retry_backoff_factor=CONFIG.http_retry_backoff_factor,
                retry_status_forcelist=CONFIG.http_retry_status_forcelist) as session:
            LOGGER.info("Logging in...")
            try:
                session.login(CONFIG.auth_type, CONFIG.auth_type_data, CONFIG.username,
                              CONFIG.password)
            except (LoginError, ParserError) as e:
                LOGGER.error("Login failed!")
                LOGGER.error(str(e))
                return 1

            LOGGER.info("Downloading course list...")

            try:
                courses = list(session.get_courses(sync_recent))
            except (LoginError, ParserError, SessionError) as e:
                LOGGER.error("Downloading course list failed!")
                LOGGER.error(str(e))
                return 1

            if CONFIG.save_course_list:
                try:
                    path = save_course_list(courses, CONFIG.config_dir)
                    LOGGER.info("Saved course list to: %s", path)
                except OSError as e:
                    LOGGER.warning("Failed to save course list: %s", e)

            if sync_recent:
                LOGGER.info("Syncing only the most recent semester!")

            stats["courses_total"] = len(courses)
            status_code = 0
            for i in range(0, len(courses)):
                course = courses[i]
                course_save_as = get_course_save_as(course)
                LOGGER.info("%s) %s", i + 1, course_save_as)

                if self.files_destination_dir:
                    try:
                        files_root_dir = os.path.join(self.files_destination_dir, course_save_as)

                        result = CourseRSync(session, self.workdir, files_root_dir, course,
                                             sync_fully, use_api).download()
                        stats["files_downloaded"] += result["files_downloaded"]
                        if result["synced"]:
                            stats["courses_file_synced"] += 1
                        else:
                            stats["courses_file_skipped"] += 1
                    except MissingFeatureError:
                        # Ignore if there are no files
                        pass
                    except DownloadError as e:
                        LOGGER.error("\tDownload of files failed: %s", e)
                        status_code = 2
                        stats["errors"] += 1
                        raise

                if self.media_destination_dir:
                    try:
                        LOGGER.info("\tSyncing media files...")

                        media_root_dir = os.path.join(self.media_destination_dir,
                                                      course_save_as)

                        media_downloaded = session.download_media(course["course_id"], media_root_dir,
                                                                  course_save_as)
                        stats["media_downloaded"] += media_downloaded
                    except MissingFeatureError:
                        # Ignore if there is no media
                        pass
                    except DownloadError as e:
                        LOGGER.error("\tDownload of media failed: %s", e)
                        status_code = 2
                        stats["errors"] += 1
                        raise
                    except ParserError as e:
                        LOGGER.error("\tDownload of media failed: %s", e)
                        if status_code != 0:
                            raise
                        else:
                            status_code = 2
                            stats["errors"] += 1

        if self.files_destination_dir and status_code == 0:
            CONFIG.update_last_sync(int(time.time()))

        LOGGER.info(
            "Summary: courses=%s, file_synced=%s, file_skipped=%s, files_downloaded=%s, "
            "media_downloaded=%s, errors=%s",
            stats["courses_total"], stats["courses_file_synced"], stats["courses_file_skipped"],
            stats["files_downloaded"], stats["media_downloaded"], stats["errors"]
        )

        return status_code

    def cleanup(self):
        shutil.rmtree(self.workdir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()


UNICODE_NORMALIZE_MODE = "NFKC"


def check_and_cleanup_form_data(form_data_files, form_data_folders, use_api):
    form_data_files_new = []
    for form_data in form_data_files:
        try:
            if "id" not in form_data:
                log("Skipped file that can't be downloaded: {}".format(form_data["name"]))
                continue
                
            form_id = form_data["id"]
            
            if not all(c in string.hexdigits for c in form_id):
                raise ParserError("id is not hexadecimal")

            # TODO: support links by saving them as .url files
            if "size" not in form_data or form_data["size"] is None or ("storage" in form_data and form_data["storage"] == "url") or ("icon" in form_data and form_data["icon"] == "link-extern"):
                if ARGS.v:
                    LOGGER.debug("[Debug] %s", str(form_data))
                log("Found unsupported file: {}".format(form_data["name"]))
                continue

            if use_api and "is_downloadable" in form_data and not form_data["is_downloadable"]:
                log("Skipped file that can't be downloaded: {}".format(form_data["name"]))
                continue

            new_file_data = {
                "name": unicodedata.normalize(UNICODE_NORMALIZE_MODE, form_data["name"]).replace("/", "--"),
                "id": form_id,
                "size": int(form_data["size"]),
                "chdate": int(form_data["chdate"])
            }

            if not use_api:
                new_file_data["download_url"] = form_data["download_url"]

            form_data_files_new.append(new_file_data)
        except Exception as e:
            LOGGER.debug("Invalid file form data: %s", form_data)
            raise ParserError("File attributes are invalid: {}".format(e))

    form_data_folders_new = []
    for form_data in form_data_folders:
        try:
            if "id" not in form_data:
                log("Skipped folder that can't be downloaded")
                continue
            form_id = form_data["id"]
            if not all(c in string.hexdigits for c in form_id):
                raise ValueError("id is not hexadecimal")

            form_data_folders_new.append({
                "name": unicodedata.normalize(UNICODE_NORMALIZE_MODE, form_data["name"]).replace("/", "--"),
                "id": form_id
            })
        except Exception as e:
            LOGGER.debug("Invalid folder form data: %s", form_data)
            raise ParserError("Folder attributes are invalid: {}".format(e))

    return form_data_files_new, form_data_folders_new


def log(message, flush=False):
    if flush:
        LOGGER.info("\t\t%s", message)
    else:
        LOGGER.info("\t\t%s", message)


def is_file_new(file, file_path):
    if not file["size"]:
        # If there is no size, skip this file, since it cant be downloaded
        return False


    if not os.path.exists(file_path):
        log("File changed: new: {}".format(file_path))
        return True

    file_time = int(os.path.getmtime(file_path))

    chdate = file["chdate"]
    if chdate > file_time:
        log("File changed: time: {} - {} : {}".format(chdate, file_time, file_path))
        return True

    file_size = os.path.getsize(file_path)

    size = file["size"]
    if not size == file_size:
        log("File changed: size: {} - {} : {}".format(size, file_size, file_path))
        return True

    return False


class CourseRSync:

    def __init__(self, session, workdir, root_folder, course, sync_fully, use_api):
        self.session = session
        self.workdir = workdir
        self.course_id = course["course_id"]
        self.course_save_as = get_course_save_as(course)
        self.root_folder = root_folder
        self.sync_fully = sync_fully
        self.use_api = use_api

    def download(self):
        if self.course_has_new_files(self.sync_fully):
            LOGGER.info("\tSyncing files...")
            downloaded = self.download_recursive()
            return {"synced": True, "files_downloaded": downloaded}
        else:
            LOGGER.info("\tSkipping this course...")
            return {"synced": False, "files_downloaded": 0}

    def course_has_new_files(self, sync_fully=False):
        if sync_fully:
            return True

        return self.session.check_course_new_files(self.course_id, CONFIG.last_sync)

    def download_recursive(self, folder_id=None, folder_path_relative=""):
        try:
            if self.use_api:
                form_data_files, form_data_folders = self.session.get_files_index_from_api(self.course_id,
                                                                              folder_id)
            else:
                form_data_files, form_data_folders = self.session.get_files_index(self.course_id,
                                                                              folder_id)
        except MissingPermissionFolderError:
            log("Couldn't view the following folder because of missing permissions: " + folder_path_relative)
            return 0

        form_data_files, form_data_folders = check_and_cleanup_form_data(form_data_files,
                                                                         form_data_folders, self.use_api)
        downloaded_files = 0

        for file_data in form_data_files:
            folder_absolute = os.path.join(self.root_folder, folder_path_relative)
            file_path = os.path.join(folder_absolute, file_data["name"])
            if is_file_new(file_data, file_path):
                log("Downloading: {}: {}".format(file_data["id"], file_data["name"]))

                target_file = os.path.join(self.workdir, file_data["id"])

                if not self.use_api:
                    self.session.download_file(file_data["download_url"], target_file)
                else:
                    self.session.download_file_api(file_data["id"], target_file)

                file_size = int(file_data["size"])
                target_file_size = os.path.getsize(target_file)
                if target_file_size != file_size:
                    if ARGS.v:
                        LOGGER.debug("[Debug] %s", str(form_data_files))
                    raise DownloadError("File size didn't match expected file size: " + file_path)

                file_path_base, file_path_name = os.path.split(file_path)
                if os.path.exists(file_path):
                    timestr = datetime.strftime(datetime.now(), "%Y-%m-%d_%H+%M+%S")
                    suffix = "_" + timestr + ".old"
                    new_file_path = os.path.join(file_path_base, file_path_name + suffix)
                    os.rename(file_path, new_file_path)
                else:
                    os.makedirs(file_path_base, exist_ok=True)

                if os.path.exists(file_path):
                    raise DownloadError("File exists already, even after moving it away: " +
                                        file_path)

                temp_output_path = file_path + ".part"
                try:
                    shutil.copyfile(target_file, temp_output_path)
                    os.replace(temp_output_path, file_path)
                except Exception:
                    if os.path.exists(temp_output_path):
                        os.remove(temp_output_path)
                    raise
                downloaded_files += 1

                self.session.plugins.hook("hook_file_download_successful", file_data["name"],
                                          self.course_save_as, file_path)

        for folder_data in form_data_folders:
            new_folder_path_relative = os.path.join(folder_path_relative, folder_data["name"])

            # self.log("Accessing folder: " + folder_data["id"] + ": " + folder_data["name"])
            downloaded_files += self.download_recursive(folder_data["id"], new_folder_path_relative)

        return downloaded_files
