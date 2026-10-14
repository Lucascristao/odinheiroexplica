"""Cost-free news discovery: RSS headlines and links, never unverified narration.

This scout does NOT mark any content as editorially verified or trigger an upload.
All selected stories still need source checks and authored scripts.
"""
import argparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DIRECT_FEEDS = (
    ("jovempan", "politica", "https://jovempan.com.br/feed"),
    ("revistaoeste", "politica", "https://revistaoeste.com/feed/"),
    ("poder360", "politica", "https://www.poder360.com.br/feed/"),
    ("braziljournal", "empresas", "https://braziljournal.com/feed/"),
    ("moneytimes", "economia", "https://www.moneytimes.com.br/feed/"),
    ("suno", "economia", "https://www.suno.com.br/noticias/feed/"),
    ("bmcnews", "economia", "https://bmcnews.com.br/feed/"),
)

SEARCHES = {
    "politica": "política brasil congresso STF TSE presidência eleições hoje",
    "economia": "economia brasil ultimas noticias",
    "empresas": "empresas negocios brasil investimento",
    "tecnologia": "tecnologia inteligência artificial negócios brasil",
    "consumidor": "bancos pix consumidor Brasil",
    "internacional": "economia internacional geopolítica brasil hoje",
}
TOPICS = tuple(SEARCHES)


def parse_rss(xml: bytes, category: str, now: datetime) -> list[dict]:
    # Normalizar prefixos XML de WordPress (ex.: content:encoded, dc:creator) para evitar falhas de namespace
    cleaned = re.sub(rb"<(/?)[a-zA-Z0-9_-]+:([a-zA-Z0-9_-]+)", rb"<\1\2", xml)
    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return []
    results = []
    for item in root.findall(".//item"):
        title = " ".join((item.findtext("title") or "").split())
        url = (item.findtext("link") or item.findtext("guid") or "").strip()
        date_text = item.findtext("pubDate") or ""
        if not title or not url.startswith("https://") or not date_text:
            continue
        try:
            published = parsedate_to_datetime(date_text).astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError):
            continue
        if published < now - timedelta(hours=30) or published > now + timedelta(minutes=15):
            continue
        results.append({"category": category, "title": title[:220],
                        "link": url, "published_utc": published.isoformat(),
                        "verification": "unverified_candidate"})
    return results[:12]


def collect(now=None) -> dict:
    now = now or datetime.now(timezone.utc)
    seen = set()
    entries = []
    errors = []
    by_category = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 ODE-News-Scout/1.0"}

    # 1. Feeds diretos e verificados de direita, liberais e cobertura de mercado
    for feed_id, category, url in DIRECT_FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                parsed = parse_rss(response.read(2_000_000), category, now)
                by_category.setdefault(category, []).extend(parsed)
        except Exception as exc:
            errors.append(f"direct_{feed_id}: {type(exc).__name__}")

    # 2. Busca ampla temática no Google News RSS
    for category in TOPICS:
        query = urllib.parse.quote(SEARCHES[category])
        url = "https://news.google.com/rss/search?q=" + query + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                parsed = parse_rss(response.read(2_000_000), category, now)
                by_category.setdefault(category, []).extend(parsed)
        except Exception as exc:
            errors.append(f"gnews_{category}: {type(exc).__name__}")

    # Mesclar editorias garantindo pluralidade de fontes e evitando repetições
    max_items = max((len(items) for items in by_category.values()), default=0)
    for index in range(max_items):
        for category in TOPICS:
            items = by_category.get(category, [])
            if index < len(items):
                article = items[index]
                key = re.sub(r"\W+", "", article["title"].lower())
                if key not in seen:
                    seen.add(key)
                    entries.append(article)
    return {"version": "1.0", "generated_at_utc": now.isoformat(),
            "editorial_status": "candidates_only_not_fact_checked",
            "candidates": entries[:70], "feed_errors": errors}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    results = collect()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NEWS_SCOUT: {len(results['candidates'])} candidates ({len(results['feed_errors'])} feeds failed)")
    if not results["candidates"]:
        raise RuntimeError("Noticiário sem fontes recentes disponíveis; não fabricar notícia.")


if __name__ == "__main__":
    main()
