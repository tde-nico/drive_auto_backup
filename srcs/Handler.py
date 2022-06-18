from srcs.settings import *
from srcs.google_api import *


class Handler(FileSystemEventHandler):

	def __init__(self, service, folder_path, folder_id):
		self.service = service
		self.folder_path = folder_path
		self.folder = folder_path.split("\\")[-1]
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
					upload_file(self.service, self.folder_path, self.folder_id, file)
					if VERBOSE_LEVEL:
						print("Backed up file: " + file)
				else:
					update_file(self.service, self.folder_path, responce)
					if VERBOSE_LEVEL:
						print("Updated up file: " + file)
			except HttpError as e:
				print("Error:" + str(e))
		self.modified_files.clear()
		self.timer = 0


	def on_any_event(self, event):
		if VERBOSE_LEVEL >= 2:
			print(f"{self.folder}: {event}")
		if event.event_type not in ("created", "modified", "moved"):
			return
		file = event.src_path[len(self.folder_path)+1:]
		if event.is_directory:
			if file in self.ignored_folders:
				return
			self.ignored_folders.add(file)
			main = os.getcwd() + "/main.py"
			self.sub_pids.append(subprocess.Popen(f"{PYTHON_ALIAS} {main} {event.src_path}", shell=True).pid)
			return
		self.modified_files.add(file)
		if self.timer:
			return
		t = Timer(DELAY, self.push, [DELAY])
		t.start()
		self.timer = 1


	def stop_sub_processes(self):
		for sub_prcss in self.sub_pids:
			try:
				os.kill(sub_prcss, signal.SIGINT)
			except OSError as e:
				if VERBOSE_LEVEL:
					print("Error: " + str(e))

