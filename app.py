import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="SPI Case Study Dashboard",
    page_icon="📈",
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

def summary_table(norm_df):
    last = norm_df.iloc[-1]
    df = pd.DataFrame({
        "Variable": last.index,
        "Performance (%)": (last.values - 1) * 100,
    })
    return df.sort_values("Performance (%)", ascending=False).reset_index(drop=True)

def compute_performance(col, stichindex):
    # Aktueller Wert
    v_now = df_all.loc[stichindex, col]

    # --- YTD ---
    ytd_start = df_all.index.min()
    v_ytd = df_all.loc[ytd_start, col]
    perf_ytd = (v_now / v_ytd - 1) * 100

    # --- 1 Woche ---
    week_ago = stichindex - pd.Timedelta(days=7)
    week_ago = df_all.index[df_all.index <= week_ago].max()  # letzter Handelstag davor
    v_week = df_all.loc[week_ago, col]
    perf_week = (v_now / v_week - 1) * 100

    # --- 1 Tag ---
    prev_day = df_all.index[df_all.index < stichindex].max()
    v_prev = df_all.loc[prev_day, col]
    perf_day = (v_now / v_prev - 1) * 100

    return perf_ytd, perf_week, perf_day

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
stichindex = pd.Timestamp(stichtag).tz_localize("Europe/Zurich")

selected_cols = st.sidebar.multiselect(
    "Select variables",
    options=["SPI", "Banken", "Finanzen", "Gesundheit", "Lebensmittel", "Versicherungen"],
    default=["SPI"],
)

if not selected_cols:
    st.warning("Please select at least one variable.")
    st.stop()

show_corr = st.sidebar.checkbox("Show correlation matrix")
show_raw = st.sidebar.checkbox("Show raw data")

# ---------------------------------------------------------
# Layout
# ---------------------------------------------------------
st.title("📊 SPI Case Study Dashboard (df_all)")

st.subheader("Performance bis Stichtag")
cols = st.columns(3)
for col in selected_cols:
    perf_ytd, perf_week, perf_day = compute_performance(col, stichtag)
    with st.container():
        st.markdown(f"### {col}")
        c1, c2, c3 = st.columns(3)
        c1.metric("YTD", f"{perf_ytd:.2f}%")
        c2.metric("1 Woche", f"{perf_week:.2f}%")
        c3.metric("1 Tag", f"{perf_day:.2f}%")

st.subheader("Normalized Performance (start = 1)")
fig_norm = px.line(
    norm,
    labels={"value": "Normalized value", "index": "Date"},
)
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

fig_peer = px.line(
    df_plot,
    x="Date",
    y=[selected_var, "Peer average"],
)
fig_peer.update_layout(height=400, legend_title_text="")
st.plotly_chart(fig_peer, use_container_width=True)

st.subheader(f"Delta: {selected_var} minus Peer Average")
fig_delta = px.area(
    deltas,
    x=deltas.index,
    y=selected_var,
)
fig_delta.update_layout(height=300, legend_title_text="")
st.plotly_chart(fig_delta, use_container_width=True)

if show_corr:
    st.subheader("Correlation Matrix")
    corr = df_all[selected_cols].corr()
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
    )
    fig_corr.update_layout(height=600)
    st.plotly_chart(fig_corr, use_container_width=True)

st.subheader("Newsmeldungen des Tages")
df_news_filtered = df_news[df_news.index.date >= stichtag]
df_news_filtered = df_news_filtered.reset_index(drop=True)
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
            <div style="font-size: 13px; font-weight: 600; color: #555;">
                {row['category']}
            </div>
            <div style="font-size: 15px; margin-top: 4px; line-height: 1.4;">
                {row['text']}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

if show_raw:
    st.subheader("Raw Data")
    st.dataframe(df_all, use_container_width=True)
