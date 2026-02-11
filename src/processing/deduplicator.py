"""
Détection de doublons par similarité cosinus sur TF-IDF.
Quand on collecte depuis plusieurs sources, la même offre peut apparaître
plusieurs fois avec des titres légèrement différents.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class Deduplicator:
    """Détecte les offres en double via TF-IDF + cosine similarity."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
        )

    def find_duplicates(self, jobs: list[dict]) -> set[int]:
        """
        Identifie les indices des offres en double.
        Returns: Set d'indices à marquer comme doublons.
        """
        texts = [
            f"{j.get('title', '')} {j.get('company', '')} "
            f"{j.get('description', '')[:200]}"
            for j in jobs
        ]

        if len(texts) < 2:
            return set()

        tfidf_matrix = self.vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_matrix)

        duplicates = set()
        for i in range(len(sim_matrix)):
            if i in duplicates:
                continue
            for j in range(i + 1, len(sim_matrix)):
                if sim_matrix[i][j] >= self.threshold:
                    duplicates.add(j)

        logger.info(f"🔍 {len(duplicates)} doublons détectés sur {len(jobs)} offres")
        return duplicates

    def mark_duplicates(self, jobs: list[dict]) -> list[dict]:
        """Marque les doublons dans la liste d'offres."""
        duplicate_indices = self.find_duplicates(jobs)
        for idx in duplicate_indices:
            jobs[idx]["is_duplicate"] = True
        return jobs
