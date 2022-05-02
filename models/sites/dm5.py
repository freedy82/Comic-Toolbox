import json
import re
import urllib.parse

import bs4
import html
import jsbeautifier
from urllib.parse import urljoin

from models.site import Site

class DM5(Site):
	URL_MATCH = ["dm5.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.dm5.com"
		self._site_name = "动漫屋"
		self._sample_url = ["https://www.dm5.com/manhua-jiandieguojiajia/","https://www.dm5.com/manhua-longzhuchao/"]
		self._cookies = {
			"isAdult": "1",
			"fastshow": "true",
			"ComicHistoryitem_zh": "ViewType=1"
		}
		self._accept_language = "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"

	def get_book_id_from_url(self,url):
		pattern_book_id = re.compile(r'//(.*?)dm5.com/manhua-([^/]*)(/?)')

		plists = re.findall(pattern_book_id, url)
		if len(plists) > 0 and len(plists[0]) > 1:
			self._book_id = plists[0][1]
			return self._book_id
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		return self.get_main_url()

	def get_book_title_from_html(self,html_code):
		pattern_title = re.compile(r'<div class="info">(.*?)<p class="title">(.*?)<span class="right">')
		info_title = re.findall(pattern_title, html_code)
		if info_title and info_title[0][1] != '':
			title = html.unescape(info_title[0][1].strip())
			return title
		return "unknown"

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_author = bs.select('div.info p.subtitle')
		if tmp_author and len(tmp_author) > 0:
			author = tmp_author[0].text.strip()
			author = html.unescape(author.replace("作者：","").strip())
			return author
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		chapters = bs.select('ul#detail-list-select-1')
		books = bs.select('ul#detail-list-select-2')
		extras = bs.select('ul#detail-list-select-3')

		results = {}
		if len(chapters) > 0:
			plists_chapter = self._parse_list_from_content(info=str(chapters[0]),url=url)
			results["chapter"] = plists_chapter
		if len(books) > 0:
			plists_book = self._parse_list_from_content(info=str(books[0]),url=url)
			results["book"] = plists_book
		if len(extras) > 0:
			plists_extra = self._parse_list_from_content(info=str(extras[0]),url=url)
			results["extra"] = plists_extra

		return results

	def get_image_list_from_html(self,html_code,url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		div = bs.find('div', {'id': 'barChapter'})
		if div:
			img_urls = [img.get('data-src') for img in div.find_all('img', recursive=False)]
			image_urls = []
			for img_url in img_urls:
				image_urls.append({"url":img_url,"ref":url})
			return {"images": image_urls}
		else:
			count = int(re.search("DM5_IMAGE_COUNT=(\d+);", html_code).group(1))
			sign = re.search(r'var DM5_VIEWSIGN="(.*?)";', html_code).group(1)
			dt = re.search(r'var DM5_VIEWSIGN_DT="(.*?)";', html_code).group(1)
			mid = re.search(r'var COMIC_MID = (\d*);', html_code).group(1)
			cid = re.search(r"DM5_CID=(\d+);", html_code).group(1)

			page_urls = []
			for page in range(count):
				params = {
					'cid': cid,
					'_cid': cid,
					'page': page+1,
					'key': '',
					'language': '1',
					'gtk': '6',
					'_mid': mid,
					'_dt': dt,
					'_sign': sign
				}
				page_url = urljoin(url, "chapterfun.ashx?"+urllib.parse.urlencode(params,doseq=True))
				page_urls.append({"url":page_url,"ref":url})
			return {"pages":page_urls}

	# use only need for page list
	def get_single_page_image_from_html(self, html_code,url):
		js_str = jsbeautifier.beautify(html_code)
		cid = re.search(r"var cid = (.*?);", js_str).group(1)
		key = re.search(r"var key = '(.*?)';", js_str).group(1)
		pvalue = re.search(r'var pvalue = (\[.*?\]);', js_str).group(1)
		pix = re.search(r'var pix = "(.*?)";', js_str).group(1)
		data = json.loads(pvalue)
		image_file = data[0]
		image_url = '%s%s?cid=%s&key=%s' % (pix, image_file, cid, key)
		return image_url

	def _parse_list_from_content(self,info,url):
		pattern_list = re.compile(
			r'<a href="([^"]*)"(.*?)title="([^"]*)">([^"]*?)<span>([^"]*?)</span>')
		plists = re.findall(pattern_list, info)
		plists.reverse()

		results = []
		index = 1
		for plist in plists:
			tmp_url = urljoin(url, plist[0])
			results.append({"title": plist[3], "url": tmp_url, "index": str(index), "ref": url})
			index += 1
		return results
