from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from functools import partial
from PyQt5.QtCore import Qt
import webbrowser

import util
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
		# self.ui.lbl_app_link.clicked.connect(self.lbl_app_link_clicked)
		# self.ui.lbl_app_link.mousePressEvent(self.lbl_app_link_clicked)
		self.ui.btn_app_link.clicked.connect(self.btn_app_link_clicked)
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)

		self.ui.lbl_version.setText(TRSM("Version: %s") % APP_VERSION)
		self.ui.btn_app_link.setText(TRSM("%s") % APP_LINK)

		pass

	#action
	def accept(self):
		#print("Click accept")
		self.close()
		pass

	def reject(self):
		#print("Click reject")
		pass

	def btn_app_link_clicked(self):
		webbrowser.open(APP_LINK)
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
