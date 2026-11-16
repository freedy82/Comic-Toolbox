from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import Qt

from models.const import TRSM, WEB_BOT
from models.site import Site
from uis import help_window


class HelpWindowController(QtWidgets.QMainWindow):
    def __init__(self, app, main_controller):
        super().__init__()
        self.app = app
        self.main_controller = main_controller
        self.ui = help_window.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_control()

    def setup_control(self):
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        # GUI
        self.retranslateUi()

        # action

    def retranslateUi(self):
        self.ui.retranslateUi(self)
        self._update_sites()
        self._update_other()

    # action
    def accept(self):
        self.close()

    def reject(self):
        pass

    def center_pos_of_parent(self):
        qr = self.main_controller.frameGeometry()
        x = qr.left() + (qr.width() - self.width()) // 2
        y = qr.top() + (qr.height() - self.height()) // 2
        self.move(x, y)

    # internal
    def _update_sites(self):
        self.ui.txt_supported_site.clear()
        site_objs = Site.get_all_sites_object(WEB_BOT)
        for site_obj in site_objs:
            self.ui.txt_supported_site.append(TRSM("Site: %s") % site_obj.get_site_name())
            url = site_obj.get_home_url()
            self.ui.txt_supported_site.append(TRSM("URL: <a href='%s'>%s</a>") % (url, url))
            if site_obj.get_is_need_nodejs():
                self.ui.txt_supported_site.append(
                    "<div style='color:#FF0000'>" + TRSM("Install Node.js was required for this site") + "</div>"
                )
            sample_urls = site_obj.get_sample_url()
            self.ui.txt_supported_site.append(TRSM("Sample URL:"))
            for sample_url in sample_urls:
                self.ui.txt_supported_site.append(sample_url)
            self.ui.txt_supported_site.append("")
        self.ui.txt_supported_site.moveCursor(QtGui.QTextCursor.MoveOperation.Start)

    def _update_other(self):
        self.ui.txt_other.clear()
        self.ui.txt_other.append(
            TRSM("For converter, cropper, archiver, please select the folder of comic series before scan")
        )
        self.ui.txt_other.append(TRSM("For example:"))
        self.ui.txt_other.append(TRSM("📁 d:\\comics\\  (Download folder)"))
        self.ui.txt_other.append(TRSM("📁 d:\\comics\\book_name\\  (Series folder)"))
        self.ui.txt_other.append(TRSM("📁 d:\\comics\\book_name\\chapter-##\\  (Chapter/Book folder)"))
        self.ui.txt_other.append(TRSM("🖼 d:\\comics\\book_name\\chapter-##\\###.jpg  (Image file)"))
        self.ui.txt_other.append("")
        self.ui.txt_other.append(
            TRSM(
                "Converter destination folder suggest use different with source folder, even it should be work, but for safe reason😅"
            )
        )

        self.ui.txt_other.moveCursor(QtGui.QTextCursor.MoveOperation.Start)

    def show(self):
        super().show()
        self.center_pos_of_parent()

    @staticmethod
    def setModal(is_modal):
        pass
