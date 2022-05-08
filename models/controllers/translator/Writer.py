from PIL import Image,ImageFont, ImageDraw
from PyQt5.QtCore import QRect

from .helper import *

class Writer(object):
	image = None
	draw = None
	test_word = "國"
	max_try_font_size = 200

	def __init__(self):
		super(Writer, self).__init__()

	def load_image_from_file(self,file):
		self.image = Image.open(file)
		self.draw = ImageDraw.Draw(self.image)

	def get_result_image(self):
		return self.image

	def fill_background(self,area,color):
		self.draw.rectangle(area, fill=color)

	def write_text(self,text,is_vertical=True,frame=QRect(0,0,0,0),font_name="",font_size=0,alignment=Alignment.LINE_START,text_style=Style.WHITE_BG_BLACK_TEXT,gap=0.1):
		x0 = frame.x()
		y0 = frame.y()
		frame_width = frame.width()
		frame_height = frame.height()
		x1 = x0 + frame_width
		y1 = y0 + frame_height
		if text != "":
			if text_style == Style.BLACK_BG_WHITE_TEXT:
				text_color = (255,255,255)
				self.fill_background((x0, y0, x1, y1), (0,0,0))
			elif text_style == Style.NO_BG_BLACK_TEXT:
				text_color = (0,0,0)
			elif text_style == Style.NO_BG_WHITE_TEXT:
				text_color = (255,255,255)
			else:
				text_color = (0, 0, 0)
				self.fill_background((x0, y0, x1, y1), (255, 255, 255))

			final_font_size = Writer._get_final_font_size(
				text, frame_width, frame_height, gap, font_name, font_size,is_vertical
			)
			#print(f"final_font_size {final_font_size}")
			write_area_width,write_area_height,write_area_line_space,write_area_gap = Writer._get_multi_line_size(text,font_name,final_font_size,is_vertical,gap)
			#print(f"write_area_width {write_area_width},write_area_width {write_area_height}")
			font = ImageFont.truetype(font_name, final_font_size)
			write_area_x0, write_area_y0,write_area_x1,write_area_y1 = Writer._get_write_area_pos(x0,y0,x1,y1,write_area_width,write_area_height)
			#print(f"write_area: {write_area_x0}, {write_area_y0}, {write_area_x1}, {write_area_y1}")
			self.start_write_text(
				text,font,font_name,final_font_size,text_color,write_area_x0,write_area_y0,write_area_x1,write_area_y1,
				write_area_line_space,write_area_gap,is_vertical,alignment
			)
			#print(f"finish draw text:{text}",flush=True)

	def start_write_text(self,text,font,font_name,font_size,text_color,write_area_x0,write_area_y0,write_area_x1,write_area_y1,write_area_line_space,write_area_gap,is_vertical,alignment):
		text_data = self._convert_line_text_to_array(text)
		for i in range(text_data["row"]):
			if is_vertical:
				line_x1 = write_area_x1 - (write_area_line_space + write_area_gap) * i
				line_x0 = line_x1 - write_area_line_space
				line_y0 = write_area_y0
				line_y1 = write_area_y1
				#print(f"line {line_x0}, {line_y0}, {line_x1}, {line_y1}")
				self.start_write_vertical_line_text(text_data["word_data"][i],font,font_name,font_size,text_color,line_x0,line_y0,line_x1,line_y1,alignment)
			else:
				line_x0 = write_area_x0
				line_x1 = write_area_x1
				line_y0 = write_area_y0 + (write_area_line_space + write_area_gap) * i
				line_y1 = line_y0 + write_area_line_space
				self.start_write_horizontal_line_text(text_data["line_data"][i],font,font_name,font_size,text_color,line_x0,line_y0,line_x1,line_y1,alignment)

	def start_write_vertical_line_text(self,text_list,font,font_name,font_size,text_color,x0,y0,x1,y1,alignment):
		real_line_width, real_line_height = Writer._get_single_line_size(text_list,font_name,font_size,is_vertical=True)
		word_width, word_height = Writer._get_word_size(font_name,font_size)
		if alignment == Alignment.LINE_MIDDLE:
			y0 = int(y0 + ((y1-y0) - real_line_height) / 2)
		if alignment == Alignment.LINE_END:
			y0 = y1 - real_line_height
		#todo handle well of text weight
		for word_idx, word in enumerate(text_list):
			self.draw.text(
				(x0 + (x1-x0)/2, y0 + word_idx * word_height + word_height / 2),
				word, fill=text_color, font=font, anchor="mm", stroke_width=0, stroke_fill=(150,150,150)
			)

	def start_write_horizontal_line_text(self, text, font, font_name, font_size, text_color, x0, y0, x1, y1, alignment):
		real_line_width, real_line_height = Writer._get_single_line_size(text, font_name, font_size,is_vertical=False)
		if alignment == Alignment.LINE_MIDDLE:
			x0 = int(x0 + ((x1 - x0) - real_line_width) / 2)
		if alignment == Alignment.LINE_END:
			x0 = x1 - real_line_width
		#todo handle well of text weight
		self.draw.text((x0, y0), text, fill=text_color, font=font, anchor="lm", stroke_width=0, stroke_fill=(150,150,150))

	@staticmethod
	def _convert_line_text_to_array(text):
		lines = text.split("\n")
		word_data = []
		line_data = []
		col = 0
		for line in lines:
			#line_word = spliteKeyWord(line)
			line_word = list(line)
			col = max(col,len(line_word))
			word_data.append(line_word)
			line_data.append(line)
		return {"line_data":line_data,"word_data":word_data,"row":len(word_data),"col":col}

	@staticmethod
	def _check_best_fit_with_line(line,font_name,cell_width,cell_height):
		fit_font_size = 0
		for i in range(1,Writer.max_try_font_size):
			font = ImageFont.truetype(font_name, i)
			tmp_width, tmp_height = font.getsize(line)
			if tmp_width > cell_width or tmp_height > cell_height:
				return fit_font_size
			else:
				fit_font_size = i
		return Writer.max_try_font_size

	@staticmethod
	def _check_best_fit_font_size(width,height,font_name):
		fit_width = fit_height = fit_font_size = 0
		#print(f"check fit in {width},{height}")
		for i in range(1,Writer.max_try_font_size):
			font = ImageFont.truetype(font_name, i)
			tmp_width, tmp_height = font.getsize(Writer.test_word)
			if tmp_width > width or tmp_height > height:
				return fit_font_size, fit_width, fit_height
			else:
				fit_width = tmp_width
				fit_height = tmp_height
				fit_font_size = i
		return Writer.max_try_font_size, fit_width, fit_height

	@staticmethod
	def _get_word_size(font_name,font_size):
		font = ImageFont.truetype(font_name, font_size)
		return font.getsize(Writer.test_word)

	@staticmethod
	def _get_single_line_size(text_str,font_name,font_size,is_vertical=True):
		if is_vertical:
			width, height = Writer._get_word_size(font_name,font_size)
			if type(text_str) == str:
				text_array = Writer._convert_line_text_to_array(text_str)
				text_data = text_array["word_data"][0]
				num_words = len(text_data)
			else:
				num_words = len(text_str)
			return width, height * num_words
		else:
			font = ImageFont.truetype(font_name, font_size)
			return font.getsize(text_str)

	@staticmethod
	def _get_max_line_size(text_str,font_name,font_size,is_vertical=True):
		text_data = Writer._convert_line_text_to_array(text_str)
		max_line_width = max_line_height = 0
		for line_str in text_data["line_data"]:
			line_width, line_height = Writer._get_single_line_size(line_str,font_name,font_size,is_vertical)
			max_line_width = max(max_line_width,line_width)
			max_line_height = max(max_line_height,line_height)
		return max_line_width,max_line_height

	@staticmethod
	def _get_multi_line_size(text_str,font_name,font_size,is_vertical=True,gap=0.1):
		text_data = Writer._convert_line_text_to_array(text_str)
		max_line_width, max_line_height = Writer._get_max_line_size(text_str,font_name,font_size,is_vertical)

		total_line = len(text_data["line_data"])
		if is_vertical:
			return max_line_width*total_line + (max_line_width*gap)*(total_line-1), max_line_height, max_line_width, max_line_width*gap
		else:
			return max_line_width, max_line_height*total_line + (max_line_height*gap)+(total_line-1), max_line_height, max_line_height*gap

	@staticmethod
	def _get_final_font_size(text,frame_width,frame_height,gap,font_name,font_size,is_vertical=True):
		text_data = Writer._convert_line_text_to_array(text)
		if is_vertical:
			cell_width = int(frame_width / text_data["row"] * (1-gap))
			cell_height = int(frame_height / text_data["col"])
			fit_font_size, word_width, word_height = Writer._check_best_fit_font_size(
				cell_width, cell_height,font_name
			)
		else:
			fit_font_size = Writer.max_try_font_size
			cell_width = frame_width
			cell_height = int(frame_height / text_data["row"])
			for line in text_data["line_data"]:
				tmp_font_size = Writer._check_best_fit_with_line(line,font_name,cell_width,cell_height)
				fit_font_size = min(fit_font_size,tmp_font_size)

		if font_size == 0 or fit_font_size < font_size:
			return fit_font_size
		else:
			return font_size

	@staticmethod
	def _get_write_area_pos(x0,y0,x1,y1,write_area_width,write_area_height):
		x_offset = int((x1 - x0 - write_area_width) / 2)
		y_offset = int((y1 - y0 - write_area_height) / 2)
		return x0+x_offset,y0+y_offset,x1-x_offset,y1-y_offset

