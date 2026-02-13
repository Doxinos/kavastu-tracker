---
name: kavastu-screener
description: Screen 300+ Swedish stocks using Kavastu criteria (MA200, golden cross, relative strength, fundamentals). Updates watchlist with top 70 stocks. Run weekly or monthly.
---

# Kavastu Stock Screener

## Instructions

When invoked:

1. Run: `cd ~/Projects/kavastu-tracker && source venv/bin/activate && python scripts/run_screener.py`
2. Parse output to extract:
   - Number of stocks scanned
   - Number passing filters
   - Top 10 stocks by score
   - Watchlist update status
3. Present summary with top stocks and their scores

## Output Format

**Screening Results:**
- Scanned: X stocks
- Passing filters: Y stocks (price > MA200)
- Added to watchlist: Top 70 stocks

**Top 10 Strongest Stocks:**
1. TICKER - Score X/125, Distance from MA200: Y%
2. ...

**Next Steps:**
- Review watchlist in config/watchlist.csv
- Consider running backtest with new watchlist
- Run weekly portfolio check on Sunday

## Trigger Phrases
- "Run stock screener"
- "Update watchlist"
- "Screen Swedish stocks"
- "Find strongest stocks"
- "/kavastu-screener"
