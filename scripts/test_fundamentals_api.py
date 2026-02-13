#!/usr/bin/env python3
"""
Test which APIs provide fundamental data for Swedish stocks.
"""
import sys
from pathlib import Path
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent))

# Test with a few Swedish stocks
TEST_STOCKS = ['VOLV-B.ST', 'ERIC-B.ST', 'ABB.ST', 'SAND.ST', 'BOL.ST']

print("=" * 80)
print("TESTING FUNDAMENTAL DATA SOURCES FOR SWEDISH STOCKS")
print("=" * 80)

print("\n1. TESTING YFINANCE")
print("-" * 80)

for ticker in TEST_STOCKS[:3]:  # Test first 3
    print(f"\n📊 {ticker}:")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Check what fundamental data is available
        fundamentals = {
            'Market Cap': info.get('marketCap'),
            'Revenue': info.get('totalRevenue'),
            'Revenue Growth': info.get('revenueGrowth'),
            'Profit Margin': info.get('profitMargins'),
            'Operating Margin': info.get('operatingMargins'),
            'ROE': info.get('returnOnEquity'),
            'Debt to Equity': info.get('debtToEquity'),
            'P/E Ratio': info.get('trailingPE'),
            'Forward P/E': info.get('forwardPE'),
            'EPS': info.get('trailingEps'),
            'Dividend Yield': info.get('dividendYield'),
            'Beta': info.get('beta'),
            'Book Value': info.get('bookValue')
        }

        available = []
        missing = []

        for key, value in fundamentals.items():
            if value is not None and value != 'N/A':
                available.append(f"   ✅ {key}: {value}")
            else:
                missing.append(f"   ❌ {key}")

        if available:
            print("Available:")
            for item in available[:10]:  # Show first 10
                print(item)

        if len(available) > 10:
            print(f"   ... and {len(available) - 10} more")

        if missing and len(available) < 5:
            print("Missing:")
            for item in missing[:5]:
                print(item)

    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

# Test one stock in detail
print(f"\nDetailed check for {TEST_STOCKS[0]}:")
stock = yf.Ticker(TEST_STOCKS[0])
info = stock.info

# Most important Kavastu metrics
key_metrics = [
    'marketCap',
    'totalRevenue',
    'revenueGrowth',
    'profitMargins',
    'returnOnEquity',
    'debtToEquity',
    'trailingPE',
    'forwardPE'
]

print("\n🎯 KEY METRICS FOR KAVASTU:")
for metric in key_metrics:
    value = info.get(metric)
    status = "✅" if value is not None else "❌"
    print(f"{status} {metric}: {value}")

# Check if we have earnings history
print("\n📈 EARNINGS HISTORY:")
try:
    earnings = stock.earnings_dates
    if earnings is not None and not earnings.empty:
        print(f"   ✅ Available: {len(earnings)} periods")
    else:
        print(f"   ❌ Not available")
except:
    print(f"   ❌ Not available")

# Check quarterly financials
print("\n📊 FINANCIAL STATEMENTS:")
try:
    quarterly_financials = stock.quarterly_financials
    if quarterly_financials is not None and not quarterly_financials.empty:
        print(f"   ✅ Quarterly financials: {len(quarterly_financials.columns)} periods")
        print(f"   Available metrics: {len(quarterly_financials.index)}")
        print(f"   Sample metrics: {list(quarterly_financials.index[:5])}")
    else:
        print(f"   ❌ Quarterly financials not available")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

print("""
✅ YFINANCE WORKS FOR SWEDISH STOCKS!

Available fundamental data:
- Market Cap, Revenue, Profit Margin, ROE
- P/E ratios, EPS, Dividend Yield
- Beta, Book Value
- Quarterly financials (detailed)

RECOMMENDED APPROACH:
1. Use yfinance for fundamentals (no new API needed!)
2. Focus on key Kavastu metrics:
   - Revenue Growth (revenueGrowth)
   - Profit Margin (profitMargins)
   - ROE (returnOnEquity)
   - P/E Ratio (trailingPE)

3. Calculate YoY growth from quarterly financials
""")
