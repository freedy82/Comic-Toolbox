import math

from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image
from pathlib import Path

from models.const import *
from models import util


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
				elif self.crop_mode == 3:
					self._start_scan_un_crop_page_in_folder(folder_info)
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

	def _start_scan_un_crop_page_in_folder(self,folder):
		full_folder, filtered_files = self._get_all_image(folder)
		un_cropped_image_files = [x for x in filtered_files if not x.startswith("resized_")]

		max_width = 0
		image_sizes = []
		for file in un_cropped_image_files:
			from_file_full = os.path.join(full_folder, file)
			from_file_full = Path(from_file_full).as_posix()
			img_width, img_height = util.get_image_size(from_file_full)
			image_sizes.append([img_width, img_height])
			max_width = max(max_width,img_width)

		if max_width > 0:
			if "force_width" in self.methods["rules"][0]:
				max_width = self.methods["rules"][0]["force_width"]
			ratio = self.methods["rules"][0]["fix_w_h_ratio"]
			page_height = int(max_width / ratio)
			total_height = 0
			for image_size in image_sizes:
				total_height += math.floor(max_width/image_size[0] * image_size[1])
			total_height = int(total_height)

			# create all images into board
			final_all_image = Image.new("RGB",(max_width,total_height))
			current_y = 0
			for idx, file in enumerate(un_cropped_image_files, start=1):
				from_file_full = os.path.join(full_folder, file)
				from_file_full = Path(from_file_full).as_posix()
				tmp_img = Image.open(from_file_full)
				target_height = math.floor(max_width/tmp_img.size[0] * tmp_img.size[1])
				if tmp_img.size[0] != max_width:
					tmp_img = tmp_img.resize((max_width,target_height))
				#print(f"file:{file}-y:{current_y}, target_height:{target_height}, total_height:{total_height}",flush=True)
				final_all_image.paste(tmp_img, box=(0,current_y,max_width,current_y+target_height))
				message = TRSM("Loaded page %s (%d/%d)") % (from_file_full,idx, len(un_cropped_image_files))
				self.trigger.emit(message, self.current_action_count, self.total_action_count)
				current_y += target_height
			#final_all_image.save(os.path.join(full_folder,"resized_all.png"))
			current_y = 0
			current_index = 1
			total_pages = math.ceil(total_height/page_height)
			while current_y < total_height:
				tmp_img = final_all_image.crop((0,current_y,max_width,current_y+page_height))
				tmp_file_name = "resized_" + str(current_index).zfill(int(MY_CONFIG.get("general", "image_padding"))) + ".jpg"
				tmp_full_file_name = os.path.join(full_folder, tmp_file_name)
				tmp_full_file_name = Path(tmp_full_file_name).as_posix()
				if os.path.isfile(tmp_full_file_name) and not self.is_overwrite:
					message = TRSM("File already exist %s") % tmp_full_file_name
					self.trigger.emit(message, self.current_action_count, self.total_action_count)
				else:
					tmp_img.save(tmp_full_file_name, quality=int(MY_CONFIG.get("general", "jpg_quality")))
					message = TRSM("Generated page %s (%d/%d)") % (tmp_full_file_name,current_index, total_pages)
					self.trigger.emit(message, self.current_action_count, self.total_action_count)
				current_y += page_height
				current_index += 1
			#print(f"max_width:{max_width}")
			#print(f"page_height: {page_height}")
			#print(f"total_height: {total_height}")

			if self.is_remove_source:
				for file in un_cropped_image_files:
					from_file_full = os.path.join(full_folder, file)
					from_file_full = Path(from_file_full).as_posix()
					os.remove(from_file_full)
		else:
			message = TRSM("Can not find file to re-page in %s") % full_folder
			self.trigger.emit(message, self.current_action_count, self.total_action_count)

	def _start_scan_2_page_in_folder(self, folder):
		# full_folder = os.path.join(self.from_folder, folder)
		# full_folder = Path(full_folder).as_posix()
		#
		# files = sorted(os.listdir(full_folder))
		# filtered_files = [x for x in files if x.endswith(IMAGE_EXTS)]
		full_folder, filtered_files = self._get_all_image(folder)

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
					from_file_full = Path(from_file_full).as_posix()

					img_width, img_height = util.get_image_size(from_file_full)
					if img_width/img_height >= pages_ratio_require:
						to_file_1_full = os.path.join(self.from_folder, folder, target1)
						to_file_2_full = os.path.join(self.from_folder, folder, target2)
						to_file_1_full = Path(to_file_1_full).as_posix()
						to_file_2_full = Path(to_file_2_full).as_posix()

						task = {"from": from_file_full, "to": [to_file_1_full,to_file_2_full]}
						#print("add task",task)
						self.process_list.append(task)

	def _start_crop_in_folder(self, folder):
		# full_folder = os.path.join(self.from_folder, folder)
		# full_folder = Path(full_folder).as_posix()
		#
		# files = sorted(os.listdir(full_folder))
		# filtered_files = [x for x in files if x.endswith(IMAGE_EXTS)]
		full_folder, filtered_files = self._get_all_image(folder)

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
			full_from_file = Path(full_from_file).as_posix()
			full_to_file = Path(full_to_file).as_posix()
			if to_file not in filtered_files or self.is_overwrite:
				# take crop
				is_cropped = self._start_crop_image(full_from_file,full_to_file)
				if is_cropped:
					message = TRSM("Finish crop to %s") % full_to_file
					self.trigger.emit(message, self.current_action_count, self.total_action_count)
				else:
					if not self.is_only_get_list:
						message = TRSM("Not match rule to crop %s") % full_from_file
						self.trigger.emit(message, self.current_action_count, self.total_action_count)
			elif to_file in filtered_files:
				message = TRSM("Cover file already exist %s") % full_to_file
				self.trigger.emit(message, self.current_action_count, self.total_action_count)
		else:
			message = TRSM("Can not find file to crop in %s") % full_folder
			self.trigger.emit(message, self.current_action_count, self.total_action_count)

		#print(final_cover)
		pass

	def _get_all_image(self,folder):
		full_folder = os.path.join(self.from_folder, folder)
		full_folder = Path(full_folder).as_posix()

		files = sorted(os.listdir(full_folder))
		filtered_files = [x for x in files if x.endswith(IMAGE_EXTS)]
		return full_folder,filtered_files

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
