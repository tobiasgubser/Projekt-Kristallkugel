import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
from app_utils import (
    normalize, compute_peer_deltas, compute_performance, 
    forecast_series, compute_event_study,get_latest_data
)
from tabs.dashboard import render_dashboard_tab
from tabs.finance import render_finance_tab
from tabs.correlations import render_corr_tab
from tabs.news import render_news_tab
from tabs.forecast import render_forecast_tab
from tabs.event_studies import render_event_tab
from tabs.raw_data_intf import render_raw_data_tab

st.set_page_config(
    page_title="Kristallkugel",
    page_icon="🔮",
    layout="wide",
)

# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
@st.cache_resource
def load_df_all():
    df = pd.read_csv("data/df_all.csv", parse_dates=["date"])
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df['date'] = df['date'].dt.tz_convert('Europe/Zurich')
    df = df.set_index("date")
    return df

df_all = load_df_all()

def get_random_forest():
    model    = joblib.load('data/kristallkugel_model.pkl')
    features = joblib.load('data/kristallkugel_features.pkl')

    return model, features

model, features = get_random_forest()

@st.cache_resource
def load_df_news():
    df = pd.read_csv("data/df_news.tsv", sep="\t", parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["date"] = df["date"].dt.tz_convert("Europe/Zurich")
    df = df.set_index("date")
    return df

df_news = load_df_news()

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
st.sidebar.header("Settings")

handelstage = df_all.index.date

stichtag = st.sidebar.date_input(
    "Stichtag",
    value=df_all.index.max().date(),
    min_value=df_all.index.min().date(),
    max_value=df_all.index.max().date(),
)
if stichtag not in handelstage:
    st.warning("Wähle bitte einen SPI Handelstag aus (keine Wochenenden / Feiertage).")
    st.stop()

selected_cols = st.sidebar.multiselect(
    "Select variables",
    options=["SPI", "Banken", "Finanzen", "Gesundheit", "Lebensmittel", "Versicherungen"],
    default=["SPI"],
)
if not selected_cols:
    st.warning("Please select at least one variable.")
    st.stop()

norm = normalize(df_all[selected_cols])
deltas = compute_peer_deltas(norm)

selected_var = st.sidebar.selectbox(
    "Variable for peer comparison",
    options=selected_cols,
)

sp500_pct, vix_close, gold_pct, brent_pct, wti_pct = get_latest_data()

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
st.title("🔮 Kristallkugel")
tab_dashboard, tab_finance, tab_corr, tab_news, tab_event, tab_forecast, tab_raw = st.tabs(
    ["📊 Dashboard", "🏦 Finanzdaten", "🔗 Korrelationen", "📰 News", "📉 Event-Studien", "🔮 Forecast", "📄 Raw Data"]
)

# ---------------------------------------------------------
# Render Tabs
# ---------------------------------------------------------
with tab_dashboard:
        render_dashboard_tab(df_all, stichtag, selected_cols, norm, deltas, selected_var, compute_performance, handelstage)

with tab_finance:
    render_finance_tab(df_all, stichtag, norm, deltas, compute_performance, handelstage)

with tab_corr:
        render_corr_tab(df_all, selected_cols)

with tab_news:
        render_news_tab(df_news, stichtag)

with tab_event:
        render_event_tab(df_all, df_news, selected_cols, handelstage, compute_event_study, stichtag)

with tab_forecast:
        render_forecast_tab(sp500_pct, vix_close, gold_pct, brent_pct, wti_pct,model, features)

with tab_raw:
        render_raw_data_tab(df_all, stichtag)
