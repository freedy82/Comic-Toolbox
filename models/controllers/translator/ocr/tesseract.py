import cv2
import numpy as np
import pytesseract
from PyQt5.QtCore import QRect
from pytesseract import Output

from models.controllers.translator.OCR import OCREngine

class TesseractOCREngine(OCREngine):
	original_image = None

	def __init__(self):
		super(TesseractOCREngine, self).__init__()

	def load_image(self,file_name):
		self.original_image = cv2.imdecode(np.fromfile(file_name, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

	def ocr_image_with_area_frame(self,area_frame:QRect,lang=""):
		img = self.original_image[area_frame.y():area_frame.y()+area_frame.height(), area_frame.x():area_frame.x()+area_frame.width()]
		img = self._preprocess_for_ocr(img)
		if lang.endswith("_vert"):
			psm_mode = "5"
		else:
			psm_mode = "6"

		data = pytesseract.image_to_data(img, lang=lang, config='--psm '+psm_mode, output_type=Output.DICT)
		ocr_text = self._get_string_info_from_data(data)
		ocr_text = ocr_text.strip()
		return ocr_text

	@staticmethod
	def _preprocess_for_ocr(img_array):
		img = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
		return img

	@staticmethod
	def _get_string_info_from_data(data):
		total_line = max(data["line_num"]) + 1
		lines = [""] * total_line
		for idx, text in enumerate(data["text"]):
			cnf = float(data["conf"][idx])
			line_num = data["line_num"][idx]
			if cnf > 20:
				lines[line_num] += text
		lines = [value for value in lines if value != ""]
		all_line_str = "\n".join(lines)
		return all_line_str
