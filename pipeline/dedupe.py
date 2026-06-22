"""Déduplique les items : même URL ou titres très proches → fusion."""
import re
from typing import List
from .normalize import NewsItem


def _slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return " ".join(text.split()[:8])  # 8 premiers mots significatifs


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def dedupe(items: List[NewsItem], similarity_threshold: float = 0.6) -> List[NewsItem]:
    seen_urls: set = set()
    kept: List[NewsItem] = []

    for item in items:
        # Dédupe par URL exacte
        if item.source_url in seen_urls:
            continue

        # Dédupe par similarité de titre
        slug = _slug(item.title_fr)
        duplicate = False
        for existing in kept:
            if _jaccard(slug, _slug(existing.title_fr)) >= similarity_threshold:
                # Fusion : on ajoute la source alternative
                if {"name": item.source_name, "url": item.source_url} not in existing.all_sources:
                    existing.all_sources.append({"name": item.source_name, "url": item.source_url})
                # Garde le meilleur visuel
                if not existing.image_url and item.image_url:
                    existing.image_url = item.image_url
                duplicate = True
                break

        if not duplicate:
            seen_urls.add(item.source_url)
            kept.append(item)

    return kept
