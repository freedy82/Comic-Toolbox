import json
import re

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QColorDialog

from models.const import *
from models import util
from uis.main_window import Ui_MainWindow

class SettingsController(object):

	def __init__(self, app=None, ui: Ui_MainWindow = None, main_controller=None):
		self.app = app
		self.ui = ui
		self.main_controller = main_controller
		self.setup_control()
		pass

	def setup_control(self):
		self.ui.cbx_settings_proxy_mode.addItems([TRSM("Disable proxy"),TRSM("Use proxy and not proxy same time"),TRSM("Only use proxy")])
		self.ui.cbx_settings_proxy_type.addItems([TRSM("https"),TRSM("http")])
		self.ui.cbx_settings_cugan_denoise.addItems([TRSM("No effect"),TRSM("Level 0"),TRSM("Level 1"),TRSM("Level 2"),TRSM("Level 3")])
		self.ui.cbx_settings_cugan_resize.addItems([TRSM("No"),TRSM("Yes")])
		self.ui.cbx_settings_when_close_window.addItems([TRSM("Minimize to system tray"),TRSM("Close window")])

		# UI Display
		self.retranslateUi()
		self.load_config()

		# action
		self.ui.btn_settings_save.clicked.connect(self.btn_settings_save_clicked)
		self.ui.btn_settings_reset.clicked.connect(self.btn_settings_reset_clicked)
		self.ui.btn_settings_general_folder.clicked.connect(self.btn_settings_general_folder_clicked)
		self.ui.btn_settings_proxy_add.clicked.connect(self.btn_settings_proxy_add_clicked)
		self.ui.btn_settings_proxy_delete.clicked.connect(self.btn_settings_proxy_delete_clicked)
		self.ui.btn_settings_cugan_browser.clicked.connect(self.btn_settings_cugan_browser_clicked)
		self.ui.btn_settings_reader_background.clicked.connect(self.btn_settings_reader_background_clicked)
		self.ui.txt_settings_reader_background.textChanged.connect(self.txt_settings_reader_background_text_changed)

	def retranslateUi(self):
		self.ui.cbx_settings_proxy_mode.setItemText(0,TRSM("Disable proxy"))
		self.ui.cbx_settings_proxy_mode.setItemText(1,TRSM("Use proxy and not proxy same time"))
		self.ui.cbx_settings_proxy_mode.setItemText(2,TRSM("Only use proxy"))

		self.ui.cbx_settings_cugan_denoise.setItemText(0,TRSM("No effect"))
		self.ui.cbx_settings_cugan_denoise.setItemText(1,TRSM("Level 0"))
		self.ui.cbx_settings_cugan_denoise.setItemText(2,TRSM("Level 1"))
		self.ui.cbx_settings_cugan_denoise.setItemText(3,TRSM("Level 2"))
		self.ui.cbx_settings_cugan_denoise.setItemText(4,TRSM("Level 3"))

		self.ui.cbx_settings_cugan_resize.setItemText(0,TRSM("No"))
		self.ui.cbx_settings_cugan_resize.setItemText(1,TRSM("Yes"))

		self.ui.cbx_settings_when_close_window.setItemText(0,TRSM("Minimize to system tray"))
		self.ui.cbx_settings_when_close_window.setItemText(1,TRSM("Close window"))

		pass

	#action
	def btn_settings_general_folder_clicked(self):
		old_folder_path = self.ui.txt_settings_general_folder.text()
		if old_folder_path == "":
			old_folder_path = "./"
		folder_path = QFileDialog.getExistingDirectory(self.main_controller,TRSM("Open folder"), old_folder_path)
		if folder_path != "":
			self.ui.txt_settings_general_folder.setText(folder_path)
		pass

	def btn_settings_reader_background_clicked(self):
		old_color = QColor(self.ui.txt_settings_reader_background.text())
		color = QColorDialog.getColor(old_color,self.main_controller,TRSM("Pick a color"))
		if color.isValid():
			color_name = color.name()
			self.ui.txt_settings_reader_background.setText(color_name)
			self.ui.lbl_settings_reader_background_preview.setStyleSheet("background-color: "+color_name+";")

	def btn_settings_cugan_browser_clicked(self):
		old_file_path = self.ui.txt_settings_cugan_location.text()
		if old_file_path == "":
			old_file_path = "./"
		file_path = QFileDialog.getOpenFileName(self.main_controller,TRSM("EXE location"), old_file_path)
		if len(file_path) >= 2 and file_path[0] != "":
			self.ui.txt_settings_cugan_location.setText(file_path[0])

	def btn_settings_proxy_add_clicked(self):
		if self.ui.txt_settings_proxy_ip.text() != "":
			proxy = self.ui.cbx_settings_proxy_type.currentText() + "://" + self.ui.txt_settings_proxy_ip.text()
			if not self.check_proxy_format(proxy):
				util.msg_box(TRSM("Please enter a proxy with ip:port format"), self.main_controller)
			elif self.check_proxy_exist_in_list(proxy):
				util.msg_box(TRSM("Proxy already exist in list"), self.main_controller)
			else:
				self.try_add_proxy(proxy)
				self.ui.txt_settings_proxy_ip.setText("")
		else:
			util.msg_box(TRSM("Please enter a proxy with ip:port format"),self.main_controller)
			pass

	def btn_settings_proxy_delete_clicked(self):
		if len(self.ui.list_settings_proxy.selectedItems()) > 0:
			if util.confirm_box(TRSM("Confirm delete these proxy?"),self.main_controller):
				for item in self.ui.list_settings_proxy.selectedItems():
					self.ui.list_settings_proxy.takeItem(self.ui.list_settings_proxy.row(item))
		else:
			util.msg_box(TRSM("Please select at least one proxy"),self.main_controller)
		pass

	def btn_settings_save_clicked(self):
		self.save_config()

	def btn_settings_reset_clicked(self):
		self.ui.spin_settings_max_retry.setValue(5)
		self.ui.spin_settings_timeout.setValue(30)

		self.ui.spin_settings_book_padding.setValue(2)
		self.ui.spin_settings_chapter_padding.setValue(3)
		self.ui.spin_settings_image_padding.setValue(3)
		self.ui.spin_settings_jpg_quality.setValue(90)
		self.ui.spin_settings_check_is_2_page.setValue(1.0)
		self.ui.txt_settings_reader_background.setText("#000000")
		self.ui.spin_settings_reader_auto_play_interval.setValue(5.0)

		self.ui.spin_settings_page_sleep.setValue(10)
		self.ui.spin_settings_image_sleep.setValue(1)
		self.ui.spin_settings_download_worker.setValue(2)
		self.ui.cbx_settings_proxy_mode.setCurrentIndex(0)

		self.ui.spin_settings_cugan_scale.setValue(2)
		self.ui.cbx_settings_cugan_denoise.setCurrentIndex(4)
		self.ui.cbx_settings_cugan_resize.setCurrentIndex(0)

		self.ui.cbx_settings_when_close_window.setCurrentIndex(0)

		pass

	def txt_settings_reader_background_text_changed(self):
		color_str = self.ui.txt_settings_reader_background.text()
		q_color = QColor(color_str)
		if q_color.isValid():
			self.ui.lbl_settings_reader_background_preview.setStyleSheet("background-color: " + color_str)

	# internal
	def load_config(self):
		#general
		download_folder = MY_CONFIG.get("general", "download_folder")
		self.ui.txt_settings_general_folder.setText(download_folder)
		max_retry = MY_CONFIG.get("general", "max_retry")
		self.ui.spin_settings_max_retry.setValue(int(max_retry))
		timeout = MY_CONFIG.get("general", "timeout")
		self.ui.spin_settings_timeout.setValue(float(timeout))

		self.ui.cbx_settings_user_agent.addItems([
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
		])
		# "Mozilla/5.0 (iPad; CPU OS 8_0_2 like Mac OS X) AppleWebKit/60.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12A405 Safari/600.1.4",
		# "Mozilla/5.0 (iPhone; CPU iPhone OS 13_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.2 Mobile/15E148 Safari/604.1",
		# "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.58 Mobile Safari/537.36"

		agent = MY_CONFIG.get("general", "agent")
		self.ui.cbx_settings_user_agent.setCurrentText(agent)

		book_padding = MY_CONFIG.get("general", "book_padding")
		self.ui.spin_settings_book_padding.setValue(int(book_padding))
		chapter_padding = MY_CONFIG.get("general", "chapter_padding")
		self.ui.spin_settings_chapter_padding.setValue(int(chapter_padding))
		image_padding = MY_CONFIG.get("general", "image_padding")
		self.ui.spin_settings_image_padding.setValue(int(image_padding))
		jpg_quality = MY_CONFIG.get("general", "jpg_quality")
		self.ui.spin_settings_jpg_quality.setValue(int(jpg_quality))
		check_is_2_page = MY_CONFIG.get("general", "check_is_2_page")
		self.ui.spin_settings_check_is_2_page.setValue(float(check_is_2_page))

		reader_background = MY_CONFIG.get("reader", "background")
		self.ui.txt_settings_reader_background.setText(reader_background)
		self.ui.lbl_settings_reader_background_preview.setStyleSheet("background-color:"+reader_background+";")
		reader_auto_play_interval = MY_CONFIG.get("reader", "auto_play_interval")
		self.ui.spin_settings_reader_auto_play_interval.setValue(float(reader_auto_play_interval))

		#anti ban
		page_sleep = MY_CONFIG.get("anti-ban", "page_sleep")
		self.ui.spin_settings_page_sleep.setValue(float(page_sleep))
		image_sleep = MY_CONFIG.get("anti-ban", "image_sleep")
		self.ui.spin_settings_image_sleep.setValue(float(image_sleep))
		download_worker = MY_CONFIG.get("anti-ban", "download_worker")
		self.ui.spin_settings_download_worker.setValue(int(download_worker))
		proxy_mode = MY_CONFIG.get("anti-ban", "proxy_mode")
		self.ui.cbx_settings_proxy_mode.setCurrentIndex(int(proxy_mode))
		proxy_list = MY_CONFIG.get("anti-ban", "proxy_list")
		if proxy_list != "":
			proxy_list = json.loads(proxy_list)
			for proxy in proxy_list:
				item = QListWidgetItem()
				item.setText(proxy["url"])
				item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
				if proxy["enable"]:
					item.setCheckState(QtCore.Qt.Checked)
				else:
					item.setCheckState(QtCore.Qt.Unchecked)
				self.ui.list_settings_proxy.addItem(item)

		#real-cugan
		exe_location = MY_CONFIG.get("real-cugan", "exe_location")
		self.ui.txt_settings_cugan_location.setText(exe_location)

		scale = int(MY_CONFIG.get("real-cugan", "scale"))
		self.ui.spin_settings_cugan_scale.setValue(scale)

		denoise_level = int(MY_CONFIG.get("real-cugan", "denoise_level"))
		self.ui.cbx_settings_cugan_denoise.setCurrentIndex(denoise_level+1)

		resize = int(MY_CONFIG.get("real-cugan", "resize"))
		self.ui.cbx_settings_cugan_resize.setCurrentIndex(resize)

		#misc
		display_message = MY_CONFIG.get("misc", "display_message")
		if display_message == "False":
			self.ui.radio_settings_message_no.setChecked(True)
		else:
			self.ui.radio_settings_message_yes.setChecked(True)
		play_sound = MY_CONFIG.get("misc", "play_sound")
		if play_sound == "False":
			self.ui.radio_settings_sound_no.setChecked(True)
		else:
			self.ui.radio_settings_sound_yes.setChecked(True)
		when_close_window = MY_CONFIG.get("misc", "when_close_window")
		self.ui.cbx_settings_when_close_window.setCurrentIndex(int(when_close_window))

		pass

	def save_config(self):
		global WEB_BOT, EXECUTOR
		#print("try save")
		#general
		MY_CONFIG.set("general","download_folder",self.ui.txt_settings_general_folder.text())
		MY_CONFIG.set("general","max_retry",str(self.ui.spin_settings_max_retry.value()))
		MY_CONFIG.set("general","timeout",str(self.ui.spin_settings_timeout.value()))
		MY_CONFIG.set("general","agent",self.ui.cbx_settings_user_agent.currentText())
		MY_CONFIG.set("general","book_padding",str(self.ui.spin_settings_book_padding.value()))
		MY_CONFIG.set("general","chapter_padding",str(self.ui.spin_settings_chapter_padding.value()))
		MY_CONFIG.set("general","image_padding",str(self.ui.spin_settings_image_padding.value()))
		MY_CONFIG.set("general","jpg_quality",str(self.ui.spin_settings_jpg_quality.value()))
		MY_CONFIG.set("general","check_is_2_page",str(self.ui.spin_settings_check_is_2_page.value()))
		MY_CONFIG.set("reader","background",self.ui.txt_settings_reader_background.text())
		MY_CONFIG.set("reader","auto_play_interval",str(self.ui.spin_settings_reader_auto_play_interval.value()))

		#anti ban
		MY_CONFIG.set("anti-ban","page_sleep",str(self.ui.spin_settings_page_sleep.value()))
		MY_CONFIG.set("anti-ban","image_sleep",str(self.ui.spin_settings_image_sleep.value()))
		MY_CONFIG.set("anti-ban","download_worker",str(self.ui.spin_settings_download_worker.value()))
		MY_CONFIG.set("anti-ban","proxy_mode",str(self.ui.cbx_settings_proxy_mode.currentIndex()))
		MY_CONFIG.set("anti-ban","proxy_list",json.dumps(self.proxy_list_to_json()))

		#real-cugan
		MY_CONFIG.set("real-cugan","exe_location",self.ui.txt_settings_cugan_location.text())
		MY_CONFIG.set("real-cugan","scale",str(self.ui.spin_settings_cugan_scale.value()))
		MY_CONFIG.set("real-cugan","denoise_level",str(self.ui.cbx_settings_cugan_denoise.currentIndex()-1))
		MY_CONFIG.set("real-cugan","resize",str(self.ui.cbx_settings_cugan_resize.currentIndex()))

		#misc
		MY_CONFIG.set("misc","display_message",str(self.ui.radio_settings_message_yes.isChecked()))
		MY_CONFIG.set("misc","play_sound",str(self.ui.radio_settings_sound_yes.isChecked()))
		MY_CONFIG.set("misc","when_close_window",str(self.ui.cbx_settings_when_close_window.currentIndex()))

		MY_CONFIG.save()

		WEB_BOT.set_agent(MY_CONFIG.get("general", "agent"))
		WEB_BOT.set_time_out(float(MY_CONFIG.get("general", "timeout")))
		WEB_BOT.set_max_retry(int(MY_CONFIG.get("general", "max_retry")))
		WEB_BOT.set_proxy_mode(int(MY_CONFIG.get("anti-ban", "proxy_mode")))
		WEB_BOT.set_proxy_list(MY_CONFIG.get("anti-ban", "proxy_list"))

		EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=int(MY_CONFIG.get("anti-ban", "download_worker")))

	def try_add_proxy(self,proxy):
		if self.check_proxy_exist_in_list(proxy):
			return False
		item = QListWidgetItem()
		item.setText(proxy)
		item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
		item.setCheckState(QtCore.Qt.Checked)
		self.ui.list_settings_proxy.addItem(item)
		return True

	def check_proxy_format(self,proxy):
		pattern_proxy = re.compile(r'http([s]?)://(.*?):([0-9]*)')
		proxy_info = re.findall(pattern_proxy, proxy)
		if len(proxy_info) == 1 and len(proxy_info[0]) == 3:
			return True
		return False

	def check_proxy_exist_in_list(self,proxy):
		for i in range(self.ui.list_settings_proxy.count()):
			item = self.ui.list_settings_proxy.item(i)
			if item.text() == proxy:
				return True
		return False

	def proxy_list_to_json(self):
		result = []
		for i in range(self.ui.list_settings_proxy.count()):
			item = self.ui.list_settings_proxy.item(i)
			result.append({
				"enable": item.checkState() == QtCore.Qt.Checked,
				"url": item.text(),
			})
		return result
