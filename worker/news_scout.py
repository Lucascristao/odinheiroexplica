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

SEARCHES = {
    "economia": "economia brasil ultimas noticias",
    "empresas": "empresas negocios brasil investimento",
    "tecnologia": "tecnologia inteligência artificial negócios brasil",
    "consumidor": "bancos pix consumidor Brasil",
}
TOPICS = ("economia", "empresas", "tecnologia", "consumidor")


def parse_rss(xml: bytes, category: str, now: datetime) -> list[dict]:
    root = ET.fromstring(xml)
    results = []
    for item in root.findall("./channel/item"):
        title = " ".join((item.findtext("title") or "").split())
        url = (item.findtext("link") or "").strip()
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
    by_url = set()
    entries = []
    errors = []
    for category in TOPICS:
        query = urllib.parse.quote(SEARCHES[category])
        url = "https://news.google.com/rss/search?q=" + query + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ODE-News-Scout/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                items = parse_rss(response.read(2_000_000), category, now)
            for article in items:
                key = re.sub(r"\W+", "", article["title"].lower())
                if key not in by_url:
                    by_url.add(key)
                    entries.append(article)
        except Exception as exc:
            errors.append(f"{category}: {type(exc).__name__}")
    return {"version": "1.0", "generated_at_utc": now.isoformat(),
            "editorial_status": "candidates_only_not_fact_checked",
            "candidates": entries[:35], "feed_errors": errors}


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
