"""
Clustering des offres — Machine Learning non supervisé.
Identifie des familles de postes Data/IA.
"""
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class JobClusterer:
    """Regroupe les offres en clusters basés sur leurs descriptions et features."""

    def __init__(self, n_components: int = 50):
        self.vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)
        self.n_components = n_components
        self.kmeans = None

    def prepare_features(self, jobs_df: pd.DataFrame) -> np.ndarray:
        """
        Prépare la matrice de features:
        1. TF-IDF sur descriptions
        2. One-hot encoding catégoriel
        3. PCA pour réduction de dimensionnalité
        """
        # Features textuelles
        text_features = self.vectorizer.fit_transform(
            jobs_df["description"].fillna("")
        ).toarray()

        # Features catégorielles
        cat_cols = []
        for col in ["contract_type", "location", "experience_level"]:
            if col in jobs_df.columns:
                cat_cols.append(col)
        if cat_cols:
            cat_features = pd.get_dummies(
                jobs_df[cat_cols].fillna("unknown"), drop_first=True
            ).values
            all_features = np.hstack([text_features, cat_features])
        else:
            all_features = text_features

        # Normalisation
        all_features = self.scaler.fit_transform(all_features)

        # PCA
        n_comp = min(self.n_components, all_features.shape[1], all_features.shape[0])
        if all_features.shape[1] > n_comp:
            self.pca = PCA(n_components=n_comp)
            all_features = self.pca.fit_transform(all_features)
            explained = sum(self.pca.explained_variance_ratio_) * 100
            logger.info(f"📐 PCA : {explained:.1f}% de variance en {n_comp} dimensions")

        return all_features

    def find_optimal_k(
        self, features: np.ndarray, k_range: range = range(3, 12)
    ) -> int:
        """Trouve le nombre optimal de clusters via Silhouette Score."""
        if len(features) < max(k_range):
            k_range = range(2, min(len(features), 12))

        scores = {}
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(features)
            score = silhouette_score(features, labels)
            scores[k] = score
            logger.info(f"  K={k} → Silhouette = {score:.3f}")

        best_k = max(scores, key=scores.get)
        logger.info(f"✅ Meilleur K = {best_k} (silhouette = {scores[best_k]:.3f})")
        return best_k

    def cluster(self, jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline complet de clustering."""
        if len(jobs_df) < 5:
            logger.warning("⚠️ Pas assez de données pour le clustering")
            jobs_df["cluster_id"] = 0
            return jobs_df

        features = self.prepare_features(jobs_df)
        optimal_k = self.find_optimal_k(features)

        self.kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        jobs_df["cluster_id"] = self.kmeans.fit_predict(features)

        # Log la distribution
        for cid in range(optimal_k):
            count = (jobs_df["cluster_id"] == cid).sum()
            logger.info(f"  Cluster {cid}: {count} offres")

        return jobs_df

    def get_cluster_profiles(self, jobs_df: pd.DataFrame) -> dict:
        """Analyse le profil de chaque cluster (top skills, salaire moyen)."""
        profiles = {}
        for cid in jobs_df["cluster_id"].unique():
            cluster_df = jobs_df[jobs_df["cluster_id"] == cid]

            # Top skills du cluster
            all_skills = []
            for skills in cluster_df["extracted_skills"].dropna():
                if isinstance(skills, dict):
                    all_skills.extend(skills.get("tech_skills", []))

            skill_counts = pd.Series(all_skills).value_counts().head(5)

            profiles[int(cid)] = {
                "size": len(cluster_df),
                "top_skills": skill_counts.to_dict() if len(skill_counts) > 0 else {},
                "avg_salary": cluster_df["salary_min"].dropna().mean(),
                "top_locations": cluster_df["location"].value_counts().head(3).to_dict(),
                "top_categories": cluster_df["category"].value_counts().head(3).to_dict(),
            }
        return profiles
