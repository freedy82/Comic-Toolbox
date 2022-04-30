from PyQt5 import QtCore,QtWidgets

from models.const import *
from models.main_window_controller import MainWindowController

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    trans = QtCore.QTranslator()
    trans.load("./languages/"+MY_CONFIG.get("general", "language"))
    app.installTranslator(trans)

    theme = MY_CONFIG.get("general", "theme")
    if theme != "":
        qss_info = open("./themes/" + theme + ".qss","r").read()
        app.setStyleSheet(qss_info)

    window = MainWindowController(app,trans)
    window.show()
    sys.exit(app.exec_())