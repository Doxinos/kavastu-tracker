#!/usr/bin/env python3
"""
Sunday Review - Weekly portfolio analysis and trade recommendations.

Run every Sunday evening to:
1. Review current holdings
2. Compare vs top-ranked stocks
3. Generate Monday morning trade recommendations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stock_universe import get_all_swedish_stocks
from src.screener import run_screen, format_screening_results
from src.portfolio_manager import (
    Portfolio,
    compare_holdings_vs_watchlist,
    detect_weak_holdings,
    format_trade_recommendations,
    calculate_position_size,
    identify_base_portfolio
)
from src.market_regime import (
    get_market_regime,
    calculate_watchlist_health,
    get_position_sizing_recommendation
)
from src.data_fetcher import fetch_portfolio_data
from src.ma_calculator import calculate_ma50_ma200
from src.screener import calculate_stock_score
from src.data_fetcher import fetch_benchmark_returns
from src.fundamentals_detailed import fetch_detailed_fundamentals


def main():
    """Run Sunday review."""
    print("=" * 80)
    print("📅 KAVASTU SUNDAY REVIEW")
    print("=" * 80)
    print(f"Date: {Path(__file__).parent.parent}")

    # 1. Load portfolio
    portfolio = Portfolio()
    current_holdings = portfolio.get_tickers()

    print(f"\n💼 Current Holdings: {len(current_holdings)} stocks")
    if current_holdings:
        print(f"   {', '.join(current_holdings[:10])}")
        if len(current_holdings) > 10:
            print(f"   ... and {len(current_holdings) - 10} more")
    else:
        print("   ⚠️  No holdings tracked. Add stocks to config/active_portfolio.csv")

    # 2. Run full screener
    print(f"\n🔍 Running weekly screener...")
    all_stocks = get_all_swedish_stocks()
    print(f"   Screening {len(all_stocks)} Swedish stocks...")

    results = run_screen(all_stocks, min_score=40, period='1y')

    if results.empty:
        print("⚠️ No stocks passed screening")
        return

    print(f"   ✅ {len(results)} stocks passed (score >= 40)")

    # 3. Market regime analysis
    print("\n📊 Market Regime Analysis:")
    regime_info = get_market_regime()

    if regime_info['regime'] != 'unknown':
        print(f"   OMXS30: {regime_info['index_price']:.2f}")
        print(f"   MA200: {regime_info['index_ma200']:.2f}")
        print(f"   Distance: {regime_info['index_vs_ma200']:+.2f}%")
        print(f"   Regime: {regime_info['regime'].upper()}")

        watchlist_health = calculate_watchlist_health(results)
        print(f"   Watchlist Health: {watchlist_health:.1f}% above MA200")

        position_rec = get_position_sizing_recommendation(
            regime_info['regime'],
            watchlist_health
        )

        print(f"\n💰 Position Sizing Recommendation:")
        print(f"   Target Holdings: {position_rec['target_stocks']} stocks")
        print(f"   Target Cash: {position_rec['target_cash_pct']}")
        print(f"   {position_rec['reasoning']}")

        # Determine target count from recommendation
        # Kavastu: 60-80 stocks (full portfolio), 2-3% each
        target_count_str = position_rec['target_stocks']
        if '-' in target_count_str:
            target_count = int(target_count_str.split('-')[1])  # Use upper bound
        else:
            target_count = int(target_count_str)

        # Override to use Kavastu's actual portfolio size
        if target_count < 60:
            target_count = 70  # Default to 70 (middle of 60-80 range)
            print(f"\n   📊 Kavastu Portfolio: Using 60-80 stock diversification (target: 70)")
    else:
        target_count = 70  # Default: Kavastu's full portfolio size

    # 4. Show top 20 stocks
    print(format_screening_results(results, top_n=20))

    # 5. If we have holdings, compare them
    if current_holdings:
        print("\n" + "=" * 80)
        print("PORTFOLIO ANALYSIS")
        print("=" * 80)

        # Get current metrics for holdings
        print(f"\n📈 Analyzing current holdings...")
        holdings_data = fetch_portfolio_data(current_holdings, period='1y')

        benchmark_returns = fetch_benchmark_returns()
        holdings_metrics = []

        for ticker, df in holdings_data.items():
            df = calculate_ma50_ma200(df)
            metrics = calculate_stock_score(ticker, df, benchmark_returns)
            holdings_metrics.append(metrics)

        holdings_df = pd.DataFrame(holdings_metrics)

        # Update portfolio prices
        current_prices = {row['ticker']: row['price']
                         for _, row in holdings_df.iterrows()}
        portfolio.update_prices(current_prices)
        portfolio.save_holdings()

        total_value = portfolio.get_total_value()
        print(f"   Total Portfolio Value: {total_value:,.0f} SEK")

        # Show position sizing for new stocks (2-3% Kavastu method)
        print(f"\n💡 Position Sizing (Kavastu 2-3% method):")
        print(f"   Target per stock: 2.5% of {total_value:,.0f} SEK = {total_value * 0.025:,.0f} SEK")
        print(f"   At 70 stocks × 2.5% = ~100% invested (fully diversified)")

        # Identify and show basportfölj (top 12-14 holdings)
        base_portfolio = identify_base_portfolio(holdings_df, top_n=14)
        if not base_portfolio.empty:
            print(f"\n📊 BASPORTFÖLJ (Top 14 Strongest Holdings - ~40% portfolio weight):")
            base_total_value = 0
            for idx, row in base_portfolio.iterrows():
                if row['ticker'] in portfolio.holdings['ticker'].values:
                    position_value = portfolio.holdings[portfolio.holdings['ticker'] == row['ticker']]['current_value'].iloc[0]
                    weight = (position_value / total_value) * 100
                    base_total_value += position_value
                    print(f"   {row['ticker']:<12} Score: {row['score']:<6.1f} Value: {position_value:>10,.0f} SEK ({weight:.1f}%)")

            base_weight = (base_total_value / total_value) * 100
            print(f"   ─────────────────────────────────────────────────")
            print(f"   Total Base Portfolio: {base_total_value:,.0f} SEK ({base_weight:.1f}% of portfolio)")

        # Check for weak holdings
        weak_holdings = detect_weak_holdings(holdings_df)

        if weak_holdings:
            print(f"\n⚠️  WEAK HOLDINGS DETECTED ({len(weak_holdings)}):")
            for item in weak_holdings:
                alerts = ', '.join(item['alerts'])
                print(f"   {item['ticker']:<12} {alerts}")

        # Compare holdings vs top stocks
        print(f"\n🔄 Weekly Rotation Analysis:")
        print(f"   Current: {len(current_holdings)} stocks")
        print(f"   Target: {target_count} stocks (Kavastu full portfolio)")
        print(f"   Analyzing for rotation opportunities (\"rensa det svaga\")...")

        holdings_scores = {row['ticker']: row['score']
                          for _, row in holdings_df.iterrows()}

        recommendations = compare_holdings_vs_watchlist(
            current_holdings,
            results,
            holdings_scores,
            target_count=target_count
        )

        # Format and display recommendations
        print(format_trade_recommendations(recommendations))

        # Show position sizing for buy recommendations
        if recommendations['buy']:
            print(f"\n💰 Position Sizing for Buy Candidates (2.5% each):")
            for rec in recommendations['buy'][:5]:  # Show first 5
                ticker = rec['ticker']
                # Find price from results
                stock_data = results[results['ticker'] == ticker]
                if not stock_data.empty:
                    price = stock_data['price'].iloc[0]
                    shares, actual_weight = calculate_position_size(total_value, price)
                    cost = shares * price
                    print(f"   {ticker:<12} {shares:>5} shares @ {price:>7.2f} SEK = {cost:>10,.0f} SEK ({actual_weight:.2f}%)")
            if len(recommendations['buy']) > 5:
                print(f"   ... and {len(recommendations['buy']) - 5} more")

        # Show detailed fundamentals for buy recommendations
        if recommendations['buy']:
            print("\n" + "=" * 80)
            print("FUNDAMENTAL ANALYSIS - BUY CANDIDATES")
            print("=" * 80)

            buy_tickers = [rec['ticker'] for rec in recommendations['buy']]

            # Show comparison table
            print("\n📊 Quick Comparison:")
            print(f"{'Ticker':<12} {'P/E':<8} {'P/S':<8} {'Profit':<10} {'ROE':<8} {'Rev Growth':<12} {'Debt/Eq':<10} {'Score':<8}")
            print("─" * 80)

            for rec in recommendations['buy']:
                ticker = rec['ticker']
                fund = fetch_detailed_fundamentals(ticker)

                pe = f"{fund.get('pe_ratio', 0):.1f}" if fund.get('pe_ratio') else "N/A"
                ps = f"{fund.get('ps_ratio', 0):.1f}" if fund.get('ps_ratio') else "N/A"
                profit = f"{fund.get('profit_margin', 0)*100:.1f}%" if fund.get('profit_margin') else "N/A"
                roe = f"{fund.get('roe', 0)*100:.1f}%" if fund.get('roe') else "N/A"
                growth = fund.get('revenue_growth')
                growth_str = f"{growth*100:+.1f}%" if growth else "N/A"
                debt = f"{fund.get('debt_to_equity', 0):.0f}" if fund.get('debt_to_equity') else "N/A"
                score = rec['score']

                print(f"{ticker:<12} {pe:<8} {ps:<8} {profit:<10} {roe:<8} {growth_str:<12} {debt:<10} {score:<8.1f}")

            print("\n💡 Key Insights:")
            for rec in recommendations['buy']:
                ticker = rec['ticker']
                fund = fetch_detailed_fundamentals(ticker)

                insights = []

                # Check valuation
                pe = fund.get('pe_ratio')
                if pe and pe < 15:
                    insights.append(f"Cheap valuation (P/E {pe:.1f})")

                # Check profitability
                roe = fund.get('roe')
                if roe and roe > 0.20:
                    insights.append(f"Excellent ROE ({roe*100:.1f}%)")

                profit_margin = fund.get('profit_margin')
                if profit_margin and profit_margin > 0.15:
                    insights.append(f"High margins ({profit_margin*100:.1f}%)")

                # Check growth
                rev_growth = fund.get('revenue_growth')
                if rev_growth and rev_growth > 0.10:
                    insights.append(f"Strong growth ({rev_growth*100:+.1f}%)")

                # Check financial health
                debt = fund.get('debt_to_equity')
                if debt and debt < 50:
                    insights.append("Low debt")

                free_cf = fund.get('free_cashflow')
                if free_cf and free_cf > 0:
                    insights.append(f"Positive FCF ({free_cf/1e9:.1f}B)")

                if insights:
                    print(f"\n   {ticker}: {', '.join(insights)}")

        # Save recommendations for Monday
        recommendations_path = Path(__file__).parent.parent / "config" / "monday_trades.txt"
        with open(recommendations_path, 'w') as f:
            f.write(format_trade_recommendations(recommendations))

        print(f"\n💾 Recommendations saved to: {recommendations_path}")

    else:
        print(f"\n💡 No holdings to compare.")
        print(f"   To start tracking, add top {target_count} stocks from above to config/active_portfolio.csv")

    print(f"\n📅 Next steps:")
    print(f"   1. Review recommendations above")
    print(f"   2. Prepare trades for Monday morning")
    print(f"   3. Run daily_monitor.py during the week")


if __name__ == "__main__":
    import pandas as pd  # Need for holdings_df
    main()
