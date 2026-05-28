import streamlit as st
import pandas as pd
from app_utils import weather_icon, kpi_normal

def render_meteo_tab(df_all, stichtag):

    # --- Wetterdaten ---
    temp = df_all.loc[df_all.index.date == stichtag, "meteo_Temperatur (°C)"].iloc[0]
    rain = df_all.loc[df_all.index.date == stichtag, "meteo_Niederschlagsdauer (min)"].iloc[0]
    radiation = df_all.loc[df_all.index.date == stichtag, "meteo_Globalstrahlung (W/m²)"].iloc[0]
    wind = df_all.loc[df_all.index.date == stichtag, "meteo_Windgeschwindigkeit (km/h)"].iloc[0]
    humidity = df_all.loc[df_all.index.date == stichtag, "meteo_Relative Luftfeuchtigkeit (%)"].iloc[0]
    icon = weather_icon(temp, rain, radiation, wind)

    st.markdown(f"### Wetter des Tages")
    c1, c2, c3, c4 = st.columns(4)
    c1..markdown(kpi_normal("Temperatur", f"{icon} {temp: .1f} °C"), unsafe_allow_html=True)
    c2.markdown(kpi_normal("Niederschlagsdauer", f"{rain: .1f} min"), unsafe_allow_html=True)
    c3.markdown(kpi_normal("Wind", f"{wind: .1f} km/h"), unsafe_allow_html=True)
    c4.markdown(kpi_normal("Luftfeuchtigkeit", f"{humidity: .1f} %"), unsafe_allow_html=True)
