"""
Dashboard Streamlit — Data Storytelling interactif.
Lance avec : streamlit run dashboard/app.py
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import os
import sys

# Ajoute le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Config ---
st.set_page_config(
    page_title="AI Job Market Intelligence 🇫🇷",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS custom ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# --- Data Loading ---
@st.cache_data(ttl=3600)
def load_data():
    """Charge les données depuis la base ou un fichier sample."""
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "samples", "sample_jobs.json",
    )

    # Essaie d'abord la base de données
    try:
        from config.settings import DATABASE_URL
        from sqlalchemy import create_engine
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql(
            "SELECT * FROM job_offers WHERE is_duplicate = false", engine
        )
        if len(df) > 0:
            return df
    except Exception:
        pass

    # Fallback: fichier sample
    if os.path.exists(sample_path):
        with open(sample_path) as f:
            data = json.load(f)
        return pd.DataFrame(data)

    # Données de démo
    return _generate_demo_data()


def _generate_demo_data():
    """Génère des données de démonstration."""
    import random
    random.seed(42)

    categories = [
        "Data Engineer", "Data Scientist", "Data Analyst",
        "Machine Learning Engineer", "MLOps Engineer", "NLP Engineer",
    ]
    locations = ["Paris", "Lyon", "Toulouse", "Bordeaux", "Nantes", "Lille", "Full Remote"]
    contracts = ["CDI", "CDD", "Alternance", "Stage"]
    levels = ["alternance", "junior", "confirmé", "senior"]
    companies = [
        "TechCorp", "DataViz SAS", "AI Factory", "CloudNext", "Generali",
        "Boursorama", "BNP Paribas", "Thales", "Capgemini", "Accenture",
        "Société Générale", "Orange", "EDF", "Samsung", "Dassault",
    ]
    tech_skills = [
        "python", "sql", "spark", "aws", "docker", "kubernetes", "tensorflow",
        "pytorch", "pandas", "scikit-learn", "airflow", "kafka", "postgresql",
        "power bi", "tableau", "git", "fastapi", "mlflow", "dbt", "snowflake",
    ]

    jobs = []
    for i in range(500):
        cat = random.choice(categories)
        level = random.choice(levels)
        loc = random.choice(locations)

        base_salary = {
            "alternance": 15000, "junior": 35000,
            "confirmé": 48000, "senior": 65000,
        }[level]
        if loc == "Paris":
            base_salary *= 1.15
        salary = base_salary + random.randint(-5000, 8000)

        n_skills = random.randint(3, 10)
        selected_skills = random.sample(tech_skills, min(n_skills, len(tech_skills)))

        jobs.append({
            "id": i + 1,
            "title": f"{cat} {level.title()}",
            "company": random.choice(companies),
            "location": loc,
            "category": cat,
            "salary_min": round(salary),
            "salary_max": round(salary * 1.15),
            "contract_type": random.choice(contracts),
            "experience_level": level,
            "extracted_skills": {"tech_skills": selected_skills, "soft_skills": []},
            "cluster_id": random.randint(0, 5),
            "collected_at": pd.Timestamp("2025-01-01") + pd.Timedelta(days=random.randint(0, 60)),
        })
    return pd.DataFrame(jobs)


# === MAIN DASHBOARD ===
df = load_data()

# --- HEADER ---
st.markdown('<p class="main-header">🧠 AI Job Market Intelligence — France</p>', unsafe_allow_html=True)
st.markdown("*Analyse en temps réel du marché de l'emploi Data & IA*")
st.markdown("---")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Offres analysées", f"{len(df):,}")
with col2:
    avg_sal = df["salary_min"].dropna().mean()
    st.metric("💰 Salaire moyen", f"{avg_sal:,.0f} €" if pd.notna(avg_sal) else "N/A")
with col3:
    st.metric("🏢 Entreprises", f"{df['company'].nunique():,}")
with col4:
    n_alt = len(df[df.get("experience_level", "") == "alternance"]) if "experience_level" in df.columns else 0
    st.metric("🎓 Alternances", f"{n_alt:,}")

st.markdown("---")

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.header("🔍 Filtres")

    if "category" in df.columns:
        cats = df["category"].dropna().unique().tolist()
        selected_categories = st.multiselect("Catégorie", options=cats, default=cats[:5])
    else:
        selected_categories = []

    if "location" in df.columns:
        locs = df["location"].value_counts().head(10).index.tolist()
        selected_locations = st.multiselect("Localisation", options=locs)
    else:
        selected_locations = []

    if "experience_level" in df.columns:
        selected_experience = st.multiselect(
            "Niveau d'expérience",
            options=["alternance", "stage", "junior", "confirmé", "senior"],
        )
    else:
        selected_experience = []

    salary_range = st.slider("Fourchette salariale (€)", 15000, 100000, (20000, 70000))

# Apply filters
df_f = df.copy()
if selected_categories and "category" in df_f.columns:
    df_f = df_f[df_f["category"].isin(selected_categories)]
if selected_locations and "location" in df_f.columns:
    df_f = df_f[df_f["location"].isin(selected_locations)]
if selected_experience and "experience_level" in df_f.columns:
    df_f = df_f[df_f["experience_level"].isin(selected_experience)]
if "salary_min" in df_f.columns:
    mask = df_f["salary_min"].isna() | (
        (df_f["salary_min"] >= salary_range[0]) & (df_f["salary_min"] <= salary_range[1])
    )
    df_f = df_f[mask]

st.markdown(f"**{len(df_f)} offres** correspondent aux filtres")

# --- CHART 1: Top Skills ---
st.subheader("🔥 Compétences les plus demandées")

all_skills = []
if "extracted_skills" in df_f.columns:
    for skills in df_f["extracted_skills"].dropna():
        if isinstance(skills, dict):
            all_skills.extend(skills.get("tech_skills", []))
        elif isinstance(skills, str):
            try:
                parsed = json.loads(skills)
                all_skills.extend(parsed.get("tech_skills", []))
            except (json.JSONDecodeError, AttributeError):
                pass

if all_skills:
    skills_series = pd.Series(all_skills).value_counts().head(20)
    fig_skills = px.bar(
        x=skills_series.values, y=skills_series.index, orientation="h",
        title="Top 20 des compétences techniques demandées",
        labels={"x": "Nombre d'offres", "y": "Compétence"},
        color=skills_series.values, color_continuous_scale="viridis",
    )
    fig_skills.update_layout(yaxis=dict(autorange="reversed"), height=500, showlegend=False)
    st.plotly_chart(fig_skills, use_container_width=True)
else:
    st.info("Pas de données de compétences disponibles")

# --- CHART 2: Salary by Category ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("💰 Salaires par catégorie")
    if "salary_min" in df_f.columns and "category" in df_f.columns:
        df_sal = df_f.dropna(subset=["salary_min", "category"])
        if not df_sal.empty:
            fig_sal = px.box(
                df_sal, x="category", y="salary_min",
                color="experience_level" if "experience_level" in df_sal.columns else None,
                title="Distribution des salaires",
                labels={"salary_min": "Salaire annuel brut (€)", "category": ""},
            )
            fig_sal.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig_sal, use_container_width=True)

with col_b:
    st.subheader("🗺️ Répartition géographique")
    if "location" in df_f.columns:
        loc_counts = df_f["location"].value_counts().head(10)
        fig_geo = px.pie(
            values=loc_counts.values, names=loc_counts.index,
            title="Répartition par ville", hole=0.4,
        )
        fig_geo.update_layout(height=400)
        st.plotly_chart(fig_geo, use_container_width=True)

# --- CHART 3: Category Distribution ---
st.subheader("📊 Répartition par catégorie de poste")
if "category" in df_f.columns:
    cat_counts = df_f["category"].value_counts()
    fig_cat = px.bar(
        x=cat_counts.index, y=cat_counts.values,
        title="Nombre d'offres par catégorie",
        labels={"x": "Catégorie", "y": "Nombre d'offres"},
        color=cat_counts.values, color_continuous_scale="blues",
    )
    fig_cat.update_layout(showlegend=False)
    st.plotly_chart(fig_cat, use_container_width=True)

# --- CHART 4: Timeline ---
st.subheader("📈 Évolution temporelle")
if "collected_at" in df_f.columns:
    df_f["date"] = pd.to_datetime(df_f["collected_at"], errors="coerce").dt.date
    if df_f["date"].notna().any():
        daily = df_f.dropna(subset=["date"]).groupby("date").size().reset_index(name="count")
        fig_trend = px.line(
            daily, x="date", y="count",
            title="Nouvelles offres collectées par jour",
            labels={"date": "Date", "count": "Nombre d'offres"},
        )
        st.plotly_chart(fig_trend, use_container_width=True)

# --- SALARY PREDICTOR ---
st.markdown("---")
st.subheader("🔮 Prédicteur de salaire")
st.markdown("*Estime le salaire en fonction du profil de poste*")

pc1, pc2 = st.columns(2)
with pc1:
    pred_category = st.selectbox("Catégorie", [
        "Data Engineer", "Data Scientist", "Data Analyst",
        "Machine Learning Engineer", "MLOps Engineer", "NLP Engineer",
    ])
    pred_location = st.selectbox("Localisation", [
        "Paris", "Lyon", "Toulouse", "Bordeaux", "Nantes", "Full Remote",
    ])
with pc2:
    pred_experience = st.selectbox("Expérience", [
        "alternance", "junior", "confirmé", "senior",
    ])
    pred_skills = st.number_input("Nombre de compétences", 1, 20, 5)

if st.button("🎯 Prédire le salaire"):
    # Estimation basée sur les données filtrées
    mask = pd.Series([True] * len(df))
    if "category" in df.columns:
        mask &= df["category"] == pred_category
    if "experience_level" in df.columns:
        mask &= df["experience_level"] == pred_experience

    matching = df[mask]["salary_min"].dropna()
    if len(matching) > 5:
        avg = matching.mean()
        std = matching.std()
        low = max(15000, avg - std)
        high = avg + std
        st.success(f"💰 Salaire estimé : **{low:,.0f} € — {high:,.0f} €** annuel brut")
        st.info(f"*Estimation basée sur {len(matching)} offres similaires*")
    else:
        st.warning("Pas assez de données pour une estimation fiable")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "📊 **AI Job Market Intelligence** | "
    "Données collectées via Adzuna & France Travail | "
    "Mis à jour quotidiennement | "
    "Par **Florian** — ESIEA 2026"
)
