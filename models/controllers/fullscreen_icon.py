"""Keep fullscreen actions synchronized with their window's actual state."""

from PyQt6 import QtCore, QtGui


class FullscreenIcon(QtCore.QObject):
    def __init__(self, window, action):
        super().__init__(window)
        self.window = window
        self.action = action
        self.fullscreen = QtGui.QIcon(":/icon/full-screen")
        self.normal_screen = QtGui.QIcon(":/icon/normal-screen")
        window.installEventFilter(self)
        self._sync()

    def _sync(self):
        self.action.setIcon(self.normal_screen if self.window.isFullScreen() else self.fullscreen)

    def eventFilter(self, watched, event):
        if watched is self.window and event.type() == QtCore.QEvent.Type.WindowStateChange:
            self._sync()
        return False
