"""
Classification des offres par catégorie métier.
Utilise le zero-shot classification (pas besoin de données labellisées).
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class JobClassifier:
    """Classe les offres dans des catégories métier Data/IA."""

    CATEGORIES = [
        "Data Engineer",
        "Data Scientist",
        "Data Analyst",
        "Machine Learning Engineer",
        "MLOps Engineer",
        "NLP Engineer",
        "Business Intelligence Analyst",
        "Data Architect",
        "AI Research Scientist",
    ]

    # Fallback: classification par mots-clés si le modèle n'est pas dispo
    KEYWORD_RULES = {
        "Data Engineer": ["data engineer", "ingénieur données", "etl", "pipeline", "spark", "airflow"],
        "Data Scientist": ["data scientist", "machine learning", "modélisation", "statistique"],
        "Data Analyst": ["data analyst", "analyste données", "reporting", "power bi", "tableau"],
        "Machine Learning Engineer": ["ml engineer", "mlops", "déploiement modèle", "tensorflow"],
        "MLOps Engineer": ["mlops", "ml ops", "kubeflow", "mlflow", "model serving"],
        "NLP Engineer": ["nlp", "natural language", "traitement du langage", "chatbot", "llm"],
        "Business Intelligence Analyst": ["bi analyst", "business intelligence", "décisionnel"],
        "Data Architect": ["data architect", "architecte données", "data governance"],
        "AI Research Scientist": ["research", "chercheur", "r&d", "phd", "deep learning"],
    }

    def __init__(self, use_model: bool = False):
        self.use_model = use_model
        self.classifier = None
        if use_model:
            try:
                from transformers import pipeline
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="joeddav/xlm-roberta-large-xnli",
                )
                logger.info("✅ Zero-shot classifier chargé")
            except Exception as e:
                logger.warning(f"⚠️ Zero-shot indisponible, fallback règles : {e}")
                self.use_model = False

    def classify_rule_based(self, title: str, description: str) -> dict:
        """Classification par mots-clés (fallback rapide)."""
        text = f"{title} {description}".lower()
        scores = {}
        for category, keywords in self.KEYWORD_RULES.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score

        if scores:
            best = max(scores, key=scores.get)
            confidence = scores[best] / max(len(self.KEYWORD_RULES[best]), 1)
            return {
                "category": best,
                "confidence": round(min(confidence, 1.0), 3),
                "method": "rule_based",
            }
        return {"category": "Data Analyst", "confidence": 0.1, "method": "default"}

    def classify(self, title: str, description: str) -> dict:
        """Classifie une offre dans une catégorie métier."""
        if self.use_model and self.classifier:
            try:
                text = f"{title}. {description[:500]}"
                result = self.classifier(
                    text,
                    candidate_labels=self.CATEGORIES,
                    hypothesis_template="Ce poste est un poste de {}.",
                )
                return {
                    "category": result["labels"][0],
                    "confidence": round(result["scores"][0], 3),
                    "method": "zero_shot",
                    "all_scores": dict(
                        zip(result["labels"], [round(s, 3) for s in result["scores"]])
                    ),
                }
            except Exception as e:
                logger.warning(f"⚠️ Erreur zero-shot, fallback : {e}")

        return self.classify_rule_based(title, description)

    def classify_batch(self, jobs: list[dict]) -> list[dict]:
        """Classifie un lot d'offres."""
        results = []
        for i, job in enumerate(jobs):
            result = self.classify(job.get("title", ""), job.get("description", ""))
            results.append(result)
            if (i + 1) % 50 == 0:
                logger.info(f"  Classification : {i + 1}/{len(jobs)}")
        logger.info(f"🏷️ Classification terminée : {len(results)} offres")
        return results
