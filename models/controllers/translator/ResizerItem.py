from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsObject

#from .BoxItem import BoxItem

class ResizerItem(QGraphicsObject):
    startResizeSignal = pyqtSignal()
    resizeSignal = pyqtSignal(QPointF, str)
    start_pos = QPointF(0,0)
    resize_type_to_cursor = {
        "L": QtCore.Qt.SizeHorCursor,
        "R": QtCore.Qt.SizeHorCursor,
        "T": QtCore.Qt.SizeVerCursor,
        "B": QtCore.Qt.SizeVerCursor,
        "TL": QtCore.Qt.SizeFDiagCursor,
        "TR": QtCore.Qt.SizeBDiagCursor,
        "BL": QtCore.Qt.SizeBDiagCursor,
        "BR": QtCore.Qt.SizeFDiagCursor,
    }
    parent = None

    def __init__(self, rect=QRectF(0, 0, 10, 10), parent=None, resize_type="TL"):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resize_type = resize_type
        self.rect = rect
        self.parent = parent
        self.setCursor(QCursor(self.resize_type_to_cursor[self.resize_type]))

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        pass

    def mousePressEvent(self, event):
        #print("mouse move",event)
        self.start_pos = self.pos()
        self.startResizeSignal.emit()
        super(ResizerItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super(ResizerItem, self).mouseReleaseEvent(event)
        #print("mouse release")
        if self.parent is not None:
            self.setSelected(False)
            self.parent.setSelected(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.isSelected():
                #print(f"value:{value.x()}-{value.y()}")
                value -= self.start_pos
                if self.resize_type == "L" or self.resize_type == "R":
                    value.setY(0)
                elif self.resize_type == "T" or self.resize_type == "B":
                    value.setX(0)
                self.resizeSignal.emit(value, self.resize_type)
                value = self.pos()
        return value