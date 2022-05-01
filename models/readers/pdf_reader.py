import fitz
import sys
import time
from PyQt5.QtGui import QPixmap
from PIL import Image, ImageQt

from models.reader import Reader

class PDFReader(Reader):
	FILE_MATCH = [".pdf"]
	FILE_FILTER = [{"name":"Portable Document Format","filters":"*.pdf"}]

	name = "PDFReader"

	def __init__(self):
		super().__init__()

	def open_file(self):
		self.file_handler = fitz.open(self.main_file)
		pass

	def get_file_list(self):
		if self.file_handler is None:
			self.open_file()

		pages = []
		for page_no in range(len(self.file_handler)):
			file_name = "Page " + str(page_no+1)
			pages.append(file_name)

		self.current_file_list = [{"path":"","files":pages}]

		return self.current_file_list

	def get_data_from_file(self,file):
		if file in self.data_buffer:
			return self.data_buffer[file]

		page_index = self.get_page_index(file)
		page = self.file_handler[page_index]
		pixmap = page.get_pixmap()
		self.data_buffer[file] = pixmap
		return pixmap

	def get_q_pixmap_from_file(self,file):
		if file in self.q_pixmap_buffer:
			return self.get_rotated_image_q_pixmap(file,self.q_pixmap_buffer[file])
		if file in self.q_img_buffer:
			q_pixmap = QPixmap.fromImage(self.q_img_buffer[file])
			self.q_pixmap_buffer[file] = q_pixmap
			return self.get_rotated_image_q_pixmap(file,q_pixmap)
		pixmap = self.get_data_from_file(file)
		mode = "RGBA" if pixmap.alpha else "RGB"
		img = Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)
		q_img = ImageQt.ImageQt(img)
		self.q_img_buffer[file] = q_img
		q_pixmap = QPixmap.fromImage(q_img)
		self.q_pixmap_buffer[file] = q_pixmap
		return self.get_rotated_image_q_pixmap(file,q_pixmap)

	def get_image_size(self,file):
		if file in self.size_buffer:
			#print(f"{file} size in buffer {self.size_buffer[file]}")
			return self.get_rotated_image_size(file,self.size_buffer[file])
		pixmap = self.get_data_from_file(file)
		size = [pixmap.width, pixmap.height]
		self.size_buffer[file] = size
		return self.get_rotated_image_size(file,size)

	@staticmethod
	def get_page_index(file):
		return int(file.replace("Page ",""))-1

