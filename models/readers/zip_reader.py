import io
from PIL import Image
from zipfile import ZipFile
from PyQt5.QtGui import QPixmap

from models.const import *
from models import util
from models.reader import Reader

class ZipReader(Reader):
	FILE_MATCH = [".zip",".cbz"]
	FILE_FILTER = [{"name":"Comic Book Zip","filters":"*.cbz"},{"name":"Normal Zip","filters":"*.zip"}]

	name = "ZipReader"

	def __init__(self):
		super().__init__()

	def open_file(self):
		self.file_handler = ZipFile(self.main_file, "r")
		pass

	def get_file_list(self):
		if self.file_handler is None:
			self.open_file()

		results = {}
		filenames = self.file_handler.namelist()
		for full_filename in filenames:
			if util.get_ext(full_filename) in IMAGE_EXTS:
				path = os.path.dirname(full_filename)
				#filename = os.path.basename(full_filename)
				if path not in results:
					results[path] = []
				results[path].append(full_filename)

		new_results = []
		for path in results:
			files = results[path]
			files.sort()
			new_results.append({"path":path,"files":files})

		return new_results

	def get_data_from_file(self,file):
		return self.file_handler.read(file)

	def get_qpixmap_from_file(self,file):
		q_pixmap = QPixmap()
		q_pixmap.loadFromData(self.get_data_from_file(file))
		return q_pixmap

	def get_image_size(self,file):
		data = self.get_data_from_file(file)
		im = Image.open(io.BytesIO(data))
		width, height = im.size
		if width > 0 and height > 0:
			return [width, height]
		return [0, 0]
