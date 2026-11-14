import html
import time

import requests

from models.controllers.translator.Translator import TranslatorEngine, TranslationError


class MyMemoryTranslatorEngine(TranslatorEngine):
	DESCRIPTION = "MyMemory: no API key; free anonymous usage is limited to 5,000 characters per day. Text is sent to MyMemory for translation."
	API_URL = "https://api.mymemory.translated.net/get"
	_next_request_time = 0.0

	def translate_text(self, text, to_lang, from_lang="auto"):
		return self.translate_multi_text([text], to_lang, from_lang)[0]

	def translate_multi_text(self, text_list, to_lang, from_lang="auto"):
		if not text_list:
			return []
		source = self._language_code(from_lang)
		target = self._language_code(to_lang)
		if not source or not target or source == "auto" or target == "auto":
			raise TranslationError("MyMemory requires explicit source and target languages.")
		if source == target:
			return list(text_list)
		with requests.Session() as session:
			session.headers.update({"User-Agent": "Comic-Toolbox", "Accept": "application/json"})
			results = []
			for text in text_list:
				if not text.strip():
					results.append(text)
					continue
				parts = [self._translate_segment(session, segment, source, target) for segment in self._segments(text)]
				results.append("\n".join(parts))
			return results

	@staticmethod
	def _language_code(code):
		code = (code or "").strip().lower().replace("_", "-")
		return {"zh-tw": "zh-TW", "zh-hant": "zh-TW", "zh-cn": "zh-CN", "zh-hans": "zh-CN"}.get(code, code)

	@staticmethod
	def _segments(text):
		# MyMemory accepts at most 500 UTF-8 bytes per request. Prefer word or
		# sentence boundaries, and never split a multibyte character.
		start = 0
		while start < len(text):
			end = start
			byte_count = 0
			boundary = start
			while end < len(text):
				length = len(text[end].encode("utf-8"))
				if byte_count + length > 500:
					break
				byte_count += length
				if text[end].isspace() or text[end] in ".!?。！？":
					boundary = end + 1
				end += 1
			if end < len(text) and boundary > start:
				end = boundary
			segment = text[start:end]
			if segment.strip():
				yield segment
			start = end

	def _translate_segment(self, session, text, source, target):
		pause = type(self)._next_request_time - time.monotonic()
		if pause > 0:
			time.sleep(pause)
		type(self)._next_request_time = time.monotonic() + 1.0
		try:
			response = session.get(self.API_URL, params={"q": text, "langpair": source + "|" + target, "mt": 1}, timeout=30)
			response.raise_for_status()
		except requests.Timeout:
			raise TranslationError("MyMemory timed out. Please try again later.") from None
		except requests.HTTPError as exc:
			if exc.response.status_code == 429:
				raise TranslationError("MyMemory is limiting translation requests. Please try again later.") from None
			raise TranslationError("MyMemory returned HTTP %d.", exc.response.status_code) from None
		except requests.RequestException:
			raise TranslationError("Could not connect to MyMemory. Check your network connection.") from None
		try:
			payload = response.json()
		except ValueError:
			raise TranslationError("MyMemory returned an invalid translation response.") from None
		if not isinstance(payload, dict):
			raise TranslationError("MyMemory returned an invalid translation response.")
		if payload.get("quotaFinished"):
			raise TranslationError("MyMemory's free translation quota has been reached. Please try again later.")
		status = str(payload.get("responseStatus", ""))
		if status == "429":
			raise TranslationError("MyMemory is limiting translation requests. Please try again later.")
		if status != "200":
			raise TranslationError("MyMemory rejected the translation request: %s", str(payload.get("responseDetails") or status))
		data = payload.get("responseData")
		translated = data.get("translatedText") if isinstance(data, dict) else None
		if not isinstance(translated, str) or not translated.strip():
			raise TranslationError("MyMemory returned an invalid translation response.")
		return html.unescape(translated)
