import streamlit as st
import yfinance as yf
import numpy as np

st.title('Volatility Risk Premium (VRP) Calculator')
st.write('This app calculates VRP (IV - RV) for SPY, GOLD, and YIELDS using live market data. Updated daily.')

period = 30  # Trading days for RV (~1 month)

# Robust latest price fetch
def get_latest_price(ticker_symbol):
    try:
        for p in ["5d", "1mo", "1d"]:
            data = yf.download(ticker_symbol, period=p, progress=False, auto_adjust=False)
            if not data.empty:
                price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
                latest = data[price_col].dropna().iloc[-1]
                if not np.isnan(latest):
                    return latest
        return np.nan
    except Exception:
        return np.nan

# RV for equities/commodities (%)
def calculate_rv(ticker, period):
    try:
        data = yf.download(ticker, period='3mo', progress=False)['Adj Close']
        log_returns = np.log(data / data.shift(1)).dropna()
        if len(log_returns) < period:
            return np.nan
        rv = np.std(log_returns[-period:]) * np.sqrt(252) * 100
        return rv
    except Exception:
        return np.nan

# RV for yields (bp)
def calculate_rv_yields(ticker, period):
    try:
        data = yf.download(ticker, period='3mo', progress=False)['Close']
        daily_changes = data.diff().dropna()
        if len(daily_changes) < period:
            return np.nan
        rv_bp = np.std(daily_changes[-period:] * 100) * np.sqrt(252)
        return rv_bp
    except Exception:
        return np.nan

# SPY
st.subheader('SPY (S&P 500)')
iv_spy = get_latest_price('^VIX')
rv_spy = calculate_rv('SPY', period)
vrp_spy = iv_spy - rv_spy if not np.isnan(iv_spy) and not np.isnan(rv_spy) else np.nan
st.write(f'Implied Volatility (^VIX): {iv_spy:.2f}%' if not np.isnan(iv_spy) else 'Implied Volatility: Data unavailable (market closed or delay)')
st.write(f'Realized Volatility (last {period} days): {rv_spy:.2f}%' if not np.isnan(rv_spy) else 'RV: Data unavailable')
st.write(f'**VRP (IV - RV): {vrp_spy:.2f}%**' if not np.isnan(vrp_spy) else '**VRP: Data unavailable**')

# GOLD
st.subheader('GOLD')
iv_gold = get_latest_price('^GVZ')
rv_gold = calculate_rv('GC=F', period)
vrp_gold = iv_gold - rv_gold if not np.isnan(iv_gold) and not np.isnan(rv_gold) else np.nan
st.write(f'Implied Volatility (^GVZ): {iv_gold:.2f}%' if not np.isnan(iv_gold) else 'Implied Volatility: Data unavailable')
st.write(f'Realized Volatility (last {period} days, GC=F): {rv_gold:.2f}%' if not np.isnan(rv_gold) else 'RV: Data unavailable')
st.write(f'**VRP (IV - RV): {vrp_gold:.2f}%**' if not np.isnan(vrp_gold) else '**VRP: Data unavailable**')

# YIELDS
st.subheader('YIELDS (10Y Treasury)')
iv_yields = get_latest_price('^MOVE')
rv_yields = calculate_rv_yields('^TNX', period)
vrp_yields = iv_yields - rv_yields if not np.isnan(iv_yields) and not np.isnan(rv_yields) else np.nan
st.write(f'Implied Volatility (^MOVE): {iv_yields:.2f} bp' if not np.isnan(iv_yields) else 'Implied Volatility: Data unavailable')
st.write(f'Realized Volatility (last {period} days, ^TNX): {rv_yields:.2f} bp' if not np.isnan(rv_yields) else 'RV: Data unavailable')
st.write(f'**VRP (IV - RV): {vrp_yields:.2f} bp**' if not np.isnan(vrp_yields) else '**VRP: Data unavailable**')

st.info("Note: Data updates during US market hours (Mon-Fri). Weekend/off-hours may show previous close or 'unavailable'.")