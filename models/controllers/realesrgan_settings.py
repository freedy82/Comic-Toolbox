from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox,
                             QSpinBox, QCheckBox, QFileDialog)

from models.const import MY_CONFIG, TRSM
from models.realesrgan import MODELS, DEFAULT_MODEL, model_scales


class RealESRGANSettings(QWidget):
    def __init__(self, app, tabs):
        super().__init__(tabs)
        self.tabs = tabs
        self.setObjectName("tab_settings_esrgan")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Match the other settings pages: the tab supplies the background,
        # without a scroll viewport filling it with the window background.
        layout = QVBoxLayout(self)
        if hasattr(app, "_native_layout_margins"):
            layout.setContentsMargins(app._native_layout_margins)
            layout.setSpacing(app._native_layout_spacing)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.addLayout(form)
        self.download_label = QLabel()
        self.download_link = QLabel('<a href="https://github.com/xinntao/Real-ESRGAN">https://github.com/xinntao/Real-ESRGAN</a>')
        self.download_link.setTextFormat(Qt.TextFormat.RichText)
        self.download_link.setOpenExternalLinks(True)
        self.download_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        form.addRow(self.download_label, self.download_link)
        self.path_note = QLabel()
        self.path_note.setWordWrap(True)
        form.addRow(self.path_note)
        self.exe_label = QLabel()
        self.exe = QLineEdit()
        self.exe.setObjectName("txt_settings_esrgan_location")
        self.exe_browse = QPushButton()
        self._path_row(form, self.exe_label, self.exe, self.exe_browse)
        self.folder_label = QLabel()
        self.folder = QLineEdit()
        self.folder_browse = QPushButton()
        self._path_row(form, self.folder_label, self.folder, self.folder_browse)
        self.model_label = QLabel()
        self.model = QComboBox()
        for name in MODELS:
            self.model.addItem(name, name)
        form.addRow(self.model_label, self.model)
        self.scale_label = QLabel()
        self.scale = QComboBox()
        form.addRow(self.scale_label, self.scale)
        self.tile_label = QLabel()
        self.tile = QSpinBox()
        self.tile.setRange(0, 4096)
        self.tile.setSingleStep(32)
        form.addRow(self.tile_label, self.tile)
        self.restore_size = QCheckBox()
        form.addRow("", self.restore_size)
        layout.addStretch()

        self.model.currentIndexChanged.connect(self._model_changed)
        self.exe_browse.clicked.connect(self._browse_executable)
        self.folder_browse.clicked.connect(self._browse_folder)
        self.tabs.insertTab(self.tabs.count() - 1, self, "Real-ESRGAN")
        self._model_changed()
        self.retranslateUi()

    @staticmethod
    def _path_row(form, label, field, button):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(field)
        row.addWidget(button)
        form.addRow(label, row)

    def _model_changed(self):
        old_scale = self.scale.currentData() or 4
        self.scale.clear()
        for scale in model_scales(self.model.currentData()):
            self.scale.addItem("%dx" % scale, scale)
        index = self.scale.findData(old_scale)
        self.scale.setCurrentIndex(index if index >= 0 else self.scale.count() - 1)

    def _browse_executable(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, TRSM("Real-ESRGAN executable"), self.exe.text() or "./",
            "Real-ESRGAN (realesrgan-ncnn-vulkan.exe);;All files (*)")
        if filename:
            self.exe.setText(filename)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, TRSM("Models folder"), self.folder.text() or "./")
        if folder:
            self.folder.setText(folder)

    def retranslateUi(self):
        self.tabs.setTabText(self.tabs.indexOf(self), "Real-ESRGAN")
        self.download_label.setText(TRSM("Can download from"))
        self.path_note.setText(TRSM("Use English (ASCII) characters for folder and file names. Paths must not contain Chinese, Japanese or Korean (CJK) characters."))
        self.exe_label.setText(TRSM("EXE Location"))
        self.folder_label.setText(TRSM("Models folder"))
        self.folder.setPlaceholderText(TRSM("Leave empty to use the models folder beside the executable"))
        self.exe_browse.setText(TRSM("Browser"))
        self.folder_browse.setText(TRSM("Browser"))
        self.model_label.setText(TRSM("Model"))
        for index, description in enumerate(MODELS.values()):
            self.model.setItemData(index, TRSM(description), Qt.ItemDataRole.ToolTipRole)
        self.scale_label.setText(TRSM("Scale"))
        self.scale.setToolTip(TRSM("The x4 models use 4x. realesr-animevideov3 supports 2x, 3x and 4x."))
        self.tile_label.setText(TRSM("Tile size"))
        self.tile.setSpecialValueText(TRSM("Automatic"))
        self.tile.setToolTip(TRSM("0 selects automatically. Use 32 or more; a smaller tile uses less GPU memory."))
        self.restore_size.setText(TRSM("Resize enhanced image back to its original dimensions"))

    def load_config(self):
        self.exe.setText(MY_CONFIG.get("real-esrgan", "exe_location"))
        self.folder.setText(MY_CONFIG.get("real-esrgan", "models_folder"))
        model = MY_CONFIG.get("real-esrgan", "model") or DEFAULT_MODEL
        self.model.setCurrentIndex(max(0, self.model.findData(model)))
        scale = int(MY_CONFIG.get("real-esrgan", "scale") or "4")
        index = self.scale.findData(scale)
        self.scale.setCurrentIndex(index if index >= 0 else self.scale.count() - 1)
        self.tile.setValue(int(MY_CONFIG.get("real-esrgan", "tile_size") or "0"))
        self.restore_size.setChecked(MY_CONFIG.get("real-esrgan", "resize") == "1")

    def save_config(self):
        values = {"exe_location": self.exe.text().strip(), "models_folder": self.folder.text().strip(),
                  "model": self.model.currentData(), "scale": str(self.scale.currentData()),
                  "tile_size": str(self.tile.value()), "resize": "1" if self.restore_size.isChecked() else "0"}
        for key, value in values.items():
            MY_CONFIG.set("real-esrgan", key, value)

    def reset_defaults(self):
        self.model.setCurrentIndex(self.model.findData(DEFAULT_MODEL))
        self.scale.setCurrentIndex(self.scale.findData(4))
        self.tile.setValue(0)
        self.restore_size.setChecked(False)
