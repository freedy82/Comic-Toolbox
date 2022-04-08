from ..site import *
from const import *

class CartoonMad(Site):
	URL_MATCH = ["cartoonmad.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.cartoonmad.com"
		self._site_name = "動漫狂"
		self._code_page = "big5"
		self._sample_url = ["https://www.cartoonmad.com/comic/5033.html"]
		#self._PAGE_URL_PREFIX = 'https://www.cartoonmad.cc/comic/'

	def parse_list_from_url(self,url=''):
		site_id = self.parse_book_id_from_url(url)
		if site_id == "":
			return {}

		info = self._web_bot.get_web_content(url=url, code_page=self._code_page)
		if not info or info == "":
			return {}

		#print(info)
		bs = bs4.BeautifulSoup(info, 'html.parser')
		chapters = bs.select('#info a[href^="/comic/"]')
		tmp_title = bs.select('td[style="font-size:12pt;color:#000066"] a[href^="/comic/"]')
		if tmp_title and len(tmp_title) > 0:
			title = html.unescape(tmp_title[0].text.strip())
		else:
			title = "unknown"
		pattern_author = re.compile(r'原創作者：(.*?)</td>')
		author_plists = re.findall(pattern_author, info)
		if len(author_plists) > 0:
			author = html.unescape((re.findall(pattern_author, info))[0].strip())
		else:
			author = "unknown"

		results = {"chapter": [], "title": title, "author":author}
		index = 1
		pattern_link = re.compile(r'<a href="([^"]*)" target="_blank">(.*)</a>')
		#print("chapters",chapters)
		if len(chapters) > 0:
			for chapter in chapters:
				#print("chapter",chapter)
				chapter_info = re.findall(pattern_link, str(chapter))
				#print(chapter_info)
				if len(chapter_info)> 0:
					tmp_url = urljoin(url, chapter_info[0][0])
					results["chapter"].append({"title": chapter_info[0][1], "url": tmp_url, "index": index, "ref":url})
					index += 1
		else:
			return {}

		#print(results)
		return results

	def download_item(self,item,title="",item_type=""):
		output_dir = super(CartoonMad, self).download_item(item=item,title=title,item_type=item_type)
		#print(item)
		#final_url = self._home_url + item["url"]
		info = self._web_bot.get_web_content(url=item["url"], ref=item["ref"], code_page=self._code_page)

		bs = bs4.BeautifulSoup(info, features='html.parser')
		page_lists = bs.select('option[value]')

		pages = []
		for idx, page_link in enumerate(page_lists, start=1):
			tmp_url = urljoin(item["url"], page_link.attrs["value"])
			#ext = self.get_ext(tmp_url,self.default_image_format)
			target_file = os.path.join(output_dir.rstrip(), str(idx).zfill(int(MY_CONFIG.get("general", "image_padding"))))
			pages.append({"url":tmp_url,"ref":item["url"],"file":target_file})

		#print(pages)
		self.download_single_page_image_from_list(pages)
		return output_dir

	def parse_book_id_from_url(self,url):
		# https://www.cartoonmad.com/comic/####.html
		pattern_book_id = re.compile(r'//(.*?)cartoonmad.(.*?)/comic/(.*?)\.html')
		plists = re.findall(pattern_book_id, url)
		if len(plists) > 0 and len(plists[0]) > 2:
			self._book_id = plists[0][2]
			return self._book_id
		return ""

	def extract_single_page_image_from_info(self,html):
		bs = bs4.BeautifulSoup(html, features='html.parser')
		img_src = bs.select('img[src^="https://www.cartoonmad.com/comic/comicpic.asp"]')[0].attrs['src']
		return img_src

