import re
import bs4
import html
#import os
#import execjs
from urllib.parse import urljoin,parse_qs,urlparse

from models.site import Site

class Dongmanmanhua(Site):
	URL_MATCH = ["dongmanmanhua.cn"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.dongmanmanhua.cn"
		self._site_name = "咚漫漫画"
		self._sample_url = [
			"https://www.dongmanmanhua.cn/ANCIENTCHINESE/chongshengzhijinxiudatang/list?title_no=2209",
			"https://www.dongmanmanhua.cn/BOY/jietoushegncunshouce/list?title_no=1720",
		]
		# change is need
		self._accept_language = "zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3"

	def get_book_id_from_url(self,url):
		parsed_query = parse_qs(urlparse(url).query)
		if 'title_no' in parsed_query:
			title_no = parse_qs(urlparse(url).query)['title_no'][0]
			# print("title no:"+title_no)
			return title_no
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		return self._home_url + "/_/_/list?title_no="+self._book_id

	def get_book_title_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_title = bs.select('div.info h1.subj')
		if tmp_title and len(tmp_title) > 0:
			title = html.unescape(tmp_title[0].text.strip())
			# print("title:"+title)
			return title
		return "unknown"

	def get_book_author_from_html(self,html_code):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		tmp_author = bs.select('div.info span.author')
		if tmp_author and len(tmp_author) > 0:
			tmp_author = str(tmp_author[0])
			pattern_author = re.compile(r'<span class="author">(.*?)<a class', re.DOTALL)
			info_author = re.findall(pattern_author, tmp_author)
			if len(info_author) > 0:
				author = info_author[0].replace("\n"," ")
				author = ' '.join(author.split())
				author = author.strip()
				author = html.unescape(author)
				# print("author:"+author)
				return author
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		chapters = []
		while True:
			page_chapters = self._get_chapters_from_page(html_code, url)
			if len(page_chapters) > 0:
				chapters.extend(page_chapters)
			next_page_no, next_page_url = self._get_next_page_url(html_code, url)
			if next_page_url != "":
				self.page_trigger.emit(next_page_no)
				html_code = self._web_bot.get_web_content(
					url=next_page_url, code_page=self._code_page,cookie=self._cookies
				)
			else:
				break

		if len(chapters) > 0:
			chapters.reverse()
			return {"chapter":chapters}

		return {}

	def get_image_list_from_html(self,html_code,url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		imgs = bs.find('div', {'id': '_imageList'}).find_all('img')
		image_urls = []
		for img in imgs:
			img_url = urljoin(url,img.get('data-url'))
			if "_warning.png" not in img_url:
				image_urls.append({"url":img_url,"ref":url})
		return {"images":image_urls}

	def _get_chapters_from_page(self,html_code,url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		chapters = []
		for li in bs.find('ul', {'id': '_listUl'}).find_all('li'):
			href = li.a.get('href')
			title = li.find('span', {'class': 'subj'}).text.strip()
			index = li.find('span', {'class': 'tx'}).text.replace("#","")
			chapter_url = urljoin(url, href)
			chapters.append({"url":chapter_url,"title":title,"index":index,"ref":url})
		return chapters

	def _get_next_page_url(self,html_code,url):
		bs = bs4.BeautifulSoup(html_code, 'html.parser')
		page_div = bs.find('div', {'class': 'paginate'})
		current_page_tag = page_div.find('a', {'href': '#'})
		next_page_tag = current_page_tag.find_next_sibling("a")
		if next_page_tag:
			href = next_page_tag['href']
			if href != "" and href != "#":
				page_url = urljoin(url,href)
				page_no = parse_qs(urlparse(page_url).query)['page'][0]
				return page_no, page_url
		return "",""
