import shutil
import os
import tempfile
import zipfile
import glob
import subprocess
import time
from datetime import datetime

from studip_sync.config import CONFIG
from studip_sync.session import Session, DownloadError, LoginError, MissingFeatureError
from studip_sync.parsers import ParserError


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
        if self.files_destination_dir:
            os.makedirs(self.files_destination_dir, exist_ok=True)
        if self.media_destination_dir:
            os.makedirs(self.media_destination_dir, exist_ok=True)

    def sync(self, sync_fully=False, sync_recent=False):
        extractor = Extractor(self.extract_dir)
        rsync = RsyncWrapper()

        with Session(CONFIG.base_url) as session:
            print("Logging in...")
            try:
                session.login(CONFIG.username, CONFIG.password)
            except (LoginError, ParserError) as e:
                print("Login failed!")
                print(e)
                return 1

            print("Downloading course list...")

            courses = []
            try:
                courses = list(session.get_courses(sync_recent))
            except (LoginError, ParserError) as e:
                print("Downloading course list failed!")
                print(e)
                return 1

            if sync_recent:
                print("Syncing only the most recent semester!")

            status_code = 0
            for i in range(0, len(courses)):
                course = courses[i]
                print("{}) {}: {}".format(i+1, course["semester"], course["save_as"]))

                if self.files_destination_dir:
                    try:
                        if sync_fully or session.check_course_new_files(course["course_id"], CONFIG.last_sync):
                            print("\tDownloading files...")
                            zip_location = session.download(
                                course["course_id"], self.download_dir, course.get("sync_only"))
                            extractor.extract(zip_location, course["save_as"])
                        else:
                            print("\tSkipping this course...")
                    except MissingFeatureError as e:
                        # Ignore if there are no files
                        pass
                    except DownloadError as e:
                        print("\tDownload of files failed: " + str(e))
                        status_code = 2
                    except ExtractionError as e:
                        print("\tExtracting files failed: " + str(e))
                        status_code = 2

                if self.media_destination_dir:
                    try:
                        print("\tSyncing media files...")

                        media_course_dir = os.path.join(self.media_destination_dir, course["save_as"])

                        session.download_media(course["course_id"], media_course_dir)
                    except MissingFeatureError as e:
                        # Ignore if there is no media
                        pass
                    except DownloadError as e:
                        print("\tDownload of media failed: " + str(e))
                        status_code = 2

        if self.files_destination_dir:
            print("Synchronizing with existing files...")
            rsync.sync(self.extract_dir + "/", self.files_destination_dir)

            if status_code == 0:
                CONFIG.update_last_sync(int(time.time()))

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
