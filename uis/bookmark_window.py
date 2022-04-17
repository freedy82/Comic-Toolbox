# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bookmark_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        MainWindow.resize(500, 300)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/main_icon"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.table_bookmark = QtWidgets.QTableWidget(self.centralwidget)
        self.table_bookmark.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        self.table_bookmark.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table_bookmark.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_bookmark.setColumnCount(2)
        self.table_bookmark.setObjectName("table_bookmark")
        self.table_bookmark.setRowCount(0)
        self.verticalLayout.addWidget(self.table_bookmark)
        self.layout_button = QtWidgets.QHBoxLayout()
        self.layout_button.setObjectName("layout_button")
        self.btn_close = QtWidgets.QPushButton(self.centralwidget)
        self.btn_close.setObjectName("btn_close")
        self.layout_button.addWidget(self.btn_close)
        self.btn_delete = QtWidgets.QPushButton(self.centralwidget)
        self.btn_delete.setObjectName("btn_delete")
        self.layout_button.addWidget(self.btn_delete)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.layout_button.addItem(spacerItem)
        self.btn_load = QtWidgets.QPushButton(self.centralwidget)
        self.btn_load.setObjectName("btn_load")
        self.layout_button.addWidget(self.btn_load)
        self.verticalLayout.addLayout(self.layout_button)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Bookmarks"))
        self.btn_close.setText(_translate("MainWindow", "Close"))
        self.btn_delete.setText(_translate("MainWindow", "Delete"))
        self.btn_load.setText(_translate("MainWindow", "Load"))
from uis import resources_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())