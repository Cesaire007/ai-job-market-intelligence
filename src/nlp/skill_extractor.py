"""
Extraction de compétences — NLP appliqué au recrutement.
Combine extraction par dictionnaire (rapide) et CamemBERT NER (exhaustif).
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Extrait les compétences techniques et soft skills des descriptions."""

    TECH_SKILLS = {
        # Langages
        "python", "r", "sql", "java", "scala", "javascript", "typescript",
        "c++", "c#", "go", "rust", "julia", "matlab", "sas", "bash",
        # Data & ML
        "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch",
        "keras", "xgboost", "lightgbm", "catboost", "hugging face", "transformers",
        "spacy", "nltk", "opencv", "mlflow", "kubeflow", "airflow", "dagster",
        # Big Data
        "spark", "pyspark", "hadoop", "hive", "kafka", "flink", "databricks",
        "snowflake", "bigquery", "redshift", "dbt",
        # BDD
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "neo4j",
        "cassandra", "dynamodb", "sqlite",
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "github actions", "ci/cd", "mlops", "ansible",
        # Viz & BI
        "power bi", "tableau", "looker", "metabase", "grafana", "superset",
        "matplotlib", "seaborn", "plotly", "streamlit", "dash",
        # Web & API
        "git", "linux", "api rest", "fastapi", "flask", "django",
        "langchain", "rag", "llm", "prompt engineering", "openai",
        # Formats & outils
        "json", "xml", "csv", "parquet", "excel", "jupyter", "vscode",
    }

    SOFT_SKILLS = {
        "communication", "teamwork", "leadership", "problem solving",
        "analytical thinking", "autonomie", "rigueur", "curiosité",
        "esprit d'équipe", "gestion de projet", "agile", "scrum",
        "adaptabilité", "créativité", "esprit critique",
    }

    def __init__(self, use_model: bool = False):
        """
        Args:
            use_model: Active CamemBERT NER (nécessite torch + transformers).
        """
        self.use_model = use_model
        self.ner_pipeline = None
        if use_model:
            try:
                from transformers import pipeline
                self.ner_pipeline = pipeline(
                    "ner",
                    model="Jean-Baptiste/camembert-ner",
                    aggregation_strategy="simple",
                )
                logger.info("✅ CamemBERT NER chargé")
            except Exception as e:
                logger.warning(f"⚠️ CamemBERT NER indisponible : {e}")
                self.use_model = False

    def extract_rule_based(self, text: str) -> dict[str, list[str]]:
        """Extraction par dictionnaire — rapide et déterministe."""
        text_lower = text.lower()

        found_tech = sorted([
            skill for skill in self.TECH_SKILLS
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)
        ])
        found_soft = sorted([
            skill for skill in self.SOFT_SKILLS
            if skill in text_lower
        ])

        return {"tech_skills": found_tech, "soft_skills": found_soft}

    def extract_with_ner(self, text: str) -> list[str]:
        """Extraction via CamemBERT NER pour détecter des entités inconnues."""
        if not self.ner_pipeline:
            return []
        try:
            # On traite par chunks de 512 tokens max
            chunk = text[:1500]
            entities = self.ner_pipeline(chunk)
            return [
                ent["word"].strip()
                for ent in entities
                if ent["entity_group"] in ("ORG", "MISC")
                and len(ent["word"].strip()) > 2
            ]
        except Exception as e:
            logger.warning(f"⚠️ Erreur NER : {e}")
            return []

    def extract(self, text: str) -> dict:
        """
        Extraction complète : règles + modèle optionnel.
        Returns: {"tech_skills": [...], "soft_skills": [...], "skill_count": int}
        """
        results = self.extract_rule_based(text)

        if self.use_model:
            ner_entities = self.extract_with_ner(text)
            # Ajoute les entités NER non déjà trouvées
            existing = set(results["tech_skills"])
            for entity in ner_entities:
                if entity.lower() not in existing:
                    results["tech_skills"].append(entity.lower())

        results["skill_count"] = len(results["tech_skills"]) + len(results["soft_skills"])
        return results

    def extract_batch(self, texts: list[str]) -> list[dict]:
        """Extraction en batch."""
        results = []
        for i, text in enumerate(texts):
            results.append(self.extract(text))
            if (i + 1) % 100 == 0:
                logger.info(f"  Skills extraits : {i + 1}/{len(texts)}")
        logger.info(f"🧠 Extraction terminée : {len(results)} offres analysées")
        return results
