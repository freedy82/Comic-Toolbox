from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

from models.const import *
from models.controllers.reader.helper import *
from models.reader import Reader
from uis import reader_rotate_dialog

class ReaderRotateDialogController(QtWidgets.QDialog):
	finished = pyqtSignal(str,PageRotate,PageRotateMode)

	def __init__(self,app,main_controller,file, reader:Reader):
		super().__init__()
		self.app = app
		self.main_controller = main_controller
		self.file = file
		self.reader = reader
		self.ui = reader_rotate_dialog.Ui_MainWindow()
		self.ui.setupUi(self)
		self.setup_control()

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
		self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
		self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

		if self.file != "":
			self.ui.cbx_target_image.addItems([self.file])
		self.ui.cbx_target_image.addItems([TRSM("All image")])
		self.ui.cbx_rotate.addItems([TRSM("Rotate")+" 90°",TRSM("Rotate")+" 180°",TRSM("Rotate")+" 270°"])
		self.ui.cbx_change_mode.addItems([TRSM("Memory")])
		if self.reader.support_rotate_file_in_disk():
			self.ui.cbx_change_mode.addItems([TRSM("File")])

		# GUI
		self.retranslateUi()
		#action
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)
		pass

	#action
	def accept(self):
		file = ""
		if self.ui.cbx_target_image.count() == 2 and self.ui.cbx_target_image.currentIndex() == 0:
			file = self.ui.cbx_target_image.currentText()
		rotate = PageRotate.ROTATE_90
		if self.ui.cbx_rotate.currentIndex() == 1:
			rotate = PageRotate.ROTATE_180
		elif self.ui.cbx_rotate.currentIndex() == 2:
			rotate = PageRotate.ROTATE_270
		mode = PageRotateMode.MEMORY
		if self.ui.cbx_change_mode.currentIndex() == 1:
			mode = PageRotateMode.FILE
		self.finished.emit(file,rotate,mode)
		self.done(0)

	def reject(self):
		self.done(0)
