import streamlit as st
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px

st.title("Volatility Risk Premium (VRP) Dashboard")

# --- FRED API settings ---
fred_series = {"SPY": "VIXCLS", "GLD": "GVZ", "^TNX": "TYNVOLIndex"}
fred_base_url = "https://api.stlouisfed.org/fred/series/observations"
api_key = "DEMO"  # For public/demo access

# --- Fetch IV from FRED ---
iv_latest = {}
for ticker, series_id in fred_series.items():
    r = requests.get(fred_base_url, params={
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json"
    }).json()
    df_iv = pd.DataFrame(r["observations"])
    df_iv["date"] = pd.to_datetime(df_iv["date"])
    df_iv["value"] = pd.to_numeric(df_iv["value"], errors="coerce")
    iv_latest[ticker] = df_iv.set_index("date")["value"].dropna().iloc[-1]

st.subheader("Latest Implied Volatility (IV)")
st.write(iv_latest)

# --- Fetch RV from Yahoo Finance ---
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
tickers = ["SPY", "GLD", "^TNX"]
data = yf.download(tickers, start=start_date, end=end_date)["Close"]
rets = np.log(data / data.shift(1))
rv = rets.rolling(21).std() * np.sqrt(252)
rv_latest = rv.iloc[-1].to_dict()

st.subheader("Latest Realized Volatility (RV, 21-day, annualized)")
st.write(rv_latest)

# --- Compute VRP ---
vrp = {t: iv_latest[t] - rv_latest[t] for t in tickers}
st.subheader("Volatility Risk Premium (VRP = IV - RV)")
st.write(vrp)

# --- Plot VRP over last 6 months ---
vrp_over_time = pd.DataFrame(index=rv.index)
for t, series_id in fred_series.items():
    r = requests.get(fred_base_url, params={
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json"
    }).json()
    df_iv = pd.DataFrame(r["observations"])
    df_iv["date"] = pd.to_datetime(df_iv["date"])
    df_iv["value"] = pd.to_numeric(df_iv["value"], errors="coerce")
    df_iv.set_index("date", inplace=True)
    iv_series = df_iv["value"].reindex(rv.index).ffill()
    vrp_over_time[t] = iv_series - rv[t]

fig = px.line(vrp_over_time, title="VRP Over Time")
st.plotly_chart(fig)
