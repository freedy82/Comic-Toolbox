import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

import bs4

from models.const import TRSM
from models.site import Site


class WNACG(Site):
    URL_MATCH = ["wnacg.com", "wnacg.org", "wnacg.ru"]
    ALBUM_PATH = re.compile(r"/photos-(?:index(?:-page-\d+)?|slide|slist|list|gallery)-aid-(\d+)\.html$")

    def __init__(self, web_bot):
        super().__init__(web_bot)
        self._home_url = "https://www.wnacg.com"
        self._site_name = "WNACG"
        self._sample_url = ["https://www.wnacg.com/photos-index-aid-404263.html"]
        self._page_count = 0

    @classmethod
    def is_url_from_this_site(cls, url):
        parsed = urlsplit(url)
        return parsed.scheme in ("http", "https") and (parsed.hostname or "").removeprefix("www.") in cls.URL_MATCH

    def get_book_id_from_url(self, url):
        if self.is_url_from_this_site(url):
            parsed = urlsplit(url)
            match = self.ALBUM_PATH.fullmatch(parsed.path)
            if match:
                self._home_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
                self._book_id = match.group(1)
                return self._book_id
        return ""

    def get_main_url_from_book_id(self):
        return urljoin(self._home_url, "/photos-index-aid-%s.html" % self._book_id)

    def parse_list(self):
        self._page_count = 0
        result = super().parse_list() or {}
        if not result.get("book"):
            result.setdefault("title", "")
            result.setdefault("author", "")
            result["message"] = TRSM(
                "WNACG: The album could not be loaded. Open an album URL and complete website verification if requested."
            )
        return result

    def get_book_title_from_html(self, html_code):
        soup = bs4.BeautifulSoup(html_code, "html.parser")
        heading = soup.select_one("#bodywrap h2, #bodywrap h1")
        if heading:
            return heading.get_text(" ", strip=True)
        meta = soup.select_one('meta[property="og:title"]')
        return meta.get("content", "unknown").strip() if meta else "unknown"

    def get_book_author_from_html(self, html_code):
        soup = bs4.BeautifulSoup(html_code, "html.parser")
        author = soup.select_one('meta[name="author"]')
        if author and author.get("content", "").strip():
            return author["content"].strip()
        # Albums commonly put the creator/circle in the leading title brackets.
        match = re.match(r"^[\[\u3010]([^\]\u3011]+)[\]\u3011]", self.get_book_title_from_html(html_code))
        return match.group(1).strip() if match else "unknown"

    def get_book_item_list_from_html(self, html_code, url):
        soup = bs4.BeautifulSoup(html_code, "html.parser")
        if not soup.select_one('#reader-btn, a[href*="photos-view-id-"], a[href*="photos-slide-aid-"]'):
            return {}
        self._page_count = self._album_page_count(soup)
        return {
            "book": [
                {
                    "title": self.get_book_title_from_html(html_code),
                    "url": url,
                    "ref": self._home_url + "/",
                    "index": "1",
                    "is_single": True,
                }
            ]
        }

    @staticmethod
    def _album_page_count(soup):
        for label in soup.select(".uwconn label"):
            match = re.search(r"(?:\u9801\u6578|\u9875\u6570)\s*[:\uff1a]\s*(\d+)", label.get_text(" ", strip=True))
            if match:
                return int(match.group(1))
        return 0

    def _get_page(self, url, ref):
        return self._web_bot.get_web_content(
            url=url,
            ref=ref,
            cookie=self._cookies,
            code_page=self._code_page,
            cancel_check=lambda: self._stop_flag,
        )

    @staticmethod
    def _reader_data(source):
        """Read the site's JSON argument without executing downloaded JavaScript."""
        match = re.search(r"\b(?:mReader\.)?initData\s*\(\s*", source or "")
        if not match:
            return None
        text = source[match.end() :]
        try:
            return json.JSONDecoder().raw_decode(text)[0]
        except ValueError:
            # Some versions emit trailing commas. Strip only outside strings.
            cleaned = []
            quoted = escaped = False
            for index, char in enumerate(text):
                if not quoted and char == "," and text[index + 1 :].lstrip().startswith(("]", "}")):
                    continue
                cleaned.append(char)
                if quoted:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        quoted = False
                elif char == '"':
                    quoted = True
            try:
                return json.JSONDecoder().raw_decode("".join(cleaned))[0]
            except ValueError:
                return None

    @staticmethod
    def _image_url(value, base):
        if not isinstance(value, str) or not value.strip():
            return ""
        parsed = urlsplit(urljoin(base, value.strip()))
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return ""
        # Match the current reader and retain the complete signed query string.
        return urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, ""))

    def get_image_list_from_html(self, html_code, url):
        if not html_code:
            raise ValueError(TRSM("WNACG: The album page could not be loaded."))
        soup = bs4.BeautifulSoup(html_code, "html.parser")
        expected = self._album_page_count(soup) or self._page_count
        album_id = self._book_id or self.get_book_id_from_url(url)
        reader_url = urljoin(url, "/photos-slide-aid-%s.html" % album_id)
        reader_html = html_code
        if "/photos-index-" in urlsplit(url).path:
            link = soup.select_one('#reader-btn[href], a[href*="photos-slide-aid-"]')
            if link:
                candidate = urljoin(url, link["href"])
                if self.is_url_from_this_site(candidate):
                    reader_url = candidate
            reader_html = self._get_page(reader_url, url)
        else:
            reader_url = url

        reader = bs4.BeautifulSoup(reader_html or "", "html.parser")
        data = self._reader_data(reader_html)
        if not isinstance(data, dict) or "page_url" not in data:
            item_url = urljoin(reader_url, "/photos-item-aid-%s.html" % album_id)
            for script in reader.select("script[src]"):
                candidate = urljoin(reader_url, script["src"])
                if (
                    self.is_url_from_this_site(candidate)
                    and urlsplit(candidate).path == "/photos-item-aid-%s.html" % album_id
                ):
                    item_url = candidate
                    break
            data = self._reader_data(self._get_page(item_url, reader_url))
        if isinstance(data, dict) and isinstance(data.get("page_url"), list):
            # These are complete original pages, not thumbnails, display-width
            # variants or CSS fragments. Keep their published reader order.
            policy = reader.select_one('meta[name="referrer"]')
            ref = reader_url
            if policy and policy.get("content", "").lower() in ("no-referrer", "same-origin"):
                ref = ""
            elif policy and policy.get("content", "").lower() in (
                "origin",
                "strict-origin",
                "origin-when-cross-origin",
                "strict-origin-when-cross-origin",
            ):
                parsed = urlsplit(reader_url)
                ref = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
            images = []
            for value in data["page_url"]:
                image_url = self._image_url(value, reader_url)
                if image_url:
                    images.append({"url": image_url, "ref": ref})
            if images and len(images) == len(data["page_url"]) and (not expected or len(images) == expected):
                return {"images": images}
            raise ValueError(TRSM("WNACG: The image list is incomplete. Reload the album and try again."))

        # Older albums expose individual full-image pages in paginated indexes.
        pages = self._index_image_pages(html_code, url, album_id)
        if pages and (not expected or len(pages) == expected):
            return {"pages": pages}
        raise ValueError(TRSM("WNACG: No complete image list was found. Complete website verification and try again."))

    def _index_image_pages(self, html_code, url, album_id):
        soup = bs4.BeautifulSoup(html_code, "html.parser")
        page_numbers = {1}
        pattern = re.compile(r"/photos-index-page-(\d+)-aid-%s\.html$" % re.escape(album_id))
        for link in soup.select("a[href]"):
            match = pattern.fullmatch(urlsplit(urljoin(url, link["href"])).path)
            if match:
                page_numbers.add(int(match.group(1)))
        pages, seen = [], set()
        for number in range(1, max(page_numbers) + 1):
            if self._stop_flag:
                break
            index_url = urljoin(url, "/photos-index-page-%d-aid-%s.html" % (number, album_id))
            if number != 1:
                self.page_trigger.emit(str(number))
                content = self._get_page(index_url, url)
                if not content:
                    break
                soup = bs4.BeautifulSoup(content, "html.parser")
            for link in soup.select('.pic_box a[href*="photos-view-id-"]'):
                page_url = urljoin(index_url, link["href"])
                if (
                    self.is_url_from_this_site(page_url)
                    and re.fullmatch(r"/photos-view-id-\d+\.html", urlsplit(page_url).path)
                    and page_url not in seen
                ):
                    seen.add(page_url)
                    pages.append({"url": page_url, "ref": index_url})
        return pages

    def get_single_page_image_from_html(self, html_code, url):
        soup = bs4.BeautifulSoup(html_code or "", "html.parser")
        image = soup.select_one("img#picarea, #photo_body img, img#photo_body")
        if image:
            for attribute in ("data-original", "data-src", "src"):
                image_url = self._image_url(image.get(attribute), url)
                if image_url:
                    return image_url
        raise ValueError(TRSM("WNACG: The original page image could not be found."))
