import asyncio
import math
import time
from datetime import timezone
from email.utils import parsedate_to_datetime

import httpx
from googletrans import Translator

from models.controllers.translator.Translator import TranslationError, TranslatorEngine


class GoogleTranslatorEngine(TranslatorEngine):
    DESCRIPTION = "Google Translate: unofficial web client; requests may be rate limited."
    _next_request_time = 0.0
    _rate_limit_until = 0.0
    _RATE_LIMIT_MESSAGE = "Google is limiting translation requests (HTTP 429). Try again in at least %d seconds."

    def __init__(self):
        super(GoogleTranslatorEngine, self).__init__()

    def translate_text(self, text, to_lang, from_lang="auto"):
        return asyncio.run(self._translate([text], to_lang, from_lang))[0]

    def translate_multi_text(self, text_list, to_lang, from_lang="auto"):
        if not text_list:
            return []
        return asyncio.run(self._translate(text_list, to_lang, from_lang))

    async def _translate(self, text_list, to_lang, from_lang):
        self._check_rate_limit()
        try:
            # googletrans otherwise returns the original text as dummy data on
            # non-200 responses. Always expose failures instead of accepting it.
            async with Translator(
                service_urls=["translate.googleapis.com"],
                raise_exception=True,
                timeout=httpx.Timeout(30.0),
                list_operation_max_concurrency=1,
            ) as translator:
                # Preserve HTTP status and Retry-After before googletrans wraps errors.
                translator.client.event_hooks["response"].append(self._check_response)
                results = []
                for text in text_list:
                    if not text.strip():
                        results.append(text)
                        continue
                    self._check_rate_limit()
                    pause = type(self)._next_request_time - time.monotonic()
                    if pause > 0:
                        await asyncio.sleep(pause)
                    type(self)._next_request_time = time.monotonic() + 1.0
                    translation = await translator.translate(text, dest=to_lang, src=from_lang or "auto")
                    if not isinstance(translation.text, str) or not translation.text.strip():
                        raise TranslationError("Google returned no translated text.")
                    results.append(translation.text)
                return results
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                wait = self._retry_after(exc.response.headers.get("Retry-After"))
                type(self)._rate_limit_until = time.monotonic() + wait
                raise TranslationError(self._RATE_LIMIT_MESSAGE, wait) from None
            raise TranslationError("Google Translate returned HTTP %d.", exc.response.status_code) from None
        except httpx.TimeoutException:
            raise TranslationError("Google Translate timed out. Please try again later.") from None
        except httpx.RequestError:
            raise TranslationError("Could not connect to Google Translate. Check your network connection.") from None

    @staticmethod
    async def _check_response(response):
        response.raise_for_status()

    @classmethod
    def _check_rate_limit(cls):
        remaining = math.ceil(cls._rate_limit_until - time.monotonic())
        if remaining > 0:
            raise TranslationError(cls._RATE_LIMIT_MESSAGE, remaining)

    @staticmethod
    def _retry_after(value):
        # Respect Google's delay; otherwise pause this client for one minute.
        if not value:
            return 60
        try:
            delay = float(value)
        except ValueError:
            try:
                deadline = parsedate_to_datetime(value)
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                delay = deadline.timestamp() - time.time()
            except (TypeError, ValueError, OverflowError):
                return 60
        return max(1, math.ceil(delay)) if math.isfinite(delay) else 60
