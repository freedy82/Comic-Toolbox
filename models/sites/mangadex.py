import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from uuid import UUID

from models.const import APP_LINK, APP_VERSION
from models.site import Site


class MangaDex(Site):
    URL_MATCH = ["mangadex.org"]

    def __init__(self, web_bot):
        super().__init__(web_bot)
        self._home_url = "https://mangadex.org/"
        self._site_name = "MangaDex"
        self._sample_url = [
            "https://mangadex.org/title/c4b1cb49-46e9-405d-8b48-8104de22e659/cosmos",
            "https://mangadex.org/title/80422e14-b9ad-4fda-970f-de370d5fa4e5/made-in-abyss?page=1",
        ]
        self._api_url = "https://api.mangadex.org"
        identity = f"Comic-Toolbox/{APP_VERSION} (+{APP_LINK})"
        self._api_headers = {"User-Agent": identity, "Accept": "application/json"}
        self._image_headers = {"User-Agent": identity, "Accept": "image/*"}
        self._availability_message = ""

    def get_book_id_from_url(self, url):
        parsed = urlsplit(url.strip())
        if parsed.hostname not in ("mangadex.org", "www.mangadex.org", "api.mangadex.org"):
            return ""
        match = re.match(r"^/(?:title|manga)/([0-9a-fA-F-]{36})(?:/|$)", parsed.path)
        if match:
            try:
                self._book_id = str(UUID(match.group(1)))
                return self._book_id
            except ValueError:
                pass
        return ""

    def get_main_url_from_book_id(self):
        query = urlencode([("includes[]", "artist"), ("includes[]", "author")])
        return f"{self._api_url}/manga/{self._book_id}?{query}"

    def parse_list(self):
        result = {"title": "", "author": "", "chapter": []}
        self._availability_message = ""
        try:
            self._book_id = self.get_book_id_from_url(self._main_url)
            if not self._book_id:
                raise ValueError("Enter a MangaDex title URL containing a valid manga UUID.")
            self._web_bot.set_accept_language(self._accept_language)
            self._main_url = self.get_main_url_from_book_id()
            payload = self._api_json(self._main_url)
            self.book_title = self.get_book_title_from_html(payload)
            self.book_title = "".join(c for c in self.book_title if c.isalnum() or c == " ")
            self.book_author = self.get_book_author_from_html(payload)
            result.update(title=self.book_title, author=self.book_author)
            result.update(self.get_book_item_list_from_html(payload, self._main_url))
            if self._availability_message:
                result["message"] = self._availability_message
        except Exception as exc:
            result["message"] = self._error_message(exc)
        return result

    def _api_json(self, url):
        source = self._web_bot.get_web_content(
            url=url,
            ref=self._home_url,
            code_page=self._code_page,
            headers=self._api_headers,
            raise_errors=True,
        )
        return self._decode_json(source)

    @staticmethod
    def _decode_json(source):
        if not source:
            raise ValueError("The MangaDex API returned no data. Check network access.")
        if isinstance(source, dict):
            payload = source
        else:
            try:
                payload = json.loads(source)
            except (TypeError, ValueError):
                if isinstance(source, str) and "verification" in source.lower():
                    raise ValueError(
                        "MangaDex returned browser verification instead of API data. "
                        "Check site access and try again later."
                    ) from None
                raise ValueError("MangaDex returned a non-JSON response instead of API data.") from None
        if not isinstance(payload, dict):
            raise ValueError("MangaDex returned an unexpected API response.")
        if payload.get("result") == "error" or payload.get("errors"):
            details = "; ".join(
                str(error.get("detail") or error.get("title") or "API error")
                for error in payload.get("errors", [])
                if isinstance(error, dict)
            )
            raise ValueError(details or "MangaDex rejected the API request.")
        return payload

    @staticmethod
    def _error_message(exc):
        if isinstance(exc, HTTPError):
            if exc.code == 429:
                delay = exc.headers.get("Retry-After")
                return (
                    f"MangaDex API rate limit reached. Retry after {delay}."
                    if delay
                    else "MangaDex API rate limit reached. Wait before trying again."
                )
            if exc.code in (401, 403):
                return f"MangaDex denied API access (HTTP {exc.code}). Check site access and network/VPN settings."
            if exc.code == 404:
                return "This MangaDex title or chapter is no longer available (HTTP 404)."
            return f"MangaDex API request failed (HTTP {exc.code})."
        if isinstance(exc, URLError):
            return f"Could not connect to the MangaDex API: {exc.reason}"
        return f"MangaDex: {exc}"

    def get_book_title_from_html(self, html_code):
        payload = self._decode_json(html_code)
        titles = payload["data"]["attributes"].get("title") or {}
        return titles.get("en") or next((title for title in titles.values() if title), "unknown")

    def get_book_author_from_html(self, html_code):
        payload = self._decode_json(html_code)
        authors = []
        for relationship in payload["data"].get("relationships", []):
            if relationship.get("type") in ("author", "artist"):
                name = (relationship.get("attributes") or {}).get("name")
                if name and name not in authors:
                    authors.append(name)
        return ", ".join(authors) or "unknown"

    def get_book_item_list_from_html(self, html_code, url):
        limit, offset = 500, 0
        chapter_list = []
        external_hosts = set()
        external_count = 0
        while self._book_id:
            params = [
                ("limit", limit),
                ("offset", offset),
                ("includes[]", "scanlation_group"),
                ("order[volume]", "asc"),
                ("order[chapter]", "asc"),
                ("includeUnavailable", "0"),
            ]
            # Leave includeExternalUrl unset to fetch both kinds of entries.
            # The chapter parser excludes external publisher links locally.
            params.extend(("contentRating[]", rating) for rating in ("safe", "suggestive", "erotica", "pornographic"))
            feed_url = f"{self._api_url}/manga/{self._book_id}/feed?{urlencode(params)}"
            payload = self._api_json(feed_url)
            batch = payload.get("data")
            if not isinstance(batch, list):
                raise ValueError("The chapter feed did not return a chapter list.")
            chapter_list.extend(batch)
            for chapter in batch:
                external_url = (chapter.get("attributes") or {}).get("externalUrl")
                if external_url:
                    external_count += 1
                    host = urlsplit(external_url).hostname
                    if host:
                        external_hosts.add(host)
            returned_offset = int(payload.get("offset", offset))
            next_offset = returned_offset + int(payload.get("limit", limit))
            if not batch or next_offset >= int(payload.get("total", next_offset)):
                break
            if next_offset <= offset:
                raise ValueError("The chapter feed returned a repeated pagination offset.")
            offset = next_offset
            self.page_trigger.emit(f"MangaDex chapters: {len(chapter_list)}")
            time.sleep(0.25)
        chapters = self.parse_chapter_list(chapter_list)
        if not chapters:
            if external_count:
                publishers = ", ".join(sorted(external_hosts)) or "external publishers"
                self._availability_message = (
                    f"MangaDex lists {external_count} chapter(s) as external publisher links "
                    f"({publishers}). No downloadable chapter pages are hosted on MangaDex "
                    "for this title. Read these chapters on the publisher's website."
                )
            else:
                self._availability_message = "No downloadable chapters are currently available for this MangaDex title."
        return {"chapter": chapters}

    def get_image_list_from_html(self, html_code, url):
        try:
            payload = self._decode_json(html_code)
            chapter = payload.get("chapter") or {}
            base_url = payload.get("baseUrl")
            chapter_hash = chapter.get("hash")
            filenames = chapter.get("data")
            if not base_url or not chapter_hash or not isinstance(filenames, list) or not filenames:
                raise ValueError("No image data was returned for this chapter; it may no longer be hosted on MangaDex.")
            prefix = base_url.rstrip("/") + "/data/" + quote(chapter_hash, safe="") + "/"
            images = [
                {
                    "url": prefix + quote(filename, safe=""),
                    "ref": self._home_url,
                    "headers": self._image_headers,
                }
                for filename in filenames
            ]
            return {"images": images}
        except Exception as exc:
            self.chapter_trigger.emit(self._error_message(exc), 0, 0)
            return {"images": []}

    def parse_chapter_list(self, chapter_list, target_type="chapter"):
        results = []
        used_indexes = set()
        for chapter in chapter_list:
            attributes = chapter.get("attributes") or {}
            if (
                chapter.get("type") != target_type
                or not (attributes.get("pages") or 0)
                or attributes.get("externalUrl")
                or attributes.get("isUnavailable")
            ):
                continue
            index = self._format_chapter_index(attributes)
            if index in used_indexes:
                index += "_" + chapter["id"]
            used_indexes.add(index)
            results.append(
                {
                    "title": self._format_chapter_title(attributes),
                    "url": f"{self._api_url}/at-home/server/{chapter['id']}?forcePort443=true",
                    "ref": self._home_url,
                    "headers": self._api_headers,
                    "lang": attributes.get("translatedLanguage") or "und",
                    "index": index,
                }
            )
        return results

    @staticmethod
    def _format_chapter_title(attributes):
        title = attributes.get("title")
        if not title:
            number = attributes.get("chapter")
            title = f"Chapter {number}" if number is not None else "Oneshot"
        return f"{title} ({attributes.get('translatedLanguage') or 'und'})"

    @staticmethod
    def _format_chapter_index(attributes):
        language = (attributes.get("translatedLanguage") or "und").upper()
        volume = attributes.get("volume")
        chapter = attributes.get("chapter")
        return f"{language}_Vol{volume if volume is not None else 'No'}Ch{chapter if chapter is not None else 'No'}"
