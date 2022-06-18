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

		self.sub_folders = dict()


	def create_folder(self, path, file):
		#print(self.sub_folders)
		if file in self.sub_folders.keys() or not path:
			return
		parents = None
		folders = path.split("\\")
		#print(path, file)
		if len(folders):
			self.create_folder("\\".join(folders[:-1]), folders[-1])
			parents = [get_folder_id(self.service, folders[-1])]
		#print(file, parents)
		folder_id = get_folder_id(self.service, file, parents)
		#print(folder_id)
		self.sub_folders[file] = {"id": folder_id, "parents": parents}


	def push(self, *args):
		for file_path in self.modified_files:
			try:
				folders = file_path.split("\\")
				current_folder_path = "/".join(folders[:-1])
				self.create_folder("\\".join(folders[:-2]), folders[-2])
				parent = self.sub_folders.get(folders[-2], get_folder_id(self.service, folders[-2])).get("id")
				file = folders[-1]
				responce = check_presence(self.service, file)
				if not responce:
					upload_file(self.service, current_folder_path, parent, file)
					if VERBOSE_LEVEL:
						print("Backed up file: " + file)
				else:
					update_file(self.service, current_folder_path, responce)
					if VERBOSE_LEVEL:
						print("Updated file: " + file)
			except HttpError as e:
				if VERBOSE_LEVEL:
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
			if event.event_type == "modified":
				return
			self.create_folder(event.src_path, file)
			return
		#if event.is_directory:
			#if file in self.ignored_folders:
			#	return
			#self.ignored_folders.add(file)
			#main = os.getcwd() + "/main.py"
			#self.sub_pids.append(subprocess.Popen(f"{PYTHON_ALIAS} {main} {event.src_path}", shell=True).pid)
		#	return
		self.modified_files.add(event.src_path)
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

