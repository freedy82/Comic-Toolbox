"""Local comic colorization using the DeOldify and DDColor ONNX exports."""

import os
import tempfile
import time
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path


@dataclass(frozen=True)
class ColorizeModel:
    name: str
    family: str
    filename: str
    url: str
    size: int


_DDCOLOR_SOURCE = "https://huggingface.co/facefusion/models-3.0.0/resolve/main/"
_DEOLDIFY_SOURCE = "https://huggingface.co/OwlMaster/AllFilesRope/resolve/main/"
MODELS = {
    "ddcolor": ColorizeModel("DDColor", "ddcolor", "ddcolor.onnx", _DDCOLOR_SOURCE + "ddcolor.onnx", 980103562),
    "ddcolor_artistic": ColorizeModel(
        "DDColor Artistic", "ddcolor", "ddcolor_artistic.onnx", _DDCOLOR_SOURCE + "ddcolor_artistic.onnx", 980103562
    ),
    "deoldify_artistic": ColorizeModel(
        "DeOldify Artistic (FP16)",
        "deoldify",
        "ColorizeArtistic.fp16.onnx",
        _DEOLDIFY_SOURCE + "ColorizeArtistic.fp16.onnx",
        127578150,
    ),
    "deoldify_stable": ColorizeModel(
        "DeOldify Stable (FP16)",
        "deoldify",
        "ColorizeStable.fp16.onnx",
        _DEOLDIFY_SOURCE + "ColorizeStable.fp16.onnx",
        436769415,
    ),
}
DEFAULT_MODEL = "ddcolor"
DEFAULT_MODELS_FOLDER = "./colorize_models"


class ColorizeError(Exception):
    def __init__(self, message, *values):
        self.message = message
        self.values = values
        super().__init__(message % values if values else message)

    def translated(self, translate):
        message = translate(self.message)
        return message % self.values if self.values else message


class ColorizeCanceled(Exception):
    pass


def runtime_error_details(error):
    # Some Windows provider errors contain ANSI text which pybind11 attempts
    # to decode as UTF-8. Recover the underlying message instead of hiding it
    # behind a UnicodeDecodeError.
    if isinstance(error, UnicodeDecodeError):
        encoding = "mbcs" if os.name == "nt" else "utf-8"
        details = error.object.decode(encoding, errors="replace")
    else:
        details = str(error)
    return " ".join(details.replace("\x00", "").split())


def image_has_color(image):
    """Detect actual chromatic pixels, including RGB-encoded grayscale pages."""
    import numpy as np
    from PIL import Image

    if image.mode in ("1", "L", "LA", "I", "F") or image.mode.startswith("I;16"):
        return False
    with image.copy() as preview:
        preview.thumbnail((512, 512), Image.Resampling.BOX)
        with preview.convert("RGBA") as rgba:
            pixels = np.asarray(rgba)
            rgb = pixels[:, :, :3].astype(np.int16)
            visible = pixels[:, :, 3] >= 128
            count = int(np.count_nonzero(visible))
            if not count:
                return False
            # Ignore small JPEG color artifacts and tiny colored logos. Covers
            # and color pages normally contain many more chromatic pixels.
            spread = rgb.max(axis=2) - rgb.min(axis=2)
            colored = visible & (spread >= 18)
            return int(np.count_nonzero(colored)) >= max(8, count * 0.01)


@dataclass(frozen=True)
class ColorizeOptions:
    model: str
    models_folder: Path
    use_gpu: bool = True

    @property
    def model_path(self):
        return self.models_folder / MODELS[self.model].filename

    @classmethod
    def from_config(cls, config, model=None):
        model = model or config.get("colorize", "model") or DEFAULT_MODEL
        if model not in MODELS:
            raise ColorizeError("Unknown Colorize model: %s", model)
        try:
            folder = Path(config.get("colorize", "models_folder") or DEFAULT_MODELS_FOLDER).expanduser().resolve()
        except (OSError, ValueError) as error:
            raise ColorizeError("Cannot use the Colorize models folder: %s", str(error)) from error
        use_gpu = config.get("colorize", "use_gpu").strip().lower() not in ("false", "0", "no", "off")
        return cls(model, folder, use_gpu)

    def require_model(self):
        # Colored source pages do not require a model or an inference runtime.
        # Only check these when the batch encounters its first grayscale page.
        if not self.model_path.is_file():
            raise ColorizeError("Download %s in Settings > Colorize first.", MODELS[self.model].name)
        if find_spec("onnxruntime") is None:
            raise ColorizeError(
                "Colorize requires ONNX Runtime. Install the updated requirements.txt, then restart Comic Toolbox."
            )


