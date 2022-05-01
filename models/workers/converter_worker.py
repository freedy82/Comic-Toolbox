import glob
import shutil
#import os
from PIL import Image
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

from models import util
from models.const import *

class ConverterWorker(QThread):
	trigger = pyqtSignal(str,int,int)
	finished = pyqtSignal()
	canceled = pyqtSignal()

	def __init__(self,from_folder,to_folder,from_exts,to_ext,is_overwrite,remove_source,sub_folders,is_use_filter=False,enable_real_cugan=False):
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
		self.enable_real_cugan = enable_real_cugan

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
		tmp_file = Path(tmp_file).as_posix()

		to_file_with_path = os.path.relpath(tmp_file, self.from_folder)
		full_target_file = os.path.join(self.to_folder, to_file_with_path)
		ext = util.get_ext(full_target_file)
		full_target_file = full_target_file.replace("." + ext, "." + self.to_ext)
		target_path = Path(full_target_file).parent.absolute()
		if target_path not in self.paths_created:
			Path(target_path).mkdir(parents=True, exist_ok=True)
			self.paths_created.append(target_path)

		full_target_file = Path(full_target_file).as_posix()

		if not os.path.exists(full_target_file) or self.is_overwrite:
			if self.enable_real_cugan:
				real_cugan_exe = MY_CONFIG.get("real-cugan", "exe_location")
				real_cugan_scale = MY_CONFIG.get("real-cugan", "scale")
				real_cugan_denoise = MY_CONFIG.get("real-cugan", "denoise_level")
				if real_cugan_exe != "":
					cmd = real_cugan_exe + " -s " + real_cugan_scale + " -n " + real_cugan_denoise + " "
					cmd += "-i \"" + tmp_file + "\" -o \"" + full_target_file + "\" -f " + self.to_ext
					#os.system(cmd)
					si = subprocess.STARTUPINFO()
					si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
					si.wShowWindow = subprocess.SW_HIDE # default
					subprocess.call(cmd, startupinfo=si)
					tmp_file = full_target_file

			if ext == self.to_ext and tmp_file != full_target_file and not is_force_convert:
				shutil.copy(tmp_file, full_target_file)
				message = TRSM("Copied to %s") % full_target_file
			else:
				#if (self.enable_real_cugan and self.is_use_filter) or not self.enable_real_cugan:
				img = Image.open(tmp_file)
				if self.is_use_filter:
					contrast = float(MY_CONFIG.get("filter", "contrast"))
					sharpness = float(MY_CONFIG.get("filter", "sharpness"))
					brightness = float(MY_CONFIG.get("filter", "sharpness"))
					color = float(MY_CONFIG.get("filter", "color"))
					img = util.filter_pimage(img,contrast,sharpness,brightness,color)
					rotate = int(MY_CONFIG.get("filter", "rotate"))
					is_horizontal_flip = MY_CONFIG.get("filter", "horizontal_flip") == "True"
					is_vertical_flip = MY_CONFIG.get("filter", "vertical_flip") == "True"
					img = util.rotate_pimage(img, rotate*90, is_horizontal_flip, is_vertical_flip)

				if self.enable_real_cugan:
					if MY_CONFIG.get("real-cugan", "resize") == "1":
						real_cugan_scale = int(MY_CONFIG.get("real-cugan", "scale"))
						width, height = img.size
						new_size = (width//real_cugan_scale, height//real_cugan_scale)
						img = img.resize(new_size)

				if self.to_ext == "jpg":
					img = img.convert('RGB')
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
