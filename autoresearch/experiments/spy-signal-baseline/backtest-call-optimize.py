#!/usr/bin/env python3
"""
SPY Options Signal Backtester v2.8 - Call Optimization Focus
=============================================================
Focus on maximizing call performance since puts are structurally weak.

Tests:
A) Original 7 factors, calls at 4+ (baseline: 72.8%)
B) Original 7 factors, calls at 5+ 
C) 8 factors (with BB), calls at 5+ (prev test: 72.1% overall, 75% in bull)
D) 8 factors (with BB), calls at 4+ but require consecutive_down OR bb_low
E) Calls-only (disable puts entirely) — what's the Sharpe?

Also tests modified exit rules:
- Tighter take profit: +20% instead of +30%
- Looser RSI exit: RSI > 65 instead of 70
"""

import sys
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pip3 install yfinance pandas numpy")
    sys.exit(1)

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

# --- Fetch ---
def fetch_historical():
    print("Fetching 7 years of SPY data...")
    spy = yf.download("SPY", period="7y", interval="1d", progress=False)
    vix = yf.download("^VIX", period="7y", interval="1d", progress=False)
    if spy.empty or vix.empty:
        return None, None, "Failed"
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)
    return spy, vix, None

# --- Compute signals ---
def compute_signals(spy, vix, idx):
    spy_close = float(spy['Close'].iloc[idx])
    spy_prev = float(spy['Close'].iloc[idx-1])
    spy_chg = ((spy_close - spy_prev) / spy_prev) * 100
    
    vix_close = float(vix['Close'].iloc[idx])
    vix_prev = float(vix['Close'].iloc[idx-1])
    vix_chg = ((vix_close - vix_prev) / vix_prev) * 100
    
    s = spy['Close'].iloc[:idx+1]
    h = spy['High'].iloc[:idx+1]
    l = spy['Low'].iloc[:idx+1]
    
    rsi5 = float(calc_rsi(s, 5).iloc[-1])
    ema20 = float(calc_ema(s, 20).iloc[-1])
    sma50 = float(calc_sma(s, 50).iloc[-1])
    sma200 = float(calc_sma(s, 200).iloc[-1])
    
    dist_ema20 = ((spy_close - ema20) / ema20) * 100
    dist_sma50 = ((spy_close - sma50) / sma50) * 100
    
    ml, ms = calc_macd(s)
    cur_macd, cur_sig = float(ml.iloc[-1]), float(ms.iloc[-1])
    prev_macd, prev_sig = float(ml.iloc[-2]), float(ms.iloc[-2])
    
    ibs = float(calc_ibs(h, l, s).iloc[-1])
    sma200_slope = float(calc_sma_slope(s, 200).iloc[-1])
    
    avg_vol = spy['Volume'].iloc[idx-20:idx].mean()
    cur_vol = float(spy['Volume'].iloc[idx])
    vol_spike = (cur_vol / avg_vol) > 1.5 if avg_vol > 0 else False
    
    changes = spy['Close'].iloc[idx-5:idx].pct_change().dropna()
    down_days = sum(1 for c in changes if c < 0)
    
    pct_b = float(calc_bollinger_pct_b(s, 20, 2).iloc[-1])
    
    return {
        'date': spy.index[idx].strftime('%Y-%m-%d'),
        'idx': idx,
        'spy_close': spy_close,
        'rsi5': rsi5,
        'sma200_slope': sma200_slope,
        'is_bull': sma200_slope > 0,
        # Individual factors
        'rsi_oversold': rsi5 < 30,
        'vix_elevated': (vix_close > 20 and vix_chg > 10) or vix_close > 25,
        'price_support': (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
        'macd_bullish': prev_macd <= prev_sig and cur_macd > cur_sig,
        'ibs_low': ibs < 0.2,
        'vol_spike_down': vol_spike and spy_chg < 0,
        'consec_down': down_days >= 3,
        'bb_low': pct_b < 0.1,
        # Scores
        'score_7': sum([rsi5 < 30,
                       (vix_close > 20 and vix_chg > 10) or vix_close > 25,
                       (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
                       prev_macd <= prev_sig and cur_macd > cur_sig,
                       ibs < 0.2,
                       vol_spike and spy_chg < 0,
                       down_days >= 3]),
        'score_8': sum([rsi5 < 30,
                       (vix_close > 20 and vix_chg > 10) or vix_close > 25,
                       (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
                       prev_macd <= prev_sig and cur_macd > cur_sig,
                       ibs < 0.2,
                       vol_spike and spy_chg < 0,
                       down_days >= 3,
                       pct_b < 0.1]),
    }

# --- Simulate ---
def sim(spy, entry_idx, hold=10, sl=-0.40, tp=0.30, rsi_exit=70):
    entry = float(spy['Close'].iloc[entry_idx])
    for i in range(1, min(hold + 1, len(spy) - entry_idx)):
        idx = entry_idx + i
        cur = float(spy['Close'].iloc[idx])
        rsi = float(calc_rsi(spy['Close'].iloc[:idx+1], 5).iloc[-1])
        ret = ((cur - entry) / entry) * 0.50  # call option return
        if rsi > rsi_exit:
            return ret, 'RSI_EXIT', i
        if ret <= sl:
            return sl, 'STOP_LOSS', i
        if ret >= tp:
            return tp, 'TAKE_PROFIT', i
    
    fi = min(entry_idx + hold, len(spy) - 1)
    final = float(spy['Close'].iloc[fi])
    return ((final - entry) / entry) * 0.50, 'MAX_HOLD', hold

def run_config(all_signals, spy, label, filter_fn, hold=10, sl=-0.40, tp=0.30, rsi_exit=70):
    """Run a specific config and return results"""
    trades = []
    for sig in all_signals:
        if filter_fn(sig):
            ret, reason, days = sim(spy, sig['idx'], hold, sl, tp, rsi_exit)
            trades.append({'return': ret, 'reason': reason, 'date': sig['date'],
                          'score_7': sig['score_7'], 'score_8': sig['score_8'],
                          'is_bull': sig['is_bull']})
    
    if not trades:
        print(f"  {label}: No trades")
        return
    
    wins = sum(1 for t in trades if t['return'] > 0)
    wr = (wins / len(trades)) * 100
    avg = sum(t['return'] for t in trades) / len(trades)
    total = sum(t['return'] for t in trades)
    returns = [t['return'] for t in trades]
    sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(len(trades)/6) if len(returns) > 1 and np.std(returns) > 0 else 0
    
    # Per year
    years = 6
    trades_per_year = len(trades) / years
    
    # By regime
    bull = [t for t in trades if t['is_bull']]
    bear = [t for t in trades if not t['is_bull']]
    
    bull_wr = (sum(1 for t in bull if t['return'] > 0) / len(bull) * 100) if bull else 0
    bear_wr = (sum(1 for t in bear if t['return'] > 0) / len(bear) * 100) if bear else 0
    
    print(f"\n  {label}")
    print(f"    Trades: {len(trades)} ({trades_per_year:.0f}/yr)")
    print(f"    Win rate: {wr:.1f}% | Avg return: {avg*100:+.1f}%")
    print(f"    Total return: {total*100:+.1f}% | Sharpe: {sharpe:.2f}")
    print(f"    Bull: {len(bull)} trades, {bull_wr:.1f}% win | Bear: {len(bear)} trades, {bear_wr:.1f}% win")
    
    # Exit reasons
    reasons = {}
    for t in trades:
        reasons[t['reason']] = reasons.get(t['reason'], 0) + 1
    reason_str = " | ".join(f"{k}: {v}" for k, v in sorted(reasons.items()))
    print(f"    Exits: {reason_str}")

def main():
    spy, vix, error = fetch_historical()
    if error:
        print(f"ERROR: {error}")
        return
    
    warmup = 250
    
    # Precompute signals
    print(f"\nBacktesting from {spy.index[warmup].date()} to {spy.index[-1].date()}")
    all_signals = []
    for i in range(warmup, len(spy)):
        if i % 200 == 0:
            print(f"Computing... {i}/{len(spy)}")
        all_signals.append(compute_signals(spy, vix, i))
    
    print(f"\n{'='*70}")
    print("CALL OPTIMIZATION EXPERIMENTS")
    print(f"{'='*70}")
    
    # A) Baseline: 7 factors, 4+
    print("\n--- A) Original 7 factors ---")
    run_config(all_signals, spy, "7F, 4+ threshold",
               lambda s: s['score_7'] >= 4)
    run_config(all_signals, spy, "7F, 5+ threshold",
               lambda s: s['score_7'] >= 5)
    
    # B) 8 factors (with BB), various thresholds
    print("\n--- B) 8 factors (with Bollinger Bands %B) ---")
    run_config(all_signals, spy, "8F, 4+ threshold",
               lambda s: s['score_8'] >= 4)
    run_config(all_signals, spy, "8F, 5+ threshold",
               lambda s: s['score_8'] >= 5)
    run_config(all_signals, spy, "8F, 5+ threshold, BULL ONLY",
               lambda s: s['score_8'] >= 5 and s['is_bull'])
    
    # C) Require consecutive_down OR bb_low as mandatory
    print("\n--- C) Mandatory oversold confirmation ---")
    run_config(all_signals, spy, "7F 4+ AND (consec_down OR bb_low)",
               lambda s: s['score_7'] >= 4 and (s['consec_down'] or s['bb_low']))
    run_config(all_signals, spy, "7F 4+ AND consec_down",
               lambda s: s['score_7'] >= 4 and s['consec_down'])
    run_config(all_signals, spy, "7F 3+ AND consec_down AND rsi_oversold",
               lambda s: s['score_7'] >= 3 and s['consec_down'] and s['rsi_oversold'])
    
    # D) Exit rule variations (calls 7F 4+)
    print("\n--- D) Exit rule variations (7F, 4+) ---")
    run_config(all_signals, spy, "Standard exits (TP:30%, SL:40%, RSI:70)",
               lambda s: s['score_7'] >= 4, tp=0.30, sl=-0.40, rsi_exit=70)
    run_config(all_signals, spy, "Tighter TP:20%, same SL/RSI",
               lambda s: s['score_7'] >= 4, tp=0.20, sl=-0.40, rsi_exit=70)
    run_config(all_signals, spy, "Looser RSI exit:65",
               lambda s: s['score_7'] >= 4, tp=0.30, sl=-0.40, rsi_exit=65)
    run_config(all_signals, spy, "Tighter TP:20% + RSI exit:65",
               lambda s: s['score_7'] >= 4, tp=0.20, sl=-0.40, rsi_exit=65)
    run_config(all_signals, spy, "Tighter SL:30%, same TP/RSI",
               lambda s: s['score_7'] >= 4, tp=0.30, sl=-0.30, rsi_exit=70)
    run_config(all_signals, spy, "Hold 7 days instead of 10",
               lambda s: s['score_7'] >= 4, hold=7, tp=0.30, sl=-0.40, rsi_exit=70)
    run_config(all_signals, spy, "Hold 5 days, TP:20%",
               lambda s: s['score_7'] >= 4, hold=5, tp=0.20, sl=-0.40, rsi_exit=70)

if __name__ == "__main__":
    main()
