from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import QRect

from .helper import Alignment, Style


class Writer:
	max_try_font_size = 200

	def __init__(self):
		self.image = None
		self.draw = None

	def load_image_from_file(self, file):
		with Image.open(file) as image:
			self.image = image.convert("RGBA")
		self.draw = ImageDraw.Draw(self.image)

	def get_result_image(self):
		return self.image

	def fill_background(self, area, color):
		self.draw.rectangle(area, fill=color)

	def write_text(self, text, is_vertical=True, frame=QRect(0, 0, 0, 0), font_name="", font_size=0,
				   alignment=Alignment.LINE_START, text_style=Style.WHITE_BG_BLACK_TEXT, gap=0.1):
		if not text.strip() or frame.width() <= 0 or frame.height() <= 0:
			return
		layer = self.render_text(text, frame.width(), frame.height(), font_name, font_size,
							 is_vertical, alignment, text_style, gap)
		self.image.alpha_composite(layer, (frame.x(), frame.y()))

	@classmethod
	def render_text(cls, text, width, height, font_name="", font_size=0, is_vertical=True,
					alignment=Alignment.LINE_START, text_style=Style.WHITE_BG_BLACK_TEXT, gap=0.1):
		"""Render in image pixels; the same bounded layer serves editor and export."""
		width, height = int(width), int(height)
		layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
		if not text.strip() or width <= 0 or height <= 0:
			return layer
		text = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)
		if text_style == Style.BLACK_BG_WHITE_TEXT:
			background, color = (0, 0, 0, 255), (255, 255, 255, 255)
		elif text_style == Style.NO_BG_WHITE_TEXT:
			background, color = (0, 0, 0, 0), (255, 255, 255, 255)
		elif text_style == Style.NO_BG_BLACK_TEXT:
			background, color = (0, 0, 0, 0), (0, 0, 0, 255)
		else:
			background, color = (255, 255, 255, 255), (0, 0, 0, 255)
		layer.paste(background, (0, 0, width, height))

		padding_x = min(2, (width - 1) // 2)
		padding_y = min(2, (height - 1) // 2)
		available_width = width - padding_x * 2
		available_height = height - padding_y * 2
		font, layout = cls._fit_text(text, available_width, available_height, font_name, font_size, is_vertical, gap)
		# Assemble complete glyph bitmaps on their own full-size surface first.
		# Never rely on the bubble's edges to clip incorrectly measured text.
		ink = Image.new("L", (max(1, layout["width"]), max(1, layout["height"])), 0)
		for index, line in enumerate(layout["lines"]):
			if is_vertical:
				x = layout["width"] - layout["cell_width"] - index * (layout["cell_width"] + layout["spacing"])
				y = cls._alignment_offset(layout["height"] - len(line) * layout["cell_height"], alignment)
				for row, mask in enumerate(layout["masks"][index]):
					if mask is not None:
						ink.paste(mask, (round(x + (layout["cell_width"] - mask.width) / 2),
									 round(y + row * layout["cell_height"] + (layout["cell_height"] - mask.height) / 2)))
			else:
				mask = layout["masks"][index]
				if mask is not None:
					x = cls._alignment_offset(layout["width"] - mask.width, alignment)
					y = index * (layout["cell_height"] + layout["spacing"]) + (layout["cell_height"] - mask.height) / 2
					ink.paste(mask, (round(x), round(y)))

		# Extremely small boxes may not fit even the smallest font. Scale the
		# complete text block in that case, rather than cropping off characters.
		scale = min(1.0, available_width / ink.width, available_height / ink.height)
		if scale < 1:
			ink = ink.resize((max(1, min(available_width, int(ink.width * scale))),
							 max(1, min(available_height, int(ink.height * scale)))), Image.Resampling.LANCZOS)
		x = padding_x + (available_width - ink.width) // 2
		y = padding_y + (available_height - ink.height) // 2
		layer.paste(color, (x, y), ink)
		return layer

	@staticmethod
	def _ink_mask(font, text):
		if not text:
			return None
		bitmap = font.getmask(text, mode="L")
		if not bitmap.size[0] or not bitmap.size[1]:
			return None
		mask = Image.frombytes("L", bitmap.size, bytes(bitmap))
		bounds = mask.getbbox()
		return mask.crop(bounds) if bounds else None

	@staticmethod
	def _alignment_offset(space, alignment):
		if alignment == Alignment.LINE_MIDDLE:
			return space / 2
		if alignment == Alignment.LINE_END:
			return space
		return 0

	@staticmethod
	def _font(font_name, size):
		font = ImageFont.truetype(font_name, size) if font_name else ImageFont.load_default(size=size)
		# The bundled Noto CJK variable font defaults to Thin. There is no
		# weight selector in the UI, so use its normal readable named style.
		try:
			if b"Regular" in font.get_variation_names():
				font.set_variation_by_name(b"Regular")
		except OSError:
			pass  # Static fonts have no variation names.
		return font

	@classmethod
	def _layout(cls, text, font, is_vertical, gap):
		lines = text.split("\n")
		if is_vertical:
			glyphs = {character: cls._ink_mask(font, character) for character in set(text + "國") if character != "\n"}
			masks = [[glyphs[character] for character in line] for line in lines]
			visible = [mask for mask in glyphs.values() if mask is not None]
			cell_width = max([1] + [mask.width for mask in visible])
			cell_height = max([1] + [mask.height for mask in visible])
			spacing = max(0, round(cell_width * gap))
			width = cell_width * len(lines) + spacing * (len(lines) - 1)
			height = max(map(len, lines)) * cell_height
		else:
			masks = [cls._ink_mask(font, line) for line in lines]
			visible = [mask for mask in masks if mask is not None]
			cell_width = max([0] + [mask.width for mask in visible])
			cell_height = max([1] + [mask.height for mask in visible])
			spacing = max(0, round(cell_height * gap))
			width = cell_width
			height = cell_height * len(lines) + spacing * (len(lines) - 1)
		return {"lines": lines, "masks": masks, "width": width, "height": height,
				"cell_width": cell_width, "cell_height": cell_height, "spacing": spacing}

	@classmethod
	def _fit_text(cls, text, width, height, font_name, font_size, is_vertical, gap):
		# A nonzero value remains an upper bound, matching the existing behavior.
		# Keep 0 on the bubble as the auto-fit setting; only the rendered size changes.
		low = 1
		high = max(1, int(font_size)) if font_size > 0 else cls.max_try_font_size
		best_font = cls._font(font_name, 1)
		best_layout = cls._layout(text, best_font, is_vertical, gap)
		while low <= high:
			size = (low + high) // 2
			font = cls._font(font_name, size)
			layout = cls._layout(text, font, is_vertical, gap)
			if layout["width"] <= width and layout["height"] <= height:
				best_font, best_layout = font, layout
				low = size + 1
			else:
				high = size - 1
		return best_font, best_layout
