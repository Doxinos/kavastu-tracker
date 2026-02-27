#!/usr/bin/env python3
"""
Weekly Kavastu Automation Script

Runs every Sunday at 19:00 to:
1. Screen all Swedish stocks
2. Save results to database
3. Generate trade recommendations
4. Create weekly summary report
5. Scrape MarketMate analyses (YouTube + website)

Usage:
    python scripts/weekly_automation.py
    python scripts/weekly_automation.py --portfolio-value 100000 --cash 10000
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database import PortfolioDB
from src.stock_universe import get_all_swedish_stocks
from src.screener import calculate_stock_score
from src.data_fetcher import fetch_stock_data
from src.ma_calculator import calculate_ma50_ma200, calculate_atr
from src.fundamentals import fetch_fundamentals
from src.trending_detector import calculate_trending_score
from src.marketmate_scraper import run_full_scrape
import time


def run_screener(stocks: list) -> pd.DataFrame:
    """
    Run the Kavastu screener on all stocks.
    Returns DataFrame with screener results + trending analysis sorted by score.
    """
    print(f"\n{'=' * 80}")
    print("RUNNING SCREENER")
    print(f"{'=' * 80}")
    print(f"Scanning {len(stocks)} Swedish stocks...")

    results = []
    total = len(stocks)

    # Fetch OMXS30 benchmark data for relative strength
    print("Fetching OMXS30 benchmark...")
    benchmark_df = fetch_stock_data("^OMXS30", period="6mo")
    if benchmark_df is None or benchmark_df.empty:
        print("⚠️  Could not fetch benchmark, using defaults")
        benchmark_returns = {'return_4w': 0.0}
    else:
        # Calculate 4-week benchmark return
        if len(benchmark_df) >= 20:
            benchmark_4w = ((benchmark_df['Close'].iloc[-1] / benchmark_df['Close'].iloc[-20]) - 1) * 100
            benchmark_returns = {'return_4w': benchmark_4w}
        else:
            benchmark_returns = {'return_4w': 0.0}

    print(f"Benchmark 4-week return: {benchmark_returns['return_4w']:.2f}%")

    for i, ticker in enumerate(stocks, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{total} stocks...")

        try:
            # Fetch data
            df = fetch_stock_data(ticker, period="1y")
            if df is None or df.empty:
                continue

            # Calculate indicators
            df = calculate_ma50_ma200(df)
            df['ATR'] = calculate_atr(df, period=14)

            # Get fundamentals
            fundamentals = fetch_fundamentals(ticker)

            # Calculate Kavastu score (0-130 points)
            dummy_benchmark = (5.0, 10.0)  # Tuple of (3m_return, 6m_return)
            metrics = calculate_stock_score(ticker, df, dummy_benchmark, include_fundamentals=True)

            if metrics:
                # Calculate trending score
                trending_metrics = calculate_trending_score(ticker, df, benchmark_returns)

                # Derive MA200 trend status
                price = df['Close'].iloc[-1]
                ma200_val = df['MA200'].iloc[-1] if 'MA200' in df.columns else None
                above_ma200 = price > ma200_val if ma200_val else False
                ma200_rising = metrics.get('ma200_rising', False)

                if above_ma200 and ma200_rising:
                    ma200_trend = 'Bullish'
                elif above_ma200:
                    ma200_trend = 'Above'
                elif not above_ma200 and not ma200_rising:
                    ma200_trend = 'Bearish'
                else:
                    ma200_trend = 'Below'

                results.append({
                    'ticker': ticker,
                    'name': ticker.replace('.ST', ''),
                    'score': metrics.get('score', 0),
                    'price': price,
                    'signal': metrics.get('signal', 'HOLD'),
                    'ma200_trend': ma200_trend,
                    'above_ma200': above_ma200,
                    'ma50': df['MA50'].iloc[-1] if 'MA50' in df.columns and len(df) > 0 else None,
                    'ma200': ma200_val,
                    'rs_rating': metrics.get('relative_strength_3m', 0),
                    'momentum_3m': metrics.get('relative_strength_3m', 0),
                    'momentum_6m': metrics.get('relative_strength_6m', 0),
                    'quality_score': metrics.get('quality_score', 0),
                    # Trending fields
                    'trending_score': trending_metrics['trending_score'],
                    'trending_classification': trending_metrics['classification'],
                    'trending_reason': trending_metrics['reason'],
                    'return_4w': trending_metrics['return_4w'],
                    'rs_vs_benchmark': trending_metrics['rs_vs_benchmark']
                })

            time.sleep(0.15)  # Rate limiting

        except Exception as e:
            print(f"  ⚠️  Error processing {ticker}: {e}")
            continue

    # Create DataFrame and sort by Kavastu score
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values('score', ascending=False).reset_index(drop=True)

    print(f"\n✅ Screener complete: {len(df_results)} stocks ranked")
    if not df_results.empty:
        print(f"\nTop 10 stocks:")
        print(df_results.head(10)[['ticker', 'score', 'trending_score', 'trending_classification']].to_string(index=False))

    return df_results


def generate_trade_recommendations(screener_results: pd.DataFrame) -> dict:
    """
    Generate BUY/SELL recommendations based on screener results.

    BUY criteria:
    - Score >= 100 (top tier)
    - Trending HOT (score >= 70)
    - Above MA200

    Returns:
        Dict with 'buy_signals' and 'sell_signals' lists
    """
    buy_signals = []

    # Filter for buy candidates
    buy_candidates = screener_results[
        (screener_results['score'] >= 100) &
        (screener_results['trending_score'] >= 70) &
        (screener_results['above_ma200'] == True)
    ]

    for _, stock in buy_candidates.iterrows():
        buy_signals.append({
            'ticker': stock['ticker'],
            'score': stock['score'],
            'trending_score': stock['trending_score'],
            'trending_classification': stock['trending_classification'],
            'price': stock['price'],
            'reason': f"Score {stock['score']:.0f}/130 (Top Tier) • Trending {stock['trending_classification']} ({stock['trending_score']:.0f}/100) • Above MA200"
        })

    return {
        'buy_signals': buy_signals,
        'sell_signals': []  # Will implement sell logic when we have portfolio tracking
    }


def create_weekly_summary(screener_results: pd.DataFrame, recommendations: dict,
                         snapshot_id: int, portfolio_metrics: dict) -> str:
    """Create a text summary of the week's analysis."""

    today = datetime.now().strftime("%Y-%m-%d")

    # Get trending stats
    hot_stocks = screener_results[screener_results['trending_classification'] == 'HOT']
    cold_stocks = screener_results[screener_results['trending_classification'] == 'COLD']
    neutral_stocks = screener_results[screener_results['trending_classification'] == 'NEUTRAL']

    summary = f"""
{'=' * 80}
KAVASTU WEEKLY SUMMARY - {today}
{'=' * 80}

📊 PORTFOLIO SNAPSHOT
   Total Value:    {portfolio_metrics['total_value']:>12,.0f} SEK
   Cash:           {portfolio_metrics['cash']:>12,.0f} SEK
   Invested:       {portfolio_metrics['invested']:>12,.0f} SEK
   Week Return:    {portfolio_metrics['week_return']:>12.2f}%
   Holdings:       {portfolio_metrics['holdings_count']:>12} stocks

📈 SCREENER RESULTS
   Stocks Scanned: {len(screener_results):>12}
   Top Score:      {screener_results.iloc[0]['ticker']:>12} ({screener_results.iloc[0]['score']:.1f})

   Trending:
   🔥 HOT:         {len(hot_stocks):>12} stocks
   ❄️  COLD:        {len(cold_stocks):>12} stocks
   ➖ NEUTRAL:      {len(neutral_stocks):>12} stocks

🏆 TOP 10 STOCKS
"""

    for idx, row in screener_results.head(10).iterrows():
        trending_emoji = "🔥" if row['trending_classification'] == 'HOT' else "❄️" if row['trending_classification'] == 'COLD' else "➖"
        summary += f"   {idx+1:2d}. {row['ticker']:12s} Score: {row['score']:5.1f}  {trending_emoji} Trending: {row['trending_score']:3.0f}/100\n"

    summary += f"\n🔥 TOP 5 HOT TRENDING STOCKS\n"
    for idx, row in hot_stocks.head(5).iterrows():
        summary += f"   {row['ticker']:12s} {row['trending_score']:3.0f}/100 - {row['trending_reason']}\n"

    summary += f"\n🎯 TRADE RECOMMENDATIONS\n"
    if len(recommendations['buy_signals']) > 0:
        summary += f"   🟢 BUY SIGNALS: {len(recommendations['buy_signals'])}\n"
        for signal in recommendations['buy_signals']:
            summary += f"      {signal['ticker']}: {signal['reason']}\n"
    else:
        summary += f"   No buy signals this week\n"

    if len(recommendations['sell_signals']) > 0:
        summary += f"\n   🔴 SELL SIGNALS: {len(recommendations['sell_signals'])}\n"
    else:
        summary += f"\n   No sell signals this week\n"

    summary += f"\n💾 DATABASE\n"
    summary += f"   Snapshot ID:    {snapshot_id:>12}\n"
    summary += f"   Stocks Saved:   {len(screener_results):>12}\n"

    summary += f"\n{'=' * 80}\n"

    return summary


