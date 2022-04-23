from PyQt5.QtWidgets import QFileDialog, QListWidgetItem

from const import *
import util
from uis.main_window import Ui_MainWindow
from models.archiver_worker import ArchiverWorker


class ArchiverController(object):
	FORMATS = [
		{"desc": "Comic Book Zip", "ext": "cbz"},
		{"desc": "ePub", "ext": "epub"},
		{"desc": "Normal Zip", "ext": "zip"},
		{"desc": "Portable Document Format", "ext": "pdf"},
		{"desc": "Microsoft Word (.docx) file", "ext": "docx"}
	]

	def __init__(self, app=None, ui: Ui_MainWindow = None, main_controller=None):
		self.app = app
		self.ui = ui
		self.main_controller = main_controller

		self.folder_list = []
		self.archiver_worker = None
		self.setup_control()
		pass

	def setup_control(self):
		archive_from_folder = MY_CONFIG.get("general", "archive_from_folder")
		if archive_from_folder == "":
			archive_from_folder = MY_CONFIG.get("general", "download_folder")
		#archive_from_folder = "F:/comics/測試"
		self.ui.txt_archiver_from_folder.setText(archive_from_folder)

		for tmp_format in self.FORMATS:
			label = TRSM(tmp_format["desc"]) + " (*." + tmp_format["ext"] + ")"
			self.ui.cbx_archiver_format.addItem(label)

		self.ui.cbx_archiver_file_exist.addItems([TRSM("Skip"),TRSM("Overwrite")])

		self.retranslateUi()

		#action
		self.ui.btn_archiver_from_folder.clicked.connect(self.btn_archiver_from_folder_clicked)
		self.ui.btn_archiver_folder_scan.clicked.connect(self.btn_archiver_folder_scan_clicked)

		self.ui.btn_archiver_select.clicked.connect(self.btn_archiver_select_clicked)
		self.ui.btn_archiver_unselect.clicked.connect(self.btn_archiver_unselect_clicked)
		self.ui.btn_archiver_select_all.clicked.connect(self.btn_archiver_select_all_clicked)
		self.ui.btn_archiver_unselect_all.clicked.connect(self.btn_archiver_unselect_all_clicked)

		self.ui.btn_archiver_start.clicked.connect(self.btn_archiver_start_clicked)
		self.ui.btn_archiver_cancel.clicked.connect(self.btn_archiver_cancel_clicked)

		pass

	def retranslateUi(self):
		for idx,tmp_format in enumerate(self.FORMATS):
			label = TRSM(tmp_format["desc"]) + " (*." + tmp_format["ext"] + ")"
			self.ui.cbx_archiver_format.setItemText(idx,label)

		self.ui.cbx_archiver_file_exist.setItemText(0,TRSM("Skip"))
		self.ui.cbx_archiver_file_exist.setItemText(1,TRSM("Overwrite"))

		#self.ui.cbx_archiver_format.setCurrentIndex(1)
		#self.ui.cbx_archiver_file_exist.setCurrentIndex(1)

	#action
	def btn_archiver_from_folder_clicked(self):
		old_folder_path = self.ui.txt_archiver_from_folder.text()
		if old_folder_path == "":
			old_folder_path = "./"
		folder_path = QFileDialog.getExistingDirectory(self.main_controller,TRSM("Open folder"), old_folder_path)
		if folder_path != "":
			self.ui.txt_archiver_from_folder.setText(folder_path)
			self.ui.list_archiver_folder.clear()
			self.ui.btn_archiver_select.setEnabled(False)
			self.ui.btn_archiver_unselect.setEnabled(False)
			self.ui.btn_archiver_select_all.setEnabled(False)
			self.ui.btn_archiver_unselect_all.setEnabled(False)
			self.ui.btn_archiver_start.setEnabled(False)
			self.ui.btn_archiver_cancel.setEnabled(False)
			MY_CONFIG.set("general", "archive_from_folder", folder_path)
			MY_CONFIG.save()
		pass

	def btn_archiver_folder_scan_clicked(self):
		folder_path = self.ui.txt_archiver_from_folder.text()
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

		if len(final_folders) > 0:
			# update the title
			folder_name = os.path.basename(folder_path)
			if folder_name:
				self.ui.txt_archiver_title.setText(folder_name)
		else:
			util.msg_box(TRSM("Not sub-folder found"),self.main_controller)
			pass

	def btn_archiver_select_clicked(self):
		items = self.ui.list_archiver_folder.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Checked)
		pass

	def btn_archiver_unselect_clicked(self):
		items = self.ui.list_archiver_folder.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Unchecked)
		pass

	def btn_archiver_select_all_clicked(self):
		for i in range(self.ui.list_archiver_folder.count()):
			self.ui.list_archiver_folder.item(i).setCheckState(QtCore.Qt.Checked)

	def btn_archiver_unselect_all_clicked(self):
		for i in range(self.ui.list_archiver_folder.count()):
			self.ui.list_archiver_folder.item(i).setCheckState(QtCore.Qt.Unchecked)

	def btn_archiver_start_clicked(self):
		total_need_archive_list = []
		for i in range(self.ui.list_archiver_folder.count()):
			if self.ui.list_archiver_folder.item(i).checkState() == QtCore.Qt.Checked:
				total_need_archive_list.append(self.folder_list[i])
		#print(total_need_archive_list)

		if len(total_need_archive_list) > 0:
			self.ui.log_archiver.clear()

			self.ui.btn_archiver_start.setEnabled(False)
			self.ui.btn_archiver_cancel.setEnabled(True)

			self.archiver_worker = ArchiverWorker(
				folders=total_need_archive_list,
				from_folder=self.ui.txt_archiver_from_folder.text(),
				to_format=self.FORMATS[self.ui.cbx_archiver_format.currentIndex()]["ext"],
				is_overwrite=bool(self.ui.cbx_archiver_file_exist.currentIndex()),
				num_pre_archive=int(self.ui.spin_archiver_combie.text()),
				title=self.ui.txt_archiver_title.text()
				)
			self.archiver_worker.trigger.connect(self.archive_trigger)
			self.archiver_worker.canceled.connect(self.archive_canceled)
			self.archiver_worker.finished.connect(self.archive_finished)
			self.archiver_worker.start()

			#task_lists = self._pre_check_folder(total_need_archive_list)
			#print(task_lists)
			pass
		else:
			util.msg_box(TRSM("Please select at least one folder to archive"),self.main_controller)
			pass

	def btn_archiver_cancel_clicked(self):
		self.archiver_worker.stop()

	#callback
	def archive_trigger(self,message,current_action,total_action):
		self.ui.pgb_archiver.setMaximum(total_action)
		self.ui.pgb_archiver.setValue(current_action)
		if message != "":
			self.ui.log_archiver.append(message)
		pass

	def archive_finished(self):
		self.ui.log_archiver.append(TRSM("Archive finished!"))
		self.ui.btn_archiver_start.setEnabled(True)
		self.ui.btn_archiver_cancel.setEnabled(False)
		if self.ui.pgb_archiver.maximum() > 0:
			self.ui.pgb_archiver.setValue(self.ui.pgb_archiver.maximum())
		else:
			self.ui.pgb_archiver.setMaximum(100)
			self.ui.pgb_archiver.setValue(100)
		self.archiver_worker = None
		pass

	def archive_canceled(self):
		self.ui.log_archiver.append(TRSM("Archive canceled!"))
		self.ui.btn_archiver_start.setEnabled(True)
		self.ui.btn_archiver_cancel.setEnabled(False)
		self.archiver_worker = None

	#internal function
	def _update_folder_list(self):
		self.ui.list_archiver_folder.clear()

		for idx, tmp_folder in enumerate(self.folder_list):
			item = QListWidgetItem()
			item.setText(tmp_folder)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(QtCore.Qt.Checked)
			self.ui.list_archiver_folder.addItem(item)

		if self.ui.list_archiver_folder.count() > 0:
			self.ui.btn_archiver_select.setEnabled(True)
			self.ui.btn_archiver_unselect.setEnabled(True)
			self.ui.btn_archiver_select_all.setEnabled(True)
			self.ui.btn_archiver_unselect_all.setEnabled(True)
			self.ui.btn_archiver_start.setEnabled(True)
		else:
			self.ui.btn_archiver_select.setEnabled(False)
			self.ui.btn_archiver_unselect.setEnabled(False)
			self.ui.btn_archiver_select_all.setEnabled(False)
			self.ui.btn_archiver_unselect_all.setEnabled(False)
			self.ui.btn_archiver_start.setEnabled(False)

		pass

