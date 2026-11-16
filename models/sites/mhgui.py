import html
import json
import re
from urllib.parse import urljoin, urlsplit

import lzstring
from bs4 import BeautifulSoup

from models.site import Site


class MHGui(Site):
    URL_MATCH = ["manhuagui.com", "mhgui.com"]

    def __init__(self, web_bot):
        super().__init__(web_bot)
        self._home_url = "https://www.mhgui.com"
        self._site_name = "漫画柜/看漫画"
        self._default_image_format = "webp"
        self._sample_url = ["https://www.mhgui.com/comic/19430/", "https://www.manhuagui.com/comic/28004/"]
        self._image_url_prefix = "https://i.hamreus.com"

    def get_book_id_from_url(self, url):
        pattern_book_id = re.compile(r"//(.*?)gui.com/comic/([^/]*)(/?)")

        plists = re.findall(pattern_book_id, url)
        if len(plists) > 0 and len(plists[0]) > 1:
            self._book_id = plists[0][1]
            return self._book_id
        return ""

    def get_book_title_from_html(self, html_code):
        pattern_title = re.compile(r'<div class="book-title"><h1>(.*?)</h1>')
        info_title = re.findall(pattern_title, html_code)
        if len(info_title) > 0 and info_title[0] != "":
            title = html.unescape(info_title[0].strip())
        else:
            title = "unknown"
        return title

    def get_book_author_from_html(self, html_code):
        pattern_author = re.compile(r'<span><strong>漫画作者：</strong><a href="(.*?)" title="(.*?)">(.*?)</a></span>')
        info_author = re.findall(pattern_author, html_code)
        if len(info_author) > 0 and info_author[0][2] != "":
            tmp_author = self.remove_html(info_author[0][2])
            author = html.unescape(tmp_author.strip())
        else:
            author = "unknown"
        return author

    def get_book_item_list_from_html(self, html_code, url):
        page = BeautifulSoup(html_code, "html.parser")
        sections = list(page.select(".chapter-list"))
        state = page.select_one("input#__VIEWSTATE")
        if state is not None and state.get("value"):
            # The site's button only expands chapter metadata already embedded
            # in the response. Decode the same LZString payload without running JS.
            try:
                payload = "".join(state["value"].split())
                chapter_html = lzstring.LZString.decompressFromBase64(payload)
                if not chapter_html:
                    raise ValueError("Empty chapter data")
                chapter_page = BeautifulSoup(chapter_html, "html.parser")
                sections.extend(chapter_page.select(".chapter-list"))
            except (IndexError, KeyError, TypeError, ValueError) as error:
                if not sections:
                    raise ValueError("Manhuagui: The embedded chapter list could not be decoded.") from error

        results = {}
        seen = set()
        for section in sections:
            heading = section.find_previous("h4")
            label = heading.get_text(" ", strip=True) if heading else ""
            if any(name in label for name in ("单行本", "單行本", "全彩版")):
                kind = "book"
            elif any(name in label for name in ("番外", "外传", "外傳")):
                kind = "extra"
            else:
                kind = "chapter"
            for item in self._parse_list_from_content(section, url):
                if item["url"] in seen:
                    continue
                seen.add(item["url"])
                items = results.setdefault(kind, [])
                item["index"] = str(len(items) + 1)
                items.append(item)
        return results

    def get_image_list_from_html(self, html_code, url):
        data = self._get_image_data_from_page(html_code=html_code)
        image_urls = []
        for i in data["files"]:
            image_url = self._image_url_prefix + data["path"] + i + "?e=%(e)s&m=%(m)s" % (data["sl"])
            image_urls.append({"url": image_url, "ref": url})
        return {"images": image_urls}

    # internal function
    @staticmethod
    def _parse_list_from_content(info, url):
        content = BeautifulSoup(info, "html.parser") if isinstance(info, str) else info
        pages = content.find_all("ul") or [content]
        book_path = re.match(r"/comic/\d+/", urlsplit(url).path)
        results = []
        for page in pages:
            # Each list is newest first, as in the existing Manhuagui layout.
            for link in reversed(page.select("li > a[href]")):
                chapter_url = urljoin(url, link["href"])
                path = urlsplit(chapter_url).path
                if not re.fullmatch(r"/comic/\d+/\d+\.html", path):
                    continue
                if book_path and not path.startswith(book_path.group()):
                    continue
                title = link.get("title", "").strip()
                if not title:
                    for page_count in link.select("i"):
                        page_count.decompose()
                    title = link.get_text(" ", strip=True)
                results.append(
                    {"title": " ".join(title.split()), "url": chapter_url, "index": str(len(results) + 1), "ref": url}
                )
        return results

    @staticmethod
    def _get_image_data_from_page(html_code):
        # JScript Version

        # ref https://github.com/HSSLC/manhuagui-dlr/blob/c5279901b68d5627d202142d6785ac26f2689516/get.py#L10
        if html_code != "":
            m = re.match(r"^.*\}\(\'(.*)\',(\d*),(\d*),\'([\w|\+|\/|=]*)\'.*$", html_code)
            result = MHGui.packed(
                m.group(1),
                int(m.group(2)),
                int(m.group(3)),
                lzstring.LZString.decompressFromBase64(m.group(4)).split("|"),
            )
            return result
        return {}

    @staticmethod
    def packed(functionFrame, a, c, data):
        def e(innerC):
            return ("" if innerC < a else e(int(innerC / a))) + (
                chr(innerC % a + 29) if innerC % a > 35 else MHGui.atr(innerC % a, 36)
            )

        c -= 1
        d = {}
        while c + 1:
            d[e(c)] = e(c) if data[c] == "" else data[c]
            c -= 1
        pieces = re.split(r"(\b\w+\b)", functionFrame)
        js = "".join([d[x] if x in d else x for x in pieces]).replace("\\'", "'")
        return json.loads(re.search(r"^.*\((\{.*\})\).*$", js).group(1))

    @staticmethod
    def itr(value, num):
        d = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "" if value <= 0 else MHGui.itr(int(value / num), num) + d[value % num]

    @staticmethod
    def atr(value, num):
        tmp = MHGui.itr(value, num)
        return "0" if tmp == "" else tmp
