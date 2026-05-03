import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

st.set_page_config(
    page_title="SPI Case Study Dashboard",
    page_icon="📈",
    layout="wide",
)

# ---------------------------------------------------------
# Load df_all
# ---------------------------------------------------------
@st.cache_resource
def load_df_all():
    df = pd.read_csv("df_all.csv", parse_dates=["date"])
    df = df.set_index("date")
    return df

df_all = load_df_all()

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

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
st.sidebar.header("Settings")

filter_date = st.sidebar.date_input(
    "Zeige Daten bis:",
    value=pd.to_datetime("2025-12-31"),
    min_value=pd.to_datetime("2025-01-01"),
    max_value=df_all.index.max()
)
df_filtered = df_all.loc["2025-01-01":filter_date]

selected_cols = st.sidebar.multiselect(
    "Select variables",
    options=["SPI (%)", "Banken (%)", "Finanzen (%)", "Gesundheit (%)", "Lebensmittel (%)", "Versicherungen (%)"],
    default=["SPI (%)"],
)

if not selected_cols:
    st.warning("Please select at least one variable.")
    st.stop()

norm = normalize(df_filtered[selected_cols])
deltas = compute_peer_deltas(norm)

selected_var = st.sidebar.selectbox(
    "Variable for peer comparison",
    options=selected_cols,
)

show_corr = st.sidebar.checkbox("Show correlation matrix")
show_raw = st.sidebar.checkbox("Show raw data")

# ---------------------------------------------------------
# Layout
# ---------------------------------------------------------
st.title("📊 SPI Case Study Dashboard (df_filtered)")

st.subheader("Manager Summary Table")
st.dataframe(summary_table(norm), use_container_width=True)

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
    corr = df_filtered[selected_cols].corr()
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
    )
    fig_corr.update_layout(height=600)
    st.plotly_chart(fig_corr, use_container_width=True)

if show_raw:
    st.subheader("Raw Data")
    st.dataframe(df_filtered, use_container_width=True)
