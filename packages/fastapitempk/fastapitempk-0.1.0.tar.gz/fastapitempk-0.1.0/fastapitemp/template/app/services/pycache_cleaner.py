import os 
import shutil 
import sys 

def remove_pycaches_and_pycs(directory):
	for root, dirs, files, in os.walk(directory):
		if "__pycache__" in dirs:
				pycache_dir = os.path.join(root, "__pycache__")
				shutil.rmtree(pycache_dir)

		for file in files:
			if file.endswith(".pyc") or file.endswith(".pyo"):
				file_path = os.path.join(root, file)
				os.remove(file_path)