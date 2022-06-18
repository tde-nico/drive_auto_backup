from srcs.settings import *


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


def get_folder_id(service, folder, parents=None):
	responce = service.files().list(
		q="name='" + folder + "' and mimeType='application/vnd.google-apps.folder'",
		spaces="drive"
	).execute()
	if not responce['files']:
		file_metadata = {
			"name": folder,
			"mimeType": "application/vnd.google-apps.folder"
		}
		if parents:
			file_metadata["parents"] = parents
		file = service.files().create(body=file_metadata, fields="id").execute()
		if VERBOSE_LEVEL:
			print(f"Created folder: {folder}")
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

