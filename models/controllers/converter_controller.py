import os

from PyQt6 import QtCore
from PyQt6.QtWidgets import QComboBox, QFileDialog, QLabel, QListWidgetItem

from models import util
from models.colorize import MODELS as COLORIZE_MODELS
from models.colorize import ColorizeError, ColorizeOptions
from models.const import IMAGE_EXTS, MY_CONFIG, TRSM
from models.controllers.image_filter_window_controller import ImageFilterWindowController
from models.realesrgan import MODELS as ESRGAN_MODELS
from models.realesrgan import RealESRGANError, RealESRGANOptions
from models.workers.converter_worker import ConverterWorker
from uis.main_window import Ui_MainWindow


class ConverterController(object):
    MODES = [
        {"from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "jpg"), "to_ext": "jpg", "enable_real_cugan": False},
        {"from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "png"), "to_ext": "png", "enable_real_cugan": False},
        {"from_exts": IMAGE_EXTS, "to_ext": "jpg", "enable_real_cugan": False},
        {"from_exts": IMAGE_EXTS, "to_ext": "png", "enable_real_cugan": False},
        {"from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "gif"), "to_ext": "jpg", "enable_real_cugan": True},
        {"from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "gif"), "to_ext": "png", "enable_real_cugan": True},
        {
            "from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "gif"),
            "to_ext": "jpg",
            "enable_real_cugan": False,
            "enable_real_esrgan": True,
        },
        {
            "from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "gif"),
            "to_ext": "png",
            "enable_real_cugan": False,
            "enable_real_esrgan": True,
        },
        {
            "from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "gif"),
            "to_ext": "jpg",
            "enable_real_cugan": False,
            "enable_colorize": True,
        },
        {
            "from_exts": util.remove_element_of_tuple(IMAGE_EXTS, "gif"),
            "to_ext": "png",
            "enable_real_cugan": False,
            "enable_colorize": True,
        },
    ]

    def __init__(self, app=None, ui: Ui_MainWindow = None, main_controller=None):
        self.app = app
        self.ui = ui
        self.main_controller = main_controller
        self.folder_list = []
        self.converter_worker = None
        self.image_filter_window_controller = ImageFilterWindowController(
            app=self.app, main_controller=self.main_controller
        )
        self.setup_control()
        if self.app is not None:
            self.app.aboutToQuit.connect(self.shutdown)

    def setup_control(self):
        convert_from_folder = MY_CONFIG.get("general", "convert_from_folder")
        if convert_from_folder == "":
            convert_from_folder = MY_CONFIG.get("general", "download_folder")
        self.ui.txt_converter_from_folder.setText(convert_from_folder)

        convert_to_folder = MY_CONFIG.get("general", "convert_to_folder")
        if convert_to_folder == "":
            convert_to_folder = MY_CONFIG.get("general", "download_folder")
        self.ui.txt_converter_to_folder.setText(convert_to_folder)

        for mode in self.MODES:
            label = ", ".join(mode["from_exts"]) + " -> " + mode["to_ext"]
            if mode["to_ext"] in mode["from_exts"]:
                label += " (" + TRSM("Force convert mode") + ")"
            self.ui.cbx_converter_mode.addItem(label)
        self.ui.cbx_converter_exist.addItems([TRSM("Skip"), TRSM("Overwrite")])
        self.ui.cbx_converter_remove_source.addItems([TRSM("No"), TRSM("Yes")])
        self.ui.cbx_converter_filter.addItems([TRSM("No"), TRSM("Yes")])
        self.ui.lbl_converter_esrgan_model = QLabel(self.ui.tab_converter)
        self.ui.cbx_converter_esrgan_model = QComboBox(self.ui.tab_converter)
        self.ui.cbx_converter_esrgan_model.addItem(TRSM("Use settings"), None)
        for name in ESRGAN_MODELS:
            self.ui.cbx_converter_esrgan_model.addItem(name, name)
        self.ui.layout_converter_main.insertRow(
            3, self.ui.lbl_converter_esrgan_model, self.ui.cbx_converter_esrgan_model
        )
        self.ui.lbl_converter_colorize_model = QLabel(self.ui.tab_converter)
        self.ui.cbx_converter_colorize_model = QComboBox(self.ui.tab_converter)
        self.ui.cbx_converter_colorize_model.addItem(TRSM("Use settings"), None)
        for name, definition in COLORIZE_MODELS.items():
            self.ui.cbx_converter_colorize_model.addItem(definition.name, name)
        self.ui.layout_converter_main.insertRow(
            4, self.ui.lbl_converter_colorize_model, self.ui.cbx_converter_colorize_model
        )
        self.ui.cbx_converter_mode.currentIndexChanged.connect(self._mode_changed)
        self._mode_changed()

        self.retranslateUi()

        # action
        self.ui.btn_converter_from_browser.clicked.connect(self.btn_converter_from_browser_clicked)
        self.ui.btn_converter_folder_scan.clicked.connect(self.btn_converter_folder_scan_clicked)

        self.ui.btn_converter_select.clicked.connect(self.btn_converter_select_clicked)
        self.ui.btn_converter_unselect.clicked.connect(self.btn_converter_unselect_clicked)
        self.ui.btn_converter_select_all.clicked.connect(self.btn_converter_select_all_clicked)
        self.ui.btn_converter_unselect_all.clicked.connect(self.btn_converter_unselect_all_clicked)

        self.ui.btn_converter_to_browser.clicked.connect(self.btn_converter_to_browser_clicked)
        self.ui.btn_converter_change_filter.clicked.connect(self.btn_converter_change_filter_clicked)
        self.ui.btn_converter_start.clicked.connect(self.btn_converter_start_clicked)
        self.ui.btn_converter_cancel.clicked.connect(self.btn_converter_cancel_clicked)

    def retranslateUi(self):
        for idx, mode in enumerate(self.MODES):
            label = ", ".join(mode["from_exts"]) + " -> " + mode["to_ext"]
            if "enable_real_cugan" in mode and mode["enable_real_cugan"]:
                label += " ( " + TRSM("Real-CUGAN AI enhance mode") + " )"
            elif mode.get("enable_real_esrgan", False):
                label += " ( " + TRSM("Real-ESRGAN AI enhance mode") + " )"
            elif mode.get("enable_colorize", False):
                label += " ( " + TRSM("Colorize") + " )"
            elif mode["to_ext"] in mode["from_exts"]:
                label += " ( " + TRSM("Force convert mode") + " )"
            self.ui.cbx_converter_mode.setItemText(idx, label)

        self.ui.cbx_converter_exist.setItemText(0, TRSM("Skip"))
        self.ui.cbx_converter_exist.setItemText(1, TRSM("Overwrite"))

        self.ui.cbx_converter_remove_source.setItemText(0, TRSM("No"))
        self.ui.cbx_converter_remove_source.setItemText(1, TRSM("Yes"))

        self.ui.cbx_converter_filter.setItemText(0, TRSM("No"))
        self.ui.cbx_converter_filter.setItemText(1, TRSM("Yes"))
        self.ui.lbl_converter_esrgan_model.setText(TRSM("Real-ESRGAN model"))
        self.ui.cbx_converter_esrgan_model.setItemText(0, TRSM("Use settings"))
        self.ui.lbl_converter_colorize_model.setText(TRSM("Colorize model"))
        self.ui.cbx_converter_colorize_model.setItemText(0, TRSM("Use settings"))
        for index, description in enumerate(ESRGAN_MODELS.values(), start=1):
            self.ui.cbx_converter_esrgan_model.setItemData(index, TRSM(description), QtCore.Qt.ItemDataRole.ToolTipRole)

        if self.image_filter_window_controller:
            self.image_filter_window_controller.retranslateUi()

    # action
    def _mode_changed(self):
        index = self.ui.cbx_converter_mode.currentIndex()
        enabled = index >= 0 and self.MODES[index].get("enable_real_esrgan", False)
        self.ui.lbl_converter_esrgan_model.setVisible(enabled)
        self.ui.cbx_converter_esrgan_model.setVisible(enabled)
        colorize = index >= 0 and self.MODES[index].get("enable_colorize", False)
        self.ui.lbl_converter_colorize_model.setVisible(colorize)
        self.ui.cbx_converter_colorize_model.setVisible(colorize)

    def btn_converter_from_browser_clicked(self):
        old_folder_path = self.ui.txt_converter_from_folder.text()
        if old_folder_path == "":
            old_folder_path = "./"
        folder_path = QFileDialog.getExistingDirectory(self.main_controller, TRSM("Open folder"), old_folder_path)
        if folder_path != "":
            self.ui.txt_converter_from_folder.setText(folder_path)
            self.ui.list_converter_folder.clear()
            self.ui.btn_converter_select.setEnabled(False)
            self.ui.btn_converter_unselect.setEnabled(False)
            self.ui.btn_converter_select_all.setEnabled(False)
            self.ui.btn_converter_unselect_all.setEnabled(False)
            self.ui.btn_converter_start.setEnabled(False)
            self.ui.btn_converter_cancel.setEnabled(False)
            MY_CONFIG.set("general", "convert_from_folder", folder_path)
            MY_CONFIG.save()

    def btn_converter_folder_scan_clicked(self):
        folder_path = self.ui.txt_converter_from_folder.text()
        final_folders = []
        try:
            folders = os.listdir(folder_path)
            folders.sort()
            for folder in folders:
                if os.path.isdir(os.path.join(folder_path, folder)):
                    final_folders.append(folder)
        except Exception:
            pass
        self.folder_list = final_folders
        self._update_folder_list()

        if len(final_folders) == 0:
            util.msg_box(TRSM("Not sub-folder found"), self.main_controller)

    def btn_converter_select_clicked(self):
        items = self.ui.list_converter_folder.selectedItems()
        for item in items:
            item.setCheckState(QtCore.Qt.CheckState.Checked)

    def btn_converter_unselect_clicked(self):
        items = self.ui.list_converter_folder.selectedItems()
        for item in items:
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)

    def btn_converter_select_all_clicked(self):
        for i in range(self.ui.list_converter_folder.count()):
            self.ui.list_converter_folder.item(i).setCheckState(QtCore.Qt.CheckState.Checked)

    def btn_converter_unselect_all_clicked(self):
        for i in range(self.ui.list_converter_folder.count()):
            self.ui.list_converter_folder.item(i).setCheckState(QtCore.Qt.CheckState.Unchecked)

    def btn_converter_to_browser_clicked(self):
        old_folder_path = self.ui.txt_converter_to_folder.text()
        if old_folder_path == "":
            old_folder_path = "./"
        folder_path = QFileDialog.getExistingDirectory(self.main_controller, TRSM("Open folder"), old_folder_path)
        if folder_path != "":
            self.ui.txt_converter_to_folder.setText(folder_path)
            MY_CONFIG.set("general", "convert_to_folder", folder_path)
            MY_CONFIG.save()

    def btn_converter_change_filter_clicked(self):
        folder = self.ui.txt_converter_from_folder.text()
        images = util.get_number_of_images_from_folder(folder, 20)
        if len(images) > 0:
            self.image_filter_window_controller.set_image_list(images)
            self.image_filter_window_controller.show()
        else:
            util.msg_box(TRSM("Please select a folder with contain at least one image"), self.main_controller)

    def btn_converter_start_clicked(self):
        # Scanning folders can enable Start again while a batch is running.
        # Keep its worker alive until Qt has delivered the real finished signal.
        if self.converter_worker is not None:
            return
        # check real-cugan
        mode_index = self.ui.cbx_converter_mode.currentIndex()
        if self.MODES[mode_index]["enable_real_cugan"] and MY_CONFIG.get("real-cugan", "exe_location") == "":
            util.msg_box(TRSM("Please choose the real-cugan exe location in settings"), self.main_controller)
            return
        esrgan_options = None
        colorize_options = None
        if self.MODES[mode_index].get("enable_real_esrgan", False):
            try:
                esrgan_options = RealESRGANOptions.from_config(
                    MY_CONFIG, self.ui.cbx_converter_esrgan_model.currentData()
                )
            except RealESRGANError as error:
                util.msg_box(error.translated(TRSM), self.main_controller)
                return
        if self.MODES[mode_index].get("enable_colorize", False):
            try:
                colorize_options = ColorizeOptions.from_config(
                    MY_CONFIG, self.ui.cbx_converter_colorize_model.currentData()
                )
            except ColorizeError as error:
                util.msg_box(error.translated(TRSM), self.main_controller)
                return

        total_need_convert_list = []
        for i in range(self.ui.list_converter_folder.count()):
            if self.ui.list_converter_folder.item(i).checkState() == QtCore.Qt.CheckState.Checked:
                total_need_convert_list.append(self.folder_list[i])

        if len(total_need_convert_list) > 0:
            self.ui.pgb_converter.setMaximum(0)
            self.ui.pgb_converter.setValue(0)
            self.ui.btn_converter_start.setEnabled(False)
            self.ui.btn_converter_cancel.setEnabled(True)
            self.ui.log_converter.clear()

            self.converter_worker = ConverterWorker(
                from_folder=self.ui.txt_converter_from_folder.text(),
                to_folder=self.ui.txt_converter_to_folder.text(),
                from_exts=self.MODES[mode_index]["from_exts"],
                to_ext=self.MODES[mode_index]["to_ext"],
                is_overwrite=bool(self.ui.cbx_converter_exist.currentIndex()),
                remove_source=bool(self.ui.cbx_converter_remove_source.currentIndex()),
                sub_folders=total_need_convert_list,
                is_use_filter=bool(self.ui.cbx_converter_filter.currentIndex()),
                enable_real_cugan=self.MODES[mode_index]["enable_real_cugan"],
                enable_real_esrgan=self.MODES[mode_index].get("enable_real_esrgan", False),
                esrgan_options=esrgan_options,
                enable_colorize=self.MODES[mode_index].get("enable_colorize", False),
                colorize_options=colorize_options,
                parent=self.main_controller,
            )
            self.converter_worker.trigger.connect(self.convert_trigger)
            self.converter_worker.finished.connect(self.convert_finished, QtCore.Qt.ConnectionType.QueuedConnection)
            self.converter_worker.finished.connect(self.converter_worker.deleteLater)
            self.converter_worker.start()
        else:
            util.msg_box(TRSM("Please select at least one folder to convert"), self.main_controller)

    def btn_converter_cancel_clicked(self):
        if self.converter_worker is not None:
            self.converter_worker.stop()
            self.ui.btn_converter_cancel.setEnabled(False)

    def shutdown(self):
        # Do not destroy a running QThread or its ONNX session during app exit.
        worker = self.converter_worker
        if worker is not None:
            worker.stop()
            worker.wait()

    # callback
    def convert_trigger(self, message, current_action, total_action):
        self.ui.pgb_converter.setMaximum(total_action)
        self.ui.pgb_converter.setValue(current_action)
        if message != "":
            self.ui.log_converter.append(message)

    def convert_finished(self):
        worker = self.converter_worker
        if worker is None:
            return
        if worker.was_canceled:
            self.convert_canceled()
            return
        failed_count = worker.failed_count
        if failed_count:
            self.ui.log_converter.append(TRSM("Conversion completed with %d failed files.") % failed_count)
        else:
            self.ui.log_converter.append(TRSM("Convert finished!"))
        self.ui.btn_converter_start.setEnabled(True)
        self.ui.btn_converter_cancel.setEnabled(False)
        if self.ui.pgb_converter.maximum() > 0:
            self.ui.pgb_converter.setValue(self.ui.pgb_converter.maximum())
        else:
            self.ui.pgb_converter.setMaximum(100)
            self.ui.pgb_converter.setValue(100)
        self.converter_worker = None

    def convert_canceled(self):
        self.ui.log_converter.append(TRSM("Convert canceled!"))
        self.ui.btn_converter_start.setEnabled(True)
        self.ui.btn_converter_cancel.setEnabled(False)
        self.converter_worker = None

    # internal function
    def _update_folder_list(self):
        self.ui.list_converter_folder.clear()

        for idx, tmp_folder in enumerate(self.folder_list):
            item = QListWidgetItem()
            item.setText(tmp_folder)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Checked)
            self.ui.list_converter_folder.addItem(item)

        if self.ui.list_converter_folder.count() > 0:
            self.ui.btn_converter_select.setEnabled(True)
            self.ui.btn_converter_unselect.setEnabled(True)
            self.ui.btn_converter_select_all.setEnabled(True)
            self.ui.btn_converter_unselect_all.setEnabled(True)
            self.ui.btn_converter_start.setEnabled(True)
        else:
            self.ui.btn_converter_select.setEnabled(False)
            self.ui.btn_converter_unselect.setEnabled(False)
            self.ui.btn_converter_select_all.setEnabled(False)
            self.ui.btn_converter_unselect_all.setEnabled(False)
            self.ui.btn_converter_start.setEnabled(False)
