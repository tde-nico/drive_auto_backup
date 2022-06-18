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

PYTHON_ALIAS = "py"

CURRENT_FOLDER = os.getcwd()
LOCAL_FOLDER = "backup"

DELAY = 10


def signal_handler(sig, frame):
	print("CTRL + C")
	raise KeyboardInterrupt()



def get_creds():
	creds = None
	if os.path.exists(f"{CURRENT_FOLDER}/token.json"):
		creds = Credentials.from_authorized_user_file(f"{CURRENT_FOLDER}/token.json", SCOPES)
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				f"{CURRENT_FOLDER}/{CREDENTIALS}", SCOPES)
			creds = flow.run_local_server(port=0)
		with open(f"{CURRENT_FOLDER}/token.json", "w") as token:
			token.write(creds.to_json())
	return creds


def get_folder_id(service, folder):
	responce = service.files().list(
		q="name='" + folder + "' and mimeType='application/vnd.google-apps.folder'",
		spaces="drive"
	).execute()
	if not responce['files']:
		file_metadata = {
			"name": folder,
			"mimeType": "application/vnd.google-apps.folder"
		}
		file = service.files().create(body=file_metadata, fields="id").execute()
		return file.get("id")
	return responce["files"][0]["id"]


def upload_file(service, folder, folder_id, file):
	file_metadata = {
		"name": file,
		"parents": [folder_id],
	}
	media = MediaFileUpload(f"{folder}/{file}")
	uploaded_file = service.files().create(
		body=file_metadata,
		media_body=media,
		fields="id"
	).execute()


def update_file(service, folder, data):
	name = data[0]["name"]
	file_metadata = {
		"name": name,
	}
	media = MediaFileUpload(f"{folder}/{name}")
	updated_file = service.files().update(
		body=file_metadata,
		media_body=media,
		fileId=data[0]["id"]
	).execute()


def check_presence(service, file):
	responce = service.files().list(
		q=f"name='{file}'",
		spaces="drive"
	).execute()
	if not responce['files']:
		return None
	return responce['files']



class Handler(FileSystemEventHandler):
	def __init__(self, service, folder, folder_id):
		self.service = service
		self.folder = folder
		self.folder_id = folder_id
		self.modified_files = set()
		self.ignored_folders = set()
		self.sub_pids = []
		self.timer = 0


	def push(self, *args):
		for file in self.modified_files:
			try:
				responce = check_presence(self.service, file)
				if not responce:
					upload_file(self.service, self.folder, self.folder_id, file)
					print("Backed up file: " + file)
				else:
					update_file(self.service, self.folder, responce)
					print("Updated up file: " + file)
			except HttpError as e:
				print("Error:" + str(e))
		self.modified_files.clear()
		self.timer = 0


	def on_any_event(self, event):
		print(f"{self.folder}: {event}")
		if event.event_type not in ("created", "modified", "moved"):
			return
		file = event.src_path[len(self.folder)+1:]
		if event.is_directory:
			if file in self.ignored_folders:
				return
			self.ignored_folders.add(file)
			self.sub_pids.append(subprocess.Popen(f"{PYTHON_ALIAS} {__file__} {event.src_path}", shell=True).pid)
			return
		self.modified_files.add(file)
		if self.timer:
			return
		t = Timer(DELAY, self.push, [DELAY])
		t.start()
		self.timer = 1


	def stop_sub_processes(self):
		for sub_prcss in self.sub_pids:
			os.kill(sub_prcss, signal.SIGINT)



def main(folder):
	signal.signal(signal.SIGINT, signal_handler)
	creds = get_creds()
	try:
		service = build("drive", "v3", credentials=creds)
		folder_id = get_folder_id(service, folder)
		observer = Observer()
		handler = Handler(service, folder, folder_id)
		observer.schedule(handler, folder)
		observer.start()
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			handler.stop_sub_processes()
			observer.stop()
		observer.join()
	except HttpError as e:
		print("Error:" + str(e))





if __name__ == "__main__":
	if len(sys.argv) > 1:
		LOCAL_FOLDER = sys.argv[1]
		print(f"{LOCAL_FOLDER}: Start")
		os.chdir(LOCAL_FOLDER)
		os.chdir("..")
		LOCAL_FOLDER = LOCAL_FOLDER.split("\\")[-1]
	else:
		print(f"{LOCAL_FOLDER}: Start")
	main(LOCAL_FOLDER)
	print(f"{LOCAL_FOLDER}: Stop")
