from ..site import *

class Kumw5(Site):
	URL_MATCH = ["kumw5.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "http://www.kumw5.com"
		self._site_name = "酷漫屋"
		self._code_page = "utf-8"
		self._sample_url = ["http://www.kumw5.com/16041/","http://www.kumw5.com/mulu/16041/1-1.html"]

	def parse_list_from_url(self,url=''):
		book_id = self.parse_book_id_from_url(url)
		if book_id == "":
			return {}

		url = "http://www.kumw5.com/mulu/" + book_id + "/1-1.html"
		info = self._web_bot.get_web_content(url=url, code_page=self._code_page)
		#print(info)
		if not info or info == "":
			return {}

		results = {}
		pattern_title = re.compile(r'首页</a>&gt;<a href="(.*?)" style=" color: #999; margin: 0 5px;">(.*?)</a></div>')
		info_title = re.findall(pattern_title, info)
		#print(info_title)
		if info_title and info_title[0][1] != '':
			results["title"] = html.unescape(info_title[0][1].strip())
		else:
			results["title"] = "unknown"

		results["author"] = "unknown"

		pattern_chapter = re.compile(r'<li><a href="([^"]*?)" rel="nofollow">(.*?)</a>(.*?)</li>')
		info_chapter = re.findall(pattern_chapter, info)

		if len(info_chapter) > 0:
			chapters = []
			info_chapter.reverse()
			for idx, tmp_chapter in enumerate(info_chapter, start=1):
				tmp_chapter_title = re.sub("<span>(.*?)</span>","",tmp_chapter[1])
				tmp_url = urljoin(url, tmp_chapter[0])
				chapters.append({"url":tmp_url,"title":tmp_chapter_title,"index":idx,"ref":url})

			results["chapter"] = chapters
		else:
			return {}

		#print(results)
		return results

	def download_item(self,item,title="",item_type=""):
		super(Kumw5, self).download_item(item=item,title=title,item_type=item_type)
		#print(item)
		#final_url = self._home_url + item["url"]
		info = self._web_bot.get_web_content(url=item["url"], ref=item["ref"], code_page=self._code_page)
		pattern_image_list = re.compile(r"var km5_img_url='(.*?)'")
		plists = re.findall(pattern_image_list, info)
		if len(plists) > 0:
			tmp_lists = json.loads(base64.b64decode(plists[0]))
			image_urls = []
			for tmp_list in tmp_lists:
				idx, tmp_img_url = tmp_list.split("|",1)
				tmp_img_url = tmp_img_url.strip()
				if tmp_img_url.startswith("//"):
					tmp_img_url = "http:" + tmp_img_url
				image_urls.append({"url":tmp_img_url,"ref":item["url"]})

			output_dir = self.download_image_lists(image_urls=image_urls,item=item,item_type=item_type,title=title)
			return output_dir
		return None

	def parse_book_id_from_url(self,url):
		# http://www.kumw5.com/####/
		# http://www.kumw5.com/mulu/####/1-1.html
		pattern_book_id1 = re.compile(r'//(.*?)kumw5.(.*?)/mulu/([0-9]?)/(.*?)\.html')
		pattern_book_id2 = re.compile(r'//(.*?)kumw5.(.*?)/([0-9]*?)/')
		plists1 = re.findall(pattern_book_id1, url)
		if len(plists1) > 0 and len(plists1[0]) > 2:
			self._book_id = plists1[0][2]
			return self._book_id
		plists2 = re.findall(pattern_book_id2, url)
		if len(plists2) > 0 and len(plists2[0]) > 2:
			self._book_id = plists2[0][2]
			return self._book_id
		return ""

