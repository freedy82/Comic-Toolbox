from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import Qt
from PIL import Image

from models.const import *
from models import util
from uis import crop_window
from models.crop_frame_controller import CropFrameController


class CropWindowController(QtWidgets.QMainWindow):
	SIZE_POLICY = [
		{"name": "Use rule first, then same as last crop position"},
		{"name": "Use rule first, then full of image"},
		{"name": "Always same as last crop position"},
		{"name": "Always full of image"},
	]

	def __init__(self,app,main_controller,method):
		super().__init__()
		self.app = app
		self.main_controller = main_controller
		self.ui = crop_window.Ui_MainWindow()
		self.ui.setupUi(self)
		self.image_list = []
		self.setup_control()
		self.method = method
		self.crop_frame_controllers = []

		self.current_image_index = 0
		self.current_image_width = 0
		self.current_image_height = 0
		self.current_image_ratio = 0
		self.is_updating_frame_child = False
		self.last_crop_ratio = [{"x1":0,"y1":0,"x2":1,"y2":1},{"x1":0,"y1":0,"x2":1,"y2":1}]
		self.is_finish_job_flag = False
		self.before_full_screen_is_max = False

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)

		# GUI
		self.retranslateUi()

		#action
		self.ui.spin_frame1_x1.valueChanged.connect(self.frame_spin_value_changed)
		self.ui.spin_frame1_y1.valueChanged.connect(self.frame_spin_value_changed)
		self.ui.spin_frame1_x2.valueChanged.connect(self.frame_spin_value_changed)
		self.ui.spin_frame1_y2.valueChanged.connect(self.frame_spin_value_changed)
		self.ui.spin_frame2_x1.valueChanged.connect(self.frame_spin_value_changed)
		self.ui.spin_frame2_y1.valueChanged.connect(self.frame_spin_value_changed)
		self.ui.spin_frame2_x2.valueChanged.connect(self.frame_spin_value_changed)
		self.ui.spin_frame2_y2.valueChanged.connect(self.frame_spin_value_changed)

		self.ui.btn_ignore.clicked.connect(self.btn_ignore_clicked)
		self.ui.btn_process.clicked.connect(self.btn_process_clicked)
		self.ui.btn_use_rule.clicked.connect(self.btn_use_rule_clicked)
		self.ui.btn_full_of_image.clicked.connect(self.btn_full_of_image_clicked)
		self.ui.btn_exchange.clicked.connect(self.btn_exchange_clicked)
		self.ui.btn_full_screen.clicked.connect(self.btn_full_screen_clicked)
		self.ui.btn_quit.clicked.connect(self.btn_quit_clicked)
		#hack to combobox of F4?
		self.ui.cbx_size_policy.installEventFilter(self)
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)

		self.ui.cbx_size_policy.clear()
		for size_policy in self.SIZE_POLICY:
			self.ui.cbx_size_policy.addItem(TRSM(size_policy["name"]))

		pass

	#function
	def set_is_remove_source(self,is_remove_source):
		self.ui.chk_remove_source.setChecked(is_remove_source)

	def get_current_image_ratio(self):
		return self.current_image_ratio

	def set_image_list(self,image_list):
		self.image_list = image_list
		self.ui.pgb_cover.setMaximum(len(self.image_list))

	def start_image_process(self):
		if len(self.image_list) > 0:
			self.current_image_index = 0
			self.is_finish_job_flag = False
			self.process_single_image()
		else:
			util.msg_box(TRSM("Not image to cropping"),self)
			self.is_finish_job_flag = True
			self.close()
			pass

	def process_next_image(self):
		if self.current_image_index < len(self.image_list) - 1:
			self.save_crop_ratio()
			self.current_image_index += 1
			self.process_single_image()
		else:
			util.msg_box(TRSM("Finish of cropping"),self)
			self.is_finish_job_flag = True
			self.close()
			pass

	def process_single_image(self):
		self.ui.pgb_cover.setValue(self.current_image_index+1)
		image_from = self.image_list[self.current_image_index]["from"]
		self.ui.txt_file_name.setText(image_from)

		scene = QGraphicsScene()
		qimage = QImage(image_from)
		self.current_image_width = qimage.width()
		self.current_image_height = qimage.height()
		self.ui.txt_width.setText(str(self.current_image_width))
		self.ui.txt_height.setText(str(self.current_image_height))
		self.ui.spin_frame1_x1.setMaximum(self.current_image_width)
		self.ui.spin_frame1_x2.setMaximum(self.current_image_width)
		self.ui.spin_frame1_y1.setMaximum(self.current_image_height)
		self.ui.spin_frame1_y2.setMaximum(self.current_image_height)
		self.ui.spin_frame2_x1.setMaximum(self.current_image_width)
		self.ui.spin_frame2_x2.setMaximum(self.current_image_width)
		self.ui.spin_frame2_y1.setMaximum(self.current_image_height)
		self.ui.spin_frame2_y2.setMaximum(self.current_image_height)

		pixmap = QPixmap.fromImage(qimage)
		pixmap_item = QGraphicsPixmapItem(pixmap)
		scene.addItem(pixmap_item)
		self.ui.graphics_view.setScene(scene)
		self.ui.graphics_view.fitInView(scene.sceneRect(),Qt.KeepAspectRatio)

		self.clear_all_frame_controllers()

		#crop frame
		self.crop_frame_controllers = []
		for idx, to_file in enumerate(self.image_list[self.current_image_index]["to"]):
			crop_frame_controller = CropFrameController(self.app,self.main_controller,self.ui.frame_image,self)
			crop_frame_controller.show_frame()
			crop_frame_controller.frame_changed.connect(self.frame_changed)
			if len(self.image_list[self.current_image_index]["to"]) > 1:
				crop_frame_controller.set_display_name(TRSM("Page "+str(idx+1)))
			if idx >= 1:
				crop_frame_controller.set_border_color("#0000FF")
			self.crop_frame_controllers.append(crop_frame_controller)

		if len(self.image_list[self.current_image_index]["to"]) <= 1:
			self.ui.spin_frame2_x1.setEnabled(False)
			self.ui.spin_frame2_x2.setEnabled(False)
			self.ui.spin_frame2_y1.setEnabled(False)
			self.ui.spin_frame2_y2.setEnabled(False)
			self.reset_best_crop_pos(1)
			self.ui.btn_exchange.setEnabled(False)
		else:
			self.ui.spin_frame2_x1.setEnabled(True)
			self.ui.spin_frame2_x2.setEnabled(True)
			self.ui.spin_frame2_y1.setEnabled(True)
			self.ui.spin_frame2_y2.setEnabled(True)
			self.reset_best_crop_pos(1)
			self.reset_best_crop_pos(2)
			self.ui.btn_exchange.setEnabled(True)

		self.resize_element()
		pass

	def clear_all_frame_controllers(self):
		for cfc in self.crop_frame_controllers:
			cfc.remove_frame()
			cfc = None

	def resize_element(self):
		self.center_graphics_view_in_frame_image()
		self.update_crop_frame_by_pos_value()
		self.update_crop_frame_allow_rect()

	def center_graphics_view_in_frame_image(self):
		qr = self.ui.frame_image.frameGeometry()
		if self.ui.graphics_view.scene():
			rect = util.find_rect_to_fit(qr.width(),qr.height(),self.current_image_width,self.current_image_height)
			self.current_image_ratio = rect.width() / self.current_image_width
			#print("current image ratio ",self.current_image_ratio)
			self.ui.graphics_view.setGeometry(rect)
			self.ui.graphics_view.fitInView(self.ui.graphics_view.scene().sceneRect(), Qt.KeepAspectRatio)
		else:
			#print("not scene")
			self.ui.graphics_view.setFrameRect(QtCore.QRect(0,0,qr.width(),qr.height()))
		pass

	def update_crop_frame_allow_rect(self):
		for idx, crop_frame_controller in enumerate(self.crop_frame_controllers, start=1):
			if crop_frame_controller:
				crop_frame_controller.set_allow_rect(self.ui.graphics_view.frameGeometry())

	def update_crop_frame_by_pos_value(self):
		for idx, crop_frame_controller in enumerate(self.crop_frame_controllers, start=1):
			if crop_frame_controller.is_frame_show():
				if idx == 1:
					real_x1 = self.ui.spin_frame1_x1.value()
					real_y1 = self.ui.spin_frame1_y1.value()
					real_x2 = self.ui.spin_frame1_x2.value()
					real_y2 = self.ui.spin_frame1_y2.value()
				elif idx == 2:
					real_x1 = self.ui.spin_frame2_x1.value()
					real_y1 = self.ui.spin_frame2_y1.value()
					real_x2 = self.ui.spin_frame2_x2.value()
					real_y2 = self.ui.spin_frame2_y2.value()
				# calculate pos
				prefix_x = self.ui.graphics_view.geometry().x()
				prefix_y = self.ui.graphics_view.geometry().y()
				target_x = real_x1 * self.current_image_ratio + prefix_x
				target_y = real_y1 * self.current_image_ratio + prefix_y
				target_w = (real_x2-real_x1) * self.current_image_ratio
				target_h = (real_y2-real_y1) * self.current_image_ratio
				rect = QtCore.QRect(target_x,target_y,target_w,target_h)
				#print("update crop frame by pos value to ",rect)
				crop_frame_controller.set_real_pos_rect({"x1":real_x1,"y1":real_y1,"x2":real_x2,"y2":real_y2})
				crop_frame_controller.move_frame_to(rect)
		pass

	def reset_best_crop_pos(self,idx=1):
		pos = self.find_best_crop_pos(idx)
		if pos:
			self.set_pos_to_frame(pos,"frame"+str(idx))

	def save_crop_ratio(self):
		for idx, crop_frame_controller in enumerate(self.crop_frame_controllers, start=1):
			if crop_frame_controller.is_frame_show():
				if idx == 1:
					real_x1 = self.ui.spin_frame1_x1.value()
					real_y1 = self.ui.spin_frame1_y1.value()
					real_x2 = self.ui.spin_frame1_x2.value()
					real_y2 = self.ui.spin_frame1_y2.value()
				elif idx == 2:
					real_x1 = self.ui.spin_frame2_x1.value()
					real_y1 = self.ui.spin_frame2_y1.value()
					real_x2 = self.ui.spin_frame2_x2.value()
					real_y2 = self.ui.spin_frame2_y2.value()
				self.last_crop_ratio[idx-1] = {
					"x1": real_x1 / self.current_image_width,
					"y1": real_y1 / self.current_image_height,
					"x2": real_x2 / self.current_image_width,
					"y2": real_y2 / self.current_image_height,
				}
		#print("last_crop_ratio",self.last_crop_ratio)
		pass

	def set_pos_to_frame(self,pos,frame="frame1"):
		if frame == "frame1":
			self.ui.spin_frame1_x1.setValue(pos["x1"])
			self.ui.spin_frame1_y1.setValue(pos["y1"])
			self.ui.spin_frame1_x2.setValue(pos["x2"])
			self.ui.spin_frame1_y2.setValue(pos["y2"])
		elif frame == "frame2":
			self.ui.spin_frame2_x1.setValue(pos["x1"])
			self.ui.spin_frame2_y1.setValue(pos["y1"])
			self.ui.spin_frame2_x2.setValue(pos["x2"])
			self.ui.spin_frame2_y2.setValue(pos["y2"])

	def find_best_crop_pos(self,idx=1):
		size_policy = self.ui.cbx_size_policy.currentIndex()
		result_rule = self.find_best_crop_pos_by_rule(idx)
		result_last = self.find_crop_pos_by_last_crop(idx)
		if size_policy == 0:
			# rule => ratio
			if result_rule:
				return result_rule
			elif result_last:
				return result_last
		elif size_policy == 1:
			# rule => full
			if result_rule:
				return result_rule
		elif size_policy == 2:
			# ratio => full
			if result_last:
				return result_last

		# full image
		return self.find_crop_pos_by_full(idx)

	def find_crop_pos_by_last_crop(self,idx=1):
		if len(self.last_crop_ratio) > idx-1:
			x1 = self.current_image_width * self.last_crop_ratio[idx-1]["x1"]
			y1 = self.current_image_height * self.last_crop_ratio[idx-1]["y1"]
			x2 = self.current_image_width * self.last_crop_ratio[idx-1]["x2"]
			y2 = self.current_image_height * self.last_crop_ratio[idx-1]["y2"]
			return {"x1": x1,"y1":y1,"x2":x2,"y2":y2}
		return None

	def find_crop_pos_by_full(self,idx):
		if len(self.image_list[self.current_image_index]["to"]) > 1:
			if idx == 1:
				return {"x1": self.current_image_width / 2, "y1": 0, "x2": self.current_image_width,"y2": self.current_image_height}
			elif idx == 2:
				return {"x1": 0, "y1": 0, "x2": self.current_image_width / 2, "y2": self.current_image_height}
		else:
			return {"x1": 0, "y1": 0, "x2": self.current_image_width, "y2": self.current_image_height}

	def find_best_crop_pos_by_rule(self, idx):
		if len(self.image_list[self.current_image_index]["to"]) > 1:
			return self.find_crop_pos_by_full(idx)
		else:
			ratio = self.current_image_width / self.current_image_height
			for rule in self.method["rules"]:
				if rule["wh_ratio_from"] <= ratio <= rule["wh_ratio_to"]:
					#print("found method")
					x1 = int(rule["crop_x1"] * self.current_image_width)
					y1 = int(rule["crop_y1"] * self.current_image_height)
					x2 = int(rule["crop_x2"] * self.current_image_width)
					y2 = int(rule["crop_y2"] * self.current_image_height)
					return {"x1":x1,"y1":y1,"x2":x2,"y2":y2}

		return None

	def get_image_pos_by_frame(self,frame_rect):
		prefix_x = self.ui.graphics_view.geometry().x()
		prefix_y = self.ui.graphics_view.geometry().y()
		x1 = (frame_rect.x()-prefix_x) / self.current_image_ratio
		y1 = (frame_rect.y()-prefix_y) / self.current_image_ratio
		x2 = frame_rect.width() / self.current_image_ratio + x1
		y2 = frame_rect.height() / self.current_image_ratio + y1
		return [x1,y1,x2,y2]

	def make_crop(self):
		current_file_info = self.image_list[self.current_image_index]
		img = Image.open(current_file_info["from"])

		to_file = current_file_info["to"][0]
		x1 = self.ui.spin_frame1_x1.value()
		y1 = self.ui.spin_frame1_y1.value()
		x2 = self.ui.spin_frame1_x2.value()
		y2 = self.ui.spin_frame1_y2.value()
		self.crop_image_by_pos_to_file(img,x1,y1,x2,y2,to_file)

		if len(current_file_info["to"]) > 1:
			to_file = current_file_info["to"][1]
			x1 = self.ui.spin_frame2_x1.value()
			y1 = self.ui.spin_frame2_y1.value()
			x2 = self.ui.spin_frame2_x2.value()
			y2 = self.ui.spin_frame2_y2.value()
			self.crop_image_by_pos_to_file(img, x1, y1, x2, y2, to_file)

		if self.ui.chk_remove_source.isChecked():
			os.remove(current_file_info["from"])
		return True

	def crop_image_by_pos_to_file(self,img,x1,y1,x2,y2,to_file):
		img_to = img.crop((x1, y1, x2, y2))
		ext = util.get_ext(to_file)
		if ext in ("jpg","jpeg"):
			img_to.save(to_file, quality=int(MY_CONFIG.get("general", "jpg_quality")))
		else:
			img_to.save(to_file)

	#action
	def frame_spin_value_changed(self):
		if not self.is_updating_frame_child :
			self.update_crop_frame_by_pos_value()

	def center_pos_of_parent(self):
		if self.windowState() != QtCore.Qt.WindowMaximized:
			qr = self.main_controller.frameGeometry()
			x = qr.left() + (qr.width() - self.width()) / 2
			y = qr.top() + (qr.height() - self.height()) / 2
			self.move(x, y)

	def btn_ignore_clicked(self):
		self.process_next_image()

	def btn_process_clicked(self):
		self.make_crop()
		self.process_next_image()

	def btn_use_rule_clicked(self):
		pos = self.find_best_crop_pos_by_rule(1)
		if pos:
			self.set_pos_to_frame(pos,"frame1")
		if len(self.image_list[self.current_image_index]["to"]) > 1:
			pos = self.find_best_crop_pos_by_rule(2)
			if pos:
				self.set_pos_to_frame(pos, "frame2")

	def btn_full_of_image_clicked(self):
		if len(self.image_list[self.current_image_index]["to"]) > 1:
			pos = self.find_crop_pos_by_full(1)
			self.set_pos_to_frame(pos, "frame1")
			pos = self.find_crop_pos_by_full(2)
			self.set_pos_to_frame(pos, "frame2")
		else:
			pos = self.find_crop_pos_by_full(1)
			self.set_pos_to_frame(pos, "frame1")

	def btn_exchange_clicked(self):
		if self.ui.btn_exchange.isEnabled():
			rect1 = self.crop_frame_controllers[0].get_frame_rect()
			rect2 = self.crop_frame_controllers[1].get_frame_rect()
			self.crop_frame_controllers[0].move_frame_to(rect2)
			self.crop_frame_controllers[1].move_frame_to(rect1)
			tmp_real_pos_rect1 = self.crop_frame_controllers[0].get_real_pos_rect()
			tmp_real_pos_rect2 = self.crop_frame_controllers[1].get_real_pos_rect()
			self.crop_frame_controllers[0].set_real_pos_rect(tmp_real_pos_rect2)
			self.crop_frame_controllers[1].set_real_pos_rect(tmp_real_pos_rect1)
			self.frame_changed(self.crop_frame_controllers[0])
			self.frame_changed(self.crop_frame_controllers[1])

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

	def btn_quit_clicked(self):
		self.close()

	# callback
	def frame_changed(self,frame_controller):
		if frame_controller in self.crop_frame_controllers:
			index = self.crop_frame_controllers.index(frame_controller)
			if 1 >= index >= 0:
				# x1,y1,x2,y2 = self.get_image_pos_by_frame(frame_controller.get_frame_rect())
				self.is_updating_frame_child = True
				real_pos_rect = frame_controller.get_real_pos_rect()
				if index == 0:
					# self.ui.spin_frame1_x1.setValue(x1)
					# self.ui.spin_frame1_x2.setValue(x2)
					# self.ui.spin_frame1_y1.setValue(y1)
					# self.ui.spin_frame1_y2.setValue(y2)
					self.ui.spin_frame1_x1.setValue(real_pos_rect["x1"])
					self.ui.spin_frame1_x2.setValue(real_pos_rect["x2"])
					self.ui.spin_frame1_y1.setValue(real_pos_rect["y1"])
					self.ui.spin_frame1_y2.setValue(real_pos_rect["y2"])
				elif index == 1:
					# self.ui.spin_frame2_x1.setValue(x1)
					# self.ui.spin_frame2_x2.setValue(x2)
					# self.ui.spin_frame2_y1.setValue(y1)
					# self.ui.spin_frame2_y2.setValue(y2)
					self.ui.spin_frame2_x1.setValue(real_pos_rect["x1"])
					self.ui.spin_frame2_x2.setValue(real_pos_rect["x2"])
					self.ui.spin_frame2_y1.setValue(real_pos_rect["y1"])
					self.ui.spin_frame2_y2.setValue(real_pos_rect["y2"])
				self.is_updating_frame_child = False
				pass

	# internal
	def show(self):
		super().show()
		self.center_pos_of_parent()
		self.start_image_process()
		pass

	def resizeEvent(self, event):
		#print("resize")
		self.resize_element()

	@staticmethod
	def setModal(is_modal):
		#print("set modal %d" % is_modal)
		pass

	def closeEvent(self, event):
		if not self.is_finish_job_flag:
			if util.confirm_box(TRSM("Confirm to quit processing?"),self):
				event.accept()
			else:
				event.ignore()
		else:
			event.accept()

	def keyPressEvent(self, e):
		if e.key() == Qt.Key_F1:
			self.btn_process_clicked()
		if e.key() == Qt.Key_F2:
			self.btn_ignore_clicked()
		if e.key() == Qt.Key_F3:
			self.btn_use_rule_clicked()
		if e.key() == Qt.Key_F4:
			self.btn_full_of_image_clicked()
		if e.key() == Qt.Key_F8:
			self.btn_exchange_clicked()
		if e.key() == Qt.Key_F11:
			self.btn_full_screen_clicked()
		if e.key() == Qt.Key_F12:
			self.btn_quit_clicked()

	def eventFilter(self, obj, event):
		if obj == self.ui.cbx_size_policy and event.type() == event.KeyPress:
			self.keyPressEvent(event)
			return True
		return super(CropWindowController, self).eventFilter(obj,event)
