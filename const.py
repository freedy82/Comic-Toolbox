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

APP_VERSION = "0.6.5"
APP_LINK = "https://github.com/freedy82/Comic-Toolbox"

IMAGE_EXTS = ("jpg","gif","png","jpeg","webp")

# setting for AI
# REAL_CUGAN_DIR = "E:/Real-CUGAN/"
# REAL_CUGAN_INPUT = REAL_CUGAN_DIR + "input_dir/"
# REAL_CUGAN_OUTPUT = REAL_CUGAN_DIR + "output_dir/"
# REAL_CUGAN_GO = REAL_CUGAN_DIR + "packages100/execc.exe"
#

# should not change below debug only
DOWNLOAD_IMAGES_PER_BOOK = 0    # 0 for unlimited, number for fast debug
BY_PASS_DOWNLOAD = False        # debug
# BY_PASS_AI = True             # debug

WEB_BOT = WebBot(agent=MY_CONFIG.get("general", "agent"),
                 time_out=float(MY_CONFIG.get("general", "timeout")),
                 max_retry=int(MY_CONFIG.get("general", "max_retry")),
                 proxy_mode=int(MY_CONFIG.get("anti-ban", "proxy_mode")),
                 proxy_list=MY_CONFIG.get("anti-ban", "proxy_list")
                 )
EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=int(MY_CONFIG.get("anti-ban", "download_worker")))
