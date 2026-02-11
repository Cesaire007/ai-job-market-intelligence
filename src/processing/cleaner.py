"""
Nettoyage de données — la compétence N°1 en Data Science.
Gère : HTML, caractères spéciaux, normalisation salaires/lieux/contrats.
"""
import re
import html
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class JobCleaner:
    """Pipeline de nettoyage pour les offres d'emploi."""

    CONTRACT_MAPPING = {
        "cdi": "CDI", "cdd": "CDD",
        "alternance": "Alternance", "apprentissage": "Alternance",
        "stage": "Stage", "interim": "Intérim", "intérim": "Intérim",
        "freelance": "Freelance",
        "full_time": "CDI", "permanent": "CDI", "contract": "CDD",
    }

    CITY_MAPPING = {
        "paris": "Paris", "ile-de-france": "Paris (Île-de-France)",
        "idf": "Paris (Île-de-France)",
        "lyon": "Lyon", "rhone": "Lyon", "rhône": "Lyon",
        "toulouse": "Toulouse", "marseille": "Marseille",
        "bordeaux": "Bordeaux", "nantes": "Nantes",
        "lille": "Lille", "strasbourg": "Strasbourg",
        "montpellier": "Montpellier", "rennes": "Rennes",
        "remote": "Full Remote", "télétravail": "Full Remote",
        "distanciel": "Full Remote",
    }

    def clean_html(self, text: str) -> str:
        """Supprime les balises HTML et décode les entités."""
        if not text:
            return ""
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def normalize_salary(
        self, salary_min: Optional[float], salary_max: Optional[float]
    ) -> tuple[Optional[float], Optional[float]]:
        """Normalise les salaires en € annuel brut."""
        if salary_min and salary_min < 500:
            pass  # Probablement en K€
        elif salary_min and salary_min < 10000:
            salary_min *= 12  # Mensuel → annuel
            if salary_max:
                salary_max *= 12

        # Filtre aberrations
        if salary_min and (salary_min < 15000 or salary_min > 200000):
            salary_min = None
        if salary_max and (salary_max < 15000 or salary_max > 200000):
            salary_max = None

        # Corrige min > max
        if salary_min and salary_max and salary_min > salary_max:
            salary_min, salary_max = salary_max, salary_min

        return salary_min, salary_max

    def normalize_location(self, location: str) -> str:
        """Normalise les noms de villes."""
        if not location:
            return "Non précisé"
        location_lower = location.lower().strip()
        for key, normalized in self.CITY_MAPPING.items():
            if key in location_lower:
                return normalized
        return location.strip().title()

    def normalize_contract(self, contract: str) -> str:
        """Normalise les types de contrat."""
        if not contract:
            return "Non précisé"
        contract_lower = contract.lower().strip()
        return self.CONTRACT_MAPPING.get(contract_lower, contract.title())

    def detect_experience_level(self, title: str, description: str) -> str:
        """Détecte le niveau d'expérience (feature engineering)."""
        text = f"{title} {description}".lower()

        if any(w in text for w in ["alternance", "apprentissage", "alternant"]):
            return "alternance"
        elif any(w in text for w in ["stage", "stagiaire", "intern"]):
            return "stage"
        elif any(w in text for w in ["junior", "débutant", "0-2 ans", "1-2 ans"]):
            return "junior"
        elif any(w in text for w in ["senior", "lead", "principal", "5+ ans", "expert"]):
            return "senior"
        elif any(w in text for w in ["manager", "head of", "directeur", "cto", "vp"]):
            return "management"
        else:
            return "confirmé"

    def clean(self, job: dict) -> dict:
        """Pipeline de nettoyage complet pour une offre (ETL: Transform)."""
        job["title"] = self.clean_html(job.get("title", ""))
        job["description"] = self.clean_html(job.get("description", ""))
        job["company"] = self.clean_html(job.get("company", ""))
        job["location"] = self.normalize_location(job.get("location", ""))
        job["contract_type"] = self.normalize_contract(job.get("contract_type", ""))

        job["salary_min"], job["salary_max"] = self.normalize_salary(
            job.get("salary_min"), job.get("salary_max")
        )
        job["experience_level"] = self.detect_experience_level(
            job.get("title", ""), job.get("description", "")
        )
        return job

    def clean_batch(self, jobs: list[dict]) -> list[dict]:
        """Nettoie un lot d'offres."""
        cleaned = [self.clean(job) for job in jobs]
        logger.info(f"🧹 {len(cleaned)} offres nettoyées")
        return cleaned
