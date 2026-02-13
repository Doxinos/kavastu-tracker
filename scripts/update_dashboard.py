#!/usr/bin/env python3
"""
Weekly Dashboard Update - Kavastu Portfolio Tracker

Automates the weekly workflow:
1. Run screener on all 110 Swedish stocks
2. Generate buy/sell recommendations
3. Update Google Sheets dashboard
4. Display summary for manual review

Usage:
    python scripts/update_dashboard.py [--spreadsheet "Your Spreadsheet Name"]
    python scripts/update_dashboard.py --create  # Create new spreadsheet
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.sheets_manager import SheetsManager
from src.stock_universe import get_all_swedish_stocks
from src.screener import calculate_stock_score
from src.data_fetcher import fetch_stock_data, fetch_current_price
from src.ma_calculator import calculate_ma50_ma200, calculate_atr
from src.fundamentals import get_stock_fundamentals

# Configuration
CREDENTIALS_PATH = Path(__file__).parent.parent / "config" / "credentials" / "claude-mcp-484313-5647d3a2a087.json"
DEFAULT_SPREADSHEET = "Kavastu Portfolio Tracker"
PORTFOLIO_FILE = Path(__file__).parent.parent / "config" / "active_portfolio.csv"


def run_screener(stocks: list) -> pd.DataFrame:
    """
    Run the Kavastu screener on all stocks.

    Args:
        stocks: List of stock tickers

    Returns:
        DataFrame with screener results sorted by score
    """
    print(f"\n{'=' * 80}")
    print("RUNNING SCREENER")
    print(f"{'=' * 80}")
    print(f"Scanning {len(stocks)} Swedish stocks...")

    results = []
    total = len(stocks)

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
            fundamentals = get_stock_fundamentals(ticker)

            # Calculate score
            # Note: Need benchmark returns - using dummy for now
            dummy_benchmark = {'3m': 5.0, '6m': 10.0}
            metrics = calculate_stock_score(ticker, df, dummy_benchmark, include_fundamentals=True)

            if metrics:
                results.append({
                    'ticker': ticker,
                    'name': ticker.replace('.ST', ''),
                    'score': metrics.get('score', 0),
                    'price': df['Close'].iloc[-1],
                    'signal': metrics.get('signal', 'HOLD'),
                    'ma200_trend': metrics.get('ma200_trend', 'Unknown'),
                    'above_ma200': metrics.get('above_ma200', False)
                })

        except Exception as e:
            print(f"  ⚠️  Error processing {ticker}: {e}")
            continue

    # Create DataFrame and sort by score
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values('score', ascending=False).reset_index(drop=True)

    print(f"\n✅ Screener complete: {len(df_results)} stocks ranked")
    print(f"\nTop 10 stocks:")
    print(df_results.head(10)[['ticker', 'score', 'price', 'signal']].to_string(index=False))

    return df_results


def load_current_portfolio() -> pd.DataFrame:
    """
    Load current portfolio from CSV file.

    Returns:
        DataFrame with current holdings
    """
    if PORTFOLIO_FILE.exists():
        df = pd.DataFrame(pd.read_csv(PORTFOLIO_FILE))
        print(f"✅ Loaded {len(df)} holdings from portfolio")
        return df
    else:
        print("⚠️  No portfolio file found, returning empty portfolio")
        return pd.DataFrame()


def generate_trade_recommendations(screener_results: pd.DataFrame, current_portfolio: pd.DataFrame) -> tuple:
    """
    Generate buy and sell recommendations based on screener results and current holdings.

    Args:
        screener_results: DataFrame from screener
        current_portfolio: DataFrame with current holdings

    Returns:
        Tuple of (buy_list, sell_list)
    """
    print(f"\n{'=' * 80}")
    print("GENERATING TRADE RECOMMENDATIONS")
    print(f"{'=' * 80}")

    buy_list = []
    sell_list = []

    # Current holdings tickers
    if not current_portfolio.empty and 'ticker' in current_portfolio.columns:
        current_tickers = set(current_portfolio['ticker'].values)
    else:
        current_tickers = set()

    # Top 70 stocks from screener
    top_stocks = screener_results.head(70)
    top_tickers = set(top_stocks['ticker'].values)

    # BUY signals: Top 70 stocks with score >= 110 that we don't own
    buy_candidates = screener_results[
        (screener_results['score'] >= 110) &
        (~screener_results['ticker'].isin(current_tickers))
    ].head(10)  # Limit to top 10 buy signals

    for _, row in buy_candidates.iterrows():
        buy_list.append({
            'ticker': row['ticker'],
            'score': row['score'],
            'price': row['price'],
            'shares': 0,  # Will be calculated based on ATR sizing
            'amount': 0,  # Will be calculated
            'reason': f"Score {row['score']} (top 70, not owned)"
        })

    # SELL signals: Current holdings that dropped out of top 70 OR score < 90
    for ticker in current_tickers:
        stock_data = screener_results[screener_results['ticker'] == ticker]

        if stock_data.empty:
            # Stock not in screener results (data fetch failed)
            continue

        score = stock_data.iloc[0]['score']
        in_top_70 = ticker in top_tickers

        if score < 90 or not in_top_70:
            reason = f"Score dropped to {score}" if score < 90 else "Dropped out of top 70"

            sell_list.append({
                'ticker': ticker,
                'score': score,
                'current_value': 0,  # Will be calculated from portfolio
                'reason': reason
            })

    print(f"\n🟢 BUY SIGNALS: {len(buy_list)}")
    if buy_list:
        for b in buy_list:
            print(f"  {b['ticker']}: Score {b['score']:.0f} - {b['reason']}")

    print(f"\n🔴 SELL SIGNALS: {len(sell_list)}")
    if sell_list:
        for s in sell_list:
            print(f"  {s['ticker']}: Score {s['score']:.0f} - {s['reason']}")

    return buy_list, sell_list


def calculate_portfolio_metrics(current_portfolio: pd.DataFrame) -> dict:
    """
    Calculate current portfolio metrics.

    Args:
        current_portfolio: DataFrame with current holdings

    Returns:
        Dict with portfolio metrics
    """
    if current_portfolio.empty:
        return {
            'total_value': 0,
            'cash': 100000,  # Starting capital
            'invested': 0,
            'holdings_count': 0,
            'total_return': 0,
            'ytd_return': 0,
            '30d_return': 0,
            '7d_return': 0
        }

    # TODO: Calculate actual metrics from portfolio
    # For now, return placeholder values

    metrics = {
        'total_value': len(current_portfolio) * 10000,  # Placeholder
        'cash': 50000,  # Placeholder
        'invested': len(current_portfolio) * 10000 - 50000,
        'holdings_count': len(current_portfolio),
        'total_return': 15.5,  # Placeholder
        'ytd_return': 8.2,  # Placeholder
        '30d_return': 2.1,  # Placeholder
        '7d_return': 0.5  # Placeholder
    }

    return metrics


def update_google_sheets(screener_results: pd.DataFrame, buy_list: list, sell_list: list,
                         current_portfolio: pd.DataFrame, metrics: dict, spreadsheet_name: str):
    """
    Update all Google Sheets with latest data.

    Args:
        screener_results: DataFrame from screener
        buy_list: List of buy recommendations
        sell_list: List of sell recommendations
        current_portfolio: DataFrame with current holdings
        metrics: Dict with portfolio metrics
        spreadsheet_name: Name of the Google Spreadsheet
    """
    print(f"\n{'=' * 80}")
    print("UPDATING GOOGLE SHEETS")
    print(f"{'=' * 80}")

    # Initialize sheets manager
    manager = SheetsManager(str(CREDENTIALS_PATH))

    if not manager.authenticate():
        print("❌ Failed to authenticate with Google Sheets")
        return False

    if not manager.open_spreadsheet(spreadsheet_name):
        print(f"❌ Failed to open spreadsheet '{spreadsheet_name}'")
        return False

    # Update Sheet 1: Portfolio Overview
    print("\n📊 Updating Portfolio Overview...")
    manager.update_portfolio_overview(metrics, metrics['holdings_count'])

    # Update Sheet 2: Current Holdings
    if not current_portfolio.empty:
        print("📊 Updating Current Holdings...")
        holdings_list = current_portfolio.to_dict('records')
        manager.update_current_holdings(holdings_list)

    # Update Sheet 3: Screener Results
    print("📊 Updating Screener Results...")
    manager.update_screener_results(screener_results)

    # Update Sheet 4: Trade Recommendations
    print("📊 Updating Trade Recommendations...")
    manager.update_trade_recommendations(buy_list, sell_list)

    # Update Sheet 5: Performance Tracking
    print("📊 Appending Performance History...")
    today = datetime.now().strftime('%Y-%m-%d')
    manager.append_performance_history(today, metrics)

    print("\n✅ Google Sheets updated successfully!")
    print(f"\nView your dashboard: https://docs.google.com/spreadsheets/d/{manager.spreadsheet.id}")

    return True


def main():
    """Main entry point for weekly dashboard update."""
    parser = argparse.ArgumentParser(description='Update Kavastu Portfolio Dashboard')
    parser.add_argument('--spreadsheet', type=str, default=DEFAULT_SPREADSHEET,
                       help='Name of Google Spreadsheet')
    parser.add_argument('--create', action='store_true',
                       help='Create a new spreadsheet')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run screener without updating Google Sheets')

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("KAVASTU WEEKLY DASHBOARD UPDATE")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Spreadsheet: {args.spreadsheet}")

    # Create new spreadsheet if requested
    if args.create:
        manager = SheetsManager(str(CREDENTIALS_PATH))
        if manager.authenticate():
            url = manager.create_spreadsheet(args.spreadsheet)
            if url:
                print(f"\n✅ Spreadsheet created: {url}")
                print("\nRun the script again without --create to populate it with data")
                return
        print("❌ Failed to create spreadsheet")
        return

    # 1. Load current portfolio
    current_portfolio = load_current_portfolio()

    # 2. Run screener
    stocks = get_all_swedish_stocks()
    screener_results = run_screener(stocks)

    if screener_results.empty:
        print("❌ Screener returned no results")
        return

    # 3. Generate trade recommendations
    buy_list, sell_list = generate_trade_recommendations(screener_results, current_portfolio)

    # 4. Calculate portfolio metrics
    metrics = calculate_portfolio_metrics(current_portfolio)

    # 5. Update Google Sheets (unless dry-run)
    if not args.dry_run:
        update_google_sheets(
            screener_results,
            buy_list,
            sell_list,
            current_portfolio,
            metrics,
            args.spreadsheet
        )
    else:
        print("\n⚠️  DRY RUN: Skipping Google Sheets update")

    # 6. Summary
    print(f"\n{'=' * 80}")
    print("WEEKLY UPDATE COMPLETE")
    print(f"{'=' * 80}")
    print(f"✅ Screener: {len(screener_results)} stocks ranked")
    print(f"🟢 Buy signals: {len(buy_list)}")
    print(f"🔴 Sell signals: {len(sell_list)}")
    print(f"💼 Current holdings: {metrics['holdings_count']}")
    print(f"💰 Portfolio value: {metrics['total_value']:,.0f} SEK")
    print(f"\nNext steps:")
    print(f"1. Review trade recommendations in Google Sheets")
    print(f"2. Execute trades on Avanza (Sunday 20:00-20:30)")
    print(f"3. Update portfolio file: config/active_portfolio.csv")


if __name__ == "__main__":
    main()
