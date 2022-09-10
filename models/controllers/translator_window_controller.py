from pathlib import Path
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QRect, QRectF
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QFileDialog

from models.const import *
from models import util
from uis import translator_window
from models.controllers.translator.helper import *
from models.controllers.translator.PhotoViewer import PhotoViewer
from models.controllers.translator.BoxItem import BoxItem
from models.controllers.translator.BubbleDetect import BubbleDetectEngine
from models.controllers.translator.OCR import OCREngine
from models.controllers.translator.Translator import TranslatorEngine
from models.controllers.translator.Writer import Writer

class TranslatorWindowController(QtWidgets.QMainWindow):
	LANG_OCR_FROM = ["jpn_vert","chi_tra_vert","chi_sim_vert","kor_vert","jpn","chi_tra","chi_sim","kor","eng"]
	LANG_TO = ["jpn_vert","chi_tra_vert","chi_sim_vert","kor_vert","jpn","chi_tra","chi_sim","kor","eng"]
	LANG_MAP_TO_TRANS = {
		"chi_tra":"zh-tw","chi_tra_vert":"zh-tw","chi_sim":"zh-cn","chi_sim_vert":"zh-cn",
		"jpn":"ja","jpn_vert":"ja","kor":"ko","kor_vert":"ko","eng":"en"
	}
	LANG_MAP_TO_WRITE_FLOW = {
		"chi_tra": "", "chi_tra_vert": "vert", "chi_sim": "", "chi_sim_vert": "vert",
		"jpn": "", "jpn_vert": "vert", "kor": "", "kor_vert": "vert", "eng": ""
	}

	def __init__(self,app,main_controller):
		super().__init__()
		self.app = app
		self.main_controller = main_controller
		self.ui = translator_window.Ui_MainWindow()
		self.ui.setupUi(self)
		self.from_folder = ""
		self.to_folder = ""
		self.image_list = []
		self.current_image_index = -1
		self.current_image_file = ""
		self.fonts = [{}]
		self.current_photo_viewer = PhotoViewer()
		self.current_preview_viewer = PhotoViewer()
		self.current_preview_viewer.setVisible(False)
		self.before_full_screen_is_max = False

		self.setup_control()

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)

		self.ui.layout_main.insertWidget(0,self.current_photo_viewer,4)
		self.ui.layout_main.insertWidget(0,self.current_preview_viewer,4)

		for tmp_class in BubbleDetectEngine.find_all_sub_class():
			self.ui.cbx_bubble_detect_engine.addItem(tmp_class.__name__)
		for tmp_class in OCREngine.find_all_sub_class():
			self.ui.cbx_ocr_engine.addItem(tmp_class.__name__)
		for tmp_class in TranslatorEngine.find_all_sub_class():
			self.ui.cbx_translator_engine.addItem(tmp_class.__name__)

		for lang_from in self.LANG_OCR_FROM:
			self.ui.cbx_language_from.addItem(lang_from)
		for lang_to in self.LANG_TO:
			self.ui.cbx_language_to.addItem(lang_to)

		self.fonts = util.find_all_fonts()
		for font in self.fonts:
			self.ui.cbx_font.addItem(font["name"])

		for tmp_alignment in Alignment:
			self.ui.cbx_alignment.addItem(tmp_alignment.name)
		for tmp_style in Style:
			self.ui.cbx_text_style.addItem(tmp_style.name)

		self.close_folder()

		self.bind_scroll_bars(self.current_photo_viewer.horizontalScrollBar(), self.current_preview_viewer.horizontalScrollBar())
		self.bind_scroll_bars(self.current_photo_viewer.verticalScrollBar(), self.current_preview_viewer.verticalScrollBar())

		# GUI
		self.retranslateUi()

		# action
		self.ui.actionOpenFolder.triggered.connect(self.on_file_open_folder)
		self.ui.actionBubbleDetect.triggered.connect(self.on_file_bubble_detect)
		self.ui.actionManualAddBubble.triggered.connect(self.on_file_manual_add_bubble)
		self.ui.actionOCRAllBubble.triggered.connect(self.on_file_ocr_all_bubble)
		self.ui.actionOCRThisBubble.triggered.connect(self.on_file_ocr_this_bubble)
		self.ui.actionTranslateAllBubble.triggered.connect(self.on_file_translate_all_bubble)
		self.ui.actionTranslateThisBubble.triggered.connect(self.on_file_translate_this_bubble)
		self.ui.actionDisplayPreview.triggered.connect(self.on_file_display_preview)
		self.ui.actionRefreshPreview.triggered.connect(self.on_file_refresh_preview)
		self.ui.actionSaveAndNext.triggered.connect(self.on_file_save_and_next)
		self.ui.actionSkipAndNext.triggered.connect(self.on_file_skip_and_next)
		self.ui.actionFullscreen.triggered.connect(self.on_file_full_screen)

		self.ui.btn_update_frame.clicked.connect(self.btn_update_frame_clicked)
		self.ui.btn_update_text.clicked.connect(self.btn_update_text_clicked)
		self.ui.btn_update_style_to_all_bubble.clicked.connect(self.btn_update_style_to_all_bubble_clicked)

		self.current_photo_viewer.item_selected.connect(self.on_label_item_selected)
		self.current_photo_viewer.item_changed.connect(self.on_label_item_changed)

		self.current_photo_viewer.view_updated.connect(self.current_preview_viewer.set_transform)
		self.current_preview_viewer.view_updated.connect(self.current_photo_viewer.set_transform)

		# event filter
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)

		for idx,lang_from in enumerate(self.LANG_OCR_FROM):
			self.ui.cbx_language_from.setItemText(idx,TRSM(lang_from))
		for idx,lang_to in enumerate(self.LANG_TO):
			self.ui.cbx_language_to.setItemText(idx,TRSM(lang_to))

		for idx,tmp_alignment in enumerate(Alignment):
			self.ui.cbx_alignment.setItemText(idx,TRSM(tmp_alignment.name))
		for idx,tmp_style in enumerate(Style):
			self.ui.cbx_text_style.setItemText(idx,TRSM(tmp_style.name))

	def show(self):
		super().show()
		#self.debug_action()

	def closeEvent(self, event):
		if util.confirm_box(TRSM("Confirm to quit?"),self):
			event.accept()
		else:
			event.ignore()

	# action
	def debug_action(self):
		self.from_folder = "F:/comics/測試"
		self.to_folder = "F:/comics/測試2"
		self.start_load_folder()
		self.current_image_index = 3
		self.start_load_image()
		self.on_file_bubble_detect()
		self.ui.cbx_language_from.setCurrentIndex(1)
		self.ui.cbx_language_to.setCurrentIndex(0)
		self.current_photo_viewer.select_label_by_index(2)
		self.ui.txt_text.setPlainText("中了計的\n是妳!")
		self.ui.txt_translated_text.setPlainText("クリックしました\nあなたです！\nTesting ABC DEF")
		self.btn_update_text_clicked()
		#print(self.image_list)

	def on_file_open_folder(self):
		self.close_folder()

		self.from_folder = self.try_ask_from_folder()
		if self.from_folder == "":
			return
		self.to_folder = self.try_ask_to_folder()
		if self.to_folder == "":
			return

		self.start_load_folder()
		self.current_image_index = 0
		self.start_load_image()

	def on_file_bubble_detect(self):
		engine_name = self.ui.cbx_bubble_detect_engine.currentText()
		engine = BubbleDetectEngine.init_by_name(engine_name)
		results = engine.get_bubble_from_file(self.current_image_file)
		#print(results)
		for tmp_result in results:
			self.current_photo_viewer.add_label("",frame=QRectF(tmp_result[0],tmp_result[1],tmp_result[2],tmp_result[3]))
		#print(results)

	def on_file_manual_add_bubble(self):
		if self.ui.actionManualAddBubble.isChecked():
			self.current_photo_viewer.toggle_add_mode(True)
		else:
			self.current_photo_viewer.toggle_add_mode(False)

	def on_file_ocr_all_bubble(self):
		engine_name = self.ui.cbx_ocr_engine.currentText()
		engine = OCREngine.init_by_name(engine_name)
		engine.load_image(self.current_image_file)
		lang_from = self.LANG_OCR_FROM[self.ui.cbx_language_from.currentIndex()]

		for tmp_label in self.current_photo_viewer.get_all_labels():
			ocr_text = engine.ocr_image_with_area_frame(tmp_label.get_frame(),lang_from)
			tmp_label.org_text = ocr_text
			tmp_label.update_text()
		#print("done")

	def on_file_ocr_this_bubble(self):
		tmp_label = self.current_photo_viewer.get_current_selected_label()
		if tmp_label is not None:
			engine_name = self.ui.cbx_ocr_engine.currentText()
			engine = OCREngine.init_by_name(engine_name)
			engine.load_image(self.current_image_file)
			lang_from = self.LANG_OCR_FROM[self.ui.cbx_language_from.currentIndex()]
			ocr_text = engine.ocr_image_with_area_frame(tmp_label.get_frame(),lang_from)
			tmp_label.org_text = ocr_text
			tmp_label.update_text()
			self.ui.txt_text.setPlainText(ocr_text)

	def on_file_translate_all_bubble(self):
		engine_name = self.ui.cbx_translator_engine.currentText()
		engine = TranslatorEngine.init_by_name(engine_name)
		from_lang = self.LANG_MAP_TO_TRANS[self.LANG_OCR_FROM[self.ui.cbx_language_from.currentIndex()]]
		to_lang = self.LANG_MAP_TO_TRANS[self.LANG_TO[self.ui.cbx_language_to.currentIndex()]]

		#text_to_translate = []
		for tmp_label in self.current_photo_viewer.get_all_labels():
			if tmp_label.org_text != "":
				#text_to_translate.append(tmp_label.org_text)
				trans_text = engine.translate_text(tmp_label.org_text,to_lang,from_lang)
				tmp_label.trans_text = trans_text
				tmp_label.update_text()

		# if len(text_to_translate) > 0:
		# 	translated_text = engine.translate_multi_text(text_to_translate,to_lang,from_lang)
		# 	current_idx = 0
		# 	for tmp_label in self.current_photo_viewer.get_all_labels():
		# 		if tmp_label.org_text != "":
		# 			tmp_label.trans_text = translated_text[current_idx]
		# 			tmp_label.update_text()
		# 			current_idx += 1

	def on_file_translate_this_bubble(self):
		tmp_label = self.current_photo_viewer.get_current_selected_label()
		if tmp_label is not None and self.ui.txt_text.toPlainText() != "":
			tmp_label.org_text = self.ui.txt_text.toPlainText()
			engine_name = self.ui.cbx_translator_engine.currentText()
			engine = TranslatorEngine.init_by_name(engine_name)
			from_lang = self.LANG_MAP_TO_TRANS[self.LANG_OCR_FROM[self.ui.cbx_language_from.currentIndex()]]
			to_lang = self.LANG_MAP_TO_TRANS[self.LANG_TO[self.ui.cbx_language_to.currentIndex()]]
			trans_text = engine.translate_text(tmp_label.org_text,to_lang,from_lang)
			tmp_label.trans_text = trans_text
			self.ui.txt_translated_text.setPlainText(trans_text)
			tmp_label.update_text()

	def on_file_display_preview(self):
		if self.ui.actionDisplayPreview.isChecked():
			self.current_preview_viewer.setVisible(True)
			self.on_file_refresh_preview()

		else:
			self.current_preview_viewer.setVisible(False)

	def on_file_refresh_preview(self):
		if not self.ui.actionDisplayPreview.isChecked():
			self.ui.actionDisplayPreview.setChecked(True)
			self.on_file_display_preview()
		else:
			result_image = self.get_result_image()
			result_q_pixmap = self.p_image_to_q_pixmap(result_image)
			self.current_preview_viewer.set_pixmap_photo(result_q_pixmap)
			self.current_preview_viewer.set_transform(self.current_photo_viewer.transform(),self.current_photo_viewer.get_zoom())
			#self.ui.layout_main.update()

	def on_file_save_and_next(self):
		target_image_file = os.path.join(self.to_folder,self.image_list[self.current_image_index])
		target_image_file = Path(target_image_file).as_posix()
		target_image_path = os.path.dirname(target_image_file)
		Path(target_image_path).mkdir(parents=True, exist_ok=True)
		result_image = self.get_result_image()
		ext = util.get_ext(target_image_file)
		if ext in ["jpg","jpeg"]:
			result_image = result_image.convert('RGB')
			result_image.save(target_image_file,quality=int(MY_CONFIG.get("general", "jpg_quality")))
		else:
			result_image.save(target_image_file)
		self.try_load_next_image()

	def on_file_skip_and_next(self):
		self.try_load_next_image()

	def on_file_full_screen(self):
		if not self.isFullScreen():
			if self.isMaximized():
				self.before_full_screen_is_max = True
			else:
				self.before_full_screen_is_max = False
			self.showFullScreen()
		else:
			if self.before_full_screen_is_max:
				self.showMaximized()
			else:
				self.showNormal()

	def btn_update_frame_clicked(self):
		frame = QRect(self.ui.spin_x.value(), self.ui.spin_y.value(), self.ui.spin_w.value(), self.ui.spin_h.value())
		tmp_label = self.current_photo_viewer.get_current_selected_label()
		if tmp_label is not None:
			tmp_label.set_frame(frame)

	def btn_update_text_clicked(self):
		tmp_label = self.current_photo_viewer.get_current_selected_label()
		if tmp_label is not None:
			tmp_label.org_text = self.ui.txt_text.toPlainText()
			tmp_label.trans_text = self.ui.txt_translated_text.toPlainText()
			tmp_label.font_index = self.ui.cbx_font.currentIndex()
			tmp_label.font_size = self.ui.spin_font_size.value()
			tmp_label.align_index = self.ui.cbx_alignment.currentIndex()
			tmp_label.text_style_index = self.ui.cbx_text_style.currentIndex()
			tmp_label.update_text()

	def btn_update_style_to_all_bubble_clicked(self):
		for tmp_label in self.current_photo_viewer.get_all_labels():
			tmp_label.font_index = self.ui.cbx_font.currentIndex()
			tmp_label.font_size = self.ui.spin_font_size.value()
			tmp_label.align_index = self.ui.cbx_alignment.currentIndex()
			tmp_label.text_style_index = self.ui.cbx_text_style.currentIndex()

	# photo viewer call back
	def on_label_item_selected(self,item):
		if isinstance(item, BoxItem):
			self.update_item_info(item)

	def on_label_item_changed(self,item,frame):
		if isinstance(item, BoxItem):
			self.update_item_info(item)

	# internal function
	def try_ask_from_folder(self):
		old_folder_path = MY_CONFIG.get("general", "download_folder")
		if old_folder_path == "":
			old_folder_path = "./"
		folder_path = QFileDialog.getExistingDirectory(self,TRSM("From folder"), old_folder_path)
		if folder_path != "":
			return folder_path
		else:
			return ""

	def try_ask_to_folder(self):
		folder_path = QFileDialog.getExistingDirectory(self, TRSM("To folder"), self.from_folder)
		if folder_path == self.from_folder:
			util.msg_box(TRSM("Please choose other folder than from folder"),self)
			return self.try_ask_to_folder()
		elif folder_path != "":
			return folder_path
		else:
			return ""

	def clean_view(self):
		self.current_photo_viewer.set_pixmap_photo(None)
		self.current_preview_viewer.set_pixmap_photo(None)
		self.current_photo_viewer.delete_all_label()
		self.current_image_file = ""

	def open_folder(self):
		self.ui.actionBubbleDetect.setEnabled(True)
		self.ui.actionManualAddBubble.setEnabled(True)
		self.ui.actionOCRAllBubble.setEnabled(True)
		self.ui.actionOCRThisBubble.setEnabled(True)
		self.ui.actionTranslateAllBubble.setEnabled(True)
		self.ui.actionTranslateThisBubble.setEnabled(True)
		self.ui.actionDisplayPreview.setEnabled(True)
		self.ui.actionRefreshPreview.setEnabled(True)
		self.ui.actionSaveAndNext.setEnabled(True)
		self.ui.actionSkipAndNext.setEnabled(True)
		self.ui.btn_update_frame.setEnabled(True)
		#self.ui.btn_ocr_this_bubble.setEnabled(True)
		self.ui.btn_update_text.setEnabled(True)
		self.ui.btn_update_style_to_all_bubble.setEnabled(True)
		#self.ui.btn_translate_this_bubble.setEnabled(True)

	def close_folder(self):
		self.clean_view()
		self.from_folder = ""
		self.to_folder = ""
		self.image_list = []
		self.ui.actionBubbleDetect.setEnabled(False)
		self.ui.actionManualAddBubble.setEnabled(False)
		self.ui.actionOCRAllBubble.setEnabled(False)
		self.ui.actionOCRThisBubble.setEnabled(False)
		self.ui.actionTranslateAllBubble.setEnabled(False)
		self.ui.actionTranslateThisBubble.setEnabled(False)
		self.ui.actionDisplayPreview.setEnabled(False)
		self.ui.actionRefreshPreview.setEnabled(False)
		self.ui.actionSaveAndNext.setEnabled(False)
		self.ui.actionSkipAndNext.setEnabled(False)
		self.ui.spin_x.setValue(0)
		self.ui.spin_y.setValue(0)
		self.ui.spin_w.setValue(0)
		self.ui.spin_h.setValue(0)
		self.ui.btn_update_frame.setEnabled(False)
		#self.ui.btn_ocr_this_bubble.setEnabled(False)
		self.ui.txt_text.setPlainText("")
		self.ui.txt_translated_text.setPlainText("")
		#self.ui.cbx_font.setCurrentIndex(0)
		#self.ui.spin_font_size.setValue(0)
		#self.ui.cbx_alignment.setCurrentIndex(0)
		#self.ui.cbx_text_style.setCurrentIndex(0)
		self.ui.btn_update_text.setEnabled(False)
		self.ui.btn_update_style_to_all_bubble.setEnabled(False)
		#self.ui.btn_translate_this_bubble.setEnabled(False)
		self.ui.statusbar.showMessage("")

	def start_load_folder(self):
		tmp_image_list = []
		util.get_image_list_from_folder(self.from_folder,tmp_image_list)
		self.image_list = []
		for tmp_list in tmp_image_list:
			self.image_list = self.image_list + tmp_list["files"]

		if len(self.image_list) > 0:
			self.open_folder()
		else:
			self.close_folder()
			util.msg_box(TRSM("Please select a folder with contain at least one image"),self)

	def start_load_image(self):
		self.current_image_file = os.path.join(self.from_folder,self.image_list[self.current_image_index])
		self.current_image_file = Path(self.current_image_file).as_posix()
		current_q_pixmap = QtGui.QPixmap(self.current_image_file)

		self.current_photo_viewer.set_pixmap_photo(current_q_pixmap)
		self.current_preview_viewer.set_pixmap_photo(current_q_pixmap)
		self.ui.statusbar.showMessage(self.current_image_file + " (%d/%d)" % (self.current_image_index+1,len(self.image_list)))

	def try_load_next_image(self):
		self.clean_view()
		if self.current_image_index < len(self.image_list) - 1:
			self.current_image_index += 1
			self.start_load_image()
		else:
			util.msg_box(TRSM("Finish all image"),self)
			self.close_folder()

	def update_item_info(self, item: BoxItem):
		self.ui.spin_x.setValue(item.get_frame().x())
		self.ui.spin_y.setValue(item.get_frame().y())
		self.ui.spin_w.setValue(item.get_frame().width())
		self.ui.spin_h.setValue(item.get_frame().height())
		self.ui.txt_text.setPlainText(item.org_text)
		self.ui.txt_translated_text.setPlainText(item.trans_text)

		self.ui.cbx_font.setCurrentIndex(item.font_index)
		self.ui.spin_font_size.setValue(item.font_size)
		self.ui.cbx_alignment.setCurrentIndex(item.align_index)
		self.ui.cbx_text_style.setCurrentIndex(item.text_style_index)

	def get_result_image(self):
		tmp_writer = Writer()
		tmp_writer.load_image_from_file(self.current_image_file)
		for tmp_label in self.current_photo_viewer.get_all_labels():
			frame = tmp_label.get_frame()
			text = tmp_label.trans_text
			flow = self.LANG_MAP_TO_WRITE_FLOW[self.LANG_TO[self.ui.cbx_language_to.currentIndex()]]
			is_vertical = True if flow == "vert" else False
			font = self.fonts[tmp_label.font_index]["file"]
			font_size = tmp_label.font_size
			alignment = Alignment(tmp_label.align_index + 1)
			style = Style(tmp_label.text_style_index + 1)
			tmp_writer.write_text(
				text=text, is_vertical=is_vertical, frame=frame, font_name=font, font_size=font_size,
				alignment=alignment, text_style=style
			)
		return tmp_writer.get_result_image()

	@staticmethod
	def p_image_to_q_pixmap(p_image):
		q_image = TranslatorWindowController.p_image_to_q_image(p_image)
		q_pixmap = QPixmap.fromImage(q_image)
		return q_pixmap

	@staticmethod
	def p_image_to_q_image(p_image):
		pimg_converted = p_image.convert("RGBA")
		data = pimg_converted.tobytes("raw", "RGBA")
		return QImage(data, pimg_converted.size[0], pimg_converted.size[1], QImage.Format_RGBA8888)

	@staticmethod
	def bind_scroll_bars(scroll_bar1, scroll_bar2):
		scroll_bar1.valueChanged.connect(
			lambda _: QtCore.QTimer.singleShot(0, lambda: scroll_bar2.setValue(scroll_bar1.value())))
		scroll_bar2.valueChanged.connect(
			lambda _: QtCore.QTimer.singleShot(0, lambda: scroll_bar1.setValue(scroll_bar2.value())))
