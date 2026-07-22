import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx


MAX_RESPONSE_BYTES = 1_000_000
MAX_REDIRECTS = 3


class JobContentFetchError(ValueError):
    pass


class UnsafeJobUrlError(JobContentFetchError):
    pass


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._ignored_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in {"p", "div", "li", "br", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
        self.parts.append(data)

    def result(self) -> tuple[str | None, str]:
        title = " ".join(" ".join(self.title_parts).split()) or None
        lines = [" ".join(line.split()) for line in "".join(self.parts).splitlines()]
        return title, "\n".join(line for line in lines if line)


def extract_visible_text(content: str) -> tuple[str | None, str]:
    if "<" not in content or ">" not in content:
        return None, content.strip()
    parser = _VisibleTextParser()
    parser.feed(content)
    return parser.result()


def validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeJobUrlError("Only public HTTP(S) URLs are allowed")
    if parsed.username or parsed.password:
        raise UnsafeJobUrlError("URLs containing credentials are not allowed")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise JobContentFetchError("Job posting host could not be resolved") from exc
    if not addresses:
        raise JobContentFetchError("Job posting host could not be resolved")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise UnsafeJobUrlError("Private or local network URLs are not allowed")


def fetch_job_content(url: str) -> tuple[str, str | None, str]:
    current_url = url
    with httpx.Client(timeout=8.0, follow_redirects=False, trust_env=False) as client:
        for redirect_count in range(MAX_REDIRECTS + 1):
            validate_public_url(current_url)
            try:
                with client.stream(
                    "GET",
                    current_url,
                    headers={"User-Agent": "JobOpsRadar/0.1 (+job-analysis)"},
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location or redirect_count == MAX_REDIRECTS:
                            raise JobContentFetchError("Too many or invalid redirects")
                        current_url = urljoin(current_url, location)
                        continue
                    response.raise_for_status()
                    media_type = response.headers.get("content-type", "").lower()
                    if not any(kind in media_type for kind in ("text/", "html", "xhtml")):
                        raise JobContentFetchError("URL did not return a text document")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise JobContentFetchError("Job posting page is too large")
                    content = bytes(body).decode(response.encoding or "utf-8", errors="replace")
            except httpx.HTTPError as exc:
                raise JobContentFetchError("Job posting page could not be fetched") from exc
            title, text = extract_visible_text(content)
            if not text:
                raise JobContentFetchError("No readable job posting text was found")
            return current_url, title, text
    raise JobContentFetchError("Job posting page could not be fetched")
