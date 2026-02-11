"""Tests pour le module de classification."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp.classifier import JobClassifier


class TestJobClassifier:

    def setup_method(self):
        self.classifier = JobClassifier(use_model=False)

    def test_classify_data_engineer(self):
        result = self.classifier.classify(
            "Data Engineer", "Nous recherchons un Data Engineer pour construire des pipelines ETL avec Spark et Airflow"
        )
        assert result["category"] == "Data Engineer"

    def test_classify_data_scientist(self):
        result = self.classifier.classify(
            "Data Scientist", "Mission : modélisation machine learning et analyse statistique"
        )
        assert result["category"] == "Data Scientist"

    def test_classify_data_analyst(self):
        result = self.classifier.classify(
            "Data Analyst", "Reporting et visualisation avec Power BI et Tableau"
        )
        assert result["category"] in ["Data Analyst", "Business Intelligence Analyst"]

    def test_classify_returns_confidence(self):
        result = self.classifier.classify("Data Engineer", "Pipeline ETL Spark")
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    def test_classify_returns_method(self):
        result = self.classifier.classify("Data Engineer", "Pipeline ETL")
        assert result["method"] in ["rule_based", "zero_shot", "default"]

    def test_classify_unknown_defaults(self):
        result = self.classifier.classify("Chef de projet", "Gestion d'équipe")
        assert result["category"] is not None
