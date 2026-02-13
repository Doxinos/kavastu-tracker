#!/usr/bin/env python3
"""
Daily Monitor - Quick health check of current holdings.

Run daily (Mon-Fri) to catch:
- Stocks dropping below MA200
- Large daily price moves
- Death crosses
- Score deterioration
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.portfolio_manager import Portfolio, detect_weak_holdings
from src.data_fetcher import fetch_portfolio_data, fetch_benchmark_returns
from src.ma_calculator import calculate_ma50_ma200
from src.screener import calculate_stock_score
import pandas as pd


def main():
    """Run daily monitor."""
    print("=" * 80)
    print(f"📅 DAILY MONITOR - {datetime.now().strftime('%Y-%m-%d %A')}")
    print("=" * 80)

    # Load portfolio
    portfolio = Portfolio()
    current_holdings = portfolio.get_tickers()

    if not current_holdings:
        print("\n⚠️  No holdings tracked in config/active_portfolio.csv")
        print("   Add your holdings to start monitoring.")
        return

    print(f"\n💼 Monitoring {len(current_holdings)} holdings:")
    print(f"   {', '.join(current_holdings)}")

    # Fetch current data
    print(f"\n📊 Fetching latest data...")
    holdings_data = fetch_portfolio_data(current_holdings, period='1y')

    if not holdings_data:
        print("⚠️ Could not fetch data")
        return

    # Calculate metrics
    benchmark_returns = fetch_benchmark_returns()
    holdings_metrics = []

    for ticker, df in holdings_data.items():
        df = calculate_ma50_ma200(df)
        metrics = calculate_stock_score(ticker, df, benchmark_returns)

        # Add daily change
        if len(df) >= 2:
            yesterday_price = df['Close'].iloc[-2]
            today_price = df['Close'].iloc[-1]
            daily_change = ((today_price - yesterday_price) / yesterday_price) * 100
            metrics['daily_change'] = daily_change
        else:
            metrics['daily_change'] = 0.0

        holdings_metrics.append(metrics)

    holdings_df = pd.DataFrame(holdings_metrics)

    # Update portfolio
    current_prices = {row['ticker']: row['price']
                     for _, row in holdings_df.iterrows()}
    portfolio.update_prices(current_prices)
    portfolio.save_holdings()

    # Overall status
    total_value = portfolio.get_total_value()
    avg_distance = holdings_df['distance_ma200'].mean()

    print(f"\n💰 Portfolio Status:")
    print(f"   Total Value: {total_value:,.0f} SEK")
    print(f"   Avg Distance from MA200: {avg_distance:+.2f}%")
    print(f"   Avg Score: {holdings_df['score'].mean():.1f}/120")

    # Check for alerts
    alerts_found = False

    # 1. Check for stocks below MA200
    below_ma200 = holdings_df[holdings_df['distance_ma200'] < -3]
    if not below_ma200.empty:
        alerts_found = True
        print(f"\n🔴 ALERT: Stocks >3% below MA200:")
        for _, row in below_ma200.iterrows():
            print(f"   {row['ticker']:<12} {row['distance_ma200']:+.2f}% (Score: {row['score']:.1f})")

    # 2. Check for death crosses
    death_crosses = holdings_df[holdings_df['death_cross'] == True]
    if not death_crosses.empty:
        alerts_found = True
        print(f"\n🔴 ALERT: Death crosses detected:")
        for _, row in death_crosses.iterrows():
            days = row.get('days_since_death_cross', 0)
            print(f"   {row['ticker']:<12} Crossed {days} days ago (Score: {row['score']:.1f})")

    # 3. Check for large daily moves
    large_moves = holdings_df[abs(holdings_df['daily_change']) > 5]
    if not large_moves.empty:
        alerts_found = True
        print(f"\n⚠️  Large daily moves (>5%):")
        for _, row in large_moves.iterrows():
            direction = "📈" if row['daily_change'] > 0 else "📉"
            print(f"   {row['ticker']:<12} {direction} {row['daily_change']:+.2f}%")

    # 4. Check for weak scores
    weak_scores = holdings_df[holdings_df['score'] < 60]
    if not weak_scores.empty:
        alerts_found = True
        print(f"\n⚠️  Weak scores (<60):")
        for _, row in weak_scores.iterrows():
            print(f"   {row['ticker']:<12} Score: {row['score']:.1f}/120")

    # 5. Show daily gainers/losers
    print(f"\n📊 Daily Performance:")

    # Top 3 gainers
    top_gainers = holdings_df.nlargest(3, 'daily_change')
    print(f"   Top Gainers:")
    for _, row in top_gainers.iterrows():
        print(f"      {row['ticker']:<12} +{row['daily_change']:.2f}%")

    # Top 3 losers
    top_losers = holdings_df.nsmallest(3, 'daily_change')
    print(f"   Top Losers:")
    for _, row in top_losers.iterrows():
        print(f"      {row['ticker']:<12} {row['daily_change']:+.2f}%")

    if not alerts_found:
        print(f"\n✅ All holdings look healthy!")
        print(f"   No immediate concerns detected.")
    else:
        print(f"\n💡 Action items:")
        print(f"   - Review alerted stocks")
        print(f"   - Consider early exit if deterioration continues")
        print(f"   - Wait for Sunday review for full analysis")

    print(f"\n📅 Next: Run sunday_review.py this Sunday for weekly rebalancing")


if __name__ == "__main__":
    main()
