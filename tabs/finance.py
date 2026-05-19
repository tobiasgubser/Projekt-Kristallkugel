import streamlit as st
import pandas as pd

def render_finance_tab(df_all, stichtag, norm, deltas, compute_performance, handelstage):

    # --- Performance je Variabel ---
    st.subheader("Performance bis Stichtag")
  assets = ["Gold", "S&P 500", "Brent", "WTI"]
    for col in assets:
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
        c1.metric("Stand", f"{nominal:,.2f}")
        c2.metric("YTD", "", delta_ytd, delta_color=color_ytd)
        c3.metric("1 Woche", "", delta_week, delta_color=color_week)
        c4.metric("1 Tag", "", delta_day, delta_color=color_day)
