from ..site import *

class Empty(Site):
	URL_MATCH = ["domain.com"]

	def __init__(self,web_bot):
		super().__init__(web_bot)
		self._home_url = "https://www.domain.com"
		self._site_name = "Site Name"
		self._sample_url = ["http://www.domain.com/comic/1234/"]

	def get_book_id_from_url(self,url):
		#todo parse id from url
		return ""

	# use only need
	def get_main_url_from_book_id(self):
		#todo reformat the main url from book id
		return self.get_main_url()

	def get_book_title_from_html(self,html_code):
		#todo parse book title from html
		return "unknown"

	def get_book_author_from_html(self,html_code):
		#todo parse book author from html
		return "unknown"

	def get_book_item_list_from_html(self, html_code, url):
		#todo parse book list from html
		#can have chapter,book,extra section
		return {}

	def download_item(self,item,title="",item_type=""):
		output_dir = super(Empty, self).download_item(item=item,title=title,item_type=item_type)
		info = self._web_bot.get_web_content(url=item["url"], ref=item["ref"], code_page=self._code_page)
		#todo parse page/image list
		# for image list use
		#   self.download_image_lists(image_urls=image_urls,item=item,item_type=item_type,title=title)
		# for page list use
		#   self.download_single_page_image_from_list(pages,output_dir)
		return output_dir

	# use only need
	def get_single_page_image_from_html(self, html_code):
		#todo use for page list
		return ""


