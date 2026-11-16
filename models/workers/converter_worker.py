import glob
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

from models import util
from models.colorize import (
    MODELS as COLORIZE_MODELS,
)
from models.colorize import (
    ColorizeCanceled,
    ColorizeError,
    ColorizeRunner,
    image_has_color,
    runtime_error_details,
)
from models.const import MY_CONFIG, TRSM
from models.realesrgan import RealESRGANCanceled, RealESRGANError


class ConverterWorker(QThread):
    trigger = pyqtSignal(str, int, int)

    def __init__(
        self,
        from_folder,
        to_folder,
        from_exts,
        to_ext,
        is_overwrite,
        remove_source,
        sub_folders,
        is_use_filter=False,
        enable_real_cugan=False,
        enable_real_esrgan=False,
        esrgan_options=None,
        enable_colorize=False,
        colorize_options=None,
        parent=None,
    ):
        super().__init__(parent)
        self.from_folder = from_folder
        self.to_folder = to_folder
        self.from_exts = from_exts
        self.to_ext = to_ext
        self.is_overwrite = is_overwrite
        self.remove_source = remove_source
        self.current_action_count = 0
        self.total_action_count = 0
        self.paths_created = []
        self.stop_flag = False
        self.was_canceled = False
        self.sub_folders = sub_folders
        self.is_use_filter = is_use_filter
        self.enable_real_cugan = enable_real_cugan
        self.enable_real_esrgan = enable_real_esrgan
        self.esrgan_options = esrgan_options
        self.enable_colorize = enable_colorize
        self.colorize_options = colorize_options
        self.colorizer = None
        self.colorize_init_failure = None
        self.failed_count = 0

    def run(self):
        # QThread.finished is emitted by Qt after run() returns. Never emit it
        # ourselves: the GUI must retain this worker through native cleanup.
        try:
            self._convert_files()
        except Exception as error:
            self._report_failure(error)
        finally:
            try:
                if self.colorizer is not None:
                    self.colorizer.close()
            except Exception as error:
                self._report_failure(error)
            finally:
                self.colorizer = None
                self.was_canceled = self.stop_flag

    def _report_failure(self, error):
        self.failed_count += 1
        details = error.translated(TRSM) if isinstance(error, (ColorizeError, RealESRGANError)) else str(error)
        self.trigger.emit(TRSM("Conversion failed: %s") % details, self.current_action_count, self.total_action_count)

    def _convert_files(self):
        self.trigger.emit(TRSM("Scanning files, please wait"), 0, 0)
        self.paths_created = []

        # make sure first level folder was created

        for folder in self.sub_folders:
            if not os.path.isdir(os.path.join(self.to_folder, folder)):
                Path(os.path.join(self.to_folder, folder)).mkdir(parents=True, exist_ok=True)

        need_convert_lists = []
        not_need_convert_lists = []
        for from_ext in self.from_exts:
            for folder in self.sub_folders:
                need_convert_lists += glob.glob(self.from_folder + "/" + folder + "/**/*." + from_ext, recursive=True)
        if self.to_ext not in self.from_exts:
            for folder in self.sub_folders:
                not_need_convert_lists += glob.glob(
                    self.from_folder + "/" + folder + "/**/*." + self.to_ext, recursive=True
                )
        else:
            not_need_convert_lists = []

        self.current_action_count = 0
        if self.from_folder == self.to_folder:
            self.total_action_count = len(need_convert_lists)
        else:
            self.total_action_count = len(need_convert_lists) + len(not_need_convert_lists)

        message = TRSM("Need convert: %d, not need convert: %d") % (
            len(need_convert_lists),
            len(not_need_convert_lists),
        )
        self.trigger.emit(message, self.current_action_count, self.total_action_count)

        self.paths_created = []

        for tmp_file in need_convert_lists:
            if not self.stop_flag:
                self._image_file_action(tmp_file, is_force_convert=True)

        if self.from_folder != self.to_folder:
            for tmp_file in not_need_convert_lists:
                if not self.stop_flag:
                    self._image_file_action(tmp_file)

    def _colorize_status(self, message, *values):
        text = TRSM(message)
        self.trigger.emit(text % values if values else text, self.current_action_count, self.total_action_count)

    def _get_colorizer(self):
        if self.colorize_init_failure is not None:
            raise ColorizeError("Colorize could not start: %s", self.colorize_init_failure)
        if self.colorizer is None:
            if self.stop_flag:
                raise ColorizeCanceled()
            self._colorize_status("Loading Colorize model %s...", COLORIZE_MODELS[self.colorize_options.model].name)
            try:
                self.colorizer = ColorizeRunner(self.colorize_options, notify=self._colorize_status)
            except Exception as error:
                # Store text, not an exception traceback retaining a partial model.
                self.colorize_init_failure = (
                    error.translated(TRSM) if isinstance(error, ColorizeError) else runtime_error_details(error)
                )
                raise ColorizeError("Colorize could not start: %s", self.colorize_init_failure) from error
        return self.colorizer

    def stop(self):
        self.stop_flag = True
        self.requestInterruption()

    # internal
    def _image_file_action(self, tmp_file, is_force_convert=False):
        tmp_file = Path(tmp_file).as_posix()

        to_file_with_path = os.path.relpath(tmp_file, self.from_folder)
        full_target_file = os.path.join(self.to_folder, to_file_with_path)
        ext = util.get_ext(full_target_file)
        full_target_file = str(Path(full_target_file).with_suffix("." + self.to_ext))
        if self.enable_colorize:
            self._colorize_image_file_action(Path(tmp_file), Path(full_target_file))
            return
        if self.enable_real_esrgan:
            self._esrgan_image_file_action(Path(tmp_file), Path(full_target_file))
            return
        target_path = Path(full_target_file).parent.absolute()
        if target_path not in self.paths_created:
            Path(target_path).mkdir(parents=True, exist_ok=True)
            self.paths_created.append(target_path)

        full_target_file = Path(full_target_file).as_posix()

        if not os.path.exists(full_target_file) or self.is_overwrite:
            if self.enable_real_cugan:
                real_cugan_exe = MY_CONFIG.get("real-cugan", "exe_location")
                real_cugan_scale = MY_CONFIG.get("real-cugan", "scale")
                real_cugan_denoise = MY_CONFIG.get("real-cugan", "denoise_level")
                if real_cugan_exe != "":
                    cmd = real_cugan_exe + " -s " + real_cugan_scale + " -n " + real_cugan_denoise + " "
                    cmd += '-i "' + tmp_file + '" -o "' + full_target_file + '" -f ' + self.to_ext
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE  # default
                    subprocess.call(cmd, startupinfo=si)
                    tmp_file = full_target_file

            if ext == self.to_ext and tmp_file != full_target_file and not is_force_convert:
                shutil.copy(tmp_file, full_target_file)
                message = TRSM("Copied to %s") % full_target_file
            else:
                img = Image.open(tmp_file)
                if self.is_use_filter:
                    contrast = float(MY_CONFIG.get("filter", "contrast"))
                    sharpness = float(MY_CONFIG.get("filter", "sharpness"))
                    brightness = float(MY_CONFIG.get("filter", "sharpness"))
                    color = float(MY_CONFIG.get("filter", "color"))
                    img = util.filter_pimage(img, contrast, sharpness, brightness, color)
                    rotate = int(MY_CONFIG.get("filter", "rotate"))
                    is_horizontal_flip = MY_CONFIG.get("filter", "horizontal_flip") == "True"
                    is_vertical_flip = MY_CONFIG.get("filter", "vertical_flip") == "True"
                    img = util.rotate_pimage(img, rotate * 90, is_horizontal_flip, is_vertical_flip)

                if self.enable_real_cugan:
                    if MY_CONFIG.get("real-cugan", "resize") == "1":
                        real_cugan_scale = int(MY_CONFIG.get("real-cugan", "scale"))
                        width, height = img.size
                        new_size = (width // real_cugan_scale, height // real_cugan_scale)
                        img = img.resize(new_size)

                if self.to_ext == "jpg":
                    img = img.convert("RGB")
                    img.save(full_target_file, quality=int(MY_CONFIG.get("general", "jpg_quality")))
                else:
                    img.save(full_target_file)

                message = TRSM("Converted to %s") % full_target_file
                if self.remove_source:
                    os.remove(tmp_file)
        else:
            message = TRSM("Skipped of %s") % full_target_file

        self.current_action_count += 1
        self.trigger.emit(message, self.current_action_count, self.total_action_count)

    def _esrgan_image_file_action(self, source, target):
        try:
            if target.exists() and not self.is_overwrite:
                message = TRSM("Skipped of %s") % target.as_posix()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                self.trigger.emit(
                    TRSM("Real-ESRGAN enhancing %s with %s") % (source.as_posix(), self.esrgan_options.model),
                    self.current_action_count,
                    self.total_action_count,
                )
                # Stage the complete result beside the destination before replacing any file.
                with TemporaryDirectory(prefix="comic-esrgan-", dir=str(target.parent)) as work_folder:
                    work_folder = Path(work_folder).resolve()
                    input_file = work_folder / "input.png"
                    enhanced_file = work_folder / "enhanced.png"
                    with Image.open(source) as original:
                        original_size = original.size
                        mode = "RGBA" if "A" in original.getbands() or "transparency" in original.info else "RGB"
                        with original.convert(mode) as normalized:
                            normalized.save(input_file)
                    self.esrgan_options.enhance(input_file, enhanced_file, lambda: self.stop_flag)
                    with Image.open(enhanced_file) as enhanced:
                        image = enhanced.copy()
                    try:
                        if self.esrgan_options.restore_size:
                            image = image.resize(original_size, Image.Resampling.LANCZOS)
                        if self.is_use_filter:
                            image = util.filter_pimage(
                                image,
                                float(MY_CONFIG.get("filter", "contrast")),
                                float(MY_CONFIG.get("filter", "sharpness")),
                                float(MY_CONFIG.get("filter", "brightness")),
                                float(MY_CONFIG.get("filter", "color")),
                            )
                            image = util.rotate_pimage(
                                image,
                                int(MY_CONFIG.get("filter", "rotate")) * 90,
                                MY_CONFIG.get("filter", "horizontal_flip") == "True",
                                MY_CONFIG.get("filter", "vertical_flip") == "True",
                            )
                        result_file = work_folder / ("result." + self.to_ext)
                        if self.to_ext == "jpg":
                            if "A" in image.getbands():
                                background = Image.new("RGB", image.size, "white")
                                background.paste(image, mask=image.getchannel("A"))
                                image.close()
                                image = background
                            else:
                                image = image.convert("RGB")
                            image.save(result_file, quality=int(MY_CONFIG.get("general", "jpg_quality")))
                        else:
                            image.save(result_file)
                    finally:
                        image.close()
                    if self.stop_flag:
                        raise RealESRGANCanceled()
                    os.replace(result_file, target)
                if self.remove_source and source.resolve() != target.resolve():
                    source.unlink()
                message = TRSM("Converted to %s") % target.as_posix()
        except RealESRGANCanceled:
            return
        except Exception as error:
            self.failed_count += 1
            details = error.translated(TRSM) if isinstance(error, RealESRGANError) else str(error)
            message = TRSM("Real-ESRGAN could not convert %s: %s") % (source.as_posix(), details)
        self.current_action_count += 1
        self.trigger.emit(message, self.current_action_count, self.total_action_count)

    def _colorize_image_file_action(self, source, target):
        try:
            if target.exists() and not self.is_overwrite:
                message = TRSM("Skipped of %s") % target.as_posix()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                image = None
                with Image.open(source) as original:
                    already_colored = image_has_color(original)
                    copy_source = (
                        already_colored
                        and not self.is_use_filter
                        and original.format == {"jpg": "JPEG", "png": "PNG"}[self.to_ext]
                    )
                    if self.stop_flag:
                        raise ColorizeCanceled()
                    if already_colored:
                        self._colorize_status("Already colored; using source %s", source.as_posix())
                        if not copy_source:
                            image = original.copy()
                    else:
                        self._colorize_status(
                            "Colorizing %s with %s",
                            source.as_posix(),
                            COLORIZE_MODELS[self.colorize_options.model].name,
                        )
                        image = self._get_colorizer().colorize(original, lambda: self.stop_flag)
                try:
                    if self.is_use_filter:
                        image = util.filter_pimage(
                            image,
                            float(MY_CONFIG.get("filter", "contrast")),
                            float(MY_CONFIG.get("filter", "sharpness")),
                            float(MY_CONFIG.get("filter", "brightness")),
                            float(MY_CONFIG.get("filter", "color")),
                        )
                        image = util.rotate_pimage(
                            image,
                            int(MY_CONFIG.get("filter", "rotate")) * 90,
                            MY_CONFIG.get("filter", "horizontal_flip") == "True",
                            MY_CONFIG.get("filter", "vertical_flip") == "True",
                        )
                    with TemporaryDirectory(prefix="comic-colorize-", dir=str(target.parent)) as work_folder:
                        result_file = Path(work_folder) / ("result." + self.to_ext)
                        if copy_source:
                            shutil.copy2(source, result_file)
                        elif self.to_ext == "jpg":
                            if "A" in image.getbands():
                                background = Image.new("RGB", image.size, "white")
                                background.paste(image, mask=image.getchannel("A"))
                                image.close()
                                image = background
                            else:
                                converted = image.convert("RGB")
                                image.close()
                                image = converted
                            image.save(result_file, quality=int(MY_CONFIG.get("general", "jpg_quality")))
                        else:
                            image.save(result_file)
                        if self.stop_flag:
                            raise ColorizeCanceled()
                        os.replace(result_file, target)
                finally:
                    if image is not None:
                        image.close()
                if self.remove_source and source.resolve() != target.resolve():
                    source.unlink()
                message = TRSM("Copied to %s" if copy_source else "Converted to %s") % target.as_posix()
        except ColorizeCanceled:
            return
        except Exception as error:
            self.failed_count += 1
            details = error.translated(TRSM) if isinstance(error, ColorizeError) else str(error)
            message = TRSM("Colorize could not convert %s: %s") % (source.as_posix(), details)
        self.current_action_count += 1
        self.trigger.emit(message, self.current_action_count, self.total_action_count)
