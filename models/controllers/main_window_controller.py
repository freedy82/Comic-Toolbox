from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QPixmap, QCursor
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu
from PyQt5.QtMultimedia import QSound
from functools import partial

from models.const import *
from models import util
from uis import main_window
from models.controllers.downloader_controller import DownloaderController
from models.controllers.converter_controller import ConverterController
from models.controllers.cropper_controller import CropperController
from models.controllers.archiver_controller import ArchiverController
from models.controllers.settings_controller import SettingsController
#from models.about_window_controller import AboutWindowController
from models.controllers.help_window_controller import HelpWindowController
from models.controllers.reader_window_controller import ReaderWindowController

class MainWindowController(QtWidgets.QMainWindow):
	def __init__(self,app,trans):
		super().__init__()
		self.app = app
		self.trans = trans
		self.ui = main_window.Ui_MainWindow()
		self.ui.setupUi(self)
		#self.about = main_window.Ui_MainWindow()
		#self.about.setupUi(self)
		self.tray_icon = None
		self.st_showAction = None
		self.st_hideAction = None
		self.st_exitAction = None
		self.disambiguateTimer = None
		self.setup_control()
		self.downloader_controller = DownloaderController(app=app,ui=self.ui,main_controller=self)
		self.converter_controller = ConverterController(app=app,ui=self.ui,main_controller=self)
		self.cropper_controller = CropperController(app=app, ui=self.ui, main_controller=self)
		self.archiver_controller = ArchiverController(app=app,ui=self.ui,main_controller=self)
		self.settings_controller = SettingsController(app=app,ui=self.ui,main_controller=self)
		self.reader_controller = ReaderWindowController(app=app,main_controller=self)

		#self.about_window_controller = AboutWindowController(app=self.app, main_controller=self)
		self.help_window_controller = HelpWindowController(app=self.app, main_controller=self)

	def setup_control(self):
		self.setup_languages()
		self.setup_themes()
		self.setup_tray_icon()

		#action
		self.ui.actionFileStartReader.triggered.connect(self.on_file_start_reader)
		self.ui.actionFileExit.triggered.connect(self.on_file_exit)
		self.ui.actionHelpAbout.triggered.connect(self.on_help_about)
		self.ui.actionHelpHelp.triggered.connect(self.on_help_help)
		self.ui.actionHelpAboutQt.triggered.connect(self.on_help_about_qt)

		#self.ui.actionHelpThemeDefault.triggered.connect(partial(self.on_help_theme_select, theme={"name":""}))
		pass

	def retranslateUi(self):
		if self.st_showAction:
			self.st_showAction.setText(TRSM("Show Main Window"))
		if self.st_hideAction:
			self.st_hideAction.setText(TRSM("Hide Main Window"))
		if self.st_exitAction:
			self.st_exitAction.setText(TRSM("Exit"))
		if self.tray_icon:
			self.tray_icon.setToolTip(TRSM("Comic Toolbox"))
		if self.help_window_controller:
			self.help_window_controller.retranslateUi()
		if self.reader_controller:
			self.reader_controller.retranslateUi()

		self.setup_themes()

	def setup_languages(self):
		languages = util.find_all_languages()
		self.ui.menuHelpLanguage.removeAction(self.ui.action_help_language_tmp_language)
		for lang in languages:
			tmp_lang_action = QtWidgets.QAction(self)
			tmp_lang_action.setText(lang["name"])
			tmp_lang_action.triggered.connect(partial(self.on_select_language, lang=lang))
			self.ui.menuHelpLanguage.addAction(tmp_lang_action)

	def setup_themes(self):
		self.ui.menuHelpTheme.clear()

		tmp_theme_action = QtWidgets.QAction(self)
		tmp_theme_action.setText(TRSM("Default"))
		tmp_theme_action.triggered.connect(partial(self.on_help_theme_select, theme={"name":""}))
		self.ui.menuHelpTheme.addAction(tmp_theme_action)

		themes = util.find_all_themes()
		for theme in themes:
			tmp_theme_action = QtWidgets.QAction(self)
			tmp_theme_action.setText(TRSM(theme["name"]))
			tmp_theme_action.triggered.connect(partial(self.on_help_theme_select, theme=theme))
			self.ui.menuHelpTheme.addAction(tmp_theme_action)

	def setup_tray_icon(self):
		icon = QIcon()
		icon.addPixmap(QPixmap(":/icon/main_icon"), QIcon.Normal, QIcon.Off)
		self.tray_icon = QSystemTrayIcon(icon, self.app)
		self.tray_icon.setToolTip(TRSM("Comic Toolbox"))

		tray_menu = QMenu()
		self.st_showAction = tray_menu.addAction(TRSM("Show Main Window"))
		self.st_showAction.triggered.connect(self.on_show_main_window)
		icon_show = QIcon()
		icon_show.addPixmap(QPixmap(":/icon/show"), QIcon.Normal, QIcon.Off)
		self.st_showAction.setIcon(icon_show)

		self.st_hideAction = tray_menu.addAction(TRSM("Hide Main Window"))
		self.st_hideAction.triggered.connect(self.on_hide_main_window)
		icon_hide = QIcon()
		icon_hide.addPixmap(QPixmap(":/icon/hide"), QIcon.Normal, QIcon.Off)
		self.st_hideAction.setIcon(icon_hide)

		#debug
		#st_messageAction = tray_menu.addAction(TRSM("Show a message"))
		#st_messageAction.triggered.connect(self.on_show_message)

		tray_menu.addSeparator()
		self.st_exitAction = tray_menu.addAction(TRSM("Exit"))
		self.st_exitAction.triggered.connect(self.on_file_exit)
		icon_exit = QIcon()
		icon_exit.addPixmap(QPixmap(":/icon/exit"), QIcon.Normal, QIcon.Off)
		self.st_exitAction.setIcon(icon_exit)

		self.tray_icon.setContextMenu(tray_menu)
		self.tray_icon.activated.connect(self.on_tray_icon_activated)
		self.tray_icon.show()

		self.disambiguateTimer = QTimer(self)
		self.disambiguateTimer.setSingleShot(True)
		self.disambiguateTimer.timeout.connect(self.disambiguate_timer_timeout)

		self.tray_icon.messageClicked.connect(self.tray_icon_message_clicked)

	#function
	def show_tray_message(self,message):
		if MY_CONFIG.get("misc", "display_message") != "False":
			if self.tray_icon:
				self.tray_icon.showMessage("",message,self.tray_icon.icon(),3*1000)

	def try_play_notification_sound(self):
		if MY_CONFIG.get("misc", "play_sound") != "False":
			QSound.play(":/sound/ring")
			pass

	def show_help(self):
		self.help_window_controller.show()

	def cursor_busy(self):
		self.app.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))

	def cursor_un_busy(self):
		self.app.restoreOverrideCursor()

	def set_window_opacity(self,opacity):
		self.setWindowOpacity(opacity)

	#action
	def on_tray_icon_activated(self, reason):
		if reason == QSystemTrayIcon.Trigger:
			self.disambiguateTimer.start(self.app.doubleClickInterval())
		elif reason == QSystemTrayIcon.DoubleClick:
			self.disambiguateTimer.stop()
			self.on_show_main_window()

	def disambiguate_timer_timeout(self):
		#print("Tray icon single clicked")
		pass

	def on_show_main_window(self):
		self.setVisible(True)
		self.activateWindow()

	def on_hide_main_window(self):
		self.setVisible(False)

	def on_show_message(self):
		self.show_tray_message("This is a message")

	def on_file_start_reader(self):
		self.reader_controller.show()

	def on_file_exit(self):
		if util.confirm_box(TRSM("Confirm to quit?"),self):
			self.app.quit()
		pass

	def on_select_language(self,lang):
		self.trans.load("./languages/"+lang["file"])
		self.app.installTranslator(self.trans)
		self.ui.retranslateUi(self)

		self.downloader_controller.retranslateUi()
		self.converter_controller.retranslateUi()
		self.cropper_controller.retranslateUi()
		self.archiver_controller.retranslateUi()
		self.settings_controller.retranslateUi()
		#self.about_window_controller.retranslateUi()

		self.retranslateUi()

		MY_CONFIG.set("general","language",lang["file"])
		MY_CONFIG.save()
		pass

	def on_help_theme_select(self,theme):
		if theme["name"] != "":
			qss_info = open("./themes/" + theme["name"] + ".qss","r").read()
			self.app.setStyleSheet(qss_info)
		else:
			self.app.setStyleSheet("")

		MY_CONFIG.set("general","theme",theme["name"])
		MY_CONFIG.save()

	def on_help_help(self):
		self.show_help()

	def on_help_about(self):
		#self.about_window_controller.show()
		message = ""
		message += "<span style='font-weight:900;font-size:x-large'>" + TRSM("Comic Toolbox") + "</span><br><br>"
		message += (TRSM("Version: %s") % APP_VERSION) + "<br><br>"
		message += TRSM("Author") + ": "
		message += ("<a href=\"%s\">%s</a>" % (APP_AUTHOR_LINK, APP_AUTHOR))
		message += "<br><br>"
		message += ("<a href=\"%s\">%s</a>" % (APP_LINK, APP_LINK)) + "<br><br>"
		message += TRSM("Respect the copyright, please support the genuine version, and the resources downloaded or generated through this tool are prohibited from spreading and sharing!") + "<br>"
		message += TRSM("It is prohibited to use this project for commercial activities!")
		message += "<br><br>"
		message += TRSM("License") + ":<br>"
		message += ("<a href=\"%s\">%s</a>" % (APP_LICENSE_LINK, APP_LICENSE))

		dlg = QtWidgets.QMessageBox(self)
		icon_pixmap = QPixmap(":/icon/main_icon")
		icon_pixmap = icon_pixmap.scaled(60,60,transformMode=Qt.SmoothTransformation)
		dlg.setIconPixmap(icon_pixmap)
		dlg.setWindowTitle(TRSM("About Comic Toolbox"))
		dlg.setText(message)
		dlg.show()

		pass

	def on_help_about_qt(self):
		QtWidgets.QMessageBox().aboutQt(self, TRSM("About Qt"))

	def tray_icon_message_clicked(self):
		self.setVisible(True)

	#debug
	def show(self):
		super().show()
		#self.on_file_start_reader()

	# replace event
	def closeEvent(self, event):
		event.ignore()
		if MY_CONFIG.get("misc", "when_close_window") == "1":
			self.on_file_exit()
		else:
			self.setVisible(False)
			if MY_CONFIG.get("general", "is_show_message_of_hidden") == "":
				self.show_tray_message(TRSM("Comic toolbox was hidden to system tray"))
				MY_CONFIG.set("general","is_show_message_of_hidden","True")
				MY_CONFIG.save()
		pass
