import threading

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QScrollArea

from models.reader import Reader
from models.controllers.reader.helper import *

class ReaderImageProcess:
	def __init__(self):
		super(ReaderImageProcess, self).__init__()
		self.current_reader = Reader()

	def set_reader(self,reader):
		self.current_reader = reader

	@staticmethod
	def get_image_size(file,results,idx,reader:Reader):
		size = reader.get_image_size(file)
		results[idx] = size

	@staticmethod
	def process_make_multi_pages_list(files,pages_ratio_require,reader:Reader):
		results1 = []
		results2 = []
		results3 = []
		results4 = []
		current_pages_list1 = []
		current_pages_list2 = []
		current_pages_list3 = []
		current_pages_list4 = []
		# 1-2 page was not need handle
		current_pages_in_list3 = 0
		current_pages_in_list4 = 0

		threads = []
		sizes_info = [0,0] * len(files)
		for idx,file in enumerate(files):
			tmp_threading = threading.Thread(target=ReaderImageProcess.get_image_size, args=(file, sizes_info, idx, reader))
			threads.append(tmp_threading)
			tmp_threading.start()
		for tmp_threading in threads:
			tmp_threading.join()

		for idx,file in enumerate(files):
			img_width, img_height = sizes_info[idx]
			is_2page_already = False
			#print(f"{file} = {img_width}-{img_height}",flush=True)
			if img_width / img_height >= pages_ratio_require:
				is_2page_already = True
			if is_2page_already:
				if len(current_pages_list1) > 0:
					results1.append(current_pages_list1)
					current_pages_list1 = []
				if len(current_pages_list2) > 0:
					results2.append(current_pages_list2)
					current_pages_list2 = []
				if len(current_pages_list3) > 0 and current_pages_in_list3 > 1:
					results3.append(current_pages_list3)
					current_pages_list3 = []
					current_pages_in_list3 = 0
				if len(current_pages_list4) > 0 and current_pages_in_list4 > 2:
					results4.append(current_pages_list4)
					current_pages_list4 = []
					current_pages_in_list4 = 0
				results1.append([file])
				results2.append([file])
				#results3.append([file])
				#results4.append([file])
				current_pages_list3.append(file)
				current_pages_list4.append(file)
				current_pages_in_list3 += 2
				current_pages_in_list4 += 2
			else:
				current_pages_list1.append(file)
				current_pages_list2.append(file)
				current_pages_list3.append(file)
				current_pages_list4.append(file)
				current_pages_in_list3 += 1
				current_pages_in_list4 += 1

			if len(current_pages_list1) >= 1:
				results1.append(current_pages_list1)
				current_pages_list1 = []
			if len(current_pages_list2) >= 2:
				results2.append(current_pages_list2)
				current_pages_list2 = []
			if len(current_pages_list3) >= 3 or current_pages_in_list3 >= 3:
				results3.append(current_pages_list3)
				current_pages_list3 = []
				current_pages_in_list3 = 0
			if len(current_pages_list4) >= 4 or current_pages_in_list4 >= 4:
				results4.append(current_pages_list4)
				current_pages_list4 = []
				current_pages_in_list4 = 0

		if len(current_pages_list1) > 0:
			results1.append(current_pages_list1)
		if len(current_pages_list2) > 0:
			results2.append(current_pages_list2)
		if len(current_pages_list3) > 0:
			results3.append(current_pages_list3)
		if len(current_pages_list4) > 0:
			results4.append(current_pages_list4)

		#print(results3)
		return results1,results2,results3,results4

	@staticmethod
	def get_fit_image_size(area_size,image_size,v_scrollbar_size,h_scrollbar_size,page_fit:PageFit,scroll_flow:ScrollFlow,free_width):
		new_width = image_size.width()
		new_height = image_size.height()
		width_rate = height_rate = 1
		if page_fit == PageFit.BOTH:
			width_rate = image_size.width()/area_size.width()
			height_rate = image_size.height()/area_size.height()
			if scroll_flow == ScrollFlow.UP_DOWN:
				new_width -= v_scrollbar_size
				new_height = new_width / image_size.width() * image_size.height()
		if page_fit == PageFit.HEIGHT or (page_fit == PageFit.BOTH and width_rate <= height_rate):
			new_height = area_size.height()
			new_width = new_height/image_size.height() * image_size.width()
			# fallback to check scroll bar will appear
			if new_width > area_size.width():
				new_height -= h_scrollbar_size
				new_width = new_height/image_size.height() * image_size.width()
		elif page_fit == PageFit.WIDTH or page_fit == PageFit.WIDTH_FREE or (page_fit == PageFit.BOTH and width_rate >= height_rate):
			if page_fit == PageFit.WIDTH_FREE:
				new_width = area_size.width()*free_width/100
			else:
				new_width = area_size.width()
			new_height = new_width/image_size.width() * image_size.height()
			# fallback to check scroll bar will appear
			if new_height > area_size.height() or scroll_flow == ScrollFlow.UP_DOWN:
				new_width -= v_scrollbar_size
				new_height = new_width/image_size.width() * image_size.height()

		return QSize(new_width,new_height)

	@staticmethod
	def update_image_at_scroll_area(
			target_image_list,current_reader:Reader,page_mode:PageMode,page_flow:PageFlow,
			scroll_area_widget_contents:QWidget,layout_main:QGridLayout,pages_ratio_require:float,parent_controller):
		tmp_current_image_file = ""
		for rowIdx, row in enumerate(target_image_list):
			if tmp_current_image_file == "":
				tmp_current_image_file = row[0]
			col_count = len(row)
			col_add_count = 0
			for colIdx, file in enumerate(row):
				q_pixmap = current_reader.get_q_pixmap_from_file(file)
				lbl_tmp = QLabel(scroll_area_widget_contents)
				lbl_tmp.setLineWidth(0)
				lbl_tmp.setText("")
				lbl_tmp.setScaledContents(True)
				lbl_tmp.setPixmap(q_pixmap)
				lbl_tmp.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
				lbl_tmp.setWindowFilePath(file)
				lbl_tmp.installEventFilter(parent_controller)
				image_size = q_pixmap.size()
				is_2_pages_already = False
				if image_size.width() / image_size.height() > pages_ratio_require and page_mode.value > 1:
					is_2_pages_already = True
					if col_count == 1 and page_mode == PageMode.QUADRUPLE:
						layout_main.addWidget(lbl_tmp, rowIdx, 1, 1, 2)
					elif col_count == 1:
						layout_main.addWidget(lbl_tmp, rowIdx, 0, 1, page_mode.value)
					elif page_flow == PageFlow.RIGHT_TO_LEFT:
						layout_main.addWidget(lbl_tmp, rowIdx, page_mode.value-col_add_count-2, 1, 2)
					else:
						layout_main.addWidget(lbl_tmp, rowIdx, col_add_count, 1, 2)
					col_add_count += 2
				# if col_count == 1 and page_mode == PageMode.DOUBLE:
				# 	layout_main.addWidget(lbl_tmp, rowIdx, colIdx, 1, 2)
				# elif col_count == 1 and page_mode == PageMode.TRIPLE:
				# 	layout_main.addWidget(lbl_tmp, rowIdx, colIdx, 1, 3)
				# elif col_count == 1 and page_mode == PageMode.QUADRUPLE:
				# 	layout_main.addWidget(lbl_tmp, rowIdx, colIdx, 1, 4)
				else:
					#if col_count == 1 and page_mode.value > 1:
					#	layout_main.addWidget(lbl_tmp, rowIdx, 0, 1, page_mode.value)
					if page_flow == PageFlow.RIGHT_TO_LEFT:
						layout_main.addWidget(lbl_tmp,rowIdx, page_mode.value - col_add_count - 1, 1, 1)
					else:
						layout_main.addWidget(lbl_tmp,rowIdx,col_add_count, 1, 1)
					col_add_count += 1
				if page_mode == PageMode.DOUBLE and col_count > 1:
					if is_2_pages_already:
						layout_main.setAlignment(lbl_tmp, Qt.AlignHCenter | Qt.AlignCenter)
					elif page_flow == PageFlow.LEFT_TO_RIGHT:
						if col_add_count == 1:
							layout_main.setAlignment(lbl_tmp, Qt.AlignHCenter | Qt.AlignRight)
						else:
							layout_main.setAlignment(lbl_tmp, Qt.AlignHCenter | Qt.AlignLeft)
					elif page_flow == PageFlow.RIGHT_TO_LEFT:
						if col_add_count == 1:
							layout_main.setAlignment(lbl_tmp, Qt.AlignHCenter | Qt.AlignLeft)
						else:
							layout_main.setAlignment(lbl_tmp, Qt.AlignHCenter | Qt.AlignRight)
				else:
					layout_main.setAlignment(lbl_tmp, Qt.AlignHCenter | Qt.AlignCenter)
		return tmp_current_image_file

	@staticmethod
	def update_image_size_inner(
			area_size,page_mode:PageMode,page_fit:PageFit,scroll_flow:ScrollFlow,pages_ratio_require:float,
			layout_main:QGridLayout,scroll_area:QScrollArea,page_gap,free_width):
		rows = layout_main.rowCount()
		#cols = self.ui.layout_main.columnCount()
		cols = page_mode.value
		#print(f"rows: {rows}, cols: {cols}")
		v_scrollbar_size = scroll_area.verticalScrollBar().size().width()
		h_scrollbar_size = scroll_area.horizontalScrollBar().size().height()

		total_width = 0
		total_height = 0
		for row in range(rows):
			row_width = 0
			row_height = 0
			for col in range(cols):
				#print(f"check {row}-{col}")
				if layout_main.itemAtPosition(row,col) is not None:
					tmp_widget = layout_main.itemAtPosition(row,col).widget()
					if (tmp_widget is not None) and (type(tmp_widget) is QtWidgets.QLabel):
						if tmp_widget.pixmap() is not None:
							image_size = tmp_widget.pixmap().size()
							item_idx = layout_main.indexOf(layout_main.itemAtPosition(row,col))
							from_row,from_col,from_rowspan,from_colspan = layout_main.getItemPosition(item_idx)
							total_cols_in_row = ReaderImageProcess.get_cols_in_row(layout_main,row,cols)
							#print(f"row {row} have col {total_cols_in_row}")

							if image_size.width() / image_size.height() > pages_ratio_require and from_colspan > 1:
								# 2 page already!
								#print(f"{tmp_widget.windowFilePath()} is 2 page")
								target_width_ratio = from_colspan/page_mode.value
								#print(f"area size {area_size}")
								if scroll_flow == ScrollFlow.UP_DOWN and page_mode.value > 2:
									# 3 or 4 pages
									new_image_size = ReaderImageProcess.get_fit_image_size(
										QSize(int((area_size.width() - (page_gap * (total_cols_in_row - 1))) * target_width_ratio)-int(v_scrollbar_size * target_width_ratio) - 1, area_size.height()),
										image_size, 0, h_scrollbar_size, page_fit,
										scroll_flow,free_width)
									#print("use small area")
								else:
									new_image_size = ReaderImageProcess.get_fit_image_size(
										QSize(int((area_size.width() - (page_gap * (total_cols_in_row - 1)))*target_width_ratio), area_size.height()), image_size,
										int(v_scrollbar_size*target_width_ratio), h_scrollbar_size,page_fit,scroll_flow,free_width)
								#print(f"new_image_size {new_image_size}")
							else:
								#print(f"{tmp_widget.windowFilePath()} is 1 page")
								if scroll_flow == ScrollFlow.UP_DOWN and page_mode.value > 2:
									# force display the scroll bar case
									new_image_size = ReaderImageProcess.get_fit_image_size(
										QSize((area_size.width() - (page_gap * (total_cols_in_row - 1))) / cols - (v_scrollbar_size / cols) - 1, area_size.height()), image_size,
										0, h_scrollbar_size, page_fit, scroll_flow,free_width)
								else:
									new_image_size = ReaderImageProcess.get_fit_image_size(
										QSize((area_size.width() - (page_gap * (total_cols_in_row - 1))) / cols, area_size.height()),image_size,
										v_scrollbar_size / cols, h_scrollbar_size,page_fit,scroll_flow,free_width)
								#print(f"new_image_size {new_image_size}")
							tmp_widget.setFixedSize(new_image_size.width(), new_image_size.height())
							#print(f"row:{row},col:{col}, width:{new_image_size.width()},height:{new_image_size.height()}")
							row_width += new_image_size.width()
							row_height = max(row_height, new_image_size.height())
			total_width = max(total_width,row_width)
			total_height += row_height
		#print(f"total_width:{total_width}, total_height:{total_height}")
		return total_width, total_height

	@staticmethod
	def get_cols_in_row(layout_main:QGridLayout,row:int,total_check_col:int):
		total_col = 0
		current_col = 0
		while current_col < total_check_col:
			#print(f"row:{row} current_col: {current_col}")
			tmp_item = layout_main.itemAtPosition(row, current_col)
			if tmp_item is not None:
				item_idx = layout_main.indexOf(tmp_item)
				from_row, from_col, from_rowspan, from_colspan = layout_main.getItemPosition(item_idx)
				#print(f"total check {total_check_col}, cel info: {from_row}, {from_col}, {from_rowspan}, {from_colspan}")
				total_col += 1
				current_col += from_colspan
			else:
				total_col += 1
				current_col += 1
		return total_col

	@staticmethod
	def update_single_image(file,page_mode:PageMode,layout_main:QGridLayout,current_reader:Reader):
		rows = layout_main.rowCount()
		cols = page_mode.value
		for row in range(rows):
			for col in range(cols):
				if layout_main.itemAtPosition(row,col) is not None:
					tmp_widget = layout_main.itemAtPosition(row,col).widget()
					if (tmp_widget is not None) and (type(tmp_widget) is QtWidgets.QLabel):
						if tmp_widget.windowFilePath() == file:
							q_pixmap = current_reader.get_q_pixmap_from_file(file)
							tmp_widget.setPixmap(q_pixmap)
							return
		pass
