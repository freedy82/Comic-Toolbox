import os.path
import re
import execjs
import lzstring
import json
import bs4
import threading
import base64
import sys
import time
from abc import ABCMeta, abstractmethod
from pathlib import Path
import concurrent.futures
from const import *
from PyQt5.QtCore import QThread, pyqtSignal
from urllib.parse import urljoin
import importlib
import html
import glob


class Site(QThread):
	chapter_trigger = pyqtSignal(str, int, int)
	chapter_finished = pyqtSignal()
	chapter_canceled = pyqtSignal()

	def __init__(self, web_bot):
		"""Init Class
		"""
		super().__init__()
		self._web_bot = web_bot
		self._home_url = ""
		self._book_id = ""
		self._site_name = ""
		self._main_url = ""
		self._sample_url = []
		self._code_page = "utf-8"
		self._default_image_format = "jpg"
		self._stop_flag = False
		self._is_overwrite = False
		self.current_finish_download = 0
		self.final_total_download = 0

	@classmethod
	def init_site_by_url(cls,url,web_bot):
		all_sites_class = cls.find_all_sites_class()
		for site_class in all_sites_class:
			if site_class.is_url_from_this_site(url=url):
				site_obj = site_class(web_bot)
				site_obj.set_main_url(url)
				return site_obj
		return None

	@classmethod
	def get_all_sites_class(cls):
		return cls.find_all_sites_class()

	@classmethod
	def get_all_sites_object(cls,web_bot):
		results = []
		all_sites_class = cls.find_all_sites_class()
		for site_class in all_sites_class:
			results.append(site_class(web_bot))
		return results

	@classmethod
	def is_url_from_this_site(cls,url):
		if any(tmp_str in url for tmp_str in cls.URL_MATCH):
			return True
		return False

	def get_site_name(self):
		return self._site_name

	def set_site_name(self, new_site_name):
		self._site_name = new_site_name

	def get_home_url(self):
		return self._home_url

	def get_sample_url(self):
		return self._sample_url

	def get_main_url(self):
		return self._main_url

	def set_main_url(self, new_main_url):
		self._main_url = new_main_url

	def set_is_overwrite(self,is_overwrite):
		self._is_overwrite = is_overwrite

	def parse_list(self):
		return self.parse_list_from_url(self._main_url)

	def download_item(self, item, title="", item_type=""):
		"""download item of 1 list
		:param item: list
		:param title: book title
		:param item_type: type of resource
		"""
		self._stop_flag = False

		if item_type == "book":
			tmp_output_dir = item_type + "-" + str(item["index"]).zfill(int(MY_CONFIG.get("general", "book_padding")))
		else:
			tmp_output_dir = item_type + "-" + str(item["index"]).zfill(int(MY_CONFIG.get("general", "chapter_padding")))

		output_dir = os.path.join(MY_CONFIG.get("general", "download_folder"), title, tmp_output_dir)
		Path(output_dir).mkdir(parents=True, exist_ok=True)

		return output_dir

	#flow 1
	def download_image_lists(self, image_urls, item, item_type, title):
		if item_type == "book":
			tmp_output_dir = item_type + "-" + str(item["index"]).zfill(int(MY_CONFIG.get("general", "book_padding")))
		else:
			tmp_output_dir = item_type + "-" + str(item["index"]).zfill(
				int(MY_CONFIG.get("general", "chapter_padding")))

		output_dir = os.path.join(MY_CONFIG.get("general", "download_folder"), title, tmp_output_dir)
		#page_ref = self._home_url + item["url"]
		Path(output_dir).mkdir(parents=True, exist_ok=True)
		print("Total need check download images: " + str(len(image_urls)))

		self.final_total_download = 0
		self.current_finish_download = 0
		if not BY_PASS_DOWNLOAD:
			tasks = []
			for idx, image_url in enumerate(image_urls, start=1):
				ext = self.get_ext(image_url["url"],self._default_image_format)
				# print("starting")
				# target_file = os.path.join(output_dir.rstrip(), "{name:0"+MY_CONFIG.get("general", "image_padding")+"d}.{ext}".format(name=idx, ext=ext))
				target_file = os.path.join(output_dir.rstrip(),str(idx).zfill(int(MY_CONFIG.get("general", "image_padding"))) + "." + ext)
				# print("target_file",target_file)

				if self._is_overwrite or not os.path.isfile(target_file):
					self.final_total_download += 1
					task = EXECUTOR.submit(self.download_image, image_url["url"], target_file, image_url["ref"])
					tasks.append(task)

				# break on # of page
				if idx >= DOWNLOAD_IMAGES_PER_BOOK > 0:
					break

			message = TRSM("Total: %d, need download: %d, skip: %d") % (
			len(image_urls), self.final_total_download, len(image_urls) - self.final_total_download)
			self.chapter_trigger.emit(message, self.current_finish_download, self.final_total_download)

			# wait finish download
			for future in concurrent.futures.as_completed(tasks):
				try:
					data = future.result()
				except Exception as exc:
					# print('Download %s failed' % exc)
					sys.stdout.flush()
				else:
					if data is not None:
						self.current_finish_download += 1
						message = TRSM('Saved to: %s (%d/%d)') % (data, self.current_finish_download, self.final_total_download)
						#print(message)
						#sys.stdout.flush()
						self.chapter_trigger.emit(message, self.current_finish_download, self.final_total_download)

		return output_dir

	def download_image(self, image_url, target_file, page_ref):
		# print("Start Download: ",image_url)
		# sys.stdout.flush()
		if not self._stop_flag:
			data = self._web_bot.get_web_content_raw(url=image_url, ref=page_ref)
			if data:
				fp = open(target_file, mode="wb")
				fp.write(data)
				fp.close()
				if float(MY_CONFIG.get("anti-ban", "image_sleep")) > 0.0:
					time.sleep(float(MY_CONFIG.get("anti-ban", "image_sleep")))
				return target_file
			else:
				message = TRSM("Download failed from %s to %s") % (image_url,target_file)
				self.chapter_trigger.emit(message, self.current_finish_download, self.final_total_download)
		return None

	#flow 2
	def download_single_page_image_from_list(self,page_list):
		if not BY_PASS_DOWNLOAD:
			threads = []
			self.final_total_download = 0
			self.current_finish_download = 0
			for page in page_list:
				old_exist_file_check = []
				[old_exist_file_check.extend(glob.glob(page["file"] + '.' + ext)) for ext in IMAGE_EXTS]
				if self._is_overwrite or len(old_exist_file_check)==0:
					# unknown need 2 args!!!
					t = threading.Thread(target=self.download_single_page_image_from_page_item, args=(page,True))
					threads.append(t)
					t.start()

			self.final_total_download = len(threads)
			message = TRSM("Total: %d, need download: %d, skip: %d") % (
			len(page_list), self.final_total_download, len(page_list) - self.final_total_download)
			self.chapter_trigger.emit(message, self.current_finish_download, self.final_total_download)

			for i in threads:
				i.join()

			#page_sleep = float(MY_CONFIG.get("anti-ban", "page_sleep"))
			#print("Page Sleep %fs" % page_sleep)
			#sys.stdout.flush()
			#time.sleep(page_sleep)

		pass

	def download_single_page_image_from_page_item(self,page,unused_flag):
		html = self._web_bot.get_web_content(url=page["url"], ref=page["ref"], code_page=self._code_page)
		img_url = self.extract_single_page_image_from_info(html)
		ext = self.get_ext(img_url,self._default_image_format)

		if not BY_PASS_DOWNLOAD:
			target_file = page["file"] + "." + ext

			if self._is_overwrite or not os.path.isfile(target_file):
				tasks = []
				task = EXECUTOR.submit(self.download_image, img_url, target_file, page["ref"])
				tasks.append(task)

				# wait finish download
				for future in concurrent.futures.as_completed(tasks):
					result = None
					try:
						result = future.result()
					except Exception as exc:
						#todo add more handle
						print('Download %s failed' % result)
						sys.stdout.flush()
						return None
					else:
						#print('Saved to: %s' % data)
						if result:
							self.current_finish_download += 1
							message = TRSM('Saved to: %s (%d/%d)') % (result, self.current_finish_download, self.final_total_download)
							#print(message)
							#sys.stdout.flush()
							self.chapter_trigger.emit(message, self.current_finish_download, self.final_total_download)
			else:
				self.current_finish_download += 1
				message = TRSM('Exist: %s (%d/%d)') % (target_file, self.current_finish_download, self.final_total_download)
				#print(message)
				#sys.stdout.flush()
				self.chapter_trigger.emit(message, self.current_finish_download, self.final_total_download)

		return page["file"]

	def extract_single_page_image_from_info(self,html):
		return ""

	#action
	def stop(self):
		self._stop_flag = True

	@abstractmethod
	def parse_list_from_url(self, url=''):
		pass

	@abstractmethod
	def parse_book_id_from_url(self, url):
		return ""

	@staticmethod
	def get_ext(image_url, default='jpg', allow=IMAGE_EXTS):
		url = image_url.split('?')[0]
		ext = url.rsplit('.', 1)[-1].lower()
		if ext in allow:
			return ext
		return default

	@staticmethod
	def find_all_sites_class():
		for file in os.listdir(os.path.join(os.path.dirname(__file__), "sites")):
			if re.match(r"^[a-zA-Z].*?\.py$", file):
				importlib.import_module(".sites.{}".format(file.split(".")[0]), __package__)
		return [site_class for site_class in Site.__subclasses__()]
