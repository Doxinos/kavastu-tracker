# Kavastu Stock Tracker

Automated stock screening, backtesting, and portfolio tracking system based on Arne "Kavastu" Talving's momentum strategy.

**Current Status (Feb 9, 2026):** Phase 2 complete! ATR position sizing + Dynamic regime detection achieving **15.43% CAGR** (+50% improvement). Next: conviction weighting for 23-29% target.

## Features

### 1. Stock Screener ✅
- Scans 110+ Swedish stocks automatically
- **Scoring system: 0-125 points**
  - Technical (40): Price > MA200, golden cross, rising MA200
  - Relative Strength (30): Outperformance vs OMXS30 index
  - Momentum (30): Distance from MA200, near 52-week high
  - **Quality (25): Fundamentals (revenue, profit, ROE, dividends, debt)**
- Outputs top 70 stocks for portfolio

### 2. Backtester ✅
- Full historical backtesting with rebalancing
- Dividend tracking and automatic reinvestment
- Fundamental screening integration
- Performance metrics: CAGR, Sharpe ratio, max drawdown
- Benchmark comparison (OMXS30 buy & hold)
- **Current result: 8.07% CAGR** (monthly, 2024-2026)

### 3. Portfolio Tracker (Coming Soon)
- Real-time portfolio monitoring
- Weekly Sunday reports via Claude Code
- Google Sheets integration

## Quick Start

### Setup
```bash
cd ~/Projects/kavastu-tracker
source venv/bin/activate
```

### Test Components
```bash
# Test dividend fetching (5 min)
python scripts/test_dividends.py

# Test screener (5 min)
python scripts/test_screener.py
```

### Run Backtests
```bash
# Quick backtest - Monthly rebalancing, 2 years (~30 min)
python scripts/backtest_kavastu_quick.py

# Full backtest - Weekly rebalancing, 3 years (~2 hours)
python scripts/backtest_kavastu_full.py
```

### Run Screener
```bash
python scripts/run_screener.py
```

## Project Structure

```
kavastu-tracker/
├── config/
│   ├── swedish_stocks.csv          # 110 Swedish stocks
│   └── watchlist.csv                # Top 70 from screener
├── src/
│   ├── stock_universe.py           # Load stock list
│   ├── data_fetcher.py             # yfinance + dividends
│   ├── ma_calculator.py            # MA50/MA200 + crossovers
│   ├── screener.py                 # Scoring (0-125 pts)
│   ├── fundamentals.py             # Quality scoring (0-25 pts)
│   ├── backtester.py               # Backtesting engine
│   ├── portfolio_manager.py        # Position sizing + rotation
│   └── signal_detector.py          # Buy/sell signals
├── scripts/
│   ├── test_screener.py            # Quick test (10 stocks)
│   ├── test_dividends.py           # Verify dividend fetching
│   ├── run_screener.py             # Full screener (110 stocks)
│   ├── backtest_kavastu_quick.py   # Monthly backtest (2 years)
│   └── backtest_kavastu_full.py    # Weekly backtest (3 years)
├── docs/
│   ├── KAVASTU_METHODOLOGY.md      # Strategy deep-dive
│   ├── IMPLEMENTATION_NOTES.md     # Current state & rebuilding guide
│   └── RESEARCH_FINDINGS.md        # Performance gap analysis & roadmap
└── requirements.txt
```

## Kavastu Strategy

**Key principle:** MA200 as "fire alarm"
- ✅ Stock above MA200 → OK to hold/buy
- ⚠️ Stock below MA200 → No new buys, consider selling
- 🔄 Just crossed above MA200 → Buy signal
- 🚨 Just crossed below MA200 → Sell signal

**Screening criteria (0-125 points):**
1. **Technical (40 pts):** Price > MA200, golden cross, rising MA200
2. **Relative Strength (30 pts):** Outperforming OMXS30 index
3. **Momentum (30 pts):** Distance from MA200, near 52-week high
4. **Quality (25 pts):** Revenue growth, profit margin, ROE, dividends, low debt

**Portfolio structure:**
- 60-80 stocks, 2-3% position sizing each
- Weekly rotation: "Rensa det svaga" (clean out the weak)
- Dividend reinvestment (69% of holdings pay dividends)

## Data Source

- **yfinance** - Free Yahoo Finance API
- Swedish stocks use `.ST` suffix (e.g., `VOLV-B.ST`)
- Historical data: 1 year for MA200 calculations

