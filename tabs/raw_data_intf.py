# ---------------------------------------------------------
# TAB – Raw Data
# ---------------------------------------------------------
with tab_raw:
    st.header("📄 Raw Data")
    st.dataframe(df_all.loc[df_all.index.date == stichtag].iloc[0], use_container_width=True)
