# Claude Code Project Context

This file provides context for Claude Code when working on the Kavastu Stock Tracker project.

## Project Overview

Automated stock screening and backtesting system for Swedish stocks based on Arne "Kavastu" Talving's momentum strategy. The goal is to systematically achieve 23-38% CAGR through trend-following and momentum-based stock selection.

## Current Status (Feb 9, 2026)

**Phase 2 COMPLETE** - All feature testing finished
- **Optimal Configuration:** ATR position sizing + Dynamic regime detection
- **Best Performance:** 15.43% CAGR (2023-2026, weekly rebalancing)
- **Improvement:** +50% over Phase 1 baseline (11.06%)
- **Sharpe Ratio:** 1.85 (excellent risk-adjusted returns)
- **Alpha vs OMXS30:** +2.42% per year

**All Phase 2 Tests Completed:**
- ✅ ATR Position Sizing Only: 15.77% CAGR, Sharpe 2.15 (standalone winner)
- ✅ ATR + Dynamic Regime: 15.43% CAGR, Sharpe 1.85 (optimal combination)
- ❌ ATR + Indicators: 9.58% CAGR (indicators destroy performance)
- ❌ Conviction Weighting: 9.63% CAGR (reduces diversification, hurts returns)
- ❌ Full Phase 2 (All 4): 8.76% CAGR (worst result - features conflict)

**Next Phase:** Full Cycle Validation (2014-2021 + 2020-2026)
- **Target:** Validate 15-20% CAGR across bear markets
- **Timeline:** 1-2 weeks
- **Priority:** Test optimal config through COVID crash and 2018 bear market

## Key Project Files

### Configuration
- `config/backtest_config.yaml` - Phase 2 feature toggles
- `config/swedish_stocks.csv` - 110 Swedish stocks universe
- `config/watchlist.csv` - Top 70 from screener

### Core Modules
- `src/backtester.py` - Main backtesting engine (ATR + regime integrated)
- `src/screener.py` - 0-130 point scoring system
- `src/portfolio_manager.py` - Position sizing (ATR-based now available)
- `src/market_regime.py` - Dynamic regime detection (5-80 stocks scaling)
- `src/ma_calculator.py` - Technical indicators (MA, ATR, RSI, MACD)
- `src/data_fetcher.py` - yfinance data with 0.15s rate limiting

### Scripts
- `scripts/backtest_kavastu_phase2.py` - Main Phase 2 testing script
- `scripts/run_screener.py` - Full screener (110 stocks)

### Documentation
- **`docs/PHASE2_SUMMARY.md`** - CRITICAL: Complete Phase 2 results, gap analysis, next steps
- `docs/IMPLEMENTATION_NOTES.md` - Rebuild guide
- `docs/RESEARCH_FINDINGS.md` - Performance gap analysis
- `README.md` - Project overview and status

## Critical Learnings (Must Read!)

### Kavastu's ACTUAL Strategy (Corrected Understanding)
- **Portfolio size:** 30-80 stocks simultaneously (NOT 10-15 as initially assumed!)
- **Conviction weighting:** Top 10-12 holdings = 40% of portfolio ← **WE'RE MISSING THIS**
- **Two-tier structure:** Core (14-20 stocks) + Satellite (40-60 stocks)
- **Performance:** 38% CAGR sustained 2014-2021 (7 years, not just 2024)
- **Asset allocation:** 100% stocks, no bonds
- **Turnover:** Weekly rotation, high activity

### Phase 2 Test Results

#### ✅ WINNERS (Keep These)
1. **ATR Position Sizing:** +5.32% CAGR (15.77% total)
   - Volatility-adjusted position sizing
   - Sharpe ratio: 2.15 (exceptional)
   - Max drawdown: -13.15% (improved from -15.3%)

2. **Dynamic Market Regime:** +4.98% CAGR (15.43% total)
   - Scales portfolio 5-80 stocks based on market conditions
   - Factors: Index position, breadth, volatility
   - Combined beautifully with ATR

#### ❌ LOSERS (Dropped)
3. **RSI + MACD Indicators:** -6.19% vs ATR-only (DESTROYED performance)
   - Over-filtering in bull markets
   - "Overbought" signals filtered out best performers
   - Contradicts momentum-based MA200 system
   - **Never re-enable this**

### Gap Analysis: 38% vs 15.43%

| Factor | Impact | Fixable? |
|--------|--------|----------|
| Conviction weighting (top 15 = 50%) | -5 to -8% | ✅ YES (Priority 1) |
| Stock selection quality | -4 to -6% | ⚠️ PARTIAL |
| Two-tier holding periods | -2 to -3% | ✅ YES (Priority 2) |
| Entry/exit timing | -3 to -5% | ⚠️ PARTIAL |
| Testing period (bull only) | -2 to -4% | ✅ YES (test 2014-2021) |
| Discretionary edge (12 yrs exp) | -3 to -5% | ❌ NO |

**Total explainable gap:** 19-31% (matches the ~23% difference)

