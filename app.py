import streamlit as st
import requests
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

st.title('Volatility Risk Premium (VRP) Calculator – FRED + yfinance')
st.write('Daily updated VRP = IV (FRED close) - RV (21-day ann. from 252-day history).')

# FRED public JSON endpoint (no API key needed for observations)
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

def get_fred_latest(series_id):
    """Get most recent non-. value from FRED JSON"""
    try:
        params = {
            'series_id': series_id,
            'file_type': 'json',
            'limit': 10,  # last 10 obs to find latest valid
            'sort_order': 'desc'
        }
        r = requests.get(FRED_BASE, params=params, timeout=10)
        data = r.json()
        if 'observations' in data:
            for obs in data['observations']:
                if obs['value'] != '.':
                    return float(obs['value'])
        return np.nan
    except Exception:
        return np.nan

# Robust yfinance fetch for latest or history
def get_yf_data(ticker, period='1y'):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty:
            return pd.Series()
        return data['Adj Close'] if 'Adj Close' in data else data['Close']
    except Exception:
        return pd.Series()

# RV calc: 21-day ann std of log returns (equity/commodity) or changes (yields)
def calculate_rv(closes, window=21, is_yield=False):
    if len(closes) < window + 1:
        return np.nan
    if is_yield:
        changes = closes.diff().dropna()
        recent_changes = changes[-window:]
        rv = np.std(recent_changes) * np.sqrt(252) * 100  # bp scale
    else:
        log_ret = np.log(closes / closes.shift(1)).dropna()
        recent_ret = log_ret[-window:]
        rv = np.std(recent_ret) * np.sqrt(252) * 100  # %
    return rv

# Fetch IVs
iv_spy = get_fred_latest('VIXCLS')      # SPY/S&P500 IV
iv_gold = get_fred_latest('GVZCLS')     # Gold IV
iv_yields = get_latest_price('^MOVE')   # MOVE fallback (yfinance robust)

def get_latest_price(ticker):
    data = get_yf_data(ticker, '5d')
    if not data.empty:
        return data.iloc[-1]
    data = get_yf_data(ticker, '1mo')
    if not data.empty:
        return data.iloc[-1]
    return np.nan

# Fetch underlying history for RV (last 252 days ~1y)
spy_closes = get_yf_data('SPY', '2y')     # extra buffer
gold_closes = get_yf_data('GLD', '2y')    # GLD ETF for gold
tnx_closes = get_yf_data('^TNX', '2y')    # 10Y yield

# Compute RVs
rv_spy = calculate_rv(spy_closes)
rv_gold = calculate_rv(gold_closes)
rv_yields = calculate_rv(tnx_closes, is_yield=True)

# VRPs
vrp_spy = iv_spy - rv_spy if not np.isnan(iv_spy) and not np.isnan(rv_spy) else np.nan
vrp_gold = iv_gold - rv_gold if not np.isnan(iv_gold) and not np.isnan(rv_gold) else np.nan
vrp_yields = iv_yields - rv_yields if not np.isnan(iv_yields) and not np.isnan(rv_yields) else np.nan

# Display Dashboard
st.subheader('SPY (S&P 500)')
st.write(f'**Implied Vol (VIXCLS latest close):** {iv_spy:.2f}%' if not np.isnan(iv_spy) else 'IV: Unavailable (FRED delay)')
st.write(f'**Realized Vol (21-day ann.):** {rv_spy:.2f}%')
st.write(f'**VRP:** **{vrp_spy:.2f}%**' if not np.isnan(vrp_spy) else 'VRP: Unavailable')

st.subheader('GOLD (GLD)')
st.write(f'**Implied Vol (GVZCLS latest close):** {iv_gold:.2f}%' if not np.isnan(iv_gold) else 'IV: Unavailable (FRED delay)')
st.write(f'**Realized Vol (21-day ann.):** {rv_gold:.2f}%')
st.write(f'**VRP:** **{vrp_gold:.2f}%**' if not np.isnan(vrp_gold) else 'VRP: Unavailable')

st.subheader('YIELDS (10Y Treasury ^TNX)')
st.write(f'**Implied Vol (^MOVE latest):** {iv_yields:.2f} bp' if not np.isnan(iv_yields) else 'IV: Unavailable')
st.write(f'**Realized Vol (21-day ann. yield changes):** {rv_yields:.2f} bp')
st.write(f'**VRP:** **{vrp_yields:.2f} bp**' if not np.isnan(vrp_yields) else 'VRP: Unavailable')

st.info(f"Data as of latest available (FRED/yfinance): {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}. "
        "FRED updates ~daily after close. Weekend/non-market: previous values shown. "
        "RV uses last 252 trading days history.")