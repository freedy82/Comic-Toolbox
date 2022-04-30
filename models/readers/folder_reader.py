from PyQt5.QtGui import QPixmap

from models import util
from models.reader import Reader


class FolderReader(Reader):
	FILE_MATCH = ["NO_FILE_MATCH"]
	FILE_FILTER = []
	name = "FolderReader"

	def __init__(self):
		super().__init__()

	def open_file(self):
		pass

	def get_file_list(self):
		image_list = []
		util.get_image_list_from_folder(self.main_file,image_list)
		image_list = sorted(image_list, key=lambda d: d['path'])
		return image_list

	def get_data_from_file(self,file):
		fp = open(file, "rb")
		data = fp.read()
		fp.close()
		return data

	def get_qpixmap_from_file(self,file):
		return QPixmap(file)

	def get_image_size(self,file):
		return util.get_image_size(file)
