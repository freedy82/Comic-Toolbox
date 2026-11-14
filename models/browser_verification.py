"""Run the verification browser over private process pipes."""

import json
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from models.const import MY_CONFIG, TRSM
from models.verification_messages import VERIFICATION_MESSAGES
from models.webbot import BrowserVerificationError


@dataclass
class VerificationRequest:
    url: str
    done: threading.Event = field(default_factory=threading.Event)
    result: dict = None
    error: str = ""


class BrowserVerificationBroker(QtCore.QObject):
    requested = QtCore.pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self._requests = []
        self._lock = threading.Lock()
        self._active = None
        self._loop = None
        self._process = None
        self._output = bytearray()
        self._command = None
        self._closing = False
        self.requested.connect(self._show, QtCore.Qt.ConnectionType.QueuedConnection)
        QtWidgets.QApplication.instance().aboutToQuit.connect(self._shutdown)

    def verify(self, url):
        request = VerificationRequest(url)
        with self._lock:
            if self._closing:
                raise BrowserVerificationError(TRSM("Website verification was cancelled."))
            self._requests.append(request)
        if QtCore.QThread.currentThread() == self.thread():
            self._show(request)
        else:
            self.requested.emit(request)
        request.done.wait()
        if request.error:
            raise BrowserVerificationError(request.error)
        return request.result

    @QtCore.pyqtSlot(object)
    def _show(self, request):
        parent_was_enabled = self.parent().isEnabled()
        try:
            if self._closing or request.done.is_set():
                return
            self._active = request
            self._loop = QtCore.QEventLoop(self)
            self.parent().setEnabled(False)
            app = QtWidgets.QApplication.instance()
            font = app.font()
            self._command = {
                "command": "verify", "url": request.url,
                "language": MY_CONFIG.get("general", "language"),
                "theme": MY_CONFIG.get("general", "theme"),
                "messages": {source: TRSM(source) for source in VERIFICATION_MESSAGES},
                "font_family": font.family(), "font_size": font.pointSizeF(),
                "stylesheet": app.styleSheet(),
            }
            if self._process is None or self._process.state() == QtCore.QProcess.ProcessState.NotRunning:
                self._start_browser()
            elif self._process.state() == QtCore.QProcess.ProcessState.Running:
                self._send_command()
            if not request.done.is_set():
                self._loop.exec()
        except Exception as exc:
            request.error = TRSM("The verification browser could not start.")
            request.error += "\n" + TRSM("Details: %s") % (type(exc).__name__ + ": " + str(exc))
        finally:
            self._active = None
            self._command = None
            if self._loop is not None:
                self._loop.deleteLater()
                self._loop = None
            self.parent().setEnabled(parent_was_enabled)
            with self._lock:
                if request in self._requests:
                    self._requests.remove(request)
            request.done.set()

    def _start_browser(self):
        if self._process is not None:
            self._process.deleteLater()
        self._output.clear()
        self._process = QtCore.QProcess(self)
        # Qt6 must discover its own plugins, resources and subprocess executable.
        environment = QtCore.QProcessEnvironment.systemEnvironment()
        for name in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "QML2_IMPORT_PATH",
                     "QML_IMPORT_PATH", "QTWEBENGINEPROCESS_PATH", "QTWEBENGINE_RESOURCES_PATH",
                     "QTWEBENGINE_LOCALES_PATH"):
            environment.remove(name)
        self._process.setProcessEnvironment(environment)
        self._process.setWorkingDirectory(str(Path(__file__).resolve().parent.parent))
        self._process.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.SeparateChannels)
        # Use Qt's native null-device path for Windows process redirection.
        self._process.setStandardErrorFile(QtCore.QProcess.nullDevice())
        self._process.started.connect(self._send_command)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.errorOccurred.connect(self._process_error)
        self._process.finished.connect(self._process_finished)
        self._process.start(sys.executable, ["-m", "models.browser_verification_helper"])

    def _send_command(self):
        if self._command is not None:
            self._process.write((json.dumps(self._command, ensure_ascii=True) + "\n").encode("utf-8"))
            self._command = None

    def _read_output(self):
        # Cookie values travel only through captured pipes, never console or files.
        self._output.extend(bytes(self._process.readAllStandardOutput()))
        while b"\n" in self._output:
            line, _, remaining = self._output.partition(b"\n")
            self._output = bytearray(remaining)
            try:
                message = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if self._active is None or message.get("type") != "result":
                continue
            self._active.result = message.get("result")
            self._active.error = message.get("error", "")
            if message.get("diagnostic"):
                self._active.error += "\n" + TRSM("Details: %s") % message["diagnostic"]
            if not self._active.result and not self._active.error:
                self._active.error = TRSM("Website verification was cancelled.")
            self._active.done.set()
            if self._loop is not None:
                self._loop.quit()

    def _fail_active(self, source, details=""):
        if self._active is not None and not self._active.done.is_set():
            self._active.error = TRSM(source)
            if details:
                self._active.error += "\n" + details
            self._active.done.set()
            if self._loop is not None:
                self._loop.quit()

    def _process_error(self, error):
        if error == QtCore.QProcess.ProcessError.FailedToStart:
            self._fail_active("The verification browser could not start.",
                              TRSM("Details: %s") % self._process.errorString())

    def _process_finished(self, exit_code, exit_status):
        self._read_output()
        if self._active is not None and not self._active.done.is_set():
            self._fail_active("The verification browser closed unexpectedly. Please try again.",
                              TRSM("Browser exit code: %s") % f"0x{exit_code & 0xFFFFFFFF:08X}")

    def _shutdown(self):
        with self._lock:
            self._closing = True
            for request in self._requests:
                request.error = TRSM("Website verification was cancelled.")
                request.done.set()
        if self._loop is not None:
            self._loop.quit()
        if self._process is not None and self._process.state() != QtCore.QProcess.ProcessState.NotRunning:
            self._process.write(b'{"command":"quit"}\n')
            self._process.closeWriteChannel()
            if not self._process.waitForFinished(2000):
                self._process.kill()
