import re
import bs4
import html
import os
import execjs
from urllib.parse import urljoin

from models.site import Site

class ComicABC(Site):
	URL_MATCH = ["comicabc.com","8comic.com","comicbus.com","comicvip.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.comicabc.com"
		self._site_name = "無限動漫"
		self._sample_url = ["https://www.comicabc.com/html/7257.html","https://www.8comic.com/html/653.html"]
		self._page_prefix = "https://www.comicabc.com/online/new-"
		self._is_need_nodejs = True

	def get_book_id_from_url(self,url):
		# https://www.comicabc.com/html/####.html
		# https://www.8comic.com/html/653.html
		pattern_book_id1 = re.compile(r'//(.*?)/html/(.*?)\.html')
		plists = re.findall(pattern_book_id1, url)
		if len(plists) > 0 and len(plists[0]) > 1:
			self._book_id = plists[0][1]
			return self._book_id
		return ""

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_title = bs.select('div.item-top-content li h3')
		if tmp_title and len(tmp_title) > 0:
			title = html.unescape(tmp_title[0].text.strip())
		else:
			title = "unknown"
		return title

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_author = bs.select('div.item-top-content li.item_detail_color_gray')
		author = "unknown"
		if tmp_author and len(tmp_author) > 1:
			pattern_author = re.compile(r'<a(.*?)>(.*?)</a>(.*?)</li>',re.DOTALL)
			author_plists = re.findall(pattern_author, str(tmp_author[1]))
			if len(author_plists) >= 1:
				author = author_plists[0][2].strip()
		return author

	def get_book_item_list_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		books = bs.select('#div_li1 a.Vol')
		chapters = bs.select('#div_li1 a.Ch')
		results = {"chapter": [], "book": []}
		pattern_link = re.compile(r"<a (.*?)cview\('(.*?)',[0-9]*?,[0-9]*?\);(.*?)>(.*?)</a>",re.DOTALL)

		index = 1
		if len(chapters) > 0:
			for chapter in chapters:
				parse_result = self._parse_link_from_html(chapter,pattern_link,url,index)
				if parse_result:
					results["chapter"].append(parse_result)
					index += 1

		index = 1
		if len(books) > 0:
			for book in books:
				parse_result = self._parse_link_from_html(book,pattern_link,url,index)
				if parse_result:
					results["book"].append(parse_result)
					index += 1
		#print(results)
		return results

	def get_image_list_from_html(self,html_code,url):
		nview = re.search('src="([^"]*nview\.js[^"]*)"', html_code).group(1)
		nview = urljoin(url, nview)
		nview = self._web_bot.get_web_content(url=nview, ref=url, code_page=self._code_page)

		try:
			# http://www.comicbus.com/html/103.html
			script = re.search('(var ch=.+?)spp\(\)', html_code, re.DOTALL).group(1)
		except AttributeError:
			# http://www.comicbus.com/html/7294.html
			script = re.search('(var chs=.+?)</script>', html_code, re.DOTALL).group(1)

		html = """
			var url;
			var images = [];
			var document = {
				location: {
					toString() {return url;},
					get href() {return url;},
					set href(_url) {url = _url; scriptBody()}
				},
				getElementById() {
					return {
						set src(value) {
							images.push(value);
						},
						style: {}
					};
				}
			};
			var navigator = {
				userAgent: "",
				language: ""
			};
			var window = {};
			var alert = () => {};

			function scriptBody() {
				initpage = () => {};
			""" + nview + script + """
				jn();
			}

			function getImages(url) {
				images = [];
				document.location.href = url;
				return images;
			}
		"""

		try:
			# os.environ["EXECJS_RUNTIME"] = "JScript"
			os.environ["EXECJS_RUNTIME"] = "NodeJS"
			ctx = execjs.compile(html)
			images = ctx.call('getImages', url)
		# print(images)
		except Exception:
			images = []

		image_urls = []
		for img in images:
			url = urljoin(url, img)
			image_urls.append({"url": url, "ref": url})

		return {"images":image_urls}

	# internal function
	@staticmethod
	def _parse_link_from_html(html_code,pattern_link,url,default_index):
		chapter_info = re.findall(pattern_link, str(html_code))
		# print(chapter_info)
		if len(chapter_info) > 0:
			tmp_url = chapter_info[0][1]
			tmp_url = tmp_url.replace(".html", "").replace("-", ".html?ch=")
			tmp_url = urljoin(url, tmp_url).replace("/html/", "/online/new-")
			tmp_ch_title = chapter_info[0][3].strip()
			bs_ch = bs4.BeautifulSoup(tmp_ch_title, 'html.parser')
			tmp_ch_title = bs_ch.getText().strip()
			prefix, ch = tmp_url.split("?ch=")
			return {"title": tmp_ch_title, "url": tmp_url, "index": ch, "ref": url}
		return None

