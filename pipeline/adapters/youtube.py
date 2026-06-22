import hashlib
import logging
from datetime import datetime, timezone
from typing import List

import feedparser

from .base import Adapter, RawItem

logger = logging.getLogger(__name__)


class YouTubeAdapter(Adapter):
    """Récupère les dernières vidéos d'une chaîne YouTube via RSS — sans clé API."""

    def __init__(self, name: str, channel_id: str, lang: str, weight: int):
        self.name = name
        self.channel_id = channel_id
        self.lang = lang
        self.weight = weight

    def fetch(self) -> List[RawItem]:
        items = []
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                video_id = entry.get("yt_videoid", "")
                title = entry.get("title", "").strip()
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                if not video_id or not title:
                    continue

                thumbnail = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                body = entry.get("summary", "") or ""

                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    published = datetime(*published_parsed[:6], tzinfo=timezone.utc).isoformat()
                else:
                    published = datetime.now(timezone.utc).isoformat()

                item_id = hashlib.md5(f"yt:{video_id}".encode()).hexdigest()[:12]
                items.append(RawItem(
                    id=item_id,
                    title=title,
                    url=video_url,
                    source_name=self.name,
                    source_type="youtube",
                    published_at=published,
                    language=self.lang,
                    body_text=body[:1000],
                    image_url=thumbnail,
                    extra={"weight": self.weight, "video_id": video_id},
                ))
            logger.info(f"[YouTube] {self.name}: {len(items)} items")
        except Exception as e:
            logger.warning(f"[YouTube] {self.name} failed: {e}")
        return items
