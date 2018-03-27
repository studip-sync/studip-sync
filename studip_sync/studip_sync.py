import shutil
import os
import tempfile
import zipfile
import glob
import subprocess
from datetime import datetime

import requests

from studip_sync import parsers
from studip_sync.config import config


class LoginError(Exception):
    pass


class DownloadError(Exception):
    pass

class ExtractionError(Exception):
    pass


class StudipSync(object):

    def __init__(self):
        super(StudipSync, self).__init__()
        self.workdir = tempfile.mkdtemp(prefix="studip-sync")
        self.download_dir = os.path.join(self.workdir, "zips")
        self.extract_dir = os.path.join(self.workdir, "extracted")
        self.destination_dir = config.target

        os.makedirs(self.download_dir)
        os.makedirs(self.extract_dir)
        os.makedirs(self.destination_dir, exist_ok=True)

    def sync(self):
        extractor = Extractor(self.extract_dir)
        rsync = RsyncWrapper()

        with Downloader(self.download_dir) as downloader:
            print("Logging in...")
            downloader.login(config.username, config.password)
            for course in config.courses:
                print("Downloading '{}'...".format(course["save_as"]), end="", flush=True)
                try:
                    zip_location = downloader.download(course["course_id"], course.get("sync_only"))
                    extractor.extract(zip_location, course["save_as"])
                except DownloadError:
                    print(" Download FAILED!", end="")
                except ExtractionError:
                    print(" Extracting FAILED!", end="")
                finally:
                    print()

        print("Synchronizing with existing files...")
        rsync.sync(self.extract_dir + "/", self.destination_dir)

    def cleanup(self):
        shutil.rmtree(self.workdir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()


class RsyncWrapper(object):

    def __init__(self):
        super(RsyncWrapper, self).__init__()
        timestr = datetime.strftime(datetime.now(), "%Y-%m-%d_%H+%M+%S")
        self.suffix = "_" + timestr + ".old"

    def sync(self, source, destination):
        subprocess.call(["rsync", "--recursive", "--checksum", "--backup", "--suffix=" + self.suffix,
                         source, destination])


class Extractor(object):

    def __init__(self, basedir):
        super(Extractor, self).__init__()
        self.basedir = basedir

    @staticmethod
    def remove_intermediary_dir(extracted_dir):
        def _filter_dirs(d):
            return os.path.isdir(os.path.join(extracted_dir, d))

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

    def extract(self, archive_filename, destination, cleanup=True):
        try:
            with zipfile.ZipFile(archive_filename, "r") as z:
                destination = os.path.join(self.basedir, destination)
                z.extractall(destination)
                if cleanup:
                    self.remove_intermediary_dir(destination)
                    self.remove_empty_dirs(destination)

                return destination
        except zipfile.BadZipFile:
            raise ExtractionError("Cannot extract file {}".format(archive_filename))


class Downloader(object):

    def __init__(self, workdir):
        super(Downloader, self).__init__()
        self.workdir = workdir

        self.session = requests.Session()
        self.csrf_token = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.__exit__()

    def login(self, username, password):
        with self.session.get("https://studip.uni-passau.de/studip/index.php?again=yes&sso=shib") as r:
            if not r.ok:
                raise LoginError("Cannot access Stud.IP login page")
            sso_url = "https://sso.uni-passau.de" + parsers.extract_sso_url(r.text)

        login_data = {
            "j_username": username,
            "j_password": password,
            "donotcache": 1,
            "_eventId_proceed": ""
        }

        with self.session.post(sso_url, data=login_data) as r:
            if not r.ok:
                raise LoginError("Cannot access SSO server")
            saml_data = parsers.extract_saml_data(r.text)

        with self.session.post("https://studip.uni-passau.de/Shibboleth.sso/SAML2/POST", data=saml_data) as r:
            if not r.ok:
                raise LoginError("Cannot access Stud.IP main page")
            self.csrf_token = parsers.extract_csrf_token(r.text)

    def download(self, course_id, sync_only=None):
        params = {"cid": course_id}

        with self.session.get("https://studip.uni-passau.de/studip/dispatch.php/course/files", params=params) as r:
            if not r.ok:
                raise DownloadError("Cannot access course files page")
            folder_id = parsers.extract_parent_folder_id(r.text)

        url = "https://studip.uni-passau.de/studip/dispatch.php/file/bulk/" + folder_id
        data = {
            "security_token": self.csrf_token,
            # "parent_folder_id": folder_id,
            "ids[]": sync_only or folder_id,
            "download": 1
        }

        with self.session.post(url, params=params, data=data, stream=True) as r:
            if not r.ok:
                raise DownloadError("Cannot download course files")
            path = os.path.join(self.workdir, course_id)
            with open(path, "wb") as f:
                shutil.copyfileobj(r.raw, f)
                return path
