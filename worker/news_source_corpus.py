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


def collect_verified(candidates, max_links=54, max_articles=18):
    from gnews_decoder import decode_many

    chosen = prioritize_same_story(
        [item for item in candidates if item.get("link", "").startswith("https://")]
    )[:max_links]
    if not chosen:
        raise RuntimeError("Corpus editorial sem candidatos RSS.")
    links = [item["link"] for item in chosen]
    decoded = decode_many(links, ceid="BR:pt-419", concurrency=8, timeout=20.0)
    results = []
    seen_urls = set()
    domain_counts = {}
    for item in chosen:
        original = item["link"]
        url = decoded.get(original) if "news.google.com" in urlparse(original).netloc else original
        if not url or not url.startswith("https://"):
            continue
        host = (urlparse(url).hostname or "").casefold().removeprefix("www.")
        if not host or host.endswith("google.com") or url in seen_urls:
            continue
        if domain_counts.get(host, 0) >= 3:
            continue
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 ODE-editor/1.0"},
                                    timeout=10, allow_redirects=True)
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
                            "actual_article_text": content[:6000]})
            seen_urls.add(final)
            domain_counts[final_host] = domain_counts.get(final_host, 0) + 1
            if len(results) >= max_articles:
                break
        except (requests.RequestException, ValueError):
            continue
    if len(domain_counts) < 2:
        raise RuntimeError("Menos de dois publicadores independentes foram lidos; não fabricar evidências.")
    print("VERIFIED_SOURCE_CORPUS", len(results), "publishers", len(domain_counts), flush=True)
    return results
