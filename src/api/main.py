"""
API REST avec FastAPI — point d'accès programmatique aux données.
Lance avec : uvicorn src.api.main:app --reload
Docs auto : http://localhost:8000/docs
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Job Market Intelligence API",
    description="API d'analyse du marché de l'emploi Data & IA en France",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---
class JobResponse(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    experience_level: Optional[str] = None
    extracted_skills: Optional[dict] = None
    url: Optional[str] = None

    class Config:
        from_attributes = True


class MarketStats(BaseModel):
    total_offers: int
    avg_salary: Optional[float] = None
    top_skills: dict = {}
    category_distribution: dict = {}
    location_distribution: dict = {}
    experience_distribution: dict = {}


class SalaryPrediction(BaseModel):
    predicted_salary: int
    range_min: int
    range_max: int


# --- Endpoints ---
@app.get("/")
def root():
    return {
        "message": "🧠 AI Job Market Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/jobs", response_model=list[JobResponse])
def get_jobs(
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    location: Optional[str] = Query(None, description="Filtrer par ville"),
    experience: Optional[str] = Query(None, description="Filtrer par niveau"),
    contract: Optional[str] = Query(None, description="Filtrer par type de contrat"),
    min_salary: Optional[float] = Query(None, description="Salaire minimum"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
):
    """Récupère les offres avec filtres optionnels et pagination."""
    from src.database.db_manager import get_session
    from src.database.models import JobOffer

    with get_session() as session:
        query = session.query(JobOffer).filter(JobOffer.is_duplicate == False)

        if category:
            query = query.filter(JobOffer.category == category)
        if location:
            query = query.filter(JobOffer.location.contains(location))
        if experience:
            query = query.filter(JobOffer.experience_level == experience)
        if contract:
            query = query.filter(JobOffer.contract_type == contract)
        if min_salary:
            query = query.filter(JobOffer.salary_min >= min_salary)

        total = query.count()
        jobs = query.order_by(JobOffer.collected_at.desc()).offset(offset).limit(limit).all()

        return jobs


@app.get("/stats", response_model=MarketStats)
def get_market_stats():
    """Vue d'ensemble du marché — métriques agrégées."""
    from src.database.db_manager import get_session
    from src.database.models import JobOffer
    from sqlalchemy import func
    import json

    with get_session() as session:
        base_query = session.query(JobOffer).filter(JobOffer.is_duplicate == False)
        total = base_query.count()

        avg_sal = session.query(func.avg(JobOffer.salary_min)).filter(
            JobOffer.is_duplicate == False,
            JobOffer.salary_min != None,
        ).scalar()

        # Top categories
        categories = (
            session.query(JobOffer.category, func.count())
            .filter(JobOffer.is_duplicate == False, JobOffer.category != None)
            .group_by(JobOffer.category)
            .order_by(func.count().desc())
            .all()
        )

        # Top locations
        locations = (
            session.query(JobOffer.location, func.count())
            .filter(JobOffer.is_duplicate == False, JobOffer.location != None)
            .group_by(JobOffer.location)
            .order_by(func.count().desc())
            .limit(10)
            .all()
        )

        return MarketStats(
            total_offers=total,
            avg_salary=round(avg_sal, 2) if avg_sal else None,
            category_distribution={c: n for c, n in categories},
            location_distribution={l: n for l, n in locations},
        )


@app.get("/skills/trending")
def get_trending_skills(days: int = Query(30, description="Période en jours")):
    """Compétences en tendance sur les N derniers jours."""
    import pandas as pd
    from src.database.db_manager import get_all_jobs

    jobs = get_all_jobs()
    if not jobs:
        return {"skills": [], "period_days": days}

    df = pd.DataFrame(jobs)
    from src.analytics.trend_analyzer import TrendAnalyzer
    trends = TrendAnalyzer.compute_skill_trends(df, days=days)

    if trends.empty:
        return {"skills": [], "period_days": days}

    return {
        "skills": trends.head(30).to_dict(orient="records"),
        "period_days": days,
    }


@app.get("/predict/salary", response_model=SalaryPrediction)
def predict_salary(
    category: str = Query(..., description="Catégorie de poste"),
    location: str = Query(..., description="Ville"),
    experience: str = Query(..., description="Niveau d'expérience"),
    contract: str = Query("CDI", description="Type de contrat"),
    skill_count: int = Query(5, description="Nombre de compétences"),
):
    """Prédit le salaire pour un profil donné."""
    import os
    from config.settings import MODELS_DIR

    model_path = MODELS_DIR / "salary_predictor.joblib"
    if not os.path.exists(model_path):
        raise HTTPException(404, "Modèle de prédiction non encore entraîné")

    from src.analytics.salary_predictor import SalaryPredictor
    predictor = SalaryPredictor()
    predictor.load(str(model_path))

    result = predictor.predict(category, experience, location, contract, skill_count)
    return SalaryPrediction(**result)


@app.get("/categories")
def get_categories():
    """Liste des catégories de poste disponibles."""
    from src.nlp.classifier import JobClassifier
    return {"categories": JobClassifier.CATEGORIES}
