import json
import re
import bs4
import html
import os
import execjs
from urllib.parse import urljoin

from models.site import Site

class MangaDex(Site):
	URL_MATCH = ["mangadex.org"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://mangadex.org/"
		self._site_name = "MangaDex"
		self._sample_url = ["https://mangadex.org/title/859e3107-f37e-46b8-954c-1318b5c63c9c/ghost-in-the-shell-stand-alone-complex","https://mangadex.org/title/80422e14-b9ad-4fda-970f-de370d5fa4e5/made-in-abyss?page=1"]
		self._api_url = "https://api.mangadex.org"

	def get_book_id_from_url(self,url):
		#todo parse id from url
		pattern_book_id = re.compile(r'//mangadex.org/title/([^/]*?)/')
		plists = re.findall(pattern_book_id, url)
		if len(plists) > 0:
			self._book_id = plists[0]
			return self._book_id
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		new_main_url = f"{self._api_url}/manga/{self._book_id}?includes[]=artist&includes[]=author&includes[]=cover_art"
		return new_main_url

	def get_book_title_from_html(self,html_code):
		json_obj = json.loads(html_code)
		tmp_title_info = json_obj["data"]["attributes"]["title"]
		for lang in tmp_title_info:
			return tmp_title_info[lang]
		return "unknown"

	def get_book_author_from_html(self,html_code):
		json_obj = json.loads(html_code)
		tmp_relationships_info = json_obj["data"]["relationships"]
		for tmp_relationship in tmp_relationships_info:
			if tmp_relationship["type"] == "author" or tmp_relationship["type"] == "artist":
				return tmp_relationship["attributes"]["name"]
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		if self._book_id != "":
			limit = 500
			offset = 0
			tmp_chapter_list = []
			while True:
				api_url = f'{self._api_url}/manga/{self._book_id}/feed?limit={limit}&includes[]=scanlation_group&includes[]=' \
					f'user&order[volume]=asc&order[chapter]=asc&offset={offset}&contentRating[]=' \
					f'safe&contentRating[]=suggestive&contentRating[]=erotica&contentRating[]=pornographic'
				json_code = self._web_bot.get_web_content(
					url=api_url, code_page=self._code_page,cookie=self._cookies, ref=self._home_url
				)
				json_obj = json.loads(json_code)

				tmp_chapter_list += json_obj['data']
				if json_obj['total'] < json_obj['offset'] + limit:
					break
				offset = json_obj['offset']
			if len(tmp_chapter_list) > 0:
				results = {}
				chapters = self.parse_chapter_list(tmp_chapter_list,"chapter")
				books = self.parse_chapter_list(tmp_chapter_list,"volume")
				if len(chapters) > 0:
					results["chapter"] = chapters
				if len(books) > 0:
					results["book"] = books
				#print(result)
				return results
		return {}

	def get_image_list_from_html(self,html_code,url):
		json_obj = json.loads(html_code)
		images_list = []
		image_url_prefix = json_obj["baseUrl"] + "/data/" + json_obj["chapter"]["hash"] + "/"
		for tmp_img in json_obj["chapter"]["data"]:
			images_list.append({"url":image_url_prefix + tmp_img,"ref":self._home_url})
		return {"images":images_list}

	def parse_chapter_list(self,chapter_list,target_type="chapter"):
		results = []
		for tmp_chapter in chapter_list:
			if tmp_chapter["type"] == target_type and tmp_chapter["attributes"]["pages"] > 0:
				tmp_chapter_dic = {
					"title": self._format_chapter_title(tmp_chapter["attributes"]),
					"url": f"{self._api_url}/at-home/server/{tmp_chapter['id']}?forcePort443=false",
					"ref": self._home_url, "lang": tmp_chapter["attributes"]["translatedLanguage"],
					"index": self._format_chapter_index(tmp_chapter["attributes"])
				}
				results.append(tmp_chapter_dic)
		return results

	@staticmethod
	def _format_chapter_title(attributes):
		chapter_title = ""
		if "title" in attributes and attributes["title"] is not None:
			chapter_title += attributes["title"]
		chapter_title += " ("
		chapter_title += attributes["translatedLanguage"]
		chapter_title += ")"
		return chapter_title

	@staticmethod
	def _format_chapter_index(attributes):
		#print(attributes)
		chapter_title = attributes["translatedLanguage"].upper()
		chapter_title += "_Vol"
		if "volume" in attributes and attributes["volume"] is not None:
			chapter_title += attributes["volume"]
		else:
			chapter_title += "No"
		chapter_title += "Ch"
		chapter_title += attributes["chapter"]
		return chapter_title
