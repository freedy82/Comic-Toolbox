from PyQt6 import QtCore, QtGui, QtWidgets


class FullscreenToolbar(QtCore.QObject):
    """Slide the reader's existing toolbar over the full-screen page."""

    def __init__(self, window, toolbar):
        super().__init__(window)
        self.window = window
        self.toolbar = toolbar
        self.active = False
        self.revealed = False
        self.normal_area = QtCore.Qt.ToolBarArea.TopToolBarArea

        self.overlay = QtWidgets.QWidget(window)
        self.overlay.setObjectName("reader_fullscreen_toolbar")
        self.overlay.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.overlay.hide()
        self.layout = QtWidgets.QVBoxLayout(self.overlay)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.animation = QtCore.QPropertyAnimation(self.overlay, b"pos", self)
        self.animation.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self._animation_finished)
        # Poll only in full screen so dynamically created image labels do not
        # need mouse tracking or changes to the reader's drag-to-pan behavior.
        self.cursor_timer = QtCore.QTimer(self)
        self.cursor_timer.setInterval(40)
        self.cursor_timer.timeout.connect(self._check_cursor)
        self.hide_timer = QtCore.QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(200)
        self.hide_timer.timeout.connect(self._hide_if_outside)
        window.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched is self.window:
            event_type = event.type()
            if event_type == QtCore.QEvent.Type.WindowStateChange:
                if self.window.isFullScreen():
                    if not self.active:
                        self._enter()
                elif self.active:
                    self._leave()
            elif event_type == QtCore.QEvent.Type.Resize and self.active:
                self._resize_overlay()
            elif event_type in (QtCore.QEvent.Type.PaletteChange, QtCore.QEvent.Type.StyleChange):
                if self.active:
                    self._sync_background()
            elif event_type == QtCore.QEvent.Type.Hide:
                self.cursor_timer.stop()
                self.hide_timer.stop()
                self.animation.stop()
                if self.active:
                    self.revealed = False
                    self.overlay.move(0, -self.overlay.height())
                    self.overlay.hide()
            elif event_type == QtCore.QEvent.Type.Show and self.window.isFullScreen():
                if not self.active:
                    self._enter()
                self._resize_overlay()
                self.cursor_timer.start()
        return False

    def _enter(self):
        self.active = True
        self.revealed = False
        self.normal_area = self.window.toolBarArea(self.toolbar)
        self._sync_background()
        self.toolbar.hide()
        self.window.removeToolBar(self.toolbar)
        self.toolbar.setParent(self.overlay)
        self.layout.addWidget(self.toolbar)
        self.toolbar.show()
        self._resize_overlay()
        self.overlay.hide()
        self.cursor_timer.start()

    def _leave(self):
        self.active = False
        self.revealed = False
        self.cursor_timer.stop()
        self.hide_timer.stop()
        self.animation.stop()
        self.toolbar.hide()
        self.layout.removeWidget(self.toolbar)
        self.toolbar.setParent(self.window)
        self.window.addToolBar(self.normal_area, self.toolbar)
        self.toolbar.show()
        self.overlay.hide()

    def _sync_background(self):
        # Native docked toolbars can rely on their main window's background.
        # Give both overlay layers a solid fill so native toolbar painting
        # cannot blend the comic into the full-screen controls.
        color = self.window.palette().color(self.toolbar.backgroundRole())
        color.setAlpha(255)
        self.overlay.setStyleSheet(
            f"QWidget#reader_fullscreen_toolbar, QToolBar#tb_main {{background-color: {color.name()};}}"
        )

    def _resize_overlay(self):
        self.animation.stop()
        height = max(1, self.toolbar.sizeHint().height())
        self.overlay.resize(self.window.width(), height)
        self.overlay.move(0, 0 if self.revealed else -height)

    def _pointer_needs_toolbar(self):
        if not self.window.isVisible() or self.window.isMinimized():
            return False
        app = QtWidgets.QApplication.instance()
        if self.revealed:
            # QComboBox hosts its list in a separate popup window. Check the
            # view itself so moving below the toolbar cannot hide its owner.
            for combo in self.toolbar.findChildren(QtWidgets.QComboBox):
                if combo.view().isVisible():
                    return True
            popup = app.activePopupWidget()
            if popup is not None:
                if self.overlay.isAncestorOf(popup):
                    return True
                # Reader menus are assigned to tool buttons and may have no
                # QWidget parent. Keep the toolbar visible for their submenus.
                for button in self.toolbar.findChildren(QtWidgets.QToolButton):
                    menu = button.menu()
                    if menu is not None and (menu is popup or menu.isAncestorOf(popup)):
                        return True
            grabber = QtWidgets.QWidget.mouseGrabber()
            if grabber is not None and self.overlay.isAncestorOf(grabber):
                return True
        if not self.window.isActiveWindow():
            return False
        position = self.window.mapFromGlobal(QtGui.QCursor.pos())
        if not self.window.rect().contains(position):
            return False
        if position.y() <= 4:
            return True
        return self.revealed and position.y() <= self.overlay.height() + 4

    def _check_cursor(self):
        if not self.active:
            return
        if self._pointer_needs_toolbar():
            self.hide_timer.stop()
            self._animate(True)
        elif self.revealed and not self.hide_timer.isActive():
            self.hide_timer.start()

    def _hide_if_outside(self):
        if self.active and not self._pointer_needs_toolbar():
            self._animate(False)

    def _animate(self, reveal):
        if reveal == self.revealed:
            return
        self.revealed = reveal
        self.animation.stop()
        self.overlay.show()
        self.overlay.raise_()
        target = QtCore.QPoint(0, 0 if reveal else -self.overlay.height())
        distance = abs(target.y() - self.overlay.y())
        self.animation.setDuration(max(1, round(180 * distance / self.overlay.height())))
        self.animation.setStartValue(self.overlay.pos())
        self.animation.setEndValue(target)
        self.animation.start()

    def _animation_finished(self):
        if self.active and not self.revealed:
            self.overlay.hide()
