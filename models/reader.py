import os
import re
import importlib

from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal

from models import util
from models.const import *
from models.controllers.reader.helper import *
#import fitz

class Reader(QThread):
	FILE_MATCH = []
	FILE_FILTER = []
	main_file = ""
	file_handler = None
	name = ""
	current_file_list = []
	rotate_setting_buffer = {}

	data_buffer = {}
	size_buffer = {}
	q_img_buffer = {}
	q_pixmap_buffer = {}

	def __init__(self):
		super().__init__()
		self.data_buffer = {}
		self.size_buffer = {}
		self.q_img_buffer = {}
		self.q_pixmap_buffer = {}
		self.rotate_setting_buffer = {}

	def set_main_file(self, new_main_file):
		self.main_file = new_main_file

	def open_file(self):
		#todo open the file handler
		pass

	def get_file_list(self):
		return [[]]

	def get_data_from_file(self,file):
		return None

	def get_q_pixmap_from_file(self,file):
		return None

	def get_image_size(self,file):
		return 0,0

	def get_rotated_image_size(self,file,size):
		target_angle = 0
		if file in self.rotate_setting_buffer and self.rotate_setting_buffer[file] != 0:
			target_angle = self.rotate_setting_buffer[file]
		if target_angle == 90 or target_angle == 270:
			return size[::-1]
		return size

	def get_rotated_image_q_pixmap(self,file,q_pixmap):
		target_angle = 0
		if file in self.rotate_setting_buffer and self.rotate_setting_buffer[file] != 0:
			target_angle = self.rotate_setting_buffer[file]
		if target_angle > 0:
			q_pixmap = q_pixmap.transformed(QtGui.QTransform().rotate(target_angle))
		return q_pixmap

	def rotate_file(self,file,rotate:PageRotate,mode:PageRotateMode):
		if mode == PageRotateMode.MEMORY:
			if file != "":
				self.rotate_single_file_in_memory(file, rotate)
			else:
				for tmp_list in self.current_file_list:
					for tmp_file in tmp_list["files"]:
						self.rotate_single_file_in_memory(tmp_file, rotate)
			#print(self.rotate_setting_buffer)
		return True

	def rotate_single_file_in_memory(self,file,rotate:PageRotate):
		old_rotate = 0
		if file in self.rotate_setting_buffer:
			old_rotate = self.rotate_setting_buffer[file]
		rotate = (old_rotate + rotate.value) % 360
		self.rotate_setting_buffer[file] = rotate

	@staticmethod
	def support_rotate_file_in_disk():
		return False

	@staticmethod
	def get_all_supported_filter_string():
		reader_objs = Reader.get_all_readers_object()
		all_support_file_filter_list = []
		other_support_file_filter_list = []
		for reader_obj in reader_objs:
			file_filters = reader_obj.FILE_FILTER
			for file_filter in file_filters:
				all_support_file_filter_list.append(file_filter["filters"])
				other_support_file_filter_list.append(TRSM(file_filter["name"]) + " (" + file_filter["filters"] + ")")
		other_support_file_filter_string = ";;".join(other_support_file_filter_list)
		all_support_file_filter_string = TRSM("All supported format") + " (" + " ".join(all_support_file_filter_list) + ")"
		final_filter_string = all_support_file_filter_string + ";;" + other_support_file_filter_string
		return final_filter_string

	@staticmethod
	def find_all_readers_class():
		for file in os.listdir(os.path.join(os.path.dirname(__file__), "readers")):
			if re.match(r"^[a-zA-Z].*?\.py(c)?$", file):
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
