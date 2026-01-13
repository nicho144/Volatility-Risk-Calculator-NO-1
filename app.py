import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import time
from yfinance.exceptions import YFRateLimitError
from curl_cffi import requests  # For browser impersonation

# ================= CONFIG =================
TICKERS = ["AAPL", "TSLA", "SPY", "NVDA"]       # Add your watchlist here
IV_CHEAP_THRESHOLD = 0.25                       # e.g., <25% → potentially cheap
NEAR_ATM_RANGE = 10                             # dollars from current price for "near ATM"
HISTORY_FILE = "iv_history.csv"                 # For simple IV rank tracking
MAX_RETRIES = 5                                 # For rate limit handling
RETRY_DELAY = 10                                # Seconds to wait on retry

sns.set_style("darkgrid")  # Nicer plots

# Create global impersonating session (mimics Chrome to avoid rate limits/detections)
session = requests.Session(impersonate="chrome110")  # Use a recent Chrome version

# ================= HELPERS =================
def get_current_price(ticker):
    """Get latest underlying price"""
    stock = yf.Ticker(ticker, session=session)
    return stock.info.get('regularMarketPrice') or stock.info.get('currentPrice')

def get_near_atm_iv(ticker, days_ahead=1):
    """
    Get average IV for near-ATM options on the nearest expiration.
    Returns dict with avg_iv, current_price, nearest_exp, etc.
    """
    stock = yf.Ticker(ticker, session=session)
    
    expirations = stock.options
    
    if not expirations:
        return None
    
    # Pick nearest expiration (you can change logic to pick ~30-45 DTE if wanted)
    nearest_exp = expirations[0]
    chain = stock.option_chain(nearest_exp)
    
    current_price = get_current_price(ticker)
    if not current_price:
        return None
    
    # Combine calls & puts, filter near ATM
    options = pd.concat([chain.calls, chain.puts])
    near_atm = options[
        abs(options['strike'] - current_price) <= NEAR_ATM_RANGE
    ]
    
    if near_atm.empty:
        return None
    
    avg_iv = near_atm['impliedVolatility'].mean()
    median_iv = near_atm['impliedVolatility'].median()
    
    return {
        'ticker': ticker,
        'current_price': round(current_price, 2),
        'nearest_exp': nearest_exp,
        'avg_near_atm_iv': avg_iv,
        'median_near_atm_iv': median_iv,
        'iv_percent': f"{avg_iv:.1%}",
        'is_cheap': avg_iv < IV_CHEAP_THRESHOLD,
        'num_contracts': len(near_atm)
    }

def get_near_atm_iv_with_retry(ticker, retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Wrapper with retry logic for rate limits"""
    for attempt in range(retries):
        try:
            return get_near_atm_iv(ticker)
        except YFRateLimitError:
            print(f"Rate limited on {ticker}. Attempt {attempt+1}/{retries}. Waiting {delay}s...")
            time.sleep(delay)
        except Exception as e:
            print(f"Error on {ticker}: {e}")
            break
    return None

def plot_iv_smile(ticker, exp_date=None):
    """Quick plot of IV vs Strike (volatility smile/skew)"""
    stock = yf.Ticker(ticker, session=session)
    if not exp_date:
        exp_date = stock.options[0]  # nearest
    
    chain = stock.option_chain(exp_date)
    current_price = get_current_price(ticker)
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=chain.calls, x='strike', y='impliedVolatility', 
                    label='Calls', alpha=0.6, color='blue')
    sns.scatterplot(data=chain.puts, x='strike', y='impliedVolatility', 
                    label='Puts', alpha=0.6, color='red')
    
    plt.axvline(current_price, color='black', linestyle='--', 
                label=f'Current Price ≈ ${current_price:.0f}')
    plt.title(f"{ticker} IV Smile/Skew - Expiration: {exp_date}")
    plt.xlabel("Strike Price")
    plt.ylabel("Implied Volatility")
    plt.legend()
    plt.tight_layout()
    plt.show()

def update_iv_history(results):
    """Append today's results to CSV for future IV rank calculation"""
    today = datetime.now().strftime("%Y-%m-%d")
    df_new = pd.DataFrame(results)
    df_new['date'] = today
    
    if os.path.exists(HISTORY_FILE):
        df_old = pd.read_csv(HISTORY_FILE)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    
    df.to_csv(HISTORY_FILE, index=False)
    print(f"History updated → {HISTORY_FILE}")

# ================= MAIN SCANNER =================
def scan_watchlist():
    print(f"\n=== IV Scan Report - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
    
    results = []
    for ticker in TICKERS:
        data = get_near_atm_iv_with_retry(ticker)
        if data:
            results.append(data)
            status = "CHEAP!" if data['is_cheap'] else "Normal/High"
            print(f"{ticker:6} | Price: ${data['current_price']:7.2f} | "
                  f"Nearest Exp: {data['nearest_exp']} | "
                  f"Avg IV: {data['iv_percent']:>6} → {status}")
        else:
            print(f"{ticker:6} → No data / no options")
    
    if results:
        # Optional: save for IV rank later
        update_iv_history(results)
    
    print("\nDone. Add plot_iv_smile('AAPL') to visualize any ticker!")
    return results

# ================= RUN IT =================
if __name__ == "__main__":
    scan_watchlist()
    
    # Uncomment to see a nice IV smile plot (example)
    # plot_iv_smile("AAPL")