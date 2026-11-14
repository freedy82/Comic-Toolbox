"""Qt6 verification browser, kept in a separate process from the application."""

import json
import sys
import threading
from urllib.parse import urlsplit

from PyQt6 import QtCore, QtGui, QtWidgets, sip
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

from models.webbot import is_browser_challenge
from models.theme import apply_color_scheme
from uis import resources_rc


class BrowserPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        # Website scripts must not write session data to application logs.
        pass


class BrowserSession(QtCore.QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.profile = QWebEngineProfile(self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        self.cookies = {}
        store = self.profile.cookieStore()
        store.cookieAdded.connect(self._added)
        store.cookieRemoved.connect(self._removed)

    @staticmethod
    def _key(cookie):
        return (cookie.domain(), cookie.path(), bytes(cookie.name()))

    def _added(self, cookie):
        self.cookies[self._key(cookie)] = {
            "name": bytes(cookie.name()).decode("latin-1"),
            "value": bytes(cookie.value()).decode("latin-1"),
            "domain": cookie.domain(), "path": cookie.path() or "/",
            "secure": cookie.isSecure(), "http_only": cookie.isHttpOnly(),
            "expires": None if cookie.isSessionCookie() else cookie.expirationDate().toSecsSinceEpoch(),
        }

    def _removed(self, cookie):
        self.cookies.pop(self._key(cookie), None)

    def export(self, url):
        host = urlsplit(url).hostname or ""
        return [dict(cookie) for cookie in self.cookies.values()
                if host == cookie["domain"].lstrip(".")
                or (cookie["domain"].startswith(".") and host.endswith(cookie["domain"]))]


class VerificationDialog(QtWidgets.QDialog):
    def __init__(self, command, session):
        super().__init__()
        self.url = command["url"]
        self.session = session
        self._messages = command["messages"]
        self.captured_result = None
        self._loading = True
        self._closed = False
        self.setWindowTitle(self.tr_text("Website verification"))
        self.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint, False)
        layout = QtWidgets.QVBoxLayout(self)
        explanation = QtWidgets.QLabel(self.tr_text(
            "Wait for the website to finish its security check. If a verification control appears, complete it. When the comic page appears, click Continue. Cookies stay in memory until Comic Toolbox closes."
        ))
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.address = QtWidgets.QLineEdit(self.url)
        self.address.setReadOnly(True)
        layout.addWidget(self.address)
        self.browser = QWebEngineView(self)
        self.browser.setPage(BrowserPage(session.profile, self.browser))
        self.browser.urlChanged.connect(lambda url: self.address.setText(url.toString()))
        self.browser.loadStarted.connect(self._load_started)
        self.browser.loadFinished.connect(self._load_finished)
        self.browser.page().renderProcessTerminated.connect(self._render_stopped)
        layout.addWidget(self.browser, 1)
        self.status = QtWidgets.QLabel(self.tr_text("Loading website…"))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QtWidgets.QDialogButtonBox(self)
        self.continue_button = buttons.addButton(self.tr_text("Continue"), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        reload_button = buttons.addButton(self.tr_text("Reload"), QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.tr_text("Cancel"), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.continue_button.setEnabled(False)
        reload_button.clicked.connect(self.browser.reload)
        buttons.accepted.connect(self._capture)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.stall_timer = QtCore.QTimer(self)
        self.stall_timer.setSingleShot(True)
        self.stall_timer.setInterval(20000)
        self.stall_timer.timeout.connect(self._check_stalled)
        screen = self.screen().availableGeometry()
        self.resize(min(1100, int(screen.width() * 0.9)), min(850, int(screen.height() * 0.9)))
        self.browser.load(QtCore.QUrl(self.url))

    def tr_text(self, source):
        return self._messages.get(source, source)

    def _load_started(self):
        if self._closed:
            return
        self._loading = True
        self.continue_button.setEnabled(False)
        self.status.setText(self.tr_text("Loading website…"))
        self.stall_timer.start()

    def _load_finished(self, ok):
        if self._closed:
            return
        self._loading = False
        self.continue_button.setEnabled(ok)
        self.status.setText(self.tr_text(
            "Complete any verification shown by the website, then click Continue when the comic page appears."
            if ok else "The page could not load. You can reload or cancel."
        ))
        if ok:
            self.stall_timer.start()

    def _render_stopped(self, termination_status, exit_code):
        if not self._closed:
            self.continue_button.setEnabled(False)
            self.status.setText(self.tr_text("The browser stopped displaying this page. Try Reload or cancel."))

    def _check_stalled(self):
        if not self._closed:
            self.browser.page().toHtml(self._stalled_html)

    def _stalled_html(self, html):
        if not self._closed and html and is_browser_challenge({}, html.encode("utf-8")):
            self.status.setText(self.tr_text(
                "The site is still checking this browser. If no verification control appears, try Reload. The site may not support embedded browsers."
            ))

    def _correct_origin(self):
        expected = urlsplit(self.url)
        actual = urlsplit(self.browser.url().toString())
        return (actual.scheme, actual.hostname, actual.port) == (expected.scheme, expected.hostname, expected.port)

    def _capture(self):
        if self._loading or self._closed:
            return
        if not self._correct_origin():
            self.status.setText(self.tr_text("Return to the requested website before clicking Continue."))
            return
        self.continue_button.setEnabled(False)
        self.browser.page().toHtml(self._captured)

    def _captured(self, html):
        if self._closed:
            return
        self.continue_button.setEnabled(True)
        if not self._correct_origin():
            self.status.setText(self.tr_text("Return to the requested website before clicking Continue."))
            return
        if self._loading or not html or is_browser_challenge({}, html.encode("utf-8")):
            self.status.setText(self.tr_text("The verification page is still showing. Complete the check before continuing."))
            return
        self.captured_result = {
            "cookies": self.session.export(self.url),
            "user_agent": self.session.profile.httpUserAgent(),
            "url": self.browser.url().toString(), "html": html,
        }
        self.accept()

    def done(self, result):
        self._closed = True
        self.stall_timer.stop()
        self.browser.stop()
        super().done(result)


class BrowserHost(QtCore.QObject):
    command_received = QtCore.pyqtSignal(object)

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.sessions = {}
        self.dialog = None
        self.qt_translator = QtCore.QTranslator(self)
        self.command_received.connect(self._dispatch, QtCore.Qt.ConnectionType.QueuedConnection)

    def read_commands(self):
        for line in sys.stdin.buffer:
            try:
                command = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            self.command_received.emit(command)
        self.command_received.emit({"command": "quit"})

    @QtCore.pyqtSlot(object)
    def _dispatch(self, command):
        if command.get("command") == "quit":
            if self.dialog is not None:
                self.dialog.reject()
            self.app.quit()
            return
        if command.get("command") != "verify":
            return
        messages = command.get("messages", {})
        reply = {"type": "result", "result": None, "error": ""}
        try:
            parsed = urlsplit(command["url"])
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise ValueError("Invalid website URL")
            locale = QtCore.QLocale(command["language"])
            QtCore.QLocale.setDefault(locale)
            self.app.removeTranslator(self.qt_translator)
            translations_dir = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.TranslationsPath)
            if self.qt_translator.load(locale, "qtbase", "_", translations_dir):
                self.app.installTranslator(self.qt_translator)
            font = QtGui.QFont(command["font_family"])
            if command["font_size"] > 0:
                font.setPointSizeF(command["font_size"])
            self.app.setFont(font)
            apply_color_scheme(self.app, command.get("theme", "default"))
            self.app.setStyleSheet(command.get("stylesheet", ""))
            session = self.sessions.get(parsed.netloc)
            if session is None:
                session = BrowserSession(self)
                self.sessions[parsed.netloc] = session
            session.profile.setHttpAcceptLanguage(locale.bcp47Name())
            self.dialog = VerificationDialog(command, session)
            if self.dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                reply["result"] = self.dialog.captured_result
            else:
                source = "Website verification was cancelled."
                reply["error"] = messages.get(source, source)
        except Exception as exc:
            source = "The verification browser could not start."
            reply["error"] = messages.get(source, source)
            reply["diagnostic"] = type(exc).__name__ + ": " + str(exc)
        finally:
            if self.dialog is not None:
                # Destroy pages before the profiles, including during app shutdown.
                self.dialog._closed = True
                sip.delete(self.dialog)
                self.dialog = None
        sys.stdout.buffer.write((json.dumps(reply, ensure_ascii=True) + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()


def main():
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(":/icon/main_icon"))
    app.setQuitOnLastWindowClosed(False)
    host = BrowserHost(app)
    threading.Thread(target=host.read_commands, daemon=True).start()
    exit_code = app.exec()
    sip.delete(host)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