## Backtest Results

| Period | Frequency | Features | CAGR | Sharpe | Status |
|--------|-----------|----------|------|--------|--------|
| 2024-2026 | Monthly | Momentum only | 5.51% | - | ✅ Baseline |
| 2024-2026 | Weekly | Momentum only | 6.92% | - | ✅ Complete |
| 2024-2026 | Monthly | + Dividends + Fundamentals | 8.07% | - | ✅ Complete |
| 2023-2026 | Weekly | Phase 1 (Fundamentals + Dividends) | 11.06% | 0.95 | ✅ Phase 1 best |
| 2023-2026 | Weekly | **Phase 2: ATR Only** | **15.77%** | **2.15** | ✅ **Winner** |
| 2023-2026 | Weekly | Phase 2: ATR + Indicators | 9.58% | 1.13 | ❌ Dropped |
| 2023-2026 | Weekly | **Phase 2: ATR + Regime** | **15.43%** | **1.85** | ✅ **OPTIMAL** |
| 2023-2026 | Weekly | Phase 2: Conviction Only | 9.63% | - | ❌ Dropped |
| 2023-2026 | Weekly | Phase 2: Full (All 4 Features) | 8.76% | 1.35 | ❌ Worst |

**Target:** 38% CAGR (Kavastu's verified performance 2014-2021, 7 years)

**Phase 2 FINAL Results (Complete):**
- ✅ **ATR + Dynamic Regime = 15.43% CAGR** (OPTIMAL configuration, +50% improvement)
- ✅ ATR Position Sizing: +4.71% CAGR over baseline (15.77% standalone)
- ✅ Dynamic Market Regime: Combines well with ATR (15.43% together)
- ❌ RSI/MACD Indicators: **DROPPED** (destroyed performance, -5.67% vs baseline)
- ❌ Conviction Weighting: **DROPPED** (hurt performance, -1.43% vs baseline)
- ❌ All Features Combined: **WORST** result (8.76%, even below baseline)
- Performance progression: 5.51% → 11.06% → **15.43% CAGR**
- Gap to Kavastu's 38%: ~23% (requires additional factors beyond Phase 2)

**ISK Account Advantage:**
- 1.065% flat tax on portfolio value (2026)
- NO capital gains tax on trades
- Perfect for frequent momentum rotation strategy!

**Documentation:**
- [PHASE2_SUMMARY.md](docs/PHASE2_SUMMARY.md) - **Phase 2 complete results & next steps**
- [IMPLEMENTATION_NOTES.md](docs/IMPLEMENTATION_NOTES.md) - Complete rebuild guide
- [RESEARCH_FINDINGS.md](docs/RESEARCH_FINDINGS.md) - Performance gap analysis & improvement roadmap

## Next Steps

### Completed ✅
1. Stock screener with fundamental scoring (0-125 points)
2. Backtester with dividend tracking and reinvestment
3. Monthly and weekly rebalancing tests
4. Weekly backtest with full integration (**11.06% CAGR**)
5. Comprehensive research and performance gap analysis
6. **Phase 2: ATR position sizing (+4.71% CAGR) ← WINNER**
7. **Phase 2: Dynamic market regime (combined with ATR) ← WINNER**
8. Phase 2: RSI/MACD indicators (DROPPED - destroyed performance)
9. Phase 2: Conviction weighting (DROPPED - hurt performance)
10. **Phase 2 COMPLETE: 15.43% CAGR (+50% improvement over Phase 1)**

### Phase 3 - Full Cycle Testing & Validation (1-2 weeks) ← **CURRENT**
1. ⏳ Run 2014-2021 full cycle backtest (Kavastu's verified period)
2. ⏳ Run 2020-2026 test (includes COVID crash + recovery)
3. ⏳ Validate ATR + Regime config across bear markets
4. ⏳ Analyze performance in different market conditions
5. **Target: Validate 15-20% CAGR across full market cycle**

### Phase 4 - Production Deployment (1-2 months)
1. ⏳ Finalize optimal configuration based on full cycle tests
2. ⏳ Google Sheets integration for portfolio tracking
3. ⏳ Weekly automated portfolio reports via Claude Code
4. ⏳ Live deployment on Avanza ISK account
5. **Target: Sustain 15-20% CAGR in live trading**

## Credits

Based on Arne "Kavastu" Talving's trend-following strategy.
Built with Claude Code.
