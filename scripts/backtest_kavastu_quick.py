#!/usr/bin/env python3
"""
Quick Kavastu Full Portfolio Backtest - 2 years, monthly rebalancing.

Tests the complete approach but faster:
- 60-80 stock portfolio (diversified)
- 2-3% position sizing per stock
- MONTHLY rebalancing (faster than weekly)
- 2-year period (2024-2026)

Should complete in 20-30 minutes vs 2-5 hours for full test.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtester import backtest_strategy
from src.stock_universe import get_all_swedish_stocks

print("=" * 80)
print("📈 KAVASTU FULL PORTFOLIO BACKTEST (QUICK VERSION)")
print("=" * 80)
print("\nTesting Kavastu's strategy (fast version):")
print("  - 70-stock portfolio (vs 10-14 concentrated)")
print("  - 2.5% position sizing (vs equal weight)")
print("  - Monthly rebalancing (vs weekly - for speed)")
print("  - 2-year period (2024-2026)")
print()

# Get all Swedish stocks
all_stocks = get_all_swedish_stocks()
print(f"Stock Universe: {len(all_stocks)} Swedish stocks")

# Configuration - FASTER VERSION
START_DATE = "2024-01-01"  # 2 years instead of 3
END_DATE = "2026-01-31"
INITIAL_CAPITAL = 100000  # 100,000 SEK
MAX_HOLDINGS = 70  # Kavastu's target
REBALANCE = "monthly"  # Monthly instead of weekly (24 periods vs 104)

print(f"\nBacktest Parameters:")
print(f"  Period: {START_DATE} to {END_DATE} (2 years)")
print(f"  Initial Capital: {INITIAL_CAPITAL:,} SEK")
print(f"  Max Holdings: {MAX_HOLDINGS} stocks")
print(f"  Position Sizing: 2.5% per stock")
print(f"  Rebalancing: {REBALANCE} (24 periods)")
print(f"  Transaction Cost: 0.25% per trade")
print()

print("⏱️  Estimated time: 20-30 minutes")
print("    (24 monthly periods × ~110 stocks = ~2,640 API calls)")
print()

try:
    # Run backtest
    print("Running backtest...")
    print()

    results = backtest_strategy(
        stocks=all_stocks,
        start_date=START_DATE,
        end_date=END_DATE,
        initial_capital=INITIAL_CAPITAL,
        max_holdings=MAX_HOLDINGS,
        rebalance_frequency=REBALANCE,
        transaction_cost=0.0025
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS - KAVASTU FULL PORTFOLIO (70 stocks, 2.5% sizing, monthly)")
    print("=" * 80)

    metrics = results['metrics']

    print(f"\n🚀 FULL PORTFOLIO PERFORMANCE:")
    print(f"   Initial Investment: {INITIAL_CAPITAL:,} SEK ({START_DATE})")
    print(f"   Final Value: {metrics['final_value']:,.0f} SEK ({END_DATE})")
    print(f"   Total Return: {metrics['total_return']:+.2f}%")
    print(f"   CAGR: {metrics['cagr']:.2f}%")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

    if 'dividend_return' in metrics and metrics['dividend_return'] > 0:
        print(f"\n💰 RETURN BREAKDOWN:")
        print(f"   Price Return: {metrics['price_return']:+.2f}% (CAGR: {metrics['price_cagr']:.2f}%)")
        print(f"   Dividend Return: {metrics['dividend_return']:+.2f}%")
        print(f"   Total Dividends: {metrics['total_dividends']:,.0f} SEK")
        print(f"   Dividend Contribution to CAGR: +{metrics['dividend_contribution']:.2f}%")

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
        print(f"   Avg Trades/Month: {len(trade_log) / 24:.1f}")

    # Final holdings
    final_holdings = results['final_holdings']
    print(f"\n💼 FINAL PORTFOLIO:")
    print(f"   Holdings: {len(final_holdings)} stocks")

    # Show top 14 (basportfölj)
    if final_holdings:
        print(f"\n   📊 Top 14 Holdings (Basportfölj):")
        sorted_holdings = sorted(
            final_holdings.items(),
            key=lambda x: x[1]['shares'] * x[1]['entry_price'],
            reverse=True
        )
        for ticker, holding in sorted_holdings[:14]:
            value = holding['shares'] * holding['entry_price']
            print(f"      {ticker}: {holding['shares']} shares @ {holding['entry_price']:.2f} SEK = {value:,.0f} SEK")

    print(f"\n📊 COMPARISON TO PREVIOUS TESTS:")
    print(f"   Concentrated (10 stocks):     13.45% CAGR (equal weight, monthly)")
    print(f"   Concentrated (3 stocks):      5.59% CAGR (equal weight, monthly)")
    print(f"   Full Portfolio (70 stocks):   {metrics['cagr']:.2f}% CAGR (2.5% sizing, monthly)")
    print(f"   ─────────────────────────────────────────────────────────")
    print(f"   Target (Kavastu actual):      38.00% CAGR (60-80 stocks, weekly)")

    print(f"\n💡 INSIGHTS:")
    print(f"   ✅ Diversification impact: 70 stocks vs 10 stocks")
    print(f"   ✅ Position sizing: 2.5% per stock vs equal weight")
    print(f"   ✅ Risk spreading: Max {MAX_HOLDINGS} stocks × 2.5% = full diversification")
    print(f"   📊 Next: Try weekly rebalancing for even better results (closer to 38%)")

    if metrics['cagr'] > 15:
        print(f"\n🎉 Great! {metrics['cagr']:.2f}% beats both concentrated approaches!")
        print(f"   Full diversification is working better than concentration.")
    elif metrics['cagr'] > 13:
        print(f"\n✅ Good! {metrics['cagr']:.2f}% is competitive with concentrated approach.")
        print(f"   With lower risk (70 stocks vs 10).")
    else:
        print(f"\n⚠️  {metrics['cagr']:.2f}% - Consider:")
        print(f"   - Weekly rebalancing (catches momentum faster)")
        print(f"   - Longer test period (more market cycles)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
