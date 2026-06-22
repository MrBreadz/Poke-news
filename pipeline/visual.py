"""Garantit qu'il y a au moins 1 visuel par item (fallback générique par catégorie)."""
from typing import List
from .normalize import NewsItem

# Images de fallback par catégorie (hébergées sur le CDN PokeAPI, toujours dispo)
FALLBACK_IMAGES = {
    "nouveaux_sets":    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/384.png",  # Rayquaza
    "nouvelles_cartes": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png",   # Pikachu
    "impression":       "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/143.png",  # Snorlax
    "stocks":           "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/133.png",  # Eevee
    "prix_marche":      "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/6.png",    # Charizard
    "cartes_gradees":   "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/150.png",  # Mewtwo
    "leaks_niche":      "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/249.png",  # Lugia
    "default":          "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/151.png",  # Mew
}


def ensure_visuals(items: List[NewsItem]) -> List[NewsItem]:
    for item in items:
        if not item.image_url:
            item.image_url = FALLBACK_IMAGES.get(item.category, FALLBACK_IMAGES["default"])
    return items
