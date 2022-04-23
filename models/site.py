import os.path
import re
import threading
import concurrent.futures
import importlib
import glob
import time
from abc import ABCMeta, abstractmethod
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

# fix for pyInstaller
import execjs
import lzstring

from const import *


class Site(QThread):
	chapter_trigger = pyqtSignal(str, int, int)
	chapter_finished = pyqtSignal()
	chapter_canceled = pyqtSignal()

	def __init__(self, web_bot):
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
		self._is_need_nodejs = False
		self._current_finish_download = 0
		self._final_total_download = 0

	# normal method
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

	def get_is_need_nodejs(self):
		return self._is_need_nodejs

	def parse_list(self):
		self._book_id = self.get_book_id_from_url(self._main_url)
		if self._book_id == "":
			return {}

		self._main_url = self.get_main_url_from_book_id()

		html_code = self._web_bot.get_web_content(url=self._main_url, code_page=self._code_page)
		lists = {}
		if html_code is not None and html_code != "":
			title = self.get_book_title_from_html(html_code)
			author = self.get_book_author_from_html(html_code)
			lists = self.get_book_item_list_from_html(html_code,self._main_url)
			if lists is not None:
				lists["title"] = title
				lists["author"] = author

		return lists

	def download_item(self, item, title="", item_type=""):
		self._stop_flag = False

		if item_type == "book":
			tmp_output_dir = item_type + "-" + str(item["index"]).zfill(int(MY_CONFIG.get("general", "book_padding")))
		else:
			tmp_output_dir = item_type + "-" + str(item["index"]).zfill(int(MY_CONFIG.get("general", "chapter_padding")))

		output_dir = os.path.join(MY_CONFIG.get("general", "download_folder"), title, tmp_output_dir)
		Path(output_dir).mkdir(parents=True, exist_ok=True)

		html_code = self._web_bot.get_web_content(url=item["url"], ref=item["ref"], code_page=self._code_page)
		results = self.get_image_list_from_html(html_code=html_code,url=item["url"])
		if "images" in results:
			self.download_image_lists(results["images"],output_dir)
		if "pages" in results:
			self.download_single_page_image_from_list(results["pages"],output_dir)

		return output_dir

	#flow 1
	def download_image_lists(self, image_urls, output_dir):
		#print("Total need check download images: " + str(len(image_urls)))

		self._final_total_download = 0
		self._current_finish_download = 0
		if not BY_PASS_DOWNLOAD:
			tasks = []
			for idx, image_url in enumerate(image_urls, start=1):
				ext = self.get_ext(image_url["url"],self._default_image_format)
				# print("starting")
				target_file = os.path.join(output_dir.rstrip(),str(idx).zfill(int(MY_CONFIG.get("general", "image_padding"))) + "." + ext)
				# print("target_file",target_file)

				if self._is_overwrite or not os.path.isfile(target_file):
					self._final_total_download += 1
					task = EXECUTOR.submit(self.download_image, image_url["url"], target_file, image_url["ref"])
					tasks.append(task)

				# break on # of page
				if idx >= DOWNLOAD_IMAGES_PER_BOOK > 0:
					break

			if len(image_urls) > 0:
				message = TRSM("Total: %d, need download: %d, skip: %d") % (
					len(image_urls), self._final_total_download, len(image_urls) - self._final_total_download
				)
				self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)
			else:
				#display a warning message
				message = TRSM("Either web page format was changed or the site was required install Node.JS")
				self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)
				pass

			# wait finish download
			for future in concurrent.futures.as_completed(tasks):
				try:
					data = future.result()
				except Exception as exc:
					# print('Download %s failed' % exc)
					# sys.stdout.flush()
					pass
				else:
					if data is not None:
						self._current_finish_download += 1
						message = TRSM('Saved to: %s (%d/%d)') % (data, self._current_finish_download, self._final_total_download)
						#print(message)
						#sys.stdout.flush()
						self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)

		return output_dir

	def download_image(self, image_url, target_file, page_ref):
		# print("Start Download: ",image_url)
		# sys.stdout.flush()
		if not self._stop_flag:
			# debug
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
				self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)
		return None

	#flow 2
	def download_single_page_image_from_list(self,page_list,target_folder):
		if not BY_PASS_DOWNLOAD:
			threads = []
			self._final_total_download = 0
			self._current_finish_download = 0
			for idx, page in enumerate(page_list, start=1):
				page["file"] = os.path.join(target_folder.rstrip(), str(idx).zfill(int(MY_CONFIG.get("general", "image_padding"))))
				old_exist_file_check = []
				[old_exist_file_check.extend(glob.glob(page["file"] + '.' + ext)) for ext in IMAGE_EXTS]
				if self._is_overwrite or len(old_exist_file_check) == 0:
					# unknown need 2 args!!!
					t = threading.Thread(target=self.download_single_page_image_from_page, args=(page,True))
					threads.append(t)
					t.start()

			self._final_total_download = len(threads)
			message = TRSM("Total: %d, need download: %d, skip: %d") % (
				len(page_list), self._final_total_download, len(page_list) - self._final_total_download
			)
			self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)

			for i in threads:
				i.join()

			#page_sleep = float(MY_CONFIG.get("anti-ban", "page_sleep"))
			#print("Page Sleep %fs" % page_sleep)
			#sys.stdout.flush()
			#time.sleep(page_sleep)
		pass

	def download_single_page_image_from_page(self,page,unused_flag):
		html_code = self._web_bot.get_web_content(url=page["url"], ref=page["ref"], code_page=self._code_page)
		img_url = self.get_single_page_image_from_html(html_code,page["url"])
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
						#print('Download %s failed' % result)
						#sys.stdout.flush()
						return None
					else:
						#print('Saved to: %s' % data)
						if result:
							self._current_finish_download += 1
							message = TRSM('Saved to: %s (%d/%d)') % (result, self._current_finish_download, self._final_total_download)
							#print(message)
							#sys.stdout.flush()
							self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)
			else:
				self._current_finish_download += 1
				message = TRSM('Exist: %s (%d/%d)') % (target_file, self._current_finish_download, self._final_total_download)
				#print(message)
				#sys.stdout.flush()
				self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)

		return page["file"]

	#should call from child
	def get_main_url_from_book_id(self):
		return self._main_url

	def get_single_page_image_from_html(self, html_code, url):
		return ""

	#action
	def stop(self):
		self._stop_flag = True

	#@abstractmethod
	#def parse_list_from_url(self, url=''):
	#	pass

	@abstractmethod
	def get_book_id_from_url(self, url):
		return ""

	@abstractmethod
	def get_book_title_from_html(self,html_code):
		return 'unknown'

	@abstractmethod
	def get_book_author_from_html(self,html_code):
		return 'unknown'

	@abstractmethod
	def get_book_item_list_from_html(self,html_code,url):
		return {}

	@abstractmethod
	def get_image_list_from_html(self,html_code,url):
		return {}

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
			if re.match(r"^[a-zA-Z].*?\.py$", file) and file != "empty.py":
				importlib.import_module(".sites.{}".format(file.split(".")[0]), __package__)
		return [site_class for site_class in Site.__subclasses__()]

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
