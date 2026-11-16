from PyQt6.QtCore import QThread, pyqtSignal

from models.const import TRSM


class SiteParseWorker(QThread):
    page_trigger = pyqtSignal(str)

    def __init__(self, site, parent=None):
        super().__init__(parent)
        self.site = site
        self.result = {}

    def run(self):
        self.site.page_trigger.connect(self.parse_site_page_trigger)
        try:
            self.result = self.site.parse_list()
        except Exception as exc:
            self.result = {"title": "", "author": "", "message": TRSM(str(exc))}
        finally:
            self.site.page_trigger.disconnect(self.parse_site_page_trigger)

    def stop(self):
        self.requestInterruption()
        self.site.stop()

    def parse_site_page_trigger(self, page_no):
        self.page_trigger.emit(page_no)
