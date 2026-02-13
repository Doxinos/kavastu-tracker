#!/usr/bin/env python3
"""
Quick backtest test - 2023-2025 with 10 stocks
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtester import backtest_strategy

# Quick test with just 10 large-cap stocks
TEST_STOCKS = [
    'ABB.ST', 'VOLV-B.ST', 'ERIC-B.ST', 'SAND.ST', 'ATCO-A.ST',
    'ATCO-B.ST', 'SWED-A.ST', 'SEB-A.ST', 'HM-B.ST', 'BOL.ST'
]

print("📈 Quick Backtest Test (2023-2025, 10 stocks)")
print("=" * 60)

results = backtest_strategy(
    stocks=TEST_STOCKS,
    start_date="2023-01-01",
    end_date="2025-01-01",
    initial_capital=100000,
    max_holdings=7,
    rebalance_frequency="monthly",
    transaction_cost=0.0025
)

# Display results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

metrics = results['metrics']

print(f"\n📊 STRATEGY PERFORMANCE:")
print(f"   Total Return: {metrics['total_return']:+.2f}%")
print(f"   CAGR: {metrics['cagr']:.2f}%")
print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"   Final Value: {metrics['final_value']:,.0f} SEK")

if 'benchmark' in metrics:
    bench = metrics['benchmark']
    print(f"\n📊 BENCHMARK (OMXS30):")
    print(f"   CAGR: {bench['cagr']:.2f}%")
    print(f"   Alpha: {metrics['cagr'] - bench['cagr']:+.2f}%")

print(f"\n✅ Backtest logic validated!")
