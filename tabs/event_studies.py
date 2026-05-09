import streamlit as st
import pandas as pd
import plotly.express as px

def render_event_tab(df_all, df_news, selected_cols, handelstage, compute_event_study):
    """Render the Event Studies tab."""
    st.header("📉 Event-Studien")

    # Event-Typ auswählen
    event_type = st.selectbox(
        "Event-Typ",
        options=df_news["category"].unique().tolist()
    )

    # Event-Datum auswählen
    event_dates = df_news[df_news["category"] == event_type].index.date
    event_date = st.selectbox("Event-Datum", sorted(event_dates))

    # Event-Fenster
    c1, c2 = st.columns(2)
    window_before = c1.number_input("Tage vor Event", min_value=1, max_value=10, value=3)
    window_after = c2.number_input("Tage nach Event", min_value=1, max_value=10, value=3)

    # Variable auswählen
    col = st.selectbox("Variable für Event-Studie", selected_cols)

    # Event-Date als Timestamp holen
    mask = handelstage <= event_date
    if not mask.any():
        st.warning("Für dieses Event-Datum existiert kein vorheriger Handelstag im df_all.")
        #st.stop()
    event_ts = df_all.index[mask].max()

    # Event-Studie berechnen
    result = compute_event_study(df_all[selected_cols], col, event_ts, window_before, window_after)

    # Plot AR
    st.subheader("Abnormal Returns (AR)")
    fig_ar = px.bar(
        result,
        x=result.index,
        y="abnormal_return",
        labels={"abnormal_return": "AR", "index": "Datum"},
    )
    st.plotly_chart(fig_ar, use_container_width=True)

    # Plot CAR
    st.subheader("Cumulative Abnormal Returns (CAR)")
    fig_car = px.line(
        result,
        x=result.index,
        y="CAR",
        labels={"CAR": "Cumulative AR", "index": "Datum"},
    )
    st.plotly_chart(fig_car, use_container_width=True)

    # Tabelle
    st.subheader("Event-Fenster Daten")
    st.dataframe(result, use_container_width=True)
