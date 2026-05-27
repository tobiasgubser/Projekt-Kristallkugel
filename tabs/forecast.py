import streamlit as st
import pandas as pd
def render_forecast_tab(sp500_pct, vix_close, gold_pct, brent_pct, wti_pct, temp, leitzins, model, features):
    st.title('🔮 Kristallkugel – SPI Prognose')
    st.subheader('Vorhersage für den nächsten Handelstag')
    
    col1, col2, col3 = st.columns(3)
    col1.metric('S&P 500 (%)',     f'{sp500_pct:.2f}%')
    col1.metric('VIX',             f'{vix_close:.2f}')
    col2.metric('Gold (%)',        f'{gold_pct:.2f}%')
    col2.metric('Brent (%)',       f'{brent_pct:.2f}%')
    col3.metric('WTI (%)',         f'{wti_pct:.2f}%')

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
