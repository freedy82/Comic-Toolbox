from PyQt6.QtCore import QThread, pyqtSignal

from models.colorize import ColorizeCanceled, ColorizeError, download_model
from models.const import TRSM


class ColorizeDownloadWorker(QThread):
    progress = pyqtSignal(object, object)
    downloaded = pyqtSignal(str)
    failed = pyqtSignal(str)
    canceled = pyqtSignal()

    def __init__(self, model, folder, parent=None):
        super().__init__(parent)
        self.model = model
        self.folder = folder

    def run(self):
        try:
            path = download_model(self.model, self.folder, self.progress.emit, self.isInterruptionRequested)
            self.downloaded.emit(str(path))
        except ColorizeCanceled:
            self.canceled.emit()
        except Exception as error:
            details = error.translated(TRSM) if isinstance(error, ColorizeError) else str(error)
            self.failed.emit(details)

    def stop(self):
        self.requestInterruption()
