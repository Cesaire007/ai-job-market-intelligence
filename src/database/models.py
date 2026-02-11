"""
Modèles de données — SQLAlchemy ORM.
Chaque classe = une table dans PostgreSQL.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, JSON,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class JobOffer(Base):
    """Table principale : une ligne = une offre d'emploi."""

    __tablename__ = "job_offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    external_id = Column(String(100))
    title = Column(String(500), nullable=False)
    company = Column(String(300))
    description = Column(Text)
    location = Column(String(200))
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    contract_type = Column(String(50))
    url = Column(String(1000))
    created_at = Column(DateTime)
    collected_at = Column(DateTime, server_default=func.now())

    # Champs enrichis par le NLP
    extracted_skills = Column(JSON, nullable=True)
    category = Column(String(100), nullable=True)
    experience_level = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    is_duplicate = Column(Boolean, default=False)

    def __repr__(self):
        return f"<JobOffer {self.title} @ {self.company}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "contract_type": self.contract_type,
            "url": self.url,
            "extracted_skills": self.extracted_skills,
            "category": self.category,
            "experience_level": self.experience_level,
            "cluster_id": self.cluster_id,
            "is_duplicate": self.is_duplicate,
        }


class SkillTrend(Base):
    """Évolution des compétences demandées dans le temps."""

    __tablename__ = "skill_trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(100), nullable=False)
    date = Column(DateTime, nullable=False)
    count = Column(Integer, default=0)
    avg_salary = Column(Float, nullable=True)
    top_locations = Column(JSON, nullable=True)


class MarketSnapshot(Base):
    """Photo du marché à un instant T."""

    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    total_offers = Column(Integer)
    avg_salary = Column(Float)
    top_skills = Column(JSON)
    category_distribution = Column(JSON)
    location_distribution = Column(JSON)
