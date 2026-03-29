#!/usr/bin/env python3
"""
SPY Options Signal Backtester v2.7 - Redesigned Puts + Enhanced Calls
======================================================================
Key changes:
1. CALLS: Add Bollinger %B < 0.1 as 8th factor, require 5+ of 8
   (Higher conviction = higher win rate target of 75%+)
2. PUTS: Complete redesign — require ALL of:
   - Price above upper Bollinger Band (%B > 1.0) OR extended from 200 SMA (>5%)
   - RSI(5) > 75 (stronger overbought)
   - VIX < 16 (complacency, not just crushed)
   - At least 3+ consecutive up days
   Then standard factors scored on top.

Hypothesis: Puts need stronger overbought conditions + trend exhaustion.
The old put factors were too loose — they triggered on normal bull pullback setups.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pip3 install yfinance pandas numpy")
    sys.exit(1)

# --- Configuration ---
HOLD_DAYS = 10
STOP_LOSS = -0.40
TAKE_PROFIT = 0.30
OPTION_PREMIUM_FACTOR = 0.50

# --- Indicators ---
def calc_rsi(series, period=5):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_sma(series, period):
    return series.rolling(window=period).mean()

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(series, fast)
    ema_slow = calc_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    return macd_line, signal_line

def calc_ibs(high, low, close):
    return (close - low) / (high - low)

def calc_sma_slope(series, period=20):
    sma = calc_sma(series, period)
    return (sma.diff(5) / sma.shift(5)) * 100

def calc_bollinger_pct_b(close, period=20, std_dev=2):
    sma = calc_sma(close, period)
    rolling_std = close.rolling(window=period).std()
    upper_band = sma + (rolling_std * std_dev)
    lower_band = sma - (rolling_std * std_dev)
    band_width = upper_band - lower_band
    pct_b = (close - lower_band) / band_width
    return pct_b

# --- Fetch Historical Data ---
def fetch_historical():
    print("Fetching 7 years of SPY data...")
    spy = yf.download("SPY", period="7y", interval="1d", progress=False)
    vix = yf.download("^VIX", period="7y", interval="1d", progress=False)
    
    if spy.empty or vix.empty:
        return None, None, "Failed to fetch data"
    
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)
    
    return spy, vix, None

# --- Signal Calculation ---
def compute_signals_for_day(spy, vix, idx):
    spy_close = float(spy['Close'].iloc[idx])
    spy_prev = float(spy['Close'].iloc[idx-1])
    spy_chg = ((spy_close - spy_prev) / spy_prev) * 100
    
    vix_close = float(vix['Close'].iloc[idx])
    vix_prev = float(vix['Close'].iloc[idx-1])
    vix_chg = ((vix_close - vix_prev) / vix_prev) * 100
    
    spy_close_series = spy['Close'].iloc[:idx+1]
    spy_high_series = spy['High'].iloc[:idx+1]
    spy_low_series = spy['Low'].iloc[:idx+1]
    
    rsi5 = float(calc_rsi(spy_close_series, 5).iloc[-1])
    ema20 = float(calc_ema(spy_close_series, 20).iloc[-1])
    sma50 = float(calc_sma(spy_close_series, 50).iloc[-1])
    sma200 = float(calc_sma(spy_close_series, 200).iloc[-1])
    
    dist_ema20 = ((spy_close - ema20) / ema20) * 100
    dist_sma50 = ((spy_close - sma50) / sma50) * 100
    dist_sma200 = ((spy_close - sma200) / sma200) * 100
    
    macd_line, macd_sig = calc_macd(spy_close_series)
    cur_macd = float(macd_line.iloc[-1])
    cur_macd_sig = float(macd_sig.iloc[-1])
    prev_macd = float(macd_line.iloc[-2])
    prev_macd_sig = float(macd_sig.iloc[-2])
    
    ibs = float(calc_ibs(spy_high_series, spy_low_series, spy_close_series).iloc[-1])
    sma200_slope = float(calc_sma_slope(spy_close_series, 200).iloc[-1])
    
    avg_volume = spy['Volume'].iloc[idx-20:idx].mean()
    cur_volume = float(spy['Volume'].iloc[idx])
    volume_spike = (cur_volume / avg_volume) > 1.5 if avg_volume > 0 else False
    
    spy_changes = spy['Close'].iloc[idx-5:idx].pct_change().dropna()
    down_days = sum(1 for c in spy_changes if c < 0)
    up_days = sum(1 for c in spy_changes if c > 0)
    
    pct_b = float(calc_bollinger_pct_b(spy_close_series, 20, 2).iloc[-1])
    
    # 5-day cumulative return (how extended is the move?)
    five_day_return = float((spy['Close'].iloc[idx] / spy['Close'].iloc[idx-5] - 1) * 100)
    
    # --- CALL FACTORS (8 with BB) ---
    call_factors = {
        'rsi_oversold': rsi5 < 30,
        'vix_elevated': (vix_close > 20 and vix_chg > 10) or vix_close > 25,
        'price_support': (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
        'macd_bullish': prev_macd <= prev_macd_sig and cur_macd > cur_macd_sig,
        'ibs_low': ibs < 0.2,
        'volume_spike': volume_spike and spy_chg < 0,
        'consecutive_down': down_days >= 3,
        'bb_low': pct_b < 0.1,
    }
    call_score = sum(call_factors.values())
    
    # --- PUT FACTORS (redesigned — 7 factors) ---
    put_factors = {
        'rsi_extreme_overbought': rsi5 > 75,           # Stricter than old 70
        'vix_complacent': vix_close < 16,               # Broader complacency zone
        'extended_from_sma200': dist_sma200 > 5,        # Way above 200 SMA
        'macd_bearish': prev_macd >= prev_macd_sig and cur_macd < cur_macd_sig,
        'ibs_high': ibs > 0.8,
        'consecutive_up': up_days >= 3,
        'bb_high': pct_b > 0.9,                         # At upper Bollinger
    }
    put_score = sum(put_factors.values())
    
    return {
        'date': spy.index[idx].strftime('%Y-%m-%d'),
        'spy_close': spy_close,
        'spy_chg': spy_chg,
        'vix_close': vix_close,
        'rsi5': rsi5,
        'dist_ema20': dist_ema20,
        'dist_sma200': dist_sma200,
        'sma200_slope': sma200_slope,
        'pct_b': pct_b,
        'five_day_return': five_day_return,
        'down_days': down_days,
        'up_days': up_days,
        'call_score': call_score,
        'put_score': put_score,
        'call_factors': {k: bool(v) for k, v in call_factors.items()},
        'put_factors': {k: bool(v) for k, v in put_factors.items()},
    }

# --- Simulate Trade ---
def simulate_trade(spy, entry_idx, direction, hold_days, stop_loss, take_profit):
    entry_price = float(spy['Close'].iloc[entry_idx])
    
    for i in range(1, min(hold_days + 1, len(spy) - entry_idx)):
        idx = entry_idx + i
        current_price = float(spy['Close'].iloc[idx])
        current_rsi = float(calc_rsi(spy['Close'].iloc[:idx+1], 5).iloc[-1])
        
        spy_return = (current_price - entry_price) / entry_price
        
        if direction == 'CALL':
            option_return = spy_return * OPTION_PREMIUM_FACTOR
            if current_rsi > 70:
                return option_return, spy.index[idx].strftime('%Y-%m-%d'), 'RSI_EXIT', i
        else:
            option_return = -spy_return * OPTION_PREMIUM_FACTOR
            if current_rsi < 30:
                return option_return, spy.index[idx].strftime('%Y-%m-%d'), 'RSI_EXIT', i
        
        if option_return <= stop_loss:
            return stop_loss, spy.index[idx].strftime('%Y-%m-%d'), 'STOP_LOSS', i
        if option_return >= take_profit:
            return take_profit, spy.index[idx].strftime('%Y-%m-%d'), 'TAKE_PROFIT', i
    
    final_idx = min(entry_idx + hold_days, len(spy) - 1)
    final_price = float(spy['Close'].iloc[final_idx])
    spy_return = (final_price - entry_price) / entry_price
    option_return = spy_return * OPTION_PREMIUM_FACTOR if direction == 'CALL' else -spy_return * OPTION_PREMIUM_FACTOR
    return option_return, spy.index[final_idx].strftime('%Y-%m-%d'), 'MAX_HOLD', hold_days

# --- Run Backtest with multiple threshold combos ---
def run_backtest():
    spy, vix, error = fetch_historical()
    if error:
        print(f"ERROR: {error}")
        return
    
    warmup = 250
    
    # Test multiple threshold combinations
    combos = [
        (4, 3, "Calls 4+/8, Puts 3+/7 (redesigned)"),
        (4, 4, "Calls 4+/8, Puts 4+/7 (redesigned)"),
        (5, 3, "Calls 5+/8, Puts 3+/7 (redesigned)"),
        (5, 4, "Calls 5+/8, Puts 4+/7 (redesigned)"),
    ]
    
    print(f"\nBacktesting from {spy.index[warmup].date()} to {spy.index[-1].date()}")
    print("=" * 70)
    
    # Precompute all signals
    all_signals = []
    for i in range(warmup, len(spy)):
        if i % 100 == 0:
            print(f"Computing signals... {i}/{len(spy)} days")
        signals = compute_signals_for_day(spy, vix, i)
        signals['idx'] = i
        all_signals.append(signals)
    
    print(f"\nTotal signal days: {len(all_signals)}")
    
    for call_thresh, put_thresh, label in combos:
        trades = {'CALL': [], 'PUT': []}
        
        for signals in all_signals:
            i = signals['idx']
            
            if signals['call_score'] >= call_thresh:
                ret, exit_date, reason, days = simulate_trade(
                    spy, i, 'CALL', HOLD_DAYS, STOP_LOSS, TAKE_PROFIT
                )
                trades['CALL'].append({
                    'entry_date': signals['date'],
                    'score': signals['call_score'],
                    'return': ret,
                    'exit_reason': reason,
                    'sma200_slope': signals['sma200_slope'],
                })
            
            if signals['put_score'] >= put_thresh:
                ret, exit_date, reason, days = simulate_trade(
                    spy, i, 'PUT', HOLD_DAYS, STOP_LOSS, TAKE_PROFIT
                )
                trades['PUT'].append({
                    'entry_date': signals['date'],
                    'score': signals['put_score'],
                    'return': ret,
                    'exit_reason': reason,
                    'sma200_slope': signals['sma200_slope'],
                })
        
        # Results
        print(f"\n{'='*70}")
        print(f"CONFIG: {label}")
        print(f"{'='*70}")
        
        for direction in ['CALL', 'PUT']:
            t = trades[direction]
            if not t:
                print(f"  {direction}: No trades")
                continue
            wins = sum(1 for x in t if x['return'] > 0)
            wr = (wins / len(t)) * 100
            avg = sum(x['return'] for x in t) / len(t)
            
            # By score
            scores = sorted(set(x['score'] for x in t))
            score_details = []
            for s in scores:
                st = [x for x in t if x['score'] == s]
                sw = sum(1 for x in st if x['return'] > 0)
                swr = (sw / len(st)) * 100
                savg = sum(x['return'] for x in st) / len(st)
                score_details.append(f"    Score {s}: {len(st)} trades, {swr:.1f}% win, {savg*100:+.1f}%")
            
            # By regime
            bull = [x for x in t if x['sma200_slope'] > 0]
            bear = [x for x in t if x['sma200_slope'] <= 0]
            
            print(f"  {direction}: {len(t)} trades, {wr:.1f}% win, {avg*100:+.1f}% avg")
            for sd in score_details:
                print(sd)
            if bull:
                bw = sum(1 for x in bull if x['return'] > 0)
                bwr = (bw / len(bull)) * 100
                print(f"    Bull regime: {len(bull)} trades, {bwr:.1f}% win")
            if bear:
                bw = sum(1 for x in bear if x['return'] > 0)
                bwr = (bw / len(bear)) * 100
                print(f"    Bear regime: {len(bear)} trades, {bwr:.1f}% win")
        
        # Combined metrics
        all_t = trades['CALL'] + trades['PUT']
        if all_t:
            wins = sum(1 for x in all_t if x['return'] > 0)
            wr = (wins / len(all_t)) * 100
            avg = sum(x['return'] for x in all_t) / len(all_t)
            returns = [x['return'] for x in all_t]
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(26) if len(returns) > 1 else 0
            print(f"  COMBINED: {len(all_t)} trades, {wr:.1f}% win, {avg*100:+.1f}% avg, Sharpe {sharpe:.2f}")

# --- Main ---
if __name__ == "__main__":
    print("SPY Options Signal Backtest - Redesigned Puts + BB Calls")
    print("=" * 70)
    run_backtest()
