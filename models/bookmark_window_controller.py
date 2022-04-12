import json

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidgetItem

import util
from uis import bookmark_window

from const import *

class BookmarkWindowController(QtWidgets.QMainWindow):
	def __init__(self,app,main_controller,parent_controller):
		super().__init__()
		self.app = app
		self.main_controller = main_controller
		self.parent_controller = parent_controller
		self.ui = bookmark_window.Ui_MainWindow()
		self.ui.setupUi(self)
		self.bookmarks = []
		self.setup_control()

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)

		# GUI
		self.retranslateUi()

		#action
		self.ui.table_bookmark.itemChanged.connect(self.table_bookmark_changed)

		self.ui.btn_load.clicked.connect(self.btn_load_clicked)
		self.ui.btn_close.clicked.connect(self.btn_close_clicked)
		self.ui.btn_delete.clicked.connect(self.btn_delete_clicked)
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)
		pass

	def add_book_mark(self,url,title):
		self._load_bookmarks()
		# check is exist
		for tmp_bookmark in self.bookmarks:
			if tmp_bookmark["url"] == url:
				util.msg_box(TRSM("Bookmark already exist"),self.main_controller)
				return False

		self.bookmarks.append({"url":url,"title":title})
		self._save_bookmarks()

	#action
	def btn_load_clicked(self):
		selected = self.ui.table_bookmark.selectionModel()
		rows = selected.selectedRows()
		if len(rows) == 1:
			row = rows[0].row()
			url = self.ui.table_bookmark.item(row, 1).text()
			self.parent_controller.load_url(url)
			self.close()
		elif len(rows) == 0:
			util.msg_box(TRSM("Please select at least one bookmark"),self)
			pass
		elif len(rows) > 1:
			util.msg_box(TRSM("Please select only one bookmark"),self)
			pass

	def btn_close_clicked(self):
		self.close()

	def btn_delete_clicked(self):
		selected = self.ui.table_bookmark.selectionModel()
		rows = selected.selectedRows()
		if len(rows) > 0:
			if util.confirm_box(TRSM("Confirm to delete?"),self):
				for row in sorted(rows, reverse=True):
					row_index = row.row()
					self.ui.table_bookmark.removeRow(row_index)
				self.bookmarks = self._table_to_json()
				self._save_bookmarks()
		else:
			util.msg_box(TRSM("Please select at least one bookmark"),self)
		pass

	def table_bookmark_changed(self):
		self.bookmarks = self._table_to_json()
		self._save_bookmarks()

	# internal function
	def _load_bookmarks(self):
		bookmarks = MY_BOOKMARK.get("bookmarks","bookmarks")
		if bookmarks:
			self.bookmarks = json.loads(bookmarks)
		else:
			self.bookmarks = []

	def _save_bookmarks(self):
		MY_BOOKMARK.set("bookmarks","bookmarks",json.dumps(self.bookmarks))
		MY_BOOKMARK.save()

	def _update_table(self):
		self.ui.table_bookmark.blockSignals(True)
		self.ui.table_bookmark.clear()
		self.ui.table_bookmark.setHorizontalHeaderLabels([TRSM("Title"),TRSM("URL")])
		self.ui.table_bookmark.setRowCount(len(self.bookmarks))
		for idx,bookmark in enumerate(self.bookmarks):
			self.ui.table_bookmark.setItem(idx, 0, QTableWidgetItem(bookmark["title"]))
			self.ui.table_bookmark.setItem(idx, 1, QTableWidgetItem(bookmark["url"]))
		self.ui.table_bookmark.resizeColumnsToContents()
		self.ui.table_bookmark.blockSignals(False)

	def _table_to_json(self):
		result = []
		for row_idx in range(self.ui.table_bookmark.rowCount()):
			result.append({
				"title": self.ui.table_bookmark.item(row_idx,0).text(),
				"url": self.ui.table_bookmark.item(row_idx, 1).text(),
			})
		return result

	#override
	def show(self):
		super().show()
		self._load_bookmarks()
		self._update_table()
		pass
