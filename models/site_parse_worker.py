from PyQt5.QtCore import QThread, pyqtSignal


class SiteParseWorker(QThread):
	# trigger = pyqtSignal(str)
	finished = pyqtSignal(object)

	def __init__(self, site):
		super().__init__()
		self.site = site

	def run(self):
		item_lists = self.site.parse_list()

		self.finished.emit(item_lists)
