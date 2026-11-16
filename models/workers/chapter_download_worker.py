from threading import Event

from PyQt6.QtCore import QThread, pyqtSignal

from models.const import MY_CONFIG, TRSM


class ChapterDownloadWorker(QThread):
    trigger = pyqtSignal(str, int, int, int, int)

    def __init__(self, site, items, title="", current_type="", is_overwrite=False, parent=None):
        super().__init__(parent)
        self.site = site
        self.items = items
        self.title = title
        self.current_type = current_type
        self.finish_page = 0
        self.total_page = 0
        self.finish_chapter = 0
        self.total_chapter = 0
        self.is_overwrite = is_overwrite

        self.stop_flag = False
        self.was_canceled = False
        self._cancel_event = Event()

    def run(self):
        connected = False
        try:
            self.site.chapter_trigger.connect(self.chapter_trigger)
            connected = True
            self._download_chapters()
        except Exception as error:
            self.trigger.emit(str(error), self.finish_page, self.total_page, self.finish_chapter, self.total_chapter)
            self.stop()
        finally:
            if connected:
                self.site.chapter_trigger.disconnect(self.chapter_trigger)
            self.was_canceled = self.stop_flag

    def _download_chapters(self):
        self.finish_page = 0
        self.total_page = 0
        self.finish_chapter = 0
        self.total_chapter = len(self.items)
        self.site.set_is_overwrite(self.is_overwrite)
        page_sleep = float(MY_CONFIG.get("anti-ban", "page_sleep"))

        for idx, temp_item in enumerate(self.items):
            if self.stop_flag:
                break
            try:
                self.site.download_item(item=temp_item, title=self.title, item_type=self.current_type)
            except Exception as exc:
                self.trigger.emit(
                    TRSM(str(exc)), self.finish_page, self.total_page, self.finish_chapter, self.total_chapter
                )
                self.stop()
            if self.site._stop_flag:
                self.stop_flag = True
            if self.stop_flag:
                break
            self.finish_chapter = idx + 1
            if not self.stop_flag:
                message = TRSM("Finish %s item %d") % (TRSM(self.current_type), self.finish_chapter)
                self.trigger.emit(message, self.total_page, self.total_page, self.finish_chapter, self.total_chapter)

                if page_sleep > 0.0:
                    message = TRSM("Page sleep %0.1fs") % page_sleep
                    self.trigger.emit(
                        message, self.total_page, self.total_page, self.finish_chapter, self.total_chapter
                    )
                    if self._cancel_event.wait(page_sleep):
                        break

    def chapter_trigger(self, message, current_page, total_page):
        self.finish_page = current_page
        self.total_page = total_page
        self.trigger.emit(message, self.finish_page, self.total_page, self.finish_chapter, self.total_chapter)

    def stop(self):
        self.stop_flag = True
        self.requestInterruption()
        self._cancel_event.set()
        self.site.stop()