## Next Steps (Prioritized)

### Priority 1: Conviction-Weighted Portfolio ⭐ **CURRENT TASK**
**Expected gain:** +3-5% CAGR
**Implementation:**
- Top 15 stocks = 50% of capital (3.3% each)
- Next 25 stocks = 35% of capital (1.4% each)
- Remaining = 15% of capital (0.5-1% each)
- Use score to determine tier placement

**Files to modify:**
- `src/portfolio_manager.py` - Add conviction weighting logic
- `src/backtester.py` - Integrate conviction weights into buy logic
- `config/backtest_config.yaml` - Add conviction weighting config

### Priority 2: Two-Tier Holding Periods
**Expected gain:** +2-3% CAGR
**Implementation:**
- Core (top 15): Hold until score drops below 90
- Satellite (rest): Normal weekly rotation
- Reduces turnover on winners

### Priority 3: 2014-2021 Full Cycle Test
**Purpose:** Validate strategy through:
- 2018 bear market
- 2020 COVID crash
- Full market cycle
- Direct comparison to Kavastu's proven period

**Expected result:** 18-25% CAGR (more realistic than 2023-2026 bull-only)

## Technical Notes

### Rate Limiting
- **Problem:** Yahoo Finance throttles parallel requests
- **Solution:** 0.15s delay between API calls (data_fetcher.py)
- **Impact:** Tests take longer but succeed reliably
- **Run tests sequentially**, not in parallel

### Config System
Location: `config/backtest_config.yaml`

Current optimal config:
```yaml
features:
  atr_sizing:
    enabled: true
    account_risk_pct: 1.0
    atr_multiplier: 2.0
    min_weight: 1.0
    max_weight: 5.0

  indicator_confirmation:
    enabled: false  # NEVER re-enable - destroys performance

  dynamic_regime:
    enabled: true
    max_holdings_strong_bull: 80
    min_holdings_panic: 5
```

### Backtest Runtime
- 3-year weekly test: ~2-2.5 hours
- Data fetching: 110 stocks × 0.15s = ~17 seconds per rebalance
- 161 rebalances (weekly 2023-2026) = ~45 minutes data fetching + ~1.5 hours calculation

## Common Tasks

### Run Phase 2 Backtest
```bash
cd ~/Projects/kavastu-tracker
source venv/bin/activate
python scripts/backtest_kavastu_phase2.py
```

### Modify Config for Testing
Edit `config/backtest_config.yaml` to enable/disable features

### Run Screener
```bash
python scripts/run_screener.py
```

## Important Conventions

### Scoring System
- Total: 0-130 points
- Technical (45): MA position, trend, crossovers
- Relative Strength (30): vs OMXS30 index
- Momentum (30): Distance from MA200, 52-week high
- Quality (25): Fundamentals (revenue, profit, ROE, dividends, debt)

### Position Sizing
- **ATR-based (current):** Volatility-adjusted, 1-5% per stock
- **Fixed (old):** 2.5% per stock
- **Conviction-weighted (next):** 0.5-3.3% based on score rank

### Rebalancing
- **Frequency:** Weekly (Sunday evenings in production)
- **Process:** Sell losers, buy winners based on updated scores
- **Transaction cost:** 0.25% per trade

## Warnings & Gotchas

1. **Never re-enable RSI/MACD indicators** - they destroy performance in bull markets
2. **Always use rate limiting** - Yahoo Finance will throttle without delays
3. **Run tests sequentially** - parallel execution causes API errors
4. **Bull market bias** - 2023-2026 test period was strong bull (OMXS30: 13.01%)
5. **Need full cycle test** - 2014-2021 or 2020-2026 for realistic expectations

## Performance Targets

| Phase | Target CAGR | Status | Key Features |
|-------|-------------|--------|--------------|
| Phase 1 | 10-12% | ✅ Achieved 11.06% | Fundamentals + dividends |
| Phase 2 | 15-18% | ✅ Achieved 15.43% | ATR + dynamic regime |
| Phase 2.5 | 23-29% | ⏳ In Progress | + Conviction weighting |
| Kavastu | 38% | 🎯 Long-term goal | + 12 years experience |

## References

- **Kavastu's verified track record:** 38% CAGR (2014-2021, 7 years)
- **OMXS30 long-term average:** ~9.3% CAGR
- **ISK tax rate:** 1.065% flat on portfolio value (2026)
- **Swedish market hours:** 09:00-17:30 CET (Stockholm time)
- **Best rebalancing day:** Sunday evening (after week closes)

## Contact & Resources

- **Yahoo Finance API:** yfinance library (free, rate limited)
- **Avanza:** Swedish broker for ISK account
- **OMXS30:** Stockholm Stock Exchange index (benchmark)

---

**Last Updated:** February 9, 2026
**Next Milestone:** Conviction weighting implementation + 2014-2021 backtest
**Current Focus:** Priority 1 - Top 15 stocks = 50% of portfolio
