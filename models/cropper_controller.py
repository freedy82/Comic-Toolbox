from PyQt5 import QtCore, QtWidgets
from const import *
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem
from uis.main_window import Ui_MainWindow
from .cropper_worker import CropperWorker

from .crop_window_controller import CropWindowController

import util

class CropperController(object):
	METHODS = [
		{"name":"Auto crop japanese comic (Simple Rules)","rules":[
			{
				"wh_ratio_from": 1.12,
				"wh_ratio_to": 1.18,
				"crop_x1": 493.0 / 1520.0,
				"crop_y1": 0,
				"crop_x2": 1394.0 / 1520.0,
				"crop_y2": 1
			},
			{
				"wh_ratio_from": 1.25,
				"wh_ratio_to": 1.45,
				"crop_x1": 0,
				"crop_y1": 0,
				"crop_x2": 0.5,
				"crop_y2": 1
			},
			{
				"wh_ratio_from": 1.85,
				"wh_ratio_to": 1.95,
				"crop_x1": 390.0 / 1960.0,
				"crop_y1": 0,
				"crop_x2": 1130.0 / 1960.0,
				"crop_y2": 1
			},
			{
				"wh_ratio_from": 1.95,
				"wh_ratio_to": 2.0,
				"crop_x1": 416.0 / 1960.0,
				"crop_y1": 0,
				"crop_x2": 1142.0 / 1960.0,
				"crop_y2": 1
			}
		]},
		{"name":"Manual Crop", "rules":[]}
	]

	MODES = [{"name":"Cover mode"},{"name":"2 page split mode"}]

	def __init__(self, app=None, ui: Ui_MainWindow = None, main_controller=None):
		self.app = app
		self.ui = ui
		self.main_controller = main_controller
		self.cropper_worker = None
		self.crop_window_controller = None
		self.folder_list = []
		self.setup_control()

		self.crop_window_controller = CropWindowController(app=self.app, main_controller=self.main_controller, method=self.METHODS[0])

		pass

	def setup_control(self):
		download_folder = MY_CONFIG.get("general", "download_folder")
		#download_folder = "F:/comics/測試"
		self.ui.txt_cropper_from_folder.setText(download_folder)

		for method in self.METHODS:
			self.ui.cbx_cropper_method.addItem(TRSM(method["name"]))
		for mode in self.MODES:
			self.ui.cbx_cropper_mode.addItem(TRSM(mode["name"]))

		self.ui.cbx_cropper_file_exist.addItems([TRSM("Skip"),TRSM("Overwrite")])
		self.ui.cbx_cropper_remove_source.addItems([TRSM("No"),TRSM("Yes")])

		self.retranslateUi()
		#self.ui.cbx_cropper_method.setCurrentIndex(1)
		#self.ui.cbx_cropper_mode.setCurrentIndex(1)

		#action
		self.ui.btn_cropper_from_folder.clicked.connect(self.btn_cropper_from_folder_clicked)
		self.ui.btn_cropper_folder_scan.clicked.connect(self.btn_cropper_folder_scan_clicked)

		self.ui.btn_cropper_select.clicked.connect(self.btn_cropper_select_clicked)
		self.ui.btn_cropper_unselect.clicked.connect(self.btn_cropper_unselect_clicked)
		self.ui.btn_cropper_select_all.clicked.connect(self.btn_cropper_select_all_clicked)
		self.ui.btn_cropper_unselect_all.clicked.connect(self.btn_cropper_unselect_all_clicked)

		self.ui.btn_cropper_start.clicked.connect(self.btn_cropper_start_clicked)
		self.ui.btn_cropper_cancel.clicked.connect(self.btn_cropper_cancel_clicked)
		self.ui.cbx_cropper_mode.currentIndexChanged.connect(self.cbx_cropper_mode_changed)

		pass

	def retranslateUi(self):
		for idx, method in enumerate(self.METHODS):
			self.ui.cbx_cropper_method.setItemText(idx,TRSM(method["name"]))

		for idx, mode in enumerate(self.MODES):
			self.ui.cbx_cropper_mode.setItemText(idx,TRSM(mode["name"]))

		self.ui.cbx_cropper_file_exist.setItemText(0,TRSM("Skip"))
		self.ui.cbx_cropper_file_exist.setItemText(1,TRSM("Overwrite"))

		self.ui.cbx_cropper_remove_source.setItemText(0,TRSM("No"))
		self.ui.cbx_cropper_remove_source.setItemText(1,TRSM("Yes"))

		if self.crop_window_controller:
			self.crop_window_controller.retranslateUi()

	#action
	def btn_cropper_from_folder_clicked(self):
		old_folder_path = self.ui.txt_cropper_from_folder.text()
		if old_folder_path == "":
			old_folder_path = "./"
		folder_path = QFileDialog.getExistingDirectory(self.main_controller,TRSM("Open folder"), old_folder_path)
		if folder_path != "":
			self.ui.txt_cropper_from_folder.setText(folder_path)
			self.ui.list_cropper_folder.clear()
			self.ui.btn_cropper_select.setEnabled(False)
			self.ui.btn_cropper_unselect.setEnabled(False)
			self.ui.btn_cropper_select_all.setEnabled(False)
			self.ui.btn_cropper_unselect_all.setEnabled(False)
			self.ui.btn_cropper_start.setEnabled(False)
			self.ui.btn_cropper_cancel.setEnabled(False)

		pass

	def btn_cropper_folder_scan_clicked(self):
		folder_path = self.ui.txt_cropper_from_folder.text()
		folders = os.listdir(folder_path)
		folders.sort()
		final_folders = []
		for folder in folders:
			if os.path.isdir(os.path.join(folder_path,folder)):
				final_folders.append(folder)
		self.folder_list = final_folders
		self._update_folder_list()

		if len(final_folders) == 0:
			util.msg_box(TRSM("Not sub-folder found"),self.main_controller)
			pass

	def btn_cropper_select_clicked(self):
		items = self.ui.list_cropper_folder.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Checked)
		pass

	def btn_cropper_unselect_clicked(self):
		items = self.ui.list_cropper_folder.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Unchecked)
		pass

	def btn_cropper_select_all_clicked(self):
		for i in range(self.ui.list_cropper_folder.count()):
			self.ui.list_cropper_folder.item(i).setCheckState(QtCore.Qt.Checked)

	def btn_cropper_unselect_all_clicked(self):
		for i in range(self.ui.list_cropper_folder.count()):
			self.ui.list_cropper_folder.item(i).setCheckState(QtCore.Qt.Unchecked)

	def btn_cropper_start_clicked(self):
		total_need_crop_list = []
		for i in range(self.ui.list_cropper_folder.count()):
			if self.ui.list_cropper_folder.item(i).checkState() == QtCore.Qt.Checked:
				total_need_crop_list.append(self.folder_list[i])
		#print(total_need_crop_list)

		if len(total_need_crop_list) > 0:
			method_index = self.ui.cbx_cropper_method.currentIndex()
			self.ui.pgb_cropper.setMaximum(0)
			self.ui.pgb_cropper.setValue(0)
			self.ui.btn_cropper_start.setEnabled(False)
			self.ui.btn_cropper_cancel.setEnabled(True)
			self.ui.log_cropper.clear()
			self.cropper_worker = CropperWorker(
				from_folder=self.ui.txt_cropper_from_folder.text(),
				methods=self.METHODS[method_index],
				is_overwrite=bool(self.ui.cbx_cropper_file_exist.currentIndex()),
				is_remove_source=bool(self.ui.cbx_cropper_remove_source.currentIndex()),
				sub_folders=total_need_crop_list
			)
			self.cropper_worker.set_crop_mode(self.ui.cbx_cropper_mode.currentIndex() + 1)

			if method_index == 0:
				self.cropper_worker.set_is_only_get_list(False)
				pass
			elif method_index == 1:
				self.cropper_worker.set_is_only_get_list(True)

			self.cropper_worker.trigger.connect(self.cropper_trigger)
			self.cropper_worker.canceled.connect(self.cropper_canceled)
			self.cropper_worker.finished.connect(self.cropper_finished)
			self.cropper_worker.start()
		else:
			util.msg_box(TRSM("Please select at least one folder to crop"),self.main_controller)
			pass

		pass

	def btn_cropper_cancel_clicked(self):
		self.cropper_worker.stop()
		pass

	def cbx_cropper_mode_changed(self):
		idx = self.ui.cbx_cropper_mode.currentIndex()
		if idx == 1:
			self.ui.cbx_cropper_method.setCurrentIndex(1)
			self.ui.cbx_cropper_method.setEnabled(False)
			self.ui.cbx_cropper_remove_source.setCurrentIndex(1)
		else:
			self.ui.cbx_cropper_method.setEnabled(True)

	#callback
	def cropper_trigger(self, message, current_action, total_action):
		self.ui.pgb_cropper.setMaximum(total_action)
		self.ui.pgb_cropper.setValue(current_action)
		if message != "":
			self.ui.log_cropper.append(message)
		pass

	def cropper_finished(self):
		if self.cropper_worker.get_is_only_get_list():
			image_list = self.cropper_worker.get_process_list()
			if len(image_list)>0:
				self.crop_window_controller.set_image_list(image_list)
				self.crop_window_controller.set_is_remove_source(bool(self.ui.cbx_cropper_remove_source.currentIndex()))
				self.crop_window_controller.show()
			else:
				util.msg_box(TRSM("Not image to cropping"), self.main_controller)
		else:
			self.ui.log_cropper.append(TRSM("Crop image finished!"))

		self.ui.btn_cropper_start.setEnabled(True)
		self.ui.btn_cropper_cancel.setEnabled(False)
		if self.ui.pgb_cropper.maximum() > 0:
			self.ui.pgb_cropper.setValue(self.ui.pgb_cropper.maximum())
		else:
			self.ui.pgb_cropper.setMaximum(100)
			self.ui.pgb_cropper.setValue(100)
		self.cropper_worker = None
		pass

	def cropper_canceled(self):
		self.ui.log_cropper.append(TRSM("Crop image canceled!"))
		self.ui.btn_cropper_start.setEnabled(True)
		self.ui.btn_cropper_cancel.setEnabled(False)
		self.cropper_worker = None

	#internal
	def _update_folder_list(self):
		self.ui.list_cropper_folder.clear()

		for idx, tmp_folder in enumerate(self.folder_list):
			item = QListWidgetItem()
			item.setText(tmp_folder)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(QtCore.Qt.Checked)
			self.ui.list_cropper_folder.addItem(item)

		if self.ui.list_cropper_folder.count() > 0:
			self.ui.btn_cropper_select.setEnabled(True)
			self.ui.btn_cropper_unselect.setEnabled(True)
			self.ui.btn_cropper_select_all.setEnabled(True)
			self.ui.btn_cropper_unselect_all.setEnabled(True)
			self.ui.btn_cropper_start.setEnabled(True)
		else:
			self.ui.btn_cropper_select.setEnabled(False)
			self.ui.btn_cropper_unselect.setEnabled(False)
			self.ui.btn_cropper_select_all.setEnabled(False)
			self.ui.btn_cropper_unselect_all.setEnabled(False)
			self.ui.btn_cropper_start.setEnabled(False)

		pass
