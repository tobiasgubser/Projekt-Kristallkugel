import streamlit as st
import pandas as pd
import plotly.express as px
from app_utils import kpi_normal, kpi_color

def render_spi_tab(df_all, stichtag, selected_cols, norm, deltas, compute_performance, handelstage):

    # --- Performance je Variabel ---
    st.subheader("Performance bis Stichtag")
    for col in selected_cols:
        perf_ytd, perf_week, perf_day = compute_performance(col, stichtag, df_all, handelstage)
        nominal = df_all.loc[df_all.index.date == stichtag, col].iloc[0]
        
        st.markdown(f"### {col}")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi_normal("Stand", nominal), unsafe_allow_html=True)
        c2.markdown(kpi_color("YTD (%)", perf_ytd), unsafe_allow_html=True)
        c3.markdown(kpi_color("1 Woche (%)", perf_week), unsafe_allow_html=True)
        c4.markdown(kpi_color("1 Tag (%)", perf_day), unsafe_allow_html=True)

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
