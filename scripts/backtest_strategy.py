#!/usr/bin/env python3
"""
Run Kavastu Strategy Backtest
Simulates historical performance from 2020-2026.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stock_universe import get_all_swedish_stocks
from src.backtester import backtest_strategy


def main():
    """Run the backtest."""
    print("📈 Kavastu Strategy Backtesting")
    print("=" * 80)

    # Get stock universe
    all_stocks = get_all_swedish_stocks()
    print(f"\n📊 Loaded {len(all_stocks)} Swedish stocks from universe")

    # Configuration
    START_DATE = "2020-01-01"
    END_DATE = "2026-01-01"
    INITIAL_CAPITAL = 100000  # 100,000 SEK
    MAX_HOLDINGS = 14
    REBALANCE = "monthly"

    # Note: For first test, use smaller sample to speed up
    print(f"\n⚠️  Note: Using top 30 stocks for faster initial test")
    print(f"   (Full universe backtest will take longer)")
    test_stocks = all_stocks[:30]  # Start with 30 stocks for faster test

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
        print("PERFORMANCE RESULTS")
        print("=" * 80)

        metrics = results['metrics']

        print(f"\n📊 STRATEGY PERFORMANCE:")
        print(f"   Total Return: {metrics['total_return']:+.2f}%")
        print(f"   CAGR: {metrics['cagr']:.2f}%")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"   Volatility: {metrics['volatility']:.2f}%")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Final Value: {metrics['final_value']:,.0f} SEK")
        print(f"   Years: {metrics['years']:.1f}")

        # Benchmark comparison
        if 'benchmark' in metrics:
            bench = metrics['benchmark']
            print(f"\n📊 BENCHMARK (OMXS30 Buy & Hold):")
            print(f"   Total Return: {bench['total_return']:+.2f}%")
            print(f"   CAGR: {bench['cagr']:.2f}%")
            print(f"   Max Drawdown: {bench['max_drawdown']:.2f}%")
            print(f"   Final Value: {bench['final_value']:,.0f} SEK")

            print(f"\n🎯 OUTPERFORMANCE:")
            print(f"   Alpha (CAGR): {metrics['cagr'] - bench['cagr']:+.2f}%")
            print(f"   Total Return: {metrics['total_return'] - bench['total_return']:+.2f}%")
            print(f"   Max DD Improvement: {bench['max_drawdown'] - metrics['max_drawdown']:+.2f}%")

        # Trade statistics
        trade_log = results['trade_log']
        if not trade_log.empty:
            buys = trade_log[trade_log['action'] == 'BUY']
            sells = trade_log[trade_log['action'] == 'SELL']

            print(f"\n📈 TRADE STATISTICS:")
            print(f"   Total Trades: {len(trade_log)}")
            print(f"   Buys: {len(buys)}")
            print(f"   Sells: {len(sells)}")

            if not sells.empty and 'reason' in sells.columns:
                fire_alarm_sells = sells[sells['reason'] == 'Below MA200 (fire alarm)']
                print(f"   Fire Alarm Sells: {len(fire_alarm_sells)}")

        # Final holdings
        final_holdings = results['final_holdings']
        print(f"\n💼 FINAL HOLDINGS ({len(final_holdings)} stocks):")
        for ticker, holding in list(final_holdings.items())[:10]:
            print(f"   {ticker}: {holding['shares']} shares @ {holding['entry_price']:.2f} SEK")

        # Save results
        output_dir = Path(__file__).parent.parent / "backtests"
        output_dir.mkdir(exist_ok=True)

        equity_path = output_dir / "equity_curve.csv"
        trades_path = output_dir / "trade_log.csv"

        results['equity_curve'].to_csv(equity_path, index=False)
        results['trade_log'].to_csv(trades_path, index=False)

        print(f"\n✅ Results saved:")
        print(f"   Equity curve: {equity_path}")
        print(f"   Trade log: {trades_path}")

        print(f"\n💡 Next steps:")
        print(f"   1. Review trade_log.csv to see all trades")
        print(f"   2. Review equity_curve.csv to see portfolio growth")
        print(f"   3. Run full backtest with all {len(all_stocks)} stocks")
        print(f"   4. Try different parameters (max_holdings, rebalance frequency)")

    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