def run_weekly_automation(portfolio_value: float = 100000, cash: float = 10000):
    """
    Main automation function - runs the complete weekly workflow.

    Args:
        portfolio_value: Current total portfolio value
        cash: Current cash balance
    """
    print(f"\n{'=' * 80}")
    print("KAVASTU WEEKLY AUTOMATION")
    print(f"{'=' * 80}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get current date
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Run screener
    print("\n📊 Step 1/5: Running screener...")
    stocks = get_all_swedish_stocks()
    screener_results = run_screener(stocks)

    if screener_results.empty:
        print("❌ Screener returned no results - aborting")
        return

    print(f"✅ Screened {len(screener_results)} stocks")

    # 2. Save to database
    print("\n💾 Step 2/5: Saving to database...")
    with PortfolioDB() as db:
        # Calculate portfolio metrics
        portfolio_metrics = {
            'total_value': portfolio_value,
            'cash': cash,
            'invested': portfolio_value - cash,
            'ytd_return': 0.0,
            'week_return': 0.0,
            'month_return': 0.0,
            'year_return': 0.0,
            'holdings_count': 0,
            'benchmark_ytd': 0.0,
            'alpha_ytd': 0.0
        }

        # Check if there's a previous snapshot to calculate returns
        previous = db.get_latest_snapshot()
        if previous:
            previous_value = previous['total_value']
            portfolio_metrics['week_return'] = ((portfolio_value - previous_value) / previous_value) * 100
            print(f"   Previous value: {previous_value:,.0f} SEK")
            print(f"   Week return: {portfolio_metrics['week_return']:+.2f}%")

        # Save snapshot
        snapshot_id = db.save_weekly_snapshot(today, portfolio_metrics)
        print(f"✅ Snapshot saved (ID: {snapshot_id})")

        # Save screener results (top 50 + all watchlist stocks)
        top_stocks = screener_results.head(50).copy()
        top_tickers = set(top_stocks['ticker'].tolist())

        # Include watchlist stocks even if not in top 50
        watchlist_items = db.get_watchlist()
        watchlist_tickers = {item['ticker'] for item in watchlist_items}
        missing_watchlist = watchlist_tickers - top_tickers

        if missing_watchlist:
            watchlist_extras = screener_results[screener_results['ticker'].isin(missing_watchlist)]
            if not watchlist_extras.empty:
                top_stocks = pd.concat([top_stocks, watchlist_extras], ignore_index=True)
                print(f"   Added {len(watchlist_extras)} watchlist stocks outside top 50")

        db.save_screener_results(snapshot_id, today, top_stocks)
        print(f"✅ Saved {len(top_stocks)} stocks to database")

        # Get database stats
        db_size = db.db_path.stat().st_size / 1024
        print(f"   Database size: {db_size:.1f} KB")

    # 3. Generate trade recommendations
    print("\n🎯 Step 3/5: Generating trade recommendations...")
    recommendations = generate_trade_recommendations(screener_results)
    print(f"✅ {len(recommendations['buy_signals'])} buy signals, {len(recommendations['sell_signals'])} sell signals")

    # 4. Create and save weekly summary
    print("\n📝 Step 4/5: Creating weekly summary...")
    summary = create_weekly_summary(screener_results, recommendations, snapshot_id, portfolio_metrics)

    # Save summary to file
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    summary_file = reports_dir / f"weekly_summary_{today}.txt"
    summary_file.write_text(summary)
    print(f"✅ Summary saved to: {summary_file}")

    # Print summary to console
    print(summary)

    # 5. Scrape MarketMate analyses
    print("\n📰 Step 5/5: Scraping MarketMate analyses...")
    try:
        scrape_result = run_full_scrape(save_to_db=True)
        yt_count = len(scrape_result.get('youtube', []))
        web_count = len(scrape_result.get('website', []))
        print(f"✅ MarketMate: {yt_count} YouTube analyses, {web_count} website analyses scraped")

        if scrape_result.get('regime'):
            regime = scrape_result['regime']
            print(f"   Market regime: {regime.get('regime', 'UNKNOWN')} - {regime.get('summary', '')[:80]}")
    except Exception as e:
        print(f"⚠️  MarketMate scrape failed (non-critical): {e}")

    print(f"\n{'=' * 80}")
    print("✅ WEEKLY AUTOMATION COMPLETE")
    print(f"{'=' * 80}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Kavastu weekly automation')
    parser.add_argument('--portfolio-value', type=float, default=100000,
                       help='Current portfolio value (default: 100000 SEK)')
    parser.add_argument('--cash', type=float, default=10000,
                       help='Current cash balance (default: 10000 SEK)')

    args = parser.parse_args()

    run_weekly_automation(
        portfolio_value=args.portfolio_value,
        cash=args.cash
    )
