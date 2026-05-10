import streamlit as st
import pandas as pd
import plotly.express as px

def render_forecast_tab(df_all, selected_cols, forecast_series):
    """Render the Forecast tab."""
    st.header("🔮 Forecasting")

    # Variablen wählen (Mehrfachauswahl)
    forecast_vars = st.multiselect(
        "Variablen für Forecast",
        options=selected_cols,
        default=selected_cols[:1],
    )

    if not forecast_vars:
        st.warning("Bitte mindestens eine Variable auswählen.")
        return

    # Horizon & Methode
    c1, c2, c3 = st.columns(3)
    with c1:
        horizon = st.number_input("Forecast-Horizont (Perioden)", min_value=1, max_value=60, value=10, step=1)
    with c2:
        method = st.selectbox("Methode", ["EMA", "Naiv"])
    with c3:
        alpha = st.slider("Alpha (für EMA)", min_value=0.05, max_value=0.9, value=0.3, step=0.05)

    # Forecasts für alle ausgewählten Variablen berechnen
    for forecast_var in forecast_vars:
        series = df_all[forecast_var]

        # Forecast berechnen
        forecast = forecast_series(series, horizon=horizon, method=method, alpha=alpha)

        # Plot: Historie + Forecast
        st.subheader(f"Historie und Forecast: {forecast_var}")

        df_hist = series.to_frame(name="Historie")
        df_fc = forecast.to_frame(name="Forecast")

        df_plot_fc = pd.concat([df_hist, df_fc], axis=0)

        fig_fc = px.line(
            df_plot_fc,
            x=df_plot_fc.index,
            y=df_plot_fc.columns,
            labels={"value": forecast_var, "index": "Datum"},
        )

        # Forecast-Teil hervorheben
        fig_fc.add_vrect(
            x0=forecast.index[0],
            x1=forecast.index[-1],
            fillcolor="orange",
            opacity=0.1,
            line_width=0,
        )

        fig_fc.update_layout(height=500, legend_title_text="")
        st.plotly_chart(fig_fc, use_container_width=True)

        # Tabelle
        st.subheader("Forecast-Werte")
        st.dataframe(forecast.to_frame(name=f"{forecast_var} Forecast"), use_container_width=True)
