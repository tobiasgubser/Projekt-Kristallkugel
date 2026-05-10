import streamlit as st
import pandas as pd

def render_raw_data_tab(df_all, stichtag):

    PREFIXES = {
        "Trump": "trump_",
        "Meteo": "meteo_",
        "FX": "fx_",
        "Leitzins": "snb_",
        "VIX": "vix_",
        "Events": "events_",
        "Baltic": "baltic_",
    }

    def get_spi_columns(df, prefixes):
        return [
            c for c in df.columns
            if not any(c.startswith(p) for p in prefixes.values())
        ]

    # Filter data for selected date
    df_filtered = df_all[df_all.index.date == stichtag]

    if df_filtered.empty:
        st.warning(f"Keine Daten für {stichtag} verfügbar.")
        return

    st.subheader(f"Daten für {stichtag}")

    # Download
    csv = df_filtered.to_csv(index=True)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"kristallkugel_{stichtag}.csv",
        mime="text/csv"
    )

    st.subheader("SPI / Sektoren")
    spi_cols = get_spi_columns(df_all, PREFIXES)
    st.dataframe(df_filtered[spi_cols], use_container_width=True, hide_index=True)

    # --- Alle anderen Gruppen ---
    for group_name, prefix in PREFIXES.items():
        cols = [c for c in df_all.columns if c.startswith(prefix)]
        if not cols:
            continue
    
        st.subheader(f"📁 {group_name}")
        df_group = df_filtered[cols].rename(columns=lambda c: c.replace(prefix, ""))
        st.dataframe(df_group, use_container_width=True, hide_index=True)
