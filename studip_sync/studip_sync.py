import shutil
import os
import tempfile
import zipfile
import glob
import subprocess
import time
from datetime import datetime

from studip_sync.config import CONFIG
from studip_sync.session import Session, DownloadError, LoginError
from studip_sync.parsers import ParserError


class ExtractionError(Exception):
    pass


class StudipSync(object):

    def __init__(self):
        super(StudipSync, self).__init__()
        self.workdir = tempfile.mkdtemp(prefix="studip-sync")
        self.download_dir = os.path.join(self.workdir, "zips")
        self.extract_dir = os.path.join(self.workdir, "extracted")
        self.destination_dir = CONFIG.target

        os.makedirs(self.download_dir)
        os.makedirs(self.extract_dir)
        os.makedirs(self.destination_dir, exist_ok=True)

    def sync(self, sync_fully=False):
        extractor = Extractor(self.extract_dir)
        rsync = RsyncWrapper()

        with Session() as session:
            print("Logging in...")
            try:
                session.login(CONFIG.username, CONFIG.password)
            except (LoginError, ParserError):
                print("Login failed!")
                return 1

            print("Downloading course list...")
            courses = []
            try:
                courses = list(session.get_courses())
            except (LoginError, ParserError):
                print("Downloading course list failed!")
                return 1

            status_code = 0
            for i in range(0, len(courses)):
                course = courses[i]
                print("{}) {}".format(i+1, course["save_as"]))
                try:
                    if sync_fully or session.check_course_new_files(course["course_id"], CONFIG.last_sync):
                        print("\tDownloading files...")
                        zip_location = session.download(
                            course["course_id"], self.download_dir, course.get("sync_only"))
                        extractor.extract(zip_location, course["save_as"])
                    else:
                        print("\tSkipping this course...")
                except DownloadError:
                    print(" Download FAILED!")
                    status_code = 2
                except ExtractionError:
                    print(" Extracting FAILED!")
                    status_code = 2

        print("Synchronizing with existing files...")
        rsync.sync(self.extract_dir + "/", self.destination_dir)

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
        subprocess.call(["rsync", "--recursive", "--checksum", "--backup",
                         "--suffix=" + self.suffix, source, destination], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


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
