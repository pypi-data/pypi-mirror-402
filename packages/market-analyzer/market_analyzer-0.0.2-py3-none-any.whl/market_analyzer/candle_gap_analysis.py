#!/usr/bin/env python3

"""
Hard-coded multi-stock candle & gap analysis using yfinance.
Outputs:
 - green/red/doji counts & %
 - gap-up/gap-down based on previous close
 - gap above prev high / below prev low
 - high > open, low < open counts & %
 - sustained gap-up/gap-down %
 - terminal report
 - CSV save
 - visualization save
"""

import os
from datetime import datetime
from . import stock_data_manager
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from tqdm import tqdm
import time
import warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------
# Analysis functions (Parameters are passed from the main runner)
# -------------------------------------------------------------
# -------------------------------------------------------------

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def fetch_data(tickers, period="1mo", interval="1d"):
    data = {}
    print("\nDownloading price data...\n")

    for i, t in enumerate(tqdm(tickers, desc="Fetching", ncols=150)):
        df = yf.download(t, period=period, interval=interval, auto_adjust=False, progress=False, multi_level_index=None, rounding=True)
        if df.empty:
            print(f"⚠ No data for {t}")
        data[t] = df

        if (i + 1) % 10 == 0:
            time.sleep(1) # Reduced delay
    return data

def analyze_df(df):
    if df.empty:
        return df
    
    df = df.copy()

    df["Prev_Close"] = df["Close"].shift(1)
    df["Prev_High"] = df["High"].shift(1)
    df["Prev_Low"] = df["Low"].shift(1)

    # Candle categories
    df["is_green"] = df["Close"] > df["Open"]
    df["is_red"] = df["Close"] < df["Open"]
    df["is_doji"] = df["Close"] == df["Open"]

    # Basic gaps
    df["gap_up_prev_close"] = (df["Open"] > df["Prev_Close"]) & (df["Open"] <= df["Prev_High"])
    df["gap_down_prev_close"] = (df["Open"] < df["Prev_Close"]) & (df["Open"] >= df["Prev_Low"])

    df["gap_above_prev_high"] = df["Open"] > df["Prev_High"]
    df["gap_below_prev_low"] = df["Open"] < df["Prev_Low"]

    # Open = high/low
    df["open_equal_high"] = df["High"] == df["Open"]
    df["open_equal_low"]  = df["Low"]  == df["Open"]

    # Sustained
    df["sustained_gap_up"] = df["gap_up_prev_close"] & (df["Close"] > df["Open"])
    df["sustained_gap_down"] = df["gap_down_prev_close"] & (df["Close"] < df["Open"])

    df = df.dropna(subset=["Prev_Close"])
    return df


def stats(df):
    if df.empty:
        return {}

    total = len(df)
    pct = lambda x: round((x / total) * 100, 2)

    S = {
        "days": total,
        "green": df["is_green"].sum(),
        "red": df["is_red"].sum(),
        "doji": df["is_doji"].sum(),
    }

    S["green_pct"] = pct(S["green"])
    S["red_pct"] = pct(S["red"])
    S["doji_pct"] = pct(S["doji"])

    # Gaps
    S["gap_up"] = df["gap_up_prev_close"].sum()
    S["gap_down"] = df["gap_down_prev_close"].sum()
    S["gap_up_pct"] = pct(S["gap_up"])
    S["gap_down_pct"] = pct(S["gap_down"])

    S["gap_above_prev_high"] = df["gap_above_prev_high"].sum()
    S["gap_below_prev_low"] = df["gap_below_prev_low"].sum()
    S["gap_above_prev_high_pct"] = pct(S["gap_above_prev_high"])
    S["gap_below_prev_low_pct"] = pct(S["gap_below_prev_low"])

    S["open_equal_high"] = df["open_equal_high"].sum()
    S["open_equal_low"] = df["open_equal_low"].sum()
    S["open_equal_high_pct"] = pct(S["open_equal_high"])
    S["open_equal_low_pct"] = pct(S["open_equal_low"])

    S["sustained_gap_up"] = df["sustained_gap_up"].sum()
    S["sustained_gap_down"] = df["sustained_gap_down"].sum()

    S["sustained_gap_up_pct"] = round((S["sustained_gap_up"] / (S["gap_up"] or 1)) * 100, 2)
    S["sustained_gap_down_pct"] = round((S["sustained_gap_down"] / (S["gap_down"] or 1)) * 100, 2)

    return S


