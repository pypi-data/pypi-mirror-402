import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import asyncio
import warnings
import os
import time
from tqdm import tqdm
import json
import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials

warnings.filterwarnings('ignore')

from . import stock_data_manager


# --- DATA STRUCTURES (UNCHANGED) ---
class Alerts:
    def __init__(self):
        self.internal_bullish_bos = False
        self.internal_bearish_bos = False
        self.internal_bullish_choch = False
        self.internal_bearish_choch = False
        self.swing_bullish_bos = False
        self.swing_bearish_bos = False
        self.swing_bullish_choch = False
        self.swing_bearish_choch = False
        self.internal_bullish_order_block = False
        self.internal_bearish_order_block = False
        self.swing_bullish_order_block = False
        self.swing_bearish_order_block = False
        self.equal_highs = False
        self.equal_lows = False
        self.bullish_fair_value_gap = False
        self.bearish_fair_value_gap = False
        self.current_candle_swing_bullish_bos = False
        self.current_candle_swing_bearish_bos = False
        self.current_candle_swing_bullish_choch = False
        self.current_candle_swing_bearish_choch = False
        self.current_candle_internal_bullish_bos = False
        self.current_candle_internal_bearish_bos = False
        self.current_candle_internal_bullish_choch = False
        self.current_candle_internal_bearish_choch = False

class TrailingExtremes:
    def __init__(self):
        self.top = None
        self.bottom = None
        self.bar_time = None
        self.bar_index = None
        self.last_top_time = None
        self.last_bottom_time = None

class FairValueGap:
    def __init__(self, top: float, bottom: float, bias: int, start_time: int = None,
                 end_time: int = None, start_idx: int = None, width: int = 0):
        self.top = top
        self.bottom = bottom
        self.bias = bias
        self.start_time = start_time
        self.end_time = end_time
        self.start_idx = start_idx
        self.width = width
        self.top_box = None
        self.bottom_box = None

class Trend:
    def __init__(self, bias: int = 0):
        self.bias = bias

class EqualDisplay:
    def __init__(self):
        self.line = None
        self.label = None

class Pivot:
    def __init__(self, current_level: float = None, last_level: float = None,
                 crossed: bool = False, bar_time: int = None, bar_index: int = None):
        self.current_level = current_level
        self.last_level = last_level
        self.crossed = crossed
        self.bar_time = bar_time
        self.bar_index = bar_index

class OrderBlock:
    def __init__(self, bar_high: float, bar_low: float, bar_time: int, bias: int, start_idx: int = None, break_idx: int = None):
        self.bar_high = bar_high
        self.bar_low = bar_low
        self.bar_time = bar_time
        self.bias = bias
        self.start_idx = start_idx
        self.break_idx = break_idx
        self.mitigation_idx = -1

