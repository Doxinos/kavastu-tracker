# Trending Detector Module

**Status:** ✅ COMPLETE - Task 1.1 (Phase 1: Production Dashboard)

## Overview

The `trending_detector.py` module identifies hot and cold trending stocks based on momentum analysis. It provides a 0-100 point scoring system that detects which stocks are gaining momentum (HOT 🔥) or losing momentum (COLD ❄️).

## Location

`/Users/peter/Projects/kavastu-tracker/src/trending_detector.py`

## Key Features

### 1. `calculate_trending_score()` - Core Scoring Function

Calculates a momentum score (0-100 points) based on four key factors:

**Scoring Breakdown:**
- **4-week price return (40 points):** Recent momentum
  - >15%: 40 points (very hot)
  - 10-15%: 30 points
  - 5-10%: 20 points
  - -5 to 5%: 10 points
  - -10 to -5%: 5 points
  - <-10%: 0 points (cold)

- **Relative strength vs OMXS30 (30 points):** Outperformance
  - Outperformance >10%: 30 points
  - Outperformance 5-10%: 20 points
  - Outperformance 0-5%: 10 points
  - Underperformance: 0 points

- **Volume trend (15 points):** Increasing volume = stronger trend
  - Volume increasing >50%: 15 points
  - Volume increasing 25-50%: 10 points
  - Volume increasing 0-25%: 5 points
  - Volume decreasing: 0 points

- **Acceleration (15 points):** Rate of change improving
  - Accelerating (2-week > expected): 15 points
  - Stable (-2% to +2%): 7 points
  - Decelerating: 0 points

**Classification:**
- Score ≥75: **HOT** 🔥 (strong momentum)
- Score ≤25: **COLD** ❄️ (weak/negative momentum)
- Score 26-74: **NEUTRAL** (mixed signals)

**Returns:**
```python
{
    'trending_score': 0-100,
    'classification': 'HOT' | 'COLD' | 'NEUTRAL',
    'return_4w': float,
    'rs_vs_benchmark': float,
    'volume_trend': float,
    'acceleration': float,
    'reason': str  # Human-readable explanation
}
```

### 2. `get_trending_stocks()` - Extract Hot/Cold Lists

Identifies hot and cold stocks from screener results.

**Parameters:**
- `screener_results`: DataFrame with trending scores
- `benchmark_returns`: Dict with 'return_4w' for benchmark
- `top_n`: Number of hot/cold stocks to return (default 10)

**Returns:** `(hot_stocks, cold_stocks)`
- Each list contains dicts with: ticker, score, trending_score, classification, reason

### 3. `add_trending_analysis()` - Enhance Screener Results

Convenience function to add trending analysis to existing screener results.

**Parameters:**
- `screener_results`: DataFrame from screener
- `stock_data`: Dict mapping ticker -> price DataFrame
- `benchmark_returns`: Dict with 'return_4w'

**Returns:** Enhanced DataFrame with trending columns added

## Usage Examples

### Basic Usage

```python
from src.trending_detector import calculate_trending_score
from src.data_fetcher import fetch_stock_data

# Fetch stock data
df = fetch_stock_data('VOLV-B.ST', period='6mo')

# Calculate trending score
benchmark_returns = {'return_4w': 5.0}  # OMXS30 4-week return
result = calculate_trending_score('VOLV-B.ST', df, benchmark_returns)

print(f"Score: {result['trending_score']}/100")
print(f"Classification: {result['classification']}")
print(f"Why: {result['reason']}")
```

### Integration with Screener

