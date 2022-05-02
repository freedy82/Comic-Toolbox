import os
import concurrent.futures
from PyQt5 import QtCore

from models.webbot import WebBot
from models.config import MyConfig

ROOT_DIR = os.getcwd()
MY_CONFIG = MyConfig(os.path.join(ROOT_DIR, "setting.ini"))
MY_BOOKMARK = MyConfig(os.path.join(ROOT_DIR, "bookmarks.ini"),need_init_as_config=False)
TRS = QtCore.QCoreApplication.translate

def TRSM(str_name):
    return TRS("MainWindow", str_name)

APP_VERSION = "0.9.0"
APP_LINK = "https://github.com/freedy82/Comic-Toolbox"
APP_LICENSE = "GNU General Public License v3.0"
APP_LICENSE_LINK = "https://github.com/freedy82/Comic-Toolbox/blob/main/LICENSE"
APP_AUTHOR = "Freedy Lam"
APP_AUTHOR_LINK = "https://github.com/freedy82"

IMAGE_EXTS = ("jpg","gif","png","jpeg","webp")

# should not change below debug only
DOWNLOAD_IMAGES_PER_BOOK = 0    # 0 for unlimited, number for fast debug
BY_PASS_DOWNLOAD = False        # debug

WEB_BOT = WebBot(agent=MY_CONFIG.get("general", "agent"),
                 time_out=float(MY_CONFIG.get("general", "timeout")),
                 max_retry=int(MY_CONFIG.get("general", "max_retry")),
                 proxy_mode=int(MY_CONFIG.get("anti-ban", "proxy_mode")),
                 proxy_list=MY_CONFIG.get("anti-ban", "proxy_list")
                 )
EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=int(MY_CONFIG.get("anti-ban", "download_worker")))
