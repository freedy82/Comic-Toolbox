import os
import re
import importlib

from PyQt5.QtCore import QThread, pyqtSignal

import util
import fitz

class Reader(QThread):
	FILE_MATCH = []
	FILE_FILTER = []
	main_file = ""
	file_handler = None
	name = ""

	def __init__(self):
		super().__init__()

	def set_main_file(self, new_main_file):
		self.main_file = new_main_file

	def open_file(self):
		#todo open the file handler
		pass

	def get_file_list(self):
		return [[]]

	def get_data_from_file(self,file):
		return None

	def get_qpixmap_from_file(self,file):
		return None

	def get_image_size(self,file):
		return 0,0

	@staticmethod
	def find_all_readers_class():
		for file in os.listdir(os.path.join(os.path.dirname(__file__), "readers")):
			if re.match(r"^[a-zA-Z].*?\.py$", file) and file != "empty.py":
				importlib.import_module(".readers.{}".format(file.split(".")[0]), __package__)
		return [reader_class for reader_class in Reader.__subclasses__()]

	@classmethod
	def get_all_readers_object(cls):
		results = []
		all_readers_class = cls.find_all_readers_class()
		for reader_class in all_readers_class:
			results.append(reader_class())
		return results

	@classmethod
	def init_reader_by_file(cls,file):
		all_readers_class = cls.find_all_readers_class()
		for reader_class in all_readers_class:
			if reader_class.is_support_file_from_this_reader(file=file):
				reader_obj = reader_class()
				reader_obj.set_main_file(file)
				return reader_obj
		return None

	@classmethod
	def init_folder_reader(cls,folder):
		all_readers_class = cls.find_all_readers_class()
		for reader_class in all_readers_class:
			if reader_class.name == "FolderReader":
				reader_obj = reader_class()
				reader_obj.set_main_file(folder)
				return reader_obj
		return None

	@classmethod
	def is_support_file_from_this_reader(cls,file):
		ext = util.get_ext(file)
		if "."+ext in cls.FILE_MATCH:
			return True
		return False
