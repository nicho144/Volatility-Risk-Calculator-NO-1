import streamlit as st
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="VRP Dashboard", layout="wide")
st.title("Volatility Risk Premium (VRP) Dashboard")

# --- 1) Settings ---
fred_series = {"SPY": "VIXCLS", "GLD": "GVZ", "^TNX": "TYNVOLIndex"}
api_key = "DEMO"  # replace with your FRED key for frequent use
window_rv = 21  # rolling window for realized vol

# --- 2) Function to fetch IV from FRED ---
def fetch_fred_iv(series_id):
    base_url = "https://api.stlouisfed.org/fred/series/observations"
    try:
        r = requests.get(base_url, params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json"
        }).json()
        if "observations" not in r:
            st.warning(f"No observations returned for {series_id}")
            return None
        df = pd.DataFrame(r["observations"])
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna()
        return df.set_index("date")["value"]
    except Exception as e:
        st.error(f"Error fetching {series_id}: {e}")
        return None

# --- 3) Fetch latest IV ---
iv_data = {}
for ticker, series_id in fred_series.items():
    iv_series = fetch_fred_iv(series_id)
    if iv_series is not None and not iv_series.empty:
        iv_data[ticker] = iv_series
    else:
        iv_data[ticker] = pd.Series(dtype=float)

latest_iv = {t: series.iloc[-1] if not series.empty else np.nan for t, series in iv_data.items()}
st.subheader("Latest Implied Volatility (IV)")
st.write(latest_iv)

# --- 4) Fetch RV from Yahoo Finance ---
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
tickers = ["SPY", "GLD", "^TNX"]
data = yf.download(tickers, start=start_date, end=end_date)["Close"]

rets = np.log(data / data.shift(1))
rv = rets.rolling(window_rv).std() * np.sqrt(252)
latest_rv = rv.iloc[-1].to_dict()
st.subheader(f"Latest Realized Volatility (RV, {window_rv}-day, annualized)")
st.write(latest_rv)

# --- 5) Compute VRP ---
vrp = {t: latest_iv.get(t, np.nan) - latest_rv.get(t, np.nan) for t in tickers}
st.subheader("Volatility Risk Premium (VRP = IV - RV)")
st.write(vrp)

# --- 6) Plot VRP over time (6 months) ---
vrp_over_ti
