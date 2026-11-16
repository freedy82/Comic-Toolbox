from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.colorize import DEFAULT_MODEL, DEFAULT_MODELS_FOLDER, MODELS
from models.const import MY_CONFIG, TRSM
from models.theme import apply_native_progress_bar
from models.workers.colorize_download_worker import ColorizeDownloadWorker


class ColorizeSettings(QWidget):
    def __init__(self, app, tabs):
        super().__init__(tabs)
        self.tabs = tabs
        self.worker = None
        self._status_message = None
        self.setObjectName("tab_settings_colorize")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        if hasattr(app, "_native_layout_margins"):
            layout.setContentsMargins(app._native_layout_margins)
            layout.setSpacing(app._native_layout_spacing)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.addLayout(form)
        self.note = QLabel()
        self.note.setWordWrap(True)
        form.addRow(self.note)
        self.folder_label = QLabel()
        self.folder = QLineEdit()
        self.browse = QPushButton()
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.folder)
        row.addWidget(self.browse)
        form.addRow(self.folder_label, row)
        self.model_label = QLabel()
        self.model = QComboBox()
        for key, definition in MODELS.items():
            self.model.addItem(definition.name, key)
        form.addRow(self.model_label, self.model)
        self.use_gpu = QCheckBox()
        self.use_gpu.setChecked(True)
        form.addRow("", self.use_gpu)
        self.model_info = QLabel()
        self.model_info.setWordWrap(True)
        form.addRow("", self.model_info)
        self.model_source = QLabel()
        self.model_source.setOpenExternalLinks(True)
        form.addRow("", self.model_source)
        self.download = QPushButton()
        self.cancel = QPushButton()
        self.cancel.setEnabled(False)
        actions = QHBoxLayout()
        actions.addWidget(self.download)
        actions.addWidget(self.cancel)
        actions.addStretch()
        form.addRow("", actions)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        apply_native_progress_bar(app, self.progress)
        form.addRow("", self.progress)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("", self.status)
        layout.addStretch()
        self.tabs.insertTab(self.tabs.count() - 1, self, TRSM("Colorize"))
        self.model.currentIndexChanged.connect(self._selection_changed)
        self.folder.textChanged.connect(self._selection_changed)
        self.browse.clicked.connect(self._browse)
        self.download.clicked.connect(self._download)
        self.cancel.clicked.connect(self._cancel)
        app.aboutToQuit.connect(self.shutdown)
        self.retranslateUi()

    def _selection_changed(self):
        self._status_message = None
        self._refresh_model()
        self.status.clear()

    def _refresh_model(self):
        definition = MODELS[self.model.currentData() or DEFAULT_MODEL]
        folder = Path(self.folder.text().strip() or DEFAULT_MODELS_FOLDER).expanduser()
        path = folder / definition.filename
        try:
            downloaded = path.is_file() and path.stat().st_size == definition.size
        except (OSError, ValueError):
            downloaded = False
        self.model_info.setText(
            TRSM("Download size: %s MB | %s")
            % ("%.0f" % (definition.size / 1024**2), TRSM("Downloaded") if downloaded else TRSM("Not downloaded"))
        )
        self.model_source.setText('<a href="%s">%s</a>' % (definition.url, TRSM("Model download source")))

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(
            self, TRSM("Models folder"), self.folder.text() or DEFAULT_MODELS_FOLDER
        )
        if folder:
            self.folder.setText(folder)

    def _set_status(self, message, *values):
        self._status_message = (message, values)
        text = TRSM(message)
        self.status.setText(text % values if values else text)

    def _download(self):
        if self.worker is not None:
            return
        folder = self.folder.text().strip() or DEFAULT_MODELS_FOLDER
        self.folder.setText(folder)
        self.progress.setValue(0)
        self.progress.show()
        self._set_status("Downloading %s...", MODELS[self.model.currentData()].name)
        self.worker = ColorizeDownloadWorker(self.model.currentData(), folder, self)
        self.worker.progress.connect(self._download_progress)
        self.worker.downloaded.connect(self._downloaded)
        self.worker.failed.connect(self._download_failed)
        self.worker.canceled.connect(self._download_canceled)
        self.worker.finished.connect(self._download_finished)
        self._set_busy(True)
        self.worker.start()

    def _download_progress(self, received, total):
        self.progress.setValue(min(100, int(received * 100 / total)) if total else 0)

    def _downloaded(self, path):
        self.progress.setValue(100)
        self._refresh_model()
        self._set_status("Model downloaded. Click Save to use this model in Converter.")

    def _download_failed(self, details):
        self._set_status("Model download failed: %s", details)

    def _download_canceled(self):
        self._set_status("Model download canceled.")

    def _download_finished(self):
        worker = self.worker
        self.worker = None
        if worker is not None:
            worker.deleteLater()
        self._set_busy(False)

    def _cancel(self):
        if self.worker is not None:
            self.worker.stop()
            self.cancel.setEnabled(False)
            self._set_status("Canceling model download...")

    def _set_busy(self, busy):
        for control in (self.model, self.folder, self.browse, self.download):
            control.setEnabled(not busy)
        self.cancel.setEnabled(busy)

    def shutdown(self):
        if self.worker is not None:
            self.worker.stop()
            self.worker.wait()

    def retranslateUi(self):
        self.tabs.setTabText(self.tabs.indexOf(self), TRSM("Colorize"))
        self.note.setText(
            TRSM(
                "Download a DeOldify or DDColor model, then click Save. Choose Colorize in Converter to colorize images locally. Image dimensions are preserved."
            )
            + "\n"
            + TRSM(
                "Pages already in color skip AI recoloring. Matching formats are copied when image filters are disabled."
            )
        )
        self.folder_label.setText(TRSM("Models folder"))
        self.browse.setText(TRSM("Browser"))
        self.model_label.setText(TRSM("Model"))
        self.use_gpu.setText(TRSM("Use GPU acceleration (when available)"))
        self.use_gpu.setToolTip(
            TRSM(
                "Enabled by default. Uses a supported GPU; falls back to CPU if GPU acceleration is unavailable. Turn off to use CPU only."
            )
        )
        self.download.setText(TRSM("Download selected model"))
        self.cancel.setText(TRSM("Cancel"))
        self._refresh_model()
        if self._status_message:
            message, values = self._status_message
            self._set_status(message, *values)

    def load_config(self):
        if self.worker is not None:
            return
        self.folder.setText(MY_CONFIG.get("colorize", "models_folder") or DEFAULT_MODELS_FOLDER)
        self.model.setCurrentIndex(max(0, self.model.findData(MY_CONFIG.get("colorize", "model") or DEFAULT_MODEL)))
        self.use_gpu.setChecked(MY_CONFIG.get("colorize", "use_gpu").strip().lower() not in ("false", "0", "no", "off"))
        self._refresh_model()

    def save_config(self):
        MY_CONFIG.set("colorize", "model", self.model.currentData())
        MY_CONFIG.set("colorize", "models_folder", self.folder.text().strip() or DEFAULT_MODELS_FOLDER)
        MY_CONFIG.set("colorize", "use_gpu", "True" if self.use_gpu.isChecked() else "False")

    def reset_defaults(self):
        if self.worker is not None:
            return
        self.folder.setText(DEFAULT_MODELS_FOLDER)
        self.model.setCurrentIndex(self.model.findData(DEFAULT_MODEL))
        self.use_gpu.setChecked(True)
