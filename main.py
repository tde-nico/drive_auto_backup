from srcs.settings import *
from srcs.Handler import Handler
from srcs.google_api import *


def signal_handler(sig, frame):
	if VERBOSE_LEVEL >= 3:
		print("CTRL + C")
	raise KeyboardInterrupt()


def track_folder(service, folder_path):
	folders = folder_path.split("\\")
	parents = None
	if len(folders) > 1:
		parents = [get_folder_id(service, folders[-2])]
	folder = folders[-1]

	folder_id = get_folder_id(service, folder, parents)
	observer = Observer()
	handler = Handler(service, folder_path, folder_id)
	observer.schedule(handler, folder_path, recursive=True)
	observer.start()
	return observer


def main(folders):
	if VERBOSE_LEVEL >= 2:
		for folder in folders:
			print(f"{folder}: Start")

	signal.signal(signal.SIGINT, signal_handler)
	creds = get_creds()
	observers = []
	try:
		service = build("drive", "v3", credentials=creds)

		for folder in folders:
			observers.append(track_folder(service, folder))

		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			for observer in observers:
				observer.stop()
		for observer in observers:
			observer.join()

	except HttpError as e:
		if VERBOSE_LEVEL:
			print("Error:" + str(e))
	
	if VERBOSE_LEVEL >= 2:
		for folder in folders:
			print(f"{folder}: Stop")


if __name__ == "__main__":
	if len(sys.argv) > 1:
		FOLDERS = sys.argv[1:]
	main(FOLDERS)
