import re
import bs4
import html
import os
import execjs
from urllib.parse import urljoin

from models.site import Site

class Empty(Site):
	URL_MATCH = ["domain.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.domain.com"
		self._site_name = "Site Name"
		self._sample_url = ["https://www.domain.com/comic/1234/"]
		# change is need
		self._cookies = {}
		self._accept_language = ""
		self._code_page = "utf-8"
		self._default_image_format = "jpg"

	def get_book_id_from_url(self,url):
		#todo parse id from url
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		#todo reformat the main url from book id
		return self.get_main_url()

	def get_book_title_from_html(self,html_code):
		#todo parse book title from html
		return "unknown"

	def get_book_author_from_html(self,html_code):
		#todo parse book author from html
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		#todo parse book list from html
		#   can have chapter,book,extra section
		return {}

	def get_image_list_from_html(self,html_code,url):
		#todo parse page/image list
		#   each page/image include {"url":"","ref":""}
		#   for image list use {"images":image_urls}
		#   for page list use {"pages":page_urls}
		return {}

	# use only need for page list
	def get_single_page_image_from_html(self, html_code,url):
		#todo get image url from page html
		return ""


