import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import requests

# Function to calculate Implied Volatility (IV)
def calculate_iv(price, strike, time, risk_free_rate, option_price, option_type='call'):
    # Placeholder for a more complex IV calculation method (like the Black-Scholes model)
    # This is a simple approximation for demonstration
    if option_type == 'call':
        iv = (option_price / price) * np.sqrt(time)  # Simplified formula
    else:
        iv = (strike / option_price) * np.sqrt(time)  # Simplified formula
    return iv

# Fetching data from Yahoo Finance
def fetch_data(ticker):
    stock_data = yf.Ticker(ticker)
    return stock_data.history(period="1y")

# Fetching yield data from FRED
def fetch_yield_data(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    response = requests.get(url)
    data = pd.read_csv(pd.compat.StringIO(response.text), parse_dates=['DATE'])
    return data

# Streamlit application layout
st.title("Financial Calculator for Gold, Yields, and SPY")

# User inputs
option_price = st.number_input("Enter Option Price", value=10.0)
strike = st.number_input("Enter Strike Price", value=100.0)
time = st.number_input("Enter Time to Expiration (in years)", value=1.0)
risk_free_rate = st.number_input("Enter Risk-Free Rate (in %)", value=2.0) / 100

# Fetching data
gold_data = fetch_data("GC=F")  # Gold futures
spy_data = fetch_data("SPY")    # SPY ETF
yield_data = fetch_yield_data("GS10")  # 10-Year Treasury Yield

# Calculating IV for Gold, Yields, and SPY
iv_gold = calculate_iv(gold_data['Close'][-1], strike, time, risk_free_rate, option_price)
iv_spy = calculate_iv(spy_data['Close'][-1], strike, time, risk_free_rate, option_price)

# Displaying results
st.subheader("Implied Volatility (IV) Results:")
st.write(f"Gold IV: {iv_gold:.2f}")
st.write(f"SPY IV: {iv_spy:.2f}")

# Optional: Display yield data
st.subheader("10-Year Treasury Yield Data:")
st.line_chart(yield_data.set_index('DATE')['VALUE'])

# Run the Streamlit app
if __name__ == "__main__":
    st.run()