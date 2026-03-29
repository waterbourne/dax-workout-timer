#!/usr/bin/env python3
"""
SPY Options Signal System v3.0 (Optimized)
============================================
Changes from v2.1 based on 2019-2026 backtest optimization:

1. Added consecutive days factor (7th factor for both sides)
   - Calls: 3+ down days = bounce signal
   - Puts: 3+ up days = pullback signal

2. Improved RSI exit (exit calls when RSI > 65 instead of 70)
   - Win rate: 72.8% → 73.9%

3. Regime-gated puts (bearish trend only)
   - Puts only fire when 200 SMA slope is falling
   - Prevents losing put trades during structural bull markets
   - Put win rate in bear regimes: ~42% (vs 36% overall)

4. Added Bollinger Bands %B as informational indicator

BACKTEST RESULTS (2020-2026):
  Calls 4+/7: 73.9% win rate, +0.9% avg return, ~15 trades/yr
  Calls-only Sharpe: 2.28
  Previous: 72.8% win, 0.54 Sharpe (with puts dragging performance)
"""

import sys
import json
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pip3 install yfinance pandas numpy")
    sys.exit(1)

SIGNAL_FILE = Path(__file__).parent / "signal-state.json"
LOG_FILE = Path(__file__).parent / "signal-log.json"

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

def calc_bollinger_pct_b(close, period=20, std_dev=2):
    """Bollinger Bands %B: 0 = lower band, 1 = upper band"""
    sma = calc_sma(close, period)
    rolling_std = close.rolling(window=period).std()
    upper = sma + (rolling_std * std_dev)
    lower = sma - (rolling_std * std_dev)
    return (close - lower) / (upper - lower)

# --- Fetch Data ---
def fetch_data():
    spy = yf.download("SPY", period="250d", interval="1d", progress=False)
    vix = yf.download("^VIX", period="250d", interval="1d", progress=False)
    if spy.empty or vix.empty:
        return None, None, "Failed to fetch market data"
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)
    return spy, vix, None

