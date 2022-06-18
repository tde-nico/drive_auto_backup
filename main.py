import os
import os.path
import time
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

LOCAL_FOLDER = "backup"

DELAY = 10


def get_creds():
	creds = None
	if os.path.exists("token.json"):
		creds = Credentials.from_authorized_user_file("token.json", SCOPES)
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				CREDENTIALS, SCOPES)
			creds = flow.run_local_server(port=0)
		with open("token.json", "w") as token:
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
		print(event)
		if event.event_type not in ("created", "modified", "moved"):
			return
		if event.is_directory:
			print("dir")
			return
		file = event.src_path[len(self.folder)+1:]
		self.modified_files.add(file)
		if self.timer:
			return
		t = Timer(DELAY, self.push, [DELAY])
		t.start()
		self.timer = 1



def main(folder):
	creds = get_creds()
	try:
		service = build("drive", "v3", credentials=creds)
		folder_id = get_folder_id(service, folder)
		observer = Observer()
		observer.schedule(Handler(service, folder, folder_id), folder)
		observer.start()
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			observer.stop()
		observer.join()
	except HttpError as e:
		print("Error:" + str(e))
	


if __name__ == "__main__":
	main(LOCAL_FOLDER)
