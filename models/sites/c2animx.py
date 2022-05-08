import re
import bs4
import html
import os
import execjs
from urllib.parse import urljoin

from models.site import Site

class C2Animx(Site):
	URL_MATCH = ["2animx.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.2animx.com/"
		self._site_name = "二次元动漫"
		self._sample_url = ["https://www.2animx.com/index-comic-name-山海逆戰-id-22822"]

	def get_book_id_from_url(self,url):
		result = re.search(r'-id-(\d+)',url)
		if result:
			return result.group(1)
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		return urljoin(self._home_url, "/index-comic-id-{}/".format(self._book_id))

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		title = bs.find('div', {'class': 'box-hd'}).h1.text.strip()
		if title != "":
			return title
		return "unknown"

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		mh_info = bs.find('dl', {'class': 'mh-detail'})
		for p in mh_info.dd.find_all('p'):
			if not p.span:
				continue
			text = p.span.text
			if '漫畫作者：' in text:
				return p.a.text
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		li_list = bs.find('ul', {'class': 'b1'}).find_all('li')
		chapters = []
		for ch_idx, li in enumerate(li_list, start=1):
			href = li.a.get('href')
			ch_url = urljoin(self._home_url, href)
			ch_title = li.a.text.strip()
			chapters.append({"url":ch_url,"title":ch_title,"index":str(ch_idx),"ref":url})
		if len(chapters) > 0:
			return {"chapter":chapters}
		return {}

	def get_image_list_from_html(self,html_code,url):
		#todo parse page/image list
		#   each page/image include {"url":"","ref":""}
		#       PS: each item have option with "post_download_action" for post image action
		#           call back will with image_in_disk and image_url as param
		#   for image list use {"images":image_urls}
		#   for page list use {"pages":page_urls}
		bs = bs4.BeautifulSoup(html_code, 'html.parser')

		max_page = 1
		for i in bs.find('select', {'name': 'select1'}).find_all('option'):
			page = int(i.get('value'))
			if page > max_page:
				max_page = page

		page_urls = []
		page_urls.append({"url":url,"ref":url})
		for page in range(2, max_page + 1):
			page_url = url + "-p-%s" % page
			page_urls.append({"url":page_url,"ref":url})
		if len(page_urls) > 0:
			return {"pages":page_urls}
		return {}

	# use only need for page list
	def get_single_page_image_from_html(self, html_code,url):
		try:
			bs = bs4.BeautifulSoup(html_code, 'html.parser')
			img_url = bs.find('img', {'id': 'ComicPic'}).get('src')
			if img_url != "":
				return urljoin(url, img_url)
		except Exception as ex:
			print("throw exception with",url)
			print(ex)
			print(html_code)
		return ""

