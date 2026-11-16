import glob
import os.path
import re
import threading
from pathlib import Path

import imagesize
from langcodes import Language
from PIL import Image, ImageEnhance, ImageOps
from PyQt6 import QtWidgets
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QMessageBox

from models.const import IMAGE_EXTS, RESOURCE_DIR, TRSM


def find_all_languages():
    languages = []
    for file in os.listdir(os.path.join(RESOURCE_DIR, "languages")):
        if re.match(r"^[a-zA-Z_].*?\.qm$", file):
            file_name = get_file_name(file)
            language_full_name = Language.get(file_name).autonym()
            language_full_name = language_full_name.replace("（", " (").replace("）", ")")
            languages.append({"name": language_full_name, "file": file_name})
    sorted(languages, key=lambda language: language["name"])
    return languages


def find_all_themes():
    themes = []
    for file in os.listdir(os.path.join(RESOURCE_DIR, "themes")):
        if re.match(r"^[a-zA-Z_].*?\.qss$", file):
            file_name = get_file_name(file)
            if file_name != "default":
                themes.append({"name": file_name})
    sorted(themes, key=lambda theme: theme["name"])
    return themes


def find_all_fonts():
    fonts = []
    for path in (RESOURCE_DIR / "fonts").iterdir():
        if path.is_file() and path.suffix.lower() in {".ttf", ".ttc", ".otf"}:
            fonts.append({"name": path.name, "file": path.as_posix()})
    # Keep existing TTF/TTC choices first so adding OTF does not replace the
    # translator's current default font. Spaces and CJK filenames are allowed.
    fonts.sort(key=lambda font: Path(font["file"]).suffix.lower() == ".otf")
    return fonts


def get_number_of_images_from_folder(folder, num=1, exts=IMAGE_EXTS):
    lists = []
    for ext in exts:
        lists += glob.glob(folder + "/**/*." + ext, recursive=True)
        if len(lists) > num > 0:
            break
    lists.sort()
    if len(lists) > num > 0:
        lists = lists[0:num]
    return lists


def get_image_list_from_folder(folder, results, main_folder="", exts=IMAGE_EXTS, path=""):
    if main_folder == "":
        main_folder = folder
    files = sorted(os.listdir(folder))
    root_files = []
    threads = []
    for file in files:
        full_file = os.path.join(folder, file)
        full_file = Path(full_file).as_posix()
        if os.path.isdir(full_file):
            new_path = os.path.join(path, file)
            new_path = Path(new_path).as_posix()
            tmp_threading = threading.Thread(
                target=get_image_list_from_folder,
                args=(
                    full_file,
                    results,
                    main_folder,
                    exts,
                    new_path,
                ),
            )
            threads.append(tmp_threading)
            tmp_threading.start()
        elif get_ext(file) in exts:
            rel_file = Path(os.path.relpath(full_file, main_folder)).as_posix()
            root_files.append(rel_file)

    for tmp_threading in threads:
        tmp_threading.join()

    if len(root_files) > 0:
        results.append({"path": path, "files": root_files})


def filter_pimage(pimage, contrast=1, sharpness=1, brightness=1, color=1):
    new_pimage = pimage
    enhancer = ImageEnhance.Color(new_pimage)
    new_pimage = enhancer.enhance(color)

    enhancer = ImageEnhance.Contrast(new_pimage)
    new_pimage = enhancer.enhance(contrast)

    enhancer = ImageEnhance.Brightness(new_pimage)
    new_pimage = enhancer.enhance(brightness)

    enhancer = ImageEnhance.Sharpness(new_pimage)
    new_pimage = enhancer.enhance(sharpness)

    return new_pimage


def rotate_pimage(pimage, rotate=0, horizontal_flip=False, vertical_flip=False):
    new_pimage = pimage
    if rotate > 0:
        new_pimage = new_pimage.rotate(-rotate, Image.NEAREST, expand=True)
    if horizontal_flip:
        new_pimage = ImageOps.mirror(new_pimage)
    if vertical_flip:
        new_pimage = ImageOps.flip(new_pimage)
    return new_pimage


def msg_box(message, parent: QtWidgets.QMainWindow = None):
    if parent is not None:
        title = parent.windowTitle()
    else:
        title = TRSM("Comic Toolbox")
    QMessageBox.information(parent, title, message)


def confirm_box(message, parent: QtWidgets.QMainWindow = None):
    if parent is not None:
        title = parent.windowTitle()
    else:
        title = TRSM("Comic Toolbox")
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if reply == QMessageBox.StandardButton.Yes:
        return True
    else:
        return False


def get_file_name(filename):
    name = filename.split(".", 1)[0]
    return name


def get_ext(file_name):
    ext = file_name.rsplit(".", 1)[-1].lower()
    return ext


def find_rect_to_fit(p_width, p_height, c_width, c_height):
    w_ratio = p_width / c_width
    h_ratio = p_height / c_height
    ratio = min(w_ratio, h_ratio)
    c_final_width = c_width * ratio
    c_final_height = c_height * ratio
    c_x = (p_width - c_final_width) / 2.0
    c_y = (p_height - c_final_height) / 2.0
    return QRect(int(c_x), int(c_y), int(c_final_width), int(c_final_height))


def remove_element_of_tuple(tuple_from, need_remove):
    tmp_list = list(tuple_from)
    tmp_list.remove(need_remove)
    return tuple(tmp_list)


def get_image_size(file_name):
    try:
        width, height = imagesize.get(file_name)
        if width > 0 and height > 0:
            return [width, height]
    except Exception:
        pass
    with Image.open(file_name) as image:
        width, height = image.size
        if width > 0 and height > 0:
            return [width, height]
    return [0, 0]
