import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import List

import feedparser

from .base import Adapter, RawItem

logger = logging.getLogger(__name__)


class RedditAdapter(Adapter):
    """Utilise le flux RSS public de Reddit — pas d'authentification requise."""

    def __init__(self, sub: str, weight: int, limit: int = 25):
        self.sub = sub
        self.weight = weight
        self.limit = limit

    def fetch(self) -> List[RawItem]:
        items = []
        url = f"https://www.reddit.com/r/{self.sub}/new.rss?limit={self.limit}"
        try:
            time.sleep(0.5)
            feed = feedparser.parse(url)
            for entry in feed.entries[:self.limit]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                if not title or not link:
                    continue

                body = entry.get("summary", "")[:2000]

                # Image : cherche dans le contenu
                image = None
                content = entry.get("content", [{}])
                if content:
                    import re
                    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content[0].get("value", ""))
                    if imgs:
                        image = imgs[0]

                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    published = datetime(*published_parsed[:6], tzinfo=timezone.utc).isoformat()
                else:
                    published = datetime.now(timezone.utc).isoformat()

                item_id = hashlib.md5(f"reddit:{link}".encode()).hexdigest()[:12]
                items.append(RawItem(
                    id=item_id,
                    title=title,
                    url=link,
                    source_name=f"r/{self.sub}",
                    source_type="reddit",
                    published_at=published,
                    language="en",
                    body_text=body,
                    image_url=image,
                    extra={"weight": self.weight},
                ))
            logger.info(f"[Reddit] r/{self.sub}: {len(items)} items")
        except Exception as e:
            logger.warning(f"[Reddit] r/{self.sub} failed: {e}")
        return items
