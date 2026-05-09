# ---------------------------------------------------------
# TAB – Raw Data
# ---------------------------------------------------------
import streamlit as st

def render_raw_data_tab(df_all, stichtag):
    st.write("Index sample:", df_all.index[:5])
    st.write("Stichtag:", stichtag, type(stichtag))

    st.title("📄 Rohdaten")

    df_stichtag = df_all.loc[df_all.index.date == stichtag]

    if df_stichtag.empty:
        st.warning("Keine Daten für diesen Stichtag.")
        return

    st.dataframe(df_stichtag.iloc[[0]], use_container_width=True)
