import hashlib
import logging
from datetime import datetime, timezone
from typing import List

import requests

from .base import Adapter, RawItem

logger = logging.getLogger(__name__)


def _fetch_oembed(tweet_url: str) -> dict:
    """Récupère le contenu d'un tweet via l'API oEmbed publique (gratuit, sans clé)."""
    try:
        r = requests.get(
            "https://publish.twitter.com/oembed",
            params={"url": tweet_url, "omit_script": "true"},
            timeout=8,
            headers={"User-Agent": "PokeNewsBot/1.0"},
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.debug(f"[X seed] oEmbed failed for {tweet_url}: {e}")
    return {}


class XSeedAdapter(Adapter):
    """
    Récupère le contenu de tweets depuis une liste d'URLs manuelles.
    Méthode gratuite : oEmbed public (pas d'OAuth, pas d'API payante).
    """

    def __init__(self, urls: List[str]):
        self.urls = urls

    def fetch(self) -> List[RawItem]:
        items = []
        for tweet_url in self.urls:
            try:
                data = _fetch_oembed(tweet_url)
                if not data:
                    logger.warning(f"[X seed] Impossible de récupérer : {tweet_url}")
                    continue

                html = data.get("html", "")
                author = data.get("author_name", "Compte X")
                # Texte brut extrait du HTML oEmbed
                from html.parser import HTMLParser

                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.parts = []
                        self._in_p = False

                    def handle_starttag(self, tag, attrs):
                        if tag == "p":
                            self._in_p = True

                    def handle_endtag(self, tag):
                        if tag == "p":
                            self._in_p = False

                    def handle_data(self, data):
                        if self._in_p:
                            self.parts.append(data)

                extractor = TextExtractor()
                extractor.feed(html)
                body = " ".join(extractor.parts).strip()

                item_id = hashlib.md5(f"x:{tweet_url}".encode()).hexdigest()[:12]
                items.append(RawItem(
                    id=item_id,
                    title=f"[X] {author} — tweet",
                    url=tweet_url,
                    source_name=f"X/{author}",
                    source_type="x_seed",
                    published_at=datetime.now(timezone.utc).isoformat(),
                    language="ja",  # les comptes seedés sont JP par défaut
                    body_text=body or html[:500],
                    image_url=None,
                    extra={"weight": 4, "author": author},
                ))
                logger.info(f"[X seed] OK: {tweet_url}")
            except Exception as e:
                logger.warning(f"[X seed] {tweet_url}: {e}")
        return items
