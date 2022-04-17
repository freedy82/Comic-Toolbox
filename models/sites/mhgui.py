from ..site import *

class MHGui(Site):
	URL_MATCH = ["manhuagui.com", "mhgui.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.mhgui.com"
		self._site_name = "漫画柜/看漫画"
		self._default_image_format = "webp"
		self._sample_url = ["https://www.mhgui.com/comic/19430/","https://www.manhuagui.com/comic/28004/"]
		self._image_url_prefix = 'https://i.hamreus.com'

	def get_book_id_from_url(self,url):
		pattern_book_id = re.compile(r'//(.*?)gui.com/comic/([^/]*)(/?)')

		plists = re.findall(pattern_book_id, url)
		if len(plists) > 0 and len(plists[0]) > 1:
			self._book_id = plists[0][1]
			return self._book_id
		return ""

	def get_book_title_from_html(self,html_code):
		pattern_title = re.compile(r'<div class="book-title"><h1>(.*?)</h1>')
		info_title = re.findall(pattern_title, html_code)
		if len(info_title) > 0 and info_title[0] != '':
			title = html.unescape(info_title[0].strip())
		else:
			title = "unknown"
		return title

	def get_book_author_from_html(self,html_code):
		pattern_author = re.compile(r'<span><strong>漫画作者：</strong><a href="(.*?)" title="(.*?)">(.*?)</a></span>')
		info_author = re.findall(pattern_author, html_code)
		if len(info_author) > 0 and info_author[0][2] != '':
			author = html.unescape(info_author[0][2].strip())
		else:
			author = "unknown"
		return author

	def get_book_item_list_from_html(self, html_code, url):
		results = {}
		pattern_book = re.compile(r'<h4><span>单行本</span></h4>(.*?)<div class="chapter-list cf mt10" id=\'chapter-list-[0-9]*\'>(.*?)</div>')
		pattern_chapter = re.compile(r'<h4><span>单话</span></h4>(.*?)<div class="chapter-list cf mt10" id=\'chapter-list-[0-9]*\'>(.*?)</div>')
		pattern_extra = re.compile(r'<h4><span>番外篇</span></h4>(.*?)<div class="chapter-list cf mt10" id=\'chapter-list-[0-9]*\'>(.*?)</div>')
		info_book = re.findall(pattern_book, html_code)
		info_chapter = re.findall(pattern_chapter, html_code)
		info_extra = re.findall(pattern_extra, html_code)

		if len(info_book) > 0:
			plists_book = self._parse_list_from_content(info=info_book[0][1],url=url)
			results["book"] = plists_book
		if len(info_chapter) > 0:
			plists_chapter = self._parse_list_from_content(info=info_chapter[0][1],url=url)
			results["chapter"] = plists_chapter
		if len(info_extra) > 0:
			plists_extra = self._parse_list_from_content(info=info_extra[0][1],url=url)
			results["extra"] = plists_extra

		return results

	def download_item(self,item,title="",item_type=""):
		output_dir = super(MHGui, self).download_item(item=item,title=title,item_type=item_type)
		html_code = self._web_bot.get_web_content(url=item["url"], ref=item["ref"], code_page=self._code_page)
		data = self._get_image_data_from_page(html_code=html_code)

		image_urls = []
		for i in data['files']:
			url = self._IMAGE_URL_PREFIX + data['path'] + i + '?e=%(e)s&m=%(m)s' % (data['sl'])
			image_urls.append({"url":url,"ref":item["url"]})

		#print(image_urls)
		self.download_image_lists(image_urls=image_urls,item=item,item_type=item_type,title=title)
		return output_dir

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
	def _get_image_data_from_page(html_code):
		#JScript Version
		# js = re.search(r">window.*(\(function\(p.*?)</script>", html).group(1)
		# b64_str = re.search(r"[0-9],'([A-Za-z0-9+/=]+?)'", js).group(1)
		# s = lzstring.LZString.decompressFromBase64(b64_str)
		# new_js = re.sub(r"'[A-Za-z0-9+/=]*'\[.*\]\('\\x7c'\)", "'" + s + "'.split('|')", js)
		# os.environ["EXECJS_RUNTIME"] = "JScript"
		# res = execjs.eval(new_js)
		# return json.loads(re.search(r"(\{.*\})", res).group(1))

		# ref https://github.com/HSSLC/manhuagui-dlr/blob/c5279901b68d5627d202142d6785ac26f2689516/get.py#L10
		if html_code != "":
			m = re.match(r'^.*\}\(\'(.*)\',(\d*),(\d*),\'([\w|\+|\/|=]*)\'.*$', html_code)
			result = MHGui.packed(m.group(1), int(m.group(2)), int(m.group(3)), lzstring.LZString.decompressFromBase64(m.group(4)).split('|'))
			#print(result)
			return result
		return {}

	@staticmethod
	def packed(functionFrame, a, c, data):
		def e(innerC):
			return ('' if innerC < a else e(int(innerC / a))) + (
				chr(innerC % a + 29) if innerC % a > 35 else MHGui.atr(innerC % a, 36))
		c -= 1
		d = {}
		while c + 1:
			d[e(c)] = e(c) if data[c] == '' else data[c]
			c -= 1
		pieces = re.split(r'(\b\w+\b)', functionFrame)
		js = ''.join([d[x] if x in d else x for x in pieces]).replace('\\\'', '\'')
		return json.loads(re.search(r'^.*\((\{.*\})\).*$', js).group(1))

	@staticmethod
	def itr(value, num):
		d = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
		return '' if value <= 0 else MHGui.itr(int(value / num), num) + d[value % num]

	@staticmethod
	def atr(value, num):
		tmp = MHGui.itr(value, num)
		return '0' if tmp == '' else tmp