class SmartMoneyConcepts:
    def __init__(self, stock_code: str, period: str = "1y", interval: str = "1d", auto_adjust: bool =False, 
                 print_details: bool = True, fetch_csv_data: bool = False, csv_path: str = None,
                 column_mapping: dict = None, df: pd.DataFrame = None):
        """Smart Money Concepts Indicator - Python Implementation.

        Args:
            stock_code (str): Stock ticker symbol (e.g., 'RELIANCE.NS' for NSE).
            period (str): Period for yfinance data (e.g., '1y' for 1 year).
            interval (str): Interval for yfinance data (e.g., '1d' for daily).
            print_details (bool): Whether to print detailed analysis logs.
            fetch_csv_data (bool): If True, fetch data from CSV instead of yfinance.
            csv_path (str): Path to CSV file containing OHLCV data.
            column_mapping (dict, optional): Custom column mapping for renaming DataFrame columns.
            df (pd.DataFrame, optional): Pre-fetched DataFrame.
        """
        self.stock_code = stock_code
        self.period = period
        self.interval = interval
        self.auto_adjust = auto_adjust
        self.print_details = print_details
        self.fetch_csv_data = fetch_csv_data
        self.csv_path = csv_path
        self.column_mapping = column_mapping

        # Initialize data containers
        self.df = df
        self.ohlcv_data = None

        # Initialize the indicator
        self.setup_constants()
        self.setup_variables()

    def setup_constants(self):
        self.BULLISH_LEG = 1
        self.BEARISH_LEG = 0
        self.BULLISH = 1
        self.BEARISH = -1
        self.GREEN = '#089981'
        self.RED = '#F23645'
        self.BLUE = '#2157f3'
        self.GRAY = '#878b94'
        self.MONO_BULLISH = '#b2b5be'
        self.MONO_BEARISH = '#5d606b'
        self.HISTORICAL = 'Historical'
        self.PRESENT = 'Present'
        self.COLORED = 'Colored'
        self.MONOCHROME = 'Monochrome'
        self.ALL = 'All'
        self.BOS = 'BOS'
        self.CHOCH = 'CHOCH'
        self.ATR = 'Atr'
        self.RANGE = 'Cumulative Mean Range'
        self.CLOSE = 'Close'
        self.HIGHLOW = 'High/Low'
        self.mode_input = self.HISTORICAL
        self.style_input = self.COLORED
        self.show_trend_input = False
        self.show_internals_input = True
        self.show_internal_bull_input = self.ALL
        self.internal_bull_color_input = self.GREEN
        self.show_internal_bear_input = self.ALL
        self.internal_bear_color_input = self.RED
        self.internal_filter_confluence_input = False
        self.show_structure_input = True
        self.show_swing_bull_input = self.ALL
        self.swing_bull_color_input = self.GREEN
        self.show_swing_bear_input = self.ALL
        self.swing_bear_color_input = self.RED
        self.show_swings_input = False
        self.swings_length_input = 50
        self.show_high_low_swings_input = True
        self.show_internal_order_blocks_input = True
        self.internal_order_blocks_size_input = 5
        self.show_swing_order_blocks_input = True
        self.swing_order_blocks_size_input = 5
        self.order_block_filter_input = self.ATR
        self.order_block_mitigation_input = self.HIGHLOW
        self.internal_bullish_order_block_color = "#3179f580"
        self.internal_bearish_order_block_color = "#f77c8080"
        self.swing_bullish_order_block_color = "#1848cc80"
        self.swing_bearish_order_block_color = "#b2283380"
        self.show_equal_highs_lows_input = True
        self.equal_highs_lows_length_input = 3
        self.equal_highs_lows_threshold_input = 0.1
        self.show_fair_value_gaps_input = True
        self.fair_value_gaps_threshold_input = True
        self.fair_value_gaps_timeframe_input = ''
        self.fair_value_gaps_bull_color_input = "#00ff6870"
        self.fair_value_gaps_bear_color_input = "#ff000870"
        self.fair_value_gaps_extend_input = 5
        self.show_premium_discount_zones_input = True
        self.premium_zone_color_input = self.RED
        self.equilibrium_zone_color_input = self.GRAY
        self.discount_zone_color_input = self.GREEN

    def setup_variables(self):
        self.parsed_highs = []
        self.parsed_lows = []
        self.highs = []
        self.lows = []
        self.times = []
        self.swing_high = Pivot()
        self.swing_low = Pivot()
        self.internal_high = Pivot()
        self.internal_low = Pivot()
        self.equal_high = Pivot()
        self.equal_low = Pivot()
        self.swing_trend = Trend(0)
        self.internal_trend = Trend(0)
        self.equal_high_display = EqualDisplay()
        self.equal_low_display = EqualDisplay()
        self.fair_value_gaps = []
        self.swing_order_blocks = []
        self.internal_order_blocks = []
        self.trailing = TrailingExtremes()
        self.current_bar_index = 0
        self.last_bar_index = 0
        self.current_alerts = Alerts()
        self.initial_time = None
        self.swing_bullish_color = self.MONO_BULLISH if self.style_input == self.MONOCHROME else self.swing_bull_color_input
        self.swing_bearish_color = self.MONO_BEARISH if self.style_input == self.MONOCHROME else self.swing_bear_color_input
        self.fair_value_gap_bullish_color = f"{self.MONO_BULLISH}70" if self.style_input == self.MONOCHROME else self.fair_value_gaps_bull_color_input
        self.fair_value_gap_bearish_color = f"{self.MONO_BEARISH}70" if self.style_input == self.MONOCHROME else self.fair_value_gaps_bear_color_input
        self.premium_zone_color = self.MONO_BEARISH if self.style_input == self.MONOCHROME else self.premium_zone_color_input
        self.discount_zone_color = self.MONO_BULLISH if self.style_input == self.MONOCHROME else self.discount_zone_color_input

    def fetch_ohlcv_sync(self, column_mapping=None):
        """Synchronous version of fetch_ohlcv for parallel processing."""
        if self.df is not None:
            self.ohlcv_data = self.df[['open', 'high', 'low', 'close']].copy()
            return True
        # Original logic omitted for brevity as we always use pre-fetched DataFrames now
        return False

    async def fetch_ohlcv(self, column_mapping=None):
        """Fetch OHLCV data from yfinance or CSV."""
        if self.df is not None:
            # Already have data (likely from pre-fetch)
            self.ohlcv_data = self.df[['open', 'high', 'low', 'close']].copy()
            return True
        
        try:
            # Default column mapping for yfinance
            default_yfinance_mapping = {
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close'
            }
            # Use provided column_mapping or fallback to default
            active_mapping = column_mapping or default_yfinance_mapping
            # Determine the date column name for CSV parsing
            date_column = next((k for k, v in active_mapping.items() if v == 'Date'), None) if column_mapping else None

            if self.fetch_csv_data:
                if not self.csv_path or not os.path.exists(self.csv_path):
                    if self.print_details:
                        print(f"CSV file not found at {self.csv_path}")
                    return False
                if self.print_details:
                    print(f"Fetching data for {self.stock_code} from CSV at {self.csv_path}...")
                # Use the date column from mapping (e.g., 'DATE1') for parsing
                parse_dates = [date_column] if date_column else False
                self.df = pd.read_csv(self.csv_path, parse_dates=parse_dates)
                if date_column in self.df.columns:
                    self.df.set_index(date_column, inplace=True)
                    # Remove date_column from mapping to avoid duplicate renaming
                    active_mapping = {k: v for k, v in active_mapping.items() if v != 'Date'}
                else:
                    self.df.index = pd.to_datetime(self.df.index)
            else:
                if self.print_details:
                    print(f"Fetching data for {self.stock_code} using yfinance...")
                ticker = yf.Ticker(self.stock_code)
                self.df = ticker.history(period=self.period, interval=self.interval , auto_adjust=self.auto_adjust)
                self.df.index = pd.to_datetime(self.df.index)

            required_columns = [k for k, v in active_mapping.items() if v in ['open', 'high', 'low', 'close']]
            if not all(col in self.df.columns for col in required_columns):
                if self.print_details:
                    print(f"Data for {self.stock_code} missing required columns: {required_columns}")
                return False

            self.df = self.df.rename(columns=active_mapping)
            self.df = self.df.sort_index()
            self.df = self.df.dropna(subset=['open', 'high', 'low', 'close'])
            self.ohlcv_data = self.df[['open', 'high', 'low', 'close']].copy()
            if self.print_details:
                print(f"Successfully fetched {len(self.df)} bars")
                print(f"Data range: {self.df.index[0].date()} to {self.df.index[-1].date()}")
            return True
        except Exception as e:
            if self.print_details:
                print(f"Error fetching data for {self.stock_code}: {e}")
            return False

    def prepare_data(self):
        if self.df is None:
            raise ValueError("No data available. Please fetch data first.")
        
        # Vectorized volatility and parsing
        self.df['tr'] = np.maximum(
            self.df['high'] - self.df['low'],
            np.maximum(
                abs(self.df['high'] - self.df['close'].shift(1)),
                abs(self.df['low'] - self.df['close'].shift(1))
            )
        )
        self.df['atr'] = self.df['tr'].rolling(window=200, min_periods=1).mean()
        self.df['volatility_measure'] = self.df['atr'] if self.order_block_filter_input == self.ATR else self.df['tr'].expanding().mean()
        self.df['high_volatility_bar'] = (self.df['high'] - self.df['low']) >= (2 * self.df['volatility_measure'])
        self.df['parsed_high'] = np.where(self.df['high_volatility_bar'], self.df['low'], self.df['high'])
        self.df['parsed_low'] = np.where(self.df['high_volatility_bar'], self.df['high'], self.df['low'])
        
        # Store as numpy arrays for speed
        self.highs = self.df['high'].values
        self.lows = self.df['low'].values
        self.closes = self.df['close'].values
        self.opens = self.df['open'].values
        self.atrs = self.df['atr'].values
        self.parsed_highs = self.df['parsed_high'].values
        self.parsed_lows = self.df['parsed_low'].values
        self.times = self.df.index.values
        self.initial_time = self.times[0]
        
        # Pre-calculate legs for all relevant sizes
        self.all_legs = {}
        target_sizes = [self.swings_length_input, 5]
        if self.show_equal_highs_lows_input:
            target_sizes.append(self.equal_highs_lows_length_input)
        
        for size in set(target_sizes):
            self.all_legs[size] = self.calculate_all_legs_vectorized(size)

        # Pre-detect FVGs and their mitigation
        self.precompute_fvgs()

        # Pre-calculate confluence bars
        max_co = np.maximum(self.closes, self.opens)
        min_co = np.minimum(self.closes, self.opens)
        if self.internal_filter_confluence_input:
            self.bullish_bars = (self.highs - max_co) > np.minimum(self.closes, self.opens - self.lows)
            self.bearish_bars = (self.highs - max_co) < np.minimum(self.closes, self.opens - self.lows)
        else:
            self.bullish_bars = np.ones(len(self.highs), dtype=bool)
            self.bearish_bars = np.ones(len(self.highs), dtype=bool)

        # Vectorize trailing extremes
        self.df['trailing_top'] = self.df['high'].cummax()
        self.df['trailing_bottom'] = self.df['low'].cummin()
        self.trailing_tops = self.df['trailing_top'].values
        self.trailing_bottoms = self.df['trailing_bottom'].values
        
        # Vectorize PD zones
        top = self.trailing_tops
        bot = self.trailing_bottoms
        self.pd_zones = {
            'premium': {'top': top, 'bottom': 0.95 * top + 0.05 * bot},
            'equilibrium': {'top': 0.525 * top + 0.475 * bot, 'bottom': 0.525 * bot + 0.475 * top},
            'discount': {'top': 0.95 * bot + 0.05 * top, 'bottom': bot}
        }

        if self.print_details:
            print("Data preparation completed")

    def detect_fair_value_gaps_vectorized(self):
        """Pre-detects all potential FVGs across the entire history."""
        n = len(self.highs)
        if n < 3:
            return np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)
            
        threshold = 0.002
        bar_delta_pct = (self.closes - self.opens) / np.where(self.opens != 0, self.opens, np.nan)
        
        # Values shifted to compare against current i
        last2_highs = np.roll(self.highs, 2)
        last2_lows = np.roll(self.lows, 2)
        last_closes = np.roll(self.closes, 1)
        last_delta_pct = np.roll(bar_delta_pct, 1)
        
        bullish_mask = (self.lows > last2_highs) & (last_closes > last2_highs) & (last_delta_pct > threshold)
        bearish_mask = (self.highs < last2_lows) & (last_closes < last2_lows) & (-last_delta_pct > threshold)
        
        # Zero out the first 2 bars as they can't have FVGs
        bullish_mask[:2] = False
        bearish_mask[:2] = False
        
        return bullish_mask, bearish_mask

    def precompute_fvgs(self):
        """Precomputes all FVGs and their mitigation indices."""
        fvg_bullish_mask, fvg_bearish_mask = self.detect_fair_value_gaps_vectorized()
        self.fvg_bullish_mask = fvg_bullish_mask
        self.fvg_bearish_mask = fvg_bearish_mask
        self.fvg_creation_events = {} # index -> list of FVG objects
        self.fvg_mitigation_events = {} # index -> list of FVG objects
        
        # Bullish FVGs
        bull_indices = np.where(self.fvg_bullish_mask)[0]
        for idx in bull_indices:
            top = self.lows[idx]
            bottom = self.highs[idx-2]
            # Mitigation: low falls below fvg bottom
            mitigated_at = np.where(self.lows[idx:] < bottom)[0]
            if len(mitigated_at) > 0:
                mitigation_idx = idx + mitigated_at[0]
            else:
                mitigation_idx = -1
            
            fvg = FairValueGap(
                top=top, bottom=bottom, bias=self.BULLISH,
                start_time=self.times[idx-1], end_time=self.times[idx] + self.fair_value_gaps_extend_input,
                start_idx=idx-1, width=self.fair_value_gaps_extend_input + 1
            )
            fvg.mitigation_idx = mitigation_idx
            
            if idx not in self.fvg_creation_events: self.fvg_creation_events[idx] = []
            self.fvg_creation_events[idx].append(fvg)
            if mitigation_idx != -1:
                if mitigation_idx not in self.fvg_mitigation_events: self.fvg_mitigation_events[mitigation_idx] = []
                self.fvg_mitigation_events[mitigation_idx].append(fvg)
        
        # Bearish FVGs
        bear_indices = np.where(self.fvg_bearish_mask)[0]
        for idx in bear_indices:
            top = self.lows[idx-2]
            bottom = self.highs[idx]
            # Mitigation: high rises above fvg top
            mitigated_at = np.where(self.highs[idx:] > top)[0]
            if len(mitigated_at) > 0:
                mitigation_idx = idx + mitigated_at[0]
            else:
                mitigation_idx = -1
            
            fvg = FairValueGap(
                top=top, bottom=bottom, bias=self.BEARISH,
                start_time=self.times[idx-1], end_time=self.times[idx] + self.fair_value_gaps_extend_input,
                start_idx=idx-1, width=self.fair_value_gaps_extend_input + 1
            )
            fvg.mitigation_idx = mitigation_idx
            
            if idx not in self.fvg_creation_events: self.fvg_creation_events[idx] = []
            self.fvg_creation_events[idx].append(fvg)
            if mitigation_idx != -1:
                if mitigation_idx not in self.fvg_mitigation_events: self.fvg_mitigation_events[mitigation_idx] = []
                self.fvg_mitigation_events[mitigation_idx].append(fvg)

        return fvg_bullish_mask, fvg_bearish_mask

    def compute_structure_vectorized(self, size: int, internal: bool = False):
        """Highly optimized structure detection using segments between pivots."""
        n = len(self.highs)
        legs = self.all_legs[size]
        diffs = np.diff(legs)
        pivot_indices = np.where(diffs != 0)[0] + 1
        
        # Initial state
        bias = 0
        active_high = None
        active_low = None
        
        breaks = []
        pivots = [] # List of (bar_index, type, level, time)
        
        # Precompute swing levels if this is internal structure
        active_swing_high_levels = None
        active_swing_low_levels = None
        if internal and hasattr(self, 'swing_pivots_indexed'):
            active_swing_high_levels = np.zeros(n)
            active_swing_low_levels = np.zeros(n)
            curr_sh = 0
            curr_sl = 0
            for i in range(n):
                if i in self.swing_pivots_indexed['high']: curr_sh = self.swing_pivots_indexed['high'][i]
                if i in self.swing_pivots_indexed['low']: curr_sl = self.swing_pivots_indexed['low'][i]
                active_swing_high_levels[i] = curr_sh
                active_swing_low_levels[i] = curr_sl

        # We also need to track pivots bar-by-bar for display/OB logic
        # But we can do it more efficiently by just iterating through pivot_indices
        pivot_map = {idx: ('low' if legs[idx]-legs[idx-1] == 1 else 'high') for idx in pivot_indices}
        
        # Main structure logic
        last_pivot_idx = 0
        for i in range(n):
            # 1. Update active pivots
            if i in pivot_map:
                p_type = pivot_map[i]
                if i >= size:
                    val = self.lows[i-size] if p_type == 'low' else self.highs[i-size]
                    p_idx = i - size
                    pivots.append({'index': p_idx, 'type': p_type, 'level': val, 'time': self.times[p_idx]})
                    if p_type == 'low':
                        active_low = {'level': val, 'index': p_idx, 'time': self.times[p_idx], 'crossed': False}
                    else:
                        active_high = {'level': val, 'index': p_idx, 'time': self.times[p_idx], 'crossed': False}

            # 2. Check for breaks
            # Optimization: only check if we have active pivots and NOT yet crossed
            if active_high and not active_high['crossed']:
                extra_bull = True
                if internal and active_swing_high_levels is not None:
                    extra_bull = (active_high['level'] != active_swing_high_levels[i] and self.bullish_bars[i])
                
                if self.closes[i] > active_high['level'] and extra_bull:
                    if i > 0 and self.closes[i-1] <= active_high['level']:
                        tag = self.CHOCH if bias != self.BULLISH else self.BOS
                        bias = self.BULLISH
                        active_high['crossed'] = True
                        breaks.append({
                            'type': tag, 'direction': 'bullish', 'internal': internal,
                            'price': active_high['level'], 'time': active_high['time'],
                            'bar_index': active_high['index'], 'break_time': self.times[i],
                            'break_bar_index': i,
                            'current_candle': i == n - 1
                        })

            if active_low and not active_low['crossed']:
                extra_bear = True
                if internal and active_swing_low_levels is not None:
                    extra_bear = (active_low['level'] != active_swing_low_levels[i] and self.bearish_bars[i])

                if self.closes[i] < active_low['level'] and extra_bear:
                    if i > 0 and self.closes[i-1] >= active_low['level']:
                        tag = self.CHOCH if bias != self.BEARISH else self.BOS
                        bias = self.BEARISH
                        active_low['crossed'] = True
                        breaks.append({
                            'type': tag, 'direction': 'bearish', 'internal': internal,
                            'price': active_low['level'], 'time': active_low['time'],
                            'bar_index': active_low['index'], 'break_time': self.times[i],
                            'break_bar_index': i, 'current_candle': i == n - 1
                        })
                        
        return pivots, breaks, bias

    def run_smc_analysis(self):
        """Optimized SMC analysis without the heavy per-bar loop."""
        if self.print_details:
            print("Running Optimized Smart Money Concepts analysis...")
        
        # 1. Structure Analysis (Vectorized-ish)
        # Swing Structure
        swing_pivots, self.swing_breaks, self.swing_trend.bias = self.compute_structure_vectorized(self.swings_length_input, internal=False)
        
        # Index swing pivots for internal structure check
        self.swing_pivots_indexed = {'high': {}, 'low': {}}
        for p in swing_pivots:
            self.swing_pivots_indexed[p['type']][p['index']] = p['level']
            
        # Internal Structure
        internal_pivots, self.internal_breaks, self.internal_trend.bias = self.compute_structure_vectorized(5, internal=True)
        
        # Equal Highs/Lows
        equal_pivots, _, _ = self.compute_structure_vectorized(self.equal_highs_lows_length_input, internal=False)
        self.equal_structures = []
        # We need to compare consecutive pivots of the SAME type.
        # High pivots comparison
        curr_high_pivots = [p for p in equal_pivots if p['type'] == 'high']
        for i in range(1, len(curr_high_pivots)):
            p1 = curr_high_pivots[i-1]
            p2 = curr_high_pivots[i]
            atr_val = self.atrs[p2['index']]
            if abs(p1['level'] - p2['level']) < self.equal_highs_lows_threshold_input * atr_val:
                self.equal_structures.append({
                    'type': 'EQH',
                    'start_time': p1['time'], 'start_level': p1['level'],
                    'end_time': p2['time'], 'end_level': p2['level'],
                    'end_idx': p2['index'],
                    'color': self.swing_bearish_color
                })
                
        # Low pivots comparison
        curr_low_pivots = [p for p in equal_pivots if p['type'] == 'low']
        for i in range(1, len(curr_low_pivots)):
            p1 = curr_low_pivots[i-1]
            p2 = curr_low_pivots[i]
            atr_val = self.atrs[p2['index']]
            if abs(p1['level'] - p2['level']) < self.equal_highs_lows_threshold_input * atr_val:
                self.equal_structures.append({
                    'type': 'EQL',
                    'start_time': p1['time'], 'start_level': p1['level'],
                    'end_time': p2['time'], 'end_level': p2['level'],
                    'end_idx': p2['index'],
                    'color': self.swing_bullish_color
                })
        
        # Combine all structure breaks
        self.structure_breaks = self.swing_breaks + self.internal_breaks
        
        # 2. Final State Setup (for backward compatibility and alerts)
        if swing_pivots:
            h_pivots = [p for p in swing_pivots if p['type'] == 'high']
            l_pivots = [p for p in swing_pivots if p['type'] == 'low']
            if h_pivots:
                self.swing_high.current_level = h_pivots[-1]['level']
                self.swing_high.bar_index = h_pivots[-1]['index']
                self.swing_high.bar_time = h_pivots[-1]['time']
            if l_pivots:
                self.swing_low.current_level = l_pivots[-1]['level']
                self.swing_low.bar_index = l_pivots[-1]['index']
                self.swing_low.bar_time = l_pivots[-1]['time']

        if internal_pivots:
            h_pivots = [p for p in internal_pivots if p['type'] == 'high']
            l_pivots = [p for p in internal_pivots if p['type'] == 'low']
            if h_pivots:
                self.internal_high.current_level = h_pivots[-1]['level']
                self.internal_high.bar_index = h_pivots[-1]['index']
                self.internal_high.bar_time = h_pivots[-1]['time']
            if l_pivots:
                self.internal_low.current_level = l_pivots[-1]['level']
                self.internal_low.bar_index = l_pivots[-1]['index']
                self.internal_low.bar_time = l_pivots[-1]['time']

        # 3. Order Blocks (Precompute from breaks)
        self.swing_order_blocks = []
        self.internal_order_blocks = []
        
        for brk in self.structure_breaks:
            self.store_order_block_from_break(brk)
            
        # Calculate trailing extremes (Matches old code's swing-based reset logic)
        # The old code resets trailing.top whenever a new swing_high is confirmed.
        # Since we have the final pivots, trailing.top is max(latest_swing_high, highs since then)
        h_pivots_swing = [p for p in swing_pivots if p['type'] == 'high']
        l_pivots_swing = [p for p in swing_pivots if p['type'] == 'low']

        if h_pivots_swing:
            last_h_idx = h_pivots_swing[-1]['index']
            self.trailing.top = np.max(self.highs[last_h_idx:])
            self.trailing.last_top_time = self.times[last_h_idx + np.argmax(self.highs[last_h_idx:])]
        else:
            self.trailing.top = np.max(self.highs) if len(self.highs) > 0 else None
            
        if l_pivots_swing:
            last_l_idx = l_pivots_swing[-1]['index']
            self.trailing.bottom = np.min(self.lows[last_l_idx:])
            self.trailing.last_bottom_time = self.times[last_l_idx + np.argmin(self.lows[last_l_idx:])]
        else:
            self.trailing.bottom = np.min(self.lows) if len(self.lows) > 0 else None

        # 4. Mitigation and Alerts
        # For the final results, we filter final FVGs and OBs
        # The old code keeps historic ones until they are mitigated.
        # We'll populate self.fair_value_gaps from the precomputed ones.
        self.fair_value_gaps = []
        last_idx = len(self.highs) - 1
        
        # In the old code, fair_value_gaps list only has unmitigated ones.
        # Mitigation for FVG is always on WICK (High/Low)
        for idx, fvgs in self.fvg_creation_events.items():
            for fvg in fvgs:
                if fvg.mitigation_idx == -1 or fvg.mitigation_idx > last_idx:
                    self.fair_value_gaps.insert(0, fvg)
        
        # Similarly, filter active OBs for the final state
        # Mitigation for OB is on CLOSE by default in the old code
        if self.order_block_mitigation_input == self.CLOSE:
            # Re-calculate mitigation for all OBs using CLOSE
            for ob in self.swing_order_blocks + self.internal_order_blocks:
                if ob.break_idx is None: continue
                end_idx = ob.break_idx
                if ob.bias == self.BULLISH:
                    mit = np.where(self.df['close'].values[end_idx:] < ob.bar_low)[0]
                else:
                    mit = np.where(self.df['close'].values[end_idx:] > ob.bar_high)[0]
                
                if len(mit) > 0:
                    ob.mitigation_idx = end_idx + mit[0]
                else:
                    ob.mitigation_idx = -1
        
        self.filter_active_order_blocks(last_idx)
        
        # Apply 100-limit to active blocks (matching old code's active list limit)
        self.swing_order_blocks = self.swing_order_blocks[:100]
        self.internal_order_blocks = self.internal_order_blocks[:100]
        
        # Calculate premium/discount zones based on final trailing extremes
        if self.show_premium_discount_zones_input:
            if self.trailing.top is not None and self.trailing.bottom is not None:
                premium_top = self.trailing.top
                premium_bottom = 0.95 * self.trailing.top + 0.05 * self.trailing.bottom
                equilibrium_top = 0.525 * self.trailing.top + 0.475 * self.trailing.bottom
                equilibrium_bottom = 0.525 * self.trailing.bottom + 0.475 * self.trailing.top
                discount_top = 0.95 * self.trailing.bottom + 0.05 * self.trailing.top
                discount_bottom = self.trailing.bottom
                self.premium_discount_zones = {
                    'premium': {'top': premium_top, 'bottom': premium_bottom},
                    'equilibrium': {'top': equilibrium_top, 'bottom': equilibrium_bottom},
                    'discount': {'top': discount_top, 'bottom': discount_bottom}
                }
            else:
                self.premium_discount_zones = None

        # 5. Final Alerts (for the last candle)
        self.update_final_alerts(last_idx)

        if self.print_details:
            print("Smart Money Concepts analysis completed!")
            sh = self.swing_high.current_level if self.swing_high.current_level else 0
            sl = self.swing_low.current_level if self.swing_low.current_level else 0
            print(f"Swing high: {sh:.2f}")
            print(f"Swing low: {sl:.2f}")
            print(f"Structure breaks: {len(self.structure_breaks)}")
            print(f"Order blocks: {len(self.internal_order_blocks) + len(self.swing_order_blocks)}")

    def store_order_block_from_break(self, brk):
        start_idx = brk['bar_index']
        end_idx = brk['break_bar_index']
        bias = self.BULLISH if brk['direction'] == 'bullish' else self.BEARISH
        
        if start_idx < end_idx and end_idx < len(self.parsed_highs):
            if bias == self.BEARISH:
                array_slice = self.parsed_highs[start_idx:end_idx]
                max_idx = np.argmax(array_slice)
                parsed_index = start_idx + max_idx
            else:
                array_slice = self.parsed_lows[start_idx:end_idx]
                min_idx = np.argmin(array_slice)
                parsed_index = start_idx + min_idx
            
            ob = OrderBlock(
                bar_high=self.parsed_highs[parsed_index],
                bar_low=self.parsed_lows[parsed_index],
                bar_time=self.times[parsed_index],
                bias=bias,
                start_idx=parsed_index,
                break_idx=end_idx
            )
            # Mitigation
            # Old code uses CLOSE for mitigation by default in delete_order_blocks_bar if set
            if self.order_block_mitigation_input == self.CLOSE:
                mit_source = self.df['close'].values
            else:
                mit_source = self.lows if bias == self.BULLISH else self.highs

            if bias == self.BULLISH:
                mit = np.where(mit_source[end_idx:] < ob.bar_low)[0]
            else:
                mit = np.where(mit_source[end_idx:] > ob.bar_high)[0]
            
            ob.mitigation_idx = end_idx + mit[0] if len(mit) > 0 else -1
            
            # We keep ALL order blocks for consistency with old code, 
            # and filter/limit at the end in run_smc_analysis
            order_blocks = self.internal_order_blocks if brk['internal'] else self.swing_order_blocks
            order_blocks.insert(0, ob)

    def filter_active_order_blocks(self, last_idx):
        self.internal_order_blocks = [ob for ob in self.internal_order_blocks if ob.mitigation_idx == -1 or ob.mitigation_idx > last_idx]
        self.swing_order_blocks = [ob for ob in self.swing_order_blocks if ob.mitigation_idx == -1 or ob.mitigation_idx > last_idx]

    def update_final_alerts(self, last_idx):
        # Check alerts for the last index
        # This replicates the logic of what alert would be triggered on the latest candle
        for brk in self.structure_breaks:
            if brk['break_bar_index'] == last_idx:
                dir = brk['direction']
                int = brk['internal']
                type = brk['type']
                if int:
                    if dir == 'bullish':
                        if type == 'CHOCH': self.current_alerts.current_candle_internal_bullish_choch = True
                        else: self.current_alerts.current_candle_internal_bullish_bos = True
                    else:
                        if type == 'CHOCH': self.current_alerts.current_candle_internal_bearish_choch = True
                        else: self.current_alerts.current_candle_internal_bearish_bos = True
                else:
                    if dir == 'bullish':
                        if type == 'CHOCH': self.current_alerts.current_candle_swing_bullish_choch = True
                        else: self.current_alerts.current_candle_swing_bullish_bos = True
                    else:
                        if type == 'CHOCH': self.current_alerts.current_candle_swing_bearish_choch = True
                        else: self.current_alerts.current_candle_swing_bearish_bos = True
        
        # FVG alerts for last candle
        if last_idx in self.fvg_creation_events:
            for fvg in self.fvg_creation_events[last_idx]:
                if fvg.bias == self.BULLISH: self.current_alerts.bullish_fair_value_gap = True
                else: self.current_alerts.bearish_fair_value_gap = True

        # OB alerts (mitigation)
        for ob in self.internal_order_blocks + self.swing_order_blocks:
            if ob.mitigation_idx == last_idx:
                bias = ob.bias
                # Determine if it was internal or swing (simplified, could be more precise)
                if bias == 'BEARISH': self.current_alerts.internal_bearish_order_block = True
                else: self.current_alerts.internal_bullish_order_block = True
        
        # Equal structure alerts
        if hasattr(self, 'equal_structures'):
            for eq in self.equal_structures:
                if eq['end_idx'] == last_idx:
                    if eq['type'] == 'EQH': self.current_alerts.equal_highs = True
                    else: self.current_alerts.equal_lows = True

    def calculate_all_legs_vectorized(self, size: int) -> np.ndarray:
        """Calculates all legs for a given size using vectorized operations."""
        n = len(self.highs)
        legs = np.zeros(n, dtype=int)
        
        if n <= size:
            return legs

        # Shifted highs/lows for comparison
        high_size_ago = np.roll(self.highs, size)
        low_size_ago = np.roll(self.lows, size)
        
        # Rolling max/min of the intermediate range (excluding current and size_ago)
        # We use pandas for easy rolling max/min
        s_highs = pd.Series(self.highs)
        s_lows = pd.Series(self.lows)
        
        # highest_high of range [current-size+1 : current] inclusive
        rolling_max = s_highs.rolling(window=size).max().values
        rolling_min = s_lows.rolling(window=size).min().values
        
        # new_leg_high condition: high[i-size] > max(high[i-size+1 : i])
        # Note: rolling_max[i] covers [i-size+1 : i]
        new_leg_high = high_size_ago > rolling_max
        new_leg_low = low_size_ago < rolling_min
        
        curr_leg = 0
        for i in range(size, n):
            if new_leg_high[i]:
                curr_leg = self.BEARISH_LEG
            elif new_leg_low[i]:
                curr_leg = self.BULLISH_LEG
            legs[i] = curr_leg
            
        return legs


    async def run_analysis(self):
        if not await self.fetch_ohlcv():
            return False
        self.prepare_data()
        self.run_smc_analysis()
        print("Smart Money Concepts analysis completed")
        return True

    def plot_candlestick_chart(self, ax, start_idx: int = 0, end_idx: int = None):
        if end_idx is None:
            end_idx = len(self.df)
        df_slice = self.df.iloc[start_idx:end_idx]
        for i, (idx, row) in enumerate(df_slice.iterrows()):
            color = self.swing_bullish_color if row['close'] > row['open'] else self.swing_bearish_color
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['close'], row['open'])
            ax.add_patch(patches.Rectangle(
                (i, body_bottom), 0.8, body_height,
                facecolor=color, edgecolor='black', linewidth=0.5
            ))
            ax.plot([i+0.4, i+0.4], [row['low'], row['high']],
                    color='black', linewidth=0.5)

    def plot_structure_breaks(self, ax, start_idx: int = 0, end_idx: int = None):
        if not hasattr(self, 'structure_breaks') or not self.structure_breaks:
            return
        if end_idx is None:
            end_idx = len(self.df)
        for structure in self.structure_breaks:
            pivot_time = structure['time']
            time_diff = np.abs(self.times - pivot_time)
            pivot_time_idx = np.argmin(time_diff)
            plot_start_idx = pivot_time_idx - start_idx
            if plot_start_idx < -50:
                continue
            if structure['internal']:
                color = self.internal_bull_color_input if structure['direction'] == 'bullish' else self.internal_bear_color_input
            else:
                color = self.swing_bull_color_input if structure['direction'] == 'bullish' else self.swing_bear_color_input
            line_style = '--' if structure['internal'] else '-'
            detection_time = structure.get('break_time', pivot_time)
            detection_time_diff = np.abs(self.times - detection_time)
            detection_time_idx = np.argmin(detection_time_diff)
            plot_end_idx = detection_time_idx - start_idx
            actual_start = max(0, plot_start_idx)
            actual_end = min(end_idx - start_idx, plot_end_idx)
            if actual_start < actual_end:
                ax.plot([actual_start, actual_end],
                        [structure['price'], structure['price']],
                        color=color, linestyle=line_style, alpha=0.8, linewidth=1.5)
                label_x = (actual_start + actual_end) / 2
                label_y_offset = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.005
                if structure['direction'] == 'bullish':
                    label_y = structure['price'] + label_y_offset
                    va = 'bottom'
                else:
                    label_y = structure['price'] - label_y_offset
                    va = 'top'
                ax.text(label_x, label_y, structure['type'],
                        color=color, fontsize=9, ha='center', va=va, weight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3))

        all_start_indices = [max(0, pivot_time_idx - start_idx) for structure in self.structure_breaks 
                            if (pivot_time_idx - start_idx) >= -50 and (detection_time_idx - start_idx) < end_idx]
        all_end_indices = [min(end_idx - start_idx, detection_time_idx - start_idx) for structure in self.structure_breaks 
                        if (pivot_time_idx - start_idx) >= -50 and (detection_time_idx - start_idx) < end_idx]
        if all_start_indices and all_end_indices:
            min_x = min(all_start_indices)
            max_x = max(all_end_indices)
            x_range = max_x - min_x
            ax.set_xlim(min_x - x_range * 0.1, max_x + x_range * 0.1)

    def plot_order_blocks(self, ax, start_idx: int = 0, end_idx: int = None):
        if end_idx is None:
            end_idx = len(self.df)
        for i, ob in enumerate(self.swing_order_blocks):
            if i >= self.swing_order_blocks_size_input:
                break
            time_idx = np.where(self.times == ob.bar_time)[0]
            if len(time_idx) > 0:
                time_idx = time_idx[0]
                plot_start_idx = time_idx - start_idx
                if plot_start_idx <= end_idx - start_idx:
                    color = self.swing_bullish_order_block_color if ob.bias == self.BULLISH else self.swing_bearish_order_block_color
                    actual_start = max(0, plot_start_idx)
                    width = (end_idx - start_idx) - actual_start
                    height = ob.bar_high - ob.bar_low
                    if width > 0:
                        ax.add_patch(patches.Rectangle(
                            (actual_start, ob.bar_low), width, height,
                            facecolor=color, edgecolor=color,
                            alpha=0.3, linewidth=1
                        ))
        for i, ob in enumerate(self.internal_order_blocks):
            if i >= self.internal_order_blocks_size_input:
                break
            time_idx = np.where(self.times == ob.bar_time)[0]
            if len(time_idx) > 0:
                time_idx = time_idx[0]
                plot_start_idx = time_idx - start_idx
                if plot_start_idx <= end_idx - start_idx:
                    color = self.internal_bullish_order_block_color if ob.bias == self.BULLISH else self.internal_bearish_order_block_color
                    actual_start = max(0, plot_start_idx)
                    width = (end_idx - start_idx) - actual_start
                    height = ob.bar_high - ob.bar_low
                    if width > 0:
                        ax.add_patch(patches.Rectangle(
                            (actual_start, ob.bar_low), width, height,
                            facecolor=color, edgecolor=color,
                            alpha=0.3, linewidth=1
                        ))

    def plot_equal_highs_lows(self, ax, start_idx: int = 0, end_idx: int = None):
        if not hasattr(self, 'equal_structures'):
            return
        if end_idx is None:
            end_idx = len(self.df)
        for equal in self.equal_structures:
            start_time_idx = np.where(self.times == equal['start_time'])[0]
            end_time_idx = np.where(self.times == equal['end_time'])[0]
            if len(start_time_idx) > 0 and len(end_time_idx) > 0:
                start_plot_idx = start_time_idx[0] - start_idx
                end_plot_idx = end_time_idx[0] - start_idx
                if start_plot_idx < end_idx - start_idx and end_plot_idx > 0:
                    actual_start = max(0, start_plot_idx)
                    actual_end = min(end_idx - start_idx, end_plot_idx)
                    ax.plot([actual_start, actual_end],
                            [equal['start_level'], equal['end_level']],
                            color=equal['color'], linewidth=1.5, linestyle=':', alpha=0.8)
                    mid_x = (actual_start + actual_end) / 2
                    mid_y = (equal['start_level'] + equal['end_level']) / 2
                    ax.text(mid_x, mid_y,
                            equal['type'], color=equal['color'],
                            fontsize=8, ha='center', va='center', weight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", facecolor=equal['color'], alpha=0.3))

    def plot_fair_value_gaps(self, ax, start_idx: int = 0, end_idx: int = None):
        if not self.show_fair_value_gaps_input or not hasattr(self, 'fair_value_gaps'):
            return
        if end_idx is None:
            end_idx = len(self.df)
        for fvg in self.fair_value_gaps:
            if hasattr(fvg, 'start_idx') and fvg.start_idx is not None:
                plot_start_idx = fvg.start_idx - start_idx
                plot_width = fvg.width
            else:
                plot_start_idx = 0
                plot_width = 10
            if plot_start_idx <= end_idx - start_idx and plot_start_idx + plot_width >= 0:
                actual_start = max(0, plot_start_idx)
                actual_width = min(plot_width, end_idx - start_idx - actual_start)
                if actual_width > 0:
                    color = self.fair_value_gap_bullish_color if fvg.bias == self.BULLISH else self.fair_value_gap_bearish_color
                    height = fvg.top - fvg.bottom
                    ax.add_patch(patches.Rectangle(
                        (actual_start, fvg.bottom), actual_width, height,
                        facecolor=color, edgecolor=color,
                        alpha=0.3, linewidth=1
                    ))
                    label_text = 'FVG' if fvg.bias == self.BULLISH else 'FVG'
                    mid_x = actual_start + actual_width / 2
                    mid_y = (fvg.top + fvg.bottom) / 2
                    ax.text(mid_x, mid_y, label_text,
                            color=color[:-2] if len(color) > 7 else color,
                            fontsize=6, ha='center', va='center', weight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", facecolor=color, alpha=0.5))

    def plot_premium_discount_zones(self, ax, start_idx: int = 0, end_idx: int = None):
        if not self.show_premium_discount_zones_input or not hasattr(self, 'premium_discount_zones'):
            return
        if end_idx is None:
            end_idx = len(self.df)
        zone_colors = {
            'premium': self.premium_zone_color,
            'equilibrium': self.equilibrium_zone_color_input,
            'discount': self.discount_zone_color
        }
        for zone_name, zone_data in self.premium_discount_zones.items():
            base_color = zone_colors.get(zone_name, '#808080')
            ax.axhspan(zone_data['bottom'], zone_data['top'],
                       facecolor=base_color, alpha=0.15, zorder=1)
            mid_price = (zone_data['top'] + zone_data['bottom']) / 2
            ax.text(end_idx - start_idx - 5, mid_price, zone_name.capitalize(),
                    color=base_color, fontsize=10, ha='right', va='center',
                    weight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=base_color, alpha=0.3))

    def plot_trailing_extremes(self, ax, start_idx: int = 0, end_idx: int = None):
        if not self.show_high_low_swings_input:
            return
        if end_idx is None:
            end_idx = len(self.df)
        bars_to_extend = 20
        right_time_bar = end_idx - start_idx + bars_to_extend
        if hasattr(self.trailing, 'last_top_time') and self.trailing.last_top_time is not None:
            top_time_idx = np.where(self.times == self.trailing.last_top_time)[0]
            if len(top_time_idx) > 0:
                plot_start_idx = top_time_idx[0] - start_idx
                if plot_start_idx <= end_idx - start_idx:
                    actual_start = max(0, plot_start_idx)
                    actual_end = min(right_time_bar, end_idx - start_idx)
                    ax.plot([actual_start, actual_end],
                            [self.trailing.top, self.trailing.top],
                            color=self.swing_bearish_color, linewidth=2, linestyle='-', alpha=0.8)
                    trend_label = 'Strong High' if self.swing_trend.bias == self.BEARISH else 'Weak High'
                    ax.text(actual_end - 2, self.trailing.top, trend_label,
                            color=self.swing_bearish_color, fontsize=9,
                            ha='right', va='bottom', weight='bold')
        if hasattr(self.trailing, 'last_bottom_time') and self.trailing.last_bottom_time is not None:
            bottom_time_idx = np.where(self.times == self.trailing.last_bottom_time)[0]
            if len(bottom_time_idx) > 0:
                plot_start_idx = bottom_time_idx[0] - start_idx
                if plot_start_idx <= end_idx - start_idx:
                    actual_start = max(0, plot_start_idx)
                    actual_end = min(right_time_bar, end_idx - start_idx)
                    ax.plot([actual_start, actual_end],
                            [self.trailing.bottom, self.trailing.bottom],
                            color=self.swing_bullish_color, linewidth=2, linestyle='-', alpha=0.8)
                    trend_label = 'Strong Low' if self.swing_trend.bias == self.BULLISH else 'Weak Low'
                    ax.text(actual_end - 2, self.trailing.bottom, trend_label,
                            color=self.swing_bullish_color, fontsize=9,
                            ha='right', va='top', weight='bold')

    def visualize_smc(self, bars_to_show: int = 1000):
        if self.df is None:
            print("No data available for visualization")
            return
        total_bars = len(self.df)
        start_idx = max(0, total_bars - bars_to_show)
        end_idx = total_bars
        fig, ax = plt.subplots(figsize=(15, 10))
        self.plot_candlestick_chart(ax, start_idx, end_idx)
        self.plot_premium_discount_zones(ax, start_idx, end_idx)
        self.plot_fair_value_gaps(ax, start_idx, end_idx)
        self.plot_order_blocks(ax, start_idx, end_idx)
        self.plot_structure_breaks(ax, start_idx, end_idx)
        self.plot_equal_highs_lows(ax, start_idx, end_idx)
        self.plot_trailing_extremes(ax, start_idx, end_idx)
        ax.set_xlim(0, bars_to_show)
        ax.set_ylim(self.df.iloc[start_idx:end_idx]['low'].min() * 0.995,
                    self.df.iloc[start_idx:end_idx]['high'].max() * 1.005)
        ax.set_title(f"{self.stock_code} - Smart Money Concepts",
                     fontsize=16, fontweight='bold')
        ax.set_xlabel("Bars", fontsize=12)
        ax.set_ylabel("Price", fontsize=12)
        ax.grid(True, alpha=0.3)
        legend_elements = [
            plt.Line2D([0], [0], color=self.swing_bullish_color, lw=2, label='Bullish Structure'),
            plt.Line2D([0], [0], color=self.swing_bearish_color, lw=2, label='Bearish Structure'),
            patches.Patch(color=self.swing_bullish_order_block_color, alpha=0.3, label='Swing Order Blocks'),
            patches.Patch(color=self.internal_bullish_order_block_color, alpha=0.3, label='Internal Order Blocks')
        ]
        if self.show_equal_highs_lows_input:
            legend_elements.append(plt.Line2D([0], [0], color=self.swing_bullish_color,
                                              lw=1, linestyle=':', label='Equal Highs/Lows'))
        if self.show_fair_value_gaps_input:
            legend_elements.append(patches.Patch(color=self.fair_value_gap_bullish_color,
                                                alpha=0.2, label='Fair Value Gaps'))
        if self.show_premium_discount_zones_input:
            legend_elements.append(patches.Patch(color=self.premium_zone_color,
                                                alpha=0.1, label='Premium/Discount Zones'))
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        plt.tight_layout()
        plt.show()
        self.print_analysis_summary()

    def print_analysis_summary(self):
        if not self.print_details:
            summary_data, levels_data = self._generate_analysis_summary()
            return summary_data, levels_data

        print("\n" + "="*80)
        print("\nSMART MONEY CONCEPTS ANALYSIS SUMMARY")
        print("\n" + "="*80)
        print(f"Stock Code: {self.stock_code}")
        print(f"Total Bars Analyzed: {len(self.df)}")
        print(f"Data Range: {self.df.index[0]} to {self.df.index[-1]}")
        print("-" * 80)

        summary_data, levels_data = self._generate_analysis_summary()
        current_price = summary_data['Current_Price']

        print("\nSTRUCTURE ANALYSIS:")
        print(f"Swing BOS: {summary_data['Swing_BOS']}")
        print(f"Swing CHoCH: {summary_data['Swing_CHoCH']}")
        print(f"Internal BOS: {summary_data['Internal_BOS']}")
        print(f"Internal CHoCH: {summary_data['Internal_CHoCH']}")

        print("\nORDER BLOCKS:")
        print(f"Swing Order Blocks: {summary_data['Swing_Order_Blocks']}")
        print(f"Internal Order Blocks: {summary_data['Internal_Order_Blocks']}")

        print("\nEQUAL HIGHS/LOWS:")
        print(f"Equal Highs (EQH): {summary_data['Equal_Highs']}")
        print(f"Equal Lows (EQL): {summary_data['Equal_Lows']}")

        if self.show_fair_value_gaps_input:
            print("\nFAIR VALUE GAPS:")
            print(f"Bullish FVG: {summary_data['Bullish_FVG']}")
            print(f"Bearish FVG: {summary_data['Bearish_FVG']}")

        print("\nTRAILING EXTREMES:")
        if summary_data['Trailing_High'] is not None:
            print(f"Trailing High: {summary_data['Trailing_High']}")
        if summary_data['Trailing_Low'] is not None:
            print(f"Trailing Low: {summary_data['Trailing_Low']}")

        if self.show_premium_discount_zones_input and hasattr(self, 'premium_discount_zones'):
            print("\nPREMIUM/DISCOUNT ZONES:")
            for zone_name in ['premium', 'equilibrium', 'discount']:
                bottom = summary_data[f"{zone_name.capitalize()}_Bottom"]
                top = summary_data[f"{zone_name.capitalize()}_Top"]
                print(f"{zone_name.capitalize()}: Bottom = {bottom}, Top = {top}")

        print("\nPRICE ANALYSIS:")
        print(f"Current Price: {current_price}")
        if summary_data['Current_Zone'] is not None:
            print(f"Current Zone: {summary_data['Current_Zone']}")

        print("=" * 80)
        print("Analysis completed successfully!")
        print("=" * 80 + "\n")
        return summary_data, levels_data

    def _generate_analysis_summary(self):
        current_price = round(self.df.iloc[-1]['close'], 2)
        summary_data = {
            'Stock_Code': self.stock_code,
            'Total_Bars': len(self.df),
            'Data_Start': str(self.df.index[0]),
            'Data_End': str(self.df.index[-1]),
            'Swing_High': round(self.swing_high.current_level, 2) if self.swing_high.current_level is not None else None,
            'Swing_Low': round(self.swing_low.current_level, 2) if self.swing_low.current_level is not None else None,
            'Internal_High': round(self.internal_high.current_level, 2) if self.internal_high.current_level is not None else None,
            'Internal_Low': round(self.internal_low.current_level, 2) if self.internal_low.current_level is not None else None,
            'Swing_Trend': "Bullish" if self.swing_trend.bias == self.BULLISH else "Bearish" if self.swing_trend.bias == self.BEARISH else "Neutral",
            'Internal_Trend': "Bullish" if self.internal_trend.bias == self.BULLISH else "Bearish" if self.internal_trend.bias == self.BEARISH else "Neutral",
            'Current_Price': current_price,
        }

        if hasattr(self, 'structure_breaks'):
            summary_data.update({
                'Swing_BOS': len([s for s in self.structure_breaks if s['type'] == self.BOS and not s['internal']]),
                'Swing_CHoCH': len([s for s in self.structure_breaks if s['type'] == self.CHOCH and not s['internal']]),
                'Internal_BOS': len([s for s in self.structure_breaks if s['type'] == self.BOS and s['internal']]),
                'Internal_CHoCH': len([s for s in self.structure_breaks if s['type'] == self.CHOCH and s['internal']])
            })
        else:
            summary_data.update({
                'Swing_BOS': 0,
                'Swing_CHoCH': 0,
                'Internal_BOS': 0,
                'Internal_CHoCH': 0
            })

        summary_data.update({
            'Swing_Order_Blocks': len(self.swing_order_blocks),
            'Internal_Order_Blocks': len(self.internal_order_blocks)
        })

        if hasattr(self, 'equal_structures'):
            summary_data.update({
                'Equal_Highs': len([e for e in self.equal_structures if e['type'] == 'EQH']),
                'Equal_Lows': len([e for e in self.equal_structures if e['type'] == 'EQL'])
            })
        else:
            summary_data.update({
                'Equal_Highs': 0,
                'Equal_Lows': 0
            })

        if self.show_fair_value_gaps_input:
            summary_data.update({
                'Bullish_FVG': len([f for f in self.fair_value_gaps if f.bias == self.BULLISH]),
                'Bearish_FVG': len([f for f in self.fair_value_gaps if f.bias == self.BEARISH])
            })
        else:
            summary_data.update({
                'Bullish_FVG': 0,
                'Bearish_FVG': 0
            })

        summary_data.update({
            'Trailing_High': round(self.trailing.top, 2) if self.trailing.top is not None else None,
            'Trailing_Low': round(self.trailing.bottom, 2) if self.trailing.bottom is not None else None
        })

        if self.show_premium_discount_zones_input and hasattr(self, 'premium_discount_zones') and self.premium_discount_zones:
            for zone_name in ['premium', 'equilibrium', 'discount']:
                zone_data = self.premium_discount_zones[zone_name]
                summary_data.update({
                    f"{zone_name.capitalize()}_Bottom": round(zone_data['bottom'], 2),
                    f"{zone_name.capitalize()}_Top": round(zone_data['top'], 2)
                })

        if self.show_premium_discount_zones_input and hasattr(self, 'premium_discount_zones') and self.premium_discount_zones:
            if current_price >= self.premium_discount_zones['premium']['bottom']:
                summary_data['Current_Zone'] = "Premium"
            elif current_price <= self.premium_discount_zones['discount']['top']:
                summary_data['Current_Zone'] = "Discount"
            else:
                summary_data['Current_Zone'] = "Equilibrium"
        else:
            summary_data['Current_Zone'] = None

        levels_data = []
        # Swing High
        if self.swing_high.current_level is not None:
            level = round(self.swing_high.current_level, 2)
            midpoint = level
            distance = abs(current_price - midpoint) / midpoint * 100 if midpoint else None
            levels_data.append({
                'Stock_Code': self.stock_code,
                'Level_Type': 'Swing_High',
                'Top': level,
                'Bottom': level,
                'Midpoint': midpoint,
                'Time': self.swing_high.bar_time,
                'Current_Price': current_price,
                'Distance_To_Midpoint_Percent': round(distance, 2) if distance is not None else None
            })
        # Swing Low
        if self.swing_low.current_level is not None:
            level = round(self.swing_low.current_level, 2)
            midpoint = level
            distance = abs(current_price - midpoint) / midpoint * 100 if midpoint else None
            levels_data.append({
                'Stock_Code': self.stock_code,
                'Level_Type': 'Swing_Low',
                'Top': level,
                'Bottom': level,
                'Midpoint': midpoint,
                'Time': self.swing_low.bar_time,
                'Current_Price': current_price,
                'Distance_To_Midpoint_Percent': round(distance, 2) if distance is not None else None
            })
        # Internal High
        if self.internal_high.current_level is not None:
            level = round(self.internal_high.current_level, 2)
            midpoint = level
            distance = abs(current_price - midpoint) / midpoint * 100 if midpoint else None
            levels_data.append({
                'Stock_Code': self.stock_code,
                'Level_Type': 'Internal_High',
                'Top': level,
                'Bottom': level,
                'Midpoint': midpoint,
                'Time': self.internal_high.bar_time,
                'Current_Price': current_price,
                'Distance_To_Midpoint_Percent': round(distance, 2) if distance is not None else None
            })
        # Internal Low
        if self.internal_low.current_level is not None:
            level = round(self.internal_low.current_level, 2)
            midpoint = level
            distance = abs(current_price - midpoint) / midpoint * 100 if midpoint else None
            levels_data.append({
                'Stock_Code': self.stock_code,
                'Level_Type': 'Internal_Low',
                'Top': level,
                'Bottom': level,
                'Midpoint': midpoint,
                'Time': self.internal_low.bar_time,
                'Current_Price': current_price,
                'Distance_To_Midpoint_Percent': round(distance, 2) if distance is not None else None
            })
        # Swing Order Blocks
        # The old code saves ALL historic OBs and FVGs that were present at current_bar.
        # But wait, the old code's loop appends to the file.
        # Actually, in old _generate_analysis_summary, it iterates over self.swing_order_blocks.
        for ob in self.swing_order_blocks:
            top = round(ob.bar_high, 2)
            bottom = round(ob.bar_low, 2)
            midpoint = (top + bottom) / 2
            distance = abs(current_price - midpoint) / midpoint * 100 if midpoint else None
            levels_data.append({
                'Stock_Code': self.stock_code,
                'Level_Type': f"Swing_Order_Block_{'Bullish' if ob.bias == self.BULLISH else 'Bearish'}",
                'Top': top,
                'Bottom': bottom,
                'Midpoint': round(midpoint, 2),
                'Time': ob.bar_time,
                'Current_Price': current_price,
                'Distance_To_Midpoint_Percent': round(distance, 2) if distance is not None else None
            })
        # Internal Order Blocks
        for ob in self.internal_order_blocks:
            top = round(ob.bar_high, 2)
            bottom = round(ob.bar_low, 2)
            midpoint = (top + bottom) / 2
            distance = abs(current_price - midpoint) / midpoint * 100 if midpoint else None
            levels_data.append({
                'Stock_Code': self.stock_code,
                'Level_Type': f"Internal_Order_Block_{'Bullish' if ob.bias == self.BULLISH else 'Bearish'}",
                'Top': top,
                'Bottom': bottom,
                'Midpoint': round(midpoint, 2),
                'Time': ob.bar_time,
                'Current_Price': current_price,
                'Distance_To_Midpoint_Percent': round(distance, 2) if distance is not None else None
            })
        # Fair Value Gaps
        # NEW logic to match old code: we should include ALL historic ones?
        # No, old code ALSO removed them when crossed.
        # But wait, in our vectorized detection, we might have found many more.
        for fvg in self.fair_value_gaps:
            top = round(fvg.top, 2)
            bottom = round(fvg.bottom, 2)
            midpoint = (top + bottom) / 2
            distance = abs(current_price - midpoint) / midpoint * 100 if midpoint else None
            levels_data.append({
                'Stock_Code': self.stock_code,
                'Level_Type': f"Fair_Value_Gap_{'Bullish' if fvg.bias == self.BULLISH else 'Bearish'}",
                'Top': top,
                'Bottom': bottom,
                'Midpoint': round(midpoint, 2),
                'Time': fvg.start_time,
                'Current_Price': current_price,
                'Distance_To_Midpoint_Percent': round(distance, 2) if distance is not None else None
            })

        return summary_data, levels_data

def process_single_stock_sync(stock_code, df, period, interval, auto_adjust, print_details, visualize, output_format, summary_file, levels_file, summary_file_exists, levels_file_exists):
    """Sync worker function for ProcessPoolExecutor."""
    try:
        smc = SmartMoneyConcepts(
            stock_code=stock_code,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            print_details=print_details,
            df=df
        )

        success = smc.fetch_ohlcv_sync()
        if success:
            smc.prepare_data()
            smc.run_smc_analysis()
            
            if visualize:
                smc.visualize_smc()
                
            summary_data, levels_data = smc.print_analysis_summary()
            
            alerts = None
            if hasattr(smc.current_alerts, 'current_candle_swing_bullish_bos'):
                if any([
                    smc.current_alerts.current_candle_swing_bullish_bos,
                    smc.current_alerts.current_candle_swing_bearish_bos,
                    smc.current_alerts.current_candle_swing_bullish_choch,
                    smc.current_alerts.current_candle_swing_bearish_choch,
                    smc.current_alerts.current_candle_internal_bullish_bos,
                    smc.current_alerts.current_candle_internal_bearish_bos,
                    smc.current_alerts.current_candle_internal_bullish_choch,
                    smc.current_alerts.current_candle_internal_bearish_choch
                ]):
                    alerts = {
                        'Stock_Code': stock_code,
                        'Swing_Bullish_CHoCH': smc.current_alerts.current_candle_swing_bullish_choch,
                        'Swing_Bearish_CHoCH': smc.current_alerts.current_candle_swing_bearish_choch,
                        'Swing_Bullish_BOS': smc.current_alerts.current_candle_swing_bullish_bos,
                        'Swing_Bearish_BOS': smc.current_alerts.current_candle_swing_bearish_bos,
                        'Internal_Bullish_CHoCH': smc.current_alerts.current_candle_internal_bullish_choch,
                        'Internal_Bearish_CHoCH': smc.current_alerts.current_candle_internal_bearish_choch,
                        'Internal_Bullish_BOS': smc.current_alerts.current_candle_internal_bullish_bos,
                        'Internal_Bearish_BOS': smc.current_alerts.current_candle_internal_bearish_bos,
                        'Timestamp': str(datetime.now())
                    }
            return stock_code, summary_data, levels_data, alerts
    except Exception as e:
        print(f"Error processing {stock_code}: {e}")
    return stock_code, None, None, None

async def main(
    stock_codes: List[str],
    csv_directory: str = "data",
    fetch_csv_data: bool = False,  # Respect the user's True setting
    csv_column_mapping: dict = None,   # <-- New parameter
    spreadsheet_id: str = None,   # Reinstated as requested
    period: str = "max",
    interval: str = "1d",
    auto_adjust: bool =False,
    visualize: bool = False,
    print_details: bool = True,
    clear: bool = True,
    force_refresh_data: bool = False,
    output_format: str = "csv",
    use_colab: bool = False       # Reinstated as requested
):
    # Remove duplicates from stock_codes
    stock_codes = list(set(stock_codes))
    if not stock_codes:
        stock_codes = ["RELIANCE.NS"]

    # Fallback mapping if not provided
    if csv_column_mapping is None:
        csv_column_mapping = {
            'OPEN_PRICE': 'open',
            'HIGH_PRICE': 'high',
            'LOW_PRICE': 'low',
            'CLOSE_PRICE': 'close',
            'DATE1': 'Date'
        }

    # Create stock_csv_map
    stock_csv_map = {}
    os.makedirs(csv_directory, exist_ok=True)
    if fetch_csv_data:
        for stock_code in stock_codes:
            base_name = stock_code.replace(".NS", "")
            csv_path = os.path.join(csv_directory, f"{base_name}.csv")
            if os.path.exists(csv_path):
                stock_csv_map[stock_code] = csv_path
                if print_details:
                    print(f"Mapped {stock_code} to {csv_path}")
            elif print_details:
                print(f"⚠️ CSV file for {stock_code} not found at {csv_path}. Using yfinance.")

    # today_str = datetime.now().strftime("%Y-%m-%d")
    # output_dir = os.path.join("analysis", today_str)
    # os.makedirs(output_dir, exist_ok=True)
    
    # Initialize CSV output
    output_dir = "analysis"
    os.makedirs(output_dir, exist_ok=True)
    summary_file = os.path.join(output_dir, 'smc_analysis_summaries.csv')
    levels_file = os.path.join(output_dir, 'smc_analysis_levels.csv')
    filtered_file = os.path.join(output_dir, 'current_candle_breaks.csv')

    if clear:
        for file in [summary_file, levels_file, filtered_file]:
            if os.path.exists(file):
                os.remove(file)

    summary_file_exists = os.path.exists(summary_file)
    levels_file_exists = os.path.exists(levels_file)
    filtered_file_exists = os.path.exists(filtered_file)

    # Google Sheets setup (only if output_format includes google_sheets)
    spreadsheet_url, summary_worksheet, levels_worksheet, filtered_worksheet = None, None, None, None
    gspread_client, summary_rows, levels_rows, filtered_rows = None, [], [], []
    summary_headers, levels_headers, filtered_headers = None, None, None
    processed_summary, processed_levels, processed_filtered = set(), set(), set()

    if output_format in ["google_sheets", "both"]:
        creds = None
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            if use_colab:
                try:
                    from google.colab import userdata
                    SERVICE_ACCOUNT_CREDS = userdata.get("SERVICE_ACCOUNT_CREDS")
                    if SERVICE_ACCOUNT_CREDS:
                        SERVICE_ACCOUNT_CREDS = json.loads(SERVICE_ACCOUNT_CREDS)
                        creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_CREDS, scopes=scope)
                except ImportError:
                    print("⚠️ Not running in Colab. Falling back to local credentials.")
            if creds is None:
                local_cred_path = "Credentials/credentials.json"
                if os.path.exists(local_cred_path):
                    creds = ServiceAccountCredentials.from_json_keyfile_name(local_cred_path, scope)
                else:
                    print(f"⚠️ Local credentials.json not found at {local_cred_path}. Falling back to CSV output.")
                    output_format = "csv"
            if creds:
                gspread_client = gspread.authorize(creds)
                spreadsheet = gspread_client.open_by_key(spreadsheet_id)
                spreadsheet_url = spreadsheet.url
                summary_worksheet = spreadsheet.worksheet("Summaries")
                levels_worksheet = spreadsheet.worksheet("Levels")
                try:
                    filtered_worksheet = spreadsheet.worksheet("Current_Candle_Breaks")
                except gspread.exceptions.WorksheetNotFound:
                    filtered_worksheet = spreadsheet.add_worksheet(title="Current_Candle_Breaks", rows=1000, cols=20)
                if clear:
                    summary_worksheet.clear()
                    levels_worksheet.clear()
                    filtered_worksheet.clear()
                if not clear:
                    existing_summary = {tuple(row) for row in summary_worksheet.get_all_values()}
                    existing_levels = {tuple(row) for row in levels_worksheet.get_all_values()}
                    existing_filtered = {tuple(row) for row in filtered_worksheet.get_all_values()}
                    processed_summary.update(existing_summary)
                    processed_levels.update(existing_levels)
                    processed_filtered.update(existing_filtered)
        except Exception as e:
            print(f"Failed to initialize Google Sheets: {e}")
            if output_format == "google_sheets":
                return
            output_format = "csv"

    # 1. Fetch ALL data
    all_data = {}
    if fetch_csv_data and stock_csv_map:
        if print_details:
            print(f"📦 Loading data for {len(stock_csv_map)} stocks from CSV...")
        for stock, path in stock_csv_map.items():
            try:
                # Use same parsing logic as fetch_ohlcv
                date_column = next((k for k, v in csv_column_mapping.items() if v == 'Date'), None) if csv_column_mapping else None
                parse_dates = [date_column] if date_column else False
                df = pd.read_csv(path, parse_dates=parse_dates)
                if date_column in df.columns:
                    df.set_index(date_column, inplace=True)
                
                # Standardize columns
                if csv_column_mapping:
                    # Remove Date from mapping to avoid duplicate renaming
                    mapping = {k: v for k, v in csv_column_mapping.items() if v != 'Date'}
                    df = df.rename(columns=mapping)
                
                df = df.dropna(subset=['open', 'high', 'low', 'close'])
                all_data[stock] = df
            except Exception as e:
                print(f"Error loading CSV for {stock}: {e}")
    
    # Fetch remaining or all from yfinance using Centralized Manager
    remaining_stocks = [s for s in stock_codes if s not in all_data]
    failed_symbols = []
    if remaining_stocks:
        if print_details:
            print(f"📦 Fetching data for {len(remaining_stocks)} stocks using centralized manager...")
        yf_data = stock_data_manager.get_data(
            tickers=remaining_stocks, 
            period=period, 
            interval=interval, 
            force_refresh=force_refresh_data
        )
        all_data.update(yf_data)
        failed_symbols = [s for s in remaining_stocks if s not in yf_data]
    
    # 2. SMC Analysis (Parallel unless visualization is required)
    if visualize:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        PoolExecutor = ThreadPoolExecutor
        num_workers = 1 # Sequential is better for visualization
        print(f"🖼️ Running sequential analysis for visualization...")
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        PoolExecutor = ProcessPoolExecutor
        import multiprocessing
        num_workers = min(multiprocessing.cpu_count(), 8)
    print(f"� Running analysis with {num_workers} processes...")
    
    filtered_stocks = []
    
    with PoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for stock_code in stock_codes:
            if stock_code in all_data:
                futures.append(executor.submit(
                    process_single_stock_sync,
                    stock_code, all_data[stock_code], period, interval, auto_adjust, 
                    print_details=print_details, visualize=visualize,
                    output_format=output_format, summary_file=summary_file, 
                    levels_file=levels_file, summary_file_exists=summary_file_exists, 
                    levels_file_exists=levels_file_exists
                ))
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Analyzing stocks", unit="stock"):
            stock_code, summary_data, levels_data, alerts = future.result()
            
            if summary_data:
                # Save results in main process to avoid file locking issues
                if output_format in ["csv", "both"]:
                    pd.DataFrame([summary_data]).to_csv(summary_file, mode='a', index=False, header=not os.path.exists(summary_file))
                    pd.DataFrame(levels_data).to_csv(levels_file, mode='a', index=False, header=not os.path.exists(levels_file))
                
                if alerts:
                    filtered_stocks.append(alerts)
                # Unified Google Sheets handling (still in main loop)
                if output_format in ["google_sheets", "both"] and gspread_client:
                    if summary_data:
                        normalized_summary = {k: str(v) if v is not None else "" for k, v in summary_data.items()}
                        if summary_headers is None:
                            summary_headers = list(normalized_summary.keys())
                            summary_rows.append(summary_headers)
                        row_data = [normalized_summary.get(h, "") for h in summary_headers]
                        row_tuple = tuple(row_data)
                        if row_tuple not in processed_summary:
                            summary_rows.append(row_data)
                            processed_summary.add(row_tuple)
                            
                    if levels_data:
                        if not levels_headers:
                            levels_headers = list(levels_data[0].keys())
                            levels_rows.append(levels_headers)
                        for level in levels_data:
                            normalized_level = {k: str(v) if v is not None else "" for k, v in level.items()}
                            row_data = [normalized_level.get(h, "") for h in levels_headers]
                            row_tuple = tuple(row_data)
                            if row_tuple not in processed_levels:
                                levels_rows.append(row_data)
                                processed_levels.add(row_tuple)

                    if alerts:
                        normalized_alerts = {k: str(v) if v is not None else "" for k, v in alerts.items()}
                        if filtered_headers is None:
                            filtered_headers = list(normalized_alerts.keys())
                            filtered_rows.append(filtered_headers)
                        row_data = [normalized_alerts.get(h, "") for h in filtered_headers]
                        row_tuple = tuple(row_data)
                        if row_tuple not in processed_filtered:
                            filtered_rows.append(row_data)
                            processed_filtered.add(row_tuple)

    # Save filtered stocks to CSV
    if output_format in ["csv", "both"] and filtered_stocks:
        pd.DataFrame(filtered_stocks).to_csv(
            filtered_file,
            mode='a',
            index=False,
            header=not filtered_file_exists
        )
        if print_details:
            print(f"Filtered stocks with current candle CHoCH/BOS saved to {filtered_file}")

    # Write to Google Sheets
    if output_format in ["google_sheets", "both"] and gspread_client and (summary_rows or levels_rows or filtered_rows):
        try:
            if summary_rows and len(summary_rows) > 1:
                summary_worksheet.update("A1", summary_rows)
                if print_details:
                    print(f"Updated Summaries worksheet with {len(summary_rows)-1} rows")
            if levels_rows and len(levels_rows) > 1:
                levels_worksheet.update("A1", levels_rows)
                if print_details:
                    print(f"Updated Levels worksheet with {len(levels_rows)-1} rows")
            if filtered_rows and len(filtered_rows) > 1:
                filtered_worksheet.update("A1", filtered_rows)
                if print_details:
                    print(f"Updated Current_Candle_Breaks worksheet with {len(filtered_rows)-1} rows")
            time.sleep(1)
        except Exception as e:
            print(f"Error updating Google Sheets: {e}")

    # Print output locations
    if output_format in ["csv", "both"] and (summary_file_exists or clear):
        print(f"\nSummaries saved to {summary_file}")
    if output_format in ["csv", "both"] and (levels_file_exists or clear):
        print(f"Levels saved to {levels_file}")  # Fixed from previous incorrect reference
    if output_format in ["csv", "both"] and (filtered_file_exists or clear):
        print(f"Current candle breaks saved to {filtered_file}")
    if output_format in ["google_sheets", "both"] and gspread_client:
        print(f"\nData saved to Google Sheets: {spreadsheet_url}")
    
    return failed_symbols
