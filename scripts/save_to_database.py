#!/usr/bin/env python3
"""
Save screener results to database for historical tracking.

This script:
1. Runs the screener to get top stocks
2. Saves portfolio snapshot
3. Saves screener results
4. Saves any trade recommendations

Run weekly via automation to build historical data.
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database import PortfolioDB
from src.stock_universe import get_all_swedish_stocks
from src.screener import calculate_stock_score
from src.data_fetcher import fetch_stock_data
from src.ma_calculator import calculate_ma50_ma200, calculate_atr
from src.fundamentals import fetch_fundamentals
from src.trending_detector import calculate_trending_score
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

                results.append({
                    'ticker': ticker,
                    'name': ticker.replace('.ST', ''),
                    'score': metrics.get('score', 0),
                    'price': df['Close'].iloc[-1],
                    'signal': metrics.get('signal', 'HOLD'),
                    'ma200_trend': metrics.get('ma200_trend', 'Unknown'),
                    'above_ma200': metrics.get('above_ma200', False),
                    'ma50': df['MA50'].iloc[-1] if 'MA50' in df.columns and len(df) > 0 else None,
                    'ma200': df['MA200'].iloc[-1] if 'MA200' in df.columns and len(df) > 0 else None,
                    'rs_rating': metrics.get('rs_rating', 0),
                    'momentum_3m': metrics.get('momentum_3m', 0),
                    'momentum_6m': metrics.get('momentum_6m', 0),
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


def save_screener_to_database(portfolio_value: float = 100000, cash: float = 10000):
    """
    Run screener and save results to database.

    Args:
        portfolio_value: Current total portfolio value
        cash: Current cash balance
    """
    print("=" * 80)
    print("SAVING SCREENER RESULTS TO DATABASE")
    print("=" * 80)

    # Get current date
    today = datetime.now().strftime("%Y-%m-%d")

    # Run screener
    print("\n📊 Running screener...")
    stocks = get_all_swedish_stocks()
    screener_results = run_screener(stocks)

    if screener_results.empty:
        print("❌ Screener returned no results")
        return

    print(f"✅ Screened {len(screener_results)} stocks")

    # Open database connection
    with PortfolioDB() as db:
        print(f"\n💾 Database: {db.db_path}")

        # Save portfolio snapshot
        print("\n📸 Saving portfolio snapshot...")
        portfolio_metrics = {
            'total_value': portfolio_value,
            'cash': cash,
            'invested': portfolio_value - cash,
            'ytd_return': 0.0,  # Calculate from previous snapshots
            'week_return': 0.0,
            'month_return': 0.0,
            'year_return': 0.0,
            'holdings_count': 0,  # Will be updated with actual holdings
            'benchmark_ytd': 0.0,
            'alpha_ytd': 0.0
        }

        # Check if there's a previous snapshot to calculate returns
        previous = db.get_latest_snapshot()
        if previous:
            previous_value = previous['total_value']
            portfolio_metrics['week_return'] = ((portfolio_value - previous_value) / previous_value) * 100
            print(f"   Previous snapshot: {previous['date']} ({previous_value:,.0f} SEK)")
            print(f"   Week return: {portfolio_metrics['week_return']:+.2f}%")

        snapshot_id = db.save_weekly_snapshot(today, portfolio_metrics)
        print(f"✅ Snapshot saved (ID: {snapshot_id})")
        print(f"   Total value: {portfolio_value:,.0f} SEK")
        print(f"   Cash: {cash:,.0f} SEK")
        print(f"   Invested: {portfolio_value - cash:,.0f} SEK")

        # Save screener results (top 50 stocks to database)
        print(f"\n📋 Saving top 50 screener results...")
        top_stocks = screener_results.head(50).copy()

        db.save_screener_results(snapshot_id, today, top_stocks)
        print(f"✅ Saved {len(top_stocks)} stocks to database")

        # Show top 10
        print("\n🏆 Top 10 Stocks:")
        for idx, row in top_stocks.head(10).iterrows():
            trending_emoji = "🔥" if row.get('trending_classification') == 'HOT' else "❄️" if row.get('trending_classification') == 'COLD' else "➖"
            print(f"   {idx+1:2d}. {row['ticker']:12s} Score: {row['score']:5.1f}  {trending_emoji} Trending: {row.get('trending_score', 0):3.0f}/100")

        # Show database size
        db_size = db.db_path.stat().st_size / 1024
        print(f"\n💾 Database size: {db_size:.1f} KB")

        # Show statistics
        print("\n📈 Database Statistics:")
        cursor = db.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM weekly_snapshots")
        snapshot_count = cursor.fetchone()[0]
        print(f"   Weekly snapshots: {snapshot_count}")

        cursor.execute("SELECT COUNT(*) FROM screener_results")
        screener_count = cursor.fetchone()[0]
        print(f"   Screener results: {screener_count}")

        cursor.execute("SELECT COUNT(*) FROM trade_history")
        trade_count = cursor.fetchone()[0]
        print(f"   Trade history: {trade_count}")

        if snapshot_count > 1:
            print(f"\n📊 Historical data: {snapshot_count} weeks tracked")
            print(f"   Storage: ~{db_size / snapshot_count:.1f} KB per week")

    print("\n" + "=" * 80)
    print("✅ DATABASE UPDATE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Save screener results to database')
    parser.add_argument('--portfolio-value', type=float, default=100000,
                       help='Current portfolio value (default: 100000 SEK)')
    parser.add_argument('--cash', type=float, default=10000,
                       help='Current cash balance (default: 10000 SEK)')

    args = parser.parse_args()

    save_screener_to_database(
        portfolio_value=args.portfolio_value,
        cash=args.cash
    )
