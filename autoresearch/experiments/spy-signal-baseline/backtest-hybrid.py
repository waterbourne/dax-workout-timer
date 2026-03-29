#!/usr/bin/env python3
"""
SPY Options Signal Backtester v2.5 - Hybrid Thresholds
========================================================
Different thresholds for calls vs puts:
- Calls: 4+ of 7 factors (proven 72.8% win rate)
- Puts: 5+ of 7 factors (stricter, higher conviction)

Hypothesis: Put signals need higher bar due to bull market bias.
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

# --- Signal Calculation for a Single Day ---
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
    
    # --- CALL FACTORS (7) ---
    call_factors = {
        'rsi_oversold': rsi5 < 30,
        'vix_elevated': (vix_close > 20 and vix_chg > 10) or vix_close > 25,
        'price_support': (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
        'macd_bullish': prev_macd <= prev_macd_sig and cur_macd > cur_macd_sig,
        'ibs_low': ibs < 0.2,
        'volume_spike': volume_spike and spy_chg < 0,
        'consecutive_down': down_days >= 3,
    }
    call_score = sum(call_factors.values())
    
    # --- PUT FACTORS (7) ---
    put_factors = {
        'rsi_overbought': rsi5 > 70,
        'vix_crushed': vix_close < 14 or (vix_close < 18 and vix_chg < -10),
        'price_resistance': ((dist_ema20 > 0 and dist_ema20 < 2) or 
                             (dist_sma50 > 0 and dist_sma50 < 3) or
                             dist_ema20 > 3 or dist_sma50 > 5),
        'macd_bearish': prev_macd >= prev_macd_sig and cur_macd < cur_macd_sig,
        'ibs_high': ibs > 0.8,
        'volume_spike': volume_spike and spy_chg > 0,
        'consecutive_up': up_days >= 3,
    }
    put_score = sum(put_factors.values())
    
    return {
        'date': spy.index[idx].strftime('%Y-%m-%d'),
        'spy_close': spy_close,
        'spy_chg': spy_chg,
        'vix_close': vix_close,
        'rsi5': rsi5,
        'sma200_slope': sma200_slope,
        'call_score': call_score,
        'put_score': put_score,
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

# --- Run Backtest ---
def run_backtest():
    spy, vix, error = fetch_historical()
    if error:
        print(f"ERROR: {error}")
        return
    
    warmup = 250
    trades = {'CALL': [], 'PUT': []}
    
    print(f"\nBacktesting from {spy.index[warmup].date()} to {spy.index[-1].date()}")
    print("Thresholds: Calls 4+, Puts 5+")
    print("=" * 70)
    
    for i in range(warmup, len(spy)):
        if i % 100 == 0:
            print(f"Processing... {i}/{len(spy)} days")
        
        signals = compute_signals_for_day(spy, vix, i)
        
        # Calls at 4+
        if signals['call_score'] >= 4:
            ret, exit_date, reason, days = simulate_trade(
                spy, i, 'CALL', HOLD_DAYS, STOP_LOSS, TAKE_PROFIT
            )
            trades['CALL'].append({
                'entry_date': signals['date'],
                'exit_date': exit_date,
                'direction': 'CALL',
                'score': signals['call_score'],
                'entry_price': signals['spy_close'],
                'return': ret,
                'exit_reason': reason,
                'days_held': days,
                'sma200_slope': signals['sma200_slope'],
            })
        
        # Puts at 5+ (stricter)
        if signals['put_score'] >= 5:
            ret, exit_date, reason, days = simulate_trade(
                spy, i, 'PUT', HOLD_DAYS, STOP_LOSS, TAKE_PROFIT
            )
            trades['PUT'].append({
                'entry_date': signals['date'],
                'exit_date': exit_date,
                'direction': 'PUT',
                'score': signals['put_score'],
                'entry_price': signals['spy_close'],
                'return': ret,
                'exit_reason': reason,
                'days_held': days,
                'sma200_slope': signals['sma200_slope'],
            })
    
    return trades

# --- Analyze Results ---
def analyze_results(trades):
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS - HYBRID THRESHOLDS")
    print("Calls: 4+ of 7 | Puts: 5+ of 7")
    print("=" * 70)
    
    for direction in ['CALL', 'PUT']:
        all_trades = trades[direction]
        if not all_trades:
            print(f"\n{direction}: No trades generated")
            continue
        
        print(f"\n📈 {direction} OPTIONS SUMMARY")
        print("-" * 50)
        print(f"Total trades: {len(all_trades)}")
        
        # By score
        for score in [4, 5, 6, 7]:
            score_trades = [t for t in all_trades if t['score'] == score]
            if not score_trades:
                continue
            
            wins = sum(1 for t in score_trades if t['return'] > 0)
            win_rate = (wins / len(score_trades)) * 100
            avg_return = sum(t['return'] for t in score_trades) / len(score_trades)
            
            print(f"  Score {score}/7: {len(score_trades)} trades, {win_rate:.1f}% win, {avg_return*100:+.1f}% avg")
        
        # All
        wins = sum(1 for t in all_trades if t['return'] > 0)
        win_rate = (wins / len(all_trades)) * 100
        avg_return = sum(t['return'] for t in all_trades) / len(all_trades)
        print(f"\n  ALL TRADES ({len(all_trades)}):")
        print(f"    Win rate: {win_rate:.1f}%")
        print(f"    Avg return per trade: {avg_return*100:+.1f}%")
        
        # By regime
        bull_trades = [t for t in all_trades if t['sma200_slope'] > 0]
        bear_trades = [t for t in all_trades if t['sma200_slope'] <= 0]
        
        print(f"\n  BY MARKET REGIME:")
        if bull_trades:
            wins = sum(1 for t in bull_trades if t['return'] > 0)
            wr = (wins / len(bull_trades)) * 100
            avg = sum(t['return'] for t in bull_trades) / len(bull_trades)
            print(f"    Bullish trend ({len(bull_trades)}): {wr:.1f}% win, {avg*100:+.1f}% avg")
        
        if bear_trades:
            wins = sum(1 for t in bear_trades if t['return'] > 0)
            wr = (wins / len(bear_trades)) * 100
            avg = sum(t['return'] for t in bear_trades) / len(bear_trades)
            print(f"    Bearish trend ({len(bear_trades)}): {wr:.1f}% win, {avg*100:+.1f}% avg")
    
    # Combined
    print("\n" + "=" * 70)
    print("COMBINED PERFORMANCE")
    print("=" * 70)
    all_trades = trades['CALL'] + trades['PUT']
    if all_trades:
        wins = sum(1 for t in all_trades if t['return'] > 0)
        win_rate = (wins / len(all_trades)) * 100
        avg_return = sum(t['return'] for t in all_trades) / len(all_trades)
        
        print(f"Total trades: {len(all_trades)}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Avg return: {avg_return*100:+.1f}%")
        
        returns = [t['return'] for t in all_trades]
        if len(returns) > 1:
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(26)
            print(f"Approx Sharpe: {sharpe:.2f}")

# --- Main ---
if __name__ == "__main__":
    print("SPY Options Signal Backtest - Hybrid Thresholds")
    print("=" * 70)
    
    trades = run_backtest()
    if trades:
        analyze_results(trades)
