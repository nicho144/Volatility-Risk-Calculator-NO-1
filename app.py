def get_latest_price(ticker_symbol):
    """Robust fetch for index prices like ^MOVE, ^VIX, etc."""
    periods = ["5d", "1mo", "3mo"]  # Try short → longer to catch recent data
    for period in periods:
        try:
            data = yf.download(ticker_symbol, period=period, progress=False)
            if not data.empty:
                # Indices use 'Close' (not Adj Close)
                price_col = 'Close' if 'Close' in data.columns else 'Adj Close'
                # Get last non-NaN value
                valid_prices = data[price_col].dropna()
                if not valid_prices.empty:
                    return valid_prices.iloc[-1]
        except Exception as e:
            st.warning(f"Fetch attempt failed for {ticker_symbol} ({period}): {str(e)}")
            continue
    st.warning(f"No data fetched for {ticker_symbol} after multiple attempts. Market closed?")
    return np.nan