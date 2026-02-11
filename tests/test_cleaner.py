"""Tests pour le module de nettoyage des données."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.processing.cleaner import JobCleaner


class TestJobCleaner:
    """Tests unitaires pour JobCleaner."""

    def setup_method(self):
        self.cleaner = JobCleaner()

    # --- HTML Cleaning ---
    def test_clean_html_removes_tags(self):
        assert self.cleaner.clean_html("<p>Hello <b>World</b></p>") == "Hello World"

    def test_clean_html_decodes_entities(self):
        assert self.cleaner.clean_html("Data &amp; IA") == "Data & IA"

    def test_clean_html_handles_empty(self):
        assert self.cleaner.clean_html("") == ""
        assert self.cleaner.clean_html(None) == ""

    # --- Salary Normalization ---
    def test_normalize_salary_normal_range(self):
        result = self.cleaner.normalize_salary(35000, 45000)
        assert result == (35000, 45000)

    def test_normalize_salary_monthly_to_annual(self):
        result = self.cleaner.normalize_salary(3000, 4000)
        assert result == (36000, 48000)

    def test_normalize_salary_filters_outliers(self):
        result = self.cleaner.normalize_salary(5000000, None)
        assert result == (None, None)

    def test_normalize_salary_corrects_min_max(self):
        result = self.cleaner.normalize_salary(50000, 35000)
        assert result == (35000, 50000)

    def test_normalize_salary_handles_none(self):
        result = self.cleaner.normalize_salary(None, None)
        assert result == (None, None)

    # --- Location ---
    def test_normalize_location_paris(self):
        assert self.cleaner.normalize_location("Paris 75") == "Paris"

    def test_normalize_location_idf(self):
        assert self.cleaner.normalize_location("Ile-de-France") == "Paris (Île-de-France)"

    def test_normalize_location_remote(self):
        assert self.cleaner.normalize_location("Full Remote") == "Full Remote"
        assert self.cleaner.normalize_location("Télétravail") == "Full Remote"

    def test_normalize_location_empty(self):
        assert self.cleaner.normalize_location("") == "Non précisé"

    # --- Contract ---
    def test_normalize_contract_cdi(self):
        assert self.cleaner.normalize_contract("cdi") == "CDI"
        assert self.cleaner.normalize_contract("full_time") == "CDI"

    def test_normalize_contract_alternance(self):
        assert self.cleaner.normalize_contract("alternance") == "Alternance"
        assert self.cleaner.normalize_contract("apprentissage") == "Alternance"

    # --- Experience Level ---
    def test_detect_alternance(self):
        assert self.cleaner.detect_experience_level(
            "Data Analyst en alternance", ""
        ) == "alternance"

    def test_detect_senior(self):
        assert self.cleaner.detect_experience_level(
            "Senior Data Engineer", ""
        ) == "senior"

    def test_detect_junior(self):
        assert self.cleaner.detect_experience_level(
            "Data Scientist Junior", ""
        ) == "junior"

    # --- Full Pipeline ---
    def test_clean_full_job(self):
        job = {
            "title": "<b>Data Engineer</b>",
            "description": "<p>We need a Data Engineer with Python &amp; SQL</p>",
            "company": "TechCorp &amp; Co",
            "location": "Paris 75008",
            "contract_type": "cdi",
            "salary_min": 3500,
            "salary_max": 4500,
        }
        cleaned = self.cleaner.clean(job)
        assert cleaned["title"] == "Data Engineer"
        assert "Python & SQL" in cleaned["description"]
        assert cleaned["location"] == "Paris"
        assert cleaned["contract_type"] == "CDI"
        assert cleaned["salary_min"] == 42000
        assert cleaned["experience_level"] == "confirmé"
