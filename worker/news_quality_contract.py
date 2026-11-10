"""Bind a machine editorial review to the exact content it reviewed."""
import hashlib
import json


def editorial_fingerprint(episode):
    keys = ("news_date", "title", "thumbnail_headline", "sources", "verified_facts",
            "segments", "news_selection", "publication_description")
    payload = {key: episode.get(key) for key in keys}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()
