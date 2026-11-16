import html
import re
from urllib.parse import unquote, urljoin, urlsplit

import bs4

from models.const import TRSM
from models.site import Site


class ReadComicsOnline(Site):
    URL_MATCH = ["readcomicsonline.ru"]

    def __init__(self, web_bot):
        super().__init__(web_bot)
        self._home_url = "https://readcomicsonline.ru"
        self._site_name = "Read Comics Online"
        self._sample_url = ["https://readcomicsonline.ru/comic/avengers-2018"]

    def get_book_id_from_url(self, url):
        parsed = urlsplit(url)
        match = re.match(r"^/comic/([^/]+)", parsed.path)
        if parsed.hostname in ("readcomicsonline.ru", "www.readcomicsonline.ru") and match:
            self._book_id = match.group(1)
            return self._book_id
        return ""

    def get_main_url_from_book_id(self):
        return f"{self._home_url}/comic/{self._book_id}"

    def parse_list(self):
        results = super().parse_list() or {}
        if not results.get("chapter"):
            results.setdefault("title", "")
            results.setdefault("author", "")
            results["message"] = TRSM(
                "Read Comics Online: No chapter links were found. Complete website verification and make sure the comic page is visible before continuing."
            )
        return results

    def get_book_title_from_html(self, html_code):
        bs = bs4.BeautifulSoup(html_code, "html.parser")
        title = bs.select_one("main h1") or bs.select_one("h1") or bs.select_one("h2.listmanga-header")
        return title.get_text(" ", strip=True) if title else "unknown"

    def get_book_author_from_html(self, html_code):
        bs = bs4.BeautifulSoup(html_code, "html.parser")
        tmp_author = bs.select('a[href*="/comic-list/author/"]')
        if tmp_author and len(tmp_author) > 0:
            author = html.unescape(tmp_author[0].text.strip())
        else:
            author = "unknown"
        return author

    def get_book_item_list_from_html(self, html_code, url):
        bs = bs4.BeautifulSoup(html_code, "html.parser")
        # The current layout uses ordinary links inside a Chapters section.
        chapters = bs.select("main section a[href], h5.chapter-title-rtl a[href], .chapter-title a[href]")
        if not chapters:
            chapters = bs.select("a[href]")
        results = {"chapter": []}
        seen = set()
        book_id = unquote(self._book_id or self.get_book_id_from_url(url))
        # Both current and legacy lists are newest first; keep the site's issue
        # identifiers (including decimals and specials) in their original URLs.
        for chapter in reversed(chapters):
            tmp_url = urljoin(url, chapter["href"].strip())
            parsed = urlsplit(tmp_url)
            parts = unquote(parsed.path).strip("/").split("/")
            if (
                parsed.scheme not in ("http", "https")
                or parsed.hostname not in ("readcomicsonline.ru", "www.readcomicsonline.ru")
                or len(parts) != 3
                or parts[:2] != ["comic", book_id]
            ):
                continue
            key = tuple(parts)
            if key in seen:
                continue
            seen.add(key)
            # The second span is a release date, not part of the chapter title.
            label = chapter.select_one("span.font-medium") or chapter.find("span", recursive=False) or chapter
            results["chapter"].append(
                {
                    "title": label.get_text(" ", strip=True),
                    "url": parsed._replace(fragment="").geturl(),
                    "index": str(len(results["chapter"]) + 1),
                    "ref": url,
                }
            )
        return results

    def get_image_list_from_html(self, html_code, url):
        if not html_code:
            raise ValueError(TRSM("Read Comics Online: The chapter page could not be loaded."))
        bs = bs4.BeautifulSoup(html_code, features="html.parser")
        # All pages are present in the HTML even when the reader shows only one.
        # Do not also include #reader-img, which duplicates the current page.
        image_lists = bs.select("#reader-all img") or bs.select("div#all img")
        image_urls = []
        seen = set()
        for image in image_lists:
            link = self._image_url(image, url)
            if link and link not in seen:
                seen.add(link)
                image_urls.append({"url": link, "ref": url})

        # Fall back to the published page dropdown if the all-pages strip is
        # unavailable or incomplete, instead of silently downloading one page.
        pages = []
        seen_pages = set()
        chapter_path = "/" + "/".join(urlsplit(url).path.strip("/").split("/")[:3])
        for option in bs.select("#page-list option[value]"):
            page_url = urljoin(url, option["value"].strip())
            parsed = urlsplit(page_url)
            prefix = chapter_path + "/"
            if (
                parsed.hostname in ("readcomicsonline.ru", "www.readcomicsonline.ru")
                and parsed.scheme in ("http", "https")
                and parsed.path.startswith(prefix)
                and parsed.path[len(prefix) :].strip("/").isdigit()
                and page_url not in seen_pages
            ):
                seen_pages.add(page_url)
                pages.append({"url": page_url, "ref": url})
        if image_urls and len(image_urls) >= len(pages):
            return {"images": image_urls}
        if pages:
            return {"pages": pages}
        link = self.get_single_page_image_from_html(html_code, url)
        if link:
            return {"images": [{"url": link, "ref": url}]}
        raise ValueError(TRSM("Read Comics Online: No comic images were found on the chapter page."))

    def get_single_page_image_from_html(self, html_code, url):
        if not html_code:
            return ""
        bs = bs4.BeautifulSoup(html_code, "html.parser")
        image = bs.select_one("#reader-img")
        return self._image_url(image, url) if image else ""

    @staticmethod
    def _image_url(image, url):
        for attribute in ("data-src", "data-original", "src"):
            source = image.get(attribute, "").strip()
            if source:
                link = urljoin(url, source)
                if urlsplit(link).scheme in ("http", "https"):
                    return link
        return ""
