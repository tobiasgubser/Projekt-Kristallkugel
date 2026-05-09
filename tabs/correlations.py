import streamlit as st
import pandas as pd
import plotly.express as px

def render_corr_tab(df_all, selected_cols):
    """Render the Correlations tab."""
    st.header("🔗 Korrelationen")
    corr = df_all[selected_cols].corr()
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
    )
    fig_corr.update_layout(height=600)
    st.plotly_chart(fig_corr, use_container_width=True)
