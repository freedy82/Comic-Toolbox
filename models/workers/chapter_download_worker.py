import time
from PyQt5.QtCore import QThread, pyqtSignal

from models.const import *

class ChapterDownloadWorker(QThread):
	trigger = pyqtSignal(str, int, int, int, int)
	canceled = pyqtSignal()
	finished = pyqtSignal()

	def __init__(self, site,items,title="",author="",current_type="",is_overwrite=False):
		super().__init__()
		self.site = site
		self.items = items
		self.title = title
		self.author = author
		self.current_type = current_type
		self.finish_page = 0
		self.total_page = 0
		self.finish_chapter = 0
		self.total_chapter = 0
		self.is_overwrite = is_overwrite

		self.stop_flag = False

	def run(self):
		self.finish_page = 0
		self.total_page = 0
		self.finish_chapter = 0
		self.total_chapter = len(self.items)
		self.site.chapter_trigger.connect(self.chapter_trigger)
		self.site.chapter_finished.connect(self.chapter_finished)
		self.stop_flag = False
		self.site.set_is_overwrite(self.is_overwrite)
		page_sleep = float(MY_CONFIG.get("anti-ban", "page_sleep"))

		for idx, temp_item in enumerate(self.items):
			if self.stop_flag:
				break
			self.site.download_item(item=temp_item, title=self.title, item_type=self.current_type)
			#util.process_book_item(site=self.site,item=temp_item,book_title=self.title,author=self.author,item_type=self.current_type)
			self.finish_chapter = idx + 1
			if not self.stop_flag:
				message = TRSM("Finish %s item %d") % (TRSM(self.current_type), self.finish_chapter)
				self.trigger.emit(message,self.total_page,self.total_page,self.finish_chapter,self.total_chapter)

				if page_sleep > 0.0:
					message = TRSM("Page sleep %0.1fs") % page_sleep
					#print(message)
					self.trigger.emit(message,self.total_page,self.total_page,self.finish_chapter,self.total_chapter)
					#sys.stdout.flush()
					time.sleep(page_sleep)

		if not self.stop_flag:
			self.finished.emit()
		else:
			self.canceled.emit()
		self.site.chapter_trigger.disconnect(self.chapter_trigger)
		self.site.chapter_finished.disconnect(self.chapter_finished)

	def chapter_trigger(self,message,current_page,total_page):
		self.finish_page = current_page
		self.total_page = total_page
		self.trigger.emit(message, self.finish_page, self.total_page, self.finish_chapter, self.total_chapter)
		pass

	def chapter_finished(self):
		pass

	def stop(self):
		self.stop_flag = True
		self.site.stop()
