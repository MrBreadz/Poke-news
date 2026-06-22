import hashlib
import logging
from typing import List, Optional
from datetime import datetime, timezone

import feedparser
import requests

from .base import Adapter, RawItem

logger = logging.getLogger(__name__)


def _og_image(url: str) -> Optional[str]:
    """Tente de récupérer og:image depuis la page HTML."""
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "PokeNewsBot/1.0"})
        if r.status_code == 200:
            from html.parser import HTMLParser

            class OGParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.og_image = None

                def handle_starttag(self, tag, attrs):
                    if tag == "meta":
                        d = dict(attrs)
                        if d.get("property") == "og:image" and d.get("content"):
                            self.og_image = d["content"]

            p = OGParser()
            p.feed(r.text[:20_000])
            return p.og_image
    except Exception:
        pass
    return None


def _parse_date(entry) -> str:
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


class RSSAdapter(Adapter):
    def __init__(self, name: str, url: str, lang: str, weight: int):
        self.name = name
        self.url = url
        self.lang = lang
        self.weight = weight

    def fetch(self) -> List[RawItem]:
        items = []
        try:
            feed = feedparser.parse(self.url)
            for entry in feed.entries[:20]:
                url = entry.get("link", "")
                title = entry.get("title", "").strip()
                if not url or not title:
                    continue

                body = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")

                # Image : media_thumbnail > enclosure > og:image
                image = None
                if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    image = entry.media_thumbnail[0].get("url")
                if not image and hasattr(entry, "enclosures"):
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("image"):
                            image = enc.get("href") or enc.get("url")
                            break
                if not image:
                    image = _og_image(url)

                item_id = hashlib.md5(f"{url}{title}".encode()).hexdigest()[:12]
                items.append(RawItem(
                    id=item_id,
                    title=title,
                    url=url,
                    source_name=self.name,
                    source_type="rss",
                    published_at=_parse_date(entry),
                    language=self.lang,
                    body_text=body[:2000],
                    image_url=image,
                    extra={"weight": self.weight},
                ))
            logger.info(f"[RSS] {self.name}: {len(items)} items")
        except Exception as e:
            logger.warning(f"[RSS] {self.name} failed: {e}")
        return items
