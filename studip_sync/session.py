import os
import shutil
import time

import requests

from studip_sync import parsers


class SessionError(Exception):
    pass

class FileError(Exception):
    pass

class LoginError(SessionError):
    pass

class MissingFeatureError(Exception):
    pass

class MissingPermissionFolderError(Exception):
    pass

class DownloadError(SessionError):
    pass


class URL(object):
    @staticmethod
    def login_page():
        return "https://studip.uni-goettingen.de"

    @staticmethod
    def files_main():
        return "https://studip.uni-goettingen.de/dispatch.php/course/files"

    @staticmethod
    def files_index(folder_id):
        return "https://studip.uni-goettingen.de/dispatch.php/course/files/index/{}".format(folder_id)

    @staticmethod
    def files_flat():
        return "https://studip.uni-goettingen.de/dispatch.php/course/files/flat"

    @staticmethod
    def bulk_download(folder_id):
        return "https://studip.uni-goettingen.de/dispatch.php/file/bulk/{}".format(folder_id)

    @staticmethod
    def studip_main():
        return "https://studip.uni-goettingen.de/dispatch.php/start"

    @staticmethod
    def courses():
        return "https://studip.uni-goettingen.de/dispatch.php/my_courses"

    @staticmethod
    def mediacast_list():
        return "https://studip.uni-goettingen.de/plugins.php/mediacastplugin/media/index"


class Session(object):

    def __init__(self):
        super(Session, self).__init__()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "WeWantFileSync"})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.__exit__()

    def login(self, username, password):
        with self.session.get(URL.login_page()) as response:
            if not response.ok:
                raise LoginError("Cannot access Stud.IP login page")
            login_data = parsers.extract_login_data(response.text)

        login_params_auth = {
            "loginname": username,
            "password": password
        }

        login_params = {**login_params_auth, **login_data['params']}

        with self.session.post(login_data['action'], data=login_params) as response:
            if not response.ok:
                raise LoginError("Cannot post login data")
            elif "messagebox_error" in response.text:
                raise LoginError("Wrong credentials, cannot login")

        #Test if logged in
        with self.session.post(URL.studip_main()) as response:
            if not response.ok or not "Veranstaltungen" in response.text:
                raise LoginError("Cannot access Stud.IP main page")

    def get_courses(self, only_recent_semester=False):
        with self.session.get(URL.courses()) as response:
            if not response.ok:
                raise SessionError("Failed to get courses")

            return parsers.extract_courses(response.text, only_recent_semester)

    def check_course_new_files(self, course_id, last_sync):
        params = {"cid": course_id}

        with self.session.get(URL.files_flat(), params=params) as response:
            if not response.ok:
                if response.status_code == 403 and "Documents" in response.text:
                    raise MissingFeatureError("This course has no files")
                else:
                    raise DownloadError("Cannot access course files_flat page")
            last_edit = parsers.extract_files_flat_last_edit(response.text)

        if last_edit == 0:
            print("\tLast file edit couldn't be detected!")
        else:
            print("\tLast file edit: {}".format(time.strftime("%d.%m.%Y %H:%M", time.gmtime(last_edit))))
        return last_edit == 0 or last_edit > last_sync

    def download(self, course_id, workdir, sync_only=None):
        params = {"cid": course_id}

        with self.session.get(URL.files_main(), params=params) as response:
            if not response.ok:
                raise DownloadError("Cannot access course files page")
            folder_id = parsers.extract_parent_folder_id(response.text)
            csrf_token = parsers.extract_csrf_token(response.text)

        download_url = URL.bulk_download(folder_id)
        data = {
            "security_token": csrf_token,
            # "parent_folder_id": folder_id,
            "ids[]": sync_only or folder_id,
            "download": 1
        }

        with self.session.post(download_url, params=params, data=data, stream=True) as response:
            if not response.ok:
                raise DownloadError("Cannot download course files")
            path = os.path.join(workdir, course_id)
            with open(path, "wb") as download_file:
                shutil.copyfileobj(response.raw, download_file)
                return path

    def download_file(self, download_url, tempfile):
        with self.session.post(download_url, stream=True) as response:
            if not response.ok:
                raise DownloadError("Cannot download file")

            with open(tempfile, "wb") as file:
                shutil.copyfileobj(response.raw, file)

    def get_files_index(self, course_id, folder_id=None):
        params = {"cid": course_id}

        if folder_id:
            url = URL.files_index(folder_id)
        else:
            url = URL.files_main()

        with self.session.get(url, params=params) as response:
            if not response.ok:
                if response.status_code == 403 and "Documents" in response.text:
                    raise MissingFeatureError("This course has no files")
                elif response.status_code == 403 and "Zugriff verweigert" in response.text:
                    raise MissingPermissionFolderError("You are missing the required pemissions to view this folder")
                else:
                    raise DownloadError("Cannot access course files/files_index page")
            return parsers.extract_files_index_data(response.text)

    def download_media(self, course_id, media_workdir):
        params = {"cid": course_id}

        mediacast_list_url = URL.mediacast_list()

        with self.session.get(mediacast_list_url, params=params) as response:
            if not response.ok:
                if response.status_code == 500 and "not found" in response.text:
                    raise MissingFeatureError("This course has no media")
                else:
                    raise DownloadError("Cannot access mediacast list page")

            media_files = parsers.extract_media_list(response.text)

        os.makedirs(media_workdir, exist_ok=True)

        workdir_files = os.listdir(media_workdir)

        print("\tFound {} media files".format(len(media_files)))

        for media_file in media_files:
            media_hash = media_file[0]
            media_player_url_relative = media_file[1]
            media_player_url = requests.compat.urljoin(mediacast_list_url, media_player_url_relative)

            # files are saved as "{hash}-{filename}"

            found_existing_file = False

            for workdir_filename in workdir_files:
                workdir_filename_split = workdir_filename.split("-")
                if len(workdir_filename_split) > 0 and workdir_filename_split[0] == media_hash:
                    found_existing_file = True
                    break

            # Skip this file if it already exists
            if found_existing_file:
                continue

            print("\t\tDownloading " + media_hash)

            with self.session.get(media_player_url) as response:
                if not response.ok:
                    raise DownloadError("Cannot access media file page: " + media_hash)

                download_media_url_relative = parsers.extract_media_best_download_link(response.text)

                download_media_url = requests.compat.urljoin(media_player_url, download_media_url_relative)


            with self.session.get(download_media_url, stream=True) as response:
                if not response.ok:
                    print("\t\tCannot download media file: " + str(response))
                    continue

                media_filename = parsers.extract_filename_from_headers(response.headers)

                filename = media_hash + "-" + media_filename

                filepath = os.path.join(media_workdir, filename)

                if os.path.exists(filepath):
                    raise FileError("Cannot access filepath since file already exists: " + filepath)

                with open(filepath, "wb") as download_file:
                    shutil.copyfileobj(response.raw, download_file)
