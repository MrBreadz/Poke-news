"""Sauvegarde l'édition du jour en JSON dans /data/ et met à jour l'index."""
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .normalize import NewsItem


def _item_to_dict(item: NewsItem) -> dict:
    d = asdict(item)
    # Supprimer les champs internes (préfixe _)
    return {k: v for k, v in d.items() if not k.startswith("_")}


def save_edition(items: List[NewsItem], date_str: str, stats: dict, data_dir: str = "data") -> str:
    """Sauvegarde /data/YYYY-MM-DD.json et retourne le chemin."""
    Path(data_dir).mkdir(exist_ok=True)

    edition = {
        "date": date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": [_item_to_dict(i) for i in items],
        "stats": stats,
    }

    path = os.path.join(data_dir, f"{date_str}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(edition, f, ensure_ascii=False, indent=2)

    _update_index(date_str, len(items), data_dir)
    return path


def _update_index(date_str: str, item_count: int, data_dir: str):
    index_path = os.path.join(data_dir, "index.json")
    try:
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        index = {"editions": []}

    # Met à jour ou ajoute l'entrée
    existing = next((e for e in index["editions"] if e["date"] == date_str), None)
    if existing:
        existing["item_count"] = item_count
    else:
        index["editions"].insert(0, {"date": date_str, "item_count": item_count})

    # Garde les 365 derniers jours
    index["editions"] = index["editions"][:365]

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_edition(date_str: str, data_dir: str = "data") -> dict:
    path = os.path.join(data_dir, f"{date_str}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
