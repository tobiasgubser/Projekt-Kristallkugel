import streamlit as st
import pandas as pd
import plotly.express as px
from app_utils import weather_icon

def render_dashboard_tab(df_all, stichtag, selected_cols, norm, deltas, compute_performance, handelstage):

    # --- Wetterdaten ---
    temp = df_all.loc[df_all.index.date == stichtag, "meteo_Temperatur (°C)"].iloc[0]
    rain = df_all.loc[df_all.index.date == stichtag, "meteo_Niederschlagsdauer (min)"].iloc[0]
    radiation = df_all.loc[df_all.index.date == stichtag, "meteo_Globalstrahlung (W/m²)"].iloc[0]
    wind = df_all.loc[df_all.index.date == stichtag, "meteo_Windgeschwindigkeit (km/h)"].iloc[0]
    humidity = df_all.loc[df_all.index.date == stichtag, "meteo_Relative Luftfeuchtigkeit (%)"].iloc[0]
    icon = weather_icon(temp, rain, radiation, wind)

    st.markdown(f"### Wetter des Tages")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatur", f"{icon} {temp: .1f} °C")
    c2.metric("Niederschlagsdauer", f"{rain: .1f} min")
    c3.metric("Wind", f"{wind: .1f} km/h")
    c4.metric("Luftfeuchtigkeit", f"{humidity: .1f} %")

    # --- Performance je Variabel ---
    st.subheader("Performance bis Stichtag")
    for col in selected_cols:
        perf_ytd, perf_week, perf_day = compute_performance(col, stichtag, df_all, handelstage)
        nominal = df_all.loc[df_all.index.date == stichtag, col].iloc[0]

        def metric_block(value):
            delta_color = "inverse" if value >= 0 else "inverse"
            return value, delta_color
        
        delta_ytd, color_ytd = metric_block(perf_ytd)
        delta_week, color_week = metric_block(perf_week)
        delta_day, color_day = metric_block(perf_day)
        
        st.markdown(f"### {col}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stand", f"{nominal:,.2f}")
        c2.metric("YTD (%)", f"{perf_ytd:.2f}", perf_ytd, delta_color=color_ytd)
        c3.metric("1 Woche (%)", f"{perf_week:.2f}", perf_week, delta_color=color_week)
        c4.metric("1 Tag (%)", f"{perf_day:.2f}", perf_day, delta_color=color_day)

    st.subheader("Normalized Performance (start = 1)")
    peer_avg = norm.mean(axis=1)
    df_plot = norm[selected_cols].copy()
    df_plot["Peer average"] = peer_avg
    df_plot["Date"] = df_plot.index
    
    df_long = df_plot.melt(id_vars="Date", var_name="Variable", value_name="Value")
    fig = px.line(df_long, x="Date", y="Value", color="Variable")
    fig.update_layout(height=500, legend_title_text="")
    st.plotly_chart(fig, width='stretch')

    for c in selected_cols:
        st.subheader(f"Delta: {c} minus Peer Average")
        fig_delta = px.area(deltas, x=deltas.index, y=c)
        fig_delta.update_layout(height=300, legend_title_text="")
        st.plotly_chart(fig_delta, width='stretch')
