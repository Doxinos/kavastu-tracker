#!/usr/bin/env python3
"""
Quick backtest with just 3 stocks to see historical performance.

Tests a concentrated portfolio (3 stocks) vs diversified approach.
This runs MUCH faster than full backtest!
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtester import backtest_strategy

# Test with current top 3 stocks
TEST_STOCKS = ['BOL.ST', 'SAND.ST', 'EPI-B.ST']

print("📈 QUICK BACKTEST: 3-Stock Portfolio")
print("=" * 80)
print(f"\nTesting: {', '.join(TEST_STOCKS)}")
print("Period: 2020-01-01 to 2026-01-31")
print("Strategy: Hold top 3 stocks, rebalance weekly if they fall out of top rankings")
print()

# Configuration
START_DATE = "2020-01-01"
END_DATE = "2026-01-31"
INITIAL_CAPITAL = 100000  # 100,000 SEK
MAX_HOLDINGS = 3  # Only 3 stocks
REBALANCE = "monthly"  # Monthly for speed

try:
    # Run backtest
    results = backtest_strategy(
        stocks=TEST_STOCKS,
        start_date=START_DATE,
        end_date=END_DATE,
        initial_capital=INITIAL_CAPITAL,
        max_holdings=MAX_HOLDINGS,
        rebalance_frequency=REBALANCE,
        transaction_cost=0.0025
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    metrics = results['metrics']

    print(f"\n🚀 3-STOCK PORTFOLIO PERFORMANCE:")
    print(f"   Initial Investment: 100,000 SEK (2020)")
    print(f"   Final Value: {metrics['final_value']:,.0f} SEK (2026)")
    print(f"   Total Return: {metrics['total_return']:+.2f}%")
    print(f"   CAGR: {metrics['cagr']:.2f}%")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

    if 'benchmark' in metrics:
        bench = metrics['benchmark']
        print(f"\n📊 BENCHMARK (OMXS30 Buy & Hold):")
        print(f"   Final Value: {bench['final_value']:,.0f} SEK")
        print(f"   Total Return: {bench['total_return']:+.2f}%")
        print(f"   CAGR: {bench['cagr']:.2f}%")
        print(f"   Max Drawdown: {bench['max_drawdown']:.2f}%")

        print(f"\n🎯 OUTPERFORMANCE:")
        print(f"   Final Value: +{metrics['final_value'] - bench['final_value']:,.0f} SEK")
        print(f"   Alpha (CAGR): {metrics['cagr'] - bench['cagr']:+.2f}% per year")
        print(f"   Total Return: {metrics['total_return'] - bench['total_return']:+.2f}%")

    # Trade statistics
    trade_log = results['trade_log']
    if not trade_log.empty:
        buys = trade_log[trade_log['action'] == 'BUY']
        sells = trade_log[trade_log['action'] == 'SELL']

        print(f"\n📈 TRADE STATISTICS:")
        print(f"   Total Trades: {len(trade_log)}")
        print(f"   Buys: {len(buys)}")
        print(f"   Sells: {len(sells)}")

    # Final holdings
    final_holdings = results['final_holdings']
    print(f"\n💼 FINAL HOLDINGS:")
    for ticker, holding in final_holdings.items():
        print(f"   {ticker}: {holding['shares']} shares @ {holding['entry_price']:.2f} SEK")

    print(f"\n💡 INSIGHTS:")
    print(f"   Concentrated portfolio (3 stocks) offers:")
    print(f"   ✅ Higher potential returns from best performers")
    print(f"   ✅ Simpler to manage")
    print(f"   ⚠️  Higher risk (less diversification)")
    print(f"   ⚠️  More volatile (larger swings)")

    print(f"\n📊 100,000 SEK in 2020 → {metrics['final_value']:,.0f} SEK in 2026")
    profit = metrics['final_value'] - INITIAL_CAPITAL
    print(f"   Profit: {profit:,.0f} SEK ({metrics['total_return']:.1f}%)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
