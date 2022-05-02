import json
import re
import bs4
import html
import os
import execjs
from urllib.parse import urljoin, quote

import jsbeautifier

from models.site import Site

class Dmzj(Site):
	URL_MATCH = ["dmzj.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.dmzj.com"
		self._site_name = "动漫之家"
		self._sample_url = ["https://manhua.dmzj.com/yaojingdeweibabainianrenwu/","https://www.dmzj.com/info/yishenji.html"]

	def get_book_id_from_url(self,url):
		if url:
			r = re.search(r'/info/(.*?).html', url)
			if r:
				return r.group(1)
			r = re.search(r'dmzj.com/([\w\d]*)/$', url)
			if r:
				return r.group(1)
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		if self._book_id != "":
			return self._home_url + "/info/" + self._book_id + ".html"
		return self.get_main_url()

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		title = bs.h1.text.strip()
		if title != "":
			return title
		return "unknown"

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		book_info_list = bs.select("ul.comic_deCon_liO li")
		for tmp_info in book_info_list:
			tmp_text = tmp_info.text.strip()
			if "作者：" in tmp_text:
				return tmp_text.replace("作者：","")
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		results = {}
		li_list = bs.find('ul', {'class': 'list_con_li autoHeight'}).find_all('li')
		chapters = []
		for chapter_number, li in enumerate(reversed(li_list), start=1):
			ch_url = urljoin(url,li.a.get('href'))
			ch_title = li.find('span', {'class': 'list_con_zj'}).text.strip()
			chapters.append({"title":ch_title,"url":ch_url,"index":str(chapter_number),"ref":url})
		if len(chapters) > 0:
			results["chapter"] = chapters
		return results

	def get_image_list_from_html(self,html_code,url):
		s = re.search(r'(eval\(function.*)', html_code).group(1)
		js_str = jsbeautifier.beautify(s)
		json_str = re.search(r"var pages = '(.*?)';", js_str).group(1)
		data = json.loads(json_str)
		image_urls = []
		image_prefix = 'https://images.dmzj.com'
		for image_url in data['page_url'].split('\n'):
			image_url = urljoin(image_prefix, quote(image_url.strip()))
			image_urls.append({"url":image_url,"ref":url})
		return {"images":image_urls}


