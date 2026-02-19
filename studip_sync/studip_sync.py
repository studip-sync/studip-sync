import shutil
import os
import tempfile
import zipfile
import glob
import subprocess
import time
from datetime import datetime

from studip_sync.cli_ui import format_banner, format_controls_hint, format_course_header, \
    format_status_line, format_summary_line
from studip_sync.config import CONFIG
from studip_sync.course_list_store import save_course_list
from studip_sync.course_paths import get_course_save_as
from studip_sync.logins import LoginError
from studip_sync.log import get_logger
from studip_sync.plugins.plugins import PLUGINS
from studip_sync.runtime_controls import RuntimeControls, UserAbortError
from studip_sync.session import Session, DownloadError, MissingFeatureError, SessionError
from studip_sync.parsers import ParserError
from studip_sync.sync_report import build_sync_report, write_sync_report

LOGGER = get_logger(__name__)


class ExtractionError(Exception):
    pass


class StudipSync(object):

    def __init__(self):
        super(StudipSync, self).__init__()
        self.workdir = tempfile.mkdtemp(prefix="studip-sync")
        self.download_dir = os.path.join(self.workdir, "zips")
        self.extract_dir = os.path.join(self.workdir, "extracted")
        self.files_destination_dir = CONFIG.files_destination
        self.media_destination_dir = CONFIG.media_destination

        os.makedirs(self.download_dir)
        os.makedirs(self.extract_dir)
        if self.files_destination_dir and not CONFIG.dry_run:
            os.makedirs(self.files_destination_dir, exist_ok=True)
        if self.media_destination_dir and not CONFIG.dry_run:
            os.makedirs(self.media_destination_dir, exist_ok=True)

    def sync(self, sync_fully=False, sync_recent=False):
        PLUGINS.hook("hook_start")
        LOGGER.info("%s", format_banner("legacy", sync_fully, sync_recent, CONFIG.dry_run))
        stats = {
            "courses_total": 0,
            "courses_file_synced": 0,
            "courses_file_would_sync": 0,
            "courses_file_skipped": 0,
            "files_downloaded": 0,
            "files_would_download": 0,
            "media_downloaded": 0,
            "media_would_download": 0,
            "errors": 0
        }
        status_code = 0
        aborted = False
        controls = RuntimeControls(enabled=True)

        extractor = Extractor(self.extract_dir)
        rsync = RsyncWrapper()

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

            if CONFIG.save_course_list and not CONFIG.dry_run:
                try:
                    path = save_course_list(courses, CONFIG.config_dir)
                    LOGGER.info("Saved course list to: %s", path)
                except OSError as e:
                    LOGGER.warning("Failed to save course list: %s", e)
            elif CONFIG.save_course_list and CONFIG.dry_run:
                LOGGER.info("Dry-run: skipping course_list.json write")

            if sync_recent:
                LOGGER.info("Syncing only the most recent semester!")

            stats["courses_total"] = len(courses)
            controls_enabled = controls.start()
            LOGGER.info("%s", format_controls_hint(controls_enabled))
            checkpoint = controls.checkpoint if controls_enabled else None

            try:
                for i in range(0, len(courses)):
                    if checkpoint:
                        checkpoint()

                    course = courses[i]
                    course_save_as = get_course_save_as(course)
                    LOGGER.info("%s", format_course_header(i + 1, len(courses), course_save_as))

                    if self.files_destination_dir:
                        try:
                            if sync_fully or session.check_course_new_files(course["course_id"], CONFIG.last_sync):
                                if CONFIG.dry_run:
                                    LOGGER.info("%s", format_status_line("files", "changed (dry-run)",
                                                                         state="ok"))
                                    stats["courses_file_would_sync"] += 1
                                else:
                                    zip_location = session.download(
                                        course["course_id"], self.download_dir, course.get("sync_only"))
                                    extracted_dir = extractor.extract(zip_location, course_save_as)
                                    extracted_count = extractor.count_files(extracted_dir)
                                    stats["files_downloaded"] += extracted_count
                                    stats["courses_file_synced"] += 1
                                    LOGGER.info("%s", format_status_line(
                                        "files",
                                        "downloaded={}".format(extracted_count),
                                        state="ok"
                                    ))
                            else:
                                LOGGER.info("%s", format_status_line("files", "skipped", state="warn"))
                                stats["courses_file_skipped"] += 1
                        except MissingFeatureError:
                            LOGGER.info("%s", format_status_line("files", "unavailable", state="warn"))
                        except UserAbortError:
                            raise
                        except DownloadError as e:
                            LOGGER.error("%s", format_status_line("files", "failed ({})".format(e),
                                                                  state="error"))
                            status_code = 2
                            stats["errors"] += 1
                        except ExtractionError as e:
                            LOGGER.error("%s", format_status_line(
                                "files", "extract failed ({})".format(e), state="error"
                            ))
                            status_code = 2
                            stats["errors"] += 1

                    if self.media_destination_dir:
                        try:
                            if checkpoint:
                                checkpoint()

                            media_course_dir = os.path.join(self.media_destination_dir, course_save_as)
                            media_stats = session.download_media(
                                course["course_id"],
                                media_course_dir,
                                course_save_as,
                                dry_run=CONFIG.dry_run,
                                checkpoint=checkpoint
                            )
                            stats["media_downloaded"] += media_stats["downloaded"]
                            stats["media_would_download"] += media_stats["would_download"]
                            state = "warn" if media_stats["failed"] else "ok"
                            LOGGER.info("%s", format_status_line(
                                "media",
                                "total={}, existing={}, downloaded={}, would_download={}, failed={}".format(
                                    media_stats["total"], media_stats["existing"], media_stats["downloaded"],
                                    media_stats["would_download"], media_stats["failed"]
                                ),
                                state=state
                            ))
                        except MissingFeatureError:
                            LOGGER.info("%s", format_status_line("media", "unavailable", state="warn"))
                        except UserAbortError:
                            raise
                        except DownloadError as e:
                            LOGGER.error("%s", format_status_line("media", "failed ({})".format(e),
                                                                  state="error"))
                            status_code = 2
                            stats["errors"] += 1
                        except ParserError as e:
                            LOGGER.error("%s", format_status_line("media", "failed ({})".format(e),
                                                                  state="error"))
                            status_code = 2
                            stats["errors"] += 1
            except UserAbortError:
                aborted = True
                status_code = 130
                LOGGER.warning("Sync aborted by user.")
            except KeyboardInterrupt:
                aborted = True
                status_code = 130
                LOGGER.warning("Sync interrupted (Ctrl+C).")
            finally:
                controls.stop()

        if self.files_destination_dir and status_code != 130 and not CONFIG.dry_run:
            LOGGER.info("Synchronizing with existing files...")
            rsync.sync(self.extract_dir + "/", self.files_destination_dir)

            if status_code == 0:
                CONFIG.update_last_sync(int(time.time()))
        elif self.files_destination_dir and CONFIG.dry_run:
            LOGGER.info("Dry-run: skipping rsync and last_sync update")

        LOGGER.info("%s", format_summary_line(status_code, stats, aborted=aborted))
        LOGGER.info("%s", format_status_line(
            "summary",
            "file_skipped={}, files_would_download={}, media_would_download={}".format(
                stats["courses_file_skipped"], stats["files_would_download"],
                stats["media_would_download"]
            ),
            state="info"
        ))

        if CONFIG.report_json_path:
            report = build_sync_report(
                mode="legacy",
                status_code=status_code,
                sync_fully=sync_fully,
                sync_recent=sync_recent,
                dry_run=CONFIG.dry_run,
                use_api=False,
                stats=stats,
                aborted=aborted
            )
            try:
                write_sync_report(CONFIG.report_json_path, report)
                LOGGER.info("Wrote sync report to: %s", CONFIG.report_json_path)
            except OSError as e:
                LOGGER.warning("Failed to write sync report: %s", e)

        return status_code

    def cleanup(self):
        shutil.rmtree(self.workdir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()


# pylint: disable=too-few-public-methods
class RsyncWrapper(object):

    def __init__(self):
        super(RsyncWrapper, self).__init__()
        timestr = datetime.strftime(datetime.now(), "%Y-%m-%d_%H+%M+%S")
        self.suffix = "_" + timestr + ".old"

    def sync(self, source, destination):
        subprocess.call(["rsync", "--recursive", "--checksum", "--backup", "-v",
                         "--suffix=" + self.suffix, source, destination])


class Extractor(object):

    def __init__(self, basedir):
        super(Extractor, self).__init__()
        self.basedir = basedir

    @staticmethod
    def remove_intermediary_dir(extracted_dir):
        def _filter_dirs(base_name):
            return os.path.isdir(os.path.join(extracted_dir, base_name))

        subdirs = list(filter(_filter_dirs, os.listdir(extracted_dir)))
        if len(subdirs) == 1:
            intermediary = os.path.join(extracted_dir, subdirs[0])
            for filename in glob.iglob(os.path.join(intermediary, "*")):
                shutil.move(filename, extracted_dir)
            os.rmdir(intermediary)

    @staticmethod
    def remove_empty_dirs(directory):
        for root, dirs, files in os.walk(directory):
            if not dirs and not files:
                os.rmdir(root)

    @staticmethod
    def remove_filelist(directory):
        filelist = os.path.join(directory, "archive_filelist.csv")
        if os.path.isfile(filelist):
            os.remove(filelist)

    @staticmethod
    def count_files(directory):
        file_count = 0
        for _, _, files in os.walk(directory):
            file_count += len(files)
        return file_count

    def extract(self, archive_filename, destination, cleanup=True):
        try:
            with zipfile.ZipFile(archive_filename, "r") as archive:
                destination = os.path.join(self.basedir, destination)
                archive.extractall(destination)
                if cleanup:
                    self.remove_filelist(destination)
                    self.remove_intermediary_dir(destination)
                    self.remove_empty_dirs(destination)

                return destination
        except zipfile.BadZipFile:
            raise ExtractionError("Cannot extract file {}".format(archive_filename))
