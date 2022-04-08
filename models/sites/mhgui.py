from ..site import *

class MHGui(Site):
	URL_MATCH = ["manhuagui.com", "mhgui.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.mhgui.com"
		self._site_name = "漫画柜/看漫画"
		self._default_image_format = "webp"
		self._sample_url = ["https://www.mhgui.com/comic/19430/","https://www.manhuagui.com/comic/28004/"]
		self._IMAGE_URL_PREFIX = 'https://i.hamreus.com'

	def parse_list_from_url(self,url=''):
		book_id = self.parse_book_id_from_url(url)
		if book_id == "":
			return {}
		info = self._web_bot.get_web_content(url=url, code_page=self._code_page)
		if not info or info == "":
			return {}

		results = {}
		#print(info)
		#todo need handle mobile version
		pattern_title = re.compile(r'<div class="book-title"><h1>(.*?)</h1>')
		info_title = re.findall(pattern_title, info)
		if len(info_title) > 0 and info_title[0] != '':
			results["title"] = html.unescape(info_title[0].strip())
		else:
			results["title"] = "unknown"

		pattern_author = re.compile(r'<span><strong>漫画作者：</strong><a href="(.*?)" title="(.*?)">(.*?)</a></span>')
		info_author = re.findall(pattern_author, info)
		if len(info_author) > 0 and info_author[0][2] != '':
			results["author"] = html.unescape(info_author[0][2].strip())
		else:
			results["author"] = "unknown"

		pattern_book = re.compile(r'<h4><span>单行本</span></h4>(.*?)<div class="chapter-list cf mt10" id=\'chapter-list-[0-9]*\'>(.*?)</div>')
		pattern_chapter = re.compile(r'<h4><span>单话</span></h4>(.*?)<div class="chapter-list cf mt10" id=\'chapter-list-[0-9]*\'>(.*?)</div>')
		pattern_extra = re.compile(r'<h4><span>番外篇</span></h4>(.*?)<div class="chapter-list cf mt10" id=\'chapter-list-[0-9]*\'>(.*?)</div>')

		info_book = re.findall(pattern_book, info)
		info_chapter = re.findall(pattern_chapter, info)
		info_extra = re.findall(pattern_extra, info)

		if len(info_book) > 0:
			plists_book = self._parse_list_from_content(info=info_book[0][1],url=url)
			results["book"] = plists_book

		if len(info_chapter) > 0:
			plists_chapter = self._parse_list_from_content(info=info_chapter[0][1],url=url)
			results["chapter"] = plists_chapter

		if len(info_extra) > 0:
			plists_extra = self._parse_list_from_content(info=info_extra[0][1],url=url)
			results["extra"] = plists_extra

		#print(results)
		return results

	def download_item(self,item,title="",item_type=""):
		super(MHGui, self).download_item(item=item,title=title,item_type=item_type)
		#print(item)
		#final_url = self._home_url + item["url"]
		info = self._web_bot.get_web_content(url=item["url"], ref=item["ref"], code_page=self._code_page)
		#print(info)
		data = self._get_image_data_from_page(html=info)
		#print(data)

		image_urls = []
		for i in data['files']:
			url = self._IMAGE_URL_PREFIX + data['path'] + i + '?e=%(e)s&m=%(m)s' % (data['sl'])
			image_urls.append({"url":url,"ref":item["url"]})

		output_dir = self.download_image_lists(image_urls=image_urls,item=item,item_type=item_type,title=title)

		return output_dir

	def parse_book_id_from_url(self,url):
		pattern_book_id = re.compile(r'//(.*?)gui.com/comic/([^/]*)(/?)')

		plists = re.findall(pattern_book_id, url)
		if len(plists) > 0 and len(plists[0]) > 1:
			self._book_id = plists[0][1]
			return self._book_id
		return ""

	# internal function
	@staticmethod
	def _parse_list_from_content(info,url):
		#print(info)
		pattern_page = re.compile(r'<ul([^>]*?)>(.*?)</ul>')
		pages = re.findall(pattern_page, info)

		results = []
		index = 1
		for page in pages:
			pattern_list = re.compile(r'<li><a href="([^"]*)" title="([^"]*)" class="status0" target="_blank"><span>([^"]*)<i>([^"]*)</i>(.*?)</span></a></li>')
			plists = re.findall(pattern_list, page[1])
			plists.reverse()

			for plist in plists:
				tmp_url = urljoin(url, plist[0])
				results.append({"title":plist[1], "url":tmp_url, "index": index, "ref":url})
				index += 1
				#print("add %s %s" % (plist[1], plist[0]))

		return results

	@staticmethod
	def _get_image_data_from_page(html):
		js = re.search(r">window.*(\(function\(p.*?)</script>", html).group(1)
		b64_str = re.search(r"[0-9],'([A-Za-z0-9+/=]+?)'", js).group(1)
		s = lzstring.LZString.decompressFromBase64(b64_str)
		new_js = re.sub(r"'[A-Za-z0-9+/=]*'\[.*\]\('\\x7c'\)", "'" + s + "'.split('|')", js)
		res = execjs.eval(new_js)
		return json.loads(re.search(r"(\{.*\})", res).group(1))

