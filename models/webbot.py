import json
import re
import ssl
import string
import threading
import urllib.request as url_request
from http.cookiejar import Cookie, DefaultCookiePolicy
from http.cookies import SimpleCookie
from urllib.error import HTTPError
from urllib.parse import quote, urlparse


class BrowserVerificationError(RuntimeError):
    pass


def is_browser_challenge(headers, content):
    if headers.get("cf-mitigated", "").lower() == "challenge":
        return True
    text = content[:262144].decode("utf-8", "ignore").lower()
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.DOTALL)
    return bool(
        title
        and re.search(
            r"just a moment|attention required|verify.*human|human verification|browser verification|checking your browser|security (?:verification|check)|performing.*verification",
            title.group(1),
        )
        and any(marker in text for marker in ("cloudflare", "challenge-platform", "cf-chl-", "captcha"))
    )


class _BrowserChallenge(Exception):
    pass


class WebBot(object):
    def __init__(
        self,
        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
        time_out=30,
        max_retry=5,
        proxy_mode=0,
        proxy_list="",
    ):
        self._agent = agent
        self._time_out = time_out
        self._max_retry = max_retry
        self._accept_language = ""
        self._cookie_processor = url_request.HTTPCookieProcessor()
        self._cookie_processor.cookiejar.set_policy(
            DefaultCookiePolicy(strict_ns_domain=DefaultCookiePolicy.DomainStrictNonDomain)
        )
        self._verification_handler = None
        self._verification_translate = str
        self._verification_lock = threading.Lock()
        self._verified_clients = {}

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self._https_handler = url_request.HTTPSHandler(context=ctx)

        self._opener = url_request.build_opener(self._cookie_processor, self._https_handler)
        self._proxy_index = 0  # 0 = no proxy
        self._proxy_mode = proxy_mode
        if proxy_list != "":
            self._proxy_list = json.loads(proxy_list)
        else:
            self._proxy_list = []

    def set_agent(self, agent):
        self._agent = agent

    def set_time_out(self, time_out):
        self._time_out = time_out

    def set_max_retry(self, max_retry):
        self._max_retry = max_retry

    def set_proxy_mode(self, proxy_mode):
        self._proxy_mode = proxy_mode

    def set_proxy_list(self, proxy_list):
        if proxy_list != "":
            self._proxy_list = json.loads(proxy_list)
        else:
            self._proxy_list = []

    def set_accept_language(self, accept_language):
        self._accept_language = accept_language

    def set_verification_handler(self, handler, translate=str):
        self._verification_handler = handler
        self._verification_translate = translate

    def _verification_error(self, source):
        return BrowserVerificationError(self._verification_translate(source))

    def get_web_content(
        self,
        url,
        ref="",
        cookie=None,
        is_json=False,
        code_page="utf-8",
        headers=None,
        raise_errors=False,
        allow_browser_verification=True,
        cancel_check=None,
        data=None,
    ):
        accept = next((str(value).lower() for name, value in (headers or {}).items() if name.lower() == "accept"), "")
        tmp_response = self.get_web_content_raw(
            url=url,
            ref=ref,
            cookie=cookie,
            headers=headers,
            raise_errors=raise_errors,
            allow_browser_verification=allow_browser_verification,
            allow_browser_html=not is_json and "json" not in accept,
            browser_html_encoding=code_page,
            cancel_check=cancel_check,
            data=data,
        )
        if tmp_response:
            tmp_content = tmp_response.decode(code_page, "ignore")

            if is_json:
                tmp_parsed = json.loads(tmp_content)
                return tmp_parsed
            else:
                return tmp_content
        else:
            return None

    def get_web_content_raw(
        self,
        url,
        ref="",
        cookie=None,
        headers=None,
        raise_errors=False,
        allow_browser_verification=True,
        allow_browser_html=False,
        browser_html_encoding="utf-8",
        cancel_check=None,
        data=None,
    ):
        try_count = 0
        origin = self._origin(url)
        initial_clients = self._verified_clients.copy()
        generation = self._verified_clients.get(origin, {}).get("generation", 0)
        verification_result = None
        verification_attempted = False
        while try_count <= self._max_retry:
            if cancel_check is not None and cancel_check():
                raise self._verification_error("Download cancelled.")
            try:
                safe_url = quote(url, safe=string.printable)
                parsed_uri = urlparse(url)
                tmp_req = url_request.Request(safe_url, data=data)

                tmp_req.add_header("User-Agent", self._agent)
                if ref != "":
                    tmp_req.add_header("Referer", quote(ref, safe=string.printable))
                if self._accept_language != "":
                    tmp_req.add_header("Accept-Language", self._accept_language)
                for name, value in (headers or {}).items():
                    tmp_req.add_header(name, str(value))
                verified = self._verified_clients.get(origin, {})
                if verified.get("user_agent"):
                    tmp_req.add_header("User-Agent", verified["user_agent"])
                # Let CookieJar enforce domain/path/expiry, then merge site preferences.
                self._cookie_processor.cookiejar.add_cookie_header(tmp_req)
                if cookie:
                    merged = SimpleCookie()
                    merged.load(tmp_req.get_header("Cookie", ""))
                    for name, value in cookie.items():
                        merged[str(name)] = str(value)
                    tmp_req.remove_header("Cookie")
                    tmp_req.add_unredirected_header(
                        "Cookie", "; ".join(f"{name}={m.value}" for name, m in merged.items())
                    )

                opener = self._build_opener(scheme=parsed_uri.scheme)
                try:
                    with opener.open(tmp_req, timeout=self._time_out) as response:
                        tmp_response = response.read()
                        if is_browser_challenge(response.headers, tmp_response):
                            raise _BrowserChallenge(response.geturl())
                        if (
                            verification_attempted
                            and not allow_browser_html
                            and "text/html" in response.headers.get("Content-Type", "").lower()
                        ):
                            raise self._verification_error(
                                "The website returned a web page instead of the requested download."
                            )
                except HTTPError as exc:
                    if exc.code in (403, 429, 503) and is_browser_challenge(exc.headers, exc.read(262144)):
                        raise _BrowserChallenge(exc.url) from None
                    raise

                return tmp_response
            except _BrowserChallenge as challenge:
                # Verify the actual destination when the site redirected the request.
                url = challenge.args[0]
                challenge_origin = self._origin(url)
                if challenge_origin != origin:
                    origin = challenge_origin
                    generation = initial_clients.get(origin, {}).get("generation", 0)
                if not allow_browser_verification or self._verification_handler is None:
                    raise self._verification_error(
                        "This website requires human verification in the application's browser."
                    )
                if verification_attempted:
                    # Some sites bind clearance to the browser's TLS session. The exact
                    # page the user opened can still supply HTML, never image/JSON data.
                    if (
                        allow_browser_html
                        and verification_result
                        and self._same_page(url, verification_result.get("url", ""))
                        and verification_result.get("html")
                    ):
                        return verification_result["html"].encode(browser_html_encoding, "ignore")
                    raise self._verification_error(
                        "The website still rejects the download after browser verification. "
                        "Its clearance may be restricted to the embedded browser."
                    )
                verification_result = self._verify_in_browser(url, origin, generation, cancel_check)
                verification_attempted = True
            except BrowserVerificationError:
                raise
            except Exception:
                if raise_errors:
                    raise
                try_count += 1
        # raise ConnectionError
        return None

    @staticmethod
    def _origin(url):
        parsed = urlparse(url)
        return (parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port)

    @classmethod
    def _same_page(cls, requested, actual):
        left, right = urlparse(requested), urlparse(actual)
        return (
            cls._origin(requested) == cls._origin(actual)
            and left.path.rstrip("/") == right.path.rstrip("/")
            and left.query == right.query
        )

    def request_browser_session(self, url, instructions="", cancel_check=None):
        if self._verification_handler is None:
            raise self._verification_error("This website requires human verification in the application's browser.")
        origin = self._origin(url)
        generation = self._verified_clients.get(origin, {}).get("generation", 0)
        return self._verify_in_browser(url, origin, generation, cancel_check, instructions)

    def _verify_in_browser(self, url, origin, generation, cancel_check, instructions=""):
        # Serialize prompts and reuse a result if another image worker just verified.
        with self._verification_lock:
            if cancel_check is not None and cancel_check():
                raise self._verification_error("Download cancelled.")
            previous = self._verified_clients.get(origin, {})
            if previous.get("generation", 0) != generation:
                if previous.get("error"):
                    raise BrowserVerificationError(previous["error"])
                return previous
            try:
                if self._proxy_mode != 0:
                    raise self._verification_error(
                        "Browser verification needs the same network route as the downloader. "
                        "Turn off the app's proxy rotation and use a stable system connection or VPN."
                    )
                result = (
                    self._verification_handler(url, instructions=instructions)
                    if instructions
                    else self._verification_handler(url)
                )
                if not result:
                    raise self._verification_error("Website verification was cancelled.")
                for data in result.get("cookies", []):
                    domain = data["domain"]
                    host = origin[1]
                    if not (host == domain.lstrip(".") or (domain.startswith(".") and host.endswith(domain))):
                        continue
                    self._cookie_processor.cookiejar.set_cookie(
                        Cookie(
                            version=0,
                            name=data["name"],
                            value=data["value"],
                            port=None,
                            port_specified=False,
                            domain=domain,
                            domain_specified=domain.startswith("."),
                            domain_initial_dot=domain.startswith("."),
                            path=data["path"],
                            path_specified=True,
                            secure=data["secure"],
                            expires=data["expires"],
                            discard=data["expires"] is None,
                            comment=None,
                            comment_url=None,
                            rest={"HttpOnly": None} if data["http_only"] else {},
                            rfc2109=False,
                        )
                    )
                result["generation"] = generation + 1
                self._verified_clients[origin] = result
                return result
            except Exception as exc:
                self._verified_clients[origin] = {**previous, "generation": generation + 1, "error": str(exc)}
                raise BrowserVerificationError(str(exc)) from None

    # internal method
    def _get_current_proxy(self, scheme, mode):
        found_before = False
        if self._proxy_index == 0:
            found_before = True
        if len(self._proxy_list) > 0:
            for idx, proxy in enumerate(self._proxy_list):
                if idx + 1 == self._proxy_index:
                    found_before = True
                    continue
                if found_before:
                    if (proxy["url"].startswith(scheme + "://") or scheme == "http") and proxy["enable"]:
                        self._proxy_index = idx + 1
                        return proxy["url"]

            if found_before and mode == 2:
                # second loop
                for idx, proxy in enumerate(self._proxy_list):
                    if (proxy["url"].startswith(scheme + "://") or scheme == "http") and proxy["enable"]:
                        self._proxy_index = idx + 1
                        return proxy["url"]

        self._proxy_index = 0
        return ""

    def _build_opener(self, scheme):
        proxy = ""
        if self._proxy_mode == 1 or self._proxy_mode == 2:
            proxy = self._get_current_proxy(scheme, self._proxy_mode)

        if proxy != "":
            proxy_info = urlparse(proxy)
            proxy_handler = url_request.ProxyHandler(
                proxies={proxy_info.scheme: proxy_info.hostname + ":" + str(proxy_info.port)}
            )
            opener = url_request.build_opener(self._cookie_processor, self._https_handler, proxy_handler)
        else:
            opener = url_request.build_opener(self._cookie_processor, self._https_handler)
        return opener
