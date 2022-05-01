import os
from pathlib import Path
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap

from models import util
from models.const import *
from models.reader import Reader
from models.controllers.reader.helper import *

class FolderReader(Reader):
	FILE_MATCH = ["NO_FILE_MATCH"]
	FILE_FILTER = []
	name = "FolderReader"

	def __init__(self):
		super().__init__()

	def open_file(self):
		pass

	@staticmethod
	def support_rotate_file_in_disk():
		return True

	def get_file_list(self):
		image_list = []
		util.get_image_list_from_folder(self.main_file,image_list,self.main_file)
		self.current_file_list = sorted(image_list, key=lambda d: d['path'])
		return self.current_file_list

	def get_data_from_file(self,file):
		full_file = Path(os.path.join(self.main_file,file)).as_posix()
		fp = open(full_file, "rb")
		data = fp.read()
		fp.close()
		return data

	def get_q_pixmap_from_file(self,file):
		full_file = Path(os.path.join(self.main_file,file)).as_posix()
		q_pixmap = QPixmap(full_file)
		return self.get_rotated_image_q_pixmap(file,q_pixmap)

	def get_image_size(self,file):
		full_file = Path(os.path.join(self.main_file,file)).as_posix()
		size = util.get_image_size(full_file)
		return self.get_rotated_image_size(file,size)

	def rotate_file(self,file,rotate:PageRotate,mode:PageRotateMode):
		if mode == PageRotateMode.MEMORY:
			super().rotate_file(file,rotate,mode)
		elif mode == PageRotateMode.FILE:
			if file != "":
				self.rotate_single_file_in_disk(file,rotate)
			else:
				for tmp_list in self.current_file_list:
					for tmp_file in tmp_list["files"]:
						self.rotate_single_file_in_disk(tmp_file, rotate)
		return True

	def rotate_single_file_in_disk(self,file,rotate:PageRotate):
		if rotate != PageRotate.ROTATE_0:
			full_file = Path(os.path.join(self.main_file,file)).as_posix()
			img = Image.open(full_file)
			img = util.rotate_pimage(img, rotate.value, False, False)
			ext = util.get_ext(full_file)

			if ext == "jpg" or ext == "jpeg":
				img = img.convert('RGB')
				img.save(full_file, quality=int(MY_CONFIG.get("general", "jpg_quality")))
			else:
				img.save(full_file)

		pass
