import os
import os.path
import time
import subprocess
import signal
import sys
from threading import Timer

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS = "credentials.json"

FOLDERS = ["backup_1", "backup_2"]
# folders to track

DELAY = 10
# delay between the event and the backup

VERBOSE_LEVEL = 3
# level 0 = no verbose
# level 1 = upload, update and errors
# level 2 = level 1 + start, stop, events
# level 3 = level 2 + signals

