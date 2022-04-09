import urllib.request as url_request
import requests
import json
from urllib.parse import quote
import string

class WebBot(object):

	def __init__(self, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36', time_out=30, max_retry=5):
		self._agent = agent
		self._time_out = time_out
		self._max_retry = max_retry
		cookie_processor = url_request.HTTPCookieProcessor()
		self._opener = url_request.build_opener(cookie_processor)
		pass

	def get_web_content(self, url, ref='', cookie='', is_json=False, code_page="utf-8"):
		tmp_response = self.get_web_content_raw(url=url, ref=ref, cookie=cookie)
		if tmp_response:
			tmp_content = tmp_response.decode(code_page, 'ignore')

			if is_json:
				tmp_parsed = json.loads(tmp_content)
				return tmp_parsed
			else:
				return tmp_content
		else:
			return None

	def get_web_content_raw(self, url, ref='', cookie=''):
		try_count = 1
		while try_count <= self._max_retry:
			try:
				safe_url = quote(url, safe=string.printable)
				tmp_req = url_request.Request(safe_url)
				#tmp_req.set_proxy("", 'https')
				#https://www.httpbin.org/ip

				tmp_req.add_header('User-Agent',self._agent)
				if ref != '':
					tmp_req.add_header('Referer', ref)
				if cookie != '':
					tmp_req.add_header('Cookie', cookie)

				tmp_response = self._opener.open(tmp_req,timeout=self._time_out).read()
				return tmp_response
			except Exception:
				# print("Get data failed from",url)
				try_count += 1
		#print("Get data failed from",url)
		#raise ConnectionError
		return None

