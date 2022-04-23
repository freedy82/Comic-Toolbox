import os.path
import glob
import shutil
import re
import imagesize
from langcodes import Language
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QRect
from PIL import Image,ImageEnhance

from const import *

def find_all_languages():
	languages = []
	for file in os.listdir(os.path.join(ROOT_DIR, "languages")):
		if re.match(r"^[a-zA-Z_].*?\.qm$", file):
			file_name = get_file_name(file)
			language_full_name = Language.get(file_name).autonym()
			#print(f"{file_name}, {language_full_name}")
			language_full_name = language_full_name.replace("（"," (").replace("）",")")
			languages.append({"name":language_full_name,"file":file_name})
	sorted(languages, key=lambda language: language["name"])
	return languages

def find_all_themes():
	themes = []
	for file in os.listdir(os.path.join(ROOT_DIR, "themes")):
		if re.match(r"^[a-zA-Z_].*?\.qss$", file):
			file_name = get_file_name(file)
			themes.append({"name":file_name})
	sorted(themes, key=lambda theme: theme["name"])
	return themes

def get_number_of_images_from_folder(folder,num=1,exts=IMAGE_EXTS):
	lists = []
	for ext in exts:
		lists += glob.glob(folder + '/**/*.' + ext, recursive=True)
		if len(lists) > num:
			break
	lists.sort()
	if len(lists) > num:
		lists = lists[0:num]
	return lists

def filter_pimage(pimage,contrast=1,sharpness=1,brightness=1,color=1):
	new_pimage = pimage
	enhancer = ImageEnhance.Color(new_pimage)
	new_pimage = enhancer.enhance(color)

	enhancer = ImageEnhance.Contrast(new_pimage)
	new_pimage = enhancer.enhance(contrast)

	enhancer = ImageEnhance.Brightness(new_pimage)
	new_pimage = enhancer.enhance(brightness)

	enhancer = ImageEnhance.Sharpness(new_pimage)
	new_pimage = enhancer.enhance(sharpness)

	return new_pimage

def cv_imread(filepath):
	# # fix the utf-8 name path!
	# cv_img = cv2.imdecode(np.fromfile(filepath,dtype=np.uint8),-1)
	# #already is BGR!
	# #cv_img = cv2.cvtColor(cv_img,cv2.COLOR_RGB2BGR)
	# return cv_img
	pass

def msg_box(message,parent=None):
	QMessageBox.information(parent, TRSM("Comic Toolbox"), message)

def confirm_box(message,parent=None):
	reply = QMessageBox.question(parent, TRSM("Comic Toolbox"), message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
	if reply == QMessageBox.Yes:
		return True
	else:
		return False

def copy_all_file(from_folder,to_folder):
	for file_name in os.listdir(from_folder):
		source = os.path.join(from_folder, file_name)
		destination = os.path.join(to_folder, file_name)
		if os.path.isfile(source):
			shutil.copy(source, destination)

def get_file_name(filename):
	name = filename.split('.', 1)[0]
	return name

def get_ext(file_name):
	ext = file_name.rsplit('.', 1)[-1].lower()
	return ext

def count_file_in_folder(folder):
	path, dirs, files = next(os.walk(folder))
	return len(files)

def find_rect_to_fit(p_width,p_height,c_width,c_height):
	w_ratio = p_width / c_width
	h_ratio = p_height / c_height
	ratio = min(w_ratio,h_ratio)
	c_final_width = c_width * ratio
	c_final_height = c_height * ratio
	c_x = (p_width - c_final_width) / 2.0
	c_y = (p_height - c_final_height) / 2.0
	return QRect(c_x,c_y,c_final_width,c_final_height)

def remove_element_of_tuple(tuple_from,need_remove):
	tmp_list = list(tuple_from)
	tmp_list.remove(need_remove)
	return tuple(tmp_list)

def get_image_size(file_name):
	try:
		width, height = imagesize.get(file_name)
		if width > 0 and height > 0:
			return [width,height]
		else:
			im = Image.open(file_name)
			width, height = im.size
			if width > 0 and height > 0:
				return [width, height]
	except Exception:
		#fallback use PIL
		im = Image.open(file_name)
		width, height = im.size
		if width > 0 and height > 0:
			return [width, height]
	return [0, 0]

# # for check GPU usage
# def get_free_gpu_memory():
# 	nvmlInit()
# 	h = nvmlDeviceGetHandleByIndex(0)
# 	info = nvmlDeviceGetMemoryInfo(h)
# 	print(f'total    : {info.total}')
# 	print(f'free     : {info.free}')
# 	print(f'used     : {info.used}')
#
# 	t = torch.cuda.get_device_properties(0).total_memory
# 	r = torch.cuda.memory_reserved(0)
# 	a = torch.cuda.memory_allocated(0)
# 	f = r - a  # free inside reserved
# 	print(f't: {t}')
# 	print(f'r: {r}')
# 	print(f'a: {a}')
# 	print(f'f: {f}')
#
# 	nvidia_smi.nvmlInit()
#
# 	device_count = nvidia_smi.nvmlDeviceGetCount()
# 	for i in range(device_count):
# 		handle = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
# 		info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
# 		print("Device {}: {}, Memory : ({:.2f}% free): {}(total), {} (free), {} (used)".format(i, nvidia_smi.nvmlDeviceGetName(handle), 100*info.free/info.total, info.total, info.free, info.used))
#
# 	nvidia_smi.nvmlShutdown()

