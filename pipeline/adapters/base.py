from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RawItem:
    id: str
    title: str
    url: str
    source_name: str
    source_type: str      # rss | reddit | youtube | tcgdex | x_seed
    published_at: str     # ISO 8601
    language: str         # fr | en | ja
    body_text: str
    image_url: Optional[str] = None
    extra: dict = field(default_factory=dict)


class Adapter(ABC):
    @abstractmethod
    def fetch(self) -> List[RawItem]:
        pass
