__all__ = ['Plugin']

import os.path

from studip_sync.helpers import JSONConfig
from studip_sync.plugins import PluginBase
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/tasks']

class CredsError(PermissionError):
    pass

class PluginConfig(JSONConfig):

    @property
    def task_list_id(self):
        if not self.config:
            return

        return self.config.get("task_list_id")

class Plugin(PluginBase):

    def __init__(self, config_path):
        super(Plugin, self).__init__("google-tasks", config_path, PluginConfig)
        self.token_pickle_path = os.path.join(self.config_dir, "token.pickle")
        self.credentials_path = os.path.join(self.config_dir, "credentials.json")

    def hook_configure(self):
        super(Plugin, self).hook_configure()

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.

        if os.path.exists(self.token_pickle_path):
            with open(self.token_pickle_path, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise CredsError("Missing credentials.json at " + self.credentials_path)

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_pickle_path, 'wb') as token:
                pickle.dump(creds, token)

        service = build('tasks', 'v1', credentials=creds)

        # Call the Tasks API
        results = service.tasklists().list(maxResults=10).execute()
        items = results.get('items', [])

        if not items:
            print("No task lists found. Please create a task list online to use!")
            return 1

        print("Task lists:")
        for item in items:
            print(u'{0} ({1})'.format(item['title'], item['id']))

        task_list_id = input("Please select a task list id to use: ")

        if task_list_id not in [item['id'] for item in items]:
            print("Invalid task id! Please select a task if from the list.")
            return 1

        config = {"task_list_id": task_list_id}

        self.save_plugin_config(config)

    def hook_start(self):
        super(Plugin, self).hook_start()

        creds = None

        if os.path.exists(self.token_pickle_path):
            with open(self.token_pickle_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise CredsError("tasks: couldn't log in")

        self.service = build('tasks', 'v1', credentials=creds)

    def hook_media_download_successful(self, filename, course_save_as):
        return self.insert_new_task(filename, course_save_as)

    def insert_new_task(self, title, description):
        body = {
            "status": "needsAction",
            "kind": "tasks#task",
            "title": title,  # Title of the task.
            "deleted": False,
            "notes": description,  # Notes describing the task. Optional.
            "hidden": False,
        }

        return self.service.tasks().insert(tasklist=self.config.task_list_id, body=body).execute()


