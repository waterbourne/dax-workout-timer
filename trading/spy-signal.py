#!/usr/bin/env python3
"""
SPY Options Signal System
==========================
Multi-factor signals for 1-2 week SPY calls AND puts.

CALLS (mean-reversion bounce):
  3+ of 5 factors:
    1. RSI(5) < 30         — Oversold
    2. VIX > 25 or spike   — Fear elevated, calls cheap
    3. Price at support     — Near EMA20/SMA50 from below
    4. MACD bullish cross   — Momentum turning up
    5. IBS < 0.2            — Closed near low, bounce setup

PUTS (mean-reversion fade):
  3+ of 5 factors:
    1. RSI(5) > 70          — Overbought
    2. VIX crushed < 14     — Complacency, puts cheap
    3. Price at resistance   — Extended above EMA20/SMA50
    4. MACD bearish cross    — Momentum turning down
    5. IBS > 0.8             — Closed near high, fade setup

Both sides: ATM or 1-2 strikes OTM, 10-14 day expiry.
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
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

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

# --- Compute All Indicators ---

def compute_indicators(spy, vix):
    spy_close = float(spy['Close'].iloc[-1])
    spy_prev = float(spy['Close'].iloc[-2])
    spy_high = float(spy['High'].iloc[-1])
    spy_low = float(spy['Low'].iloc[-1])
    spy_chg = ((spy_close - spy_prev) / spy_prev) * 100

    vix_close = float(vix['Close'].iloc[-1])
    vix_prev = float(vix['Close'].iloc[-2])
    vix_chg = ((vix_close - vix_prev) / vix_prev) * 100

    rsi5 = calc_rsi(spy['Close'], 5)
    rsi14 = calc_rsi(spy['Close'], 14)
    ema20 = calc_ema(spy['Close'], 20)
    sma50 = calc_sma(spy['Close'], 50)
    sma200 = calc_sma(spy['Close'], 200)
    macd_line, macd_sig = calc_macd(spy['Close'])
    ibs = calc_ibs(spy['High'], spy['Low'], spy['Close'])

    cur = {
        'spy_close': spy_close, 'spy_prev': spy_prev, 'spy_chg': spy_chg,
        'spy_high': spy_high, 'spy_low': spy_low,
        'vix_close': vix_close, 'vix_prev': vix_prev, 'vix_chg': vix_chg,
        'rsi5': float(rsi5.iloc[-1]), 'rsi14': float(rsi14.iloc[-1]),
        'ema20': float(ema20.iloc[-1]), 'sma50': float(sma50.iloc[-1]),
        'sma200': float(sma200.iloc[-1]),
        'macd': float(macd_line.iloc[-1]), 'macd_sig': float(macd_sig.iloc[-1]),
        'prev_macd': float(macd_line.iloc[-2]), 'prev_macd_sig': float(macd_sig.iloc[-2]),
        'ibs': float(ibs.iloc[-1]),
        'dist_ema20': ((spy_close - float(ema20.iloc[-1])) / float(ema20.iloc[-1])) * 100,
        'dist_sma50': ((spy_close - float(sma50.iloc[-1])) / float(sma50.iloc[-1])) * 100,
        'dist_sma200': ((spy_close - float(sma200.iloc[-1])) / float(sma200.iloc[-1])) * 100,
    }
    return cur

# --- Call Signal ---

def evaluate_calls(c):
    factors = {}

    factors['rsi_oversold'] = {
        'triggered': c['rsi5'] < 30,
        'value': round(c['rsi5'], 2),
        'label': f"RSI(5) = {c['rsi5']:.1f}",
        'threshold': '< 30',
    }

    vix_spike = c['vix_close'] > 20 and c['vix_chg'] > 10
    vix_high = c['vix_close'] > 25
    factors['vix_elevated'] = {
        'triggered': vix_spike or vix_high,
        'value': round(c['vix_close'], 2),
        'label': f"VIX = {c['vix_close']:.1f} ({c['vix_chg']:+.1f}%)",
        'threshold': 'VIX > 25, or > 20 with +10% spike',
    }

    at_support = (c['dist_ema20'] < 0 and c['dist_ema20'] > -2) or \
                 (c['dist_sma50'] < 0 and c['dist_sma50'] > -3)
    factors['price_support'] = {
        'triggered': at_support,
        'label': f"EMA20: {c['dist_ema20']:+.1f}% | SMA50: {c['dist_sma50']:+.1f}%",
        'threshold': 'Within 2% below EMA20 or 3% below SMA50',
    }

    cross_up = c['prev_macd'] <= c['prev_macd_sig'] and c['macd'] > c['macd_sig']
    converging = (c['macd'] - c['macd_sig']) > (c['prev_macd'] - c['prev_macd_sig'])
    factors['macd_bullish'] = {
        'triggered': cross_up,
        'converging': converging,
        'label': f"MACD gap: {c['macd'] - c['macd_sig']:.3f} ({'converging' if converging else 'diverging'})",
        'threshold': 'MACD crosses above signal',
    }

    factors['ibs_low'] = {
        'triggered': c['ibs'] < 0.2,
        'value': round(c['ibs'], 3),
        'label': f"IBS = {c['ibs']:.3f}",
        'threshold': '< 0.2',
    }

    score = sum(1 for f in factors.values() if f['triggered'])
    return factors, score

# --- Put Signal ---

def evaluate_puts(c):
    factors = {}

    factors['rsi_overbought'] = {
        'triggered': c['rsi5'] > 70,
        'value': round(c['rsi5'], 2),
        'label': f"RSI(5) = {c['rsi5']:.1f}",
        'threshold': '> 70',
    }

    vix_crushed = c['vix_close'] < 14
    vix_dropping = c['vix_close'] < 18 and c['vix_chg'] < -10
    factors['vix_complacent'] = {
        'triggered': vix_crushed or vix_dropping,
        'value': round(c['vix_close'], 2),
        'label': f"VIX = {c['vix_close']:.1f} ({c['vix_chg']:+.1f}%)",
        'threshold': 'VIX < 14, or < 18 with -10% drop',
    }

    at_resistance = (c['dist_ema20'] > 0 and c['dist_ema20'] < 2) or \
                    (c['dist_sma50'] > 0 and c['dist_sma50'] < 3)
    # Also trigger if extended far above (overextended rally)
    overextended = c['dist_ema20'] > 3 or c['dist_sma50'] > 5
    factors['price_resistance'] = {
        'triggered': at_resistance or overextended,
        'label': f"EMA20: {c['dist_ema20']:+.1f}% | SMA50: {c['dist_sma50']:+.1f}%",
        'threshold': 'Within 2% above EMA20, 3% above SMA50, or overextended (>3% EMA20 / >5% SMA50)',
    }

    cross_down = c['prev_macd'] >= c['prev_macd_sig'] and c['macd'] < c['macd_sig']
    diverging = (c['macd'] - c['macd_sig']) < (c['prev_macd'] - c['prev_macd_sig'])
    factors['macd_bearish'] = {
        'triggered': cross_down,
        'diverging': diverging,
        'label': f"MACD gap: {c['macd'] - c['macd_sig']:.3f} ({'diverging' if diverging else 'converging'})",
        'threshold': 'MACD crosses below signal',
    }

    factors['ibs_high'] = {
        'triggered': c['ibs'] > 0.8,
        'value': round(c['ibs'], 3),
        'label': f"IBS = {c['ibs']:.3f}",
        'threshold': '> 0.8',
    }

    score = sum(1 for f in factors.values() if f['triggered'])
    return factors, score

# --- Scoring ---

def score_to_strength(score):
    if score >= 5: return "🔥 FIRE", True
    if score >= 4: return "🟢 STRONG", True
    if score >= 3: return "🟡 MODERATE", True
    if score >= 2: return "⚪ WEAK", False
    return "🔴 NO SIGNAL", False

# --- Format ---

def format_alert(direction, factors, score, strength, c, trade_desc):
    emoji = "📈" if direction == "CALLS" else "📉"
    lines = []
    lines.append(f"{emoji} **SPY {direction} SIGNAL: {strength}**")
    lines.append(f"Score: {score}/5 factors triggered")
    lines.append("")
    lines.append(f"**Market:** SPY ${c['spy_close']:.2f} ({c['spy_chg']:+.1f}%)")
    lines.append(f"**VIX:** {c['vix_close']:.1f} ({c['vix_chg']:+.1f}%)")

    above_200 = c['spy_close'] > c['sma200']
    trend = "BULLISH (above 200 SMA)" if above_200 else "BEARISH (below 200 SMA)"
    lines.append(f"**Trend:** {trend}")
    lines.append("")
    lines.append("**Factors:**")
    for f in factors.values():
        icon = "✅" if f['triggered'] else "❌"
        lines.append(f"  {icon} {f['label']}")
    lines.append("")
    lines.append(f"**Suggested Trade:**")
    for line in trade_desc:
        lines.append(f"  • {line}")

    # Watch items
    if direction == "CALLS":
        macd_f = factors.get('macd_bullish', {})
        if macd_f.get('converging') and not macd_f['triggered']:
            lines.append("")
            lines.append("⏳ **Watch:** MACD converging — bullish crossover may be imminent")
    else:
        macd_f = factors.get('macd_bearish', {})
        if macd_f.get('diverging') and not macd_f['triggered']:
            lines.append("")
            lines.append("⏳ **Watch:** MACD diverging — bearish crossover may be imminent")

    return "\n".join(lines)

def format_status(c, call_score, call_str, put_score, put_str):
    return (
        f"SPY ${c['spy_close']:.2f} ({c['spy_chg']:+.1f}%) | "
        f"VIX {c['vix_close']:.1f} | "
        f"RSI(5) {c['rsi5']:.1f} | "
        f"Calls {call_score}/5 {call_str} | "
        f"Puts {put_score}/5 {put_str}"
    )

# --- Persistence ---

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
        'rsi5': result['indicators']['rsi5'],
        'call_score': result['calls']['score'],
        'call_signal': result['calls']['strength'],
        'put_score': result['puts']['score'],
        'put_signal': result['puts']['strength'],
        'alerted': result['alerted'],
    })
    log = log[-90:]
    LOG_FILE.write_text(json.dumps(log, indent=2))

# --- Main Analysis ---

def analyze():
    spy, vix, err = fetch_data()
    if err:
        return None, err

    c = compute_indicators(spy, vix)

    call_factors, call_score = evaluate_calls(c)
    call_str, call_alert = score_to_strength(call_score)

    put_factors, put_score = evaluate_puts(c)
    put_str, put_alert = score_to_strength(put_score)

    above_200 = c['spy_close'] > c['sma200']
    trend = "BULLISH" if above_200 else "BEARISH"

    result = {
        'timestamp': datetime.now().isoformat(),
        'market_data': {
            'spy_close': round(c['spy_close'], 2),
            'spy_change_pct': round(c['spy_chg'], 2),
            'vix_close': round(c['vix_close'], 2),
            'vix_change_pct': round(c['vix_chg'], 2),
        },
        'indicators': {
            'rsi5': round(c['rsi5'], 2),
            'rsi14': round(c['rsi14'], 2),
            'ema20': round(c['ema20'], 2),
            'sma50': round(c['sma50'], 2),
            'sma200': round(c['sma200'], 2),
            'macd': round(c['macd'], 4),
            'macd_signal': round(c['macd_sig'], 4),
            'ibs': round(c['ibs'], 3),
        },
        'distances': {
            'from_ema20': round(c['dist_ema20'], 2),
            'from_sma50': round(c['dist_sma50'], 2),
            'from_sma200': round(c['dist_sma200'], 2),
        },
        'trend': trend,
        'calls': {
            'factors': call_factors,
            'score': call_score,
            'strength': call_str,
            'should_alert': call_alert,
        },
        'puts': {
            'factors': put_factors,
            'score': put_score,
            'strength': put_str,
            'should_alert': put_alert,
        },
        'alerted': call_alert or put_alert,
    }

    # Build alert messages
    alerts = []

    if call_alert:
        alerts.append(format_alert("CALLS", call_factors, call_score, call_str, c, [
            "Buy SPY calls, ATM or 1-2 strikes OTM",
            "Expiration: 10-14 days out",
            "Take profit: +25-30%",
            "Stop loss: -40%",
            "Alt exit: RSI(5) > 70",
        ]))

    if put_alert:
        alerts.append(format_alert("PUTS", put_factors, put_score, put_str, c, [
            "Buy SPY puts, ATM or 1-2 strikes OTM",
            "Expiration: 10-14 days out",
            "Take profit: +25-30%",
            "Stop loss: -40%",
            "Alt exit: RSI(5) < 30",
        ]))

    result['alert_messages'] = alerts
    result['status_line'] = format_status(c, call_score, call_str, put_score, put_str)

    return result, None

# --- Entry Point ---

if __name__ == "__main__":
    result, error = analyze()

    if error:
        print(f"ERROR: {error}")
        sys.exit(1)

    save_state(result)
    append_log(result)

    if result['alerted']:
        print("ALERT")
        for msg in result['alert_messages']:
            print(msg)
            print("---")  # separator between call/put alerts
    else:
        print("NO_SIGNAL")
        print(result['status_line'])

    if "--verbose" in sys.argv:
        print("\n--- Full Analysis ---")
        print(json.dumps(result, indent=2, default=str))
