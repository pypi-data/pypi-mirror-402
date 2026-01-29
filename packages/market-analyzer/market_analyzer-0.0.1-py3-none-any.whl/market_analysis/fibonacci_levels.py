import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
from mplfinance.original_flavor import candlestick_ohlc
from tqdm import tqdm
from . import stock_data_manager

# -------------------------------------------------------------
# Analysis functions (Parameters are passed from the main runner)
# -------------------------------------------------------------

# ======================================================
# 🔍 Fibonacci Logic
# ======================================================

def detect_best_swing_vectorized(df, window=5):
    """
    Finds significant fractal pivots using vectorized operations.
    """
    if df.empty or len(df) < window * 2 + 10:
        return None, None
    
    lows = df['Low']
    highs = df['High']
    
    # Vectorized Fractal Detection
    # A pivot low is the minimum within a sliding window of (2*window + 1)
    is_pivot_low = (lows == lows.rolling(window=2*window+1, center=True).min())
    is_pivot_high = (highs == highs.rolling(window=2*window+1, center=True).max())
    
    pivot_low_indices = df.index[is_pivot_low].tolist()
    pivot_high_indices = df.index[is_pivot_high].tolist()
    
    pivot_lows = [(idx, lows.iloc[idx]) for idx in pivot_low_indices if idx >= window and idx < len(df)-window]
    pivot_highs = [(idx, highs.iloc[idx]) for idx in pivot_high_indices if idx >= window and idx < len(df)-window]

    if not pivot_lows or not pivot_highs:
        return None, None

    # Identify the "Best" Swing (Most recent major move)
    recent_lows = pivot_lows[-5:]
    recent_highs = pivot_highs[-5:]
    
    best_swing = None
    max_move_pct = 0
    
    for l_idx, l_val in recent_lows:
        for h_idx, h_val in recent_highs:
            move_pct = abs(h_val - l_val) / min(l_val, h_val)
            if move_pct > max_move_pct:
                max_move_pct = move_pct
                is_bullish = l_idx < h_idx
                best_swing = (l_val, l_idx, h_val, h_idx, is_bullish)
    
    return best_swing, {'lows': pivot_lows, 'highs': pivot_highs}

# ======================================================
# 📊 Visualization
# ======================================================


def calculate_fib_levels(low, high, is_bullish, levels=[0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]):
    diff = high - low
    
    if is_bullish:
        # Bullish Swing (Low to High), retracement levels from top down
        # 0% is High, 100% is Low
        return {lvl: high - (lvl * diff) for lvl in levels}
    else:
        # Bearish Swing (High to Low), retracement levels from bottom up
        # 0% is Low, 100% is High
        return {lvl: low + (lvl * diff) for lvl in levels}

def plot_fibonacci(df, symbol, swing_data, all_pivots, fib_levels, out_path):
    low_price, low_idx, high_price, high_idx, is_bullish = swing_data
    
    df_plot = df.copy()
    # Normalize Date for plotting
    if 'Date' not in df_plot.columns:
        df_plot.reset_index(inplace=True)
    
    df_plot['Date_num'] = df_plot['Date'].map(mpl_dates.date2num)
    ohlc = df_plot[['Date_num', 'Open', 'High', 'Low', 'Close']].values

    fig, ax = plt.subplots(figsize=(12, 8))
    candlestick_ohlc(ax, ohlc, width=0.6, colorup='green', colordown='red', alpha=0.8)

    # Plot All Pivots (Subtle)
    for l_idx, l_val in all_pivots['lows']:
        ax.scatter(df_plot.loc[l_idx, 'Date_num'], l_val, color='green', marker='.', alpha=0.3, s=10)
    for h_idx, h_val in all_pivots['highs']:
        ax.scatter(df_plot.loc[h_idx, 'Date_num'], h_val, color='red', marker='.', alpha=0.3, s=10)

    # Highlight Main Swing Impulse
    ax.plot([df_plot.loc[low_idx, 'Date_num'], df_plot.loc[high_idx, 'Date_num']], 
            [low_price, high_price], color='blue', linestyle='-', alpha=0.3, linewidth=2, label='Impulse Leg')

    # Plot Fib Levels
    colors = ['gray', 'orange', 'green', 'blue', 'purple', 'red', 'black']
    for idx, (lvl, val) in enumerate(fib_levels.items()):
        ax.axhline(val, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)
        color = 'blue' if lvl in [0.5, 0.618] else 'black'
        ax.text(df_plot['Date_num'].iloc[-1], val, f" {lvl*100:.1f}% ({val:.2f})", 
                va='center', fontsize=9, color=color, fontweight='bold' if lvl in [0.5, 0.618] else 'normal')

    # Highlight Swing Points
    ax.scatter(df_plot.loc[low_idx, 'Date_num'], low_price, color='green', marker='^', zorder=5)
    ax.scatter(df_plot.loc[high_idx, 'Date_num'], high_price, color='red', marker='v', zorder=5)

    ax.set_title(f"Fibonacci Levels for {symbol} ({'Bullish' if is_bullish else 'Bearish'} Swing)", fontsize=16)
    ax.set_ylabel("Price")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mpl_dates.DateFormatter('%d-%b-%y'))
    plt.xticks(rotation=30)
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    
    plt.savefig(out_path, dpi=150)
    plt.close()

