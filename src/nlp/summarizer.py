"""
Résumé automatique des fiches de poste.
Utilise une approche extractive simple (pas besoin de gros modèle).
"""
import re
import logging

logger = logging.getLogger(__name__)


class JobSummarizer:
    """Résume les descriptions de poste en extrayant les phrases clés."""

    KEY_PATTERNS = [
        r"(?:nous recherchons|we are looking for).*?[.!]",
        r"(?:votre mission|your mission|missions principales).*?[.!]",
        r"(?:profil recherché|profil idéal|you have|vous avez).*?[.!]",
        r"(?:rejoignez|join us|pourquoi nous).*?[.!]",
    ]

    @staticmethod
    def _extract_key_sentences(text: str, max_sentences: int = 3) -> str:
        """Extrait les phrases les plus informatives."""
        if not text or len(text) < 50:
            return text or ""

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not sentences:
            return text[:300] + "..."

        # Score chaque phrase
        scored = []
        keywords = [
            "recherche", "mission", "profil", "compétence", "expérience",
            "salaire", "avantage", "environnement", "équipe", "projet",
        ]
        for sentence in sentences:
            score = sum(1 for kw in keywords if kw in sentence.lower())
            # Bonus pour les premières phrases
            idx = sentences.index(sentence)
            if idx < 3:
                score += 2
            scored.append((score, sentence))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[:max_sentences]
        best.sort(key=lambda x: sentences.index(x[1]))

        return ". ".join(s[1] for s in best) + "."

    def summarize(self, description: str) -> str:
        """Génère un résumé concis d'une description de poste."""
        return self._extract_key_sentences(description)

    def summarize_batch(self, descriptions: list[str]) -> list[str]:
        """Résume un lot de descriptions."""
        summaries = [self.summarize(d) for d in descriptions]
        logger.info(f"📝 {len(summaries)} résumés générés")
        return summaries
