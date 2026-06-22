import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import List

import requests

from .base import Adapter, RawItem

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "PokeNewsBot/1.0 (contact: pokenews@example.com)"}


class RedditAdapter(Adapter):
    def __init__(self, sub: str, weight: int, limit: int = 25):
        self.sub = sub
        self.weight = weight
        self.limit = limit

    def fetch(self) -> List[RawItem]:
        items = []
        url = f"https://www.reddit.com/r/{self.sub}/new.json?limit={self.limit}"
        try:
            time.sleep(1)  # respect Reddit rate-limit
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            posts = r.json()["data"]["children"]

            for post in posts:
                d = post["data"]
                # Filtre : on ignore les posts supprimés ou vides
                if d.get("removed_by_category") or d.get("selftext") == "[removed]":
                    continue

                title = d.get("title", "").strip()
                link = d.get("url", "")
                permalink = f"https://reddit.com{d.get('permalink', '')}"
                if not title:
                    continue

                body = d.get("selftext", "")[:2000]

                # Image
                image = None
                if d.get("post_hint") == "image":
                    image = link
                elif d.get("thumbnail") and d["thumbnail"].startswith("http"):
                    image = d["thumbnail"]
                preview = d.get("preview", {}).get("images", [])
                if preview and not image:
                    src = preview[0].get("source", {})
                    image = src.get("url", "").replace("&amp;", "&")

                published = datetime.fromtimestamp(
                    d.get("created_utc", time.time()), tz=timezone.utc
                ).isoformat()

                item_id = hashlib.md5(f"reddit:{d.get('id', title)}".encode()).hexdigest()[:12]
                items.append(RawItem(
                    id=item_id,
                    title=title,
                    url=permalink,
                    source_name=f"r/{self.sub}",
                    source_type="reddit",
                    published_at=published,
                    language="en",
                    body_text=body,
                    image_url=image,
                    extra={"weight": self.weight, "score": d.get("score", 0), "flair": d.get("link_flair_text", "")},
                ))
            logger.info(f"[Reddit] r/{self.sub}: {len(items)} items")
        except Exception as e:
            logger.warning(f"[Reddit] r/{self.sub} failed: {e}")
        return items
