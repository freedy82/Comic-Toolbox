import re
import html
import bs4
from urllib.parse import urljoin

from models.site import Site

class ReadComicsOnline(Site):
	URL_MATCH = ["readcomicsonline.ru"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://readcomicsonline.ru"
		self._site_name = "Read Comics Online"
		self._sample_url = ["https://readcomicsonline.ru/comic/avengers-2018"]

	def get_book_id_from_url(self,url):
		# https://readcomicsonline.ru/comic/??????
		pattern_book_id = re.compile(r'//(.*?)readcomicsonline.ru/comic/([^/]*)')
		plists = re.findall(pattern_book_id, url)
		if len(plists) > 0 and len(plists[0]) > 1:
			self._book_id = plists[0][1]
			return self._book_id
		return ""

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_title = bs.select('h2.listmanga-header')
		if tmp_title and len(tmp_title) > 0:
			title = html.unescape(tmp_title[0].text.strip())
		else:
			title = "unknown"
		return title

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_author = bs.select('a[href^="https://readcomicsonline.ru/comic-list/author/"]')
		if tmp_author and len(tmp_author) > 0:
			author = html.unescape(tmp_author[0].text.strip())
		else:
			author = "unknown"
		return author

	def get_book_item_list_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		chapters = bs.select('h5.chapter-title-rtl')
		results = {"chapter": []}
		index = 1
		pattern_link = re.compile(r'<a href="([^"]*)">(.*)</a>')
		if len(chapters) > 0:
			chapters.reverse()
			for chapter in chapters:
				#print("chapter",chapter)
				chapter_info = re.findall(pattern_link, str(chapter))
				#print(chapter_info)
				if len(chapter_info) > 0:
					tmp_url = urljoin(url, chapter_info[0][0])
					results["chapter"].append({"title": chapter_info[0][1], "url": tmp_url, "index": str(index), "ref":url})
					index += 1
		return results

	def get_image_list_from_html(self,html_code,url):
		bs = bs4.BeautifulSoup(html_code, features='html.parser')
		image_lists = bs.select('div#all img')
		image_urls = []
		if len(image_lists) > 0:
			for image_link in image_lists:
				link = image_link.get("data-src").strip()
				tmp_img_url = urljoin(url,link)
				image_urls.append({"url": tmp_img_url, "ref": url})
		return {"images":image_urls}
