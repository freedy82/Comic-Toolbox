from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from uis import about_window
from const import *

class AboutWindowController(QtWidgets.QMainWindow):
	def __init__(self,app,main_controller):
		super().__init__()
		self.app = app
		self.main_controller = main_controller
		self.ui = about_window.Ui_MainWindow()
		self.ui.setupUi(self)
		self.setup_control()

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
		self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
		# GUI
		self.retranslateUi()

		#action
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)

		self.ui.lbl_version.setText(TRSM("Version: %s") % APP_VERSION)
		self.ui.lbl_app_link.setText('<a href=\"%s\">%s</a>' % (APP_LINK, APP_LINK))

		pass

	#action
	def accept(self):
		#print("Click accept")
		self.close()
		pass

	def reject(self):
		#print("Click reject")
		pass

	def center_pos_of_parent(self):
		qr = self.main_controller.frameGeometry()
		x = qr.left() + (qr.width() - self.width()) / 2
		y = qr.top() + (qr.height() - self.height()) / 2
		self.move(x, y)

	# internal
	def show(self):
		super().show()
		self.center_pos_of_parent()
		pass

	@staticmethod
	def setModal(is_modal):
		#print("set modal %d" % is_modal)
		pass
