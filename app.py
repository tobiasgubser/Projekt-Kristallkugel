import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import datetime
from app_utils import normalize, compute_peer_deltas, compute_performance, get_latest_data
from tabs.dashboard import render_dashboard_tab
from tabs.finance import render_finance_tab
from tabs.news import render_news_tab
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
    "Stichtag Historische Daten",
    value=df_all.index.max().date(),
    min_value=df_all.index.min().date(),
    max_value=df_all.index.max().date(),
)
if stichtag not in handelstage:
    st.warning("Wähle bitte einen SPI Handelstag aus (keine Wochenenden / Feiertage).")
    st.stop()

assets = ["SPI", "Banken", "Finanzen", "Gesundheit", "Lebensmittel", "Versicherungen"]
selected_cols = st.sidebar.multiselect(
    "Select variables",
    options=assets,
    default=["SPI"],
)
if not selected_cols:
    st.warning("Please select at least one variable.")
    st.stop()

norm = normalize(df_all[assets])
deltas = compute_peer_deltas(norm)

selected_var = st.sidebar.selectbox(
    "Variable for peer comparison",
    options=selected_cols,
)

sp500_pct, vix_close, gold_pct, brent_pct, wti_pct, temp, leitzins = get_latest_data()

# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
st.title("🔮 Kristallkugel")

st.subheader(f'Aktuelle Daten ({datetime.date.today().strftime("%d.%m.%Y")})')

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1.metric('S&P 500 (%)',     f'{sp500_pct:.2f}%')
col2.metric('VIX',             f'{vix_close:.2f}')
col3.metric('Gold (%)',        f'{gold_pct:.2f}%')
col4.metric('Brent (%)',       f'{brent_pct:.2f}%')
col5.metric('WTI (%)',         f'{wti_pct:.2f}%')
col6.metric('SNB Leitzins',    f'{leitzins:.2f}%')
col7.metric('Temperatur (°C)', f'{temp:.0f}°C')

# --------- Prediction --------- #
input_data = pd.DataFrame([{
    'sp500_S&P 500 (%)':      sp500_pct,
    'vix_VIX (%)':            vix_close,
    'oil_Brent (%)':          brent_pct,
    'oil_WTI (%)':            wti_pct,
    'gold_Gold (%)':          gold_pct,
    'meteo_Temperatur (°C)':  temp,
    'snb_SNB Leitzins':       leitzins
}])

prediction  = model.predict(input_data)[0]
probability = model.predict_proba(input_data)[0]

# --------- Ergebnis anzeigen --------- #
st.subheader(f'Vorhersage für den nächsten Handelstag ({(datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")})')

if prediction == 1:
    st.success(f'📈 SPI steigt  —  Wahrscheinlichkeit: {probability[1]:.1%}')
else:
    st.error(f'📉 SPI fällt  —  Wahrscheinlichkeit: {probability[0]:.1%}')
st.caption('⚠️ Diese Prognose ist kein Anlageratschlag.')

st.markdown("---")

st.subheader(f'Historische Daten ({stichtag.strftime("%d.%m.%Y")})')
tab_dashboard, tab_finance, tab_news, tab_raw = st.tabs(["📊 SPI", "🏦 Finanzdaten", "📰 News", "📄 Raw Data"])

# ---------------------------------------------------------
# Render Tabs
# ---------------------------------------------------------
with tab_dashboard:
        render_dashboard_tab(df_all, stichtag, selected_cols, norm, deltas, selected_var, compute_performance, handelstage)

with tab_finance:
    render_finance_tab(df_all, stichtag, norm, deltas, compute_performance, handelstage)

with tab_news:
        render_news_tab(df_news, stichtag)

with tab_raw:
        render_raw_data_tab(df_all, stichtag)
