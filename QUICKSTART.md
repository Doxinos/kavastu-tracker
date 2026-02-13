# Quick Reference - Kavastu Tracker

## 🚀 Running Things

### Activate Environment
```bash
cd ~/Projects/kavastu-tracker
source venv/bin/activate
```

### Run Backtests
```bash
# Quick (30 min) - Monthly rebalancing, 2 years
python scripts/backtest_kavastu_quick.py

# Full (2 hours) - Weekly rebalancing, 3 years
python scripts/backtest_kavastu_full.py
```

### Test Components
```bash
# Test dividend fetching
python scripts/test_dividends.py

# Test screener
python scripts/test_screener.py
```

### Run Screener
```bash
python scripts/run_screener.py
```

## 📊 Current Results (as of Feb 6, 2026)

| Config | CAGR |
|--------|------|
| Monthly, momentum only | 5.51% |
| Weekly, momentum only | 6.92% |
| Monthly, + dividends + fundamentals | 8.07% |
| Weekly, + dividends + fundamentals | **11.06%** |

**Target:** 38% CAGR (Kavastu 2024)
**Gap:** ~27% (fully explained - see [RESEARCH_FINDINGS.md](docs/RESEARCH_FINDINGS.md))

## 🔧 Troubleshooting

### "Possibly delisted" warnings
- **Normal!** Companies get delisted due to M&A, bankruptcy
- Backtester skips them automatically
- No action needed

### Low CAGR results (< 5%)
Check if fundamentals are enabled:
```bash
grep "include_fundamentals=True" src/backtester.py
```
Should see line 435 with `include_fundamentals=True`

If it says `False`, fix it:
```bash
sed -i '' 's/include_fundamentals=False/include_fundamentals=True/g' src/backtester.py
```

### No dividend output
Check dividend collection is working:
```bash
python scripts/test_dividends.py
```
Should see: `✅ Found 78 dividend-paying stocks (69%)`

## 📚 Documentation

- **[README.md](README.md)** - Overview and features
- **[docs/KAVASTU_METHODOLOGY.md](docs/KAVASTU_METHODOLOGY.md)** - Strategy details
- **[docs/IMPLEMENTATION_NOTES.md](docs/IMPLEMENTATION_NOTES.md)** - Complete rebuild guide

## 🔑 Key Concepts

### Scoring (0-125 points)
- Technical: 40 pts (MA200, golden cross, rising trend)
- Relative Strength: 30 pts (vs OMXS30 index)
- Momentum: 30 pts (distance from MA200, near 52W high)
- Quality: 25 pts (revenue, profit, ROE, dividend, low debt)

### Portfolio
- 70 stocks × 2.5% each = fully diversified
- Weekly rebalancing (Sundays)
- "Rensa det svaga" - clean out the weak

### Dividends
- 69% of Swedish stocks pay dividends
- Automatic reinvestment
- +3 quality points for dividend payers
- ~2-3% CAGR contribution

## 🆘 Emergency Rebuild

If you lose everything and need to rebuild from scratch:

1. **Clone or restore project folder**
2. **Install dependencies:**
   ```bash
   cd ~/Projects/kavastu-tracker
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Verify critical fix:**
   ```bash
   grep "include_fundamentals=True" src/backtester.py
   ```
   Must see `True` on line 435

4. **Run test:**
   ```bash
   python scripts/backtest_kavastu_quick.py
   ```
   Should get CAGR ≈ 8%

5. **If CAGR < 5%:**
   Fundamentals not enabled. Fix:
   ```bash
   sed -i '' 's/include_fundamentals=False/include_fundamentals=True/g' src/backtester.py
   ```

See [IMPLEMENTATION_NOTES.md](docs/IMPLEMENTATION_NOTES.md) for full details.

## 📝 File Locations

### Key Source Files
- `src/backtester.py` - Main backtesting engine (CHECK LINE 435!)
- `src/fundamentals.py` - Quality scoring (0-25 pts)
- `src/screener.py` - Stock scoring (0-125 pts)
- `src/data_fetcher.py` - yfinance + dividend fetching

### Configuration
- `config/swedish_stocks.csv` - 110 Swedish stocks

### Scripts
- `scripts/backtest_kavastu_quick.py` - Monthly 2-year test
- `scripts/backtest_kavastu_full.py` - Weekly 3-year test

## 🎯 What Works

✅ Screener (0-125 point scoring)
✅ Fundamental analysis (revenue, profit, ROE, debt, dividends)
✅ Dividend tracking and reinvestment
✅ Monthly backtesting (8.07% CAGR)
✅ Weekly backtesting (running)
✅ Benchmark comparison (OMXS30)

## 📈 Performance Gap Analysis

**Current:** 8% CAGR
**Target:** 38% CAGR
**Gap:** ~30%

**Likely reasons:**
1. Timing: Daily monitoring vs weekly rotation
2. AI screening: NeuroQuant provides additional edge
3. Position sizing: Dynamic vs fixed 2.5%
4. Market regime: Portfolio size adjustment (0-80 stocks)
5. Execution: Better fills, tax optimization

---

**Last Updated:** Feb 6, 2026
**Built with:** Claude Code by Anthropic
