"""
Prédiction salariale — ML supervisé.
Baseline Random Forest, puis XGBoost pour optimiser.
"""
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
import pandas as pd
import joblib
import logging

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("⚠️ XGBoost non installé, utilisation de Random Forest uniquement")


class SalaryPredictor:
    """Prédit le salaire d'une offre à partir de ses caractéristiques."""

    def __init__(self):
        self.label_encoders = {}
        self.model = None
        self.feature_names = None
        self.metrics = {}

    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """Prépare features et target pour la régression."""
        df_salary = df.dropna(subset=["salary_min"]).copy()

        if len(df_salary) < 30:
            logger.warning("⚠️ Pas assez de données salariales (<30)")
            return None, None

        # Target: salaire moyen
        df_salary["salary_avg"] = (
            df_salary["salary_min"]
            + df_salary["salary_max"].fillna(df_salary["salary_min"])
        ) / 2
        y = df_salary["salary_avg"].values

        # Features catégorielles → encodage
        cat_columns = ["category", "experience_level", "location", "contract_type"]
        for col in cat_columns:
            if col in df_salary.columns:
                le = LabelEncoder()
                df_salary[f"{col}_enc"] = le.fit_transform(
                    df_salary[col].fillna("unknown").astype(str)
                )
                self.label_encoders[col] = le

        # Feature: nombre de compétences
        df_salary["skill_count"] = df_salary["extracted_skills"].apply(
            lambda x: len(x.get("tech_skills", [])) if isinstance(x, dict) else 0
        )

        feature_cols = [f"{col}_enc" for col in cat_columns if col in df_salary.columns]
        feature_cols.append("skill_count")

        self.feature_names = feature_cols
        X = df_salary[feature_cols].values

        return X, y

    def train(self, df: pd.DataFrame) -> dict:
        """Entraîne et évalue les modèles de prédiction salariale."""
        X, y = self.prepare_features(df)
        if X is None:
            return {"error": "Données insuffisantes"}

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        results = {}

        # Modèle 1: Random Forest (baseline)
        rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_mae = mean_absolute_error(y_test, rf_pred)
        rf_r2 = r2_score(y_test, rf_pred)
        results["random_forest"] = {"MAE": round(rf_mae), "R2": round(rf_r2, 3)}

        # Validation croisée RF
        cv_scores = cross_val_score(rf, X, y, cv=5, scoring="r2")
        results["random_forest"]["CV_R2_mean"] = round(cv_scores.mean(), 3)

        best_model = rf
        best_name = "Random Forest"

        # Modèle 2: XGBoost (si disponible)
        if HAS_XGBOOST:
            xgb_model = xgb.XGBRegressor(
                n_estimators=300, max_depth=6,
                learning_rate=0.1, random_state=42,
            )
            xgb_model.fit(X_train, y_train)
            xgb_pred = xgb_model.predict(X_test)
            xgb_mae = mean_absolute_error(y_test, xgb_pred)
            xgb_r2 = r2_score(y_test, xgb_pred)
            results["xgboost"] = {"MAE": round(xgb_mae), "R2": round(xgb_r2, 3)}

            if xgb_r2 > rf_r2:
                best_model = xgb_model
                best_name = "XGBoost"

        self.model = best_model
        results["best_model"] = best_name
        results["training_samples"] = len(X_train)
        results["test_samples"] = len(X_test)
        self.metrics = results

        logger.info(f"🏆 Meilleur modèle : {best_name}")
        logger.info(f"   MAE = {results[best_name.lower().replace(' ', '_')]['MAE']}€")
        logger.info(f"   R² = {results[best_name.lower().replace(' ', '_')]['R2']}")

        return results

    def predict(self, category: str, experience: str, location: str,
                contract: str, skill_count: int) -> dict:
        """Prédit le salaire pour un profil donné."""
        if not self.model:
            raise ValueError("Modèle non entraîné. Appelle train() d'abord.")

        features = []
        for col, value in [
            ("category", category), ("experience_level", experience),
            ("location", location), ("contract_type", contract),
        ]:
            if col in self.label_encoders:
                le = self.label_encoders[col]
                if value in le.classes_:
                    features.append(le.transform([value])[0])
                else:
                    features.append(0)
            else:
                features.append(0)
        features.append(skill_count)

        prediction = self.model.predict([features])[0]
        return {
            "predicted_salary": round(prediction),
            "range_min": round(prediction * 0.9),
            "range_max": round(prediction * 1.1),
        }

    def save(self, path: str = "models/salary_predictor.joblib"):
        """Sauvegarde le modèle entraîné."""
        joblib.dump(
            {"model": self.model, "encoders": self.label_encoders,
             "features": self.feature_names, "metrics": self.metrics},
            path,
        )
        logger.info(f"💾 Modèle sauvegardé : {path}")

    def load(self, path: str = "models/salary_predictor.joblib"):
        """Charge un modèle pré-entraîné."""
        data = joblib.load(path)
        self.model = data["model"]
        self.label_encoders = data["encoders"]
        self.feature_names = data["features"]
        self.metrics = data.get("metrics", {})
        logger.info(f"📂 Modèle chargé : {path}")
