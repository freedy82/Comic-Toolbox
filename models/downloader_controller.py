import sys

from PyQt5 import QtCore, QtWidgets
from const import *
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem
from uis.main_window import Ui_MainWindow
from .site_parse_worker import SiteParseWorker
from .chapter_download_worker import ChapterDownloadWorker
from .bookmark_window_controller import BookmarkWindowController
from .site import Site

import util

class DownloaderController(object):

	def __init__(self, app=None, ui: Ui_MainWindow = None, main_controller=None):
		self.app = app
		self.ui = ui
		self.main_controller = main_controller
		self.site = None
		self.parse_worker = None
		self.chapter_download_worker = None

		self.item_list = None
		self.type_list = []
		self.current_type = ""

		self.bookmark_controller = BookmarkWindowController(self.app,self.main_controller,self)

		self.setup_control()

		pass

	def setup_control(self):
		#debug
		#self.ui.txt_downloader_url.setText("http://www.kumw5.com/mulu/16041/1-1.html")  # 武炼巅峰
		#self.ui.txt_downloader_url.setText("http://www.kumw5.com/mulu/9845/1-1.html")  # 全职法师 #321
		#self.ui.txt_downloader_url.setText("https://www.cartoonmad.com/comic/4462.html")  #  OVERLORD
		#self.ui.txt_downloader_url.setText("https://www.cartoonmad.com/comic/5033.html") # 火影忍者博人傳
		#self.ui.txt_downloader_url.setText("https://www.manhuagui.com/comic/1128/")  # ONE PIECE航海王

		self.ui.cbx_downloader_file_exist.addItems([TRSM("Skip"),TRSM("Overwrite")])

		self.retranslateUi()

		#action
		self.ui.btn_downloader_check.clicked.connect(self.btn_downloader_check_clicked)
		self.ui.btn_downloader_url_help.clicked.connect(self.btn_downloader_url_help_clicked)
		self.ui.btn_downloader_list.clicked.connect(self.btn_downloader_list_clicked)
		self.ui.btn_downloader_bookmark.clicked.connect(self.btn_downloader_bookmark_clicked)
		self.ui.cbx_downloader_type.currentIndexChanged.connect(self.cbx_downloader_type_changed)

		self.ui.btn_downloader_select.clicked.connect(self.btn_downloader_select_clicked)
		self.ui.btn_downloader_unselect.clicked.connect(self.btn_downloader_unselect_clicked)
		self.ui.btn_downloader_select_all.clicked.connect(self.btn_downloader_select_all_clicked)
		self.ui.btn_downloader_unselect_all.clicked.connect(self.btn_downloader_unselect_all_clicked)

		self.ui.btn_downloader_start.clicked.connect(self.btn_downloader_start_clicked)
		self.ui.btn_downloader_cancel.clicked.connect(self.btn_downloader_cancel_clicked)

		pass

	def retranslateUi(self):
		self.ui.cbx_downloader_file_exist.setItemText(0,TRSM("Skip"))
		self.ui.cbx_downloader_file_exist.setItemText(1,TRSM("Overwrite"))

		if self.item_list:
			if self.item_list["title"] != "":
				self.ui.txt_downloader_title.setText(TRSM(self.item_list["title"]))

			if self.item_list["author"] != "":
				self.ui.txt_downloader_author.setText(TRSM(self.item_list["author"]))

			idx = 0
			if "chapter" in self.item_list:
				self.ui.cbx_downloader_type.setItemText(idx,TRSM("chapter"))
				idx += 1
			if "book" in self.item_list:
				self.ui.cbx_downloader_type.setItemText(idx, TRSM("book"))
				idx += 1
			if "extra" in self.item_list:
				self.ui.cbx_downloader_type.setItemText(idx, TRSM("extra"))
				idx += 1

		if self.bookmark_controller:
			self.bookmark_controller.retranslateUi()

		pass

	# action function
	def btn_downloader_check_clicked(self):
		target_url = self.ui.txt_downloader_url.text()
		if target_url != "":
			site = Site.init_site_by_url(url=target_url, web_bot=WEB_BOT)
			if site is not None:
				self.ui.txt_downloader_title.setText("")
				self.ui.txt_downloader_author.setText("")
				self.type_list = []
				self.ui.cbx_downloader_type.clear()
				self.ui.btn_downloader_select.setEnabled(False)
				self.ui.btn_downloader_unselect.setEnabled(False)
				self.ui.btn_downloader_select_all.setEnabled(False)
				self.ui.btn_downloader_unselect_all.setEnabled(False)
				self.ui.btn_downloader_start.setEnabled(False)
				self.ui.btn_downloader_cancel.setEnabled(False)

				self.site = site
				self.parse_worker = SiteParseWorker(self.site)
				self.parse_worker.finished.connect(self.parse_site_finish)
				self.parse_worker.start()
				self.ui.btn_downloader_check.setEnabled(False)
			else:
				util.msg_box(TRSM("Unsupported site"),self.main_controller)
				pass
		else:
			util.msg_box(TRSM("Please input a URL"),self.main_controller)
			pass
		pass

	def btn_downloader_url_help_clicked(self):
		self.main_controller.show_help()

	def btn_downloader_list_clicked(self):
		self.bookmark_controller.show()

	def btn_downloader_bookmark_clicked(self):
		target_url = self.ui.txt_downloader_url.text()
		if target_url != "":
			target_title = self.ui.txt_downloader_title.text()
			self.bookmark_controller.add_book_mark(target_url,target_title)
		else:
			util.msg_box(TRSM("Please input a URL"), self.main_controller)

	def btn_downloader_select_clicked(self):
		items = self.ui.list_downloader_chapter.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Checked)
		pass

	def btn_downloader_unselect_clicked(self):
		items = self.ui.list_downloader_chapter.selectedItems()
		for item in items:
			item.setCheckState(QtCore.Qt.Unchecked)
		pass

	def btn_downloader_select_all_clicked(self):
		for i in range(self.ui.list_downloader_chapter.count()):
			self.ui.list_downloader_chapter.item(i).setCheckState(QtCore.Qt.Checked)

	def btn_downloader_unselect_all_clicked(self):
		for i in range(self.ui.list_downloader_chapter.count()):
			self.ui.list_downloader_chapter.item(i).setCheckState(QtCore.Qt.Unchecked)

	def btn_downloader_start_clicked(self):
		total_need_download_list = []
		for i in range(self.ui.list_downloader_chapter.count()):
			if self.ui.list_downloader_chapter.item(i).checkState() == QtCore.Qt.Checked:
				total_need_download_list.append(self.item_list[self.current_type][i])

		if len(total_need_download_list) > 0:
			self.chapter_download_worker = ChapterDownloadWorker(
				site=self.site,
				items=total_need_download_list,
				title=self.item_list["title"],
				author=self.item_list["author"],
				current_type=self.current_type,
				is_overwrite=bool(self.ui.cbx_downloader_file_exist.currentIndex())
			)
			self.chapter_download_worker.trigger.connect(self.chapter_download_trigger)
			self.chapter_download_worker.finished.connect(self.chapter_download_finish)
			self.chapter_download_worker.canceled.connect(self.chapter_download_cancel)
			self.chapter_download_worker.start()
			self.ui.btn_downloader_start.setEnabled(False)
			self.ui.btn_downloader_cancel.setEnabled(True)
			self.ui.pgb_downloader_current.setValue(0)
			self.ui.pgb_downloader_current.setMaximum(0)
			self.ui.pgb_downloader_total.setValue(0)
			self.ui.pgb_downloader_total.setMaximum(len(total_need_download_list))
			self.ui.txt_downloader_log.clear()

			pass
		else:
			util.msg_box(TRSM("Please select at least one item to download"),self.main_controller)
			pass

	def btn_downloader_cancel_clicked(self):
		self.chapter_download_worker.stop()
		self.ui.btn_downloader_cancel.setEnabled(False)
		pass

	def cbx_downloader_type_changed(self):
		if len(self.type_list) > self.ui.cbx_downloader_type.currentIndex() >= 0:
			current_type_text = self.type_list[self.ui.cbx_downloader_type.currentIndex()]
			if current_type_text != "":
				self.current_type = current_type_text
		else:
			self.current_type = ""
		self.update_chapter_list()

	# callback function
	def parse_site_finish(self,item_list):
		self.ui.btn_downloader_check.setEnabled(True)
		if len(item_list) <= 0:
			util.msg_box(TRSM("Can not found list"),self.main_controller)

		self.item_list = item_list
		#print("get list:")
		#print(self.item_list)

		#self.retranslateUi()
		if self.item_list:
			if self.item_list["title"] != "":
				self.ui.txt_downloader_title.setText(TRSM(self.item_list["title"]))

			if self.item_list["author"] != "":
				self.ui.txt_downloader_author.setText(TRSM(self.item_list["author"]))

			self.ui.cbx_downloader_type.clear()
			self.type_list = []
			if "chapter" in self.item_list and len(self.item_list["chapter"]) > 0:
				self.type_list.append("chapter")
				self.ui.cbx_downloader_type.addItem(TRSM("chapter"))
			if "book" in self.item_list and len(self.item_list["book"]) > 0:
				self.type_list.append("book")
				self.ui.cbx_downloader_type.addItem(TRSM("book"))
			if "extra" in self.item_list and len(self.item_list["extra"]) > 0:
				self.type_list.append("extra")
				self.ui.cbx_downloader_type.addItem(TRSM("extra"))

		if self.ui.cbx_downloader_type.count() > 0:
			self.ui.cbx_downloader_type.setCurrentIndex(0)
			self.current_type = self.type_list[self.ui.cbx_downloader_type.currentIndex()]
			if self.current_type != "":
				self.update_chapter_list()
				pass
		else:
			util.msg_box(TRSM("Can not found list"),self.main_controller)

		pass

	def chapter_download_trigger(self, message, current_page, total_page, current_chapter, total_chapter):
		if message != "":
			self.ui.txt_downloader_log.append(message)

		self.ui.pgb_downloader_current.setMaximum(total_page)
		self.ui.pgb_downloader_current.setValue(current_page)

		self.ui.pgb_downloader_total.setMaximum(total_chapter)
		self.ui.pgb_downloader_total.setValue(current_chapter)
		pass

	def chapter_download_finish(self):
		if self.ui.pgb_downloader_current.maximum() == 0:
			self.ui.pgb_downloader_current.setMaximum(100)
		self.ui.pgb_downloader_current.setValue(self.ui.pgb_downloader_current.maximum())
		self.ui.pgb_downloader_total.setValue(self.ui.pgb_downloader_total.maximum())

		self.ui.btn_downloader_start.setEnabled(True)
		self.ui.btn_downloader_cancel.setEnabled(False)

		self.chapter_download_worker.trigger.disconnect(self.chapter_download_trigger)
		self.chapter_download_worker.finished.disconnect(self.chapter_download_finish)

		self.ui.txt_downloader_log.append(TRSM("Finish all download!"))

		self.main_controller.show_tray_message(TRSM("Finish all download!"))
		self.main_controller.try_play_notification_sound()

		pass

	def chapter_download_cancel(self):
		self.ui.btn_downloader_start.setEnabled(True)
		self.ui.btn_downloader_cancel.setEnabled(False)
		self.ui.txt_downloader_log.append(TRSM("Download canceled!"))
		pass

	# internal function
	def load_url(self,url):
		self.ui.txt_downloader_url.setText(url)
		self.btn_downloader_check_clicked()

	def update_chapter_list(self):
		self.ui.list_downloader_chapter.clear()

		if self.current_type == "":
			return

		for idx, tmp_chapter in enumerate(self.item_list[self.current_type]):
			item = QListWidgetItem()
			tmp_title = ""
			if self.current_type == "book":
				tmp_title += str(tmp_chapter["index"]).zfill(int(MY_CONFIG.get("general", "book_padding")))
			else:
				tmp_title += str(tmp_chapter["index"]).zfill(int(MY_CONFIG.get("general", "chapter_padding")))
			tmp_title += " - " + tmp_chapter["title"]
			item.setText(tmp_title)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			#if idx < 3:
			#	item.setCheckState(QtCore.Qt.Checked)
			#else:
			item.setCheckState(QtCore.Qt.Unchecked)
			self.ui.list_downloader_chapter.addItem(item)

		if self.ui.list_downloader_chapter.count() > 0:
			self.ui.btn_downloader_select.setEnabled(True)
			self.ui.btn_downloader_unselect.setEnabled(True)
			self.ui.btn_downloader_select_all.setEnabled(True)
			self.ui.btn_downloader_unselect_all.setEnabled(True)
			self.ui.btn_downloader_start.setEnabled(True)
		else:
			self.ui.btn_downloader_select.setEnabled(False)
			self.ui.btn_downloader_unselect.setEnabled(False)
			self.ui.btn_downloader_select_all.setEnabled(False)
			self.ui.btn_downloader_unselect_all.setEnabled(False)
			self.ui.btn_downloader_start.setEnabled(False)

		pass

