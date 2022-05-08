from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .BoxItem import BoxItem

class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = pyqtSignal(QtCore.QPoint)
    item_selected = pyqtSignal(object)
    item_changed = pyqtSignal(object,QRect)
    item_deleted = pyqtSignal()
    view_updated = pyqtSignal(QtGui.QTransform,float)
    drag_start_pos = QPoint(-1,-1)
    current_drag_label = None

    def __init__(self, parent=None):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        #self._scene = MyScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._scene.focusItemChanged.connect(self.scene_focus_item_changed)
        self.labels = []

    def unselect_all_label(self):
        for item in self._scene.selectedItems():
            item.setSelected(False)

    def add_label(self,label_text="",frame=QRectF(0,0,100,100)):
        tmp_label = BoxItem(proxy_parent=self,position=QPointF(frame.x(),frame.y()),rect=QRectF(0,0,frame.width(),frame.height()), text=label_text)
        self._scene.addItem(tmp_label)
        self.unselect_all_label()
        tmp_label.setSelected(True)
        self.item_selected.emit(tmp_label)
        #self.labels.append(tmp_label)
        return tmp_label

    def has_photo(self):
        return not self._empty

    def try_fit_in_view(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.has_photo():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def set_pixmap_photo(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.try_fit_in_view()

    def delete_all_label(self):
        for tmp_label in self.get_all_labels():
            self._scene.removeItem(tmp_label)
        self.item_deleted.emit()

    def select_label_by_index(self,index):
        for idx,tmp_label in enumerate(self.get_all_labels()):
            if idx == index:
                self.unselect_all_label()
                tmp_label.setSelected(True)
                self.item_selected.emit(tmp_label)
                return

    def get_current_selected_label(self):
        if len(self._scene.selectedItems()) > 0:
            for item in self._scene.selectedItems():
                if isinstance(item,BoxItem):
                    return item
        return None

    def get_all_labels(self):
        results = []
        for item in self._scene.items():
            if isinstance(item,BoxItem):
                results.append(item)
        return results

    def scene_focus_item_changed(self,new_item,old_item):
        if new_item is None or isinstance(new_item, BoxItem):
            self.item_selected.emit(new_item)
            if isinstance(new_item, BoxItem):
                self.item_changed.emit(new_item,new_item.get_frame())

    def item_frame_changed(self,item,frame):
        #print(f"{item} {frame}")
        self.item_changed.emit(item,frame)

    def set_current_label_frame(self,frame):
        item = self.get_current_selected_label()
        if item is not None:
            item.set_frame(frame)

    def try_drag_create_and_move_current_label(self, start_pos, current_pos):
        if self.current_drag_label is None:
            self.current_drag_label = self.add_label()
        x0 = min(start_pos.x(),current_pos.x())
        y0 = min(start_pos.y(),current_pos.y())
        x1 = max(start_pos.x(),current_pos.x())
        y1 = max(start_pos.y(),current_pos.y())
        self.current_drag_label.set_frame(QRect(x0,y0,x1-x0,y1-y0))

    def toggle_add_mode(self,is_manual_add=False):
        if is_manual_add:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setCursor(QCursor(QtCore.Qt.CrossCursor))
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setCursor(QCursor(QtCore.Qt.OpenHandCursor))

    def get_zoom(self):
        return self._zoom

    def set_transform(self, transform, zoom):
        self.setTransform(transform)
        self._zoom = zoom

    def wheelEvent(self, event):
        if self.has_photo():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1

            if self._zoom > 0:
                self.scale(factor, factor)
                self.view_updated.emit(self.transform(), self._zoom)
            elif self._zoom == 0:
                self.try_fit_in_view()
                self.view_updated.emit(self.transform(), self._zoom)
            else:
                self._zoom = 0

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        super(PhotoViewer, self).keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_Delete:
            item = self.get_current_selected_label()
            if item is not None:
                self._scene.removeItem(item)
                self.item_deleted.emit()

    def resizeEvent(self, event):
        super(PhotoViewer, self).resizeEvent(event)
        if not self.verticalScrollBar().isVisible() and not self.horizontalScrollBar().isVisible():
            self.try_fit_in_view()

    def mousePressEvent(self, event):
        super(PhotoViewer, self).mousePressEvent(event)
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        if self.dragMode() == QtWidgets.QGraphicsView.NoDrag:
            #print("mouse press")
            if len(self._scene.selectedItems()) == 0:
                self.drag_start_pos = self.mapToScene(event.pos()).toPoint()
            else:
                self.drag_start_pos = QPoint(-1,-1)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super(PhotoViewer, self).mouseMoveEvent(event)
        if self.dragMode() == QtWidgets.QGraphicsView.NoDrag:
            current_pos = self.mapToScene(event.pos()).toPoint()
            if 0 <= self.drag_start_pos.x() < self._photo.pixmap().width() and \
                    0 <= self.drag_start_pos.y() < self._photo.pixmap().height():
                #print("mouse move event in photo ",current_pos)
                self.try_drag_create_and_move_current_label(self.drag_start_pos,current_pos)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if self.dragMode() == QtWidgets.QGraphicsView.NoDrag:
            #print("mouse release")
            self.drag_start_pos = QPoint(-1,-1)
            if self.current_drag_label is not None:
                self.current_drag_label.setSelected(True)
                self.current_drag_label.try_bring_to_front()
                self.item_selected.emit(self.current_drag_label)
            self.current_drag_label = None

        super(PhotoViewer, self).mouseReleaseEvent(event)