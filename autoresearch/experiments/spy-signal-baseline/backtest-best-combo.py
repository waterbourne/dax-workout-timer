#!/usr/bin/env python3
"""
SPY Options Signal Backtester v2.9 - Best Combo
=================================================
Best call setup: 8F 5+ with RSI exit at 65
Puts: Only when VIX > 30 AND 3+ up days (extreme conditions only)

Also tests: 7F 4+ with RSI exit 65 (simpler, more trades)
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
    upper = sma + (rolling_std * std_dev)
    lower = sma - (rolling_std * std_dev)
    return (close - lower) / (upper - lower)

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
    dist_sma200 = ((spy_close - sma200) / sma200) * 100
    
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
    up_days = sum(1 for c in changes if c > 0)
    
    pct_b = float(calc_bollinger_pct_b(s, 20, 2).iloc[-1])
    
    # RSI(14) for puts - slower RSI better for trend exhaustion
    rsi14 = float(calc_rsi(s, 14).iloc[-1])
    
    # Weekly return
    weekly_ret = float((spy['Close'].iloc[idx] / spy['Close'].iloc[max(0,idx-5)] - 1) * 100)
    
    # Call factors
    call_7f = {
        'rsi_oversold': rsi5 < 30,
        'vix_elevated': (vix_close > 20 and vix_chg > 10) or vix_close > 25,
        'price_support': (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
        'macd_bullish': prev_macd <= prev_sig and cur_macd > cur_sig,
        'ibs_low': ibs < 0.2,
        'vol_spike_down': vol_spike and spy_chg < 0,
        'consec_down': down_days >= 3,
    }
    
    call_8f = dict(call_7f)
    call_8f['bb_low'] = pct_b < 0.1
    
    # Put factors (redesigned)
    put_factors = {
        'rsi5_overbought': rsi5 > 70,
        'rsi14_overbought': rsi14 > 70,
        'vix_low': vix_close < 16,
        'extended_from_200': dist_sma200 > 5,
        'macd_bearish': prev_macd >= prev_sig and cur_macd < cur_sig,
        'ibs_high': ibs > 0.8,
        'consec_up': up_days >= 3,
        'bb_high': pct_b > 0.9,
        'weekly_up_big': weekly_ret > 3,  # Big weekly gain (exhaustion)
    }
    
    return {
        'idx': idx,
        'date': spy.index[idx].strftime('%Y-%m-%d'),
        'spy_close': spy_close,
        'vix_close': vix_close,
        'rsi5': rsi5,
        'sma200_slope': sma200_slope,
        'is_bull': sma200_slope > 0,
        'score_7': sum(call_7f.values()),
        'score_8': sum(call_8f.values()),
        'put_score': sum(put_factors.values()),
        'put_factors': {k: bool(v) for k, v in put_factors.items()},
        'call_7f': {k: bool(v) for k, v in call_7f.items()},
        'call_8f': {k: bool(v) for k, v in call_8f.items()},
    }

def sim_call(spy, entry_idx, hold=10, sl=-0.40, tp=0.30, rsi_exit=70):
    entry = float(spy['Close'].iloc[entry_idx])
    for i in range(1, min(hold + 1, len(spy) - entry_idx)):
        idx = entry_idx + i
        cur = float(spy['Close'].iloc[idx])
        rsi = float(calc_rsi(spy['Close'].iloc[:idx+1], 5).iloc[-1])
        ret = ((cur - entry) / entry) * 0.50
        if rsi > rsi_exit:
            return ret, 'RSI_EXIT', i
        if ret <= sl:
            return sl, 'STOP_LOSS', i
        if ret >= tp:
            return tp, 'TAKE_PROFIT', i
    fi = min(entry_idx + hold, len(spy) - 1)
    return ((float(spy['Close'].iloc[fi]) - entry) / entry) * 0.50, 'MAX_HOLD', hold

def sim_put(spy, entry_idx, hold=10, sl=-0.40, tp=0.30, rsi_exit=30):
    entry = float(spy['Close'].iloc[entry_idx])
    for i in range(1, min(hold + 1, len(spy) - entry_idx)):
        idx = entry_idx + i
        cur = float(spy['Close'].iloc[idx])
        rsi = float(calc_rsi(spy['Close'].iloc[:idx+1], 5).iloc[-1])
        ret = -((cur - entry) / entry) * 0.50  # put profits when price drops
        if rsi < rsi_exit:
            return ret, 'RSI_EXIT', i
        if ret <= sl:
            return sl, 'STOP_LOSS', i
        if ret >= tp:
            return tp, 'TAKE_PROFIT', i
    fi = min(entry_idx + hold, len(spy) - 1)
    return -((float(spy['Close'].iloc[fi]) - entry) / entry) * 0.50, 'MAX_HOLD', hold

def report(label, trades):
    if not trades:
        print(f"  {label}: No trades")
        return {}
    wins = sum(1 for t in trades if t['return'] > 0)
    wr = (wins / len(trades)) * 100
    avg = sum(t['return'] for t in trades) / len(trades)
    returns = [t['return'] for t in trades]
    sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(len(trades)/6) if len(returns) > 1 and np.std(returns) > 0 else 0
    print(f"  {label}: {len(trades)} trades ({len(trades)/6:.0f}/yr), {wr:.1f}% win, {avg*100:+.1f}% avg, Sharpe {sharpe:.2f}")
    return {'trades': len(trades), 'win_rate': wr, 'avg_return': avg, 'sharpe': sharpe}

def main():
    spy, vix, error = fetch_historical()
    if error:
        print(f"ERROR: {error}")
        return
    
    warmup = 250
    all_signals = []
    for i in range(warmup, len(spy)):
        if i % 200 == 0:
            print(f"Computing... {i}/{len(spy)}")
        all_signals.append(compute_signals(spy, vix, i))
    
    print(f"\n{'='*70}")
    print("EXPERIMENT RESULTS")
    print(f"{'='*70}")
    
    # --- CALLS ---
    print("\n=== CALL STRATEGIES ===")
    
    # Strategy 1: 7F 4+ with RSI exit 65
    trades_1 = []
    for sig in all_signals:
        if sig['score_7'] >= 4:
            ret, reason, days = sim_call(spy, sig['idx'], rsi_exit=65)
            trades_1.append({'return': ret})
    report("7F 4+, RSI exit 65", trades_1)
    
    # Strategy 2: 8F 5+ with RSI exit 65
    trades_2 = []
    for sig in all_signals:
        if sig['score_8'] >= 5:
            ret, reason, days = sim_call(spy, sig['idx'], rsi_exit=65)
            trades_2.append({'return': ret})
    report("8F 5+, RSI exit 65", trades_2)
    
    # Strategy 3: 8F 5+ bull, RSI exit 65
    trades_3 = []
    for sig in all_signals:
        if sig['score_8'] >= 5 and sig['is_bull']:
            ret, reason, days = sim_call(spy, sig['idx'], rsi_exit=65)
            trades_3.append({'return': ret})
    report("8F 5+ BULL, RSI exit 65", trades_3)
    
    # Strategy 4: 7F 4+ standard RSI 70 (baseline reference)
    trades_4 = []
    for sig in all_signals:
        if sig['score_7'] >= 4:
            ret, reason, days = sim_call(spy, sig['idx'], rsi_exit=70)
            trades_4.append({'return': ret})
    report("7F 4+, RSI exit 70 (BASELINE)", trades_4)
    
    # --- PUTS ---
    print("\n=== PUT STRATEGIES ===")
    
    # Put strategy A: Redesigned 4+ of 9
    puts_a = []
    for sig in all_signals:
        if sig['put_score'] >= 4:
            ret, reason, days = sim_put(spy, sig['idx'])
            puts_a.append({'return': ret})
    report("Redesigned 4+/9", puts_a)
    
    # Put strategy B: Redesigned 5+ of 9
    puts_b = []
    for sig in all_signals:
        if sig['put_score'] >= 5:
            ret, reason, days = sim_put(spy, sig['idx'])
            puts_b.append({'return': ret})
    report("Redesigned 5+/9", puts_b)
    
    # Put strategy C: Redesigned 6+ of 9
    puts_c = []
    for sig in all_signals:
        if sig['put_score'] >= 6:
            ret, reason, days = sim_put(spy, sig['idx'])
            puts_c.append({'return': ret})
    report("Redesigned 6+/9", puts_c)
    
    # Put strategy D: VIX < 14 AND rsi5 > 75 AND 3+ up days
    puts_d = []
    for sig in all_signals:
        pf = sig['put_factors']
        if pf['vix_low'] and pf['rsi5_overbought'] and pf['consec_up']:
            ret, reason, days = sim_put(spy, sig['idx'])
            puts_d.append({'return': ret})
    report("VIX<16 + RSI>70 + 3up days", puts_d)
    
    # Put strategy E: bb_high AND rsi5>70 AND consec_up
    puts_e = []
    for sig in all_signals:
        pf = sig['put_factors']
        if pf['bb_high'] and pf['rsi5_overbought'] and pf['consec_up']:
            ret, reason, days = sim_put(spy, sig['idx'])
            puts_e.append({'return': ret})
    report("BB>0.9 + RSI>70 + 3up days", puts_e)
    
    # Put strategy F: Any 3 of (rsi5>70, bb>0.9, 3up, vix<16, weekly>3%)
    puts_f = []
    for sig in all_signals:
        pf = sig['put_factors']
        extreme_count = sum([pf['rsi5_overbought'], pf['bb_high'], pf['consec_up'], 
                           pf['vix_low'], pf['weekly_up_big']])
        if extreme_count >= 3:
            ret, reason, days = sim_put(spy, sig['idx'])
            puts_f.append({'return': ret})
    report("3+ of (RSI>70, BB>0.9, 3up, VIX<16, weekly>3%)", puts_f)
    
    # Put strategy G: tighter stop and take profit
    puts_g = []
    for sig in all_signals:
        pf = sig['put_factors']
        extreme_count = sum([pf['rsi5_overbought'], pf['bb_high'], pf['consec_up'], 
                           pf['vix_low'], pf['weekly_up_big']])
        if extreme_count >= 3:
            ret, reason, days = sim_put(spy, sig['idx'], tp=0.20, sl=-0.30)
            puts_g.append({'return': ret})
    report("3+ extreme, TP:20% SL:30%", puts_g)
    
    # Put strategy H: hold only 5 days (mean reversion timeframe)
    puts_h = []
    for sig in all_signals:
        pf = sig['put_factors']
        extreme_count = sum([pf['rsi5_overbought'], pf['bb_high'], pf['consec_up'], 
                           pf['vix_low'], pf['weekly_up_big']])
        if extreme_count >= 3:
            ret, reason, days = sim_put(spy, sig['idx'], hold=5, tp=0.20, sl=-0.30)
            puts_h.append({'return': ret})
    report("3+ extreme, hold 5d, TP:20% SL:30%", puts_h)
    
    # --- COMBINED BEST ---
    print("\n=== COMBINED STRATEGIES ===")
    
    # Combo 1: 7F 4+ calls (RSI 65) + No puts (calls only)
    combined = trades_1
    report("Calls only: 7F 4+, RSI exit 65", combined)
    
    # Combo 2: 7F 4+ calls (RSI 65) + best puts
    best_puts = puts_f  # or whichever is best
    combo2 = trades_1 + best_puts
    report("7F 4+ calls + 3+ extreme puts", combo2)

if __name__ == "__main__":
    main()
