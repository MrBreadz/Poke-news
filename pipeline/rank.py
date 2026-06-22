"""Trie les items par pertinence + fraîcheur, garde le top N."""
from datetime import datetime, timezone
from typing import List

from .normalize import NewsItem
from .classify import CATEGORY_ORDER


def _freshness_bonus(published_at: str) -> float:
    """Donne un bonus de fraîcheur (max 10 points pour < 6h, 0 pour > 48h)."""
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        if age_hours < 6:
            return 10.0
        elif age_hours < 12:
            return 7.0
        elif age_hours < 24:
            return 4.0
        elif age_hours < 48:
            return 1.0
    except Exception:
        pass
    return 0.0


def rank_and_cut(items: List[NewsItem], max_blocks: int = 16) -> List[NewsItem]:
    # Score final = score pertinence + bonus fraîcheur
    for item in items:
        item.score = min(100, item.score + int(_freshness_bonus(item.published_at)))

    # Tri : score décroissant, puis catégorie prioritaire
    cat_priority = {cat: i for i, cat in enumerate(CATEGORY_ORDER)}
    items.sort(key=lambda x: (-x.score, cat_priority.get(x.category, 99)))

    # On garde max_blocks items, en s'assurant de couvrir au moins 4 catégories différentes
    kept = []
    seen_cats: dict = {}
    for item in items:
        if len(kept) >= max_blocks:
            break
        kept.append(item)
        seen_cats[item.category] = seen_cats.get(item.category, 0) + 1

    return kept
