import yfinance as yf
import pandas as pd
import time
import os
import pickle
from datetime import datetime, timedelta
from tqdm import tqdm
import warnings

# Suppress warnings from yfinance
warnings.filterwarnings("ignore")

# ⚙️ CONFIGURATION (Defaults - can be overridden by run_all_analysis.py)
CACHE_DIR = "data_cache"
CACHE_EXPIRY_HOURS = 4
BATCH_SIZE = 50
BATCH_DELAY = 1.0
PERIOD_ORDER = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

# 🗂 STOCK GROUPS
stock_groups = {} # Populated by callers or left empty

# ======================================================
# 📥 SHARED UTILS
# ======================================================

def get_combined_ticker_list():
    """Returns a unique list of all tickers from all groups."""
    all_tickers = []
    for group_tickers in stock_groups.values():
        all_tickers.extend(group_tickers)
    return sorted(list(set(all_tickers)))

# ======================================================
# 📥 CACHING LOGIC
# ======================================================

def get_cache_path(period):
    """Returns the absolute path for a cache file based on the period."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"stock_data_{period}.pkl")

def is_cache_valid(cache_path):
    """Checks if the cache file exists and is not expired."""
    if not os.path.exists(cache_path):
        return False
    
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
    if file_age > timedelta(hours=CACHE_EXPIRY_HOURS):
        print(f"⚠️ Cache expired ({file_age.total_seconds() / 3600:.1f} hours old).")
        return False
        
    return True

def save_to_cache(data, period):
    path = get_cache_path(period)
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    print(f"💾 Data saved to local cache: {path}")

def load_from_cache(period):
    path = get_cache_path(period)
    with open(path, 'rb') as f:
        data = pickle.load(f)
    print(f"📖 Loaded data from local cache: {path}")
    return data

def slice_data_dict(data_dict, period):
    """
    Slices each DataFrame in the dictionary to match the requested period.
    """
    if not data_dict or period == "max":
        return data_dict
    
    sliced_dict = {}
    for ticker, df in data_dict.items():
        if df.empty:
            sliced_dict[ticker] = df
            continue
            
        # Determine the start date for the slice
        last_date = df.index.max()
        
        if period == "1d":
            sliced_dict[ticker] = df.tail(1)
        elif period == "5d":
            # For 5d, we skip time-based slicing and just take last 5 trading days 
            # as it's more reliable for small sessions
            sliced_dict[ticker] = df.tail(5)
        elif period == "1mo":
            start_date = last_date - pd.DateOffset(months=1)
            sliced_dict[ticker] = df[df.index >= start_date]
        elif period == "3mo":
            start_date = last_date - pd.DateOffset(months=3)
            sliced_dict[ticker] = df[df.index >= start_date]
        elif period == "6mo":
            start_date = last_date - pd.DateOffset(months=6)
            sliced_dict[ticker] = df[df.index >= start_date]
        elif period == "1y":
            start_date = last_date - pd.DateOffset(years=1)
            sliced_dict[ticker] = df[df.index >= start_date]
        elif period == "2y":
            start_date = last_date - pd.DateOffset(years=2)
            sliced_dict[ticker] = df[df.index >= start_date]
        elif period == "5y":
            start_date = last_date - pd.DateOffset(years=5)
            sliced_dict[ticker] = df[df.index >= start_date]
        elif period == "ytd":
            start_date = datetime(last_date.year, 1, 1)
            sliced_dict[ticker] = df[df.index >= start_date]
        else:
            # Fallback for others (2y, 5y, etc.)
            sliced_dict[ticker] = df
            
    return sliced_dict

# ======================================================
# 📥 DATA FETCHING
# ======================================================

def fetch_all_data(tickers, period="1y", interval="1d"):
    """
    Fetches data for all provided tickers with batching and progress tracking.
    """
    data_dict = {}
    print(f"\n📥 [StockDataManager] Fetching data for {len(tickers)} stocks (Period: {period}, Interval: {interval})...")

    # Use a progress bar for batches
    num_batches = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
    
    with tqdm(total=len(tickers), desc="📥 Downloading Data", unit="stock") as pbar:
        for i in range(0, len(tickers), BATCH_SIZE):
            chunk = tickers[i:i + BATCH_SIZE]
            try:
                # Bulk download using yfinance
                df_bulk = yf.download(chunk, period=period, interval=interval, group_by='ticker', auto_adjust=False, actions=False, threads=True, progress=False)
                
                # Normalize handling for single vs multi-stock chunks
                if len(chunk) == 1:
                    ticker = chunk[0]
                    if not df_bulk.empty:
                        data_dict[ticker] = df_bulk
                else:
                    for ticker in chunk:
                        try:
                            df_stock = df_bulk[ticker].copy()
                            df_stock.dropna(how='all', inplace=True)
                            if not df_stock.empty:
                                data_dict[ticker] = df_stock
                        except KeyError:
                            pass
                            
            except Exception as e:
                print(f"⚠️ Error in batch {i//BATCH_SIZE + 1}: {e}")
            
            pbar.update(len(chunk))
            
            # API rate limit safety
            if i + BATCH_SIZE < len(tickers):
                time.sleep(BATCH_DELAY)

    print(f"\n✅ [StockDataManager] Successfully fetched {len(data_dict)} stocks.")
    return data_dict

def get_data(tickers=None, period="1y", interval="1d", force_refresh=False):
    """
    Main entry point for retrieving data. Check cache first, then larger caches, then fetch.
    """
    cache_path = get_cache_path(period)
    
    # 1. Check if exact period cache exists and is valid
    if not force_refresh and is_cache_valid(cache_path):
        data = load_from_cache(period)
        return _prepare_return_data(data, tickers, period, interval)

    # 2. Check if a larger period cache exists and is valid
    if not force_refresh:
        try:
            req_idx = PERIOD_ORDER.index(period)
            # Look at all periods larger than the requested one
            for p in PERIOD_ORDER[req_idx + 1:]:
                larger_path = get_cache_path(p)
                if is_cache_valid(larger_path):
                    print(f"💡 Larger valid cache found ({p}). Slicing for {period}...")
                    data = load_from_cache(p)
                    data = slice_data_dict(data, period)
                    return _prepare_return_data(data, tickers, period, interval)
        except ValueError:
            pass # period not in PERIOD_ORDER

    # 3. Fresh fetch required
    if tickers is None:
        tickers = get_combined_ticker_list()
        
    data = fetch_all_data(tickers, period, interval)
    if data:
        save_to_cache(data, period)
    return data

def _prepare_return_data(data, tickers, period, interval):
    """Helper to filter by tickers and handle missing data."""
    if not tickers:
        return data
        
    filtered_data = {t: data[t] for t in tickers if t in data}
    
    # If we are missing more than 20% of requested tickers, refetch
    missing = set(tickers) - set(data.keys())
    if missing and len(missing) > len(tickers) * 0.2:
        print(f"⚠️ Cache missing {len(missing)} stocks. Refetching...")
        return get_data(tickers, period, interval, force_refresh=True)
    
    return filtered_data

if __name__ == "__main__":
    # Test fetch (first 10 stocks)
    test_tickers = get_combined_ticker_list()[:10]
    data = get_data(test_tickers, force_refresh=False)
    print(f"Read {len(data)} stocks total.")
