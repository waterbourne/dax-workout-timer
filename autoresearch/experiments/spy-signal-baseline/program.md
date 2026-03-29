# Program: SPY Signal Scanner Optimization

_Instructions for improving the SPY options trading signal system_

## Goal

Optimize the SPY call/put signal scanner to maximize:
1. **Win rate** — percentage of profitable trades
2. **Risk-adjusted returns** — Sharpe ratio, not just raw profit
3. **Signal frequency** — enough trades to be useful, not too many to be noise
4. **Early detection** — catch moves before they happen

## Current System (v2.1)

**File:** `workspace/trading/spy-signal-v2.py`

**Current factors (6 per side):**
- RSI(5) oversold/overbought (< 30 / > 70)
- VIX fear/complacency (> 25 or +10% spike / < 14 or -10% drop)
- Price at support/resistance (EMA20/SMA50 proximity)
- MACD crossover (bullish/bearish)
- IBS capitulation/euphoria (< 0.2 / > 0.8)
- Volume spike on down/up days

**Threshold:** 4+ of 6 factors for signal

**Backtest results (2019-2026):**
- Calls 4+: 72.8% win rate, +1.0% avg return
- Puts 4+: 40% win rate (bull market bias)
- Frequency: ~1.3 trades/week

## Experiment Loop

```
FOR each experiment:
  1. CREATE branch: experiments/spy-{hypothesis}-{timestamp}
  
  2. MODIFY spy-signal-v2.py
     - Apply ONE change at a time
     - Options: new indicators, threshold tweaks, exit rules, position sizing
  
  3. RUN backtest
     - Use workspace/trading/backtest.py
     - Capture: win rate, avg return, max drawdown, Sharpe
  
  4. EVALUATE vs baseline
     - Must improve win rate OR Sharpe, not just total return
     - Must not increase max drawdown by > 20%
  
  5. COMMIT or REVERT
     - IF improved: git commit with metrics
     - IF worse: git checkout --
  
  6. DOCUMENT in experiment log
```

## Success Metrics (Priority Order)

| Metric | Current | Target | Min Acceptable |
|--------|---------|--------|----------------|
| Call win rate (4+) | 72.8% | 75% | 70% |
| Put win rate (4+) | 40% | 55% | 50% |
| Sharpe ratio | ~0.54 | 0.70 | 0.60 |
| Max drawdown | ? | < 15% | < 20% |
| Trades/year | ~68 | 50-80 | 40-100 |

## Hypothesis Bank (test these)

### New Indicators to Add
- [ ] **Market breadth** — % of S&P 500 above 50 DMA (requires data source)
- [ ] **Put/Call ratio** — CBOE PCR extremes (> 1.2 bullish, < 0.7 bearish)
- [ ] **VIX term structure** — contango vs backwardation
- [ ] **Moving average slope** — 200 SMA trend direction (regime filter)
- [ ] **Consecutive days** — 3+ down days for calls, 3+ up days for puts
- [ ] **Bollinger Bands** — %B < 0.1 for calls, > 0.9 for puts
- [ ] **ATR expansion** — volatility breakout confirmation

### Threshold Adjustments
- [ ] Lower call threshold to 3/6 in bear markets (200 SMA falling)
- [ ] Raise put threshold to 5/6 in bull markets (200 SMA rising)
- [ ] Dynamic thresholds based on VIX level
- [ ] Require volume spike for ALL signals (currently 6th factor)

### Exit Rule Improvements
- [ ] Trailing stop instead of fixed -40%
- [ ] Time-based exits (close at 3 PM Friday if not hit target)
- [ ] VIX-based exits (exit calls if VIX drops below 15)
- [ ] RSI-based exits more granular (RSI > 60 take half, > 70 full)

### Position Sizing
- [ ] Scale position by signal strength (4/6 = 1x, 5/6 = 1.5x, 6/6 = 2x)
- [ ] Reduce size in high VIX (> 30) environments
- [ ] Increase size in low VIX (< 15) environments

### Multi-Timeframe
- [ ] Require daily AND weekly alignment
- [ ] Check 4h chart for intraday confirmation

## Constraints

- Must use free data sources (yfinance)
- Must complete backtest in < 5 minutes
- One variable change per experiment
- Document ALL results, even failures
- Never deploy to live trading without 3+ months paper trading

## Current Baseline

See `workspace/trading/backtest-trades.json` for full trade history.

Baseline command:
```bash
cd workspace/trading && python3 backtest.py
```

## Success Criteria

Stop when:
- Calls: 75%+ win rate sustained over 3 backtest periods
- Puts: 55%+ win rate sustained
- Sharpe: 0.70+
- Max drawdown: < 15%

Then: Paper trade for 1 month before live deployment.

## Integration

Improved signal will replace `spy-signal-v2.py` in the cron job:
- Schedule: 12:30 PM PT weekdays
- Delivery: Telegram alert if 4+ factors
- Log: All readings to signal-log.json
