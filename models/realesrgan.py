"""Portable Real-ESRGAN NCNN/Vulkan integration."""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


MODELS = {
    "realesrgan-x4plus": "General images (default)",
    "realesrnet-x4plus": "General images, more conservative restoration",
    "realesrgan-x4plus-anime": "Anime and comic images (smaller model)",
    "realesr-animevideov3": "Animation frames (2x, 3x or 4x)",
}
DEFAULT_MODEL = "realesrgan-x4plus"


def model_scales(model):
    return (2, 3, 4) if model == "realesr-animevideov3" else (4,)


def _error_details(log):
    """Keep useful errors without dumping native tile progress or GPU information."""
    lines = []
    for line in log.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"\d+(?:\.\d+)?%", line):
            continue
        if re.match(r"^\[\d+ [^\]]+\]\s+(?:queueC=|bugsbn1=|fp16-|subgroup=)", line):
            continue
        lines.append(line)
    return " | ".join(lines[-3:])[-600:]


class RealESRGANError(Exception):
    def __init__(self, message, *values):
        self.message = message
        self.values = values
        super().__init__(message % values if values else message)

    def translated(self, translate):
        message = translate(self.message)
        return message % self.values if self.values else message


class RealESRGANCanceled(Exception):
    pass


@dataclass(frozen=True)
class RealESRGANOptions:
    executable: Path
    models_folder: Path
    model: str = DEFAULT_MODEL
    scale: int = 4
    tile_size: int = 0
    restore_size: bool = False

    @classmethod
    def from_config(cls, config, model_override=None):
        executable = config.get("real-esrgan", "exe_location").strip().strip('"')
        if not executable:
            raise RealESRGANError("Please choose the Real-ESRGAN executable in Settings.")
        executable = Path(executable).expanduser().resolve()
        model = model_override or config.get("real-esrgan", "model") or DEFAULT_MODEL
        if model not in MODELS:
            raise RealESRGANError("Unknown Real-ESRGAN model: %s", model)
        try:
            scale = int(config.get("real-esrgan", "scale") or "4")
            tile_size = int(config.get("real-esrgan", "tile_size") or "0")
        except ValueError:
            raise RealESRGANError("Invalid Real-ESRGAN scale or tile size. Please save Settings again.") from None
        # The x4 models have fixed-scale weights; only animevideov3 has 2x/3x weights.
        if model_override and scale not in model_scales(model):
            scale = 4
        folder = config.get("real-esrgan", "models_folder").strip().strip('"')
        models_folder = Path(folder).expanduser().resolve() if folder else executable.parent / "models"
        options = cls(executable, models_folder, model, scale, tile_size,
                      config.get("real-esrgan", "resize") == "1")
        options.check_paths()
        return options

    def check_paths(self):
        if not self.executable.is_file():
            raise RealESRGANError("Real-ESRGAN executable not found: %s", str(self.executable))
        if self.scale not in model_scales(self.model):
            raise RealESRGANError("The selected Real-ESRGAN model does not support this scale.")
        if self.tile_size != 0 and self.tile_size < 32:
            raise RealESRGANError("Real-ESRGAN tile size must be 0 (automatic) or at least 32.")
        stem = self.model
        if self.model == "realesr-animevideov3":
            stem += "-x%d" % self.scale
        for extension in (".param", ".bin"):
            model_file = self.models_folder / (stem + extension)
            if not model_file.is_file():
                raise RealESRGANError("Real-ESRGAN model file not found: %s", str(model_file))

    def enhance(self, source, output, is_canceled):
        if is_canceled():
            raise RealESRGANCanceled()
        source = Path(source).resolve()
        output = Path(output).resolve()
        work_folder = output.parent
        # The worker stages images with ASCII basenames in the same folder.
        # Older Windows NCNN image encoders can crash on absolute CJK paths.
        # Set the Unicode working directory through Python's Windows API and
        # give the executable only relative image filenames.
        command = [str(self.executable), "-i", os.path.relpath(source, work_folder), "-o", output.name,
                   "-m", str(self.models_folder), "-n", self.model,
                   "-s", str(self.scale), "-t", str(self.tile_size), "-f", "png"]
        try:
            process = subprocess.Popen(
                command, cwd=str(work_folder), stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except OSError as error:
            raise RealESRGANError("Could not start Real-ESRGAN: %s", str(error)) from error
        try:
            while True:
                if is_canceled():
                    raise RealESRGANCanceled()
                try:
                    log, _ = process.communicate(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
        if is_canceled():
            raise RealESRGANCanceled()
        details = _error_details(log)
        if process.returncode != 0:
            code = "0x%08X" % (process.returncode & 0xffffffff) if os.name == "nt" else str(process.returncode)
            if details:
                raise RealESRGANError("Real-ESRGAN failed (exit code %s): %s", code, details)
            raise RealESRGANError("Real-ESRGAN failed (exit code %s).", code)
        if not output.is_file() or output.stat().st_size == 0:
            if details:
                raise RealESRGANError("Real-ESRGAN did not create an output image: %s", details)
            raise RealESRGANError("Real-ESRGAN did not create an output image.")
