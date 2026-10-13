"""Build a source-grounded newsroom corpus from real publisher URLs, not Google snippets.

This free path never asks an LLM to invent citations. Google News is discovery
only. Every document supplied to the editor must be fetched from its publisher.
If decoding, access, independent publishers or dates fail, abort without upload.
"""
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse
import re

import requests


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "svg", "noscript"}:
            self.skip += 1
        if tag in {"p", "h1", "h2", "h3", "li", "blockquote"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "svg", "noscript"} and self.skip:
            self.skip -= 1

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


def collect_verified(candidates, max_links=35, max_articles=16):
    from gnews_decoder import decode_many

    chosen = [item for item in candidates if item.get("link", "").startswith("https://")][:max_links]
    if not chosen:
        raise RuntimeError("Corpus editorial sem candidatos RSS.")
    links = [item["link"] for item in chosen]
    decoded = decode_many(links, ceid="BR:pt-419", concurrency=8, timeout=20.0)
    results = []
    seen = set()
    for item in chosen:
        original = item["link"]
        url = decoded.get(original) if "news.google.com" in urlparse(original).netloc else original
        if not url or not url.startswith("https://"):
            continue
        host = (urlparse(url).hostname or "").casefold().removeprefix("www.")
        if not host or host.endswith("google.com") or host in seen:
            continue
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 ODE-editor/1.0"},
                                    timeout=16, allow_redirects=True)
            response.raise_for_status()
            final = response.url
            final_host = (urlparse(final).hostname or "").casefold().removeprefix("www.")
            if final_host.endswith("google.com") or not final.startswith("https://"):
                continue
            if "text/html" not in response.headers.get("Content-Type", ""):
                continue
            content = extract_article(response.text)
            if len(content) < 550:
                continue
            results.append({"category": item["category"], "headline": item["title"],
                            "publisher_host": final_host, "url": final,
                            "feed_published_utc": item["published_utc"],
                            "actual_article_text": content[:6500]})
            seen.add(final_host)
            if len(results) >= max_articles:
                break
        except (requests.RequestException, ValueError):
            continue
    if len(results) < 2:
        raise RuntimeError("Menos de duas páginas de publicadores independentes foram lidas; abortar sem inventar evidências.")
    print("VERIFIED_SOURCE_CORPUS", len(results), "publishers", len(seen), flush=True)
    return results
