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
CACHE_DIR           = "data_cache"
CACHE_EXPIRY_HOURS  = 24
BATCH_SIZE          = 50
BATCH_DELAY         = 1.0
PERIOD_ORDER        = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

# 🗂 STOCK GROUPS
stock_groups = {} # Populated by callers or left empty

# ======================================================
# 📥 SHARED UTILS
# ======================================================

# 🗂 GLOBAL STATE (In-memory cache for speed)
_memory_cache = {} # period -> {ticker: df}

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
        print(f"⚠️ Cache expired for {os.path.basename(cache_path)} ({file_age.total_seconds() / 3600:.1f} hours old, limit: {CACHE_EXPIRY_HOURS}h).")
        return False
    
    # print(f"✅ Cache valid for {os.path.basename(cache_path)} ({file_age.total_seconds() / 3600:.1f} hours old).")
        
    return True

def save_to_cache(data, period):
    path = get_cache_path(period)
    _memory_cache[period] = data # Update memory cache
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    print(f"💾 Data saved to local cache: {path}")

def normalize_df_columns(df):
    """Ensures DF has both standard and lowercase column names."""
    if df is None or df.empty:
        return df
    
    # 1. Handle MultiIndex if present (sometimes happens with yfinance bulk)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[-1] if isinstance(c, tuple) else c for c in df.columns]
    
    # 2. Convert all column names to strings and strip any whitespace
    df.columns = [str(c).strip() for c in df.columns]
    
    # 3. Add lowercase versions and ensure standard names exist
    current_cols = list(df.columns)
    mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'adj close': 'Adj Close'
    }
    
    for col in current_cols:
        l_col = col.lower()
        # Add lowercase version for all
        if l_col not in df.columns:
            df[l_col] = df[col]
        
        # Ensure standard capitalized version exists for core columns
        if l_col in mapping:
            std_col = mapping[l_col]
            if std_col not in df.columns:
                df[std_col] = df[col]
            
    return df

def load_from_cache(period, force_disk=False):
    """Loads data from memory cache if available, otherwise from disk."""
    if not force_disk and period in _memory_cache:
        return _memory_cache[period]
        
    path = get_cache_path(period)
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    # Normalize data on load
    if isinstance(data, dict):
        for ticker in data:
            data[ticker] = normalize_df_columns(data[ticker])
            
    _memory_cache[period] = data # Update memory cache
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
            
        # Ensure columns are normalized before slicing
        df = normalize_df_columns(df)
        
        # Determine the start date for the slice
        last_date = df.index.max()
        
        if period == "1d":
            sliced_dict[ticker] = df.tail(1)
        elif period == "5d":
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
            sliced_dict[ticker] = df
            
    return sliced_dict

# ======================================================
# 📥 DATA FETCHING
# ======================================================

def fetch_all_data(tickers, period="1y", interval="1d"):
    """
    Fetches data for all provided tickers with batching, progress tracking, and retry logic.
    """
    data_dict = {}
    print(f"\n📥 [StockDataManager] Fetching data for {len(tickers)} stocks (Period: {period}, Interval: {interval})...")

    # Use a progress bar for batches
    num_batches = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
    
    with tqdm(total=len(tickers), desc="📥 Downloading Data", unit="stock") as pbar:
        for i in range(0, len(tickers), BATCH_SIZE):
            chunk = tickers[i:i + BATCH_SIZE]
            
            # Retry Logic (2 attempts)
            max_attempts = 3 # 1 initial + 2 retries
            success = False
            for attempt in range(max_attempts):
                try:
                    # Bulk download using yfinance
                    df_bulk = yf.download(
                        chunk, 
                        period=period, 
                        interval=interval, 
                        group_by='ticker', 
                        auto_adjust=False, 
                        actions=False, 
                        threads=True, 
                        progress=False
                    )
                    
                    # Normalize handling for single vs multi-stock chunks
                    if len(chunk) == 1:
                        ticker = chunk[0]
                        if not df_bulk.empty:
                            df_stock = df_bulk.copy()
                            df_stock.dropna(how='all', inplace=True)
                            if not df_stock.empty:
                                data_dict[ticker] = normalize_df_columns(df_stock)
                    else:
                        for ticker in chunk:
                            try:
                                df_stock = df_bulk[ticker].copy()
                                df_stock.dropna(how='all', inplace=True)
                                if not df_stock.empty:
                                    data_dict[ticker] = normalize_df_columns(df_stock)
                            except KeyError:
                                pass
                    
                    success = True
                    break # Success, exit retry loop
                    
                except Exception as e:
                    print(f"⚠️ Attempt {attempt + 1}/{max_attempts} failed for batch {i//BATCH_SIZE + 1}: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(2) # Wait 2 seconds before retry
            
            pbar.update(len(chunk))
            
            # API rate limit safety
            if i + BATCH_SIZE < len(tickers):
                time.sleep(BATCH_DELAY)

    print(f"\n✅ [StockDataManager] Successfully fetched {len(data_dict)} stocks.")
    return data_dict

def get_data(tickers=None, period="1y", interval="1d", force_refresh=False):
    """
    Main entry point for retrieving data. Check current cache, then AGGRESSIVELY 
    slice from larger caches (like 'max'), then fetch missing and update cache.
    """
    cache_path = get_cache_path(period)
    session_data = {}
    
    # 1. Load exact period cache if valid
    if not force_refresh and os.path.exists(cache_path):
        if is_cache_valid(cache_path):
            session_data = load_from_cache(period)
        else:
            print(f"🔍 Cache exists but is invalid/expired for '{period}'.")
    elif force_refresh:
        print(f"🔄 Force refresh requested for '{period}'. Skipping cache.")
    else:
        print(f"📂 No cache file found for '{period}' at {cache_path}")

    # 2. Handle ticker list
    if tickers is None:
        tickers = get_combined_ticker_list()

    # 3. Identify missing tickers for this period
    missing_tickers = [t for t in tickers if t not in session_data]
    
    if not missing_tickers:
        return _prepare_return_data(session_data, tickers, period, interval)

    # 4. AGGRESSIVE SLICING: Check larger caches to fill missing tickers
    try:
        req_idx = PERIOD_ORDER.index(period)
        # Check all periods LARGER than requested, starting from 'max' (end of list)
        for p in reversed(PERIOD_ORDER[req_idx + 1:]):
            if not missing_tickers:
                break
                
            larger_path = get_cache_path(p)
            if os.path.exists(larger_path) and is_cache_valid(larger_path):
                larger_data = load_from_cache(p)
                
                # Extract missing tickers that exist in the larger cache
                found_in_larger = {t: larger_data[t] for t in missing_tickers if t in larger_data}
                if found_in_larger:
                    print(f"💡 Slicing {len(found_in_larger)} tickers from '{p}' cache for '{period}'...")
                    # Slice them to match the requested period
                    sliced_found = slice_data_dict(found_in_larger, period)
                    session_data.update(sliced_found)
                    # Update missing list
                    missing_tickers = [t for t in tickers if t not in session_data]
    except ValueError:
        pass

    # 5. Finally, fetch remaining missing tickers from yfinance
    if missing_tickers:
        print(f"🌐 {len(missing_tickers)} tickers still missing. Downloading from yfinance...")
        new_data = fetch_all_data(missing_tickers, period, interval)
        if new_data:
            session_data.update(new_data)
            # Update disk cache with newly merged data
            save_to_cache(session_data, period)
    elif len(session_data) > 0:
        # If we got everything from larger caches, update the current period cache for future direct access
        save_to_cache(session_data, period)
    
    return _prepare_return_data(session_data, tickers, period, interval)

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
