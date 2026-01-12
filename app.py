import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# --- 1) Fetch IV from FRED public API ---
# NOTE: FRED has a free public JSON API without requiring a key for basic series access
# Adjust series_ids to: VIXCLS, GVZ, TYNVOLIndex, etc.
series_ids = ["VIXCLS", "GVZ", "TYNVOLIndex"]
base_url = "https://api.stlouisfed.org/fred/series/observations"
params = {
    "api_key": "DEMO",  # You can use "DEMO" for public/low-rate
    "file_type": "json",
}

iv_data = {}
for sid in series_ids:
    params["series_id"] = sid
    r = requests.get(base_url, params=params).json()
    df = pd.DataFrame(r["observations"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    iv_data[sid] = df.set_index("date")["value"].dropna()
    
# Pick the most recent close for each implied vol
iv_latest = {sid: iv_data[sid].iloc[-1] for sid in iv_data}

print("Latest Implied Vol (IV) from FRED:", iv_latest)

# --- 2) Compute Realized Volatility (RV) ---
# Load last 252 trading days for target tickers
tickers = ["SPY", "GLD", "^TNX"]  # chg as desired
end_date = datetime.now()
start_date = end_date - timedelta(days=365)  # ~1 year back to ensure 252 trading days

data = yf.download(tickers, start=start_date, end=end_date)["Close"]

# Want continuous log returns; same calendar alignment
rets = np.log(data / data.shift(1))

# 21-day (approx 1 month) realized vol (annualised by sqrt(252))
rv = rets.rolling(window=21).std() * np.sqrt(252)

# latest RV for each ticker
rv_latest = rv.iloc[-1].to_dict()

print("Latest Realized Vol (21d, annualised):", rv_latest)

# --- 3) Volatility Risk Premium (VRP) ---
vrp = {}
for iv_label, iv_val in iv_latest.items():
    # match implied names to realized series if possible
    # For VIX CLS index, compare to SPY realized vol for S&P 500
    if iv_label == "VIXCLS":
        rv_val = rv_latest["SPY"]
    elif iv_label == "GVZ":
        rv_val = rv_latest["GLD"]
    elif iv_label == "TYNVOLIndex":
        rv_val = rv_latest["^TNX"]
    else:
        continue
    vrp[iv_label] = iv_val - rv_val

print("Volatility Risk Premium (IV − RV):", vrp)