# --- Analyze ---
def analyze():
    spy, vix, err = fetch_data()
    if err:
        return None, err
    
    # Current values
    spy_close = float(spy['Close'].iloc[-1])
    spy_prev = float(spy['Close'].iloc[-2])
    spy_high = float(spy['High'].iloc[-1])
    spy_low = float(spy['Low'].iloc[-1])
    spy_chg = ((spy_close - spy_prev) / spy_prev) * 100
    
    vix_close = float(vix['Close'].iloc[-1])
    vix_prev = float(vix['Close'].iloc[-2])
    vix_chg = ((vix_close - vix_prev) / vix_prev) * 100
    
    # Indicators
    rsi5 = float(calc_rsi(spy['Close'], 5).iloc[-1])
    rsi14 = float(calc_rsi(spy['Close'], 14).iloc[-1])
    ema20 = float(calc_ema(spy['Close'], 20).iloc[-1])
    sma50 = float(calc_sma(spy['Close'], 50).iloc[-1])
    sma200 = float(calc_sma(spy['Close'], 200).iloc[-1])
    
    dist_ema20 = ((spy_close - ema20) / ema20) * 100
    dist_sma50 = ((spy_close - sma50) / sma50) * 100
    dist_sma200 = ((spy_close - sma200) / sma200) * 100
    
    macd_line, macd_sig = calc_macd(spy['Close'])
    cur_macd = float(macd_line.iloc[-1])
    cur_macd_sig = float(macd_sig.iloc[-1])
    prev_macd = float(macd_line.iloc[-2])
    prev_macd_sig = float(macd_sig.iloc[-2])
    
    ibs = float(calc_ibs(spy['High'], spy['Low'], spy['Close']).iloc[-1])
    
    # Volume spike
    avg_volume = spy['Volume'].iloc[-20:-1].mean()
    cur_volume = float(spy['Volume'].iloc[-1])
    volume_spike = cur_volume > (avg_volume * 1.5)
    
    # Consecutive days (last 5 trading days)
    spy_changes = spy['Close'].iloc[-6:-1].pct_change().dropna()
    down_days = sum(1 for c in spy_changes if c < 0)
    up_days = sum(1 for c in spy_changes if c > 0)
    
    # 200 SMA slope for regime detection
    sma200_prev = float(calc_sma(spy['Close'], 200).iloc[-5])
    sma200_slope = ((sma200 - sma200_prev) / sma200) * 100
    
    above_200 = spy_close > sma200
    is_bearish_regime = sma200_slope <= 0
    trend = "BEARISH" if is_bearish_regime else "BULLISH"
    
    # Bollinger Bands %B (informational)
    pct_b = float(calc_bollinger_pct_b(spy['Close'], 20, 2).iloc[-1])
    
    # --- CALL FACTORS (7) ---
    call_factors = {
        'rsi_oversold': {
            'triggered': rsi5 < 30,
            'label': f"RSI(5) = {rsi5:.1f} {'✅' if rsi5 < 30 else ''}",
        },
        'vix_fear': {
            'triggered': (vix_close > 20 and vix_chg > 10) or vix_close > 25,
            'label': f"VIX fear spike {'✅' if ((vix_close > 20 and vix_chg > 10) or vix_close > 25) else ''} ({vix_close:.1f}, {vix_chg:+.1f}%)",
        },
        'price_support': {
            'triggered': (dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3),
            'label': f"Near support EMA20/SMA50 {'✅' if ((dist_ema20 < 0 and dist_ema20 > -2) or (dist_sma50 < 0 and dist_sma50 > -3)) else ''}",
        },
        'macd_bullish': {
            'triggered': prev_macd <= prev_macd_sig and cur_macd > cur_macd_sig,
            'label': f"MACD bullish cross {'✅' if (prev_macd <= prev_macd_sig and cur_macd > cur_macd_sig) else ''}",
        },
        'ibs_low': {
            'triggered': ibs < 0.2,
            'label': f"IBS capitulation {'✅' if ibs < 0.2 else ''} ({ibs:.3f})",
        },
        'volume_spike': {
            'triggered': volume_spike and spy_chg < 0,
            'label': f"Volume spike on down {'✅' if (volume_spike and spy_chg < 0) else ''} ({cur_volume/avg_volume:.1f}x)",
        },
        'consecutive_down': {
            'triggered': down_days >= 3,
            'label': f"3+ down days {'✅' if down_days >= 3 else ''} ({down_days}/5 days)",
        },
    }
    call_score = sum(1 for f in call_factors.values() if f['triggered'])
    
    # --- PUT FACTORS (7) ---
    put_factors = {
        'rsi_overbought': {
            'triggered': rsi5 > 70,
            'label': f"RSI(5) = {rsi5:.1f} {'✅' if rsi5 > 70 else ''}",
        },
        'vix_crushed': {
            'triggered': vix_close < 14 or (vix_close < 18 and vix_chg < -10),
            'label': f"VIX complacency {'✅' if (vix_close < 14 or (vix_close < 18 and vix_chg < -10)) else ''} ({vix_close:.1f}, {vix_chg:+.1f}%)",
        },
        'price_resistance': {
            'triggered': ((dist_ema20 > 0 and dist_ema20 < 2) or (dist_sma50 > 0 and dist_sma50 < 3) or dist_ema20 > 3 or dist_sma50 > 5),
            'label': f"At/above resistance {'✅' if ((dist_ema20 > 0 and dist_ema20 < 2) or (dist_sma50 > 0 and dist_sma50 < 3) or dist_ema20 > 3 or dist_sma50 > 5) else ''}",
        },
        'macd_bearish': {
            'triggered': prev_macd >= prev_macd_sig and cur_macd < cur_macd_sig,
            'label': f"MACD bearish cross {'✅' if (prev_macd >= prev_macd_sig and cur_macd < cur_macd_sig) else ''}",
        },
        'ibs_high': {
            'triggered': ibs > 0.8,
            'label': f"IBS euphoria {'✅' if ibs > 0.8 else ''} ({ibs:.3f})",
        },
        'volume_spike_up': {
            'triggered': volume_spike and spy_chg > 0,
            'label': f"Volume spike on up {'✅' if (volume_spike and spy_chg > 0) else ''} ({cur_volume/avg_volume:.1f}x)",
        },
        'consecutive_up': {
            'triggered': up_days >= 3,
            'label': f"3+ up days {'✅' if up_days >= 3 else ''} ({up_days}/5 days)",
        },
    }
    put_score = sum(1 for f in put_factors.values() if f['triggered'])
    
    # Signal strength — calls always active, puts regime-gated
    def call_signal(score):
        if score >= 5: return "🔥 FIRE", True
        if score >= 4: return "🟢 STRONG", True
        if score >= 3: return "🟡 MODERATE", False
        return "🔴 NO SIGNAL", False
    
    def put_signal(score, is_bearish):
        """Puts only alert in bearish regimes (200 SMA falling)"""
        if not is_bearish:
            if score >= 4:
                return f"⚠️ SUPPRESSED (bull trend)", False
            return "🔴 NO SIGNAL", False
        # Bearish regime — puts active
        if score >= 5: return "🔥 FIRE", True
        if score >= 4: return "🟢 STRONG", True
        if score >= 3: return "🟡 MODERATE", False
        return "🔴 NO SIGNAL", False
    
    call_strength, call_alert = call_signal(call_score)
    put_strength, put_alert = put_signal(put_score, is_bearish_regime)
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'market_data': {
            'spy_close': round(spy_close, 2),
            'spy_change_pct': round(spy_chg, 2),
            'vix_close': round(vix_close, 2),
            'vix_change_pct': round(vix_chg, 2),
        },
        'indicators': {
            'rsi5': round(rsi5, 2),
            'rsi14': round(rsi14, 2),
            'dist_ema20': round(dist_ema20, 2),
            'dist_sma50': round(dist_sma50, 2),
            'dist_sma200': round(dist_sma200, 2),
            'trend': trend,
            'sma200_slope': round(sma200_slope, 3),
            'bollinger_pct_b': round(pct_b, 3),
            'down_days': down_days,
            'up_days': up_days,
        },
        'calls': {
            'score': call_score,
            'strength': call_strength,
            'should_alert': call_alert,
            'factors': call_factors,
        },
        'puts': {
            'score': put_score,
            'strength': put_strength,
            'should_alert': put_alert,
            'regime_gated': not is_bearish_regime,
            'factors': put_factors,
        },
        'alerted': call_alert or put_alert,
    }
    
    return result, None

