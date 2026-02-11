# 🧠 AI Job Market Intelligence — France

> Plateforme d'analyse automatisée du marché de l'emploi Data & IA en France.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-✓-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Objectif

Analyser automatiquement le marché de l'emploi Data & IA en France :
- **Collecte** quotidienne des offres via APIs (Adzuna, France Travail)
- **NLP** : extraction automatique des compétences avec CamemBERT
- **ML** : clustering des postes et prédiction salariale
- **Dashboard** interactif pour explorer les résultats
- **API REST** pour accéder aux données programmatiquement

## 📊 Fonctionnalités

| Feature | Description |
|---|---|
| 🔄 Pipeline ETL automatisé | Collecte, nettoie et enrichit les données quotidiennement |
| 🧠 NLP français | Extraction de compétences (rule-based + CamemBERT NER) |
| 🏷️ Classification zero-shot | Catégorisation automatique des offres |
| 📈 Machine Learning | Clustering K-Means + prédiction salariale (RF / XGBoost) |
| 🖥️ Dashboard Streamlit | Visualisation interactive des tendances |
| 🚀 API REST FastAPI | Endpoints filtrage, stats, prédiction (Swagger auto) |
| 🐳 Docker | Déploiement conteneurisé one-click |
| ⚙️ GitHub Actions | CI/CD + pipeline quotidien automatisé |

## 🏗️ Architecture

```
ai-job-market-intelligence/
├── src/
│   ├── collector/          # APIs Adzuna & France Travail
│   ├── processing/         # Nettoyage, déduplication, normalisation
│   ├── nlp/               # Extraction compétences, classification, résumé
│   ├── analytics/         # Clustering, prédiction salariale, tendances
│   ├── database/          # Modèles SQLAlchemy & CRUD PostgreSQL
│   ├── api/               # FastAPI REST endpoints
│   └── pipeline.py        # Orchestrateur ETL principal
├── dashboard/             # Streamlit interactive dashboard
├── tests/                 # pytest unit tests
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/     # CI/CD + daily automation
```

## 🚀 Quick Start

### Option 1 : Docker (recommandé)
```bash
# Clone
git clone https://github.com/[ton-user]/ai-job-market-intelligence.git
cd ai-job-market-intelligence

# Configure
cp .env.example .env
# Remplis tes clés API dans .env

# Lance tout
docker-compose up -d

# Dashboard → http://localhost:8501
# API docs  → http://localhost:8000/docs
```

### Option 2 : Installation locale
```bash
# Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Remplis tes clés API

# Lance le pipeline
python -m src.pipeline

# Lance le dashboard
streamlit run dashboard/app.py

# Lance l'API
uvicorn src.api.main:app --reload
```

### Option 3 : Lancer le pipeline manuellement
```bash
# Pipeline complet
python -m src.pipeline

# Sans collecte (réutilise les données existantes)
python -m src.pipeline --skip-collect

# Sans ML
python -m src.pipeline --skip-ml
```

## 🔌 APIs utilisées

| API | Description | Inscription |
|-----|-------------|-------------|
| [Adzuna](https://developer.adzuna.com/) | Agrégateur international d'offres | Gratuit (5000 req/mois) |
| [France Travail](https://francetravail.io/data/api) | Offres officielles France | Gratuit (OAuth2) |

## 🛠️ Stack Technique

| Catégorie | Outils |
|-----------|--------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, PostgreSQL |
| **NLP** | Hugging Face Transformers, CamemBERT, spaCy |
| **ML** | Scikit-learn (K-Means, Random Forest), XGBoost |
| **Frontend** | Streamlit, Plotly |
| **DevOps** | Docker, docker-compose, GitHub Actions |
| **Quality** | pytest, black, flake8 |

## 🧪 Tests

```bash
# Lancer tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ -v --cov=src
```

## 📈 API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Info API |
| GET | `/health` | Health check |
| GET | `/jobs` | Liste des offres (filtres, pagination) |
| GET | `/stats` | Statistiques du marché |
| GET | `/skills/trending` | Compétences en tendance |
| GET | `/predict/salary` | Prédiction salariale |
| GET | `/categories` | Liste des catégories |

Documentation Swagger interactive : `http://localhost:8000/docs`

## 🎯 Compétences démontrées

| Compétence | Module |
|------------|--------|
| Python avancé (OOP, logging, config) | Tout le projet |
| API REST (consommation + création) | `collector/` + `api/` |
| SQL + ORM (SQLAlchemy) | `database/` |
| Nettoyage de données | `processing/` |
| NLP (NER, classification, résumé) | `nlp/` |
| ML supervisé (régression) | `analytics/salary_predictor` |
| ML non supervisé (clustering) | `analytics/clustering` |
| Feature Engineering | `processing/` + `analytics/` |
| Data Visualization (Plotly, Streamlit) | `dashboard/` |
| Docker & docker-compose | DevOps files |
| CI/CD (GitHub Actions) | `.github/workflows/` |
| Git professionnel | Workflow complet |
| Tests unitaires (pytest) | `tests/` |

## 📬 Contact

**Florian** — Étudiant ingénieur IA & Data Science @ ESIEA

- 🐙 GitHub : Cesaire007

---

*Projet réalisé dans le cadre de ma formation en ingénierie IA & Data Science.*
*Données collectées via APIs publiques à des fins d'analyse et d'apprentissage.*
