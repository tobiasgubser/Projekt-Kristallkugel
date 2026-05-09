import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
    df = pd.read_csv("df_all.csv", parse_dates=["date"])
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df['date'] = df['date'].dt.tz_convert('Europe/Zurich')
    df = df.set_index("date")
    return df

df_all = load_df_all()

@st.cache_resource
def load_df_news():
    df = pd.read_csv("df_news.tsv", sep="\t", parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["date"] = df["date"].dt.tz_convert("Europe/Zurich")
    df = df.set_index("date")
    return df

df_news = load_df_news()

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def get_numeric_cols(df):
    return df.select_dtypes(include=[np.number]).columns.tolist()

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
tab_dashboard, tab_corr, tab_news, tab_forecast, tab_raw = st.tabs(
    ["📊 Dashboard", "🔗 Korrelationen", "📰 News", "🔮 Forecast", "📄 Raw Data"]
)

# ---------------------------------------------------------
# TAB – Dashboard
# ---------------------------------------------------------
with tab_dashboard:

    st.title("🔮 Kristallkugel")

    temp = df_all.loc[df_all.index.date == stichtag, "meteo_Temperatur (°C)"].iloc[0]
    rain = df_all.loc[df_all.index.date == stichtag, "meteo_Niederschlagsdauer (min)"].iloc[0]
    radiation = df_all.loc[df_all.index.date == stichtag, "meteo_Globalstrahlung (W/m²)"].iloc[0]
    wind = df_all.loc[df_all.index.date == stichtag, "meteo_Windgeschwindigkeit (km/h)"].iloc[0]
    icon = weather_icon(temp, rain, radiation, wind)
    st.markdown(weather_kpi(temp, icon), unsafe_allow_html=True)

    st.subheader("Performance bis Stichtag")
    for col in selected_cols:
        perf_ytd, perf_week, perf_day = compute_performance(col, stichtag)
        nominal = df_all.loc[df_all.index.date == stichtag, col].iloc[0]

        def metric_block(label, value):
            delta = f"{value:.2f}%"
            delta_color = "normal"
            if value > 0:
                delta_color = "normal"
            elif value < 0:
                delta_color = "inverse"
            return delta, delta_color

        delta_ytd, color_ytd = metric_block("YTD", perf_ytd)
        delta_week, color_week = metric_block("1 Woche", perf_week)
        delta_day, color_day = metric_block("1 Tag", perf_day)

        st.markdown(f"### {col}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stand", f"{nominal:,.2f}")
        c2.metric("YTD", "", delta_ytd, delta_color=color_ytd)
        c3.metric("1 Woche", "", delta_week, delta_color=color_week)
        c4.metric("1 Tag", "", delta_day, delta_color=color_day)

    st.subheader("Normalized Performance (start = 1)")
    fig_norm = px.line(norm, labels={"value": "Normalized value", "index": "Date"})
    fig_norm.update_layout(height=500, legend_title_text="")
    st.plotly_chart(fig_norm, use_container_width=True)

    st.subheader(f"{selected_var} vs Peer Average")
    peers = norm.drop(columns=[selected_var])
    peer_avg = peers.mean(axis=1)

    df_plot = pd.DataFrame({
        "Date": norm.index,
        selected_var: norm[selected_var],
        "Peer average": peer_avg,
    })

    fig_peer = px.line(df_plot, x="Date", y=[selected_var, "Peer average"])
    fig_peer.update_layout(height=400, legend_title_text="")
    st.plotly_chart(fig_peer, use_container_width=True)

    st.subheader(f"Delta: {selected_var} minus Peer Average")
    fig_delta = px.area(deltas, x=deltas.index, y=selected_var)
    fig_delta.update_layout(height=300, legend_title_text="")
    st.plotly_chart(fig_delta, use_container_width=True)

# ---------------------------------------------------------
# TAB – Korrelationen
# ---------------------------------------------------------
with tab_corr:
    st.header("🔗 Korrelationen")
    corr = df_all[selected_cols].corr()
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
    )
    fig_corr.update_layout(height=600)
    st.plotly_chart(fig_corr, use_container_width=True)

# ---------------------------------------------------------
# TAB – News
# ---------------------------------------------------------
with tab_news:
    st.header("📰 Newsmeldungen des Tages")

    trump_count = df_news[(df_news.index.date == stichtag) & (df_news["category"] == "Trump Post")].shape[0]
    events_count = df_news[(df_news.index.date == stichtag) & (df_news["category"] == "Newsmeldung")].shape[0]

    c1, c2 = st.columns(2)
    c1.metric("Trump Posts", trump_count)
    c2.metric("Newsmeldungen", events_count)

    df_news_filtered = df_news[df_news.index.date == stichtag]
    for _, row in df_news_filtered.iterrows():
        st.markdown(
            f"""
            <div style="
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 12px;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 13px;
                    font-weight: 600;
                    color: #555;
                ">
                    <span>{row['category']}</span>
                    <span style="font-size: 13px; color: #333;">
                        {row['sentiment']:+.2f}
                    </span>
                </div>
        
                <div style="
                    font-size: 15px;
                    margin-top: 4px;
                    line-height: 1.4;
                    white-space: normal;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                ">
                    {row['text']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# TAB – Forecast
# ---------------------------------------------------------
with tab_forecast:
    st.header("🔮 Forecasting")

    # Variable wählen
    forecast_var = st.selectbox(
        "Variable für Forecast",
        options=selected_cols,
        index=0,
    )

    # Horizon & Methode
    c1, c2, c3 = st.columns(3)
    with c1:
        horizon = st.number_input("Forecast-Horizont (Perioden)", min_value=1, max_value=60, value=10, step=1)
    with c2:
        method = st.selectbox("Methode", ["EMA", "Naiv"])
    with c3:
        alpha = st.slider("Alpha (für EMA)", min_value=0.05, max_value=0.9, value=0.3, step=0.05)

    series = df_all[forecast_var]

    # Forecast berechnen
    forecast = forecast_series(series, horizon=horizon, method=method, alpha=alpha)

    # Plot: Historie + Forecast
    st.subheader(f"Historie und Forecast: {forecast_var}")

    df_hist = series.to_frame(name="Historie")
    df_fc = forecast.to_frame(name="Forecast")

    df_plot_fc = pd.concat([df_hist, df_fc], axis=0)

    fig_fc = px.line(
        df_plot_fc,
        x=df_plot_fc.index,
        y=df_plot_fc.columns,
        labels={"value": forecast_var, "index": "Datum"},
    )

    # Forecast-Teil hervorheben
    fig_fc.add_vrect(
        x0=forecast.index[0],
        x1=forecast.index[-1],
        fillcolor="orange",
        opacity=0.1,
        line_width=0,
    )

    fig_fc.update_layout(height=500, legend_title_text="")
    st.plotly_chart(fig_fc, use_container_width=True)

    # Tabelle
    st.subheader("Forecast-Werte")
    st.dataframe(forecast.to_frame(name=f"{forecast_var} Forecast"), use_container_width=True)

# ---------------------------------------------------------
# TAB – Raw Data
# ---------------------------------------------------------
with tab_raw:
    st.header("📄 Raw Data")
    st.dataframe(df_all.loc[df_all.index.date == stichtag].iloc[0], use_container_width=True)
