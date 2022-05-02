from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal

from models.const import *
from uis import crop_frame

class CropFrameController(QtWidgets.QMainWindow):
	frame_changed = pyqtSignal(object)

	def __init__(self,app,main_controller,parent,parent_controller):
		super().__init__()
		self.app = app
		self.parent = parent
		self.main_controller = main_controller
		self.parent_controller = parent_controller
		self.ui = crop_frame.Ui_MainWindow()
		#hack for ui code overwrite problem
		rect = self.parent.frameGeometry()
		style_sheet = self.parent.styleSheet()
		self.ui.setupUi(self.parent)
		self.parent.setGeometry(rect)
		self.parent.setStyleSheet(style_sheet)

		self.setup_control()
		self.current_drag_obj = None
		self.allow_rect = None
		self.org_frame_rect = None
		self.is_moving_frame = False
		self.start_pos = None
		self.start_frame = None
		self.real_pos_rect = {}

	def set_allow_rect(self,allow_rect):
		self.allow_rect = allow_rect

	def setup_control(self):
		# GUI
		self.retranslateUi()

		#action
		self.ui.lbl_lt.installEventFilter(self)
		self.ui.lbl_rt.installEventFilter(self)
		self.ui.lbl_lb.installEventFilter(self)
		self.ui.lbl_rb.installEventFilter(self)

		self.ui.lbl_l.installEventFilter(self)
		self.ui.lbl_r.installEventFilter(self)
		self.ui.lbl_t.installEventFilter(self)
		self.ui.lbl_b.installEventFilter(self)

		self.ui.lbl_center.installEventFilter(self)
		self.ui.frame.installEventFilter(self)
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)
		pass

	def show_frame(self):
		self.ui.frame.setVisible(True)

	def move_frame_to(self,rect):
		self.ui.frame.setGeometry(rect)

	def get_frame_rect(self):
		return self.ui.frame.frameGeometry()

	def is_frame_show(self):
		return self.ui.frame.isVisible()

	def remove_frame(self):
		self.ui.frame.setParent(None)

	def set_border_color(self,color="#00FF00"):
		self.ui.frame.setStyleSheet(f"background: rgba(255,255,255,0.8);border: 1px solid {color};")

	def set_display_name(self,display_name):
		self.ui.lbl_center.setText(display_name)

	def set_real_pos_rect(self,real_pos_rect):
		self.real_pos_rect = real_pos_rect

	def get_real_pos_rect(self):
		return self.real_pos_rect

	def update_real_pos_by_frame_changed(self):
		current_frame = self.ui.frame.frameGeometry()
		#print(f"current_frame: {current_frame}")
		image_ratio = self.parent_controller.get_current_image_ratio()
		#print(f"image_ratio: {image_ratio}")
		x1_change = (current_frame.x() - self.org_frame_rect.x()) / image_ratio
		y1_change = (current_frame.y() - self.org_frame_rect.y()) / image_ratio
		x2_change = (current_frame.x() + current_frame.width() - self.org_frame_rect.x() - self.org_frame_rect.width()) / image_ratio
		y2_change = (current_frame.y() + current_frame.height() - self.org_frame_rect.y() - self.org_frame_rect.height()) / image_ratio
		#print(f"change: {x1_change}-{y1_change}-{x2_change}-{y2_change}")
		self.real_pos_rect = {
			"x1": int(self.real_pos_rect["x1"] + x1_change),
			"y1": int(self.real_pos_rect["y1"] + y1_change),
			"x2": int(self.real_pos_rect["x2"] + x2_change),
			"y2": int(self.real_pos_rect["y2"] + y2_change),
		}
		#print(f"self.real_pos_rect: {self.real_pos_rect}")
		#print(f"{x1_change} - {y1_change} - {x2_change} - {y2_change}")

	#action
	def eventFilter(self, obj, event):
		obj_set = [
			self.ui.lbl_lt, self.ui.lbl_rt, self.ui.lbl_lb, self.ui.lbl_rb,self.ui.lbl_center,
			self.ui.lbl_l,self.ui.lbl_r,self.ui.lbl_t,self.ui.lbl_b
		]
		if obj in obj_set and event.type() == QtCore.QEvent.MouseButtonPress:
			#print("mouse down")
			self.current_drag_obj = obj
			self.org_frame_rect = self.ui.frame.frameGeometry()
			self.start_pos = self.current_drag_obj.mapToGlobal(event.pos())
			self.start_frame = self.get_frame_rect()
			self.ui.frame.raise_()
		elif obj in obj_set and event.type() == QtCore.QEvent.MouseButtonRelease:
			#print("mouse up")
			self.current_drag_obj = None
			self.start_pos = None
			if self.ui.frame.frameGeometry() != self.org_frame_rect:
				#print("changed!")
				self.update_real_pos_by_frame_changed()
				self.frame_changed.emit(self)
			self.org_frame_rect = None
		elif obj in obj_set and event.type() == QtCore.QEvent.MouseMove:
			if self.current_drag_obj and not self.is_moving_frame:
				#print("mouse move")
				global_pos = self.current_drag_obj.mapToGlobal(event.pos())
				self.lbl_mouse_move(self.current_drag_obj, global_pos - self.start_pos)

		return super().eventFilter(obj,event)

	def lbl_mouse_move(self, obj, pos):
		#print("mouse move",pos)
		if obj == self.ui.lbl_lt:
			x = self.org_frame_rect.x() + pos.x()
			y = self.org_frame_rect.y() + pos.y()
			width = self.org_frame_rect.width() - pos.x()
			height = self.org_frame_rect.height() - pos.y()
		elif obj == self.ui.lbl_lb:
			x = self.org_frame_rect.x() + pos.x()
			y = self.org_frame_rect.y()
			width = self.org_frame_rect.width() - pos.x()
			height = self.org_frame_rect.height() + pos.y()
		elif obj == self.ui.lbl_rt:
			x = self.org_frame_rect.x()
			y = self.org_frame_rect.y() + pos.y()
			width = self.org_frame_rect.width() + pos.x()
			height = self.org_frame_rect.height() - pos.y()
		elif obj == self.ui.lbl_rb:
			x = self.org_frame_rect.x()
			y = self.org_frame_rect.y()
			width = self.org_frame_rect.width() + pos.x()
			height = self.org_frame_rect.height() + pos.y()
		elif obj == self.ui.lbl_t:
			x = self.org_frame_rect.x()
			y = self.org_frame_rect.y() + pos.y()
			width = self.org_frame_rect.width()
			height = self.org_frame_rect.height() - pos.y()
		elif obj == self.ui.lbl_l:
			x = self.org_frame_rect.x() + pos.x()
			y = self.org_frame_rect.y()
			width = self.org_frame_rect.width() - pos.x()
			height = self.org_frame_rect.height()
		elif obj == self.ui.lbl_b:
			x = self.org_frame_rect.x()
			y = self.org_frame_rect.y()
			width = self.org_frame_rect.width()
			height = self.org_frame_rect.height() + pos.y()
		elif obj == self.ui.lbl_r:
			x = self.org_frame_rect.x()
			y = self.org_frame_rect.y()
			width = self.org_frame_rect.width() + pos.x()
			height = self.org_frame_rect.height()
		elif obj == self.ui.lbl_center:
			x = self.org_frame_rect.x() + pos.x()
			y = self.org_frame_rect.y() + pos.y()
			width = self.org_frame_rect.width()
			height = self.org_frame_rect.height()
		else:
			x = self.org_frame_rect.x()
			y = self.org_frame_rect.y()
			width = self.org_frame_rect.width()
			height = self.org_frame_rect.height()

		#print("allow frame ", self.allow_rect)
		#print("target frame %d,%d,%d,%d" % (x,y,width,height))
		if obj == self.ui.lbl_center:
			target_rect = self.refine_change_rect_with_allow_rect(x, y, width, height, True)
		else:
			target_rect = self.refine_change_rect_with_allow_rect(x, y, width, height,False)
		#print("final rect ", target_rect)
		if target_rect:
			self.ui.frame.setGeometry(target_rect)

	def refine_change_rect_with_allow_rect(self,x,y,width,height,is_fix_size=False):
		allow_x = self.allow_rect.x()
		allow_y = self.allow_rect.y()
		allow_width = self.allow_rect.width()
		allow_height = self.allow_rect.height()
		allow_x2 = allow_x + allow_width
		allow_y2 = allow_y + allow_height

		if x < allow_x:
			if not is_fix_size:
				width -= (allow_x - x)
			x = allow_x
		if y < allow_y:
			if not is_fix_size:
				height -= (allow_y - y)
			y = allow_y
		if x + width > allow_x2:
			if not is_fix_size:
				width = allow_x2 - x
			else:
				x = allow_x2 - width
		if y + height > allow_y2:
			if not is_fix_size:
				height = allow_y2 - y
			else:
				y = allow_y2 - height

		return QtCore.QRect(x,y,width,height)


