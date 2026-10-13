"""Build a source-grounded newsroom corpus from real publisher URLs, not Google snippets.

This free path never asks an LLM to invent citations. Google News is discovery
only. Every document supplied to the editor must be fetched from its publisher.
One publisher is enough to collect a breaking report or exclusive. Collection
proves access to text, not the truth of its claims or independent confirmation.
The editor must attribute single-source reporting and still validate event dates.
If decoding or access fail, return no invented articles.
"""
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse
import re

import requests


NON_CONTENT_TAGS = {"head", "script", "style", "svg", "noscript", "header",
                    "footer", "nav", "aside", "form", "button"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
MIN_ARTICLE_CHARS = 200


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        hidden = ("hidden" in attributes
                  or str(attributes.get("aria-hidden", "")).casefold() == "true"
                  or bool(re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)",
                                    attributes.get("style") or "", flags=re.I)))
        blocked = tag in NON_CONTENT_TAGS or hidden
        if tag not in VOID_TAGS:
            self.stack.append((tag, blocked))
            self.skip += int(blocked)
        if not self.skip and tag in {"p", "h1", "h2", "h3", "li", "blockquote", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.skip -= sum(int(blocked) for _, blocked in self.stack[index:])
                del self.stack[index:]
                break
        if not self.skip and tag in {"p", "h1", "h2", "h3", "li", "blockquote"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip() + " ")


def extract_article(html):
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    match = re.search(r"<article\b[^>]*>(.*?)</article>", html, flags=re.S | re.I)
    if match:
        html = match.group(1)
    else:
        match = re.search(r"<main\b[^>]*>(.*?)</main>", html, flags=re.S | re.I)
        if match:
            html = match.group(1)
    for tag in ("header", "footer", "nav"):
        html = re.sub(fr"<{tag}\b[^>]*>.*?</{tag}>", "", html, flags=re.S | re.I)
    parser = VisibleText()
    parser.feed(html)
    return unescape(re.sub(r"[ \t]+", " ", "".join(parser.parts))).strip()


STOPWORDS = {
    "brasil", "brasileiro", "brasileira", "hoje", "após", "sobre", "para", "com",
    "uma", "que", "dos", "das", "nos", "nas", "pela", "pelo", "mais", "como",
    "entre", "novo", "nova", "anos", "revela", "noticias", "notícia",
}


def headline_terms(title):
    import unicodedata
    unaccented = "".join(
        c for c in unicodedata.normalize("NFKD", title.split(" - ")[0].casefold())
        if not unicodedata.combining(c)
    )
    return {t for t in re.findall(r"[a-z0-9]{4,}", unaccented)
            if t not in STOPWORDS}


def prioritize_same_story(candidates):
    """Favor a news event reported by several outlets without presuming it is verified."""
    terms = [headline_terms(item.get("title", "")) for item in candidates]
    scores = []
    for i, left in enumerate(terms):
        peers = sum(1 for j, right in enumerate(terms) if j != i
                    and len(left & right) >= 3
                    and len(left & right) >= 0.35 * min(len(left), len(right)))
        scores.append(peers)
    return [item for _, item in sorted(zip(scores, candidates),
            key=lambda pair: (-pair[0], -len(headline_terms(pair[1].get("title", ""))))) ]


def publisher_host(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return ""
    host = (parsed.hostname or "").casefold().removeprefix("www.")
    if not host or host == "google.com" or host.endswith(".google.com"):
        return ""
    return host


def is_google_news(url):
    return (urlparse(url).hostname or "").casefold() == "news.google.com"


def has_article_content(html):
    """Reject menus and HTTP-200 error pages without rejecting short real reports."""
    error_headings = {
        "access denied", "forbidden", "403 forbidden", "404 not found",
        "page not found", "página não encontrada", "pagina nao encontrada",
        "just a moment", "attention required | cloudflare", "erro 404",
    }
    for match in re.finditer(r"<(h1|title)\b[^>]*>(.*?)</\1>", html, flags=re.I | re.S):
        heading = extract_article("<article>" + match.group(2) + "</article>")
        heading = " ".join(heading.casefold().split()).strip(" .!?:-")
        if heading in error_headings:
            return False
    if not re.search(r"<(?:article|main|h1)\b", html, flags=re.I):
        return False
    if re.search(r"<article\b", html, flags=re.I):
        return True
    # A main/h1 alone can be a long menu of headlines. Require real body
    # prose, but allow a brief bulletin instead of requiring 550 characters.
    return any(
        len(extract_article("<article>" + match.group(1) + "</article>")) >= 80
        for match in re.finditer(r"<p\b[^>]*>(.*?)</p>", html, flags=re.I | re.S)
    )


def collect_verified(candidates, max_links=54, max_articles=18):
    """Retrieve real source text; independent confirmation is an editorial decision."""
    unique = []
    candidate_links = set()
    for item in candidates:
        link = item.get("link", "")
        if not isinstance(link, str) or not link.startswith("https://") or link in candidate_links:
            continue
        candidate_links.add(link)
        unique.append(item)
    chosen = prioritize_same_story(unique)[:max_links]
    if not chosen:
        raise RuntimeError("Corpus editorial sem candidatos RSS.")
    google_links = list(dict.fromkeys(
        item["link"] for item in chosen if is_google_news(item["link"])
    ))
    decoded = {}
    if google_links:
        try:
            from gnews_decoder import decode_many
            decoded = decode_many(google_links, ceid="BR:pt-419", concurrency=8, timeout=20.0)
            if not isinstance(decoded, dict):
                raise ValueError("Decoder did not return URL mappings.")
        except Exception as exc:
            # Discovery failure must not discard an independently fetched
            # direct publisher URL. Undecoded Google links remain unusable.
            print("GOOGLE_DISCOVERY_UNAVAILABLE", type(exc).__name__, flush=True)
            decoded = {}
    results = []
    requested_urls = set()
    seen_urls = set()
    domain_counts = {}
    for item in chosen:
        original = item["link"]
        url = decoded.get(original) if is_google_news(original) else original
        if not url or not isinstance(url, str):
            continue
        host = publisher_host(url)
        if not host or url in requested_urls or domain_counts.get(host, 0) >= 3:
            continue
        requested_urls.add(url)
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 ODE-editor/1.0"},
                                    timeout=10, allow_redirects=True)
            response.raise_for_status()
            final = response.url
            final_host = publisher_host(final)
            if not final_host or final in seen_urls or domain_counts.get(final_host, 0) >= 3:
                continue
            if "text/html" not in response.headers.get("Content-Type", "").casefold():
                continue
            # A short current article is valid evidence of what its publisher
            # reports. Menus, hidden text and script payloads are not evidence.
            if not has_article_content(response.text):
                continue
            content = extract_article(response.text)
            if len(content) < MIN_ARTICLE_CHARS:
                continue
            results.append({"category": item["category"], "headline": item["title"],
                            "publisher_host": final_host, "url": final,
                            "feed_published_utc": item["published_utc"],
                            "actual_article_text": content[:6000]})
            seen_urls.add(final)
            domain_counts[final_host] = domain_counts.get(final_host, 0) + 1
            if len(results) >= max_articles:
                break
        except (requests.RequestException, ValueError):
            continue
    if not results:
        raise RuntimeError("Nenhuma matéria real pôde ser lida; não fabricar evidências.")
    print("FETCHED_SOURCE_CORPUS", len(results), "publishers", len(domain_counts),
          "single_publisher", len(domain_counts) == 1, flush=True)
    return results
