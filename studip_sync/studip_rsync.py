
from datetime import datetime
import os
import shutil
import tempfile
import time

from studip_sync.config import CONFIG
from studip_sync.session import Session, DownloadError, LoginError, MissingFeatureError, \
    MissingPermissionFolderError
from studip_sync.parsers import ParserError


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

    def sync(self, sync_fully=False, sync_recent=False):
        with Session() as session:
            print("Logging in...")
            try:
                session.login(CONFIG.username, CONFIG.password)
            except (LoginError, ParserError) as e:
                print("Login failed!")
                print(e)
                return 1

            print("Downloading course list...")

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
                print("{}) {}: {}".format(i + 1, course["semester"], course["save_as"]))

                if self.files_destination_dir:
                    try:
                        CourseRSync(self.files_destination_dir, session, self.workdir, course, sync_fully).download()
                    except MissingFeatureError as e:
                        # Ignore if there are no files
                        pass
                    except DownloadError as e:
                        print("\tDownload of files failed: " + str(e))
                        status_code = 2
                        raise e

                if self.media_destination_dir:
                    try:
                        print("\tSyncing media files...")

                        media_course_dir = os.path.join(self.media_destination_dir,
                                                        course["save_as"])

                        session.download_media(course["course_id"], media_course_dir)
                    except MissingFeatureError as e:
                        # Ignore if there is no media
                        pass
                    except DownloadError as e:
                        print("\tDownload of media failed: " + str(e))
                        status_code = 2
                        raise e

        if self.files_destination_dir and status_code == 0:
            CONFIG.update_last_sync(int(time.time()))

        return status_code

    def cleanup(self):
        shutil.rmtree(self.workdir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()


class CourseRSync:

    def __init__(self, files_destination, session, workdir, course, sync_fully):
        self.session = session
        self.workdir = workdir
        self.course_id = course["course_id"]
        self.course_save_as = course["save_as"]
        self.root_folder = os.path.join(files_destination, self.course_save_as)
        self.sync_fully = sync_fully

    def download(self):
        if self.course_has_new_files(self.sync_fully):
            print("\tSyncing files...")
            self.download_recursive()
        else:
            print("\tSkipping this course...")

    def course_has_new_files(self, sync_fully=False):
        if sync_fully:
            return True

        return self.session.check_course_new_files(self.course_id, CONFIG.last_sync)

    def log(self, message, flush=False):
        if flush:
            print("\t\t" + message, end="\r", flush=True)
        else:
            print("\t\t" + message)

    def download_recursive(self, folder_id=None, folder_path_relative=""):
        try:
            form_data_files, form_data_folders = self.session.get_files_index(self.course_id, folder_id)
        except MissingPermissionFolderError as e:
            self.log("Couldn't view the following folder because of missing permissions: " + folder_path_relative)
            return

        # TODO: Sanitize session data !!!

        for file_data in form_data_files:
            folder_absolute = os.path.join(self.root_folder, folder_path_relative)
            file_path = os.path.join(folder_absolute, file_data["name"])
            if self.is_file_new(file_data, file_path):
                self.log("Downloading: {}: {}".format(file_data["id"], file_data["name"]))

                download_url = file_data["download_url"]
                tempfile = os.path.join(self.workdir, file_data["id"])
                self.session.download_file(download_url, tempfile)

                file_size = int(file_data["size"])
                tempfile_size = os.path.getsize(tempfile)
                if tempfile_size != file_size:
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
                    raise DownloadError("File exists already, even after moving it away: " + file_path)

                shutil.copyfile(tempfile, file_path)



        for folder_data in form_data_folders:
            new_folder_path_relative = os.path.join(folder_path_relative, folder_data["name"])

            # self.log("Accessing folder: " + folder_data["id"] + ": " + folder_data["name"])
            self.download_recursive(folder_data["id"], new_folder_path_relative)

    def is_file_new(self, file, file_path):
        if not file["size"]:
            # If there is no size, skip this file, since it cant be downloaded
            return False

        try:
            chdate = int(file["chdate"])
            size = int(file["size"])
        except ValueError as e:
            print(file)
            raise ParserError("File attributes are invalid")

        if not os.path.exists(file_path):
            self.log("File changed: new: {}".format(file_path))
            return True

        file_size = os.path.getsize(file_path)
        file_time = int(os.path.getmtime(file_path))

        if chdate > file_time:
            self.log("File changed: time: {} - {} : {}".format(chdate, file_time, file_path))
            return True

        if not size == file_size:
            self.log("File changed: size: {} - {} : {}".format(size, file_size, file_path))
            return True

        return False

