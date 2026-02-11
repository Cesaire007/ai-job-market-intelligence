"""Tests pour le module d'extraction de compétences."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp.skill_extractor import SkillExtractor


class TestSkillExtractor:

    def setup_method(self):
        self.extractor = SkillExtractor(use_model=False)

    def test_extract_python(self):
        result = self.extractor.extract("Nous cherchons un développeur Python")
        assert "python" in result["tech_skills"]

    def test_extract_multiple_skills(self):
        text = "Compétences requises : Python, SQL, Docker, Kubernetes et AWS"
        result = self.extractor.extract(text)
        assert "python" in result["tech_skills"]
        assert "sql" in result["tech_skills"]
        assert "docker" in result["tech_skills"]
        assert "aws" in result["tech_skills"]

    def test_extract_soft_skills(self):
        text = "Le candidat doit faire preuve d'autonomie et de rigueur"
        result = self.extractor.extract(text)
        assert "autonomie" in result["soft_skills"]
        assert "rigueur" in result["soft_skills"]

    def test_skill_count(self):
        text = "Python, SQL, et autonomie requises"
        result = self.extractor.extract(text)
        assert result["skill_count"] == len(result["tech_skills"]) + len(result["soft_skills"])

    def test_no_skills_found(self):
        result = self.extractor.extract("Bonjour le monde")
        assert result["skill_count"] == 0

    def test_case_insensitive(self):
        result = self.extractor.extract("PYTHON et TensorFlow sont nécessaires")
        assert "python" in result["tech_skills"]
        assert "tensorflow" in result["tech_skills"]

    def test_bi_tools(self):
        result = self.extractor.extract("Maîtrise de Power BI et Tableau souhaitée")
        assert "power bi" in result["tech_skills"]
        assert "tableau" in result["tech_skills"]

    def test_batch_extraction(self):
        texts = [
            "Python et SQL requis",
            "Expérience en Docker et Kubernetes",
        ]
        results = self.extractor.extract_batch(texts)
        assert len(results) == 2
        assert "python" in results[0]["tech_skills"]
        assert "docker" in results[1]["tech_skills"]
