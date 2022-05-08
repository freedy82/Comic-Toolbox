from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QGraphicsView, QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem
from typing import cast

from .ResizerItem import ResizerItem

class BoxItem(QGraphicsRectItem):
    resizer_gap = 15
    proxy_parent = None
    start_pos = QPointF(0,0)
    start_rect = QRectF(0,0,0,0)
    org_text = ""
    trans_text = ""
    font_index = 0
    font_size = 0
    align_index = 0
    text_style_index = 0

    def __init__(self, position=QPointF(0,0), rect=QRectF(0, 0, 100, 50), parent=None, proxy_parent=None, resizer_gap=15, text=""):
        super().__init__(rect, parent)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(QtCore.Qt.SizeAllCursor))

        self.resizer_gap = resizer_gap
        self.proxy_parent = proxy_parent

        self.text = QGraphicsTextItem(text, self)
        self.text.setFlag(QGraphicsItem.ItemIgnoresTransformations)

        self.setPos(position)

        self.resizer_l = ResizerItem(parent=self,resize_type="L")
        self.resizer_l.resizeSignal.connect(self.resize)
        self.resizer_l.startResizeSignal.connect(self.start_resize)
        self.resizer_r = ResizerItem(parent=self,resize_type="R")
        self.resizer_r.resizeSignal.connect(self.resize)
        self.resizer_r.startResizeSignal.connect(self.start_resize)
        self.resizer_t = ResizerItem(parent=self,resize_type="T")
        self.resizer_t.resizeSignal.connect(self.resize)
        self.resizer_t.startResizeSignal.connect(self.start_resize)
        self.resizer_b = ResizerItem(parent=self,resize_type="B")
        self.resizer_b.resizeSignal.connect(self.resize)
        self.resizer_b.startResizeSignal.connect(self.start_resize)

        self.resizer_tl = ResizerItem(parent=self,resize_type="TL")
        self.resizer_tl.resizeSignal.connect(self.resize)
        self.resizer_tl.startResizeSignal.connect(self.start_resize)
        self.resizer_tr = ResizerItem(parent=self,resize_type="TR")
        self.resizer_tr.resizeSignal.connect(self.resize)
        self.resizer_tr.startResizeSignal.connect(self.start_resize)
        self.resizer_bl = ResizerItem(parent=self,resize_type="BL")
        self.resizer_bl.resizeSignal.connect(self.resize)
        self.resizer_bl.startResizeSignal.connect(self.start_resize)
        self.resizer_br = ResizerItem(parent=self,resize_type="BR")
        self.resizer_br.resizeSignal.connect(self.resize)
        self.resizer_br.startResizeSignal.connect(self.start_resize)

        self.update_all_resizer()

    def update_text(self):
        if self.trans_text != "":
            self.text.setPlainText(self.trans_text)
        else:
            self.text.setPlainText(self.org_text)

    #def set_text(self,text):
    #    self.text.setPlainText(text)

    #def get_text(self):
    #    if self.text is not None:
    #        return self.text.toPlainText()
    #    return ""

    def set_frame(self,frame:QRect,is_update_parent=True):
        if frame.x() < 0:
            frame.setX(0)
        if frame.y() < 0:
            frame.setY(0)
        if frame.x() + frame.width() > self.get_proxy_parent_width():
            frame.setWidth(self.get_proxy_parent_width() - frame.x())
        if frame.y() + frame.height() > self.get_proxy_parent_height():
            frame.setHeight(self.get_proxy_parent_height() - frame.y())

        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.setPos(frame.x(),frame.y())
        self.setRect(0,0,frame.width(),frame.height())
        self.update_all_resizer()
        self.prepareGeometryChange()
        self.update()
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        if is_update_parent:
            self.proxy_parent.item_frame_changed(self,self.get_frame())

    def get_frame(self):
        return QRect(self.pos().x(),self.pos().y(),self.rect().width(),self.rect().height())

    def get_proxy_parent_width(self):
        if self.proxy_parent is not None:
            self.proxy_parent = cast(QGraphicsView, self.proxy_parent)
            for idx,item in enumerate(self.proxy_parent.scene().items()):
                if isinstance(item,QtWidgets.QGraphicsPixmapItem):
                    item = cast(QtWidgets.QGraphicsPixmapItem, item)
                    return item.pixmap().width()
        return 0

    def get_proxy_parent_height(self):
        if self.proxy_parent is not None:
            self.proxy_parent = cast(QGraphicsView, self.proxy_parent)
            for idx,item in enumerate(self.proxy_parent.scene().items()):
                if isinstance(item,QtWidgets.QGraphicsPixmapItem):
                    item = cast(QtWidgets.QGraphicsPixmapItem, item)
                    return item.pixmap().height()
        return 0

    def try_bring_to_front(self):
        max_z = 0
        for tmp_item in self.collidingItems(Qt.IntersectsItemBoundingRect):
            max_z = max(max_z,tmp_item.zValue())
        self.setZValue(max_z+1)

    def mouseMoveEvent(self, event):
        #print("mouse move",event)
        super(BoxItem, self).mouseMoveEvent(event)

    def hoverEnterEvent(self,event):
        #print("mouse in")
        super(BoxItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        #print("mouse out")
        super(BoxItem, self).hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        super(BoxItem, self).mousePressEvent(event)
        self.try_bring_to_front()

    def mouseReleaseEvent(self, event):
        super(BoxItem, self).mouseReleaseEvent(event)
        self.try_bring_to_front()

    def paint(self, painter, option, widget=None):
        painter.fillRect(self.rect(),QColor(255,255,255,200))
        pen = QPen()
        if self.isSelected():
            pen.setColor(Qt.red)
        else:
            pen.setColor(Qt.green)
        painter.setPen(pen)
        painter.drawRect(self.rect())



    def start_resize(self):
        self.start_pos = QPointF(self.pos())
        self.start_rect = QRectF(self.rect())

    def resize(self, change, resize_type):
        if resize_type == "L":
            if change.x() + self.start_pos.x() < 0:
                change.setX(-self.start_pos.x())
            if self.start_rect.adjusted(0, 0, -change.x(), 0).width() < 0:
                change.setX(self.start_rect.width())
            self.setPos(self.start_pos + change)
            self.setRect(self.start_rect.adjusted(0, 0, -change.x(), 0))
        if resize_type == "R":
            if change.x() + self.start_pos.x() + self.start_rect.width() > self.get_proxy_parent_width():
                change.setX(self.get_proxy_parent_width() - self.start_pos.x() - self.start_rect.width())
            if self.start_rect.adjusted(0, 0, change.x(), 0).width() < 0:
                change.setX(-self.start_rect.width())
            self.setRect(self.start_rect.adjusted(0, 0, change.x(), 0))
        if resize_type == "T":
            if change.y() + self.start_pos.y() < 0:
                change.setY(-self.start_pos.y())
            if self.start_rect.adjusted(0, 0, 0, -change.y()).height() < 0:
                change.setY(self.start_rect.height())
            self.setPos(self.start_pos + change)
            self.setRect(self.start_rect.adjusted(0, 0, 0, -change.y()))
        if resize_type == "B":
            if change.y() + self.start_pos.y() + self.start_rect.height() > self.get_proxy_parent_height():
                change.setY(self.get_proxy_parent_height() - self.start_pos.y() - self.start_rect.height())
            if self.start_rect.adjusted(0, 0, 0, change.y()).height() < 0:
                change.setY(-self.start_rect.height())
            self.setRect(self.start_rect.adjusted(0, 0, 0, change.y()))
        if resize_type == "TL":
            if change.x() + self.start_pos.x() < 0:
                change.setX(-self.start_pos.x())
            if change.y() + self.start_pos.y() < 0:
                change.setY(-self.start_pos.y())
            if self.start_rect.adjusted(0, 0, -change.x(), 0).width() < 0:
                change.setX(self.start_rect.width())
            if self.start_rect.adjusted(0, 0, 0, -change.y()).height() < 0:
                change.setY(self.start_rect.height())
            self.setPos(self.start_pos + change)
            self.setRect(self.start_rect.adjusted(0, 0, -change.x(), -change.y()))
        if resize_type == "TR":
            if change.x() + self.start_pos.x() + self.start_rect.width() > self.get_proxy_parent_width():
                change.setX(self.get_proxy_parent_width() - self.start_pos.x() - self.start_rect.width())
            if change.y() + self.start_pos.y() < 0:
                change.setY(-self.start_pos.y())
            if self.start_rect.adjusted(0, 0, change.x(), 0).width() < 0:
                change.setX(-self.start_rect.width())
            if self.start_rect.adjusted(0, 0, 0, -change.y()).height() < 0:
                change.setY(self.start_rect.height())
            self.setPos(self.start_pos + QPointF(0, change.y()))
            self.setRect(self.start_rect.adjusted(0, 0, change.x(), -change.y()))
        if resize_type == "BL":
            if change.x() + self.start_pos.x() < 0:
                change.setX(-self.start_pos.x())
            if change.y() + self.start_pos.y() + self.start_rect.height() > self.get_proxy_parent_height():
                change.setY(self.get_proxy_parent_height() - self.start_pos.y() - self.start_rect.height())
            if self.start_rect.adjusted(0, 0, -change.x(), 0).width() < 0:
                change.setX(self.start_rect.width())
            if self.start_rect.adjusted(0, 0, 0, change.y()).height() < 0:
                change.setY(-self.start_rect.height())
            self.setPos(self.start_pos + QPointF(change.x(), 0))
            self.setRect(self.start_rect.adjusted(0, 0, -change.x(), change.y()))
        if resize_type == "BR":
            if change.x() + self.start_pos.x() + self.start_rect.width() > self.get_proxy_parent_width():
                change.setX(self.get_proxy_parent_width() - self.start_pos.x() - self.start_rect.width())
            if change.y() + self.start_pos.y() + self.start_rect.height() > self.get_proxy_parent_height():
                change.setY(self.get_proxy_parent_height() - self.start_pos.y() - self.start_rect.height())
            if self.start_rect.adjusted(0, 0, change.x(), 0).width() < 0:
                change.setX(-self.start_rect.width())
            if self.start_rect.adjusted(0, 0, 0, change.y()).height() < 0:
                change.setY(-self.start_rect.height())
            self.setRect(self.start_rect.adjusted(0, 0, change.x(), change.y()))

        self.update_all_resizer()
        self.prepareGeometryChange()
        self.update()
        self.proxy_parent.item_frame_changed(self,self.get_frame())

    def update_all_resizer(self):
        self.resizer_l.blockSignals(True)
        self.resizer_l.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_l.rect = QRectF(0,0,self.resizer_gap,self.rect().height()-self.resizer_gap*2)
        self.resizer_l.setPos(self.rect().topLeft() - QPointF(0, -self.resizer_gap))
        self.resizer_l.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_l.blockSignals(False)

        self.resizer_r.blockSignals(True)
        self.resizer_r.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_r.rect = QRectF(0,0,self.resizer_gap,self.rect().height()-self.resizer_gap*2)
        self.resizer_r.setPos(self.rect().topRight() - QPointF(self.resizer_gap, -self.resizer_gap))
        self.resizer_r.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_r.blockSignals(False)

        self.resizer_t.blockSignals(True)
        self.resizer_t.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_t.rect = QRectF(0,0,self.rect().width()-self.resizer_gap*2,self.resizer_gap)
        self.resizer_t.setPos(self.rect().topLeft() - QPointF(-self.resizer_gap, 0))
        self.resizer_t.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_t.blockSignals(False)

        self.resizer_b.blockSignals(True)
        self.resizer_b.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_b.rect = QRectF(0,0,self.rect().width()-self.resizer_gap*2,self.resizer_gap)
        self.resizer_b.setPos(self.rect().bottomLeft() - QPointF(-self.resizer_gap, self.resizer_gap))
        self.resizer_b.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_b.blockSignals(False)

        self.resizer_tl.blockSignals(True)
        self.resizer_tl.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_tl.rect = QRectF(0,0,self.resizer_gap,self.resizer_gap)
        self.resizer_tl.setPos(self.rect().topLeft())
        self.resizer_tl.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_tl.blockSignals(False)

        self.resizer_tr.blockSignals(True)
        self.resizer_tr.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_tr.rect = QRectF(0,0,self.resizer_gap,self.resizer_gap)
        self.resizer_tr.setPos(self.rect().topRight() - QPointF(self.resizer_gap, 0))
        self.resizer_tr.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_tr.blockSignals(False)

        self.resizer_bl.blockSignals(True)
        self.resizer_bl.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_bl.rect = QRectF(0,0,self.resizer_gap,self.resizer_gap)
        self.resizer_bl.setPos(self.rect().bottomLeft() - QPointF(0, self.resizer_gap))
        self.resizer_bl.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_bl.blockSignals(False)

        self.resizer_br.blockSignals(True)
        self.resizer_br.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.resizer_br.rect = QRectF(0,0,self.resizer_gap,self.resizer_gap)
        self.resizer_br.setPos(self.rect().bottomRight() - QPointF(self.resizer_gap, self.resizer_gap))
        self.resizer_br.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.resizer_br.blockSignals(False)

    def itemChange(self, change, value):
        #print("change",change)
        if change == QGraphicsItem.ItemPositionChange:
            if value.x() < 0:
                value.setX(0)
            if value.y() < 0:
                value.setY(0)
            if value.x() > self.get_proxy_parent_width() - self.rect().width():
                value.setX(self.get_proxy_parent_width() - self.rect().width())
            if value.y() > self.get_proxy_parent_height() - self.rect().height():
                value.setY(self.get_proxy_parent_height() - self.rect().height())
            self.proxy_parent.item_frame_changed(self, self.get_frame())
        return value