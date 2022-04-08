import glob
#import os
#from pathlib import Path
import shutil
from PIL import Image

from PyQt5.QtCore import QThread, pyqtSignal

import util
from const import *

class ConverterWorker(QThread):
	trigger = pyqtSignal(str,int,int)
	finished = pyqtSignal()
	canceled = pyqtSignal()

	def __init__(self,from_folder,to_folder,from_exts,to_ext,is_overwrite,remove_source,sub_folders,is_use_filter=False):
		super().__init__()
		self.from_folder = from_folder
		self.to_folder = to_folder
		self.from_exts = from_exts
		self.to_ext = to_ext
		self.is_overwrite = is_overwrite
		self.remove_source = remove_source
		self.current_action_count = 0
		self.total_action_count = 0
		self.paths_created = []
		self.stop_flag = True
		self.sub_folders = sub_folders
		self.is_use_filter = is_use_filter

	def run(self):
		self.stop_flag = False
		self.trigger.emit(TRSM("Scanning files, please wait"),0,0)
		self.paths_created = []

		#make sure first level folder was created
		# folders = os.listdir(self.from_folder)
		# folders.sort()
		# for folder in folders:
		# 	if os.path.isdir(os.path.join(self.from_folder,folder)) and not os.path.isdir(os.path.join(self.to_folder,folder)):
		# 		Path(os.path.join(self.to_folder,folder)).mkdir(parents=True, exist_ok=True)
		for folder in self.sub_folders:
			if not os.path.isdir(os.path.join(self.to_folder,folder)):
				Path(os.path.join(self.to_folder,folder)).mkdir(parents=True, exist_ok=True)

		need_convert_lists = []
		not_need_convert_lists = []
		for from_ext in self.from_exts:
			for folder in self.sub_folders:
				need_convert_lists += glob.glob(self.from_folder + '/'+folder+'/**/*.' + from_ext, recursive=True)
		if self.to_ext not in self.from_exts:
			for folder in self.sub_folders:
				not_need_convert_lists += glob.glob(self.from_folder + '/'+folder+'/**/*.' + self.to_ext, recursive=True)
		else:
			not_need_convert_lists = []

		self.current_action_count = 0
		if self.from_folder == self.to_folder:
			self.total_action_count = len(need_convert_lists)
		else:
			self.total_action_count = len(need_convert_lists) + len(not_need_convert_lists)

		message = TRSM("Need convert: %d, not need convert: %d") % (len(need_convert_lists),len(not_need_convert_lists))
		self.trigger.emit(message,self.current_action_count,self.total_action_count)

		self.paths_created = []

		for tmp_file in need_convert_lists:
			if not self.stop_flag:
				self._image_file_action(tmp_file,is_force_convert=True)

		if self.from_folder != self.to_folder:
			for tmp_file in not_need_convert_lists:
				if not self.stop_flag:
					self._image_file_action(tmp_file)

		if self.stop_flag:
			self.canceled.emit()
		else:
			self.finished.emit()

	def stop(self):
		self.stop_flag = True

	#internal
	def _image_file_action(self,tmp_file,is_force_convert=False):
		to_file_with_path = os.path.relpath(tmp_file, self.from_folder)
		full_target_file = os.path.join(self.to_folder, to_file_with_path)
		ext = util.get_ext(full_target_file)
		full_target_file = full_target_file.replace("." + ext, "." + self.to_ext)
		target_path = Path(full_target_file).parent.absolute()
		if target_path not in self.paths_created:
			Path(target_path).mkdir(parents=True, exist_ok=True)
			self.paths_created.append(target_path)

		if not os.path.exists(full_target_file) or self.is_overwrite:
			if ext == self.to_ext and tmp_file != full_target_file and not is_force_convert:
				shutil.copy(tmp_file, full_target_file)
				message = TRSM("Copied to %s") % full_target_file
			else:
				img = Image.open(tmp_file)
				if self.is_use_filter:
					contrast = float(MY_CONFIG.get("filter", "contrast"))
					sharpness = float(MY_CONFIG.get("filter", "sharpness"))
					brightness = float(MY_CONFIG.get("filter", "sharpness"))
					color = float(MY_CONFIG.get("filter", "color"))
					img = util.filter_pimage(img,contrast,sharpness,brightness,color)

				if self.to_ext == "jpg":
					img.save(full_target_file, quality=int(MY_CONFIG.get("general", "jpg_quality")))
				else:
					img.save(full_target_file)
				message = TRSM("Converted to %s") % full_target_file
				if self.remove_source:
					os.remove(tmp_file)
		else:
			message = TRSM("Skipped of %s") % full_target_file

		self.current_action_count += 1
		self.trigger.emit(message, self.current_action_count, self.total_action_count)
