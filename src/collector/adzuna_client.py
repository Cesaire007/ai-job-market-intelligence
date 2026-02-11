"""
Client API Adzuna — collecte d'offres d'emploi Data/IA en France.
Documentation: https://developer.adzuna.com/
"""
import requests
import logging
from datetime import datetime
from typing import Optional
from config.settings import (
    ADZUNA_APP_ID, ADZUNA_APP_KEY, SEARCH_KEYWORDS, LOCATIONS
)

logger = logging.getLogger(__name__)


class AdzunaClient:
    """Récupère les offres d'emploi Data/IA depuis l'API Adzuna."""

    BASE_URL = "https://api.adzuna.com/v1/api/jobs/fr/search"

    def __init__(self):
        if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
            raise ValueError("Clés API Adzuna manquantes. Vérifie ton fichier .env")
        self.session = requests.Session()

    def fetch_jobs(
        self,
        keyword: str,
        location: Optional[str] = None,
        page: int = 1,
        results_per_page: int = 50,
    ) -> list[dict]:
        """Récupère une page d'offres pour un mot-clé donné."""
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": keyword,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        try:
            url = f"{self.BASE_URL}/{page}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            jobs = data.get("results", [])
            logger.info(
                f"✅ {len(jobs)} offres récupérées pour '{keyword}' à {location or 'France'}"
            )
            return self._standardize(jobs)

        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Timeout pour '{keyword}'")
            return []
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Erreur HTTP {e.response.status_code} pour '{keyword}'")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur inattendue : {e}")
            return []

    def _standardize(self, raw_jobs: list[dict]) -> list[dict]:
        """Standardise les données brutes dans un format commun (data mapping)."""
        standardized = []
        for job in raw_jobs:
            standardized.append({
                "source": "adzuna",
                "external_id": str(job.get("id", "")),
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("display_name", ""),
                "description": job.get("description", ""),
                "location": job.get("location", {}).get("display_name", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "contract_type": job.get("contract_type", ""),
                "url": job.get("redirect_url", ""),
                "created_at": job.get("created", ""),
                "collected_at": datetime.utcnow().isoformat(),
            })
        return standardized

    def collect_all(self) -> list[dict]:
        """Lance la collecte complète : tous les mots-clés × toutes les villes."""
        all_jobs = []
        for keyword in SEARCH_KEYWORDS:
            for location in LOCATIONS:
                jobs = self.fetch_jobs(keyword=keyword, location=location)
                all_jobs.extend(jobs)

        logger.info(f"📊 Total collecté (Adzuna) : {len(all_jobs)} offres brutes")
        return all_jobs
