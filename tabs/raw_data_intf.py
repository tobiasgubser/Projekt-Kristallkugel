import streamlit as st
import pandas as pd

def render_raw_data_tab(df_all, stichtag):
    """Render the Raw Data tab."""
    
    st.header("📄 Raw Data")
    
    # Filter data for selected date
    df_filtered = df_all[df_all.index.date == stichtag]
    
    if df_filtered.empty:
        st.warning(f"Keine Daten für {stichtag} verfügbar.")
        return
    
    st.subheader(f"Daten für {stichtag}")
    st.dataframe(df_filtered, use_container_width=True)
    
    # Download option
    csv = df_filtered.to_csv(index=True)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"kristallkugel_{stichtag}.csv",
        mime="text/csv"
    )
    
    # Summary statistics
    st.subheader("Zusammenfassung")
    st.write(df_filtered.describe().round(2))
