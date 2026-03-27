import pandas as pd
import yfinance as yf
import os

def load_historical_candidates(file_path):
    """Loads the CSV with historical S&P 500 candidates."""
    # Use index_col=False to prevent first column from becoming index if it's shifted
    # Also drop any unnamed columns that might result from trailing commas
    df = pd.read_csv(file_path, index_col=False)
    # Filter only relevant columns in case of extra commas
    df = df[['Date', 'Ticker']]
    df['Date'] = pd.to_datetime(df['Date'].str.strip())
    df['Ticker'] = df['Ticker'].str.strip()
    return df

def fetch_market_data(tickers, start_date, end_date):
    """Fetches daily Adjusted Close prices for given tickers."""
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)
    if 'Adj Close' in data.columns:
        return data['Adj Close']
    elif 'Close' in data.columns:
        # In some versions or if auto_adjust=True, 'Adj Close' might be missing
        return data['Close']
    else:
        print(f"Columns available: {data.columns}")
        raise KeyError("Could not find 'Adj Close' or 'Close' in downloaded data.")

def get_benchmark_data(ticker, start_date, end_date):
    """Fetches benchmark data (e.g., $SPY)."""
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if 'Adj Close' in data.columns:
        return data['Adj Close']
    elif 'Close' in data.columns:
        return data['Close']
    else:
        raise KeyError(f"Could not find data for {ticker}")

def get_risk_free_rate(ticker, start_date, end_date):
    """Fetches Risk-Free Rate (e.g., ^TNX). Converts yield to decimal daily."""
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
    # ^TNX is yield in percentage (e.g., 4.5), so we divide by 100
    rf = data[col] / 100.0
    # Annual to daily (approximate)
    rf_daily = (1 + rf)**(1/252) - 1
    return rf_daily

def prepare_data_directory(directory='data/processed'):
    """Ensures the data directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
