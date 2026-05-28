import streamlit as st
import pandas as pd
from app.utils import kpi_normal, kpi_color

def render_finance_tab(df_all, stichtag, norm, deltas, compute_performance, handelstage):

    # --- Performance je Variabel ---
    st.subheader("Performance bis Stichtag")
    assets = ["gold_Gold", "sp500_S&P 500", "oil_Brent", "oil_WTI"]
    for col in assets:
        perf_ytd, perf_week, perf_day = compute_performance(col, stichtag, df_all, handelstage)
        nominal = df_all.loc[df_all.index.date == stichtag, col].iloc[0]

        def strip_prefix(name):
            return name.split("_", 1)[1] if "_" in name else name

        st.markdown(f"### {strip_prefix(col)}")
        c1, c2, c3, c4 = st.columns(4)        
        c1.markdown(kpi_normal("Stand", nominal), unsafe_allow_html=True)
        c2.markdown(kpi_color("YTD (%)", perf_ytd), unsafe_allow_html=True)
        c3.markdown(kpi_color("1 Woche (%)", perf_week), unsafe_allow_html=True)
        c4.markdown(kpi_color("1 Tag (%)", perf_day), unsafe_allow_html=True)
