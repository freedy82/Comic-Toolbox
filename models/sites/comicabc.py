import re
import bs4
import html
import execjs
from urllib.parse import parse_qs, unquote, urlencode, urljoin, urlsplit

from models.site import Site

class ComicABC(Site):
	URL_MATCH = ["comicabc.com","8comic.com","comicbus.com","comicvip.com","articles.onemoreplace.tw"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.8comic.com"
		self._site_name = "無限動漫 (8comic)"
		self._sample_url = ["https://www.8comic.com/html/11753.html","https://www.8comic.com/html/653.html"]
		self._page_prefix = "https://articles.onemoreplace.tw/online/new-"
		self._is_need_nodejs = True

	def get_book_id_from_url(self,url):
		match = re.fullmatch(r'/(?:html/|online/new-|view/)(\d+)\.html', urlsplit(url).path)
		if match:
			self._book_id = match.group(1)
			return self._book_id
		return ""

	def get_main_url_from_book_id(self):
		return f"{self._home_url}/html/{self._book_id}.html"

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_title = bs.select('div.item-top-content li h3')
		if tmp_title and len(tmp_title) > 0:
			title = html.unescape(tmp_title[0].text.strip())
		else:
			description = bs.select_one('meta[name="description"]')
			match = re.match(r'(.*?)\s*-\s*無限動漫', description.get("content", "")) if description else None
			title = match.group(1).strip() if match else "unknown"
		return title

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		current_author = bs.select_one('.item-info-author')
		if current_author:
			return re.sub(r'^作者\s*[:：]\s*', '', current_author.get_text(" ", strip=True))
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
		books = bs.select('#chapters a.Vol, #div_li1 a.Vol')
		chapters = bs.select('#chapters a.Ch, #div_li1 a.Ch')
		results = {"chapter": [], "book": []}

		index = 1
		if len(chapters) > 0:
			for chapter in chapters:
				parse_result = self._parse_chapter_link(chapter,url,index)
				if parse_result:
					results["chapter"].append(parse_result)
					index += 1

		index = 1
		if len(books) > 0:
			for book in books:
				parse_result = self._parse_chapter_link(book,url,index)
				if parse_result:
					results["book"].append(parse_result)
					index += 1
		#print(results)
		return results

	def get_image_list_from_html(self,html_code,url):
		if not html_code:
			self.chapter_trigger.emit("8comic: Could not load the chapter page.", 0, 0)
			return {"images": []}
		try:
			bs = bs4.BeautifulSoup(html_code, 'html.parser')
			images = self._get_rendered_images(bs, url)
			if images:
				return {"images": images}
			for script in bs.find_all('script', src=False):
				body = script.get_text()
				render = re.search(r'''\$\(\s*["']#comics-pics["']\s*\)\s*\.html\s*\(\s*[\w$]+\s*\)\s*;?''', body)
				if render:
					# Stop after image markup is generated; scrolling and browser UI are not needed.
					markup = self._render_reader(body[:render.end()], url)
					images = self._get_rendered_images(bs4.BeautifulSoup(markup, 'html.parser'), url)
					break
			else:
				images = [{"url": urljoin(url, image), "ref": url}
						  for image in self._get_legacy_images(html_code, url)]
			if not images:
				self.chapter_trigger.emit("8comic: No chapter images found; the reader format may have changed.", 0, 0)
			return {"images": images}
		except execjs.RuntimeUnavailableError:
			self.chapter_trigger.emit("8comic: Node.js is unavailable. Install Node.js and restart PyCharm.", 0, 0)
		except Exception as exc:
			self.chapter_trigger.emit(f"8comic: Could not decode chapter images: {exc}", 0, 0)
		return {"images": []}

	@staticmethod
	def _get_rendered_images(bs, url):
		images = []
		for image in bs.select('#comics-pics img, .comics-pic img'):
			source = image.get('s') or image.get('data-src') or image.get('src')
			if source:
				image_url = urljoin(url, unquote(source))
				if urlsplit(image_url).scheme in ('http', 'https'):
					images.append({"url": image_url, "ref": url})
		return images

	@staticmethod
	def _render_reader(script, url):
		# These three helpers are used by the inline reader's chapter/page decoder.
		runtime = execjs.get('Node')
		context = runtime.compile(r"""
			function renderReader(source, pageUrl) {
				var location = {href: pageUrl, toString: function() { return this.href; }};
				var document = {location: location};
				var window = {location: location, document: document};
				var markup = '';
				function $(selector) {
					return {html: function(value) { markup = value; }};
				}
				function lc(value) {
					if (value.length !== 2) return value;
					var alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
					var last = alphabet.indexOf(value[1]);
					return value[0] === 'Z' ? 8000 + last : alphabet.indexOf(value[0]) * 52 + last;
				}
				function nn(page) { return String(page).padStart(3, '0'); }
				function mm(page) { return Math.floor((page - 1) / 10) % 10 + (page - 1) % 10 * 3; }
				eval(source);
				return markup;
			}
		""")
		return context.call('renderReader', script, url)

	def _get_legacy_images(self,html_code,url):
		reader = bs4.BeautifulSoup(html_code, 'html.parser').find('script', src=re.compile(r'nview\.js', re.I))
		if reader is None:
			return []
		nview = urljoin(url, reader['src'])
		nview = self._web_bot.get_web_content(url=nview, ref=url, code_page=self._code_page)

		try:
			# http://www.comicbus.com/html/103.html
			script = re.search(r'(var ch=.+?)spp\(\)', html_code, re.DOTALL).group(1)
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

		ctx = execjs.get('Node').compile(html)
		return ctx.call('getImages', url)

	# internal function
	def _parse_chapter_link(self,link,url,default_index):
		match = re.search(r'''\bcview\s*\(\s*["'](\d+)-([^"']+)\.html["']''', link.get('onclick', ''))
		if match:
			book_id, chapter = match.groups()
		else:
			parsed = urlsplit(urljoin(url, link.get('href', '')))
			match = re.fullmatch(r'/(?:online/new-|view/)(\d+)\.html', parsed.path)
			if not match:
				return None
			book_id = match.group(1)
			chapter = parse_qs(parsed.query).get('ch', [str(default_index)])[0]
		# Reader appearance/resume fragments are not required to fetch chapter images.
		query = urlencode({'ch': chapter, 'ccTheme': 'day'})
		chapter_url = f"{self._page_prefix}{book_id}.html?{query}"
		return {"title": link.get_text(" ", strip=True), "url": chapter_url, "index": chapter, "ref": url}

