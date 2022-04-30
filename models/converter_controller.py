from PyQt5.QtWidgets import QFileDialog, QListWidgetItem

from models import util
from models.const import *
from uis.main_window import Ui_MainWindow
from models.converter_worker import ConverterWorker
from models.image_filter_window_controller import ImageFilterWindowController


class ConverterController(object):
	MODES = [
		{"from_exts": util.remove_element_of_tuple(IMAGE_EXTS,"jpg"), "to_ext":"jpg", "enable_real_cugan": False},
		{"from_exts": util.remove_element_of_tuple(IMAGE_EXTS,"png"), "to_ext":"png", "enable_real_cugan": False},
		{"from_exts": IMAGE_EXTS, "to_ext": "jpg", "enable_real_cugan": False},
		{"from_exts": IMAGE_EXTS, "to_ext": "png", "enable_real_cugan": False},
		{"from_exts": util.remove_element_of_tuple(IMAGE_EXTS,"gif"), "to_ext": "jpg", "enable_real_cugan": True},
		{"from_exts": util.remove_element_of_tuple(IMAGE_EXTS,"gif"), "to_ext": "png", "enable_real_cugan": True}
	]

	def __init__(self, app=None, ui: Ui_MainWindow = None, main_controller=None):
		self.app = app
		self.ui = ui
		self.main_controller = main_controller
		self.folder_list = []
		self.converter_worker = None
		self.image_filter_window_controller = ImageFilterWindowController(app=self.app, main_controller=self.main_controller)
		self.setup_control()

		pass

	def setup_control(self):
		convert_from_folder = MY_CONFIG.get("general", "convert_from_folder")
		if convert_from_folder == "":
			convert_from_folder = MY_CONFIG.get("general", "download_folder")
		#convert_from_folder = "F:/comics/測試"
		self.ui.txt_converter_from_folder.setText(convert_from_folder)

		convert_to_folder = MY_CONFIG.get("general", "convert_to_folder")
		if convert_to_folder == "":
			convert_to_folder = MY_CONFIG.get("general", "download_folder")
		#convert_to_folder = "F:/comics/測試2"
		self.ui.txt_converter_to_folder.setText(convert_to_folder)

		for mode in self.MODES:
			label = ", ".join(mode["from_exts"]) + " -> " + mode["to_ext"]
			if mode["to_ext"] in mode["from_exts"]:
				label += " ("+TRSM("Force convert mode")+")"
			self.ui.cbx_converter_mode.addItem(label)
		self.ui.cbx_converter_exist.addItems([TRSM("Skip"),TRSM("Overwrite")])
		self.ui.cbx_converter_remove_source.addItems([TRSM("No"),TRSM("Yes")])
		self.ui.cbx_converter_filter.addItems([TRSM("No"),TRSM("Yes")])

		self.retranslateUi()

		#action
		self.ui.btn_converter_from_browser.clicked.connect(self.btn_converter_from_browser_clicked)
		self.ui.btn_converter_folder_scan.clicked.connect(self.btn_converter_folder_scan_clicked)

		self.ui.btn_converter_select.clicked.connect(self.btn_converter_select_clicked)
		self.ui.btn_converter_unselect.clicked.connect(self.btn_converter_unselect_clicked)
		self.ui.btn_converter_select_all.clicked.connect(self.btn_converter_select_all_clicked)
		self.ui.btn_converter_unselect_all.clicked.connect(self.btn_converter_unselect_all_clicked)

		self.ui.btn_converter_to_browser.clicked.connect(self.btn_converter_to_browser_clicked)
		self.ui.btn_converter_change_filter.clicked.connect(self.btn_converter_change_filter_clicked)
		self.ui.btn_converter_start.clicked.connect(self.btn_converter_start_clicked)
		self.ui.btn_converter_cancel.clicked.connect(self.btn_converter_cancel_clicked)
		pass

	def retranslateUi(self):
		for idx,mode in enumerate(self.MODES):
			label = ", ".join(mode["from_exts"]) + " -> " + mode["to_ext"]
			if "enable_real_cugan" in mode and mode["enable_real_cugan"]:
				label += " ( "+TRSM("Real-CUGAN AI enhance mode")+" )"
			elif mode["to_ext"] in mode["from_exts"]:
				label += " ( "+TRSM("Force convert mode")+" )"
			self.ui.cbx_converter_mode.setItemText(idx,label)

		self.ui.cbx_converter_exist.setItemText(0,TRSM("Skip"))
		self.ui.cbx_converter_exist.setItemText(1,TRSM("Overwrite"))

		self.ui.cbx_converter_remove_source.setItemText(0,TRSM("No"))
		self.ui.cbx_converter_remove_source.setItemText(1,TRSM("Yes"))

		self.ui.cbx_converter_filter.setItemText(0,TRSM("No"))
		self.ui.cbx_converter_filter.setItemText(1,TRSM("Yes"))

		if self.image_filter_window_controller:
			self.image_filter_window_controller.retranslateUi()

	#action
	def btn_converter_from_browser_clicked(self):
		old_folder_path = self.ui.txt_converter_from_folder.text()
		if old_folder_path == "":
			old_folder_path = "./"
		folder_path = QFileDialog.getExistingDirectory(self.main_controller,TRSM("Open folder"), old_folder_path)
		if folder_path != "":
			self.ui.txt_converter_from_folder.setText(folder_path)
			self.ui.list_converter_folder.clear()
			self.ui.btn_converter_select.setEnabled(False)
			self.ui.btn_converter_unselect.setEnabled(False)
			self.ui.btn_converter_select_all.setEnabled(False)
			self.ui.btn_converter_unselect_all.setEnabled(False)
			self.ui.btn_converter_start.setEnabled(False)
			self.ui.btn_converter_cancel.setEnabled(False)
			MY_CONFIG.set("general", "convert_from_folder", folder_path)
			MY_CONFIG.save()
		pass

	def btn_converter_folder_scan_clicked(self):
		folder_path = self.ui.txt_converter_from_folder.text()
		final_folders = []
		try:
			folders = os.listdir(folder_path)
			folders.sort()
			for folder in folders:
				if os.path.isdir(os.path.join(folder_path,folder)):
					final_folders.append(folder)
		except Exception:
			pass
		self.folder_list = final_folders
		self._update_folder_list()

		if len(final_folders) == 0:
			util.msg_box(TRSM("Not sub-folder found"),self.main_controller)
		pass

	def btn_converter_select_clicked(self):
		items = self.ui.list_converter_folder.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Checked)
		pass

	def btn_converter_unselect_clicked(self):
		items = self.ui.list_converter_folder.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Unchecked)
		pass

	def btn_converter_select_all_clicked(self):
		for i in range(self.ui.list_converter_folder.count()):
			self.ui.list_converter_folder.item(i).setCheckState(QtCore.Qt.Checked)

	def btn_converter_unselect_all_clicked(self):
		for i in range(self.ui.list_converter_folder.count()):
			self.ui.list_converter_folder.item(i).setCheckState(QtCore.Qt.Unchecked)

	def btn_converter_to_browser_clicked(self):
		old_folder_path = self.ui.txt_converter_to_folder.text()
		if old_folder_path == "":
			old_folder_path = "./"
		folder_path = QFileDialog.getExistingDirectory(self.main_controller,TRSM("Open folder"), old_folder_path)
		if folder_path != "":
			self.ui.txt_converter_to_folder.setText(folder_path)
			MY_CONFIG.set("general", "convert_to_folder", folder_path)
			MY_CONFIG.save()
		pass

	def btn_converter_change_filter_clicked(self):
		folder = self.ui.txt_converter_from_folder.text()
		images = util.get_number_of_images_from_folder(folder,20)
		if len(images) > 0:
			self.image_filter_window_controller.set_image_list(images)
			self.image_filter_window_controller.show()
		else:
			util.msg_box(TRSM("Please select a folder with contain at least one image"),self.main_controller)
			pass

	def btn_converter_start_clicked(self):
		# check real-cugan
		mode_index = self.ui.cbx_converter_mode.currentIndex()
		if self.MODES[mode_index]["enable_real_cugan"] and MY_CONFIG.get("real-cugan", "exe_location") == "":
			util.msg_box(TRSM("Please choose the real-cugan exe location in settings"),self.main_controller)
			return

		total_need_convert_list = []
		for i in range(self.ui.list_converter_folder.count()):
			if self.ui.list_converter_folder.item(i).checkState() == QtCore.Qt.Checked:
				total_need_convert_list.append(self.folder_list[i])
		#print(total_need_convert_list)

		if len(total_need_convert_list) > 0:
			self.ui.pgb_converter.setMaximum(0)
			self.ui.pgb_converter.setValue(0)
			self.ui.btn_converter_start.setEnabled(False)
			self.ui.btn_converter_cancel.setEnabled(True)
			self.ui.log_converter.clear()

			self.converter_worker = ConverterWorker(
				from_folder=self.ui.txt_converter_from_folder.text(),
				to_folder=self.ui.txt_converter_to_folder.text(),
				from_exts=self.MODES[mode_index]["from_exts"],
				to_ext=self.MODES[mode_index]["to_ext"],
				is_overwrite=bool(self.ui.cbx_converter_exist.currentIndex()),
				remove_source=bool(self.ui.cbx_converter_remove_source.currentIndex()),
				sub_folders=total_need_convert_list,
				is_use_filter=bool(self.ui.cbx_converter_filter.currentIndex()),
				enable_real_cugan=self.MODES[mode_index]["enable_real_cugan"]
			)
			self.converter_worker.trigger.connect(self.convert_trigger)
			self.converter_worker.canceled.connect(self.convert_canceled)
			self.converter_worker.finished.connect(self.convert_finished)
			self.converter_worker.start()
		else:
			util.msg_box(TRSM("Please select at least one folder to convert"),self.main_controller)

		pass

	def btn_converter_cancel_clicked(self):
		self.converter_worker.stop()

	#callback
	def convert_trigger(self,message,current_action,total_action):
		self.ui.pgb_converter.setMaximum(total_action)
		self.ui.pgb_converter.setValue(current_action)
		if message != "":
			self.ui.log_converter.append(message)
		pass

	def convert_finished(self):
		self.ui.log_converter.append(TRSM("Convert finished!"))
		self.ui.btn_converter_start.setEnabled(True)
		self.ui.btn_converter_cancel.setEnabled(False)
		if self.ui.pgb_converter.maximum() > 0:
			self.ui.pgb_converter.setValue(self.ui.pgb_converter.maximum())
		else:
			self.ui.pgb_converter.setMaximum(100)
			self.ui.pgb_converter.setValue(100)
		self.converter_worker = None
		pass

	def convert_canceled(self):
		self.ui.log_converter.append(TRSM("Convert canceled!"))
		self.ui.btn_converter_start.setEnabled(True)
		self.ui.btn_converter_cancel.setEnabled(False)
		self.converter_worker = None

	#internal function
	def _update_folder_list(self):
		self.ui.list_converter_folder.clear()

		for idx, tmp_folder in enumerate(self.folder_list):
			item = QListWidgetItem()
			item.setText(tmp_folder)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(QtCore.Qt.Checked)
			self.ui.list_converter_folder.addItem(item)

		if self.ui.list_converter_folder.count() > 0:
			self.ui.btn_converter_select.setEnabled(True)
			self.ui.btn_converter_unselect.setEnabled(True)
			self.ui.btn_converter_select_all.setEnabled(True)
			self.ui.btn_converter_unselect_all.setEnabled(True)
			self.ui.btn_converter_start.setEnabled(True)
		else:
			self.ui.btn_converter_select.setEnabled(False)
			self.ui.btn_converter_unselect.setEnabled(False)
			self.ui.btn_converter_select_all.setEnabled(False)
			self.ui.btn_converter_unselect_all.setEnabled(False)
			self.ui.btn_converter_start.setEnabled(False)

		pass
