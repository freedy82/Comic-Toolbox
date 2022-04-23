import re
import bs4
import html
from urllib.parse import urljoin

from models.site import Site

class CartoonMad(Site):
	URL_MATCH = ["cartoonmad.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.cartoonmad.com"
		self._site_name = "動漫狂"
		self._code_page = "big5"
		self._sample_url = ["https://www.cartoonmad.com/comic/5033.html"]
		self._image_url_prefix = 'https://www.cartoonmad.com/comic/comicpic.asp'

	def get_book_id_from_url(self,url):
		# https://www.cartoonmad.com/comic/####.html
		pattern_book_id = re.compile(r'//(.*?)cartoonmad.(.*?)/comic/(.*?)\.html')
		plists = re.findall(pattern_book_id, url)
		if len(plists) > 0 and len(plists[0]) > 2:
			self._book_id = plists[0][2]
			return self._book_id
		return ""

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_title = bs.select('td[style="font-size:12pt;color:#000066"] a[href^="/comic/"]')
		if tmp_title and len(tmp_title) > 0:
			title = html.unescape(tmp_title[0].text.strip())
		else:
			title = "unknown"
		return title

	def get_book_author_from_html(self,html_code):
		pattern_author = re.compile(r'原創作者：(.*?)</td>')
		author_plists = re.findall(pattern_author, html_code)
		if len(author_plists) > 0:
			author = html.unescape(author_plists[0].strip())
		else:
			author = "unknown"
		return author

	def get_book_item_list_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		chapters = bs.select('#info a[href^="/comic/"]')

		index = 1
		pattern_link = re.compile(r'<a href="([^"]*)" target="_blank">(.*)</a>')
		#print("chapters",chapters)
		results = {"chapter":[]}
		if len(chapters) > 0:
			for chapter in chapters:
				#print("chapter",chapter)
				chapter_info = re.findall(pattern_link, str(chapter))
				#print(chapter_info)
				if len(chapter_info) > 0:
					tmp_url = urljoin(url, chapter_info[0][0])
					results["chapter"].append({"title": chapter_info[0][1], "url": tmp_url, "index": index, "ref":url})
					index += 1
		return results

	def get_image_list_from_html(self,html_code,url):
		bs = bs4.BeautifulSoup(html_code, features='html.parser')
		page_lists = bs.select('option[value]')

		pages = []
		for idx, page_link in enumerate(page_lists, start=1):
			tmp_url = urljoin(url, page_link.attrs["value"])
			pages.append({"url":tmp_url,"ref":url})

		return {"pages":pages}

	def get_single_page_image_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, features='html.parser')
		img_src = bs.select('img[src^="'+self._image_url_prefix+'"]')[0].attrs['src']
		return img_src

