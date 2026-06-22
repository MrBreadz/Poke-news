"""
Couche d'abstraction LLM — 3 modes :
  1. Gemini Flash (clé Google AI Studio gratuite)
  2. Mode dégradé : titre nettoyé + extrait brut traduit approximativement
  3. Claude (si exécuté dans Claude Cowork, sans clé API)
"""
import logging
import os
import re
from typing import List, Protocol

from .normalize import NewsItem

logger = logging.getLogger(__name__)


class Summarizer(Protocol):
    def summarize(self, item: NewsItem) -> dict:
        """Retourne {'title_fr': str, 'summary_fr': str}"""
        ...


# ── Mode dégradé (aucune clé requise) ─────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Supprime toutes les balises HTML d'un texte."""
    import re
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


_SIMPLE_TRANSLATIONS = {
    "new set": "nouveau set",
    "release date": "date de sortie",
    "card reveal": "révélation de carte",
    "print run": "tirage",
    "restock": "réapprovisionnement",
    "graded": "gradé",
    "price": "prix",
    "market": "marché",
    "leak": "leak",
    "rumor": "rumeur",
    "artwork": "illustration",
    "out of stock": "rupture de stock",
    "in stock": "en stock",
}


def _basic_translate(text: str) -> str:
    for en, fr in _SIMPLE_TRANSLATIONS.items():
        text = re.sub(en, fr, text, flags=re.IGNORECASE)
    return text


class DegradedSummarizer:
    """Sans LLM : titre nettoyé + extrait brut (100 % offline, 0 API)."""

    def summarize(self, item: NewsItem) -> dict:
        title = _basic_translate(item._raw_title)
        body = _strip_html(item._raw_body).strip()
        # Extrait les 3 premières phrases
        sentences = re.split(r"(?<=[.!?])\s+", body)[:3]
        summary = _basic_translate(" ".join(sentences)) if sentences else title
        return {"title_fr": title, "summary_fr": summary or title}


# ── Mode Gemini Flash (clé gratuite Google AI Studio) ─────────────────────────

class GeminiSummarizer:
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-lite")

    def summarize(self, item: NewsItem) -> dict:
        prompt = f"""Tu es un expert Pokémon TCG. Résume l'article suivant en FRANÇAIS.
Règles :
- Titre court et accrocheur (max 12 mots)
- Résumé de 3 à 5 phrases, reformulé (jamais copié-collé)
- Ne jamais inventer de prix, dates ou chiffres absents de la source
- Marquer "⚠️ Rumeur non confirmée" si c'est un leak
- Réponse UNIQUEMENT au format JSON : {{"title_fr": "...", "summary_fr": "..."}}

Source : {item.source_name}
Titre original : {item._raw_title}
Contenu : {item._raw_body[:1500]}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Extraire le JSON
            import json
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return {
                    "title_fr": data.get("title_fr", item._raw_title),
                    "summary_fr": data.get("summary_fr", item._raw_title),
                }
        except Exception as e:
            logger.warning(f"[Gemini] {item.id}: {e}")
        return {"title_fr": item._raw_title, "summary_fr": item._raw_body[:300]}


# ── Factory ────────────────────────────────────────────────────────────────────

def build_summarizer() -> Summarizer:
    """Choisit automatiquement le meilleur summarizer disponible."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        logger.info("[Summarizer] Mode Gemini Flash activé")
        try:
            return GeminiSummarizer(api_key)
        except Exception as e:
            logger.warning(f"[Summarizer] Gemini init failed: {e} — fallback dégradé")
    logger.info("[Summarizer] Mode dégradé (sans LLM)")
    return DegradedSummarizer()


def summarize_all(items: List[NewsItem], summarizer: Summarizer) -> List[NewsItem]:
    for i, item in enumerate(items):
        try:
            result = summarizer.summarize(item)
            item.title_fr = result.get("title_fr", item._raw_title)
            item.summary_fr = result.get("summary_fr", item._raw_title)
            logger.debug(f"[Summarize] {i+1}/{len(items)}: {item.title_fr[:60]}")
        except Exception as e:
            logger.warning(f"[Summarize] item {item.id}: {e}")
            item.title_fr = item._raw_title
            item.summary_fr = item._raw_body[:300] or item._raw_title
    return items