def download_model(model, folder, progress, canceled):
    """Replace the cached model only after its complete download is saved."""
    import requests

    definition = MODELS[model]
    folder = Path(folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with requests.get(definition.url, stream=True, timeout=(10, 10)) as response:
            response.raise_for_status()
            if "text/html" in response.headers.get("Content-Type", "").lower():
                raise ColorizeError("The model server returned a webpage instead of a model. Please try again later.")
            total = definition.size
            received = 0
            previous_update = 0
            with tempfile.NamedTemporaryFile(
                dir=folder, prefix=definition.filename + ".", suffix=".part", delete=False
            ) as output:
                temporary_path = Path(output.name)
                for block in response.iter_content(chunk_size=1024 * 1024):
                    if canceled():
                        raise ColorizeCanceled()
                    if block:
                        output.write(block)
                        received += len(block)
                    now = time.monotonic()
                    if now - previous_update >= 0.15:
                        progress(received, total)
                        previous_update = now
            if canceled():
                raise ColorizeCanceled()
            if received != total:
                raise ColorizeError("The model download was incomplete. Please download it again.")
            destination = folder / definition.filename
            os.replace(temporary_path, destination)
            temporary_path = None
            progress(received, total)
            return destination
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


class ColorizeRunner:
    """One inference session per batch, preferring GPU when it is enabled."""

    def __init__(self, options, notify=None):
        options.require_model()
        import onnxruntime as ort

        self.options = options
        self.definition = MODELS[options.model]
        self.ort = ort
        self.notify = notify
        self.session = None
        self.provider = "CPUExecutionProvider"
        if options.use_gpu:
            available = set(ort.get_available_providers())
            for provider in ("CUDAExecutionProvider", "DmlExecutionProvider", "CoreMLExecutionProvider"):
                if provider not in available:
                    continue
                session = None
                try:
                    session = self._create_session(provider)
                    if provider in session.get_providers():
                        self.session = session
                        self.provider = provider
                        break
                except Exception as error:
                    # A provider can be compiled in even when its driver or
                    # libraries are unavailable. Try the next supported backend.
                    self._notify("GPU backend %s could not start: %s", provider, runtime_error_details(error))
                session = None
        if self.session is None:
            self._use_cpu()
            if options.use_gpu:
                self._notify("GPU acceleration is unavailable for this model. Colorize will use CPU.")
        self._report_device()
        inputs = self.session.get_inputs()
        if len(inputs) != 1 or len(inputs[0].shape) != 4:
            raise ColorizeError("This ONNX model is incompatible. Download a model from Settings > Colorize.")
        self.input = inputs[0]
        if self.input.type not in ("tensor(float)", "tensor(float16)"):
            raise ColorizeError("This ONNX model is incompatible. Download a model from Settings > Colorize.")
        height, width = self.input.shape[2:]
        self.height = height if isinstance(height, int) and height > 0 else 256
        self.width = width if isinstance(width, int) and width > 0 else 256

    def close(self):
        self.session = None
        self.notify = None

    def _create_session(self, provider):
        settings = self.ort.SessionOptions()
        settings.intra_op_num_threads = max(1, min(4, os.cpu_count() or 1))
        # Route recoverable errors through the application's localized log.
        # Native Windows logging can otherwise emit UTF-16/ANSI console noise.
        settings.log_severity_level = 4
        if provider == "DmlExecutionProvider":
            # DirectML requires sequential execution and no memory patterns.
            settings.execution_mode = self.ort.ExecutionMode.ORT_SEQUENTIAL
            settings.enable_mem_pattern = False
            if self.definition.family == "deoldify":
                # DirectML cannot compile the fused graph of these FP16
                # DeOldify exports (E_INVALIDARG). Individual GPU operators
                # remain enabled when this optimization is disabled.
                settings.add_session_config_entry("ep.dml.disable_graph_fusion", "1")
        providers = [provider]
        if provider != "CPUExecutionProvider":
            providers.append("CPUExecutionProvider")
        session = self.ort.InferenceSession(
            str(self.options.model_path), sess_options=settings, providers=providers, enable_fallback=False
        )
        # Handle a GPU failure ourselves so the device change is visible in the
        # conversion log and the batch stays on CPU for subsequent images.
        session.disable_fallback()
        return session

    def _use_cpu(self):
        self.session = None
        self.provider = "CPUExecutionProvider"
        try:
            self.session = self._create_session(self.provider)
        except Exception as error:
            raise ColorizeError("Could not load the Colorize model: %s", runtime_error_details(error)) from error

    def _notify(self, message, *values):
        if self.notify is not None:
            self.notify(message, *values)

    def _report_device(self):
        device = {
            "CUDAExecutionProvider": "GPU (CUDA)",
            "DmlExecutionProvider": "GPU (DirectML)",
            "CoreMLExecutionProvider": "GPU (CoreML)",
        }.get(self.provider, "CPU")
        self._notify("Colorize execution backend: %s", device)

    def _run_inference(self, tensor, canceled):
        try:
            return self.session.run(None, {self.input.name: tensor})[0]
        except Exception as error:
            if canceled():
                raise ColorizeCanceled()
            if self.provider == "CPUExecutionProvider":
                raise
            self._notify(
                "GPU colorization failed: %s. Retrying this image and continuing on CPU.", runtime_error_details(error)
            )
            self._use_cpu()
            self._report_device()
            return self.session.run(None, {self.input.name: tensor})[0]

    def colorize(self, image, canceled):
        import cv2
        import numpy as np
        from PIL import Image

        if canceled():
            raise ColorizeCanceled()
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        background = Image.new("RGBA", rgba.size, "white")
        rgb_image = None
        try:
            # Transparent areas must not become black when presented to the model.
            with Image.alpha_composite(background, rgba) as merged:
                rgb_image = merged.convert("RGB")
            rgb = np.asarray(rgb_image)
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            small = cv2.resize(gray, (self.width, self.height), interpolation=cv2.INTER_AREA)
            model_rgb = cv2.cvtColor(small, cv2.COLOR_GRAY2RGB).astype(np.float32)
            if self.definition.family == "ddcolor":
                model_rgb /= 255.0
            dtype = np.float16 if self.input.type == "tensor(float16)" else np.float32
            tensor = np.ascontiguousarray(model_rgb.transpose(2, 0, 1)[None], dtype=dtype)
            prediction = self._run_inference(tensor, canceled)
            if canceled():
                raise ColorizeCanceled()
            channels = 2 if self.definition.family == "ddcolor" else 3
            if prediction.ndim != 4 or prediction.shape[0] != 1 or prediction.shape[1] != channels:
                raise ColorizeError("This ONNX model is incompatible. Download a model from Settings > Colorize.")
            colors = prediction[0].transpose(1, 2, 0).astype(np.float32)
            # Model predictions only supply color. Keep the full-resolution ink
            # and luminance so resizing the model input does not blur the comic.
            original_lab = cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
            if self.definition.family == "deoldify":
                colors = cv2.cvtColor(np.clip(colors / 255.0, 0, 1), cv2.COLOR_RGB2LAB)[:, :, 1:]
            chroma = cv2.resize(colors, rgb_image.size, interpolation=cv2.INTER_CUBIC)
            original_lab[:, :, 1:] = chroma
            result_rgb = cv2.cvtColor(original_lab, cv2.COLOR_LAB2RGB)
            result = Image.fromarray(np.clip(np.rint(result_rgb * 255.0), 0, 255).astype(np.uint8))
            if alpha.getextrema() != (255, 255):
                result.putalpha(alpha)
            return result
        finally:
            if rgb_image is not None:
                rgb_image.close()
            background.close()
            alpha.close()
            rgba.close()
