import glob
import shutil
import util
from const import *
from PIL import Image

from PyQt5.QtCore import QThread, pyqtSignal

class CropperWorker(QThread):
	trigger = pyqtSignal(str,int,int)
	finished = pyqtSignal()
	canceled = pyqtSignal()

	def __init__(self,from_folder,methods,is_overwrite,is_remove_source,sub_folders):
		super().__init__()
		self.stop_flag = True
		self.from_folder = from_folder
		self.is_overwrite = is_overwrite
		self.methods = methods
		self.current_action_count = 0
		self.total_action_count = 0
		self.folders_need_crop = []
		self.is_only_get_list = False
		self.is_remove_source = is_remove_source
		self.sub_folders = sub_folders
		self.crop_mode = 1
		self.process_list = []

	def run(self):
		self.stop_flag = False
		self.process_list = []
		self.trigger.emit(TRSM("Start checking, please wait"),0,0)
		self.current_action_count = 0
		self.total_action_count = 0

		#self.folders_need_crop = self._scan_sub_folder()
		self.folders_need_crop = self.sub_folders

		if not self.is_only_get_list:
			self.trigger.emit(TRSM("Starting crop cover"),0,len(self.folders_need_crop))

		if len(self.folders_need_crop) > 0:
			self.total_action_count = len(self.folders_need_crop)
			for idx, folder_info in enumerate(self.folders_need_crop, start=1):
				if self.stop_flag:
					break
				if self.crop_mode == 1:
					self._start_crop_in_folder(folder_info)
				elif self.crop_mode == 2:
					self._start_scan_2_page_in_folder(folder_info)
				self.current_action_count += 1
				if not self.stop_flag and not self.is_only_get_list:
					message = TRSM("Finish %s") % folder_info
					self.trigger.emit(message,self.current_action_count,self.total_action_count)

		if self.stop_flag:
			self.canceled.emit()
		else:
			self.finished.emit()

	def set_is_only_get_list(self,is_only_get_list):
		self.is_only_get_list = is_only_get_list

	def get_is_only_get_list(self):
		return self.is_only_get_list

	def set_crop_mode(self,crop_mode):
		self.crop_mode = crop_mode

	def get_crop_mode(self):
		return self.crop_mode

	def get_process_list(self):
		return self.process_list

	def stop(self):
		self.stop_flag = True

	def _scan_sub_folder(self):
		folders = os.listdir(self.from_folder)
		folders.sort()
		final_folders = []
		for folder in folders:
			if os.path.isdir(os.path.join(self.from_folder,folder)):
				final_folders.append(folder)
		return final_folders

	def _start_scan_2_page_in_folder(self, folder):
		full_folder = os.path.join(self.from_folder, folder)
		files = sorted(os.listdir(full_folder))
		exts = ('.gif', '.png', '.jpg', '.jpeg', '.webp')
		filtered_files = [x for x in files if x.endswith(exts)]
		pages_ratio_require = float(MY_CONFIG.get("general", "check_is_2_page"))
		for file in filtered_files:
			tmp_ext = util.get_ext(file)
			tmp_name = file.replace("."+tmp_ext,"")
			#print("check file %s" % file)
			if tmp_name.endswith((".1",".2")):
				#print("is already split sub page")
				continue
			else:
				target1 = tmp_name + ".1." + tmp_ext
				target2 = tmp_name + ".2." + tmp_ext
				if (target1 in filtered_files or target2 in filtered_files) and not self.is_overwrite:
					message = TRSM("%s already have split sub page!") % file
					self.trigger.emit(message, self.current_action_count, self.total_action_count)
				else:
					# check image ratio
					from_file_full = os.path.join(self.from_folder, folder, file)
					img_width, img_height = util.get_image_size(from_file_full)
					if img_width/img_height >= pages_ratio_require:
						to_file_1_full = os.path.join(self.from_folder, folder, target1)
						to_file_2_full = os.path.join(self.from_folder, folder, target2)
						task = {"from": from_file_full, "to": [to_file_1_full,to_file_2_full]}
						#print("add task",task)
						self.process_list.append(task)

	def _start_crop_in_folder(self, folder):
		full_folder = os.path.join(self.from_folder, folder)
		files = sorted(os.listdir(full_folder))
		exts = ('.gif', '.png', '.jpg', '.jpeg', '.webp')
		filtered_files = [x for x in files if x.endswith(exts)]
		# get the first file not start with "0"
		from_file = ""
		to_file = ""
		for file in filtered_files:
			tmp_ext = util.get_ext(file)
			tmp_name = file.replace("."+tmp_ext,"")
			if tmp_name != "0".zfill(len(tmp_name)):
				from_file = file
				to_file = "0".zfill(len(tmp_name)) + "." + tmp_ext
				break

		if from_file != "" and to_file != "":
			full_from_file = os.path.join(self.from_folder, folder, from_file)
			full_to_file = os.path.join(self.from_folder, folder, to_file)
			if to_file not in files or self.is_overwrite:
				# take crop
				is_cropped = self._start_crop_image(full_from_file,full_to_file)
				if is_cropped:
					message = TRSM("Finish crop to %s") % full_to_file
					self.trigger.emit(message, self.current_action_count, self.total_action_count)
				else:
					if not self.is_only_get_list:
						message = TRSM("Not match rule to crop %s") % full_from_file
						self.trigger.emit(message, self.current_action_count, self.total_action_count)
			elif to_file in files:
				message = TRSM("Cover file already exist %s") % full_to_file
				self.trigger.emit(message, self.current_action_count, self.total_action_count)
		else:
			message = TRSM("Can find file to crop in %s") % full_folder
			self.trigger.emit(message, self.current_action_count, self.total_action_count)

		#print(final_cover)
		pass

	def _start_crop_image(self,from_file,to_file):
		if self.is_only_get_list:
			self.process_list.append({"from":from_file,"to":[to_file]})
			return False
		img = Image.open(from_file)
		width, height = img.size
		ratio = width / height
		#print(f"start crop image {from_file} to {to_file}")
		#print(self.methods)

		for rule in self.methods["rules"]:
			if rule["wh_ratio_from"] <= ratio <= rule["wh_ratio_to"]:
				ext = util.get_ext(to_file)
				#print("found method")
				img = img.crop((int(rule["crop_x1"] * width), int(rule["crop_y1"] * height), int(rule["crop_x2"] * width), int(rule["crop_y2"] * height)))
				if ext in ("jpg","jpeg"):
					img.save(to_file, quality=int(MY_CONFIG.get("general", "jpg_quality")))
				else:
					img.save(to_file)
				if self.is_remove_source:
					os.remove(from_file)
				return True

		#print("can not found method")
		return False