def format_call_alert(result):
    c = result['calls']
    md = result['market_data']
    ind = result['indicators']
    lines = []
    lines.append(f"📈 **SPY CALLS SIGNAL: {c['strength']}**")
    lines.append(f"Score: {c['score']}/7 factors (need 4+)")
    lines.append("")
    lines.append(f"**Market:** SPY ${md['spy_close']} ({md['spy_change_pct']:+.1f}%)")
    lines.append(f"**VIX:** {md['vix_close']:.1f} ({md['vix_change_pct']:+.1f}%)")
    lines.append(f"**Trend:** {ind['trend']} (200 SMA slope: {ind['sma200_slope']:+.3f}%)")
    lines.append(f"**BB %B:** {ind['bollinger_pct_b']:.3f}")
    lines.append("")
    lines.append("**Call Factors:**")
    for f in c['factors'].values():
        lines.append(f"  {f['label']}")
    lines.append("")
    lines.append("**Trade:** Buy SPY calls ATM/OTM, 10-14 DTE")
    lines.append("Exit: +30% profit | -40% stop | RSI(5) > 65 | 10 days")
    lines.append("")
    lines.append("_Backtest 4+: 73.9% win, +0.9% avg, Sharpe 2.28 (2020-2026)_")
    return "\n".join(lines)

def format_put_alert(result):
    p = result['puts']
    md = result['market_data']
    ind = result['indicators']
    lines = []
    lines.append(f"📉 **SPY PUTS SIGNAL: {p['strength']}**")
    lines.append(f"Score: {p['score']}/7 factors (need 4+)")
    lines.append("")
    lines.append(f"**Market:** SPY ${md['spy_close']} ({md['spy_change_pct']:+.1f}%)")
    lines.append(f"**VIX:** {md['vix_close']:.1f} ({md['vix_change_pct']:+.1f}%)")
    lines.append(f"**Trend:** {ind['trend']} (200 SMA slope: {ind['sma200_slope']:+.3f}%)")
    lines.append(f"**BB %B:** {ind['bollinger_pct_b']:.3f}")
    lines.append("")
    lines.append("**Put Factors:**")
    for f in p['factors'].values():
        lines.append(f"  {f['label']}")
    lines.append("")
    lines.append("**Trade:** Buy SPY puts ATM/OTM, 10-14 DTE")
    lines.append("Exit: +30% profit | -40% stop | RSI(5) < 30 | 10 days")
    lines.append("")
    lines.append("_Bearish regime — puts active. Use caution._")
    return "\n".join(lines)

def format_status(result):
    c = result['calls']
    p = result['puts']
    md = result['market_data']
    ind = result['indicators']
    regime = "🐻" if ind['trend'] == "BEARISH" else "🐂"
    put_note = " (suppressed)" if p.get('regime_gated') else ""
    return (
        f"SPY ${md['spy_close']:.2f} ({md['spy_change_pct']:+.1f}%) | "
        f"VIX {md['vix_close']:.1f} | "
        f"{regime} {ind['trend']} | "
        f"Calls {c['score']}/7 {c['strength']} | "
        f"Puts {p['score']}/7 {p['strength']}{put_note}"
    )

def save_state(result):
    SIGNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SIGNAL_FILE, 'w') as f:
        json.dump(result, f, indent=2, default=str)

def append_log(result):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log = []
    if LOG_FILE.exists():
        try:
            log = json.loads(LOG_FILE.read_text())
        except:
            log = []
    log.append({
        'timestamp': result['timestamp'],
        'spy_close': result['market_data']['spy_close'],
        'vix_close': result['market_data']['vix_close'],
        'call_score': result['calls']['score'],
        'put_score': result['puts']['score'],
        'trend': result['indicators']['trend'],
        'bb_pct_b': result['indicators']['bollinger_pct_b'],
        'alerted': result['alerted'],
    })
    log = log[-90:]
    LOG_FILE.write_text(json.dumps(log, indent=2))

if __name__ == "__main__":
    result, error = analyze()
    
    if error:
        print(f"ERROR: {error}")
        sys.exit(1)
    
    save_state(result)
    append_log(result)
    
    if result['alerted']:
        print("ALERT")
        if result['calls']['should_alert']:
            print(format_call_alert(result))
            print("---")
        if result['puts']['should_alert']:
            print(format_put_alert(result))
    else:
        print("NO_SIGNAL")
        print(format_status(result))
    
    if "--verbose" in sys.argv:
        print("\n--- Full Analysis ---")
        print(json.dumps(result, indent=2, default=str))
