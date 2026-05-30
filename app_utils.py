import pandas as pd
import numpy as np
import yfinance as yf
import joblib
import streamlit as st
import datetime as dt
import io, requests

def normalize(df):
    return df.div(df.iloc[0])

def compute_peer_deltas(norm_df):
    deltas = {}
    for col in norm_df.columns:
        peers = norm_df.drop(columns=[col])
        peer_avg = peers.mean(axis=1)
        deltas[col] = norm_df[col] - peer_avg
    return pd.DataFrame(deltas)

def summary_table(norm_df):
    last = norm_df.iloc[-1]
    df = pd.DataFrame({
        "Variable": last.index,
        "Performance (%)": (last.values - 1) * 100,
    })
    return df.sort_values("Performance (%)", ascending=False).reset_index(drop=True)

def compute_performance(col, stichtag, df_all, handelstage):
    if isinstance(stichtag, pd.Timestamp):
        stichtag = stichtag.date()

    mask = handelstage <= stichtag
    if not mask.any():
        return np.nan, np.nan, np.nan

    stichtag_idx = df_all.index[mask].max()
    v_now = df_all.loc[stichtag_idx, col]

    ytd_start = df_all.index.min()
    try:
        v_ytd = df_all.loc[ytd_start, col]
    except KeyError:
        v_ytd = df_all[col].iloc[0]
    perf_ytd = (v_now / v_ytd - 1) * 100

    week_ago_date = stichtag - pd.Timedelta(days=7).to_pytimedelta()
    mask_week = handelstage <= week_ago_date
    valid_days = df_all.index[mask_week]
    if len(valid_days) == 0:
        week_idx = df_all.index[0]
    else:
        week_idx = valid_days.max()
    v_week = df_all.loc[week_idx, col]
    perf_week = (v_now / v_week - 1) * 100

    mask_prev = handelstage < stichtag
    valid_days = df_all.index[mask_prev]
    if len(valid_days) == 0:
        prev_idx = df_all.index[0]
    else:
        prev_idx = valid_days.max()
    v_prev = df_all.loc[prev_idx, col]
    perf_day = (v_now / v_prev - 1) * 100

    return perf_ytd, perf_week, perf_day

def weather_icon(temp, rain_min, radiation, wind):
    if rain_min > 0:
        return "🌧️"
    if temp < 0:
        return "❄️"
    if radiation > 200:
        return "☀️"
    if radiation > 50:
        return "⛅"
    if wind > 25:
        return "💨"
    return "🌥️"

def get_latest_data():
    try:
        # S&P 500
        sp500 = yf.download('^GSPC', period='5d', auto_adjust=True, progress=False)
        sp500_pct = sp500['Close'].pct_change().dropna().iloc[-1].item() * 100

        # VIX
        vix = yf.download('^VIX', period='5d', auto_adjust=True, progress=False)
        #vix_close = vix['Close'].dropna().iloc[-1].item()
        vix_close_pct = vix['Close'].pct_change().dropna().iloc[-1].item() * 100

        # Gold
        gold = yf.download('GC=F', period='5d', auto_adjust=True, progress=False)
        gold_pct = gold['Close'].pct_change().dropna().iloc[-1].item() * 100

        # Brent
        brent = yf.download('BZ=F', period='5d', auto_adjust=True, progress=False)
        brent_pct = brent['Close'].pct_change().dropna().iloc[-1].item() * 100

        # WTI
        wti = yf.download('CL=F', period='5d', auto_adjust=True, progress=False)
        wti_pct = wti['Close'].pct_change().dropna().iloc[-1].item() * 100

        # Temperatur
        temp = (pd.read_csv(io.StringIO(requests.get('https://data.stadt-zuerich.ch/dataset/ugz_meteodaten_stundenmittelwerte/download/ugz_ogd_meteo_h1_2026.csv').content.decode('utf-8')), sep=',', engine='python')
                .pipe(lambda df: df[df['Parameter'] == 'T'])
                .assign(Datum=lambda df: pd.to_datetime(df['Datum']))
                .pipe(lambda df: df[df['Datum'].dt.date == df['Datum'].dt.date.max()])
                .pipe(lambda df: df[df['Datum'].dt.hour >= 6])['Wert']
                .mean()
            )

        # Leitzins
        leitzins = max(requests.get('https://data.snb.ch/api/cube/snboffzisa/data/json/de?dimSel=D0(LZ)&fromDate=2026-01&toDate=2026-12').json()['timeseries'][0]['values'], key=lambda x: x['date'])['value']
        
        #return sp500_pct, vix_close, gold_pct, brent_pct, wti_pct, temp, leitzins
        return sp500_pct, vix_close_pct, gold_pct, brent_pct, wti_pct, temp, leitzins

    except Exception as e:
        st.warning(f'⚠️ Marktdaten konnten nicht geladen werden: {e}')
        return None, None, None, None, None, None, None

def kpi_normal(label, value):
    if isinstance(value, (int, float)):
        value_html = f"{value:,.2f}"
    else:
        value_html = value
    return f"""
    <div style="
        background-color: #f8fafc;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
        font-family: sans-serif;
    ">
        <div style="font-size: 13px; color: #475569; margin-bottom: 4px;">
            {label}
        </div>
        <div style="font-size: 22px; font-weight: 600; color: #000000;">
            {value_html}
        </div>
    </div>
    """

def kpi_color(label, value):
    if value > 0.1:
        color = "#16a34a"  # grün
        arrow = "▲"
    elif value < -0.1:
        color = "#dc2626"  # rot
        arrow = "▼"
    else:
        color = "#ca8a04"  # gelb
        arrow = "▶"

    return f"""
    <div style="
        background-color: #f8fafc;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
        font-family: sans-serif;
    ">
        <div style="font-size: 13px; color: #475569; margin-bottom: 4px;">
            {label}
        </div>
        <div style="font-size: 22px; font-weight: 600; color: {color};">
            {arrow} {value:.2f}%
        </div>
    </div>
    """
