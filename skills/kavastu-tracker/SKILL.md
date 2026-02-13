---
name: kavastu-tracker
description: Weekly Kavastu portfolio backtest runner. Run historical backtests with fundamental scoring and dividend tracking. Shows CAGR, Sharpe ratio, and performance vs OMXS30.
---

# Kavastu Portfolio Backtester

## Instructions

When invoked:

1. Ask user which backtest to run:
   - **Quick (30 min)**: Monthly rebalancing, 2 years (2024-2026)
   - **Full (2 hours)**: Weekly rebalancing, 3 years (2023-2026)

2. Run the appropriate script:
   - Quick: `cd ~/Projects/kavastu-tracker && source venv/bin/activate && python scripts/backtest_kavastu_quick.py`
   - Full: `cd ~/Projects/kavastu-tracker && source venv/bin/activate && python scripts/backtest_kavastu_full.py`

3. Wait for completion (this may take 30 minutes to 2 hours)

4. Parse output and present as executive summary:
   - Total Return and CAGR
   - Dividend contribution
   - Benchmark comparison (OMXS30)
   - Trade statistics
   - Top holdings

## Output Format

**Portfolio Performance:**
- Initial Investment: 100,000 SEK
- Final Value: X SEK
- Total Return: Y%
- CAGR: Z%
- Max Drawdown: W%

**Return Breakdown:**
- Price Return: X% (CAGR: Y%)
- Dividend Return: Z%
- Total Dividends: W SEK

**vs Benchmark (OMXS30):**
- Outperformance: +X% CAGR
- Alpha: Y% per year

**Trade Statistics:**
- Total Trades: X
- Avg Trades/Week: Y

**Current vs Target:**
- Current: X% CAGR
- Target (Kavastu 2024): 38% CAGR
- Gap: ~Y%

## Important Notes

- Quick backtest takes ~30 minutes
- Full backtest takes ~2 hours
- Both run with fundamentals + dividends enabled
- Results saved to console output (not logged to file)
- You'll see "possibly delisted" warnings (normal)

## Trigger Phrases
- "Run Kavastu backtest"
- "Test the strategy"
- "Backtest Kavastu portfolio"
- "Run quick backtest"
- "Run full backtest"
- "/kavastu-tracker"