```python
from src.trending_detector import add_trending_analysis, get_trending_stocks
from src.screener import run_screen
from src.data_fetcher import fetch_portfolio_data

# Run screener
screener_results = run_screen(stocks, min_score=50)

# Fetch stock data
stock_data = fetch_portfolio_data(stocks, period='6mo')

# Add trending analysis
benchmark_returns = {'return_4w': 5.0}
enhanced_results = add_trending_analysis(
    screener_results,
    stock_data,
    benchmark_returns
)

# Get hot/cold stocks
hot_stocks, cold_stocks = get_trending_stocks(
    enhanced_results,
    benchmark_returns,
    top_n=10
)

# Display results
for stock in hot_stocks:
    print(f"🔥 {stock['ticker']}: {stock['trending_score']}/100")
    print(f"   {stock['reason']}")
```

## Testing

The module includes comprehensive tests in the `if __name__ == "__main__":` block.

**Run tests:**
```bash
cd ~/Projects/kavastu-tracker
source venv/bin/activate
python -m src.trending_detector
```

**Test with real data:**
```python
from src.trending_detector import calculate_trending_score
from src.data_fetcher import fetch_stock_data, fetch_benchmark_returns

# Real Swedish stocks
tickers = ['VOLV-B.ST', 'ERIC-B.ST', 'ABB.ST']

# Fetch benchmark
bench_3m, bench_6m = fetch_benchmark_returns()
bench_df = fetch_stock_data('^OMX', period='3mo')
bench_4w = ((bench_df['Close'].iloc[-1] - bench_df['Close'].iloc[-20])
            / bench_df['Close'].iloc[-20]) * 100

benchmark_returns = {'return_4w': bench_4w}

# Test each stock
for ticker in tickers:
    df = fetch_stock_data(ticker, period='6mo')
    result = calculate_trending_score(ticker, df, benchmark_returns)
    print(f"{ticker}: {result['trending_score']}/100 - {result['classification']}")
```

## Real-World Results

Example output from February 2026:

```
ABB.ST:
  Trending Score: 75/100
  Classification: HOT
  4-week return: +17.40%
  vs OMXS30: +12.87%
  Volume trend: +15.2%
  Acceleration: -3.49%
  Why: 4-week return +17.4%, outperforming OMXS30 by 12.9%, volume up 15%

VOLV-B.ST:
  Trending Score: 55/100
  Classification: NEUTRAL
  4-week return: +12.14%
  vs OMXS30: +7.61%
  Volume trend: +18.6%
  Acceleration: -2.04%
  Why: 4-week return +12.1%, outperforming OMXS30 by 7.6%, volume up 19%
```

## Integration Points

This module integrates seamlessly with:
- ✅ `screener.py` - Add trending analysis to screening results
- ✅ `data_fetcher.py` - Use fetch_benchmark_returns() for OMXS30 data
- ✅ `ma_calculator.py` - Uses calculate_ma() for volume trends
- ✅ No circular dependencies
- ✅ Compatible with existing DataFrame structures

## Next Steps (Phase 1 Continuation)

This module is designed for the production dashboard. Next tasks:
1. **Task 1.2:** Create dashboard visualization
2. **Task 1.3:** Add alerting for hot/cold transitions
3. **Task 1.4:** Integrate with portfolio manager for rebalancing signals

## Performance Notes

- Requires minimum 60 days of data (12 weeks) for accurate scoring
- Focuses on recent 4-week momentum (matches Kavastu's weekly rebalancing)
- Volume analysis uses 4-week vs 12-week comparison
- Acceleration compares 2-week vs 4-week returns
- All scoring is objective and reproducible

## Acceptance Criteria

✅ Module runs without errors
✅ calculate_trending_score() returns all required fields
✅ Classifications (HOT/COLD/NEUTRAL) work correctly
✅ "Why" explanations are generated
✅ Test block demonstrates functionality
✅ Integration with existing modules verified
✅ Real-world data tested successfully

## File Stats

- **Lines of code:** 453
- **Functions:** 4 (3 public, 1 private)
- **Dependencies:** pandas, typing
- **Test coverage:** Comprehensive unit tests + integration tests

---

**Created:** February 14, 2026
**Time Estimate:** 2 hours
**Actual Time:** Implemented and tested
**Status:** ✅ COMPLETE
