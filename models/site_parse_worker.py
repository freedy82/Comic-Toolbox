from PyQt5.QtCore import QThread, pyqtSignal


class SiteParseWorker(QThread):
	# trigger = pyqtSignal(str)
	finished = pyqtSignal(object)
	page_trigger = pyqtSignal(str)

	def __init__(self, site):
		super().__init__()
		self.site = site

	def run(self):
		self.site.page_trigger.connect(self.parse_site_page_trigger)
		item_lists = self.site.parse_list()
		self.site.page_trigger.disconnect(self.parse_site_page_trigger)
		self.finished.emit(item_lists)

	def parse_site_page_trigger(self,page_no):
		self.page_trigger.emit(page_no)
