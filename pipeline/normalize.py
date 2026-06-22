"""Normalise les RawItems en un schéma unifié (NewsItem partiel, avant enrichissement)."""
from dataclasses import dataclass, field
from typing import List, Optional
from .adapters.base import RawItem


@dataclass
class NewsItem:
    id: str
    title_fr: str          # titre en français (rempli par summarize)
    summary_fr: str        # résumé FR (rempli par summarize)
    category: str          # catégorie principale
    subcategories: List[str] = field(default_factory=list)
    source_name: str = ""
    source_url: str = ""
    published_at: str = ""
    image_url: str = ""
    score: int = 50
    tags: List[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    all_sources: List[dict] = field(default_factory=list)
    # données brutes conservées pour le summarizer
    _raw_title: str = ""
    _raw_body: str = ""
    _raw_lang: str = "en"


def normalize(raw_items: List[RawItem]) -> List[NewsItem]:
    items = []
    for r in raw_items:
        items.append(NewsItem(
            id=r.id,
            title_fr=r.title,   # sera traduit/résumé ensuite
            summary_fr="",
            category="",        # sera déterminé par classify
            source_name=r.source_name,
            source_url=r.url,
            published_at=r.published_at,
            image_url=r.image_url or "",
            score=0,
            tags=[],
            extra=r.extra.copy(),
            all_sources=[{"name": r.source_name, "url": r.url}],
            _raw_title=r.title,
            _raw_body=r.body_text,
            _raw_lang=r.language,
        ))
    return items