# -------------------------------------------------------------
# REPORT PRINTING (NOW OPTIONAL)
# -------------------------------------------------------------
def print_report(ticker, s, enabled=False):
    if not enabled:
        return

    if not s:
        print(f"No data for {ticker}")
        return

    print("\n" + "=" * 60)
    print(f"REPORT → {ticker}")
    print("-" * 60)

    rows = [
        ("Trading days", s["days"]),
        ("Green candles", f'{s["green"]} ({s["green_pct"]}%)'),
        ("Red candles", f'{s["red"]} ({s["red_pct"]}%)'),
        ("Doji", f'{s["doji"]} ({s["doji_pct"]}%)'),

        ("Gap Up (Prev Close)", f'{s["gap_up"]} ({s["gap_up_pct"]}%)'),
        ("Gap Down (Prev Close)", f'{s["gap_down"]} ({s["gap_down_pct"]}%)'),

        ("Gap Above Prev High", f'{s["gap_above_prev_high"]} ({s["gap_above_prev_high_pct"]}%)'),
        ("Gap Below Prev Low", f'{s["gap_below_prev_low"]} ({s["gap_below_prev_low_pct"]}%)'),

        ("Open = High", f'{s["open_equal_high"]} ({s["open_equal_high_pct"]}%)'),
        ("Open = Low", f'{s["open_equal_low"]} ({s["open_equal_low_pct"]}%)'),

        ("Sustained Gap Up", f'{s["sustained_gap_up"]} ({s["sustained_gap_up_pct"]}%)'),
        ("Sustained Gap Down", f'{s["sustained_gap_down"]} ({s["sustained_gap_down_pct"]}%)')
    ]

    print(tabulate(rows, headers=["Metric", "Value"], tablefmt="simple"))
    print("=" * 60)


def save_plot(ticker, s, outpath):
    labels = [
        "Green %", "Red %",
        "Gap Up %", "Gap Above High %",
        "Open = High %", "Open = Low %"
    ]

    values = [
        s["green_pct"], s["red_pct"],
        s["gap_up_pct"], s["gap_above_prev_high_pct"],
        s["open_equal_high_pct"], s["open_equal_low_pct"]
    ]

    plt.figure(figsize=(8, 4))
    bars = plt.bar(labels, values)

    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val}%",
                 ha="center", va="bottom", fontsize=7)

    plt.title(f"{ticker} — Summary Metrics", fontsize=9)
    plt.xticks(rotation=20, fontsize=7)
    plt.yticks(fontsize=7)
    plt.ylim(0, 100)

    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def save_summary_csv(all_stats, outpath):
    df = pd.DataFrame(all_stats)
    df.to_csv(outpath, index=False)
    print(f"Saved summary: {outpath}")


def run(data_dict=None, tickers=None, period="1mo", interval="1d", out_dir="outputs/candle_analysis", save_raw=False, save_plots=False, print_enabled=False):
    ensure_dir(out_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d")

    if data_dict:
        data = data_dict
        tickers_to_process = list(data.keys())
    else:
        tickers_to_process = tickers if tickers else []
        data = fetch_data(tickers_to_process, period=period, interval=interval)

    summary_rows = []

    for t in tqdm(tickers_to_process, desc="Analyzing Candle & Gaps"):
        if t not in data:
            continue
            
        df = data[t]
        if df.empty:
            continue

        analyzed = analyze_df(df)
        stat = stats(analyzed)

        print_report(t, stat, enabled=print_enabled)

        clean_ticker = t.replace(".NS", "")
        row = {"ticker": clean_ticker}
        row.update(stat)
        summary_rows.append(row)

        if save_raw:
            raw_path = os.path.join(out_dir, f"{t.replace('.', '_')}_raw.csv")
            if os.path.exists(raw_path):
                os.remove(raw_path)
            analyzed.to_csv(raw_path)

        if save_plots:
            plot_path = os.path.join(out_dir, f"{t.replace('.', '_')}_plot.png")
            if os.path.exists(plot_path):
                os.remove(plot_path)
            save_plot(t, stat, plot_path)

    summary_path = os.path.join(out_dir, f"aa_summary_candle_gap_{timestamp}.csv")
    save_summary_csv(summary_rows, summary_path)

    print(f"\n✔ Candle Analysis Complete. Results in {out_dir}")

if __name__ == "__main__":
    # Example standalone execution with defaults
    TICKERS = ["RELIANCE.NS", "HDFCBANK.NS"]
    run(tickers=TICKERS)
