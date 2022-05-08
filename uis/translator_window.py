# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'translator_window.ui'
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
        MainWindow.resize(981, 716)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/main_icon"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.layout_main = QtWidgets.QHBoxLayout(self.centralwidget)
        self.layout_main.setObjectName("layout_main")
        self.layout_tool = QtWidgets.QVBoxLayout()
        self.layout_tool.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.layout_tool.setObjectName("layout_tool")
        self.layout_engine = QtWidgets.QVBoxLayout()
        self.layout_engine.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.layout_engine.setObjectName("layout_engine")
        self.lbl_bubble_detect_engine = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_bubble_detect_engine.sizePolicy().hasHeightForWidth())
        self.lbl_bubble_detect_engine.setSizePolicy(sizePolicy)
        self.lbl_bubble_detect_engine.setObjectName("lbl_bubble_detect_engine")
        self.layout_engine.addWidget(self.lbl_bubble_detect_engine)
        self.cbx_bubble_detect_engine = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbx_bubble_detect_engine.sizePolicy().hasHeightForWidth())
        self.cbx_bubble_detect_engine.setSizePolicy(sizePolicy)
        self.cbx_bubble_detect_engine.setObjectName("cbx_bubble_detect_engine")
        self.layout_engine.addWidget(self.cbx_bubble_detect_engine)
        self.lbl_ocr__engine = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_ocr__engine.sizePolicy().hasHeightForWidth())
        self.lbl_ocr__engine.setSizePolicy(sizePolicy)
        self.lbl_ocr__engine.setObjectName("lbl_ocr__engine")
        self.layout_engine.addWidget(self.lbl_ocr__engine)
        self.cbx_ocr_engine = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbx_ocr_engine.sizePolicy().hasHeightForWidth())
        self.cbx_ocr_engine.setSizePolicy(sizePolicy)
        self.cbx_ocr_engine.setObjectName("cbx_ocr_engine")
        self.layout_engine.addWidget(self.cbx_ocr_engine)
        self.lbl_translator_engine = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_translator_engine.sizePolicy().hasHeightForWidth())
        self.lbl_translator_engine.setSizePolicy(sizePolicy)
        self.lbl_translator_engine.setObjectName("lbl_translator_engine")
        self.layout_engine.addWidget(self.lbl_translator_engine)
        self.cbx_translator_engine = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbx_translator_engine.sizePolicy().hasHeightForWidth())
        self.cbx_translator_engine.setSizePolicy(sizePolicy)
        self.cbx_translator_engine.setObjectName("cbx_translator_engine")
        self.layout_engine.addWidget(self.cbx_translator_engine)
        self.lbl_language_from = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_language_from.sizePolicy().hasHeightForWidth())
        self.lbl_language_from.setSizePolicy(sizePolicy)
        self.lbl_language_from.setObjectName("lbl_language_from")
        self.layout_engine.addWidget(self.lbl_language_from)
        self.cbx_language_from = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbx_language_from.sizePolicy().hasHeightForWidth())
        self.cbx_language_from.setSizePolicy(sizePolicy)
        self.cbx_language_from.setObjectName("cbx_language_from")
        self.layout_engine.addWidget(self.cbx_language_from)
        self.lbl_language_to = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_language_to.sizePolicy().hasHeightForWidth())
        self.lbl_language_to.setSizePolicy(sizePolicy)
        self.lbl_language_to.setObjectName("lbl_language_to")
        self.layout_engine.addWidget(self.lbl_language_to)
        self.cbx_language_to = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbx_language_to.sizePolicy().hasHeightForWidth())
        self.cbx_language_to.setSizePolicy(sizePolicy)
        self.cbx_language_to.setObjectName("cbx_language_to")
        self.layout_engine.addWidget(self.cbx_language_to)
        self.layout_tool.addLayout(self.layout_engine)
        self.line_middle = QtWidgets.QFrame(self.centralwidget)
        self.line_middle.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_middle.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_middle.setObjectName("line_middle")
        self.layout_tool.addWidget(self.line_middle)
        self.layout_pos = QtWidgets.QFormLayout()
        self.layout_pos.setObjectName("layout_pos")
        self.lbl_x = QtWidgets.QLabel(self.centralwidget)
        self.lbl_x.setText("X")
        self.lbl_x.setObjectName("lbl_x")
        self.layout_pos.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lbl_x)
        self.spin_x = QtWidgets.QSpinBox(self.centralwidget)
        self.spin_x.setMaximum(9999999)
        self.spin_x.setObjectName("spin_x")
        self.layout_pos.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.spin_x)
        self.lbl_y = QtWidgets.QLabel(self.centralwidget)
        self.lbl_y.setText("Y")
        self.lbl_y.setObjectName("lbl_y")
        self.layout_pos.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lbl_y)
        self.spin_y = QtWidgets.QSpinBox(self.centralwidget)
        self.spin_y.setMaximum(9999999)
        self.spin_y.setObjectName("spin_y")
        self.layout_pos.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.spin_y)
        self.lbl_w = QtWidgets.QLabel(self.centralwidget)
        self.lbl_w.setText("W")
        self.lbl_w.setObjectName("lbl_w")
        self.layout_pos.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.lbl_w)
        self.spin_w = QtWidgets.QSpinBox(self.centralwidget)
        self.spin_w.setMaximum(9999999)
        self.spin_w.setObjectName("spin_w")
        self.layout_pos.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.spin_w)
        self.lbl_h = QtWidgets.QLabel(self.centralwidget)
        self.lbl_h.setText("H")
        self.lbl_h.setObjectName("lbl_h")
        self.layout_pos.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.lbl_h)
        self.spin_h = QtWidgets.QSpinBox(self.centralwidget)
        self.spin_h.setMaximum(9999999)
        self.spin_h.setObjectName("spin_h")
        self.layout_pos.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.spin_h)
        self.btn_update_frame = QtWidgets.QPushButton(self.centralwidget)
        self.btn_update_frame.setObjectName("btn_update_frame")
        self.layout_pos.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.btn_update_frame)
        self.layout_tool.addLayout(self.layout_pos)
        self.layout_text = QtWidgets.QFormLayout()
        self.layout_text.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.layout_text.setObjectName("layout_text")
        self.lbl_text = QtWidgets.QLabel(self.centralwidget)
        self.lbl_text.setObjectName("lbl_text")
        self.layout_text.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lbl_text)
        self.txt_text = QtWidgets.QPlainTextEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_text.sizePolicy().hasHeightForWidth())
        self.txt_text.setSizePolicy(sizePolicy)
        self.txt_text.setMaximumSize(QtCore.QSize(150, 50))
        self.txt_text.setObjectName("txt_text")
        self.layout_text.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.txt_text)
        self.btn_update_text = QtWidgets.QPushButton(self.centralwidget)
        self.btn_update_text.setObjectName("btn_update_text")
        self.layout_text.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.btn_update_text)
        self.lbl_font = QtWidgets.QLabel(self.centralwidget)
        self.lbl_font.setObjectName("lbl_font")
        self.layout_text.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.lbl_font)
        self.cbx_font = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbx_font.sizePolicy().hasHeightForWidth())
        self.cbx_font.setSizePolicy(sizePolicy)
        self.cbx_font.setObjectName("cbx_font")
        self.layout_text.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.cbx_font)
        self.spin_font_size = QtWidgets.QSpinBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spin_font_size.sizePolicy().hasHeightForWidth())
        self.spin_font_size.setSizePolicy(sizePolicy)
        self.spin_font_size.setObjectName("spin_font_size")
        self.layout_text.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.spin_font_size)
        self.lbl_font_size = QtWidgets.QLabel(self.centralwidget)
        self.lbl_font_size.setObjectName("lbl_font_size")
        self.layout_text.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.lbl_font_size)
        self.cbx_text_style = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbx_text_style.sizePolicy().hasHeightForWidth())
        self.cbx_text_style.setSizePolicy(sizePolicy)
        self.cbx_text_style.setObjectName("cbx_text_style")
        self.layout_text.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.cbx_text_style)
        self.lbl_text_style = QtWidgets.QLabel(self.centralwidget)
        self.lbl_text_style.setObjectName("lbl_text_style")
        self.layout_text.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.lbl_text_style)
        self.lbl_translated_text = QtWidgets.QLabel(self.centralwidget)
        self.lbl_translated_text.setObjectName("lbl_translated_text")
        self.layout_text.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lbl_translated_text)
        self.txt_translated_text = QtWidgets.QPlainTextEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_translated_text.sizePolicy().hasHeightForWidth())
        self.txt_translated_text.setSizePolicy(sizePolicy)
        self.txt_translated_text.setMaximumSize(QtCore.QSize(150, 50))
        self.txt_translated_text.setObjectName("txt_translated_text")
        self.layout_text.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.txt_translated_text)
        self.lbl_alignment = QtWidgets.QLabel(self.centralwidget)
        self.lbl_alignment.setObjectName("lbl_alignment")
        self.layout_text.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.lbl_alignment)
        self.cbx_alignment = QtWidgets.QComboBox(self.centralwidget)
        self.cbx_alignment.setObjectName("cbx_alignment")
        self.layout_text.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.cbx_alignment)
        self.btn_update_style_to_all_bubble = QtWidgets.QPushButton(self.centralwidget)
        self.btn_update_style_to_all_bubble.setObjectName("btn_update_style_to_all_bubble")
        self.layout_text.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.btn_update_style_to_all_bubble)
        self.layout_tool.addLayout(self.layout_text)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.layout_tool.addItem(spacerItem)
        self.layout_main.addLayout(self.layout_tool)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setWindowTitle("toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionBubbleDetect = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icon/bubble-search"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBubbleDetect.setIcon(icon1)
        self.actionBubbleDetect.setObjectName("actionBubbleDetect")
        self.actionManualAddBubble = QtWidgets.QAction(MainWindow)
        self.actionManualAddBubble.setCheckable(True)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icon/bubble-add"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionManualAddBubble.setIcon(icon2)
        self.actionManualAddBubble.setObjectName("actionManualAddBubble")
        self.actionOCRAllBubble = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icon/ocr"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionOCRAllBubble.setIcon(icon3)
        self.actionOCRAllBubble.setObjectName("actionOCRAllBubble")
        self.actionTranslateAllBubble = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icon/translate"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTranslateAllBubble.setIcon(icon4)
        self.actionTranslateAllBubble.setObjectName("actionTranslateAllBubble")
        self.actionDisplayPreview = QtWidgets.QAction(MainWindow)
        self.actionDisplayPreview.setCheckable(True)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icon/show"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionDisplayPreview.setIcon(icon5)
        self.actionDisplayPreview.setObjectName("actionDisplayPreview")
        self.actionSaveAndNext = QtWidgets.QAction(MainWindow)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icon/save"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSaveAndNext.setIcon(icon6)
        self.actionSaveAndNext.setObjectName("actionSaveAndNext")
        self.actionSkipAndNext = QtWidgets.QAction(MainWindow)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icon/play"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSkipAndNext.setIcon(icon7)
        self.actionSkipAndNext.setObjectName("actionSkipAndNext")
        self.actionFullscreen = QtWidgets.QAction(MainWindow)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icon/full-screen"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFullscreen.setIcon(icon8)
        self.actionFullscreen.setObjectName("actionFullscreen")
        self.actionOpenFolder = QtWidgets.QAction(MainWindow)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/icon/open-folder"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionOpenFolder.setIcon(icon9)
        self.actionOpenFolder.setObjectName("actionOpenFolder")
        self.actionRefreshPreview = QtWidgets.QAction(MainWindow)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/icon/refresh-preview"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefreshPreview.setIcon(icon10)
        self.actionRefreshPreview.setObjectName("actionRefreshPreview")
        self.actionOCRThisBubble = QtWidgets.QAction(MainWindow)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(":/icon/ocr-bubble"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionOCRThisBubble.setIcon(icon11)
        self.actionOCRThisBubble.setObjectName("actionOCRThisBubble")
        self.actionTranslateThisBubble = QtWidgets.QAction(MainWindow)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap(":/icon/translate-bubble"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTranslateThisBubble.setIcon(icon12)
        self.actionTranslateThisBubble.setObjectName("actionTranslateThisBubble")
        self.toolBar.addAction(self.actionOpenFolder)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionBubbleDetect)
        self.toolBar.addAction(self.actionManualAddBubble)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionOCRAllBubble)
        self.toolBar.addAction(self.actionOCRThisBubble)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionTranslateAllBubble)
        self.toolBar.addAction(self.actionTranslateThisBubble)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionDisplayPreview)
        self.toolBar.addAction(self.actionRefreshPreview)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionSaveAndNext)
        self.toolBar.addAction(self.actionSkipAndNext)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionFullscreen)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Translator"))
        self.lbl_bubble_detect_engine.setText(_translate("MainWindow", "Bubble detect engine"))
        self.lbl_ocr__engine.setText(_translate("MainWindow", "OCR engine"))
        self.lbl_translator_engine.setText(_translate("MainWindow", "Translator engine"))
        self.lbl_language_from.setText(_translate("MainWindow", "Language from"))
        self.lbl_language_to.setText(_translate("MainWindow", "Language to"))
        self.btn_update_frame.setText(_translate("MainWindow", "Update frame"))
        self.lbl_text.setText(_translate("MainWindow", "Text"))
        self.btn_update_text.setText(_translate("MainWindow", "Update this bubble"))
        self.lbl_font.setText(_translate("MainWindow", "Font"))
        self.lbl_font_size.setText(_translate("MainWindow", "Font size"))
        self.lbl_text_style.setText(_translate("MainWindow", "Style"))
        self.lbl_translated_text.setText(_translate("MainWindow", "Translated text"))
        self.lbl_alignment.setText(_translate("MainWindow", "Alignment"))
        self.btn_update_style_to_all_bubble.setText(_translate("MainWindow", "Update style to all bubble"))
        self.actionBubbleDetect.setText(_translate("MainWindow", "Bubble Detect (F1)"))
        self.actionBubbleDetect.setToolTip(_translate("MainWindow", "Bubble Detect (F1)"))
        self.actionBubbleDetect.setShortcut(_translate("MainWindow", "F1"))
        self.actionManualAddBubble.setText(_translate("MainWindow", "Manual Add Bubble (F2)"))
        self.actionManualAddBubble.setToolTip(_translate("MainWindow", "Manual Add Bubble (F2)"))
        self.actionManualAddBubble.setShortcut(_translate("MainWindow", "F2"))
        self.actionOCRAllBubble.setText(_translate("MainWindow", "OCR All Bubble"))
        self.actionOCRAllBubble.setToolTip(_translate("MainWindow", "OCR All Bubble"))
        self.actionTranslateAllBubble.setText(_translate("MainWindow", "Translate All Bubble"))
        self.actionTranslateAllBubble.setToolTip(_translate("MainWindow", "Translate All Bubble"))
        self.actionDisplayPreview.setText(_translate("MainWindow", "Display Preview"))
        self.actionDisplayPreview.setToolTip(_translate("MainWindow", "Display Preview"))
        self.actionSaveAndNext.setText(_translate("MainWindow", "Save and Next (Ctrl+S)"))
        self.actionSaveAndNext.setToolTip(_translate("MainWindow", "Save and Next (Ctrl+S)"))
        self.actionSaveAndNext.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.actionSkipAndNext.setText(_translate("MainWindow", "Skip and Next"))
        self.actionSkipAndNext.setToolTip(_translate("MainWindow", "Skip and Next"))
        self.actionFullscreen.setText(_translate("MainWindow", "Toggle full screen (F11)"))
        self.actionFullscreen.setToolTip(_translate("MainWindow", "Toggle full screen (F11)"))
        self.actionFullscreen.setShortcut(_translate("MainWindow", "F11"))
        self.actionOpenFolder.setText(_translate("MainWindow", "Open Folder"))
        self.actionOpenFolder.setToolTip(_translate("MainWindow", "Open Folder"))
        self.actionRefreshPreview.setText(_translate("MainWindow", "Refresh Preview (F5)"))
        self.actionRefreshPreview.setToolTip(_translate("MainWindow", "Refresh Preview (F5)"))
        self.actionRefreshPreview.setShortcut(_translate("MainWindow", "F5"))
        self.actionOCRThisBubble.setText(_translate("MainWindow", "OCR This Bubble (F3)"))
        self.actionOCRThisBubble.setToolTip(_translate("MainWindow", "OCR This Bubble (F3)"))
        self.actionOCRThisBubble.setShortcut(_translate("MainWindow", "F3"))
        self.actionTranslateThisBubble.setText(_translate("MainWindow", "Translate This Bubble (F4)"))
        self.actionTranslateThisBubble.setToolTip(_translate("MainWindow", "Translate This Bubble (F4)"))
        self.actionTranslateThisBubble.setShortcut(_translate("MainWindow", "F4"))
from uis import resources_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())