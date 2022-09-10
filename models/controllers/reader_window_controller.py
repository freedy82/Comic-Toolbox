from pathlib import Path
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QCursor, QIcon, QPixmap, QColor
from PyQt5.QtWidgets import QFileDialog, QWidget, QSizePolicy, QToolTip, QMenu, QColorDialog
from PyQt5.QtCore import Qt, QEvent, QPoint, QTimer

from models.const import *
from models import util
from models.reader import Reader
from uis import reader_window
from models.controllers.reader.helper import *
from models.controllers.reader.image_process import ReaderImageProcess
from models.controllers.reader.scroll_bar_helper import ReaderScrollBarHelper
from models.controllers.bookmark_window_controller import BookmarkWindowController
from models.controllers.reader_rotate_dialog_controller import ReaderRotateDialogController

class ReaderWindowController(QtWidgets.QMainWindow):
	AUTO_PLAY_TIME_INTERVAL = [1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0]
	PAGE_GAPS = [0,1,2,3,4,5,10,15,20,30,40,50]
	FREE_WIDTH = [25,30,40,50,60,70,75,80,90,95]

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
		self.current_open_file_or_folder = ""
		self.current_image_file = ""
		self.before_full_screen_is_max = False
		self.last_time_move = QPoint(0,0)
		self.pages_ratio_require = float(MY_CONFIG.get("general", "check_is_2_page"))
		self.current_reader = None
		self.current_rotate_dialog = ReaderRotateDialogController(self.app,self,"",self.current_reader)
		self.reader_auto_play_interval = float(MY_CONFIG.get("reader", "auto_play_interval"))*1000
		self.reader_auto_play_time = 0
		self.reader_auto_play_step = 100
		self.current_page_gap = 0
		self.current_free_width = int(MY_CONFIG.get("reader","free_width"))

		self.scroll_flow = ScrollFlow[MY_CONFIG.get("reader", "scroll_flow")]
		self.page_fit = PageFit[MY_CONFIG.get("reader", "page_fit")]
		self.page_mode = PageMode[MY_CONFIG.get("reader", "page_mode")]
		self.page_flow = PageFlow[MY_CONFIG.get("reader", "page_flow")]

		# toolbar item
		self.cbx_folders = QtWidgets.QComboBox()
		self.slider_pages = QtWidgets.QSlider()
		self.btn_auto_play = QtWidgets.QToolButton(self.ui.tb_main)
		self.btn_free_width = QtWidgets.QToolButton(self.ui.tb_main)
		self.btn_num_column = QtWidgets.QToolButton(self.ui.tb_main)
		self.btn_page_gap = QtWidgets.QToolButton(self.ui.tb_main)

		self.bookmark_controller = BookmarkWindowController(self.app,self,self,is_reader=True)
		self.auto_play_timer = QTimer(self)
		self.auto_play_timer.timeout.connect(self.auto_play_timer_timeout)
		self.auto_play_timer.setInterval(self.reader_auto_play_step)

		self.setup_control()

	def setup_control(self):
		self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
		self.ui.menubar.setVisible(False)
		self.ui.lbl_tmp.setVisible(False)
		self.ui.lbl_tmp.setText("")
		self.ui.scrollAreaWidgetContents.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))

		self.update_scroll_flow_button()
		self.update_page_fit_button()
		self.update_page_mode_button()
		self.update_page_flow_button()
		self.force_hidden_auto_play_pgb()

		# add the folder list combobox
		self.ui.tb_main.addSeparator()
		self.cbx_folders.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.cbx_folders.setFixedSize(95,22)
		self.ui.tb_main.addWidget(self.cbx_folders)
		# add spacer
		spacer = QtWidgets.QWidget()
		spacer.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
		spacer.setFixedSize(5,1)
		self.ui.tb_main.addWidget(spacer)
		# add the slider
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

		# insert autoplay icon
		q_play_icon = QtGui.QIcon()
		q_play_icon.addPixmap(QtGui.QPixmap(":/icon/play"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.btn_auto_play.setIcon(q_play_icon)
		self.btn_auto_play.setToolTip(TRSM("Start or Pause Auto Play (k)"))
		self.btn_auto_play.clicked.connect(self.btn_auto_play_clicked)
		self.btn_auto_play.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
		self.ui.tb_main.insertWidget(self.ui.actionScrollFlowLeftRight, self.btn_auto_play)
		self.ui.tb_main.insertSeparator(self.ui.actionScrollFlowLeftRight)
		self.force_update_auto_play_menu()

		# insert free width icon
		q_free_width_icon = QtGui.QIcon()
		q_free_width_icon.addPixmap(QtGui.QPixmap(":/icon/fit-width-num"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.btn_free_width.setIcon(q_free_width_icon)
		self.btn_free_width.setToolTip(TRSM("Fit Width")+"...")
		self.btn_free_width.setPopupMode(QtWidgets.QToolButton.InstantPopup)
		self.ui.tb_main.insertWidget(self.ui.actionPageModeSingle, self.btn_free_width)
		self.ui.tb_main.insertSeparator(self.ui.actionPageModeSingle)
		menu_fit_width = QtWidgets.QMenu()
		#fit_width_menu.addAction(self.ui.actionFitWidth80)
		for tmp_width_percent in self.FREE_WIDTH:
			self.create_submenu_action_of_free_width(menu_fit_width,tmp_width_percent,q_free_width_icon)
		self.btn_free_width.setMenu(menu_fit_width)

		# insert num column page
		q_num_column_icon = QtGui.QIcon()
		q_num_column_icon.addPixmap(QtGui.QPixmap(":/icon/num-column"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.btn_num_column.setIcon(q_num_column_icon)
		self.btn_num_column.setToolTip(TRSM("Multi page")+"...")
		self.btn_num_column.setPopupMode(QtWidgets.QToolButton.InstantPopup)
		self.ui.tb_main.insertWidget(self.ui.actionPageFlowRightToLeft, self.btn_num_column)
		self.ui.tb_main.insertSeparator(self.ui.actionPageFlowRightToLeft)
		menu_num_column = QtWidgets.QMenu()
		menu_num_column.addAction(self.ui.actionPageModeTriple)
		menu_num_column.addAction(self.ui.actionPageModeQuadruple)
		self.btn_num_column.setMenu(menu_num_column)

		# insert page gap
		q_page_gap_icon = QtGui.QIcon()
		q_page_gap_icon.addPixmap(QtGui.QPixmap(":/icon/gap"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.btn_page_gap.setIcon(q_page_gap_icon)
		self.btn_page_gap.setToolTip(TRSM("Page gap")+"...")
		self.btn_page_gap.setPopupMode(QtWidgets.QToolButton.InstantPopup)
		self.ui.tb_main.insertWidget(self.ui.actionRotateAllImage, self.btn_page_gap)
		self.ui.tb_main.insertSeparator(self.ui.actionRotateAllImage)
		menu_page_gap = QtWidgets.QMenu()
		for tmp_gap in self.PAGE_GAPS:
			self.create_submenu_action_of_page_gap(menu_page_gap,tmp_gap,q_page_gap_icon)
		self.btn_page_gap.setMenu(menu_page_gap)

		# GUI
		self.retranslateUi()

		# action
		self.ui.actionFileExit.triggered.connect(self.on_file_exit)
		self.ui.actionFileOpenFolder.triggered.connect(self.on_file_open_folder)
		self.ui.actionFileOpenFile.triggered.connect(self.on_file_open_file)
		self.ui.actionAutoPlay.triggered.connect(self.btn_auto_play_clicked)
		self.ui.actionScrollFlowLeftRight.triggered.connect(lambda: self.change_scroll_flow(ScrollFlow.LEFT_RIGHT))
		self.ui.actionScrollFlowUpDown.triggered.connect(lambda: self.change_scroll_flow(ScrollFlow.UP_DOWN))
		self.ui.actionFitHeight.triggered.connect(lambda: self.change_page_fit(PageFit.HEIGHT))
		self.ui.actionFitWidth.triggered.connect(lambda: self.change_page_fit(PageFit.WIDTH))
		self.ui.actionFitBoth.triggered.connect(lambda: self.change_page_fit(PageFit.BOTH))
		self.ui.actionPageModeSingle.triggered.connect(lambda: self.change_page_mode(PageMode.SINGLE))
		self.ui.actionPageModeDouble.triggered.connect(lambda: self.change_page_mode(PageMode.DOUBLE))
		self.ui.actionPageModeTriple.triggered.connect(lambda: self.change_page_mode(PageMode.TRIPLE))
		self.ui.actionPageModeQuadruple.triggered.connect(lambda: self.change_page_mode(PageMode.QUADRUPLE))
		self.ui.actionPageFlowLeftToRight.triggered.connect(lambda: self.change_page_flow(PageFlow.LEFT_TO_RIGHT))
		self.ui.actionPageFlowRightToLeft.triggered.connect(lambda: self.change_page_flow(PageFlow.RIGHT_TO_LEFT))
		self.ui.actionRotateAllImage.triggered.connect(lambda: self.show_rotate_dialog(""))
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

	def setup_timer(self):
		q_icon = QtGui.QIcon()
		q_icon.addPixmap(QtGui.QPixmap(":/icon/play"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.ui.actionAutoPlay.setIcon(q_icon)
		self.reader_auto_play_interval = float(MY_CONFIG.get("reader", "auto_play_interval"))*1000

	def update_auto_play_pgb(self):
		if MY_CONFIG.get("reader", "auto_play_pgb") == "1":
			need_display = True
		else:
			need_display = False
		if not self.auto_play_timer.isActive():
			need_display = False
		if self.ui.pgb_auto_play.isVisible() != need_display:
			self.ui.pgb_auto_play.setVisible(need_display)
			self.ui.verticalLayout.activate()
			self.update_images_size()

	def force_hidden_auto_play_pgb(self):
		if self.ui.pgb_auto_play.isVisible():
			self.ui.pgb_auto_play.setVisible(False)
			self.ui.verticalLayout.activate()
			self.update_images_size()

	def retranslateUi(self):
		self.ui.retranslateUi(self)
		self.bookmark_controller.retranslateUi()
		# start toolbar icon
		self.btn_auto_play.setToolTip(TRSM("Start or Pause Auto Play (k)"))
		self.force_update_auto_play_menu()
		self.btn_free_width.setToolTip(TRSM("Fit Width")+"...")
		self.btn_num_column.setToolTip(TRSM("Multi page")+"...")
		self.btn_page_gap.setToolTip(TRSM("Page gap")+"...")
		for tmp_index, tmp_action in enumerate(self.btn_free_width.menu().actions()):
			tmp_action.setText(TRSM("Fit Width") + ": " + str(self.FREE_WIDTH[tmp_index]) + "%")
		for tmp_index, tmp_action in enumerate(self.btn_page_gap.menu().actions()):
			tmp_action.setText(TRSM("Page gap") + ": " + str(self.PAGE_GAPS[tmp_index]))
		pass

	# override
	def show(self):
		super().show()
		self.update_layout()
		self.setup_timer()
		self.force_hidden_auto_play_pgb()
		self.force_update_auto_play_menu()
		#self.get_image_list_from_file_or_folder("F:/comics/全知讀者視角")
		#self.get_image_list_from_file_or_folder("F:/comics/全职法师")
		#self.get_image_list_from_file_or_folder("F:/comics/烙印战士_good")
		#self.get_image_list_from_file_or_folder("F:/comics/全职法师/全职法师-chapter-00001-00025.cbz")
		#self.get_image_list_from_file_or_folder("F:/comics/全职法师/全职法师-chapter-00001-00025.zip")
		#self.get_image_list_from_file_or_folder("F:/comics/全职法师/全职法师-chapter-00001.zip")
		#self.get_image_list_from_file_or_folder("F:/comics/測試")
		#self.get_image_list_from_file_or_folder("F:/comics/全职法师/全职法师-chapter-00001-00002.pdf")
		#self.get_image_list_from_file_or_folder("F:/comics/火影忍者博人傳2/火影忍者博人傳-chapter-00001.pdf")
		#self.get_image_list_from_file_or_folder("F:/comics/烙印战士_good/book-01")

	def resizeEvent(self, event):
		self.update_images_size()

	def keyPressEvent(self, e):
		if e.key() == Qt.Key_F11 or e.key() == Qt.Key_F:
			self.btn_full_screen_clicked()
		if e.key() == Qt.Key_K:
			self.btn_auto_play_clicked()
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
			self.ui.tb_main.setVisible(False)
			if self.isMaximized():
				self.before_full_screen_is_max = True
			else:
				self.before_full_screen_is_max = False
			self.showFullScreen()
		else:
			self.ui.tb_main.setVisible(True)
			if self.before_full_screen_is_max:
				self.showMaximized()
			else:
				self.showNormal()

	def btn_add_bookmark_clicked(self):
		if self.current_open_file_or_folder != "" and self.current_image_file != "":
			self.bookmark_controller.add_book_mark(self.current_image_file, self.current_open_file_or_folder)
		else:
			util.msg_box(TRSM("Please open a folder or file"),self)

	def btn_bookmark_list_clicked(self):
		self.bookmark_controller.show()
		pass

	def on_file_exit(self):
		self.close()

	def on_file_open_folder(self):
		old_folder_path = MY_CONFIG.get("general", "download_folder")
		if self.current_open_file_or_folder != "":
			if os.path.isfile(self.current_open_file_or_folder):
				old_folder_path = Path(self.current_open_file_or_folder).parent.resolve().as_posix()
			else:
				old_folder_path = self.current_open_file_or_folder

		folder_path = QFileDialog.getExistingDirectory(self,TRSM("Open folder"), old_folder_path)
		if folder_path != "":
			#print("open folder",folder_path)
			self.get_image_list_from_file_or_folder(folder_path)

	def on_file_open_file(self):
		old_folder_path = MY_CONFIG.get("general", "download_folder")
		filter_string = Reader.get_all_supported_filter_string()

		if self.current_open_file_or_folder != "":
			old_folder_path = self.current_open_file_or_folder

		file_path = QFileDialog.getOpenFileName(self,TRSM("Open File"), old_folder_path, filter_string)
		if len(file_path) >= 2 and file_path[0] != "":
			#print(file_path[0])
			self.get_image_list_from_file_or_folder(file_path[0])

	def on_toggle_auto_play_pgb(self):
		if MY_CONFIG.get("reader", "auto_play_pgb") == "1":
			MY_CONFIG.set("reader","auto_play_pgb","0")
		else:
			MY_CONFIG.set("reader","auto_play_pgb","1")
		self.update_auto_play_pgb()
		self.force_update_auto_play_menu()

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

	def btn_auto_play_clicked(self):
		q_icon = QtGui.QIcon()
		if self.auto_play_timer.isActive():
			self.auto_play_timer.stop()
			self.reader_auto_play_time = 0
			self.ui.pgb_auto_play.setValue(0)
			self.force_hidden_auto_play_pgb()
			q_icon.addPixmap(QtGui.QPixmap(":/icon/play"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		else:
			self.reader_auto_play_time = 0
			self.ui.pgb_auto_play.setValue(0)
			self.auto_play_timer.start()
			self.update_auto_play_pgb()
			q_icon.addPixmap(QtGui.QPixmap(":/icon/pause"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.ui.actionAutoPlay.setIcon(q_icon)
		self.btn_auto_play.setIcon(q_icon)
		self.force_update_auto_play_menu()

	def auto_play_timer_reset_time(self):
		self.reader_auto_play_time = 0

	def auto_play_timer_timeout(self):
		#print("auto_play next page")
		self.reader_auto_play_time += self.reader_auto_play_step
		if self.reader_auto_play_time > self.reader_auto_play_interval:
			self.reader_auto_play_time = 0
			self.go_next_page()
		self.ui.pgb_auto_play.setValue(int(self.reader_auto_play_time/self.reader_auto_play_interval*100))

	def force_stop_auto_play_timer(self):
		if self.auto_play_timer.isActive():
			self.btn_auto_play_clicked()

	def start_auto_play_with_time(self,time_interval):
		#print("start with:",time_interval)
		if self.auto_play_timer.isActive():
			self.force_stop_auto_play_timer()
		self.reader_auto_play_interval = time_interval * 1000
		self.btn_auto_play_clicked()

	def scroll_area_scroll_bar_value_changed(self):
		if self.scroll_flow == ScrollFlow.UP_DOWN:
			x = self.ui.scrollArea.horizontalScrollBar().value()
			y = self.ui.scrollArea.verticalScrollBar().value()
			w = self.ui.scrollArea.frameGeometry().width()
			h = self.ui.scrollArea.frameGeometry().height()
			current_visible_frame = QtCore.QRect(x,y,w,h)
			#print(f"x:{x},y:{y},w:{w},y:{h}, frame:{current_visible_frame}")
			found_row = ReaderScrollBarHelper.found_row_of_scroll_area(current_visible_frame, self.ui.layout_main)

			# change current page index
			self.current_page_index = found_row
			self.current_image_file = self.get_file_from_page_index(found_row)
			#print(f"scroll bar value changed update slider {found_row}")
			self.update_slider()

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
		if self.page_fit == PageFit.HEIGHT:
			self.ui.actionFitHeight.setChecked(True)
		elif self.page_fit == PageFit.WIDTH:
			self.ui.actionFitWidth.setChecked(True)
		elif self.page_fit == PageFit.BOTH:
			self.ui.actionFitBoth.setChecked(True)

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

	def change_page_fit(self,new_page_fit, new_free_width=100):
		if self.page_fit != new_page_fit or (new_page_fit == PageFit.WIDTH_FREE and new_free_width != self.current_free_width):
			self.page_fit = new_page_fit
			self.current_free_width = new_free_width
			self.update_page_fit_button()
			self.update_images_size()
			if self.scroll_flow == ScrollFlow.UP_DOWN:
				self.go_page_index(self.current_page_index)
			MY_CONFIG.set("reader", "page_fit", str(self.page_fit.name))
			MY_CONFIG.set("reader", "free_width", str(new_free_width))
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
		self.force_stop_auto_play_timer()
		self.image_list = []
		self.current_single_image_list = []
		self.current_double_image_list = []
		self.current_triple_image_list = []
		self.current_quadruple_image_list = []
		self.current_path_index = 0
		self.current_page_index = 0
		self.current_open_file_or_folder = ""
		self.current_image_file = ""
		self.current_reader = None
		self.update_images()
		self.update_slider()
		self.update_folder_combo_box_list()
		pass

	def load_bookmark(self,folder,file):
		is_same_folder = False
		is_same_path_index = False
		if folder != self.current_open_file_or_folder:
			self.get_image_list_from_file_or_folder(folder)
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
		if self.scroll_flow != ScrollFlow.UP_DOWN or not is_same_path_index:
			self.update_images()
		self.current_image_file = file

		if self.scroll_flow == ScrollFlow.UP_DOWN:
			# delay 0.3 sec to load page
			QTimer.singleShot(300,lambda: self.delay_load_book_mark_update_page(self.current_page_index))

	def delay_load_book_mark_update_page(self,page_index):
		self.current_page_index = page_index
		self.update_slider()
		self.go_page_index(self.current_page_index)

	def get_image_list_from_file_or_folder(self, file_or_folder_path):
		self.cursor_busy()
		if os.path.isdir(file_or_folder_path):
			self.current_reader = Reader.init_folder_reader(file_or_folder_path)
		else:
			self.current_reader = Reader.init_reader_by_file(file_or_folder_path)
		self.image_list = self.current_reader.get_file_list()
		self.cursor_un_busy()
		if len(self.image_list) > 0:
			self.current_open_file_or_folder = file_or_folder_path
			self.current_path_index = 0
			self.update_folder_combo_box_list()
			self.start_load_current_path_list()
		else:
			if os.path.isdir(file_or_folder_path):
				util.msg_box(TRSM("Can not found any image in folder"),self)
			else:
				util.msg_box(TRSM("Can not found any image in file"), self)

	def start_load_current_path_list(self):
		self.cursor_busy()
		self.update_current_image_list_from_path_index()
		self.current_page_index = 0
		self.update_images()
		self.go_page_start()
		self.cursor_un_busy()

	def update_current_image_list_from_path_index(self):
		list1,list2,list3,list4 = self.process_make_multi_pages_list(self.image_list[self.current_path_index]["files"])
		self.current_single_image_list = list1
		self.current_double_image_list = list2
		self.current_triple_image_list = list3
		self.current_quadruple_image_list = list4

	def update_folder_combo_box_list(self):
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

	def clean_all_images(self):
		for i in reversed(range(self.ui.layout_main.count())):
			tmp_widget = self.ui.layout_main.itemAt(i).widget()
			if type(tmp_widget) is QtWidgets.QLabel:
				self.ui.layout_main.removeItem(self.ui.layout_main.itemAt(i))
				tmp_widget.setParent(None)

	def update_images(self):
		#print("update images")
		self.clean_all_images()

		target_image_list = []
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			tmp_target_list = self.get_current_target_list()
			if self.current_page_index < len(tmp_target_list):
				target_image_list = [tmp_target_list[self.current_page_index]]
		elif self.scroll_flow == ScrollFlow.UP_DOWN:
			target_image_list = self.get_current_target_list()

		self.cursor_busy()
		self.current_image_file = ReaderImageProcess.update_image_at_scroll_area(
			target_image_list,self.current_reader,self.page_mode,self.page_flow,
			self.ui.scrollAreaWidgetContents,self.ui.layout_main,self.pages_ratio_require,self)
		#print("finish add widgets, used %0.3fs" % (time.time()-start_time))
		self.cursor_un_busy()
		self.update_images_size()
		self.update_slider()

	def update_single_image(self,file):
		ReaderImageProcess.update_single_image(file,self.page_mode,self.ui.layout_main,self.current_reader)
		self.update_images_size()

	def update_images_size(self):
		#print("update images size")
		area_size = self.ui.scrollArea.size()
		total_width, total_height = ReaderImageProcess.update_image_size_inner(
			area_size,self.page_mode,self.page_fit,self.scroll_flow,self.pages_ratio_require,
			self.ui.layout_main,self.ui.scrollArea,self.current_page_gap,self.current_free_width)

		#fix the scroll bar update delay
		if total_height-area_size.height() > 0:
			self.ui.scrollArea.verticalScrollBar().setMaximum(total_height-area_size.height())
		else:
			self.ui.scrollArea.verticalScrollBar().setMaximum(1)
		if total_width-area_size.width() > 0:
			self.ui.scrollArea.horizontalScrollBar().setMaximum(total_width-area_size.width())
		else:
			self.ui.scrollArea.horizontalScrollBar().setMaximum(1)

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
			ReaderScrollBarHelper.move_scroll_area_by_row(self.current_page_index, self.ui.layout_main, self.ui.scrollArea)
		self.auto_play_timer_reset_time()

	def go_prev_page(self):
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			if self.current_page_index > 0:
				self.current_page_index -= 1
				self.update_images()
				self.go_page_end()
			elif self.current_path_index > 0:
				self.go_prev_chapter()
		elif self.scroll_flow == ScrollFlow.UP_DOWN:
			if self.ui.scrollArea.verticalScrollBar().value() != 0:
				if self.current_page_index > 0:
					self.go_page_index(self.current_page_index-1)
				else:
					self.ui.scrollArea.verticalScrollBar().setValue(0)
			else:
				if self.current_path_index > 0:
					self.go_prev_chapter()
		self.auto_play_timer_reset_time()

	def go_prev_chapter(self):
		if self.current_path_index > 0:
			self.current_path_index -= 1
			self.update_folder_combo_box_index()
			self.update_current_image_list_from_path_index()
			current_target_list = self.get_current_target_list()
			self.current_page_index = len(current_target_list) - 1
			#print(f"go_prev__chapter self.current_page_index:{self.current_page_index}")
			self.update_images()
			self.go_page_end()
			self.auto_play_timer_reset_time()

	def go_next_page(self):
		if self.scroll_flow == ScrollFlow.LEFT_RIGHT:
			current_target_list = self.get_current_target_list()
			if self.current_page_index < len(current_target_list) - 1:
				self.current_page_index += 1
				self.update_images()
				self.go_page_start()
			elif self.current_path_index < len(self.image_list) - 1:
				self.go_next_chapter()
			else:
				self.force_stop_auto_play_timer()
		elif self.scroll_flow == ScrollFlow.UP_DOWN:
			if self.ui.scrollArea.verticalScrollBar().value() != self.ui.scrollArea.verticalScrollBar().maximum():
				current_target_list = self.get_current_target_list()
				if self.current_page_index < len(current_target_list) - 1:
					self.go_page_index(self.current_page_index+1)
				else:
					self.ui.scrollArea.verticalScrollBar().setValue(self.ui.scrollArea.verticalScrollBar().maximum())
			else:
				if self.current_path_index < len(self.image_list) - 1:
					self.go_next_chapter()
				else:
					self.force_stop_auto_play_timer()
		self.auto_play_timer_reset_time()

	def go_next_chapter(self):
		if self.current_path_index < len(self.image_list) - 1:
			self.current_path_index += 1
			self.update_folder_combo_box_index()
			self.update_current_image_list_from_path_index()
			self.current_page_index = 0
			self.update_images()
			self.go_page_start()
			self.auto_play_timer_reset_time()
		else:
			self.force_stop_auto_play_timer()

	def go_page_start(self):
		#print("go page start")
		self.ui.scrollArea.verticalScrollBar().setValue(0)
		if self.page_flow == PageFlow.LEFT_TO_RIGHT:
			self.ui.scrollArea.horizontalScrollBar().setValue(0)
		else:
			self.ui.scrollArea.horizontalScrollBar().setValue(self.ui.scrollArea.horizontalScrollBar().maximum())
		self.auto_play_timer_reset_time()

	def go_page_end(self):
		#print("go page end")
		self.ui.scrollArea.verticalScrollBar().setValue(self.ui.scrollArea.verticalScrollBar().maximum())
		if self.page_flow == PageFlow.LEFT_TO_RIGHT:
			self.ui.scrollArea.horizontalScrollBar().setValue(self.ui.scrollArea.horizontalScrollBar().maximum())
		else:
			self.ui.scrollArea.horizontalScrollBar().setValue(0)
		self.auto_play_timer_reset_time()

	def update_layout(self):
		self.update_background()
		self.set_reader_page_gap(int(MY_CONFIG.get("reader", "page_gap")))

	def update_background(self):
		reader_background = MY_CONFIG.get("reader", "background")
		self.ui.scrollAreaWidgetContents.setStyleSheet("background-color:"+reader_background+";")

	def set_reader_page_gap(self,gap):
		self.current_page_gap = gap
		self.ui.layout_main.setHorizontalSpacing(self.current_page_gap)
		#self.ui.layout_main.setVerticalSpacing(self.current_page_gap)
		MY_CONFIG.set("reader", "page_gap",str(self.current_page_gap))
		MY_CONFIG.save()
		self.update_images_size()

	# event filter
	def eventFilter(self, source, event:QEvent):
		if source == self.ui.scrollArea:
			#self.handle_scroll_area_event(event)
			if event.type() == QEvent.MouseButtonPress and event.button() == QtCore.Qt.RightButton:
				self.handle_right_click_from_image(source,event)
			else:
				self.last_time_move = ReaderScrollBarHelper.handle_scroll_area_event(
					self.last_time_move, event, self.page_flow, self.ui.scrollArea, self.go_prev_page,
					self.go_next_page)
		if type(source) is QtWidgets.QLabel and event.type() == QEvent.MouseButtonPress and event.button() == QtCore.Qt.RightButton:
			self.handle_right_click_from_image(source,event)
			# prevent to fire the scroll area event
			return True
		return QWidget.eventFilter(self, source, event)

	def handle_right_click_from_image(self,source,event:QEvent):
		if type(source) is QtWidgets.QLabel:
			file = source.windowFilePath()
		else:
			file = ""

		menu_popup = QMenu()
		# rotate
		if file != "":
			icon_rotate_right = QIcon()
			icon_rotate_right.addPixmap(QPixmap(":/icon/rotate-right"), QIcon.Normal, QIcon.Off)
			menu_rotate = menu_popup.addMenu(TRSM("Rotate"))
			menu_rotate.setIcon(icon_rotate_right)
			action_rotate_this = menu_rotate.addAction(TRSM("Rotate this image"))
			action_rotate_this.setIcon(icon_rotate_right)
			action_rotate_this.triggered.connect(lambda: self.show_rotate_dialog(file))
			menu_rotate.addAction(self.ui.actionRotateAllImage)
		else:
			menu_popup.addAction(self.ui.actionRotateAllImage)

		# autoplay
		icon_autoplay = QIcon()
		icon_autoplay.addPixmap(QPixmap(":/icon/autoplay"), QIcon.Normal, QIcon.Off)
		menu_autoplay = menu_popup.addMenu(TRSM("Autoplay"))
		menu_autoplay.setIcon(icon_autoplay)
		# sub item of autoplay
		self.recreate_auto_play_menu(menu_autoplay)

		icon_gap = QIcon()
		icon_gap.addPixmap(QPixmap(":/icon/gap"), QIcon.Normal, QIcon.Off)
		menu_page_gap = menu_popup.addMenu(TRSM("Page gap"))
		menu_page_gap.setIcon(icon_gap)
		menu_page_gap.addActions(self.btn_page_gap.menu().actions())

		# background color
		bg_color = MY_CONFIG.get("reader","background")
		action_change_background = menu_popup.addAction(TRSM("Background color"))
		icon_background = QIcon()
		pixmap_background = QPixmap(90,90)
		pixmap_background.fill(QColor(bg_color))
		icon_background.addPixmap(pixmap_background)
		action_change_background.setIcon(icon_background)
		action_change_background.triggered.connect(lambda: self.show_change_background_dialog(bg_color))

		# other
		menu_popup.addAction(self.ui.actionFullscreen)
		menu_popup.addSeparator()
		menu_popup.addAction(self.ui.actionFileExit)

		menu_popup.popup(QCursor.pos())
		QtGui.XSIMenu = menu_popup

	def force_update_auto_play_menu(self):
		# need delay if object disconnect when click
		QTimer.singleShot(200, self.real_force_update_auto_play_menu)

	def real_force_update_auto_play_menu(self):
		menu_autoplay = QtWidgets.QMenu()
		self.recreate_auto_play_menu(menu_autoplay)
		self.btn_auto_play.setMenu(menu_autoplay)

	def recreate_auto_play_menu(self,menu_parent):
		q_play_icon = QtGui.QIcon()
		q_play_icon.addPixmap(QtGui.QPixmap(":/icon/play"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		q_pause_icon = QtGui.QIcon()
		q_pause_icon.addPixmap(QtGui.QPixmap(":/icon/pause"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

		tmp_auto_play_interval = float(MY_CONFIG.get("reader", "auto_play_interval"))
		if self.auto_play_timer.isActive():
			action_pause_tmp = menu_parent.addAction(TRSM("Stop autoplay"))
			action_pause_tmp.setIcon(q_pause_icon)
			action_pause_tmp.triggered.connect(lambda: self.btn_auto_play_clicked())
		else:
			self.create_submenu_action_of_auto_play_time(menu_parent,tmp_auto_play_interval,q_play_icon)
		menu_parent.addSeparator()
		icon_autoplay_pgb = QIcon()
		if MY_CONFIG.get("reader", "auto_play_pgb") == "1":
			action_toggle_auto_play_pgb = menu_parent.addAction(TRSM("Hidden autoplay progress bar"))
			icon_autoplay_pgb.addPixmap(QPixmap(":/icon/hide"), QIcon.Normal, QIcon.Off)
		else:
			action_toggle_auto_play_pgb = menu_parent.addAction(TRSM("Show autoplay progress bar"))
			icon_autoplay_pgb.addPixmap(QPixmap(":/icon/show"), QIcon.Normal, QIcon.Off)
		action_toggle_auto_play_pgb.setIcon(icon_autoplay_pgb)
		action_toggle_auto_play_pgb.triggered.connect(self.on_toggle_auto_play_pgb)
		menu_parent.addSeparator()
		#start play interval list
		for tmp_time in self.AUTO_PLAY_TIME_INTERVAL:
			if tmp_time == tmp_auto_play_interval:
				continue
			self.create_submenu_action_of_auto_play_time(menu_parent,tmp_time,q_play_icon)

	def create_submenu_action_of_auto_play_time(self,menu_parent,time_interval,icon_play):
		action_auto_play_tmp = menu_parent.addAction(
			TRSM("Start autoplay") + " (" + str(time_interval) + "s)")
		action_auto_play_tmp.setIcon(icon_play)
		action_auto_play_tmp.triggered.connect(lambda: self.start_auto_play_with_time(time_interval))
		return action_auto_play_tmp

	def create_submenu_action_of_page_gap(self,menu_parent,gap,icon_gap):
		action_page_gap_tmp = menu_parent.addAction(
			TRSM("Page gap") + ": " + str(gap))
		action_page_gap_tmp.setIcon(icon_gap)
		action_page_gap_tmp.triggered.connect(lambda: self.set_reader_page_gap(gap))
		return action_page_gap_tmp

	def create_submenu_action_of_free_width(self,menu_parent,free_width,icon_free_width):
		action_free_width_tmp = menu_parent.addAction(
			TRSM("Fit Width") + ": " + str(free_width) + "%")
		action_free_width_tmp.setIcon(icon_free_width)
		action_free_width_tmp.setCheckable(True)
		action_free_width_tmp.triggered.connect(lambda: self.change_page_fit(PageFit.WIDTH_FREE, free_width))
		return action_free_width_tmp

	def show_rotate_dialog(self,file=""):
		if self.current_reader is not None:
			self.current_rotate_dialog = ReaderRotateDialogController(self.app,self,file,self.current_reader)
			self.current_rotate_dialog.finished.connect(self.rotate_dialog_finished)
			self.current_rotate_dialog.show()
		else:
			util.msg_box(TRSM("Please open a folder or file"),self)

	def show_change_background_dialog(self,color):
		color = QColorDialog.getColor(QColor(color),self,TRSM("Pick a color"))
		if color.isValid():
			color_name = color.name()
			MY_CONFIG.set("reader","background",color_name)
			MY_CONFIG.save()
			self.update_background()

	def rotate_dialog_finished(self,file,rotate:PageRotate,mode:PageRotateMode):
		self.cursor_busy()
		self.current_reader.rotate_file(file,rotate,mode)
		self.cursor_un_busy()
		old_current_image_file = self.current_image_file
		self.start_load_current_path_list()
		#self.update_images()
		old_page_index = self.get_page_index_from_file(old_current_image_file)
		self.go_page_index(old_page_index)

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

	def process_make_multi_pages_list(self,files):
		return ReaderImageProcess.process_make_multi_pages_list(files,self.pages_ratio_require,self.current_reader)
