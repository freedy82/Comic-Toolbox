# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'reader_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(780, 480)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/main_icon"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setStyleSheet("")
        self.mainwidget = QtWidgets.QWidget(MainWindow)
        self.mainwidget.setObjectName("mainwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.mainwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.scrollArea = QtWidgets.QScrollArea(self.mainwidget)
        self.scrollArea.setStyleSheet("")
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 780, 425))
        self.scrollAreaWidgetContents.setStyleSheet("background-color: #000000;\n"
"color: #FFFFFF;")
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 0, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 1, 0, 1, 1)
        self.layout_main = QtWidgets.QGridLayout()
        self.layout_main.setSpacing(0)
        self.layout_main.setObjectName("layout_main")
        self.lbl_tmp = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lbl_tmp.setMinimumSize(QtCore.QSize(50, 50))
        self.lbl_tmp.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
        self.lbl_tmp.setLineWidth(0)
        self.lbl_tmp.setText("page center")
        self.lbl_tmp.setScaledContents(True)
        self.lbl_tmp.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_tmp.setObjectName("lbl_tmp")
        self.layout_main.addWidget(self.lbl_tmp, 0, 0, 1, 1)
        self.gridLayout.addLayout(self.layout_main, 1, 1, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 1, 2, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 2, 1, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout.addWidget(self.scrollArea)
        MainWindow.setCentralWidget(self.mainwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 780, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.tb_main = QtWidgets.QToolBar(MainWindow)
        self.tb_main.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tb_main.sizePolicy().hasHeightForWidth())
        self.tb_main.setSizePolicy(sizePolicy)
        self.tb_main.setWindowTitle("tb_main")
        self.tb_main.setStyleSheet("")
        self.tb_main.setMovable(False)
        self.tb_main.setFloatable(False)
        self.tb_main.setObjectName("tb_main")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.tb_main)
        self.tb_right = QtWidgets.QToolBar(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tb_right.sizePolicy().hasHeightForWidth())
        self.tb_right.setSizePolicy(sizePolicy)
        self.tb_right.setWindowTitle("tb_right")
        self.tb_right.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tb_right.setMovable(False)
        self.tb_right.setFloatable(False)
        self.tb_right.setObjectName("tb_right")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.tb_right)
        self.actionPageModeSingle = QtWidgets.QAction(MainWindow)
        self.actionPageModeSingle.setCheckable(True)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icon/1column"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPageModeSingle.setIcon(icon1)
        self.actionPageModeSingle.setObjectName("actionPageModeSingle")
        self.actionFileOpenFile = QtWidgets.QAction(MainWindow)
        self.actionFileOpenFile.setEnabled(True)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icon/open-archive"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFileOpenFile.setIcon(icon2)
        self.actionFileOpenFile.setObjectName("actionFileOpenFile")
        self.actionFileOpenFolder = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icon/open_folder"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFileOpenFolder.setIcon(icon3)
        self.actionFileOpenFolder.setObjectName("actionFileOpenFolder")
        self.actionFileExit = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icon/exit"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFileExit.setIcon(icon4)
        self.actionFileExit.setObjectName("actionFileExit")
        self.actionFullscreen = QtWidgets.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icon/full_screen"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFullscreen.setIcon(icon5)
        self.actionFullscreen.setObjectName("actionFullscreen")
        self.actionScrollFlowUpDown = QtWidgets.QAction(MainWindow)
        self.actionScrollFlowUpDown.setCheckable(True)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icon/horizontal"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionScrollFlowUpDown.setIcon(icon6)
        self.actionScrollFlowUpDown.setObjectName("actionScrollFlowUpDown")
        self.actionScrollFlowLeftRight = QtWidgets.QAction(MainWindow)
        self.actionScrollFlowLeftRight.setCheckable(True)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icon/vertical"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionScrollFlowLeftRight.setIcon(icon7)
        self.actionScrollFlowLeftRight.setObjectName("actionScrollFlowLeftRight")
        self.actionPageModeDouble = QtWidgets.QAction(MainWindow)
        self.actionPageModeDouble.setCheckable(True)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icon/2columns"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPageModeDouble.setIcon(icon8)
        self.actionPageModeDouble.setObjectName("actionPageModeDouble")
        self.actionPageModeTriple = QtWidgets.QAction(MainWindow)
        self.actionPageModeTriple.setCheckable(True)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/icon/3columns"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPageModeTriple.setIcon(icon9)
        self.actionPageModeTriple.setObjectName("actionPageModeTriple")
        self.actionFitWidth = QtWidgets.QAction(MainWindow)
        self.actionFitWidth.setCheckable(True)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/icon/fit-width"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFitWidth.setIcon(icon10)
        self.actionFitWidth.setObjectName("actionFitWidth")
        self.actionFitHeight = QtWidgets.QAction(MainWindow)
        self.actionFitHeight.setCheckable(True)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(":/icon/fit-height"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFitHeight.setIcon(icon11)
        self.actionFitHeight.setObjectName("actionFitHeight")
        self.actionFitBoth = QtWidgets.QAction(MainWindow)
        self.actionFitBoth.setCheckable(True)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap(":/icon/fit-both"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFitBoth.setIcon(icon12)
        self.actionFitBoth.setObjectName("actionFitBoth")
        self.actionFitWidth80 = QtWidgets.QAction(MainWindow)
        self.actionFitWidth80.setCheckable(True)
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap(":/icon/fit-width-80"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFitWidth80.setIcon(icon13)
        self.actionFitWidth80.setObjectName("actionFitWidth80")
        self.actionPageFlowRightToLeft = QtWidgets.QAction(MainWindow)
        self.actionPageFlowRightToLeft.setCheckable(True)
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap(":/icon/right-to-left"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPageFlowRightToLeft.setIcon(icon14)
        self.actionPageFlowRightToLeft.setObjectName("actionPageFlowRightToLeft")
        self.actionPageFlowLeftToRight = QtWidgets.QAction(MainWindow)
        self.actionPageFlowLeftToRight.setCheckable(True)
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap(":/icon/left-to-right"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPageFlowLeftToRight.setIcon(icon15)
        self.actionPageFlowLeftToRight.setObjectName("actionPageFlowLeftToRight")
        self.actionPageModeQuadruple = QtWidgets.QAction(MainWindow)
        self.actionPageModeQuadruple.setCheckable(True)
        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap(":/icon/4columns"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPageModeQuadruple.setIcon(icon16)
        self.actionPageModeQuadruple.setObjectName("actionPageModeQuadruple")
        self.actionAddBookmark = QtWidgets.QAction(MainWindow)
        icon17 = QtGui.QIcon()
        icon17.addPixmap(QtGui.QPixmap(":/icon/bookmark"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionAddBookmark.setIcon(icon17)
        self.actionAddBookmark.setObjectName("actionAddBookmark")
        self.actionBookmarkList = QtWidgets.QAction(MainWindow)
        icon18 = QtGui.QIcon()
        icon18.addPixmap(QtGui.QPixmap(":/icon/list"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBookmarkList.setIcon(icon18)
        self.actionBookmarkList.setObjectName("actionBookmarkList")
        self.menuFile.addAction(self.actionFileOpenFile)
        self.menuFile.addAction(self.actionFileOpenFolder)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionFileExit)
        self.menubar.addAction(self.menuFile.menuAction())
        self.tb_main.addAction(self.actionFileOpenFolder)
        self.tb_main.addAction(self.actionFileOpenFile)
        self.tb_main.addSeparator()
        self.tb_main.addAction(self.actionScrollFlowLeftRight)
        self.tb_main.addAction(self.actionScrollFlowUpDown)
        self.tb_main.addSeparator()
        self.tb_main.addAction(self.actionFitHeight)
        self.tb_main.addAction(self.actionFitWidth)
        self.tb_main.addAction(self.actionFitBoth)
        self.tb_main.addAction(self.actionFitWidth80)
        self.tb_main.addSeparator()
        self.tb_main.addAction(self.actionPageModeSingle)
        self.tb_main.addAction(self.actionPageModeDouble)
        self.tb_main.addAction(self.actionPageModeTriple)
        self.tb_main.addAction(self.actionPageModeQuadruple)
        self.tb_main.addSeparator()
        self.tb_main.addAction(self.actionPageFlowRightToLeft)
        self.tb_main.addAction(self.actionPageFlowLeftToRight)
        self.tb_main.addSeparator()
        self.tb_main.addAction(self.actionFullscreen)
        self.tb_main.addSeparator()
        self.tb_main.addAction(self.actionAddBookmark)
        self.tb_main.addAction(self.actionBookmarkList)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Reader"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionPageModeSingle.setText(_translate("MainWindow", "1 Page"))
        self.actionPageModeSingle.setToolTip(_translate("MainWindow", "1 Page"))
        self.actionFileOpenFile.setText(_translate("MainWindow", "Open File"))
        self.actionFileOpenFolder.setText(_translate("MainWindow", "Open Folder"))
        self.actionFileExit.setText(_translate("MainWindow", "Quit"))
        self.actionFullscreen.setText(_translate("MainWindow", "Fullscreen"))
        self.actionFullscreen.setToolTip(_translate("MainWindow", "Fullscreen (F11)"))
        self.actionScrollFlowUpDown.setText(_translate("MainWindow", "Vertical"))
        self.actionScrollFlowUpDown.setToolTip(_translate("MainWindow", "Vertical"))
        self.actionScrollFlowLeftRight.setText(_translate("MainWindow", "Horizontal"))
        self.actionScrollFlowLeftRight.setToolTip(_translate("MainWindow", "Horizontal"))
        self.actionPageModeDouble.setText(_translate("MainWindow", "2 Pages"))
        self.actionPageModeDouble.setToolTip(_translate("MainWindow", "2 Pages"))
        self.actionPageModeTriple.setText(_translate("MainWindow", "3 Pages"))
        self.actionPageModeTriple.setToolTip(_translate("MainWindow", "3 Pages"))
        self.actionFitWidth.setText(_translate("MainWindow", "Fit Width"))
        self.actionFitWidth.setToolTip(_translate("MainWindow", "Fit Width"))
        self.actionFitHeight.setText(_translate("MainWindow", "Fit Height"))
        self.actionFitHeight.setToolTip(_translate("MainWindow", "Fit Height"))
        self.actionFitBoth.setText(_translate("MainWindow", "Fit Both"))
        self.actionFitBoth.setToolTip(_translate("MainWindow", "Fit Both"))
        self.actionFitWidth80.setText(_translate("MainWindow", "Fit Width 80%"))
        self.actionFitWidth80.setToolTip(_translate("MainWindow", "Fit Width 80%"))
        self.actionPageFlowRightToLeft.setText(_translate("MainWindow", "Right to Left"))
        self.actionPageFlowRightToLeft.setToolTip(_translate("MainWindow", "Right to Left"))
        self.actionPageFlowLeftToRight.setText(_translate("MainWindow", "Left to Right"))
        self.actionPageFlowLeftToRight.setToolTip(_translate("MainWindow", "Left to Right"))
        self.actionPageModeQuadruple.setText(_translate("MainWindow", "4 Pages"))
        self.actionPageModeQuadruple.setToolTip(_translate("MainWindow", "4 Pages"))
        self.actionAddBookmark.setText(_translate("MainWindow", "Add to bookmark"))
        self.actionAddBookmark.setToolTip(_translate("MainWindow", "Add to bookmark"))
        self.actionBookmarkList.setText(_translate("MainWindow", "Display bookmark list"))
        self.actionBookmarkList.setToolTip(_translate("MainWindow", "Display bookmark list"))
from uis import resources_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())