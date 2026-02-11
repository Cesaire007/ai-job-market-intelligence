"""
Pipeline principal — orchestrateur ETL.
Lance tout le pipeline : collecte → nettoyage → NLP → ML → stockage.

Usage:
    python -m src.pipeline
    python -m src.pipeline --skip-collect    # Saute la collecte
    python -m src.pipeline --skip-ml         # Saute le ML
"""
import logging
import argparse
import sys
import os
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
logger = logging.getLogger("pipeline")


def run_pipeline(skip_collect: bool = False, skip_ml: bool = False):
    """Exécute le pipeline complet."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("🚀 DÉMARRAGE DU PIPELINE AI JOB MARKET INTELLIGENCE")
    logger.info(f"   Date : {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # ═══════════════════════════════════════
    # ÉTAPE 0 : Initialisation DB
    # ═══════════════════════════════════════
    logger.info("\n📦 ÉTAPE 0 — Initialisation de la base de données")
    try:
        from src.database.db_manager import init_db
        init_db()
    except Exception as e:
        logger.error(f"❌ Erreur DB : {e}")
        logger.info("💡 Continuez en mode fichier (sans PostgreSQL)")

    all_jobs = []

    # ═══════════════════════════════════════
    # ÉTAPE 1 : Collecte
    # ═══════════════════════════════════════
    if not skip_collect:
        logger.info("\n📡 ÉTAPE 1 — Collecte des données")

        # Adzuna
        try:
            from src.collector.adzuna_client import AdzunaClient
            adzuna = AdzunaClient()
            adzuna_jobs = adzuna.collect_all()
            all_jobs.extend(adzuna_jobs)
            logger.info(f"   Adzuna : {len(adzuna_jobs)} offres")
        except Exception as e:
            logger.warning(f"⚠️ Adzuna non disponible : {e}")

        # France Travail
        try:
            from src.collector.francetravail_client import FranceTravailClient
            ft = FranceTravailClient()
            ft_jobs = ft.collect_all()
            all_jobs.extend(ft_jobs)
            logger.info(f"   France Travail : {len(ft_jobs)} offres")
        except Exception as e:
            logger.warning(f"⚠️ France Travail non disponible : {e}")

        logger.info(f"   📊 Total brut : {len(all_jobs)} offres")
    else:
        logger.info("\n⏭️ Collecte ignorée (--skip-collect)")

    # Si pas de nouvelles données, charge depuis la DB
    if not all_jobs:
        logger.info("   Chargement des données existantes depuis la DB...")
        try:
            from src.database.db_manager import get_all_jobs
            existing = get_all_jobs(include_duplicates=True)
            all_jobs = existing
            logger.info(f"   {len(all_jobs)} offres chargées depuis la DB")
        except Exception:
            logger.warning("⚠️ Aucune donnée disponible")
            return

    # ═══════════════════════════════════════
    # ÉTAPE 2 : Nettoyage
    # ═══════════════════════════════════════
    logger.info("\n🧹 ÉTAPE 2 — Nettoyage des données")
    from src.processing.cleaner import JobCleaner
    cleaner = JobCleaner()
    cleaned_jobs = cleaner.clean_batch(all_jobs)

    # ═══════════════════════════════════════
    # ÉTAPE 3 : Déduplication
    # ═══════════════════════════════════════
    logger.info("\n🔍 ÉTAPE 3 — Détection des doublons")
    from src.processing.deduplicator import Deduplicator
    dedup = Deduplicator(similarity_threshold=0.85)
    cleaned_jobs = dedup.mark_duplicates(cleaned_jobs)
    n_unique = sum(1 for j in cleaned_jobs if not j.get("is_duplicate", False))
    logger.info(f"   {n_unique} offres uniques conservées")

    # ═══════════════════════════════════════
    # ÉTAPE 4 : NLP — Extraction de compétences
    # ═══════════════════════════════════════
    logger.info("\n🧠 ÉTAPE 4 — Extraction des compétences (NLP)")
    from src.nlp.skill_extractor import SkillExtractor
    extractor = SkillExtractor(use_model=False)  # Rule-based par défaut

    for job in cleaned_jobs:
        if not job.get("is_duplicate", False):
            desc = job.get("description", "")
            title = job.get("title", "")
            skills = extractor.extract(f"{title} {desc}")
            job["extracted_skills"] = skills

    # ═══════════════════════════════════════
    # ÉTAPE 5 : NLP — Classification
    # ═══════════════════════════════════════
    logger.info("\n🏷️ ÉTAPE 5 — Classification des offres")
    from src.nlp.classifier import JobClassifier
    classifier = JobClassifier(use_model=False)  # Rule-based par défaut

    for job in cleaned_jobs:
        if not job.get("is_duplicate", False):
            result = classifier.classify(job.get("title", ""), job.get("description", ""))
            job["category"] = result["category"]

    # ═══════════════════════════════════════
    # ÉTAPE 6 : Résumé automatique
    # ═══════════════════════════════════════
    logger.info("\n📝 ÉTAPE 6 — Résumé des descriptions")
    from src.nlp.summarizer import JobSummarizer
    summarizer = JobSummarizer()

    for job in cleaned_jobs:
        if not job.get("is_duplicate", False):
            job["summary"] = summarizer.summarize(job.get("description", ""))

    # ═══════════════════════════════════════
    # ÉTAPE 7 : Stockage en base
    # ═══════════════════════════════════════
    logger.info("\n💾 ÉTAPE 7 — Stockage en base de données")
    try:
        from src.database.db_manager import insert_jobs
        inserted = insert_jobs(cleaned_jobs)
        logger.info(f"   {inserted} nouvelles offres insérées")
    except Exception as e:
        logger.warning(f"⚠️ Stockage DB échoué : {e}")
        # Sauvegarde en JSON comme fallback
        import json
        fallback_path = os.path.join("data", "processed", f"jobs_{datetime.now().strftime('%Y%m%d')}.json")
        os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
        with open(fallback_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_jobs, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"   💾 Sauvegardé en JSON : {fallback_path}")

    # ═══════════════════════════════════════
    # ÉTAPE 8 : Machine Learning (optionnel)
    # ═══════════════════════════════════════
    if not skip_ml:
        import pandas as pd
        df = pd.DataFrame([j for j in cleaned_jobs if not j.get("is_duplicate", False)])

        if len(df) >= 30:
            # Clustering
            logger.info("\n📐 ÉTAPE 8a — Clustering des offres")
            try:
                from src.analytics.clustering import JobClusterer
                clusterer = JobClusterer()
                df = clusterer.cluster(df)
                profiles = clusterer.get_cluster_profiles(df)
                logger.info(f"   {len(profiles)} clusters identifiés")
            except Exception as e:
                logger.warning(f"⚠️ Clustering échoué : {e}")

            # Prédiction salariale
            logger.info("\n💰 ÉTAPE 8b — Entraînement du prédicteur salarial")
            try:
                from src.analytics.salary_predictor import SalaryPredictor
                predictor = SalaryPredictor()
                metrics = predictor.train(df)
                if "error" not in metrics:
                    os.makedirs("models", exist_ok=True)
                    predictor.save("models/salary_predictor.joblib")
                    logger.info(f"   Modèle sauvegardé")
                else:
                    logger.warning(f"   {metrics['error']}")
            except Exception as e:
                logger.warning(f"⚠️ Prédiction salariale échouée : {e}")

            # Snapshot marché
            logger.info("\n📸 ÉTAPE 8c — Snapshot du marché")
            try:
                from src.analytics.trend_analyzer import TrendAnalyzer
                snapshot = TrendAnalyzer.compute_market_snapshot(df)
                logger.info(f"   Total offres : {snapshot['total_offers']}")
                logger.info(f"   Salaire moyen : {snapshot['avg_salary']}€")
                top_3 = list(snapshot.get("top_skills", {}).items())[:3]
                logger.info(f"   Top 3 skills : {top_3}")
            except Exception as e:
                logger.warning(f"⚠️ Snapshot échoué : {e}")
        else:
            logger.info("\n⏭️ ML ignoré (pas assez de données)")
    else:
        logger.info("\n⏭️ ML ignoré (--skip-ml)")

    # ═══════════════════════════════════════
    # TERMINÉ
    # ═══════════════════════════════════════
    duration = (datetime.now() - start).total_seconds()
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ PIPELINE TERMINÉ en {duration:.1f}s")
    logger.info(f"   Offres traitées : {len(cleaned_jobs)}")
    logger.info(f"   Offres uniques : {n_unique}")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Job Market Intelligence Pipeline")
    parser.add_argument("--skip-collect", action="store_true", help="Skip data collection")
    parser.add_argument("--skip-ml", action="store_true", help="Skip ML training")
    args = parser.parse_args()

    run_pipeline(skip_collect=args.skip_collect, skip_ml=args.skip_ml)
