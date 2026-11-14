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
		self._sample_url = ["https://www.dm5.com/manhua-shanhainizhan1/","https://www.dm5.com/manhua-jiandieguojiajia/"]
		self._cookies = {
			"isAdult": "1",
			"fastshow": "true",
			"ComicHistoryitem_zh": "ViewType=1"
		}
		self._accept_language = "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"

	def get_book_id_from_url(self,url):
		match = re.fullmatch(r'/manhua-([^/]+)/?', urllib.parse.urlsplit(url).path)
		if match:
			self._book_id = match.group(1)
			return self._book_id
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		return f"{self._home_url}/manhua-{self._book_id}/"

	def parse_list(self):
		results = super().parse_list()
		if not results:
			self.page_trigger.emit("DM5: Could not read comic details. Check site access and DNS settings.")
		return results

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		title = bs.select_one('div.info > p.title')
		if title:
			for decoration in title.select('.right'):
				decoration.decompose()
			return title.get_text(' ', strip=True)
		return "unknown"

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_author = bs.select('div.info p.subtitle')
		if tmp_author and len(tmp_author) > 0:
			author = tmp_author[0].get_text(' ', strip=True)
			author = html.unescape(re.sub(r'^作者\s*[:：]\s*', '', author))
			return author
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		results = {}
		for number, item_type in enumerate(('chapter', 'book', 'extra'), start=1):
			container = bs.select_one(f'#detail-list-select-{number}')
			if container:
				results[item_type] = self._parse_list_from_content(info=str(container),url=url)
		if not any(results.values()):
			self.page_trigger.emit("DM5: No chapter links found in the comic page.")
		return results

	def get_image_list_from_html(self,html_code,url):
		if not html_code:
			self.chapter_trigger.emit("DM5: Could not load the chapter page. Check site access and DNS settings.", 0, 0)
			return {"images": []}
		try:
			bs = bs4.BeautifulSoup(html_code, 'html.parser')
			image_urls = []
			for image in bs.select('#barChapter img'):
				source = image.get('data-src') or image.get('data-original') or image.get('src')
				if source and not re.search(r'/(?:new)?loading\d*\.gif(?:\?|$)', source, re.I):
					image_urls.append({"url": urljoin(url, source), "ref": url})
			if image_urls:
				return {"images": image_urls}

			count = int(self._script_value(html_code, 'DM5_IMAGE_COUNT') or 0)
			cid = self._script_value(html_code, 'DM5_CID')
			mid = self._script_value(html_code, 'DM5_MID') or self._script_value(html_code, 'COMIC_MID')
			sign = self._script_value(html_code, 'DM5_VIEWSIGN')
			dt = self._script_value(html_code, 'DM5_VIEWSIGN_DT')
			if count <= 0 or not cid or not mid or sign is None or dt is None:
				raise ValueError('chapter image details are missing; the page may require login or payment')
			key_input = bs.select_one('#dm5_key')
			key = key_input.get('value', '') if key_input else ''

			page_urls = []
			for page in range(count):
				params = {
					'cid': cid,
					'_cid': cid,
					'page': page+1,
					'key': key,
					'language': '1',
					'gtk': '6',
					'_mid': mid,
					'_dt': dt,
					'_sign': sign
				}
				page_url = urljoin(url, "chapterfun.ashx?"+urllib.parse.urlencode(params,doseq=True))
				page_urls.append({"url":page_url,"ref":url})
			return {"pages":page_urls}
		except Exception as exc:
			self.chapter_trigger.emit(f"DM5: Could not read chapter images: {exc}", 0, 0)
			return {"images": []}

	# use only need for page list
	def get_single_page_image_from_html(self, html_code,url):
		try:
			if not html_code:
				raise ValueError('the image loader returned no data')
			js_str = jsbeautifier.beautify(html_code)
			match = re.search(r'\bpvalue\s*=\s*(\[.*?\])\s*;', js_str, re.DOTALL)
			if not match:
				raise ValueError('the image loader did not return a page list')
			data = json.loads(match.group(1))
			if not data or not isinstance(data[0], str):
				raise ValueError('the image loader returned an empty page list')
			image_file = data[0]
			if urllib.parse.urlsplit(image_file).path.lstrip('/').lower() == 'images/war.jpg':
				raise ValueError('the site returned its shared images/war.jpg image instead of a comic page; check chapter access in your browser')
			# The current loader leaves absolute, already signed image URLs unchanged.
			if image_file.startswith(('https://', 'http://', '//')):
				return urljoin(url, image_file)
			pix = self._script_value(js_str, 'pix')
			cid = self._script_value(js_str, 'cid')
			key = self._script_value(js_str, 'key')
			if not pix or not cid or key is None:
				raise ValueError('the image loader response is missing URL details')
			# DM5 appends paths such as '/2_4711.jpg' to the chapter prefix literally.
			# urljoin() would discard '/34/33991/521974' and request the CDN root.
			image_url = pix + image_file
			parsed = urllib.parse.urlsplit(image_url)
			query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
			query.extend((('cid', cid), ('key', key)))
			return parsed._replace(query=urllib.parse.urlencode(query)).geturl()
		except Exception as exc:
			# Return a failed page normally so the download queue can finish its task.
			self.chapter_trigger.emit(f"DM5: Could not read a page image: {exc}", self._current_finish_download, self._final_total_download)
			return ''

	@staticmethod
	def _script_value(source, name):
		pattern = r'''\b''' + re.escape(name) + r'''\s*=\s*(?:"([^"]*)"|'([^']*)'|(\d+))\s*;'''
		match = re.search(pattern, source)
		return next((value for value in match.groups() if value is not None), None) if match else None

	def _parse_list_from_content(self,info,url):
		bs = bs4.BeautifulSoup(info, 'html.parser')
		results = []
		seen = set()
		for link in bs.select('a[href]'):
			tmp_url = urljoin(url, link['href'])
			if not re.fullmatch(r'/m\d+/?', urllib.parse.urlsplit(tmp_url).path) or tmp_url in seen:
				continue
			seen.add(tmp_url)
			title_node = link.select_one('p.title') or link
			title = title_node.get_text(' ', strip=True)
			title = re.sub(r'[（(]\s*\d+\s*[Pp]\s*[）)]', '', title).strip()
			if not title:
				title = link.get('title', '').strip()
			results.append({"title": title, "url": tmp_url, "ref": url})
		# New chapter cards are already ascending; older lists can be descending.
		numbers = [re.search(r'第\s*(\d+(?:\.\d+)?)\s*[话話回章节節卷集册冊]', item['title']) for item in results]
		numbers = [float(match.group(1)) for match in numbers if match]
		if len(numbers) > 1 and numbers[0] > numbers[-1]:
			results.reverse()
		for index, item in enumerate(results, start=1):
			item['index'] = str(index)
		return results
