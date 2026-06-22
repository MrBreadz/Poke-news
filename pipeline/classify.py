"""Classifie chaque item dans une catégorie + calcule un score de pertinence."""
import re
from typing import List, Tuple
from .normalize import NewsItem

# Catégories avec leurs mots-clés et icônes/couleurs (utilisés aussi dans le front)
CATEGORIES = {
    "nouveaux_sets": {
        "label": "Nouveaux Sets",
        "icon": "🃏",
        "color": "#8b5cf6",
        "keywords": [
            "new set", "nouveau set", "new expansion", "nouvelle extension",
            "stellar crown", "surging sparks", "prismatic evolutions",
            "sv7", "sv8", "sv9", "scarlet violet", "écarlate violet",
            "release date", "date de sortie", "booster box", "set announcement",
            "新弾", "新セット", "発売",
        ],
    },
    "nouvelles_cartes": {
        "label": "Nouvelles Cartes",
        "icon": "✨",
        "color": "#3b82f6",
        "keywords": [
            "alt art", "illustration rare", "secret rare", "full art",
            "special illustration", "card reveal", "new card", "nouvelle carte",
            "artwork", "illustration", "rainbow rare", "gold card",
            "イラストレアリア", "スペシャルイラスト", "新カード",
        ],
    },
    "impression": {
        "label": "Impression",
        "icon": "🖨️",
        "color": "#64748b",
        "keywords": [
            "print run", "printing", "misprint", "error card",
            "centering", "centrage", "quality", "qualité",
            "封入率", "印刷", "製版", "封入", "taux d'insertion",
            "insertion rate", "pull rate",
        ],
    },
    "stocks": {
        "label": "Stocks & Deals",
        "icon": "📦",
        "color": "#f59e0b",
        "keywords": [
            "restock", "in stock", "out of stock", "rupture",
            "disponible", "deal", "discount", "promo",
            "fnac", "cultura", "amazon", "scalping", "scalper",
            "disponibilité", "livraison", "précommande", "preorder",
            "再販", "再入荷", "在庫",
        ],
    },
    "prix_marche": {
        "label": "Prix & Marché",
        "icon": "📈",
        "color": "#f97316",
        "keywords": [
            "price", "prix", "cardmarket", "tcgplayer", "market",
            "value", "valeur", "trending", "tendance", "spike",
            "investment", "investissement", "cote", "graded price",
            "相場", "価格", "値上がり", "高騰",
        ],
    },
    "cartes_gradees": {
        "label": "Cartes Gradées",
        "icon": "🏆",
        "color": "#eab308",
        "keywords": [
            "psa", "bgs", "cgc", "graded", "grading", "gradé",
            "grade", "slab", "population report", "psa 10",
            "gem mint", "mint", "bgs 9.5", "authentification",
            "評価", "グレーディング", "PSA",
        ],
    },
    "leaks_niche": {
        "label": "Leaks & Niche JP",
        "icon": "🔍",
        "color": "#ec4899",
        "keywords": [
            "leak", "rumor", "rumeur", "insider", "niche",
            "prediction", "prédiction", "japanese", "japonais",
            "japan exclusive", "jp", "リーク", "噂", "予想",
            "未公開", "流出",
        ],
    },
}

CATEGORY_ORDER = [
    "nouveaux_sets", "nouvelles_cartes", "leaks_niche",
    "impression", "stocks", "prix_marche", "cartes_gradees",
]


def _count_keywords(text: str, keywords: List[str]) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)


def classify_item(item: NewsItem, global_keywords: List[str]) -> Tuple[str, int, List[str]]:
    """Retourne (catégorie, score, tags)."""
    full_text = f"{item._raw_title} {item._raw_body}".lower()

    # Score catégorie
    scores = {cat: _count_keywords(full_text, data["keywords"]) for cat, data in CATEGORIES.items()}

    # Catégorie dominante
    best_cat = max(scores, key=lambda c: scores[c])
    if scores[best_cat] == 0:
        best_cat = "nouvelles_cartes"  # fallback générique Pokémon

    # Subcatégories : toutes celles avec au moins 1 match
    subcats = [c for c, s in scores.items() if s > 0 and c != best_cat]

    # Score de pertinence 0–100
    kw_score = min(_count_keywords(full_text, global_keywords) * 10, 40)
    cat_score = min(scores[best_cat] * 8, 30)
    source_weight = item.extra.get("weight", 3) * 3  # max 15
    reddit_upvotes = min(item.extra.get("score", 0) // 100, 15)  # max 15
    total = kw_score + cat_score + source_weight + reddit_upvotes
    final_score = min(total, 100)

    # Tags : nom du set / carte détectés
    tags = []
    for kw in ["Charizard", "Pikachu", "Eevee", "Mewtwo", "Umbreon", "151", "SV7", "SV8", "PSA"]:
        if kw.lower() in full_text:
            tags.append(kw)

    return best_cat, final_score, tags[:5]


def classify(items: List[NewsItem], global_keywords: List[str]) -> List[NewsItem]:
    for item in items:
        cat, score, tags = classify_item(item, global_keywords)
        item.category = cat
        item.score = score
        item.tags = tags
        item.subcategories = [c for c in CATEGORY_ORDER if c in [cat] + tags]
    return items
