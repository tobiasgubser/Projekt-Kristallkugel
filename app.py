import streamlit              as st
import pandas                 as pd
import numpy                  as np
import plotly.express         as px
import plotly.graph_objects   as go
import utility                as ut
from tabs.raw_data_intf import render_raw_data_tab
from tabs.dashboard import render_dashboard_tab
from tabs.correlations import render_corr_tab
from tabs.news import render_news_tab
from tabs.forecast import render_forecast_tab
from tabs.event_studies import render_event_tab

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

@st.cache_resource
def load_df_news():
    df = pd.read_csv("data/df_news.tsv", sep="\t", parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["date"] = df["date"].dt.tz_convert("Europe/Zurich")
    df = df.set_index("date")
    return df

df_news = load_df_news()

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
#def get_numeric_cols(df):
    #return df.select_dtypes(include=[np.number]).columns.tolist()

def normalize(df):
    return df.div(df.iloc[0])

def compute_peer_deltas(norm_df):
    deltas = {}
    for col in norm_df.columns:
        peers = norm_df.drop(columns=[col])
        peer_avg = peers.mean(axis=1)
        deltas[col] = norm_df[col] - peer_avg
    return pd.DataFrame(deltas)

def summary_table(norm_df):
    last = norm_df.iloc[-1]
    df = pd.DataFrame({
        "Variable": last.index,
        "Performance (%)": (last.values - 1) * 100,
    })
    return df.sort_values("Performance (%)", ascending=False).reset_index(drop=True)

handelstage = df_all.index.date

def compute_performance(col, stichtag):
    if isinstance(stichtag, pd.Timestamp):
        stichtag = stichtag.date()

    mask = handelstage <= stichtag
    if not mask.any():
        return np.nan, np.nan, np.nan

    stichtag_idx = df_all.index[mask].max()
    v_now = df_all.loc[stichtag_idx, col]

    ytd_start = df_all.index.min()
    v_ytd = df_all.loc[ytd_start, col]
    perf_ytd = (v_now / v_ytd - 1) * 100

    week_ago_date = stichtag - pd.Timedelta(days=7).to_pytimedelta()
    mask_week = handelstage <= week_ago_date
    week_idx = df_all.index[mask_week].max()
    v_week = df_all.loc[week_idx, col]
    perf_week = (v_now / v_week - 1) * 100

    mask_prev = handelstage < stichtag
    prev_idx = df_all.index[mask_prev].max()
    v_prev = df_all.loc[prev_idx, col]
    perf_day = (v_now / v_prev - 1) * 100

    return perf_ytd, perf_week, perf_day

def weather_kpi(value, icon):
    return f"""
    <div style="
        border:1px solid #ccc;
        border-radius:8px;
        padding:10px 14px;
        background-color:#f7f7f7;
        text-align:center;
        margin-bottom:12px;
    ">
        <div style="font-size:12px; color:#666; font-weight:600;">
            aktuelles Wetter
        </div>
        <div style="font-size:20px; font-weight:700; margin-top:4px;">
            {icon} {value:.2f} °C
        </div>
    </div>
    """

def weather_icon(temp, rain_min, radiation, wind):
    if rain_min > 0:
        return "🌧️"
    if temp < 0:
        return "❄️"
    if radiation > 200:
        return "☀️"
    if radiation > 50:
        return "⛅"
    if wind > 25:
        return "💨"
    return "🌥️"

# ---------------------------------------------------------
# Forecast
# ---------------------------------------------------------

def forecast_series(series, horizon=10, method="EMA", alpha=0.3):
    """
    Einfaches Forecasting:
    - Naiv: letzter Wert fortgeschrieben
    - EMA: exponentiell geglättete Fortschreibung
    """
    series = series.dropna()
    if series.empty:
        return pd.Series(dtype=float)

    last_index = series.index[-1]
    freq = pd.infer_freq(series.index)
    if freq is None:
        # fallback: tägliche Frequenz
        freq = "D"

    future_index = pd.date_range(start=last_index, periods=horizon+1, freq=freq)[1:]

    if method == "Naiv":
        forecast_values = np.repeat(series.iloc[-1], horizon)
    elif method == "EMA":
        ema = series.ewm(alpha=alpha, adjust=False).mean().iloc[-1]
        # einfache Fortschreibung mit letztem EMA-Wert
        forecast_values = np.repeat(ema, horizon)
    else:
        raise ValueError("Unknown method")

    return pd.Series(forecast_values, index=future_index, name=series.name)

def get_event_window(df, event_date, window_before=3, window_after=3):
    """
    Gibt einen DataFrame zurück, der das Event-Fenster enthält.
    """
    idx = df.index.get_loc(event_date)
    start = max(0, idx - window_before)
    end = min(len(df) - 1, idx + window_after)
    return df.iloc[start:end+1]

def compute_event_study(df, col, event_date, window_before=3, window_after=3):
    """
    Berechnet Returns, Expected Returns (Peer Average), AR und CAR.
    """
    window_df = get_event_window(df, event_date, window_before, window_after)

    # Returns
    returns = window_df[col].pct_change().fillna(0)

    # Expected returns = Peer Average
    peers = df.drop(columns=[col])
    peer_avg = peers.mean(axis=1).pct_change().reindex(window_df.index).fillna(0)

    # Abnormal Returns
    ar = returns - peer_avg

    # CAR
    car = ar.cumsum()

    result = pd.DataFrame({
        "value": window_df[col],
        "return": returns,
        "expected_return": peer_avg,
        "abnormal_return": ar,
        "CAR": car
    })

    return result
    
# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
st.sidebar.header("Settings")

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

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tab_dashboard, tab_corr, tab_news, tab_event, tab_forecast, tab_raw = st.tabs(
    ["📊 Dashboard", "🔗 Korrelationen", "📰 News", "📉 Event-Studien", "🔮 Forecast", "📄 Raw Data"]
)

# ---------------------------------------------------------
# Render Tabs
# ---------------------------------------------------------
with tab_dashboard:
    render_dashboard_tab(df_all, stichtag, selected_cols, norm, deltas, selected_var, compute_performance)

with tab_corr:
    render_corr_tab(df_all, selected_cols)

with tab_news:
    render_news_tab(df_news, stichtag)

with tab_event:
    render_event_tab(df_all, df_news, selected_cols, handelstage, compute_event_study)

with tab_forecast:
    render_forecast_tab(df_all, selected_cols, forecast_series)

with tab_raw:
    render_raw_data_tab(df_all, stichtag)
