"""
Configuration centralisée du projet AI Job Market Intelligence.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

# APIs
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
FRANCE_TRAVAIL_CLIENT_ID = os.getenv("FRANCE_TRAVAIL_CLIENT_ID")
FRANCE_TRAVAIL_CLIENT_SECRET = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/job_intelligence"
)

# NLP
CAMEMBERT_NER_MODEL = "Jean-Baptiste/camembert-ner"
ZERO_SHOT_MODEL = "joeddav/xlm-roberta-large-xnli"

# Collecte
SEARCH_KEYWORDS = [
    "data scientist", "data engineer", "data analyst",
    "machine learning engineer", "MLOps", "NLP engineer",
    "intelligence artificielle", "deep learning",
    "alternance data", "ingénieur données", "analyste données",
]

LOCATIONS = [
    "Paris", "Lyon", "Toulouse", "Bordeaux",
    "Nantes", "Lille", "Marseille", "Strasbourg",
]

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
