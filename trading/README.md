# SPY Options Signal System

## Strategy
Multi-factor mean-reversion signals for 1-2 week SPY **calls AND puts**.

### 📈 CALLS (Bounce Play)
| # | Factor | Threshold | Logic |
|---|--------|-----------|-------|
| 1 | RSI(5) oversold | < 30 | ~80%+ win rate on 5-10 day SPY holds |
| 2 | VIX spike | > 25, or > 20 with +10% daily | Fear elevated, calls cheap |
| 3 | Price at support | Within 2% below EMA20 or 3% below SMA50 | Institutional buy zone |
| 4 | MACD bullish cross | MACD crosses above signal line | Momentum turning up |
| 5 | IBS low | < 0.2 | Closed near low → next-day bounce |

### 📉 PUTS (Fade Play)
| # | Factor | Threshold | Logic |
|---|--------|-----------|-------|
| 1 | RSI(5) overbought | > 70 | Overextended, pullback due |
| 2 | VIX crushed | < 14, or < 18 with -10% drop | Complacency, puts cheap |
| 3 | Price at resistance | Extended above EMA20/SMA50, or overextended | Distribution zone |
| 4 | MACD bearish cross | MACD crosses below signal line | Momentum turning down |
| 5 | IBS high | > 0.8 | Closed near high → fade setup |

## Signal Strength
- 🔥 FIRE (5/5) — Very rare, historically strong
- 🟢 STRONG (4/5) — High conviction
- 🟡 MODERATE (3/5) — Worth considering
- ⚪ WEAK (2/5) — Watch only
- 🔴 NO SIGNAL — Sidelines

## Trade Parameters
- **Instrument:** SPY calls or puts, ATM or 1-2 strikes OTM
- **Expiration:** 10-14 days out
- **Take profit:** +25-30%
- **Stop loss:** -40%
- **Call exit alt:** RSI(5) > 70
- **Put exit alt:** RSI(5) < 30

## Schedule
- **Cron:** Mon-Fri at 1:05 PM PT (4:05 PM ET, after market close)
- **Alert:** Telegram notification only when score ≥ 3/5 on either side
- **Silent:** No notification when no signal (no spam)

## Files
- `spy-signal.py` — Core analysis engine (calls + puts)
- `signal-state.json` — Latest full analysis
- `signal-log.json` — Historical readings (90-day rolling)
- `README.md` — This file
