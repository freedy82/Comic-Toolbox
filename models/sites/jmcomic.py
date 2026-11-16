import base64
import binascii
import hashlib
import io
import json
import os
import re
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

import bs4
from PIL import Image

from models.const import MY_CONFIG, TRSM
from models.site import Site
from models.webbot import BrowserVerificationError


class JMComic(Site):
    URL_MATCH = ["18comic.vip", "18comic.org"]

    def __init__(self, web_bot):
        super().__init__(web_bot)
        self._home_url = "https://18comic.vip"
        self._site_name = "18comic (JMComic)"
        self._sample_url = ["https://18comic.vip/album/1255565", "https://18comic.vip/album/1490368"]

    @classmethod
    def is_url_from_this_site(cls, url):
        parsed = urlsplit(url)
        return parsed.scheme in ("http", "https") and (parsed.hostname or "").removeprefix("www.") in cls.URL_MATCH

    def get_book_id_from_url(self, url):
        if self.is_url_from_this_site(url):
            parsed = urlsplit(url)
            match = re.match(r"^/album/(\d+)(?:/|$)", parsed.path)
            if match:
                self._home_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
                self._book_id = match.group(1)
                return self._book_id
        return ""

    def get_main_url_from_book_id(self):
        return urljoin(self._home_url, "/album/" + self._book_id)

    @staticmethod
    def _expanded_html(html_code):
        # Some templates insert HTML from a base64 literal. Decode the data;
        # never execute the website's JavaScript to extract album information.
        source = html_code or ""
        fragments = []
        for match in re.finditer(r"base64DecodeUtf8\s*\(\s*(['\"])([A-Za-z0-9+/=]+)\1\s*\)", source):
            try:
                fragment = base64.b64decode(match.group(2), validate=True).decode("utf-8")
            except (ValueError, binascii.Error, UnicodeDecodeError):
                continue
            if fragment not in source:
                fragments.append(fragment)
        return source + "\n" + "\n".join(fragments)

    @classmethod
    def _soup(cls, html_code):
        return bs4.BeautifulSoup(cls._expanded_html(html_code), "html.parser")

    @staticmethod
    def _clean_text(element):
        return " ".join(element.get_text(" ", strip=True).split())

    def parse_list(self):
        # Site/WebBot handles Cloudflare through the application's existing
        # human-verification broker and its in-memory cookie jar.
        result = super().parse_list() or {}
        if not (result.get("chapter") or result.get("book")):
            result.setdefault("title", "")
            result.setdefault("author", "")
            result["message"] = TRSM(
                "18comic: No album or chapter list was found. Use an album URL and complete website verification if requested."
            )
        return result

    def get_book_title_from_html(self, html_code):
        soup = self._soup(html_code)
        heading = soup.select_one("#book-name")
        if heading:
            return self._clean_text(heading)
        meta = soup.select_one('meta[property="og:title"]')
        return meta.get("content", "unknown").strip() if meta else "unknown"

    def get_book_author_from_html(self, html_code):
        soup = self._soup(html_code)
        authors = []
        # Other tag groups also use itemprop="author" on this site. Only the
        # explicitly marked author field contains the actual creator tags.
        for link in soup.select('[data-type="author"] a'):
            name = self._clean_text(link)
            if name and name not in authors:
                authors.append(name)
        return ", ".join(authors) or "unknown"

    def _photo_link(self, value, base):
        candidate = urljoin(base, value)
        if not self.is_url_from_this_site(candidate):
            return None
        parsed = urlsplit(candidate)
        match = re.match(r"^/photo/(\d+)(?:/|$)", parsed.path)
        if match:
            return match.group(1), urlunsplit((parsed.scheme, parsed.netloc, "/photo/" + match.group(1), "", ""))
        return None

    def get_book_item_list_from_html(self, html_code, url):
        soup = self._soup(html_code)
        chapters, seen = [], set()
        for link in soup.select(".episode a[data-album][href]"):
            photo = self._photo_link(link["href"], url)
            if photo is None or photo[0] in seen:
                continue
            seen.add(photo[0])
            index = link.get("data-index", "")
            order = int(index) if index.isdecimal() else len(chapters)
            heading = link.select_one("h3, .h2_series") or link
            chapters.append((order, {"title": self._clean_text(heading), "url": photo[1], "ref": url}))
        if chapters:
            chapters.sort(key=lambda entry: entry[0])
            items = []
            for index, (_, item) in enumerate(chapters, start=1):
                item["index"] = str(index)
                items.append(item)
            return {"chapter": items}
        # A single book has a reading link and no episode list. Restrict the
        # fallback to its album ID so recommendations never become chapters.
        album_id = self._book_id or self.get_book_id_from_url(url)
        for link in soup.select('a.reading[href], #album_photo_cover a[href], a[href*="/photo/"]'):
            photo = self._photo_link(link["href"], url)
            if photo and photo[0] == album_id and soup.select_one("#book-name"):
                return {
                    "book": [
                        {
                            "title": self.get_book_title_from_html(html_code),
                            "url": photo[1],
                            "index": "1",
                            "ref": url,
                            "is_single": True,
                        }
                    ]
                }
        return {}

    @staticmethod
    def _integer_variable(source, name):
        match = re.search(r"\b(?:var|let|const)\s+" + re.escape(name) + r"\s*=\s*(\d+)\s*;", source)
        return int(match.group(1)) if match else None

    @staticmethod
    def _image_url(value, base, photo_id):
        if not isinstance(value, str) or not value.strip():
            return ""
        parsed = urlsplit(urljoin(base, value.strip()))
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or not parsed.path.startswith("/media/photos/%s/" % photo_id)
        ):
            return ""
        return urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, ""))

    def get_image_list_from_html(self, html_code, url):
        if not html_code:
            raise ValueError(TRSM("18comic: The chapter page could not be loaded."))
        source = self._expanded_html(html_code)
        soup = bs4.BeautifulSoup(source, "html.parser")
        photo = self._photo_link(url, url)
        photo_id = self._integer_variable(source, "aid")
        scramble_id = self._integer_variable(source, "scramble_id")
        if not photo or photo_id != int(photo[0]) or scramble_id is None:
            raise ValueError(
                TRSM(
                    "18comic: Image-restoration information is missing. Complete website verification and reload the chapter."
                )
            )
        images_by_name, ordered_names = {}, []
        for tag in soup.select('img[id^="album_photo_"]'):
            image_url = self._image_url(tag.get("data-original") or tag.get("data-src"), url, photo_id)
            if not image_url:
                continue
            filename = unquote(urlsplit(image_url).path.rsplit("/", 1)[-1])
            if filename not in images_by_name:
                images_by_name[filename] = image_url
                ordered_names.append(filename)
        if not ordered_names:
            raise ValueError(TRSM("18comic: No original page images were found in this chapter."))
        page_array = re.search(r"\b(?:var|let|const)\s+page_arr\s*=\s*", source)
        if page_array:
            try:
                names, _ = json.JSONDecoder().raw_decode(source[page_array.end() :])
            except ValueError:
                raise ValueError(
                    TRSM("18comic: The chapter image list is incomplete. Reload the chapter and try again.")
                ) from None
            if not isinstance(names, list) or not names or any(not isinstance(name, str) or not name for name in names):
                raise ValueError(
                    TRSM("18comic: The chapter image list is incomplete. Reload the chapter and try again.")
                )
            ordered_names = names
        elif soup.select("#pageselect option") and len(ordered_names) != len(soup.select("#pageselect option")):
            raise ValueError(TRSM("18comic: The chapter image list is incomplete. Reload the chapter and try again."))
        first = urlsplit(next(iter(images_by_name.values())))
        directory = first.path.rsplit("/", 1)[0] + "/"
        images = []
        for filename in ordered_names:
            # JSON may include every page even in the site's paginated mode.
            image_url = images_by_name.get(filename)
            if not image_url:
                candidate = urlunsplit((first.scheme, first.netloc, directory + filename, first.query, ""))
                image_url = self._image_url(candidate, url, photo_id)
            if not image_url:
                raise ValueError(
                    TRSM("18comic: The chapter image list is incomplete. Reload the chapter and try again.")
                )
            images.append(
                {"url": image_url, "ref": url, "strip_count": self._strip_count(photo_id, scramble_id, filename)}
            )
        return {"images": images}

    @staticmethod
    def _strip_count(photo_id, scramble_id, filename):
        stem, extension = os.path.splitext(filename)
        if photo_id < scramble_id or extension.lower() == ".gif":
            return 0
        if photo_id < 268850:
            return 10
        modulus = 10 if photo_id < 421926 else 8
        digest = hashlib.md5((str(photo_id) + stem).encode("utf-8"), usedforsecurity=False).hexdigest()
        return 2 * (ord(digest[-1]) % modulus + 1)

    @staticmethod
    def _restore_image(image, strips):
        image = image.convert("RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB")
        if not strips:
            return image
        width, height = image.size
        restored = Image.new(image.mode, image.size)
        ordinary_height, extra_rows = divmod(height, strips)
        source_y, destination_y = 0, height
        # The source's last strip contains the remainder rows. Move complete
        # strips in reverse order, retaining every row even for uneven heights.
        for part in range(strips):
            part_height = ordinary_height + (extra_rows if part == strips - 1 else 0)
            destination_y -= part_height
            with image.crop((0, source_y, width, source_y + part_height)) as strip:
                restored.paste(strip, (0, destination_y))
            source_y += part_height
        image.close()
        return restored

    def download_image(self, image_url, target_file, page_ref, download_info=None):
        if self._stop_flag:
            return None
        temporary = None
        try:
            data = self._web_bot.get_web_content_raw(
                url=image_url,
                ref=page_ref,
                cookie=self._cookies,
                headers=download_info.get("headers") if download_info else None,
                cancel_check=lambda: self._stop_flag,
            )
            if self._stop_flag:
                return None
            if not data:
                raise ValueError(TRSM("The image request returned no data."))
            target = Path(target_file)
            with Image.open(io.BytesIO(data)) as original:
                original.load()
                strips = (download_info or {}).get("strip_count", 0)
                with NamedTemporaryFile(dir=target.parent, suffix=target.suffix, delete=False) as stream:
                    temporary = Path(stream.name)
                if not strips or getattr(original, "is_animated", False):
                    temporary.write_bytes(data)
                else:
                    with self._restore_image(original, strips) as restored:
                        if target.suffix.lower() in (".jpg", ".jpeg"):
                            with restored.convert("RGB") as rgb:
                                rgb.save(temporary, quality=95, subsampling=0)
                        elif target.suffix.lower() == ".webp":
                            restored.save(temporary, lossless=True)
                        else:
                            restored.save(temporary)
            if self._stop_flag:
                return None
            # Publish only complete, restored pages. Failed downloads never
            # leave a scrambled or partial file that a subsequent run skips.
            os.replace(temporary, target)
            temporary = None
            delay = float(MY_CONFIG.get("anti-ban", "image_sleep"))
            if delay > 0:
                time.sleep(delay)
            return target.as_posix()
        except BrowserVerificationError:
            self.stop()
            raise
        except Exception as error:
            self.stop()
            message = TRSM("18comic: Could not download or restore %s: %s") % (image_url, str(error))
            self.chapter_trigger.emit(message, self._current_finish_download, self._final_total_download)
            return None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
