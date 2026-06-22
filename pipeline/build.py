"""Génère le site statique dans /docs/ depuis les JSON de /data/."""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader
from .classify import CATEGORIES

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "site", "templates")
DOCS_DIR = "docs"
ASSETS_SRC = os.path.join(os.path.dirname(__file__), "..", "site", "assets")


def _relative_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        diff = datetime.now(timezone.utc) - dt
        h = int(diff.total_seconds() // 3600)
        if h < 1:
            return "il y a moins d'1h"
        if h < 24:
            return f"il y a {h}h"
        d = h // 24
        return f"il y a {d} jour{'s' if d > 1 else ''}"
    except Exception:
        return ""


def _size_class(score: int) -> str:
    if score >= 82:
        return "bento-large"
    if score >= 65:
        return "bento-medium"
    return "bento-small"


def build_site(data_dir: str = "data"):
    Path(DOCS_DIR).mkdir(exist_ok=True)
    assets_dst = os.path.join(DOCS_DIR, "assets")

    # Copie des assets CSS/JS
    if os.path.exists(ASSETS_SRC):
        if os.path.exists(assets_dst):
            shutil.rmtree(assets_dst)
        shutil.copytree(ASSETS_SRC, assets_dst)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters["relative_time"] = _relative_time
    env.filters["size_class"] = _size_class

    # Charge l'index
    index_path = os.path.join(data_dir, "index.json")
    try:
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
        editions = index.get("editions", [])
    except Exception:
        editions = []

    # Génère une page par édition
    day_tmpl = env.get_template("day.html.j2")
    for edition_meta in editions:
        date_str = edition_meta["date"]
        json_path = os.path.join(data_dir, f"{date_str}.json")
        if not os.path.exists(json_path):
            continue
        with open(json_path, encoding="utf-8") as f:
            edition = json.load(f)

        # Dates précédente / suivante pour la navigation
        idx = editions.index(edition_meta)
        prev_date = editions[idx + 1]["date"] if idx + 1 < len(editions) else None
        next_date = editions[idx - 1]["date"] if idx > 0 else None

        html = day_tmpl.render(
            edition=edition,
            date_str=date_str,
            prev_date=prev_date,
            next_date=next_date,
            all_editions=editions[:30],
            cat_meta=CATEGORIES,
        )
        out_path = os.path.join(DOCS_DIR, f"{date_str}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

    # index.html → redirige vers l'édition la plus récente
    if editions:
        latest = editions[0]["date"]
        index_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=./{latest}.html">
  <title>Pokémon TCG Daily</title>
</head>
<body><p><a href="./{latest}.html">Aller à l'édition du {latest}</a></p></body>
</html>"""
        with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)

    # archive.html
    archive_tmpl = env.get_template("archive.html.j2")
    archive_html = archive_tmpl.render(editions=editions)
    with open(os.path.join(DOCS_DIR, "archive.html"), "w", encoding="utf-8") as f:
        f.write(archive_html)

    print(f"[Build] Site généré dans /{DOCS_DIR}/ ({len(editions)} éditions)")
