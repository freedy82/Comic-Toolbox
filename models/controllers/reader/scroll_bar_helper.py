from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtWidgets import QGridLayout, QScrollArea

from models.controllers.reader.helper import *


class ReaderScrollBarHelper:
	def __init__(self):
		super(ReaderScrollBarHelper, self).__init__()

	@staticmethod
	def found_row_of_scroll_area(current_visible_frame,layout_main: QGridLayout):
		found_row = 0
		current_y = 0
		max_row_height = 0
		old_row = -1
		for i in range(layout_main.count()):
			tmp_widget = layout_main.itemAt(i).widget()
			if type(tmp_widget) is QtWidgets.QLabel:
				row, col, _, _ = layout_main.getItemPosition(i)
				# to fix the y was not yet update
				child_frame = tmp_widget.frameGeometry()
				if old_row != row:
					current_y += max_row_height
					max_row_height = 0
				# print(f"frame:{tmp_widget.frameGeometry()}")
				widget_height = child_frame.height()
				max_row_height = max(max_row_height, widget_height)
				old_row = row
				child_real_frame = QtCore.QRect(child_frame.x(), current_y, child_frame.width(), widget_height)
				if current_visible_frame.intersects(child_real_frame):
					found_row = row
					break
		return found_row

	@staticmethod
	def move_scroll_area_by_row(target_row,layout_main: QGridLayout, scroll_area: QScrollArea):
		#fix for item frame update delay
		current_y = 0
		max_row_height = 0
		old_row = -1
		for i in range(layout_main.count()):
			tmp_widget = layout_main.itemAt(i).widget()
			if type(tmp_widget) is QtWidgets.QLabel:
				row, col, _, _ = layout_main.getItemPosition(i)
				#print(f"checking row:{row}, col:{col}")
				if row == target_row:
					#target_y = tmp_widget.frameGeometry().y()
					#print(f"geometry:{tmp_widget.geometry()}")
					#print(f"frame:{tmp_widget.frameGeometry()}")
					#print(f"try move to row:{row} y:{current_y+max_row_height}")
					#print(f"scrollbar max:{self.ui.scrollArea.verticalScrollBar().maximum()}")
					#print(f"current_y:{current_y+max_row_height}")
					#self.ui.scrollArea.verticalScrollBar().setValue(target_y)
					#self.ui.scrollArea.verticalScrollBar().blockSignals(True)
					scroll_area.verticalScrollBar().setValue(current_y+max_row_height)
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

	@staticmethod
	def handle_scroll_area_event(last_time_move:QPoint, event:QEvent, page_flow:PageFlow, scroll_area:QScrollArea,go_prev_page,go_next_page):
		if event.type() == QEvent.MouseMove:
			if last_time_move == QPoint(0,0):
				last_time_move = event.pos()
			distance_x = last_time_move.x() - event.pos().x()
			distance_y = last_time_move.y() - event.pos().y()
			scroll_area.horizontalScrollBar().setValue(scroll_area.horizontalScrollBar().value() + distance_x)
			scroll_area.verticalScrollBar().setValue(scroll_area.verticalScrollBar().value() + distance_y)
			last_time_move = event.pos()
		elif event.type() == QEvent.MouseButtonRelease:
			last_time_move = QPoint(0, 0)
		elif event.type() == QEvent.Wheel:
			delta_y = event.angleDelta().y()
			if delta_y > 0:
				go_prev_page()
			elif delta_y < 0:
				go_next_page()
		elif event.type() == QEvent.KeyRelease:
			if event.key() == Qt.Key_Down:
				if scroll_area.verticalScrollBar().value() == scroll_area.verticalScrollBar().maximum():
					go_next_page()
			if event.key() == Qt.Key_Up:
				if scroll_area.verticalScrollBar().value() == 0:
					go_prev_page()
			if event.key() == Qt.Key_Left:
				if scroll_area.horizontalScrollBar().value() == 0:
					if page_flow == PageFlow.LEFT_TO_RIGHT:
						go_prev_page()
					elif page_flow == PageFlow.RIGHT_TO_LEFT:
						go_next_page()
			if event.key() == Qt.Key_Right:
				if scroll_area.horizontalScrollBar().value() == scroll_area.horizontalScrollBar().maximum():
					if page_flow == PageFlow.LEFT_TO_RIGHT:
						go_next_page()
					elif page_flow == PageFlow.RIGHT_TO_LEFT:
						go_prev_page()
		return last_time_move
