# -*- mode: python ; coding: utf-8 -*-
"""Build the GUI and pipe-based verification browser into one portable folder."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata


project = Path(SPECPATH).parent
runtime_hook = str(project / "build_support" / "portable_runtime.py")
icon = str(project / "uis" / "resources" / "icon.ico")
excluded_bindings = ["PyQt5", "PySide2", "PySide6"]
# This application uses Qt Widgets, not QML. Keep native Qt dependencies that
# WebEngine links against, but do not collect Python QML bindings and the whole
# QML plugin tree. Also omit optional tools imported by third-party libraries.
unused_modules = [
    "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtQuickWidgets",
    "PyQt6.QtQuick3D", "PyQt6.QtWebEngineQuick",
    "PyQt6.QtDesigner", "PyQt6.QtHelp", "PyQt6.QtTest", "PyQt6.uic",
    "tkinter", "_tkinter", "PIL.ImageTk",
    "pytest", "unittest", "_testcapi", "_testinternalcapi",
    "IPython", "matplotlib", "pandas", "scipy",
]


def keep_runtime_file(entry):
    destination = str(entry[0]).replace("\\", "/")
    filename = destination.rsplit("/", 1)[-1]
    # The normal WebEngine resource packs remain; debug symbols are not used.
    if filename.lower().endswith((".debug.pak", ".pdb")):
        return False
    # OpenCV is used for still-image OCR/bubble detection, never video input.
    if filename.lower().startswith("opencv_videoio_ffmpeg") and filename.lower().endswith(".dll"):
        return False
    if destination.startswith("PyQt6/") and "/translations/" in destination:
        if "/qtwebengine_locales/" in destination:
            return filename in {"en-US.pak", "en-GB.pak", "zh-CN.pak", "zh-TW.pak"}
        if filename.endswith(".qm"):
            return filename.endswith((
                "_en.qm", "_en_US.qm", "_en_GB.qm",
                "_zh_CN.qm", "_zh_TW.qm", "_zh_HK.qm",
            ))
    return True

# These modules are imported by name after scanning their source directories.
# Keep the directory entries as well as analyzing their Python dependencies.
plugin_folders = [
    "models/sites",
    "models/readers",
    "models/controllers/translator/bubble_detect",
    "models/controllers/translator/ocr",
    "models/controllers/translator/translator",
]
app_data = []
hidden_imports = []
for folder in plugin_folders:
    for path in sorted((project / folder).glob("*.py")):
        if path.name.startswith("_") or path.stem == "empty":
            continue
        app_data.append((str(path), path.parent.relative_to(project).as_posix()))
        hidden_imports.append(".".join(path.relative_to(project).with_suffix("").parts))

# Include runtime assets explicitly rather than copying entire source folders.
for path in sorted((project / "languages").iterdir()):
    if path.is_file() and (path.suffix == ".qm" or path.name.endswith("_extra.ts")):
        app_data.append((str(path), "languages"))
for path in sorted((project / "themes").glob("*.qss")):
    app_data.append((str(path), "themes"))
for path in sorted((project / "fonts").iterdir()):
    if path.is_file() and path.suffix.lower() in {".ttf", ".ttc", ".otf"}:
        app_data.append((str(path), "fonts"))
app_data.append((str(project / "LICENSE"), "."))
for package in ("language_data", "langcodes", "docx"):
    app_data += collect_data_files(package)
for distribution in ("googletrans", "language_data", "langcodes", "PyMuPDF"):
    app_data += copy_metadata(distribution)

app = Analysis(
    [str(project / "start.py")],
    pathex=[str(project)],
    datas=app_data,
    hiddenimports=hidden_imports,
    runtime_hooks=[runtime_hook],
    excludes=excluded_bindings + unused_modules + ["models.browser_verification_helper", "models.test_sites"],
)
app.binaries = [entry for entry in app.binaries if keep_runtime_file(entry)]
app.datas = [entry for entry in app.datas if keep_runtime_file(entry)]
app_pyz = PYZ(app.pure)
app_exe = EXE(
    app_pyz,
    app.scripts,
    [],
    exclude_binaries=True,
    name="ComicToolbox",
    console=False,
    icon=icon,
    upx=False,
    # Keep bundled libraries and assets out of the launcher's directory.
    contents_directory="_internal",
)

# A console-subsystem helper retains stdin/stdout for the private JSON pipes;
# the main GUI remains windowed. QtWebEngine's PyInstaller hook supplies its
# plugins, translations, resources, DLLs and QtWebEngineProcess executable.
browser = Analysis(
    [str(project / "models" / "browser_verification_helper.py")],
    pathex=[str(project)],
    runtime_hooks=[runtime_hook],
    excludes=excluded_bindings + unused_modules,
)
browser.binaries = [entry for entry in browser.binaries if keep_runtime_file(entry)]
browser.datas = [entry for entry in browser.datas if keep_runtime_file(entry)]
browser_pyz = PYZ(browser.pure)
browser_exe = EXE(
    browser_pyz,
    browser.scripts,
    [],
    exclude_binaries=True,
    name="ComicToolboxBrowser",
    console=True,
    hide_console="hide-early",
    icon=icon,
    upx=False,
    # The helper lives inside _internal, beside its shared Python/Qt DLLs.
    contents_directory=".",
)

# Both executables share the same Qt/Python libraries instead of shipping two
# independent browser-sized bundles. Never collect personal INI files here.
COLLECT(
    app_exe,
    # An explicit executable entry preserves its bootloader and places it
    # under _internal instead of collecting it as another top-level launcher.
    [(str(Path("_internal") / "ComicToolboxBrowser.exe"), browser_exe.name, "EXECUTABLE")],
    browser_exe.dependencies,
    app.binaries,
    app.datas,
    browser.binaries,
    browser.datas,
    name="ComicToolbox",
    upx=False,
)
