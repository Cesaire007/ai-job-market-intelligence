"""
Gestionnaire de base de données — CRUD operations.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from config.settings import DATABASE_URL
from .models import Base, JobOffer
import logging

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Crée toutes les tables si elles n'existent pas encore."""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Base de données initialisée")


@contextmanager
def get_session():
    """Context manager pour les sessions DB (garantit fermeture propre)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def insert_jobs(jobs: list[dict]) -> int:
    """Insère des offres en base, en évitant les doublons par source+external_id."""
    inserted = 0
    with get_session() as session:
        for job_data in jobs:
            exists = (
                session.query(JobOffer)
                .filter_by(
                    source=job_data.get("source"),
                    external_id=job_data.get("external_id"),
                )
                .first()
            )
            if not exists:
                job = JobOffer(**job_data)
                session.add(job)
                inserted += 1

    logger.info(f"💾 {inserted} nouvelles offres insérées en base")
    return inserted


def get_all_jobs(include_duplicates: bool = False) -> list[dict]:
    """Récupère toutes les offres."""
    with get_session() as session:
        query = session.query(JobOffer)
        if not include_duplicates:
            query = query.filter(JobOffer.is_duplicate == False)
        jobs = query.all()
        return [j.to_dict() for j in jobs]


def update_job(job_id: int, updates: dict):
    """Met à jour une offre existante."""
    with get_session() as session:
        job = session.query(JobOffer).filter_by(id=job_id).first()
        if job:
            for key, value in updates.items():
                setattr(job, key, value)


def get_jobs_without_skills() -> list:
    """Récupère les offres qui n'ont pas encore été analysées par le NLP."""
    with get_session() as session:
        jobs = (
            session.query(JobOffer)
            .filter(
                JobOffer.extracted_skills == None,
                JobOffer.is_duplicate == False,
            )
            .all()
        )
        return [(j.id, j.title, j.description) for j in jobs]


def get_job_count() -> int:
    """Nombre total d'offres non-dupliquées."""
    with get_session() as session:
        return session.query(JobOffer).filter(JobOffer.is_duplicate == False).count()
