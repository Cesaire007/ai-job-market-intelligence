"""
Normalisation avancée des données — standardisation des champs textuels.
"""
import re
import logging

logger = logging.getLogger(__name__)


class Normalizer:
    """Normalisation avancée des champs textuels."""

    @staticmethod
    def normalize_company_name(name: str) -> str:
        """Normalise les noms d'entreprises (supprime suffixes juridiques)."""
        if not name:
            return "Non précisé"
        name = name.strip()
        # Supprime les formes juridiques courantes
        patterns = [
            r"\b(SAS|SARL|SA|SNC|EURL|SASU|GIE)\b",
            r"\b(Group|Groupe|France)\b$",
        ]
        for pattern in patterns:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()
        return name.strip(" -,.")

    @staticmethod
    def extract_years_experience(text: str) -> int | None:
        """Extrait le nombre d'années d'expérience demandées."""
        if not text:
            return None
        patterns = [
            r"(\d+)\s*(?:à|-)?\s*\d*\s*ans?\s*d['\u2019]?exp",
            r"exp[ée]rience\s*(?:de\s*)?(\d+)\s*ans?",
            r"(\d+)\+?\s*ans?\s*(?:minimum|min)",
            r"(\d+)\s*years?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def detect_remote_policy(text: str) -> str:
        """Détecte la politique de télétravail."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["full remote", "100% remote", "100% télétravail"]):
            return "full_remote"
        elif any(w in text_lower for w in ["hybride", "hybrid", "2 jours", "3 jours"]):
            return "hybrid"
        elif any(w in text_lower for w in ["télétravail", "remote", "teletravail"]):
            return "partial_remote"
        elif any(w in text_lower for w in ["présentiel", "sur site", "on-site"]):
            return "on_site"
        return "unknown"
