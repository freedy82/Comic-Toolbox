import fitz
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image, ImageQt

from models.reader import Reader

class PDFReader(Reader):
	FILE_MATCH = [".pdf"]
	FILE_FILTER = [{"name":"Portable Document Format","filters":"*.pdf"}]

	name = "PDFReader"
	pixmap_buffer = {}
	size_buffer = {}
	qimg_buffer = {}
	qpixmap_buffer = {}

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
			#print(f"page no {page_no}")
			#file_name = str(page_no+1).zfill(5)+".png"
			file_name = "Page " + str(page_no+1)
			pages.append(file_name)
			page = self.file_handler[page_no]
			pixmap = page.get_pixmap()
			# below convert failed in some pdf!
			#fmt = QImage.Format_RGBA8888 if pixmap.alpha else QImage.Format_RGB888
			#print(f"image width:{pixmap.width}, height:{pixmap.height}, fmt: {fmt}")
			#q_img = QImage(pixmap.samples_ptr, pixmap.width, pixmap.height, fmt)

			mode = "RGBA" if pixmap.alpha else "RGB"
			img = Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)
			q_img = ImageQt.ImageQt(img)

			#print(f"mark d page no {page_no}")
			#print(f"q_img:{q_img}")
			try:
				q_pixmap = QPixmap.fromImage(q_img)
			except Exception as exc:
				print('Convert PDF to image failed %s' % exc)
			#print(f"mark 1 page no {page_no}")

			self.pixmap_buffer[file_name] = pixmap
			self.size_buffer[file_name] = [pixmap.width, pixmap.height]
			self.qimg_buffer[file_name] = q_img
			self.qpixmap_buffer[file_name] = q_pixmap
			#print(f"mark 5 page no {page_no}")

		#print(self.size_buffer)

		new_results = [{"path":"","files":pages}]

		return new_results

	def get_data_from_file(self,file):
		#page_no = int(file.replace(".png",""))
		#page = self.file_handler[page_no]
		#return page.get_pixmap()
		return self.pixmap_buffer[file]

	def get_qpixmap_from_file(self,file):
		if file in self.qpixmap_buffer:
			return self.qpixmap_buffer[file]
		return None

	def get_image_size(self,file):
		if file in self.size_buffer:
			return self.size_buffer[file]
		return [0, 0]



