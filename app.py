import streamlit as st
import yfinance as yf
import numpy as np

st.title('Volatility Risk Premium (VRP) Calculator')
st.write('This app calculates VRP (IV - RV) for SPY, GOLD, and YIELDS using live market data. Updated daily.')

period = 30  # Trading days for RV calculation (approx. 1 month)

# Safe function to get latest price (fixes .info issues)
def get_latest_price(ticker_symbol):
    try:
        data = yf.download(ticker_symbol, period="5d", progress=False)
        if data.empty:
            return np.nan
        return data['Close'].iloc[-1]
    except Exception:
        return np.nan

# Function to calculate RV for equities/commodities (in %)
def calculate_rv(ticker, period):
    try:
        data = yf.download(ticker, period='3mo', progress=False)['Adj Close']
        log_returns = np.log(data / data.shift(1)).dropna()
        if len(log_returns) < period:
            return np.nan
        rv = np.std(log_returns[-period:]) * np.sqrt(252) * 100  # Annualized in %
        return rv
    except Exception:
        return np.nan

# Function to calculate RV for yields (in bp)
def calculate_rv_yields(ticker, period):
    try:
        data = yf.download(ticker, period='3mo', progress=False)['Close']
        daily_changes = data.diff().dropna()
        if len(daily_changes) < period:
            return np.nan
        rv_bp = np.std(daily_changes[-period:] * 100) * np.sqrt(252)  # Changes to bp, annualized
        return rv_bp
    except Exception:
        return np.nan

# SPY (S&P 500)
st.subheader('SPY (S&P 500)')
iv_spy = get_latest_price('^VIX')
rv_spy = calculate_rv('SPY', period)
vrp_spy = iv_spy - rv_spy if not np.isnan(iv_spy) and not np.isnan(rv_spy) else np.nan
st.write(f'Implied Volatility (^VIX): {iv_spy:.2f}%' if not np.isnan(iv_spy) else 'Implied Volatility: Data unavailable')
st.write(f'Realized Volatility (last {period} trading days): {rv_spy:.2f}%' if not np.isnan(rv_spy) else 'Realized Volatility: Data unavailable')
st.write(f'Volatility Risk Premium (IV - RV): {vrp_spy:.2f}%' if not np.isnan(vrp_spy) else 'VRP: Data unavailable')

# GOLD
st.subheader('GOLD')
iv_gold = get_latest_price('^GVZ')
rv_gold = calculate_rv('GC=F', period)  # Gold futures
vrp_gold = iv_gold - rv_gold if not np.isnan(iv_gold) and not np.isnan(rv_gold) else np.nan
st.write(f'Implied Volatility (^GVZ): {iv_gold:.2f}%' if not np.isnan(iv_gold) else 'Implied Volatility: Data unavailable')
st.write(f'Realized Volatility (last {period} trading days, GC=F): {rv_gold:.2f}%' if not np.isnan(rv_gold) else 'Realized Volatility: Data unavailable')
st.write(f'Volatility Risk Premium (IV - RV): {vrp_gold:.2f}%' if not np.isnan(vrp_gold) else 'VRP: Data unavailable')

# YIELDS (10Y Treasury)
st.subheader('YIELDS (10Y Treasury)')
iv_yields = get_latest_price('^MOVE')
rv_yields = calculate_rv_yields('^TNX', period)
vrp_yields = iv_yields - rv_yields if not np.isnan(iv_yields) and not np.isnan(rv_yields) else np.nan
st.write(f'Implied Volatility (^MOVE): {iv_yields:.2f} bp' if not np.isnan(iv_yields) else 'Implied Volatility: Data unavailable')
st.write(f'Realized Volatility (last {period} trading days, ^TNX): {rv_yields:.2f} bp' if not np.isnan(rv_yields) else 'Realized Volatility: Data unavailable')
st.write(f'Volatility Risk Premium (IV - RV): {vrp_yields:.2f} bp' if not np.isnan(vrp_yields) else 'VRP: Data unavailable')