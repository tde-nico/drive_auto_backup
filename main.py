from srcs.settings import *
from srcs.Handler import Handler
from srcs.google_api import *


def signal_handler(sig, frame):
	if VERBOSE_LEVEL >= 3:
		print("CTRL + C")
	raise KeyboardInterrupt()


def main(folder_path):
	folders = folder_path.split("\\")
	parents = None
	signal.signal(signal.SIGINT, signal_handler)
	creds = get_creds()

	try:
		service = build("drive", "v3", credentials=creds)

		if len(folders) > 1:
			parents = [get_folder_id(service, folders[-2])]
		folder = folders[-1]

		folder_id = get_folder_id(service, folder, parents)
		observer = Observer()
		handler = Handler(service, folder_path, folder_id)
		observer.schedule(handler, folder_path, recursive=True)
		observer.start()

		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			handler.stop_sub_processes()
			observer.stop()
		observer.join()

	except HttpError as e:
		if VERBOSE_LEVEL:
			print("Error:" + str(e))


if __name__ == "__main__":
	if len(sys.argv) > 1:
		LOCAL_FOLDER = sys.argv[1]
	if VERBOSE_LEVEL >= 2:
		print(f"{LOCAL_FOLDER}: Start")
	main(LOCAL_FOLDER)
	if VERBOSE_LEVEL >= 2:
		print(f"{LOCAL_FOLDER}: Stop")
