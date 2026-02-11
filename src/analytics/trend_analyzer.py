"""
Analyse des tendances temporelles du marché Data/IA.
"""
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyse l'évolution du marché dans le temps."""

    @staticmethod
    def compute_skill_trends(jobs_df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
        """Calcule les skills en tendance sur les N derniers jours."""
        if "collected_at" not in jobs_df.columns:
            return pd.DataFrame()

        jobs_df["collected_at"] = pd.to_datetime(jobs_df["collected_at"])
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = jobs_df[jobs_df["collected_at"] >= cutoff]

        all_skills = []
        for _, row in recent.iterrows():
            skills = row.get("extracted_skills")
            if isinstance(skills, dict):
                for skill in skills.get("tech_skills", []):
                    all_skills.append({
                        "skill": skill,
                        "date": row["collected_at"].date(),
                        "salary": row.get("salary_min"),
                        "location": row.get("location"),
                    })

        if not all_skills:
            return pd.DataFrame()

        skills_df = pd.DataFrame(all_skills)
        trends = (
            skills_df.groupby("skill")
            .agg(
                count=("skill", "size"),
                avg_salary=("salary", "mean"),
                top_location=("location", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "N/A"),
            )
            .sort_values("count", ascending=False)
            .reset_index()
        )
        return trends

    @staticmethod
    def compute_market_snapshot(jobs_df: pd.DataFrame) -> dict:
        """Génère un snapshot du marché actuel."""
        non_dup = jobs_df[jobs_df.get("is_duplicate", False) == False] if "is_duplicate" in jobs_df.columns else jobs_df

        # Top skills
        all_skills = []
        for skills in non_dup["extracted_skills"].dropna():
            if isinstance(skills, dict):
                all_skills.extend(skills.get("tech_skills", []))
        top_skills = pd.Series(all_skills).value_counts().head(20).to_dict()

        return {
            "date": datetime.utcnow().isoformat(),
            "total_offers": len(non_dup),
            "avg_salary": round(non_dup["salary_min"].dropna().mean(), 2)
            if not non_dup["salary_min"].dropna().empty else None,
            "top_skills": top_skills,
            "category_distribution": non_dup["category"].value_counts().to_dict()
            if "category" in non_dup.columns else {},
            "location_distribution": non_dup["location"].value_counts().head(10).to_dict()
            if "location" in non_dup.columns else {},
            "contract_distribution": non_dup["contract_type"].value_counts().to_dict()
            if "contract_type" in non_dup.columns else {},
            "experience_distribution": non_dup["experience_level"].value_counts().to_dict()
            if "experience_level" in non_dup.columns else {},
        }
