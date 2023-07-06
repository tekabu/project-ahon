import os

def count_folders(path):
	folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
	# print(folders)
	count = len(folders)
	return count

def count_files(path):
	files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
	# print(files)
	count = len(files)
	return count

def create_folder(path):
	if not os.path.isdir(path):
		os.makedirs(path)