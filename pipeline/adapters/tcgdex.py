import hashlib
import logging
from datetime import datetime, timezone
from typing import List

import requests

from .base import Adapter, RawItem

logger = logging.getLogger(__name__)

TCGDEX_BASE = "https://api.tcgdex.net/v2"
TCGDEX_IMG = "https://assets.tcgdex.net"


class TCGDexAdapter(Adapter):
    """Récupère les derniers sets + prix via l'API TCGdex (gratuite, sans clé)."""

    def __init__(self, lang: str = "fr"):
        self.lang = lang

    def fetch(self) -> List[RawItem]:
        items = []
        try:
            r = requests.get(f"{TCGDEX_BASE}/{self.lang}/sets", timeout=10)
            r.raise_for_status()
            sets = r.json()

            # On prend les 5 sets les plus récents
            for s in sets[-5:]:
                set_id = s.get("id", "")
                name = s.get("name", "")
                release_date = s.get("releaseDate", "")
                card_count = s.get("cardCount", {}).get("total", 0)

                logo_url = f"{TCGDEX_IMG}/{self.lang}/{set_id.replace('-', '/')}/logo.png"

                published = f"{release_date}T00:00:00Z" if release_date else datetime.now(timezone.utc).isoformat()
                body = f"Set {name} — {card_count} cartes. Sorti le {release_date}."

                item_id = hashlib.md5(f"tcgdex:set:{set_id}".encode()).hexdigest()[:12]
                items.append(RawItem(
                    id=item_id,
                    title=f"Set TCG : {name}",
                    url=f"https://www.tcgdex.net/{self.lang}/sets/{set_id}",
                    source_name="TCGdex",
                    source_type="tcgdex",
                    published_at=published,
                    language=self.lang,
                    body_text=body,
                    image_url=logo_url,
                    extra={"weight": 3, "set_id": set_id, "card_count": card_count},
                ))
            logger.info(f"[TCGdex] {len(items)} sets récupérés")
        except Exception as e:
            logger.warning(f"[TCGdex] failed: {e}")
        return items


class PokemonTCGIOAdapter(Adapter):
    """Récupère des données de prix USD via pokemontcg.io (clé gratuite optionnelle)."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def _headers(self):
        h = {"User-Agent": "PokeNewsBot/1.0"}
        if self.api_key:
            h["X-Api-Key"] = self.api_key
        return h

    def fetch(self) -> List[RawItem]:
        # Cet adapter est utilisé principalement pour l'enrichissement
        # des items watchlist, pas pour générer des items autonomes.
        return []

    def get_card_price(self, card_name: str) -> dict:
        """Retourne un dict {name, price_usd, image_url} pour une carte donnée."""
        try:
            r = requests.get(
                "https://api.pokemontcg.io/v2/cards",
                params={"q": f'name:"{card_name}"', "pageSize": 1, "orderBy": "-set.releaseDate"},
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            if data:
                card = data[0]
                prices = card.get("tcgplayer", {}).get("prices", {})
                price = None
                for k in ("holofoil", "normal", "reverseHolofoil"):
                    if k in prices:
                        price = prices[k].get("market")
                        break
                return {
                    "name": card.get("name"),
                    "price_usd": price,
                    "image_url": card.get("images", {}).get("large"),
                    "set_name": card.get("set", {}).get("name"),
                }
        except Exception as e:
            logger.warning(f"[pokemontcg.io] {card_name}: {e}")
        return {}
