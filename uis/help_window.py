# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'help_window.ui'
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
        MainWindow.resize(480, 320)
        MainWindow.setMinimumSize(QtCore.QSize(480, 320))
        MainWindow.setMaximumSize(QtCore.QSize(480, 320))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/main_icon"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setModal(True)
        self.tab_main = QtWidgets.QTabWidget(MainWindow)
        self.tab_main.setGeometry(QtCore.QRect(9, 9, 461, 271))
        self.tab_main.setElideMode(QtCore.Qt.ElideNone)
        self.tab_main.setDocumentMode(False)
        self.tab_main.setTabsClosable(False)
        self.tab_main.setMovable(False)
        self.tab_main.setTabBarAutoHide(False)
        self.tab_main.setObjectName("tab_main")
        self.tab_page1 = QtWidgets.QWidget()
        self.tab_page1.setObjectName("tab_page1")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tab_page1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.txt_supported_site = QtWidgets.QTextBrowser(self.tab_page1)
        self.txt_supported_site.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.txt_supported_site.setHtml("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'PMingLiU\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.txt_supported_site.setAcceptRichText(True)
        self.txt_supported_site.setOpenExternalLinks(True)
        self.txt_supported_site.setObjectName("txt_supported_site")
        self.verticalLayout.addWidget(self.txt_supported_site)
        self.tab_main.addTab(self.tab_page1, "")
        self.tab_page2 = QtWidgets.QWidget()
        self.tab_page2.setObjectName("tab_page2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab_page2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.txt_other = QtWidgets.QTextBrowser(self.tab_page2)
        self.txt_other.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.txt_other.setObjectName("txt_other")
        self.verticalLayout_2.addWidget(self.txt_other)
        self.tab_main.addTab(self.tab_page2, "")
        self.btn_box = QtWidgets.QDialogButtonBox(MainWindow)
        self.btn_box.setGeometry(QtCore.QRect(10, 290, 461, 23))
        self.btn_box.setOrientation(QtCore.Qt.Horizontal)
        self.btn_box.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.btn_box.setObjectName("btn_box")

        self.retranslateUi(MainWindow)
        self.tab_main.setCurrentIndex(0)
        self.btn_box.accepted.connect(MainWindow.accept) # type: ignore
        self.btn_box.rejected.connect(MainWindow.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Comic Toolbox"))
        self.tab_main.setTabText(self.tab_main.indexOf(self.tab_page1), _translate("MainWindow", "About supported site"))
        self.tab_main.setTabText(self.tab_main.indexOf(self.tab_page2), _translate("MainWindow", "Other"))
from uis import resources_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QDialog()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
