from PyQt5 import QtWidgets
from PyQt5 import QtCore

from const import *
from models.main_window_controller import MainWindowController

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    trans = QtCore.QTranslator()
    trans.load("./languages/"+MY_CONFIG.get("general", "language"))
    app.installTranslator(trans)

    window = MainWindowController(app,trans)
    window.show()
    sys.exit(app.exec_())