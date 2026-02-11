"""
Client API France Travail (ex-Pôle Emploi) — offres d'emploi officielles.
Documentation: https://francetravail.io/data/api
"""
import requests
import logging
from datetime import datetime
from typing import Optional
from config.settings import FRANCE_TRAVAIL_CLIENT_ID, FRANCE_TRAVAIL_CLIENT_SECRET

logger = logging.getLogger(__name__)


class FranceTravailClient:
    """Récupère les offres d'emploi depuis l'API France Travail."""

    AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
    SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

    def __init__(self):
        if not FRANCE_TRAVAIL_CLIENT_ID or not FRANCE_TRAVAIL_CLIENT_SECRET:
            raise ValueError("Clés API France Travail manquantes. Vérifie ton .env")
        self.session = requests.Session()
        self.access_token = None

    def _authenticate(self):
        """Obtient un token OAuth2 pour accéder à l'API."""
        data = {
            "grant_type": "client_credentials",
            "client_id": FRANCE_TRAVAIL_CLIENT_ID,
            "client_secret": FRANCE_TRAVAIL_CLIENT_SECRET,
            "scope": "api_offresdemploiv2 o2dsoffre",
        }
        try:
            response = self.session.post(
                f"{self.AUTH_URL}?realm=%2Fpartenaire",
                data=data,
                timeout=10,
            )
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            self.session.headers.update(
                {"Authorization": f"Bearer {self.access_token}"}
            )
            logger.info("✅ Authentification France Travail réussie")
        except Exception as e:
            logger.error(f"❌ Authentification France Travail échouée : {e}")
            raise

    def fetch_jobs(
        self,
        keyword: str,
        location: Optional[str] = None,
        page: int = 0,
        results_per_page: int = 50,
    ) -> list[dict]:
        """Récupère des offres depuis France Travail."""
        if not self.access_token:
            self._authenticate()

        params = {
            "motsCles": keyword,
            "range": f"{page * results_per_page}-{(page + 1) * results_per_page - 1}",
        }
        if location:
            params["commune"] = location

        try:
            response = self.session.get(
                self.SEARCH_URL, params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            jobs = data.get("resultats", [])
            logger.info(f"✅ {len(jobs)} offres France Travail pour '{keyword}'")
            return self._standardize(jobs)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.warning("🔄 Token expiré, re-authentification...")
                self._authenticate()
                return self.fetch_jobs(keyword, location, page, results_per_page)
            logger.error(f"❌ Erreur HTTP {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur : {e}")
            return []

    def _standardize(self, raw_jobs: list[dict]) -> list[dict]:
        """Standardise les données France Travail au format commun."""
        standardized = []
        for job in raw_jobs:
            salary = job.get("salaire", {})
            entreprise = job.get("entreprise", {})
            lieu = job.get("lieuTravail", {})

            salary_min = None
            salary_max = None
            if salary.get("libelle"):
                try:
                    parts = salary["libelle"].replace("€", "").strip().split("-")
                    if len(parts) == 2:
                        salary_min = float(parts[0].strip().replace(" ", ""))
                        salary_max = float(parts[1].strip().replace(" ", ""))
                    elif len(parts) == 1:
                        salary_min = float(parts[0].strip().replace(" ", ""))
                except (ValueError, IndexError):
                    pass

            contract_map = {
                "CDI": "CDI", "CDD": "CDD", "MIS": "Intérim",
                "SAI": "Saisonnier", "LIB": "Freelance",
            }

            standardized.append({
                "source": "france_travail",
                "external_id": job.get("id", ""),
                "title": job.get("intitule", ""),
                "company": entreprise.get("nom", ""),
                "description": job.get("description", ""),
                "location": lieu.get("libelle", ""),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "contract_type": contract_map.get(
                    job.get("typeContrat", ""), job.get("typeContrat", "")
                ),
                "url": job.get("origineOffre", {}).get("urlOrigine", ""),
                "created_at": job.get("dateCreation", ""),
                "collected_at": datetime.utcnow().isoformat(),
            })
        return standardized

    def collect_all(self, keywords: list[str] = None) -> list[dict]:
        """Lance la collecte complète."""
        from config.settings import SEARCH_KEYWORDS

        keywords = keywords or SEARCH_KEYWORDS
        all_jobs = []
        for keyword in keywords:
            jobs = self.fetch_jobs(keyword=keyword)
            all_jobs.extend(jobs)

        logger.info(f"📊 Total collecté (France Travail) : {len(all_jobs)} offres")
        return all_jobs
