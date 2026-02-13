#!/usr/bin/env python3
"""
Full Kavastu Strategy Backtest 2020-2026
Tests strategy across full market cycle (bull + COVID crash + recovery + bear)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stock_universe import get_all_swedish_stocks
from src.backtester import backtest_strategy

print("📈 KAVASTU FULL BACKTEST 2020-2026")
print("=" * 80)
print("\nThis backtest validates the strategy across:")
print("  - 2020 Q1: COVID crash (-30%)")
print("  - 2020-2021: Bull market recovery")
print("  - 2022: Bear market (-20%)")
print("  - 2023-2024: Bull market")
print("  - 2025-2026: Recent market\n")

# Get all stocks
all_stocks = get_all_swedish_stocks()
print(f"📊 Stock Universe: {len(all_stocks)} Swedish stocks")

# Use top 50 for reasonable performance (full 113 would take very long)
print(f"⏱️  Using top 50 stocks for reasonable backtest time")
print(f"   (Full 113-stock backtest would take 2-3 hours)\n")
test_stocks = all_stocks[:50]

# Configuration
START_DATE = "2020-01-01"
END_DATE = "2026-01-31"
INITIAL_CAPITAL = 100000  # 100,000 SEK
MAX_HOLDINGS = 14
REBALANCE = "monthly"

try:
    # Run backtest
    results = backtest_strategy(
        stocks=test_stocks,
        start_date=START_DATE,
        end_date=END_DATE,
        initial_capital=INITIAL_CAPITAL,
        max_holdings=MAX_HOLDINGS,
        rebalance_frequency=REBALANCE,
        transaction_cost=0.0025  # 0.25% per trade
    )

    # Display results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    metrics = results['metrics']

    print(f"\n🚀 STRATEGY PERFORMANCE (6 years):")
    print(f"   Total Return: {metrics['total_return']:+.2f}%")
    print(f"   CAGR: {metrics['cagr']:.2f}%")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Volatility: {metrics['volatility']:.2f}%")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Final Value: {metrics['final_value']:,.0f} SEK")

    # Benchmark comparison
    if 'benchmark' in metrics:
        bench = metrics['benchmark']
        print(f"\n📊 BENCHMARK (OMXS30 Buy & Hold):")
        print(f"   Total Return: {bench['total_return']:+.2f}%")
        print(f"   CAGR: {bench['cagr']:.2f}%")
        print(f"   Max Drawdown: {bench['max_drawdown']:.2f}%")
        print(f"   Final Value: {bench['final_value']:,.0f} SEK")

        print(f"\n🎯 OUTPERFORMANCE:")
        print(f"   Alpha (CAGR): {metrics['cagr'] - bench['cagr']:+.2f}% per year")
        print(f"   Total Return: {metrics['total_return'] - bench['total_return']:+.2f}%")
        print(f"   Max DD Improvement: {bench['max_drawdown'] - metrics['max_drawdown']:+.2f}%")
        print(f"   Risk-Adjusted (Sharpe): {metrics['sharpe_ratio']:.2f}")

    # Save results
    output_dir = Path(__file__).parent.parent / "backtests"
    output_dir.mkdir(exist_ok=True)

    equity_path = output_dir / "equity_curve_2020_2026.csv"
    trades_path = output_dir / "trade_log_2020_2026.csv"

    results['equity_curve'].to_csv(equity_path, index=False)
    results['trade_log'].to_csv(trades_path, index=False)

    print(f"\n💾 Results saved:")
    print(f"   Equity curve: {equity_path}")
    print(f"   Trade log: {trades_path}")

    print(f"\n✅ BACKTEST COMPLETE!")

    # Compare to research
    print(f"\n📚 COMPARISON TO KAVASTU RESEARCH:")
    print(f"   Research: 12.2% CAGR, -22% max DD")
    print(f"   Our test: {metrics['cagr']:.1f}% CAGR, {metrics['max_drawdown']:.1f}% max DD")

    if metrics['cagr'] >= 10 and metrics['max_drawdown'] > -30:
        print(f"   ✅ VALIDATED: Strategy performs as expected!")
    else:
        print(f"   ⚠️  Different from research (might be due to stock selection/period)")

except Exception as e:
    print(f"\n❌ Error running backtest: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
