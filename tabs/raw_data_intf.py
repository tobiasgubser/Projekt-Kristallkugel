# ---------------------------------------------------------
# TAB – Raw Data
# ---------------------------------------------------------
import streamlit as st

def render_raw_data_tab(df_all, stichtag):
    st.title("📄 Rohdaten")

    df_stichtag = df_all.loc[df_all.index.date == stichtag]

    if df_stichtag.empty:
        st.warning("Keine Daten für diesen Stichtag.")
        return

    st.dataframe(df_stichtag.iloc[[0]], use_container_width=True)
