import streamlit as st
import pandas as pd
import plotly.express as px
from app_utils import weather_icon, weather_kpi

def render_dashboard_tab(df_all, stichtag, selected_cols, norm, deltas, selected_var, compute_performance, handelstage):

    # --- Wetterdaten ---
    temp = df_all.loc[df_all.index.date == stichtag, "meteo_Temperatur (°C)"].iloc[0]
    rain = df_all.loc[df_all.index.date == stichtag, "meteo_Niederschlagsdauer (min)"].iloc[0]
    radiation = df_all.loc[df_all.index.date == stichtag, "meteo_Globalstrahlung (W/m²)"].iloc[0]
    wind = df_all.loc[df_all.index.date == stichtag, "meteo_Windgeschwindigkeit (km/h)"].iloc[0]
    humidity = df_all.loc[df_all.index.date == stichtag, "meteo_Relative Luftfeuchtigkeit (%)"].iloc[0]
    icon = weather_icon(temp, rain, radiation, wind)

    st.markdown(f"### Wetter des Tages")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatur", {icon} {temp:.2f} °C)
    c2.metric("Niederschlagsdauer", {rain} min)
    c3.metric("Wind", {wind} km/h)
    c4.metric("Luftfeuchtigkeit", {humidity} %)

    # --- Performance je Variabel ---
    st.subheader("Performance bis Stichtag")
    for col in selected_cols:
        perf_ytd, perf_week, perf_day = compute_performance(col, stichtag, df_all, handelstage)
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
        c1.metric("Stand", f"{nominal:'.2f}")
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
