import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="VRP Dashboard", layout="wide")
st.title("💎 Volatility Risk Premium (VRP) Dashboard")

# --- 1) Settings ---
tickers = ["SPY", "GLD", "^TNX"]
window_rv = 21  # 21-day realized vol
lookback_days = 365  # ~1 year

# --- 2) Fetch IV via Yahoo Options Implied Vol (proxy) ---
def fetch_iv_yahoo(ticker):
    """
    Approximate implied vol from Yahoo Finance options data.
    This is a proxy for the vibe – no API key needed.
    """
    try:
        data = yf.Ticker(ticker)
        # pick nearest monthly expiry
        options = data.options
        if not options:
            return pd.Series(dtype=float)
        expiry = options[0]
        opt_chain = data.option_chain(expiry)
        # simple proxy: average of calls + puts impliedVolatility
        ivs = pd.concat([
            opt_chain.calls['impliedVolatility'],
            opt_chain.puts['impliedVolatility']
        ])
        iv_series = pd.Series([ivs.mean() * 100], index=[datetime.today()])
        return iv_series
    except Exception as e:
        st.warning(f"Could not fetch IV for {ticker}: {e}")
        return pd.Series(dtype=float)

iv_data = {t: fetch_iv_yahoo(t) for t in tickers}
latest_iv = {t: v.iloc[-1] if not v.empty else np.nan for t, v in iv_data.items()}

st.subheader("Latest Implied Volatility (IV, proxy)")
st.write(latest_iv)

# --- 3) Fetch RV from Yahoo Finance ---
end_date = datetime.now()
start_date = end_date - timedelta(days=lookback_days)
data = yf.download(tickers, start=start_date, end=end_date)["Close"]

rets = np.log(data / data.shift(1))
rv = rets.rolling(window_rv).std() * np.sqrt(252)
latest_rv = rv.iloc[-1].to_dict()

st.subheader(f"Latest Realized Volatility (RV, {window_rv}-day, annualized)")
st.write(latest_rv)

# --- 4) Compute VRP ---
vrp = {t: latest_iv.get(t, np.nan) - latest_rv.get(t, np.nan) for t in tickers}
st.subheader("Volatility Risk Premium (VRP = IV - RV)")
st.write(vrp)

# --- 5) Plot VRP over time ---
# For vibe: approximate IV series by forward-filling latest IV
vrp_over_time = pd.DataFrame(index=rv.index)
for t in tickers:
    iv_series = iv_data.get(t)
    if iv_series is not None and not iv_series.empty:
        iv_aligned = iv_series.reindex(rv.index).ffill()
        vrp_over_time[t] = iv_aligned - rv[t]
    else:
        vrp_over_time[t] = np.nan

st.subheader("VRP Over Time (Proxy IV - Realized Vol)")
fig = px.line(vrp_over_time, title="VRP Over Time", labels={"value":"VRP (%)"})
st.plotly_chart(fig, use_container_width=True)
