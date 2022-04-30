#import time
import threading
#from PIL import Image, ImageQt
from enum import Enum
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtGui import QPixmap, QImage, QCursor
from PyQt5.QtWidgets import QFileDialog, QWidget, QSizePolicy, QToolTip
from PyQt5.QtCore import Qt, QEvent, QPoint, QSize, QTimer

from models.const import *
from models import util
from models.reader import Reader
from uis import reader_window
from models.controllers.bookmark_window_controller import BookmarkWindowController

class ScrollFlow(Enum):
	LEFT_RIGHT = 1
	UP_DOWN = 2

class PageFit(Enum):
	HEIGHT = 1
	WIDTH = 2
	BOTH = 3
	WIDTH80 = 4

class PageMode(Enum):
	SINGLE = 1
	DOUBLE = 2
	TRIPLE = 3
	QUADRUPLE = 4

class PageFlow(Enum):
	LEFT_TO_RIGHT = 1
	RIGHT_TO_LEFT = 2


class ReaderWindowController(QtWidgets.QMainWindow):
	def __init__(self,app,main_controller):
		super().__init__()
		self.app = app
		self.main_controller = main_controller
		self.ui = reader_window.Ui_MainWindow()
		self.ui.setupUi(self)
		self.image_list = []
		self.current_single_image_list = []
		self.current_double_image_list = []
		self.current_triple_image_list = []
		self.current_quadruple_image_list = []
		self.current_path_index = 0
		self.current_page_index = 0
		self.current_open_folder = ""
		self.current_open_file = ""
		self.current_image_file = ""
		self.before_full_screen_is_max = False
		self.last_time_move = QPoint(0,0)
		self.pages_ratio_require = float(MY_CONFIG.get("general", "check_is_2_page"))
		self.current_reader = Reader()

		self.scroll_flow = ScrollFlow[MY_CONFIG.get("reader", "scroll_flow")]
		self.page_fit = PageFit[MY_CONFIG.get("reader", "page_fit")]
		self.page_mode = PageMode[MY_CONFIG.get("reader", "page_mode")]
		self.page_flow = PageFlow[MY_CONFIG.get("reader", "page_flow")]

		# add the folder list combobox
		self.ui.tb_main.addSeparator()
		#spacer = QtWidgets.QWidget()
		#spacer.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
		#spacer.setFixedSize(5,1)
		#self.ui.tb_main.addWidget(spacer)
		self.cbx_folders = QtWidgets.QComboBox()
		self.cbx_folders.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.cbx_folders.setFixedSize(95,22)
		self.ui.tb_main.addWidget(self.cbx_folders)
		# add spacer
		spacer = QtWidgets.QWidget()
		spacer.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
		spacer.setFixedSize(5,1)
		self.ui.tb_main.addWidget(spacer)
		# add the slider
		self.slider_pages = QtWidgets.QSlider()
		self.slider_pages.setOrientation(QtCore.Qt.Horizontal)
		self.slider_pages.setTickPosition(QtWidgets.QSlider.TicksBelow)
		self.slider_pages.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
		self.slider_pages.setFixedSize(80,22)
		self.slider_pages.setSingleStep(1)
		self.slider_pages.setPageStep(5)
		self.slider_pages.setMaximum(0)
		self.slider_pages.setMinimum(0)
		self.slider_pages.setTickInterval(0)
		self.slider_pages.setInvertedControls(True)
		if self.page_flow == PageFlow.RIGHT_TO_LEFT:
			self.slider_pages.setInvertedAppearance(True)
		self.ui.tb_main.addWidget(self.slider_pages)
		self.ui.tb_right.setVisible(False)

		self.bookmark_controller = BookmarkWindowController(self.app,self,self,is_reader=True)

		self.setup_control()

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
		self.ui.menubar.setVisible(False)
		self.ui.lbl_tmp.setVisible(False)
		self.ui.lbl_tmp.setText("")

		self.update_scroll_flow_button()
		self.update_page_fit_button()
		self.update_page_mode_button()
		self.update_page_flow_button()

		# GUI
		self.retranslateUi()

		# action
		self.ui.actionFileExit.triggered.connect(self.on_file_exit)
		self.ui.actionFileOpenFolder.triggered.connect(self.on_file_open_folder)
		self.ui.actionFileOpenFile.triggered.connect(self.on_file_open_file)
		self.ui.actionScrollFlowLeftRight.triggered.connect(lambda: self.change_scroll_flow(ScrollFlow.LEFT_RIGHT))
		self.ui.actionScrollFlowUpDown.triggered.connect(lambda: self.change_scroll_flow(ScrollFlow.UP_DOWN))
		self.ui.actionFitHeight.triggered.connect(lambda: self.change_page_fit(PageFit.HEIGHT))
		self.ui.actionFitWidth.triggered.connect(lambda: self.change_page_fit(PageFit.WIDTH))
		self.ui.actionFitBoth.triggered.connect(lambda: self.change_page_fit(PageFit.BOTH))
		self.ui.actionFitWidth80.triggered.connect(lambda: self.change_page_fit(PageFit.WIDTH80))
		self.ui.actionPageModeSingle.triggered.connect(lambda: self.change_page_mode(PageMode.SINGLE))
		self.ui.actionPageModeDouble.triggered.connect(lambda: self.change_page_mode(PageMode.DOUBLE))
		self.ui.actionPageModeTriple.triggered.connect(lambda: self.change_page_mode(PageMode.TRIPLE))
		self.ui.actionPageModeQuadruple.triggered.connect(lambda: self.change_page_mode(PageMode.QUADRUPLE))
		self.ui.actionPageFlowLeftToRight.triggered.connect(lambda: self.change_page_flow(PageFlow.LEFT_TO_RIGHT))
		self.ui.actionPageFlowRightToLeft.triggered.connect(lambda: self.change_page_flow(PageFlow.RIGHT_TO_LEFT))
		self.ui.actionFullscreen.triggered.connect(self.btn_full_screen_clicked)
		self.ui.actionAddBookmark.triggered.connect(self.btn_add_bookmark_clicked)
		self.ui.actionBookmarkList.triggered.connect(self.btn_bookmark_list_clicked)

		self.cbx_folders.currentIndexChanged.connect(self.cbx_folder_current_index_changed)
		self.slider_pages.sliderPressed.connect(self.slider_pages_slider_pressed)
		self.slider_pages.sliderMoved.connect(self.slider_pages_slider_moved)
		self.slider_pages.sliderReleased.connect(self.slider_pages_slider_released)
		self.slider_pages.valueChanged.connect(self.slider_pages_value_changed)

		self.ui.scrollArea.verticalScrollBar().valueChanged.connect(self.scroll_area_scroll_bar_value_changed)

		# event filter
		self.ui.scrollArea.installEventFilter(self)
		self.slider_pages.installEventFilter(self)
		pass

	def retranslateUi(self):
		self.ui.retranslateUi(self)
		self.bookmark_controller.retranslateUi()
		pass

	# override
	def show(self):
		super().show()
		self.update_background()
		#self.get_image_list_from_folder("F:/comics/全知讀者視角")
		#self.get_image_list_from_folder("F:/comics/全职法师")
		#self.get_image_list_from_folder("F:/comics/烙印战士_good")
		#self.get_image_list_from_file("F:/comics/全职法师/全职法师-chapter-00001-00025.cbz")
		#self.get_image_list_from_file("F:/comics/全职法师/全职法师-chapter-00001-00025.zip")
		#self.get_image_list_from_file("F:/comics/全职法师/全职法师-chapter-00001.zip")
		#self.get_image_list_from_folder("F:/comics/測試")
		#self.get_image_list_from_file("F:/comics/全职法师/全职法师-chapter-00001-00002.pdf")
		#self.get_image_list_from_file("F:/comics/火影忍者博人傳2/火影忍者博人傳-chapter-00001.pdf")

	def resizeEvent(self, event):
		self.update_images_size()

	def keyPressEvent(self, e):
		if e.key() == Qt.Key_F11 or e.key() == Qt.Key_F:
			self.btn_full_screen_clicked()
		if e.key() == Qt.Key_Escape:
			if self.isFullScreen():
				self.btn_full_screen_clicked()

	def closeEvent(self, event):
		if util.confirm_box(TRSM("Confirm to quit?"),self):
			self.reset_data()
			event.accept()
		else:
			event.ignore()

	#action
	def cursor_busy(self):
		self.app.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))

	def cursor_un_busy(self):
		self.app.restoreOverrideCursor()

	def btn_full_screen_clicked(self):
		if not self.isFullScreen():
			#self.ui.menubar.setVisible(False)
			self.ui.tb_main.setVisible(False)
			#self.ui.tb_right.setVisible(False)
			if self.isMaximized():
				self.before_full_screen_is_max = True
			else:
				self.before_full_screen_is_max = False
			self.showFullScreen()
		else:
			#self.ui.menubar.setVisible(True)
			self.ui.tb_main.setVisible(True)
			#self.ui.tb_right.setVisible(True)
			if self.before_full_screen_is_max:
				self.showMaximized()
			else:
				self.showNormal()

	def btn_add_bookmark_clicked(self):
		if self.current_open_folder != "" and self.current_image_file != "":
			self.bookmark_controller.add_book_mark(self.current_image_file,self.current_open_folder)
		elif self.current_open_file != "" and self.current_image_file != "":
			self.bookmark_controller.add_book_mark(self.current_image_file, self.current_open_file)
		else:
			util.msg_box(TRSM("Please open a folder or file"),self)

	def btn_bookmark_list_clicked(self):
		self.bookmark_controller.show()
		pass

	def on_file_exit(self):
		self.close()

	def on_file_open_folder(self):
		old_folder_path = MY_CONFIG.get("general", "download_folder")
		folder_path = QFileDialog.getExistingDirectory(self,TRSM("Open folder"), old_folder_path)
		if folder_path != "":
			#print("open folder",folder_path)
			self.get_image_list_from_folder(folder_path)

	def on_file_open_file(self):
		old_folder_path = MY_CONFIG.get("general", "download_folder")

		reader_objs = Reader.get_all_readers_object()
		all_support_file_filter_list = []
		other_support_file_filter_list = []
		for reader_obj in reader_objs:
			file_filters = reader_obj.FILE_FILTER
			for file_filter in file_filters:
				all_support_file_filter_list.append(file_filter["filters"])
				other_support_file_filter_list.append(TRSM(file_filter["name"]) + " (" + file_filter["filters"] + ")")
		other_support_file_filter_string = ";;".join(other_support_file_filter_list)
		all_support_file_filter_string = TRSM("All supported format") + " (" + " ".join(all_support_file_filter_list) + ")"
		final_filter_string = all_support_file_filter_string + ";;" + other_support_file_filter_string

		file_path = QFileDialog.getOpenFileName(self,TRSM("Open File"), old_folder_path, final_filter_string)
		if len(file_path) >= 2 and file_path[0] != "":
			#print(file_path[0])
			self.get_image_list_from_file(file_path[0])

	def cbx_folder_current_index_changed(self):
		self.current_path_index = self.cbx_folders.currentIndex()
		self.start_load_current_path_list()
		# un-focus of combobox
		self.setFocus()

	def slider_pages_slider_pressed(self):
		QToolTip.showText(QCursor.pos(),"%d / %d" % (self.slider_pages.value()+1,self.slider_pages.maximum()+1))

	def slider_pages_slider_moved(self, new_value):
		QToolTip.showText(QCursor.pos(),"%d / %d" % (new_value+1,self.slider_pages.maximum()+1))

	def slider_pages_slider_released(self):
		self.go_page_index(self.slider_pages.value())

	def slider_pages_value_changed(self, new_value):
		if not self.slider_pages.isSliderDown():
			self.go_page_index(new_value)
			QToolTip.showText(QCursor.pos(),"%d / %d" % (new_value+1,self.slider_pages.maximum()+1))

	def scroll_area_scroll_bar_value_changed(self):
		if self.scroll_flow == ScrollFlow.UP_DOWN:
			x = self.ui.scrollArea.horizontalScrollBar().value()
			y = self.ui.scrollArea.verticalScrollBar().value()
			w = self.ui.scrollArea.frameGeometry().width()
			h = self.ui.scrollArea.frameGeometry().height()
			current_visible_frame = QtCore.QRect(x,y,w,h)
			#print(f"x:{x},y:{y},w:{w},y:{h}, frame:{current_visible_frame}")

			found_row = 0
			current_y = 0
			max_row_height = 0
			old_row = -1
			for i in range(self.ui.layout_main.count()):
				tmp_widget = self.ui.layout_main.itemAt(i).widget()
				if type(tmp_widget) is QtWidgets.QLabel:
					row, col, _, _ = self.ui.layout_main.getItemPosition(i)
					# to fix the y was not yet update
					child_frame = tmp_widget.frameGeometry()
					if old_row != row:
						current_y += max_row_height
						max_row_height = 0
					#print(f"frame:{tmp_widget.frameGeometry()}")
					widget_height = child_frame.height()
					max_row_height = max(max_row_height,widget_height)
					old_row = row

					child_real_frame = QtCore.QRect(child_frame.x(),current_y,child_frame.width(),widget_height)

					if current_visible_frame.intersects(child_real_frame):
						found_row = row
						break

			# change current page index
			self.current_page_index = found_row
			self.current_image_file = self.get_file_from_page_index(found_row)
			#print(f"scroll bar value changed update slider {found_row}")
			self.update_slider()

	def move_scroll_area_by_index(self):
		#fix for item frame update delay
		current_y = 0
		max_row_height = 0
		old_row = -1
		for i in range(self.ui.layout_main.count()):
			tmp_widget = self.ui.layout_main.itemAt(i).widget()
			if type(tmp_widget) is QtWidgets.QLabel:
				row, col, _, _ = self.ui.layout_main.getItemPosition(i)
				#print(f"checking row:{row}, col:{col}")
				if row == self.current_page_index:
					#target_y = tmp_widget.frameGeometry().y()
					#print(f"geometry:{tmp_widget.geometry()}")
					#print(f"frame:{tmp_widget.frameGeometry()}")
					#print(f"try move to row:{row} y:{current_y+max_row_height}")
					#print(f"scrollbar max:{self.ui.scrollArea.verticalScrollBar().maximum()}")
					#print(f"current_y:{current_y+max_row_height}")
					#self.ui.scrollArea.verticalScrollBar().setValue(target_y)
					#self.ui.scrollArea.verticalScrollBar().blockSignals(True)
					self.ui.scrollArea.verticalScrollBar().setValue(current_y+max_row_height)
					#self.ui.scrollArea.verticalScrollBar().blockSignals(False)
					break
				else:
					if old_row != row:
						current_y += max_row_height
						max_row_height = 0
					#print(f"frame:{tmp_widget.frameGeometry()}")
					tmp_widget_height = tmp_widget.frameGeometry().height()
					max_row_height = max(max_row_height,tmp_widget_height)
					old_row = row

	# relate function
	def update_scroll_flow_button(self):
		self.ui.actionScrollFlowLeftRight.setChecked(False)
		self.ui.actionScrollFlowUpDown.setChecked(False)
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			self.ui.actionScrollFlowLeftRight.setChecked(True)
		elif self.scroll_flow == ScrollFlow.UP_DOWN:
			self.ui.actionScrollFlowUpDown.setChecked(True)

	def update_page_fit_button(self):
		self.ui.actionFitHeight.setChecked(False)
		self.ui.actionFitWidth.setChecked(False)
		self.ui.actionFitBoth.setChecked(False)
		self.ui.actionFitWidth80.setChecked(False)
		if self.page_fit == PageFit.HEIGHT:
			self.ui.actionFitHeight.setChecked(True)
		elif self.page_fit == PageFit.WIDTH:
			self.ui.actionFitWidth.setChecked(True)
		elif self.page_fit == PageFit.BOTH:
			self.ui.actionFitBoth.setChecked(True)
		elif self.page_fit == PageFit.WIDTH80:
			self.ui.actionFitWidth80.setChecked(True)

	def update_page_mode_button(self):
		self.ui.actionPageModeSingle.setChecked(False)
		self.ui.actionPageModeDouble.setChecked(False)
		self.ui.actionPageModeTriple.setChecked(False)
		self.ui.actionPageModeQuadruple.setChecked(False)
		if self.page_mode == PageMode.SINGLE:
			self.ui.actionPageModeSingle.setChecked(True)
		elif self.page_mode == PageMode.DOUBLE:
			self.ui.actionPageModeDouble.setChecked(True)
		elif self.page_mode == PageMode.TRIPLE:
			self.ui.actionPageModeTriple.setChecked(True)
		elif self.page_mode == PageMode.QUADRUPLE:
			self.ui.actionPageModeQuadruple.setChecked(True)

	def update_page_flow_button(self):
		self.ui.actionPageFlowLeftToRight.setChecked(False)
		self.ui.actionPageFlowRightToLeft.setChecked(False)
		if self.page_flow == PageFlow.LEFT_TO_RIGHT:
			self.ui.actionPageFlowLeftToRight.setChecked(True)
		elif self.page_flow == PageFlow.RIGHT_TO_LEFT:
			self.ui.actionPageFlowRightToLeft.setChecked(True)

	def change_scroll_flow(self,new_scroll_flow):
		if self.scroll_flow != new_scroll_flow:
			self.scroll_flow = new_scroll_flow
			self.update_scroll_flow_button()
			self.update_images()
			if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
				self.go_page_start()
			elif self.scroll_flow == ScrollFlow.UP_DOWN:
				self.go_page_index(self.current_page_index)
			MY_CONFIG.set("reader", "scroll_flow", str(self.scroll_flow.name))
			MY_CONFIG.save()
		else:
			self.update_scroll_flow_button()

	def change_page_fit(self,new_page_fit):
		if self.page_fit != new_page_fit:
			self.page_fit = new_page_fit
			self.update_page_fit_button()
			self.update_images_size()
			if self.scroll_flow == ScrollFlow.UP_DOWN:
				self.go_page_index(self.current_page_index)
			MY_CONFIG.set("reader", "page_fit", str(self.page_fit.name))
			MY_CONFIG.save()
		else:
			self.update_page_fit_button()

	def change_page_mode(self,new_page_mode):
		if self.page_mode != new_page_mode:
			self.page_mode = new_page_mode
			self.update_page_mode_button()
			if self.current_image_file != "":
				self.current_page_index = self.get_page_index_from_file(self.current_image_file)
			else:
				self.current_page_index = 0
			self.update_images()
			if self.scroll_flow == ScrollFlow.UP_DOWN:
				self.go_page_index(self.current_page_index)
			MY_CONFIG.set("reader", "page_mode", str(self.page_mode.name))
			MY_CONFIG.save()
		else:
			self.update_page_mode_button()

	def change_page_flow(self,new_page_flow):
		if self.page_flow != new_page_flow:
			self.page_flow = new_page_flow
			self.update_page_flow_button()
			if self.page_flow == PageFlow.RIGHT_TO_LEFT:
				self.slider_pages.setInvertedAppearance(True)
			else:
				self.slider_pages.setInvertedAppearance(False)
			self.update_images()
			MY_CONFIG.set("reader", "page_flow", str(self.page_flow.name))
			MY_CONFIG.save()
		else:
			self.update_page_flow_button()

	#internal function
	def reset_data(self):
		self.image_list = []
		self.current_single_image_list = []
		self.current_double_image_list = []
		self.current_triple_image_list = []
		self.current_quadruple_image_list = []
		self.current_path_index = 0
		self.current_page_index = 0
		self.current_open_folder = ""
		self.current_open_file = ""
		self.current_image_file = ""
		self.current_reader = None
		self.update_images()
		self.update_slider()
		self.update_path_list()
		pass

	def load_bookmark(self,folder,file):
		is_same_folder = False
		is_same_path_index = False
		if os.path.isdir(folder):
			if folder != self.current_open_folder:
				self.get_image_list_from_folder(folder)
			else:
				is_same_folder = True
		else:
			if folder != self.current_open_file:
				self.get_image_list_from_file(folder)
			else:
				is_same_folder = True

		# check file in which path index and page index
		new_path_index = self.get_path_index_from_file(file)
		if (not is_same_folder) or (new_path_index != self.current_path_index):
			self.current_path_index = new_path_index
			self.update_folder_combo_box_index()
			self.update_current_image_list_from_path_index()
		else:
			is_same_path_index = True

		self.current_page_index = self.get_page_index_from_file(file)
		self.current_image_file = file
		if self.scroll_flow == ScrollFlow.UP_DOWN and is_same_path_index:
			pass
		else:
			self.update_images()
			self.current_image_file = file

		if self.scroll_flow == ScrollFlow.UP_DOWN:
			# delay 0.3 sec to load page
			QTimer.singleShot(300,lambda: self.delay_load_book_mark_update_page(self.current_page_index))

	def delay_load_book_mark_update_page(self,page_index):
		self.current_page_index = page_index
		self.update_slider()
		self.go_page_index(self.current_page_index)

	def get_image_list_from_folder(self,folder_path):
		self.cursor_busy()
		#print("start get image list")
		#start_time = time.time()
		#self.image_list = util.get_image_list_from_folder_old(folder_path)

		self.current_reader = Reader.init_folder_reader(folder_path)
		self.image_list = self.current_reader.get_file_list()

		#self.image_list = []
		#util.get_image_list_from_folder(folder_path,self.image_list)
		#self.image_list = sorted(self.image_list, key=lambda d: d['path'])

		#print("used %0.3f seconds" % (time.time() - start_time))
		#print("end get image list")
		self.cursor_un_busy()
		if len(self.image_list) > 0:
			self.current_open_folder = folder_path
			self.current_open_file = ""
			self.current_path_index = 0
			self.update_path_list()
			self.start_load_current_path_list()
		else:
			util.msg_box(TRSM("Can not found any image in folder"),self)

	def get_image_list_from_file(self,file_path):
		self.cursor_busy()
		self.image_list = []
		self.current_reader = Reader.init_reader_by_file(file_path)
		self.image_list = self.current_reader.get_file_list()
		#util.get_image_list_from_file(file_path,self.image_list)
		#self.image_list = sorted(self.image_list, key=lambda d: d['path'])
		self.cursor_un_busy()

		if len(self.image_list) > 0:
			self.current_open_file = file_path
			self.current_open_folder = ""
			self.current_path_index = 0
			self.update_path_list()
			self.start_load_current_path_list()
		else:
			util.msg_box(TRSM("Can not found any image in file"),self)

	def start_load_current_path_list(self):
		#print("start_load_current_path_list")
		self.update_current_image_list_from_path_index()
		#print("finish update image list")
		self.current_page_index = 0
		self.update_images()
		self.go_page_start()

	def update_current_image_list_from_path_index(self):
		list1,list2,list3,list4 = self.process_make_multi_pages_list(self.image_list[self.current_path_index]["files"])
		self.current_single_image_list = list1
		self.current_double_image_list = list2
		self.current_triple_image_list = list3
		self.current_quadruple_image_list = list4

	def update_path_list(self):
		self.cbx_folders.blockSignals(True)
		self.cbx_folders.clear()
		for path_list in self.image_list:
			self.cbx_folders.addItem(path_list["path"])
		self.cbx_folders.blockSignals(False)

	def update_folder_combo_box_index(self):
		self.cbx_folders.blockSignals(True)
		self.cbx_folders.setCurrentIndex(self.current_path_index)
		self.cbx_folders.blockSignals(False)

	def update_slider(self):
		#print(f"update_slider self.current_page_index: {self.current_page_index}")
		target_list = self.get_current_target_list()
		self.slider_pages.blockSignals(True)
		self.slider_pages.setMinimum(0)
		self.slider_pages.setMaximum(len(target_list)-1)
		self.slider_pages.setValue(self.current_page_index)
		self.slider_pages.setTickInterval(self.slider_pages.maximum()//8)
		self.slider_pages.blockSignals(False)
		self.slider_pages.setToolTip("%d / %d" % (self.slider_pages.value()+1, self.slider_pages.maximum()+1))

	def update_images(self):
		#print("update images")
		# clean all label first
		#start_time = time.time()
		for i in reversed(range(self.ui.layout_main.count())):
			tmp_widget = self.ui.layout_main.itemAt(i).widget()
			if type(tmp_widget) is QtWidgets.QLabel:
				self.ui.layout_main.removeItem(self.ui.layout_main.itemAt(i))
				tmp_widget.setParent(None)
		#print("remove all widgets, used %0.3fs" % (time.time()-start_time))

		target_image_list = []
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			tmp_target_list = self.get_current_target_list()
			if self.current_page_index < len(tmp_target_list):
				target_image_list = [tmp_target_list[self.current_page_index]]
		elif self.scroll_flow == ScrollFlow.UP_DOWN:
			target_image_list = self.get_current_target_list()

		tmp_current_image_file = ""
		self.cursor_busy()
		#start_time = time.time()

		for rowIdx, row in enumerate(target_image_list):
			if tmp_current_image_file == "":
				tmp_current_image_file = row[0]
			col_count = len(row)
			for colIdx, file in enumerate(row):
				#file_data = self.current_reader.get_data_from_file(file)
				#q_pixmap = QPixmap()
				#q_pixmap.loadFromData(file_data)
				#q_pixmap = QPixmap(file)
				q_pixmap = self.current_reader.get_qpixmap_from_file(file)
				lbl_tmp = QtWidgets.QLabel(self.ui.scrollAreaWidgetContents)
				lbl_tmp.setLineWidth(0)
				lbl_tmp.setText("")
				lbl_tmp.setScaledContents(True)
				lbl_tmp.setPixmap(q_pixmap)
				lbl_tmp.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
				if col_count == 1 and self.page_mode == PageMode.DOUBLE:
					self.ui.layout_main.addWidget(lbl_tmp, rowIdx, colIdx, 1, 2)
				elif col_count == 1 and self.page_mode == PageMode.TRIPLE:
					self.ui.layout_main.addWidget(lbl_tmp, rowIdx, colIdx, 1, 3)
				elif col_count == 1 and self.page_mode == PageMode.QUADRUPLE:
					self.ui.layout_main.addWidget(lbl_tmp, rowIdx, colIdx, 1, 4)
				else:
					if self.page_flow == PageFlow.RIGHT_TO_LEFT:
						self.ui.layout_main.addWidget(lbl_tmp,rowIdx, self.page_mode.value - colIdx - 1, 1, 1)
					else:
						self.ui.layout_main.addWidget(lbl_tmp,rowIdx,colIdx, 1, 1)
				self.ui.layout_main.setAlignment(lbl_tmp,Qt.AlignHCenter | Qt.AlignCenter)
		#print("finish add widgets, used %0.3fs" % (time.time()-start_time))
		self.cursor_un_busy()
		self.current_image_file = tmp_current_image_file
		self.update_images_size()
		#print("update image update slider")
		self.update_slider()

	def update_images_size(self):
		#print("update images size")
		area_size = self.ui.scrollArea.size()
		total_width, total_height = self.update_image_size_inner(area_size)
		#fix the scroll bar update delay
		if total_height-area_size.height() > 0:
			self.ui.scrollArea.verticalScrollBar().setMaximum(total_height-area_size.height())
		else:
			self.ui.scrollArea.verticalScrollBar().setMaximum(1)
		if total_width-area_size.width() > 0:
			self.ui.scrollArea.horizontalScrollBar().setMaximum(total_width-area_size.width())
		else:
			self.ui.scrollArea.horizontalScrollBar().setMaximum(1)

	def update_image_size_inner(self,area_size):
		rows = self.ui.layout_main.rowCount()
		#cols = self.ui.layout_main.columnCount()
		cols = self.page_mode.value
		#print(f"rows: {rows}, cols: {cols}")
		v_scrollbar_size = self.ui.scrollArea.verticalScrollBar().size().width()
		h_scrollbar_size = self.ui.scrollArea.horizontalScrollBar().size().height()

		total_width = 0
		total_height = 0
		for row in range(rows):
			row_width = 0
			row_height = 0
			for col in range(cols):
				if self.ui.layout_main.itemAtPosition(row,col) is not None:
					tmp_widget = self.ui.layout_main.itemAtPosition(row,col).widget()
					if (tmp_widget is not None) and (type(tmp_widget) is QtWidgets.QLabel):
						if tmp_widget.pixmap() is not None:
							image_size = tmp_widget.pixmap().size()
							if image_size.width() / image_size.height() > self.pages_ratio_require:
								# 2 page already!
								new_image_size = self.get_fit_image_size(
									QSize(area_size.width(), area_size.height()), image_size,
									v_scrollbar_size, h_scrollbar_size)
							else:
								new_image_size = self.get_fit_image_size(
									QSize(area_size.width() / cols, area_size.height()),image_size,
									v_scrollbar_size / cols, h_scrollbar_size)
							tmp_widget.setFixedSize(new_image_size.width(), new_image_size.height())
							#print(f"row:{row},col:{col}, width:{new_image_size.width()},height:{new_image_size.height()}")
							row_width += new_image_size.width()
							row_height = max(row_height, new_image_size.height())
			total_width = max(total_width,row_width)
			total_height += row_height
		#print(f"total_width:{total_width}, total_height:{total_height}")
		return total_width, total_height

	def get_fit_image_size(self,area_size,image_size,v_scrollbar_size,h_scrollbar_size):
		new_width = image_size.width()
		new_height = image_size.height()
		width_rate = height_rate = 1
		if self.page_fit == PageFit.BOTH:
			width_rate = image_size.width()/area_size.width()
			height_rate = image_size.height()/area_size.height()
			if self.scroll_flow == ScrollFlow.UP_DOWN:
				new_width -= v_scrollbar_size
				new_height = new_width / image_size.width() * image_size.height()
		if self.page_fit == PageFit.HEIGHT or (self.page_fit == PageFit.BOTH and width_rate <= height_rate):
			new_height = area_size.height()
			new_width = new_height/image_size.height() * image_size.width()
			# fallback to check scroll bar will appear
			if new_width > area_size.width():
				new_height -= h_scrollbar_size
				new_width = new_height/image_size.height() * image_size.width()
		elif self.page_fit == PageFit.WIDTH or self.page_fit == PageFit.WIDTH80 or (self.page_fit == PageFit.BOTH and width_rate >= height_rate):
			if self.page_fit == PageFit.WIDTH80:
				new_width = area_size.width()*0.8
			else:
				new_width = area_size.width()
			new_height = new_width/image_size.width() * image_size.height()
			# fallback to check scroll bar will appear
			if new_height > area_size.height() or self.scroll_flow == ScrollFlow.UP_DOWN:
				new_width -= v_scrollbar_size
				new_height = new_width/image_size.width() * image_size.height()

		return QSize(new_width,new_height)

	def get_current_target_list(self):
		if self.page_mode == PageMode.SINGLE:
			return self.current_single_image_list
		elif self.page_mode == PageMode.DOUBLE:
			return self.current_double_image_list
		elif self.page_mode == PageMode.TRIPLE:
			return self.current_triple_image_list
		elif self.page_mode == PageMode.QUADRUPLE:
			return self.current_quadruple_image_list
		return self.current_single_image_list

	def go_page_index(self,new_index):
		self.current_page_index = new_index
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			self.update_images()
		else:
			self.move_scroll_area_by_index()

	def go_prev_page(self):
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			if self.current_page_index > 0:
				self.current_page_index -= 1
				self.update_images()
				self.go_page_end()
			elif self.current_path_index > 0:
				self.go_prev_chapter()
		elif self.scroll_flow == ScrollFlow.UP_DOWN:
			if self.current_path_index > 0:
				self.go_prev_chapter()

	def go_prev_chapter(self):
		self.current_path_index -= 1
		self.update_folder_combo_box_index()
		self.update_current_image_list_from_path_index()
		current_target_list = self.get_current_target_list()
		self.current_page_index = len(current_target_list) - 1
		#print(f"go_prev__chapter self.current_page_index:{self.current_page_index}")
		self.update_images()
		self.go_page_end()

	def go_next_page(self):
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			current_target_list = self.get_current_target_list()
			if self.current_page_index < len(current_target_list) - 1:
				self.current_page_index += 1
				self.update_images()
				self.go_page_start()
			elif self.current_path_index < len(self.image_list) - 1:
				self.go_next_chapter()
		elif self.scroll_flow == ScrollFlow.UP_DOWN:
			if self.current_path_index < len(self.image_list) - 1:
				self.go_next_chapter()

	def go_next_chapter(self):
		self.current_path_index += 1
		self.update_folder_combo_box_index()
		self.update_current_image_list_from_path_index()
		self.current_page_index = 0
		self.update_images()
		self.go_page_start()

	def go_page_start(self):
		#print("go page start")
		#self.ui.scrollArea.verticalScrollBar().blockSignals(True)
		self.ui.scrollArea.verticalScrollBar().setValue(0)
		#self.ui.scrollArea.verticalScrollBar().blockSignals(False)
		if self.page_flow == PageFlow.LEFT_TO_RIGHT:
			self.ui.scrollArea.horizontalScrollBar().setValue(0)
		else:
			self.ui.scrollArea.horizontalScrollBar().setValue(self.ui.scrollArea.horizontalScrollBar().maximum())

	def go_page_end(self):
		#print("go page end")
		#print(f"go_page_end self.current_page_index:{self.current_page_index}")
		#self.ui.scrollArea.verticalScrollBar().blockSignals(True)
		self.ui.scrollArea.verticalScrollBar().setValue(self.ui.scrollArea.verticalScrollBar().maximum())
		#self.ui.scrollArea.verticalScrollBar().blockSignals(False)
		if self.page_flow == PageFlow.LEFT_TO_RIGHT:
			self.ui.scrollArea.horizontalScrollBar().setValue(self.ui.scrollArea.horizontalScrollBar().maximum())
		else:
			self.ui.scrollArea.horizontalScrollBar().setValue(0)
		#print("end go page end")

	def update_background(self):
		reader_background = MY_CONFIG.get("reader", "background")
		self.ui.scrollAreaWidgetContents.setStyleSheet("background-color:"+reader_background+";")

	# event filter
	def eventFilter(self, source, event):
		if source == self.ui.scrollArea:
			self.handle_scroll_area_event(event)
		return QWidget.eventFilter(self, source, event)

	def handle_scroll_area_event(self,event):
		if event.type() == QEvent.MouseMove:
			if self.last_time_move == QPoint(0,0):
				self.last_time_move = event.pos()
			distance_x = self.last_time_move.x() - event.pos().x()
			distance_y = self.last_time_move.y() - event.pos().y()
			self.ui.scrollArea.horizontalScrollBar().setValue(self.ui.scrollArea.horizontalScrollBar().value() + distance_x)
			self.ui.scrollArea.verticalScrollBar().setValue(self.ui.scrollArea.verticalScrollBar().value() + distance_y)
			self.last_time_move = event.pos()
		elif event.type() == QEvent.MouseButtonRelease:
			self.last_time_move = QPoint(0, 0)
		elif event.type() == QEvent.Wheel:
			delta_y = event.angleDelta().y()
			if delta_y > 0:
				self.go_prev_page()
				pass
			elif delta_y < 0:
				self.go_next_page()
				pass
		elif event.type() == QEvent.KeyRelease:
			if event.key() == Qt.Key_Down:
				if self.ui.scrollArea.verticalScrollBar().value() == self.ui.scrollArea.verticalScrollBar().maximum():
					self.go_next_page()
			if event.key() == Qt.Key_Up:
				if self.ui.scrollArea.verticalScrollBar().value() == 0:
					self.go_prev_page()
			if event.key() == Qt.Key_Left:
				if self.ui.scrollArea.horizontalScrollBar().value() == 0:
					if self.page_flow == PageFlow.LEFT_TO_RIGHT:
						self.go_prev_page()
					elif self.page_flow == PageFlow.RIGHT_TO_LEFT:
						self.go_next_page()
			if event.key() == Qt.Key_Right:
				if self.ui.scrollArea.horizontalScrollBar().value() == self.ui.scrollArea.horizontalScrollBar().maximum():
					if self.page_flow == PageFlow.LEFT_TO_RIGHT:
						self.go_next_page()
					elif self.page_flow == PageFlow.RIGHT_TO_LEFT:
						self.go_prev_page()
		pass

	def get_page_index_from_file(self,image_file):
		target_list = self.get_current_target_list()
		for idx, tmp_list in enumerate(target_list):
			if image_file in tmp_list:
				return idx
		return 0

	def get_path_index_from_file(self,image_file):
		for idx,images in enumerate(self.image_list):
			if image_file in images["files"]:
				return idx
		return 0

	def get_file_from_page_index(self,page_index):
		target_list = self.get_current_target_list()
		if len(target_list) > 0 and page_index < len(target_list)  and len(target_list[page_index]) > 0:
			return target_list[page_index][0]
		return ""

	def get_image_size(self,file,results,idx):
		#size = util.get_image_size(file)
		size = self.current_reader.get_image_size(file)
		results[idx] = size

	def process_make_multi_pages_list(self,files):
		results1 = []
		results2 = []
		results3 = []
		results4 = []
		current_pages_list1 = []
		current_pages_list2 = []
		current_pages_list3 = []
		current_pages_list4 = []

		threads = []
		sizes_info = [0,0] * len(files)
		for idx,file in enumerate(files):
			tmp_threading = threading.Thread(target=self.get_image_size, args=(file, sizes_info, idx,))
			threads.append(tmp_threading)
			tmp_threading.start()
		for tmp_threading in threads:
			tmp_threading.join()

		for idx,file in enumerate(files):
			img_width, img_height = sizes_info[idx]
			is_2page_already = False
			if img_width / img_height >= self.pages_ratio_require:
				is_2page_already = True
			if is_2page_already:
				if len(current_pages_list1) > 0:
					results1.append(current_pages_list1)
					current_pages_list1 = []
				if len(current_pages_list2) > 0:
					results2.append(current_pages_list2)
					current_pages_list2 = []
				if len(current_pages_list3) > 0:
					results3.append(current_pages_list3)
					current_pages_list3 = []
				if len(current_pages_list4) > 0:
					results4.append(current_pages_list4)
					current_pages_list4 = []
				results1.append([file])
				results2.append([file])
				results3.append([file])
				results4.append([file])
			else:
				current_pages_list1.append(file)
				current_pages_list2.append(file)
				current_pages_list3.append(file)
				current_pages_list4.append(file)
			if len(current_pages_list1) >= 1:
				results1.append(current_pages_list1)
				current_pages_list1 = []
			if len(current_pages_list2) >= 2:
				results2.append(current_pages_list2)
				current_pages_list2 = []
			if len(current_pages_list3) >= 3:
				results3.append(current_pages_list3)
				current_pages_list3 = []
			if len(current_pages_list4) >= 4:
				results4.append(current_pages_list4)
				current_pages_list4 = []

		if len(current_pages_list1) > 0:
			results1.append(current_pages_list1)
		if len(current_pages_list2) > 0:
			results2.append(current_pages_list2)
		if len(current_pages_list3) > 0:
			results3.append(current_pages_list3)
		if len(current_pages_list4) > 0:
			results4.append(current_pages_list4)

		return results1,results2,results3,results4


