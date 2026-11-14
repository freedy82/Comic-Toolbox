from PyQt6.QtCore import QThread, pyqtSignal
from models.const import TRSM


class SiteParseWorker(QThread):
	# trigger = pyqtSignal(str)
	finished = pyqtSignal(object)
	page_trigger = pyqtSignal(str)

	def __init__(self, site):
		super().__init__()
		self.site = site

	def run(self):
		self.site.page_trigger.connect(self.parse_site_page_trigger)
		try:
			item_lists = self.site.parse_list()
		except Exception as exc:
			item_lists = {"title": "", "author": "", "message": TRSM(str(exc))}
		finally:
			self.site.page_trigger.disconnect(self.parse_site_page_trigger)
		self.finished.emit(item_lists)

	def parse_site_page_trigger(self,page_no):
		self.page_trigger.emit(page_no)
