import json
import string
import ssl
import urllib.request as url_request
from urllib.parse import quote,urlparse

class WebBot(object):

	def __init__(self, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36', time_out=30, max_retry=5, proxy_mode=0, proxy_list=""):
		self._agent = agent
		self._time_out = time_out
		self._max_retry = max_retry
		#self._accept_language = "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
		self._accept_language = ""
		#self._accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
		#self._accept_encoding = "gzip, deflate, br"
		#self._cache_control = "max-age=0"
		self._cookie_processor = url_request.HTTPCookieProcessor()

		ctx = ssl.create_default_context()
		ctx.check_hostname = False
		ctx.verify_mode = ssl.CERT_NONE
		self._https_handler = url_request.HTTPSHandler(context=ctx)

		self._opener = url_request.build_opener(self._cookie_processor, self._https_handler)
		self._proxy_index = 0  # 0 = no proxy
		self._proxy_mode = proxy_mode
		#print(f"init webbot with {id(self)}",flush=True)
		if proxy_list != "":
			self._proxy_list = json.loads(proxy_list)
		else:
			self._proxy_list = []
		pass

	def set_agent(self,agent):
		self._agent = agent

	def set_time_out(self,time_out):
		self._time_out = time_out

	def set_max_retry(self,max_retry):
		self._max_retry = max_retry

	def set_proxy_mode(self,proxy_mode):
		self._proxy_mode = proxy_mode

	def set_proxy_list(self,proxy_list):
		if proxy_list != "":
			self._proxy_list = json.loads(proxy_list)
		else:
			self._proxy_list = []

	def set_accept_language(self,accept_language):
		self._accept_language = accept_language

	def get_web_content(self, url, ref='', cookie=None, is_json=False, code_page="utf-8"):
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

	def get_web_content_raw(self, url, ref='', cookie=None):
		try_count = 0
		while try_count <= self._max_retry:
			try:
				safe_url = quote(url, safe=string.printable)
				parsed_uri = urlparse(url)
				tmp_req = url_request.Request(safe_url)

				tmp_req.add_header('User-Agent',self._agent)
				if ref != '':
					tmp_req.add_header('Referer', quote(ref, safe=string.printable))
				if cookie is not None and cookie != {}:
					cookie_string = "; ".join([str(x) + "=" + str(y) for x, y in cookie.items()])
					tmp_req.add_header('Cookie', cookie_string)
				if self._accept_language != "":
					tmp_req.add_header("Accept-Language",self._accept_language)

				opener = self._build_opener(scheme=parsed_uri.scheme)
				tmp_response = opener.open(tmp_req,timeout=self._time_out).read()
				#tmp_response = url_request.urlopen(tmp_req, timeout=self._time_out).read()

				return tmp_response
			except Exception as ex:
				#template = "An exception of type {0} occurred. Arguments:\n{1!r}"
				#message = template.format(type(ex).__name__, ex.args)
				#print(message)
				try_count += 1
		#print("Get data failed from",url)
		#raise ConnectionError
		return None

	# internal method
	def _get_current_proxy(self,scheme,mode):
		found_before = False
		if self._proxy_index == 0:
			found_before = True
		if len(self._proxy_list) > 0:
			for idx,proxy in enumerate(self._proxy_list):
				if idx + 1 == self._proxy_index:
					found_before = True
					continue
				if found_before:
					if (proxy["url"].startswith(scheme+"://") or scheme == "http") and proxy["enable"]:
						self._proxy_index = idx + 1
						return proxy["url"]

			if found_before and mode == 2:
				# second loop
				for idx, proxy in enumerate(self._proxy_list):
					if (proxy["url"].startswith(scheme+"://") or scheme == "http") and proxy["enable"]:
						self._proxy_index = idx + 1
						return proxy["url"]

		self._proxy_index = 0
		return ""

	def _build_opener(self,scheme):
		#print(f"building opener with {scheme} and id:{id(self)}",flush=True)
		#print(f"proxy_mode:{self._proxy_mode}",flush=True)
		proxy = ""
		if self._proxy_mode == 1 or self._proxy_mode == 2:
			proxy = self._get_current_proxy(scheme,self._proxy_mode)

		if proxy != "":
			proxy_info = urlparse(proxy)
			#print(f"use proxy {proxy}",flush=True)
			proxy_handler = url_request.ProxyHandler(proxies={proxy_info.scheme: proxy_info.hostname + ":" + str(proxy_info.port)})
			opener = url_request.build_opener(self._cookie_processor, self._https_handler, proxy_handler)
		else:
			#print(f"not use proxy",flush=True)
			opener = url_request.build_opener(self._cookie_processor, self._https_handler)
		return opener
