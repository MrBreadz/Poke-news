"""
Pokémon TCG Daily — Point d'entrée principal
============================================
Usage :
  python run.py           → run complet (ingest → build → email)
  python run.py --demo    → affiche juste le site depuis les données de démo (pas de fetch réseau)
  python run.py --no-email → run complet sans envoi email
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run")


def run_pipeline(send_email: bool = True):
    """Pipeline complet : ingest → normalize → dedupe → classify → summarize → visual → rank → persist → build → email."""
    import yaml

    from pipeline.adapters.rss import RSSAdapter
    from pipeline.adapters.reddit import RedditAdapter
    from pipeline.adapters.youtube import YouTubeAdapter
    from pipeline.adapters.tcgdex import TCGDexAdapter
    from pipeline.adapters.x_seed import XSeedAdapter
    from pipeline.normalize import normalize
    from pipeline.dedupe import dedupe
    from pipeline.classify import classify
    from pipeline.summarize import build_summarizer, summarize_all
    from pipeline.visual import ensure_visuals
    from pipeline.rank import rank_and_cut
    from pipeline.persist import save_edition
    from pipeline.build import build_site
    from pipeline.email_sender import save_newsletter, send_newsletter

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info(f"═══ Pipeline Pokémon TCG Daily — {today} ═══")

    # ── [0] Config ──────────────────────────────────────────────────────────
    with open("config/sources.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    sources_cfg = cfg.get("sources", {})
    global_keywords = cfg.get("keywords_fr_en", []) + cfg.get("keywords_jp", [])
    max_blocks = cfg.get("max_blocks_per_day", 16)

    # ── [1] INGEST ──────────────────────────────────────────────────────────
    raw_items = []
    sources_fetched = 0

    for src in sources_cfg.get("rss", []):
        try:
            adapter = RSSAdapter(src["name"], src["url"], src.get("lang", "en"), src.get("weight", 3))
            items = adapter.fetch()
            raw_items.extend(items)
            sources_fetched += 1
        except Exception as e:
            logger.warning(f"Source RSS '{src['name']}' ignorée: {e}")

    for src in sources_cfg.get("reddit", []):
        try:
            adapter = RedditAdapter(src["sub"], src.get("weight", 3))
            items = adapter.fetch()
            raw_items.extend(items)
            sources_fetched += 1
        except Exception as e:
            logger.warning(f"Reddit r/{src['sub']} ignoré: {e}")

    for src in sources_cfg.get("youtube", []):
        try:
            adapter = YouTubeAdapter(src["name"], src["channel_id"], src.get("lang", "en"), src.get("weight", 3))
            items = adapter.fetch()
            raw_items.extend(items)
            sources_fetched += 1
        except Exception as e:
            logger.warning(f"YouTube '{src['name']}' ignoré: {e}")

    if sources_cfg.get("market_api", {}).get("tcgdex", {}).get("enabled", True):
        try:
            adapter = TCGDexAdapter(sources_cfg["market_api"]["tcgdex"].get("lang", "fr"))
            raw_items.extend(adapter.fetch())
            sources_fetched += 1
        except Exception as e:
            logger.warning(f"TCGdex ignoré: {e}")

    x_seed_urls = sources_cfg.get("x_manual_seed", [])
    if x_seed_urls:
        try:
            adapter = XSeedAdapter(x_seed_urls)
            raw_items.extend(adapter.fetch())
            sources_fetched += 1
        except Exception as e:
            logger.warning(f"X seed ignoré: {e}")

    logger.info(f"[1/12] Ingest: {len(raw_items)} items bruts depuis {sources_fetched} sources")

    # ── [2] NORMALIZE ────────────────────────────────────────────────────────
    items = normalize(raw_items)
    logger.info(f"[2/12] Normalize: {len(items)} items")

    # ── [3] DEDUPE ────────────────────────────────────────────────────────────
    items = dedupe(items)
    logger.info(f"[3/12] Dedupe: {len(items)} items uniques")

    # ── [5] CLASSIFY ─────────────────────────────────────────────────────────
    items = classify(items, global_keywords)
    logger.info(f"[5/12] Classify: OK")

    # ── [8] RANK / CUT ───────────────────────────────────────────────────────
    items = rank_and_cut(items, max_blocks)
    logger.info(f"[8/12] Rank: top {len(items)} items retenus")

    # ── [6] SUMMARIZE ────────────────────────────────────────────────────────
    summarizer = build_summarizer()
    items = summarize_all(items, summarizer)
    logger.info(f"[6/12] Summarize: OK")

    # ── [7] VISUAL ────────────────────────────────────────────────────────────
    items = ensure_visuals(items)
    logger.info(f"[7/12] Visual: OK")

    # ── [9] PERSIST ─────────────────────────────────────────────────────────
    stats = {
        "sources_fetched": sources_fetched,
        "items_raw": len(raw_items),
        "items_deduplicated": len(items),
        "items_selected": len(items),
    }
    json_path = save_edition(items, today, stats)
    logger.info(f"[9/12] Persist: {json_path}")

    # ── [10] BUILD ────────────────────────────────────────────────────────────
    build_site()
    logger.info(f"[10/12] Build: site généré dans /docs/")

    # ── [11] EMAIL ────────────────────────────────────────────────────────────
    if send_email:
        with open(json_path, encoding="utf-8") as f:
            edition = json.load(f)
        html = save_newsletter(edition)
        send_newsletter(edition, html)
        logger.info(f"[11/12] Email: newsletter générée dans /newsletters/")

    logger.info(f"═══ Pipeline terminé ✓ ═══")
    logger.info(f"    → Ouvre docs/{today}.html dans ton navigateur pour voir le résultat")


def run_demo():
    """Régénère le site depuis les données de démo sans fetch réseau."""
    logger.info("Mode DÉMO — régénération du site depuis les données existantes")
    from pipeline.build import build_site
    build_site()
    logger.info("Site généré dans /docs/ — ouvre docs/index.html dans ton navigateur !")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pokémon TCG Daily pipeline")
    parser.add_argument("--demo", action="store_true", help="Régénère le site sans fetch réseau")
    parser.add_argument("--no-email", action="store_true", help="Run complet sans envoi email")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_pipeline(send_email=not args.no_email)
