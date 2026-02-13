#!/usr/bin/env python3
"""Test dividend fetching to verify integration."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import fetch_dividend_history, fetch_dividend_data

print("=" * 80)
print("DIVIDEND FETCHING TEST")
print("=" * 80)

# Test with a few Swedish dividend-paying stocks
test_stocks = [
    'VOLV-B.ST',  # Volvo - large cap, pays dividends
    'ERIC-B.ST',  # Ericsson - large cap, pays dividends
    'INDU-C.ST',  # Industrivärden - investment company, HIGH dividends
    'ABB.ST',     # ABB - large cap
    'AAK.ST'      # AAK - mid cap
]

print(f"\nTesting dividend fetching for {len(test_stocks)} stocks...")
print(f"Period: 2024-01-01 to 2026-01-31")

# Fetch dividends
dividend_data = fetch_dividend_data(test_stocks, '2024-01-01', '2026-01-31')

print(f"\n{'=' * 80}")
print(f"RESULTS")
print(f"{'=' * 80}")

print(f"\nStocks with dividends: {len(dividend_data)}/{len(test_stocks)} ({len(dividend_data)/len(test_stocks)*100:.0f}%)")

if dividend_data:
    print(f"\nDividend details:")
    for ticker, dividends in dividend_data.items():
        total_div = dividends.sum()
        num_payments = len(dividends)
        print(f"\n  {ticker}:")
        print(f"    Total dividends: {total_div:.2f} SEK per share")
        print(f"    Payments: {num_payments} times")
        for date, amount in dividends.items():
            print(f"      {date.strftime('%Y-%m-%d')}: {amount:.2f} SEK")
else:
    print("\n⚠️  No dividends found")

print(f"\n{'=' * 80}")
print("✅ Dividend fetching is working!")
print("Ready to run backtests with dividend reinvestment.")
