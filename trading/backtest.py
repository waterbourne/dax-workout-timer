#!/usr/bin/env python3
"""
SPY Options Signal Backtester
=============================
Backtests the call/put signals on 5+ years of historical SPY data.

Simulates buying 10-14 DTE ATM options on signal days, holding for:
- 10 days (max)
- RSI reversal exit (calls: RSI>70, puts: RSI<30)
- Stop loss: -40%
- Take profit: +30%

Reports: Win rate, avg return, max drawdown, expectancy by signal strength.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pip3 install yfinance pandas numpy")
    sys.exit(1)

# --- Configuration ---
BACKTEST_YEARS = 7
HOLD_DAYS = 10
STOP_LOSS = -0.40
TAKE_PROFIT = 0.30
OPTION_PREMIUM_FACTOR = 0.50  # ATM option moves ~50% of SPY move

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
    """Slope of SMA as percentage change per day"""
    sma = calc_sma(series, period)
    return (sma.diff(5) / sma.shift(5)) * 100  # 5-day change percentage

# --- Fetch Historical Data ---
def fetch_historical():
    print("Fetching 7 years of SPY data...")
    spy = yf.download("SPY", period="7y", interval="1d", progress=False)
    vix = yf.download("^VIX", period="7y", interval="1d", progress=False)
    
    if spy.empty or vix.empty:
        return None, None, "Failed to fetch data"
    
    # Flatten columns
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)
    
    return spy, vix, None

# --- Signal Calculation for a Single Day ---
def compute_signals_for_day(spy, vix, idx):
    """Compute all indicators and signals for a specific date index"""
    
    spy_close = float(spy['Close'].iloc[idx])
    spy_prev = float(spy['Close'].iloc[idx-1])
    spy_high = float(spy['High'].iloc[idx])
    spy_low = float(spy['Low'].iloc[idx])
    spy_chg = ((spy_close - spy_prev) / spy_prev) * 100
    
    vix_close = float(vix['Close'].iloc[idx])
    vix_prev = float(vix['Close'].iloc[idx-1])
    vix_chg = ((vix_close - vix_prev) / vix_prev) * 100
    
    # Get historical series up to this point
    spy_close_series = spy['Close'].iloc[:idx+1]
    spy_high_series = spy['High'].iloc[:idx+1]
    spy_low_series = spy['Low'].iloc[:idx+1]
    vix_close_series = vix['Close'].iloc[:idx+1]
    
    rsi5 = float(calc_rsi(spy_close_series, 5).iloc[-1])
    rsi14 = float(calc_rsi(spy_close_series, 14).iloc[-1])
    ema20 = float(calc_ema(spy_close_series, 20).iloc[-1])
    sma50 = float(calc_sma(spy_close_series, 50).iloc[-1])
    sma200 = float(calc_sma(spy_close_series, 200).iloc[-1])
    
    dist_ema20 = ((spy_close - ema20) / ema20) * 100
    dist_sma50 = ((spy_close - sma50) / sma50) * 100
    dist_sma200 = ((spy_close - sma200) / sma200) * 100
    
    # MACD
    macd_line, macd_sig = calc_macd(spy_close_series)
    cur_macd = float(macd_line.iloc[-1])
    cur_macd_sig = float(macd_sig.iloc[-1])
    prev_macd = float(macd_line.iloc[-2])
    prev_macd_sig = float(macd_sig.iloc[-2])
    
    # IBS
    ibs = float(calc_ibs(spy_high_series, spy_low_series, spy_close_series).iloc[-1])
    
    # SMA 200 slope (regime filter)
    sma200_slope = float(calc_sma_slope(spy_close_series, 200).iloc[-1])
    
    # Volume confirmation
    avg_volume = spy['Volume'].iloc[idx-20:idx].mean()
    cur_volume = float(spy['Volume'].iloc[idx])
    volume_spike = (cur_volume / avg_volume) > 1.5 if avg_volume > 0 else False
    
    # Consecutive days
    spy_changes = spy['Close'].iloc[idx-5:idx].pct_change().dropna()
    down_days = sum(1 for c in spy_changes if c < 0)
    up_days = sum(1 for c in spy_changes if c > 0)
    
    # --- CALL FACTORS ---
    call_factors = {
        'rsi_oversold': rsi5 < 30,
        'vix_elevated': (vix_close > 20 and vix_chg > 10) or vix_close > 25,
        'price_support': (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
        'macd_bullish': prev_macd <= prev_macd_sig and cur_macd > cur_macd_sig,
        'ibs_low': ibs < 0.2,
        # New factors
        'volume_spike': volume_spike and spy_chg < 0,  # Down on high volume
        'consecutive_down': down_days >= 3,
    }
    call_score = sum(call_factors.values())
    
    # --- PUT FACTORS ---
    put_factors = {
        'rsi_overbought': rsi5 > 70,
        'vix_crushed': vix_close < 14 or (vix_close < 18 and vix_chg < -10),
        'price_resistance': ((dist_ema20 > 0 and dist_ema20 < 2) or 
                             (dist_sma50 > 0 and dist_sma50 < 3) or
                             dist_ema20 > 3 or dist_sma50 > 5),
        'macd_bearish': prev_macd >= prev_macd_sig and cur_macd < cur_macd_sig,
        'ibs_high': ibs > 0.8,
        # New factors
        'volume_spike': volume_spike and spy_chg > 0,  # Up on high volume
        'consecutive_up': up_days >= 3,
    }
    put_score = sum(put_factors.values())
    
    return {
        'date': spy.index[idx].strftime('%Y-%m-%d'),
        'spy_close': spy_close,
        'spy_chg': spy_chg,
        'vix_close': vix_close,
        'rsi5': rsi5,
        'dist_ema20': dist_ema20,
        'dist_sma50': dist_sma50,
        'dist_sma200': dist_sma200,
        'sma200_slope': sma200_slope,
        'volume_spike': volume_spike,
        'down_days': down_days,
        'up_days': up_days,
        'call_score': call_score,
        'put_score': put_score,
        'call_factors': call_factors,
        'put_factors': put_factors,
    }

# --- Simulate Trade ---
def simulate_trade(spy, entry_idx, direction, hold_days, stop_loss, take_profit):
    """
    Simulate holding an option from entry_idx for hold_days or until exit condition
    Returns: return_pct, exit_date, exit_reason, days_held
    """
    entry_price = float(spy['Close'].iloc[entry_idx])
    entry_rsi = float(calc_rsi(spy['Close'].iloc[:entry_idx+1], 5).iloc[-1])
    
    for i in range(1, min(hold_days + 1, len(spy) - entry_idx)):
        idx = entry_idx + i
        current_price = float(spy['Close'].iloc[idx])
        current_rsi = float(calc_rsi(spy['Close'].iloc[:idx+1], 5).iloc[-1])
        
        # Calculate SPY return
        spy_return = (current_price - entry_price) / entry_price
        
        # Option return (ATM options move ~50% of SPY)
        if direction == 'CALL':
            option_return = spy_return * OPTION_PREMIUM_FACTOR
            # RSI exit
            if current_rsi > 70:
                return option_return, spy.index[idx].strftime('%Y-%m-%d'), 'RSI_EXIT', i
        else:  # PUT
            option_return = -spy_return * OPTION_PREMIUM_FACTOR
            # RSI exit
            if current_rsi < 30:
                return option_return, spy.index[idx].strftime('%Y-%m-%d'), 'RSI_EXIT', i
        
        # Stop loss
        if option_return <= stop_loss:
            return stop_loss, spy.index[idx].strftime('%Y-%m-%d'), 'STOP_LOSS', i
        
        # Take profit
        if option_return >= take_profit:
            return take_profit, spy.index[idx].strftime('%Y-%m-%d'), 'TAKE_PROFIT', i
    
    # Max hold period reached
    final_idx = entry_idx + hold_days
    if final_idx >= len(spy):
        final_idx = len(spy) - 1
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
    
    # Need warmup for 200 SMA
    warmup = 250
    trades = {'CALL': [], 'PUT': []}
    
    print(f"\nBacktesting from {spy.index[warmup].date()} to {spy.index[-1].date()}")
    print("=" * 70)
    
    for i in range(warmup, len(spy)):
        if i % 100 == 0:
            print(f"Processing... {i}/{len(spy)} days")
        
        signals = compute_signals_for_day(spy, vix, i)
        
        # Check for call signal
        if signals['call_score'] >= 3:
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
                'volume_spike': signals['volume_spike'],
            })
        
        # Check for put signal
        if signals['put_score'] >= 3:
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
                'volume_spike': signals['volume_spike'],
            })
    
    return trades

# --- Analyze Results ---
def analyze_results(trades):
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
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
        for score in [3, 4, 5, 6, 7]:
            score_trades = [t for t in all_trades if t['score'] == score]
            if not score_trades:
                continue
            
            wins = sum(1 for t in score_trades if t['return'] > 0)
            losses = len(score_trades) - wins
            win_rate = (wins / len(score_trades)) * 100
            avg_return = sum(t['return'] for t in score_trades) / len(score_trades)
            max_return = max(t['return'] for t in score_trades)
            min_return = min(t['return'] for t in score_trades)
            
            print(f"\n  Score {score}/7: {len(score_trades)} trades")
            print(f"    Win rate: {wins}/{len(score_trades)} ({win_rate:.1f}%)")
            print(f"    Avg return: {avg_return*100:+.1f}%")
            print(f"    Max gain: {max_return*100:+.1f}%")
            print(f"    Max loss: {min_return*100:+.1f}%")
        
        # Combined 3+ score
        all_valid = [t for t in all_trades if t['score'] >= 3]
        wins = sum(1 for t in all_valid if t['return'] > 0)
        win_rate = (wins / len(all_valid)) * 100
        avg_return = sum(t['return'] for t in all_valid) / len(all_valid)
        total_return = sum(t['return'] for t in all_valid)
        
        print(f"\n  ALL SCORES 3+ ({len(all_valid)} trades):")
        print(f"    Win rate: {wins}/{len(all_valid)} ({win_rate:.1f}%)")
        print(f"    Avg return per trade: {avg_return*100:+.1f}%")
        print(f"    Total return (no compounding): {total_return*100:+.1f}%")
        
        # 4+ only (higher conviction)
        high_conviction = [t for t in all_trades if t['score'] >= 4]
        if high_conviction:
            wins = sum(1 for t in high_conviction if t['return'] > 0)
            win_rate = (wins / len(high_conviction)) * 100
            avg_return = sum(t['return'] for t in high_conviction) / len(high_conviction)
            print(f"\n  SCORE 4+ ONLY ({len(high_conviction)} trades):")
            print(f"    Win rate: {wins}/{len(high_conviction)} ({win_rate:.1f}%)")
            print(f"    Avg return per trade: {avg_return*100:+.1f}%")
        
        # By regime (200 SMA slope)
        print(f"\n  BY MARKET REGIME (200 SMA slope):")
        bullish_regime = [t for t in all_valid if t['sma200_slope'] > 0]
        bearish_regime = [t for t in all_valid if t['sma200_slope'] <= 0]
        
        if bullish_regime:
            wins = sum(1 for t in bullish_regime if t['return'] > 0)
            wr = (wins / len(bullish_regime)) * 100
            avg = sum(t['return'] for t in bullish_regime) / len(bullish_regime)
            print(f"    Bullish trend ({len(bullish_regime)}): {wr:.1f}% win, {avg*100:+.1f}% avg")
        
        if bearish_regime:
            wins = sum(1 for t in bearish_regime if t['return'] > 0)
            wr = (wins / len(bearish_regime)) * 100
            avg = sum(t['return'] for t in bearish_regime) / len(bearish_regime)
            print(f"    Bearish trend ({len(bearish_regime)}): {wr:.1f}% win, {avg*100:+.1f}% avg")
        
        # By volume
        vol_spike = [t for t in all_valid if t['volume_spike']]
        if vol_spike:
            wins = sum(1 for t in vol_spike if t['return'] > 0)
            wr = (wins / len(vol_spike)) * 100
            avg = sum(t['return'] for t in vol_spike) / len(vol_spike)
            print(f"\n  With volume spike ({len(vol_spike)}): {wr:.1f}% win, {avg*100:+.1f}% avg")
        
        # Exit reasons
        print(f"\n  EXIT REASONS:")
        for reason in ['TAKE_PROFIT', 'STOP_LOSS', 'RSI_EXIT', 'MAX_HOLD']:
            count = sum(1 for t in all_valid if t['exit_reason'] == reason)
            if count > 0:
                print(f"    {reason}: {count}")
    
    # Combined performance
    print("\n" + "=" * 70)
    print("COMBINED CALLS + PUTS")
    print("=" * 70)
    all_trades = trades['CALL'] + trades['PUT']
    if all_trades:
        all_3plus = [t for t in all_trades if t['score'] >= 3]
        wins = sum(1 for t in all_3plus if t['return'] > 0)
        win_rate = (wins / len(all_3plus)) * 100
        avg_return = sum(t['return'] for t in all_3plus) / len(all_3plus)
        total = sum(t['return'] for t in all_3plus)
        
        print(f"All 3+ signals: {len(all_3plus)} trades")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Avg return: {avg_return*100:+.1f}%")
        print(f"Total return: {total*100:+.1f}%")
        
        # Rough Sharpe estimate
        returns = [t['return'] for t in all_3plus]
        if len(returns) > 1:
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(26)  # ~26 trades/year
            print(f"Approx Sharpe (annualized): {sharpe:.2f}")

# --- Main ---
if __name__ == "__main__":
    print("SPY Options Signal Backtest")
    print("=" * 70)
    
    trades = run_backtest()
    if trades:
        analyze_results(trades)
        
        # Save detailed trade log
        log_file = Path(__file__).parent / "backtest-trades.json"
        with open(log_file, 'w') as f:
            json.dump(trades, f, indent=2)
        print(f"\nDetailed trade log saved to: {log_file}")