def run_analysis(tickers, data_dict=None, period="1y", interval="1d", near_tolerance=0.01, out_dir="outputs/Fibonacci", fib_levels=[0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0], chart_levels=[0.5, 0.618], print_levels=["50.0%", "61.8%"]):
    os.makedirs(out_dir, exist_ok=True)
    charts_dir = os.path.join(out_dir, "Charts")
    
    # Clear existing charts
    if os.path.exists(charts_dir):
        shutil.rmtree(charts_dir)
    os.makedirs(charts_dir, exist_ok=True)

    if data_dict:
        data_map = data_dict
    else:
        print(f"\n📥 Fetching data for {len(tickers)} stocks...")
        data_map = stock_data_manager.get_data(tickers, period=period, interval=interval)
    
    results = []
    
    for ticker in tqdm(tickers, desc="🔍 Analyzing Fibonacci"):
        if ticker not in data_map:
            continue
            
        df = data_map[ticker].copy()
        if len(df) < 50:
            continue
            
        # Standardize DF
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if 'Date' not in df.columns:
            df.reset_index(inplace=True)

        swing_res = detect_best_swing_vectorized(df)
        if not swing_res or swing_res[0] is None:
            continue
            
        swing, all_pivots = swing_res
        low_p, low_i, high_p, high_i, is_bullish = swing
        calculated_fibs = calculate_fib_levels(low_p, high_p, is_bullish, levels=fib_levels)
        
        ltp = df['Close'].iloc[-1]
        
        # Check if near any major level
        near_lvl = None
        min_dist = float('inf')
        
        for lvl, val in calculated_fibs.items():
            dist = abs(ltp - val) / val
            if dist <= near_tolerance:
                if dist < min_dist:
                    min_dist = dist
                    near_lvl = lvl
        
        if near_lvl is not None:
            clean_ticker = ticker.replace(".NS", "")
            
            # Filter Charts: Only save for specific levels
            if near_lvl in chart_levels:
                chart_filename = f"{clean_ticker}_Fib.png"
                chart_path = os.path.join(charts_dir, chart_filename)
                plot_fibonacci(df, ticker, swing, all_pivots, calculated_fibs, chart_path)
            
            results.append({
                "Stock": clean_ticker,
                "LTP": round(ltp, 2),
                "Swing Type": "Bullish" if is_bullish else "Bearish",
                "Near Level": f"{near_lvl*100:.1f}%",
                "Level Price": round(calculated_fibs[near_lvl], 2),
                "Dist %": round(min_dist * 100, 2),
            })

    if results:
        from prettytable import PrettyTable
        table = PrettyTable()
        table.field_names = ["Stock", "LTP", "Swing", "Near Level", "Dist %"]
        
        filtered_for_print = [r for r in results if r['Near Level'] in print_levels]
        
        for r in filtered_for_print[:30]: 
            table.add_row([r['Stock'], r['LTP'], r['Swing Type'], r['Near Level'], r['Dist %']])
            
        if table.rows:
            print(f"\n📊 Stocks Near Key Levels ({print_levels}):")
            print(table)

        # Save to CSV
        res_df = pd.DataFrame(results)
        csv_path = os.path.join(out_dir, "Fibonacci_Results.csv")
        try:
            res_df.to_csv(csv_path, index=False)
            print(f"\n✅ Fibonacci complete! Results in: {out_dir}")
        except PermissionError:
            print(f"\n⚠️  Permission Denied: Could not save '{csv_path}'.")
    else:
        print("\n❌ No stocks found near key Fibonacci levels.")

if __name__ == "__main__":
    # Example standalone execution
    TICKERS = ["RELIANCE.NS", "HDFCBANK.NS"]
    run_analysis(TICKERS)
