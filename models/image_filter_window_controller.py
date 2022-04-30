from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import Qt
from PIL import Image, ImageOps

import util
from const import *
from uis import image_filter_window


class ImageFilterWindowController(QtWidgets.QMainWindow):
	def __init__(self,app,main_controller):
		super().__init__()
		self.app = app
		self.main_controller = main_controller
		self.ui = image_filter_window.Ui_MainWindow()
		self.ui.setupUi(self)
		self.image_list = []
		self.current_image_index = 0
		self.current_pimage = None
		self.current_cimage = None
		self.before_full_screen_is_max = False
		self.setup_control()

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)

		self.ui.cbx_rotate.addItems([TRSM("0 °"),TRSM("90 °"),TRSM("180 °"),TRSM("270 °")])

		# GUI
		self.retranslateUi()

		#load filter
		#print("%0.2f" % float(MY_CONFIG.get("filter", "contrast")))
		self.ui.slider_contrast.setValue(float(MY_CONFIG.get("filter", "contrast"))*100)
		self.ui.slider_sharpness.setValue(float(MY_CONFIG.get("filter", "sharpness"))*100)
		self.ui.slider_brightness.setValue(float(MY_CONFIG.get("filter", "brightness"))*100)
		self.ui.slider_color.setValue(float(MY_CONFIG.get("filter", "color"))*100)

		self.ui.lbl_contrast_value.setText("%0.2f" % float(MY_CONFIG.get("filter", "contrast")))
		self.ui.lbl_sharpness_value.setText("%0.2f" % float(MY_CONFIG.get("filter", "sharpness")))
		self.ui.lbl_brightness_value.setText("%0.2f" % float(MY_CONFIG.get("filter", "brightness")))
		self.ui.lbl_color_value.setText("%0.2f" % float(MY_CONFIG.get("filter", "color")))

		self.ui.cbx_rotate.setCurrentIndex(int(MY_CONFIG.get("filter", "rotate")))
		self.ui.chk_horizontal_flip.setChecked(MY_CONFIG.get("filter", "horizontal_flip") == "True")
		self.ui.chk_vertical_flip.setChecked(MY_CONFIG.get("filter", "vertical_flip") == "True")

		#action
		self.ui.slider_contrast.valueChanged.connect(self.slider_value_changed)
		self.ui.slider_sharpness.valueChanged.connect(self.slider_value_changed)
		self.ui.slider_brightness.valueChanged.connect(self.slider_value_changed)
		self.ui.slider_color.valueChanged.connect(self.slider_value_changed)

		self.ui.cbx_rotate.currentIndexChanged.connect(self.cbx_rotate_changed)
		self.ui.chk_horizontal_flip.clicked.connect(self.chk_flip_clicked)
		self.ui.chk_vertical_flip.clicked.connect(self.chk_flip_clicked)

		self.ui.btn_next.clicked.connect(self.btn_next_clicked)
		self.ui.btn_prev.clicked.connect(self.btn_prev_clicked)

		self.ui.btn_full_screen.clicked.connect(self.btn_full_screen_clicked)
		self.ui.btn_save.clicked.connect(self.btn_save_clicked)
		self.ui.btn_reset.clicked.connect(self.btn_reset_clicked)
		self.ui.btn_close.clicked.connect(self.btn_close_clicked)
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)

		pass

	#action
	def slider_value_changed(self):
		contrast_str = "%0.2f" % (self.ui.slider_contrast.value()/100)
		self.ui.lbl_contrast_value.setText(contrast_str)

		sharpness_str = "%0.2f" % (self.ui.slider_sharpness.value()/100)
		self.ui.lbl_sharpness_value.setText(sharpness_str)

		brightness_str = "%0.2f" % (self.ui.slider_brightness.value()/100)
		self.ui.lbl_brightness_value.setText(brightness_str)

		color_str = "%0.2f" % (self.ui.slider_color.value()/100)
		self.ui.lbl_color_value.setText(color_str)

		self.update_image_by_filter()

	def cbx_rotate_changed(self):
		self.update_image_by_filter()

	def chk_flip_clicked(self):
		self.update_image_by_filter()

	def btn_next_clicked(self):
		self.current_image_index += 1
		self.process_single_image()

	def btn_prev_clicked(self):
		self.current_image_index -= 1
		self.process_single_image()

	def btn_full_screen_clicked(self):
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

	def btn_save_clicked(self):
		MY_CONFIG.set("filter","contrast",str(self.ui.slider_contrast.value()/100))
		MY_CONFIG.set("filter","sharpness",str(self.ui.slider_sharpness.value()/100))
		MY_CONFIG.set("filter","brightness",str(self.ui.slider_brightness.value()/100))
		MY_CONFIG.set("filter","color",str(self.ui.slider_color.value()/100))
		MY_CONFIG.set("filter","rotate",str(self.ui.cbx_rotate.currentIndex()))
		MY_CONFIG.set("filter","horizontal_flip",str(self.ui.chk_horizontal_flip.isChecked()))
		MY_CONFIG.set("filter","vertical_flip",str(self.ui.chk_vertical_flip.isChecked()))
		MY_CONFIG.save()

		util.msg_box(TRSM("Filter setting saved"), self)

		pass

	def btn_reset_clicked(self):
		self.ui.slider_contrast.setValue(100)
		self.ui.slider_sharpness.setValue(100)
		self.ui.slider_brightness.setValue(100)
		self.ui.slider_color.setValue(100)

		self.ui.cbx_rotate.setCurrentIndex(0)
		self.ui.chk_horizontal_flip.setChecked(False)
		self.ui.chk_vertical_flip.setChecked(False)
		self.update_image_by_filter()

	def btn_close_clicked(self):
		self.close()

	#function
	def set_image_list(self,image_list):
		self.image_list = image_list

	def start_process_image(self):
		self.current_image_index = 0
		self.process_single_image()

	def process_single_image(self):
		image_from = self.image_list[self.current_image_index]
		self.update_nav_button_enabled()
		self.current_pimage = Image.open(image_from)
		#print(image_from)
		#self.current_cimage = util.cv_imread(image_from)
		#print(self.current_cimage)

		#self.set_cimage_to_gv(self.current_cimage,self.ui.gv_from)
		self.set_pimage_to_gv(self.current_pimage,self.ui.gv_from)
		self.update_image_by_filter()

	def set_pimage_to_gv(self,pimage,gv):
		scene = QGraphicsScene()
		qimage = self.pimage_to_qimage(pimage)
		pixmap = QPixmap.fromImage(qimage)
		pixmap_item = QGraphicsPixmapItem(pixmap)
		scene.addItem(pixmap_item)
		gv.setScene(scene)
		gv.fitInView(scene.sceneRect(),Qt.KeepAspectRatio)

	# def set_cimage_to_gv(self,cimage,gv):
	# 	cimage = cv2.cvtColor(cimage, cv2.COLOR_BGR2RGB)
	# 	height, width = cimage.shape[:2]
	#
	# 	#widthStep = width * 3
	# 	#qimage = QImage(cimage.data, width, height, widthStep, QImage.Format_RGB888)
	#
	# 	scene = QGraphicsScene()
	# 	qimage = QImage(cimage.data, width, height, QImage.Format_RGB888)
	# 	pixmap = QPixmap.fromImage(qimage)
	# 	pixmap_item = QGraphicsPixmapItem(pixmap)
	# 	scene.addItem(pixmap_item)
	# 	gv.setScene(scene)
	# 	gv.fitInView(scene.sceneRect(),Qt.KeepAspectRatio)

	def update_image_by_filter(self):
		color_factor = float(self.ui.lbl_color_value.text())
		contrast_factor = float(self.ui.lbl_contrast_value.text())
		brightness_factor = float(self.ui.lbl_brightness_value.text())
		sharpness_factor = float(self.ui.lbl_sharpness_value.text())
		new_pimage = util.filter_pimage(self.current_pimage,contrast_factor,sharpness_factor,brightness_factor,color_factor)

		rotate = self.ui.cbx_rotate.currentIndex()*90
		new_pimage = util.rotate_pimage(new_pimage,rotate,self.ui.chk_horizontal_flip.isChecked(),self.ui.chk_vertical_flip.isChecked())

		self.set_pimage_to_gv(new_pimage,self.ui.gv_to)

	def update_nav_button_enabled(self):
		if self.current_image_index > 0:
			self.ui.btn_prev.setEnabled(True)
		else:
			self.ui.btn_prev.setEnabled(False)
		if self.current_image_index < len(self.image_list)-1:
			self.ui.btn_next.setEnabled(True)
		else:
			self.ui.btn_next.setEnabled(False)

	def pimage_to_qimage(self,pimg):
		pimg_converted = pimg.convert("RGBA")
		data = pimg_converted.tobytes("raw", "RGBA")
		return QImage(data, pimg_converted.size[0], pimg_converted.size[1], QImage.Format_RGBA8888)

	def center_pos_of_parent(self):
		if self.windowState() != QtCore.Qt.WindowMaximized:
			qr = self.main_controller.frameGeometry()
			x = qr.left() + (qr.width() - self.width()) / 2
			y = qr.top() + (qr.height() - self.height()) / 2
			self.move(x, y)

	def resize_element(self):
		if self.ui.gv_from.scene():
			self.ui.gv_from.fitInView(self.ui.gv_from.scene().sceneRect(),Qt.KeepAspectRatio)
		if self.ui.gv_to.scene():
			self.ui.gv_to.fitInView(self.ui.gv_to.scene().sceneRect(),Qt.KeepAspectRatio)

	#override
	def show(self):
		super().show()
		self.center_pos_of_parent()
		self.start_process_image()
		pass

	def resizeEvent(self, event):
		self.resize_element()

	def keyPressEvent(self, e):
		if e.key() == Qt.Key_F11:
			self.btn_full_screen_clicked()

	@staticmethod
	def setModal(is_modal):
		#print("set modal %d" % is_modal)
		pass
