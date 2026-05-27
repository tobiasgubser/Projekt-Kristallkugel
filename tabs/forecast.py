import streamlit as st
import pandas as pd
def render_forecast_tab(sp500_pct, vix_close, gold_pct, brent_pct, wti_pct, temp, leitzins, model, features):
    st.title('🔮 Kristallkugel – SPI Prognose')
    st.subheader('Vorhersage für den nächsten Handelstag')
    
    col1, col2, col3 = st.columns(7)
    col1.metric('S&P 500 (%)',     f'{sp500_pct:.2f}%')
    col2.metric('VIX',             f'{vix_close:.2f}')
    col3.metric('Gold (%)',        f'{gold_pct:.2f}%')
    col4.metric('Brent (%)',       f'{brent_pct:.2f}%')
    col5.metric('WTI (%)',         f'{wti_pct:.2f}%')
    col6.metric('SNB Leitzins',    f'{leitzins:.2f}%')
    col7.metric('Temperatur (°C)', f'{temp:.0f}°C')

    # --------- Prediction --------- #
    input_data = pd.DataFrame([{
        'sp500_S&P 500 (%)':      sp500_pct,
        'vix_VIX (%)':            vix_close,
        'oil_Brent (%)':          brent_pct,
        'oil_WTI (%)':            wti_pct,
        'gold_Gold (%)':          gold_pct,
        'meteo_Temperatur (°C)':  temp,
        'snb_SNB Leitzins':       leitzins
    }])
    
    prediction  = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0]
    
    # --------- Ergebnis anzeigen --------- #
    st.subheader('🔮 Prognose für morgen')
    
    if prediction == 1:
        st.success(f'📈 SPI steigt  —  Wahrscheinlichkeit: {probability[1]:.1%}')
    else:
        st.error(f'📉 SPI fällt  —  Wahrscheinlichkeit: {probability[0]:.1%}')
    st.caption('⚠️ Diese Prognose ist kein Anlageratschlag.')
