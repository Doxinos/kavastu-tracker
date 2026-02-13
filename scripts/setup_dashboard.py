#!/usr/bin/env python3
"""
Setup Kavastu Portfolio Dashboard

Creates a new Google Spreadsheet with all 7 sheets properly formatted:
1. Portfolio Overview - Main dashboard
2. Current Holdings - Live positions
3. Screener Results - Weekly top 70
4. Trade Recommendations - Buy/sell signals
5. Performance Tracking - Historical data
6. Dividend Tracker - Upcoming dividends
7. ISK Tax Calculator - Tax estimates

Usage:
    python scripts/setup_dashboard.py
    python scripts/setup_dashboard.py --name "My Custom Name"
    python scripts/setup_dashboard.py --email your.email@example.com
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.sheets_manager import SheetsManager

CREDENTIALS_PATH = Path(__file__).parent.parent / "config" / "credentials" / "claude-mcp-484313-5647d3a2a087.json"


def setup_portfolio_overview(manager):
    """Set up Sheet 1: Portfolio Overview."""
    print("📊 Setting up Portfolio Overview...")

    ws = manager.get_worksheet("Portfolio Overview")
    if not ws:
        return False

    # Clear and set up structure
    ws.clear()

    # Title
    ws.update('A1:F1', [['KAVASTU PORTFOLIO TRACKER']])
    ws.merge_cells('A1:F1')
    ws.format('A1:F1', {
        'textFormat': {'bold': True, 'fontSize': 18},
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })

    # Last updated
    ws.update('A2', [['Last Updated: (will be auto-updated)']])

    # Section headers and data structure
    data = [
        ['', ''],
        ['Portfolio Metrics', ''],
        ['Total Value', '0 SEK'],
        ['Cash', '0 SEK'],
        ['Invested', '0 SEK'],
        ['Holdings', '0'],
        ['', ''],
        ['Performance', ''],
        ['Total Return', '0.00%'],
        ['YTD Return', '0.00%'],
        ['30d Return', '0.00%'],
        ['7d Return', '0.00%'],
        ['', ''],
        ['vs OMXS30', ''],
        ['Alpha (YTD)', '0.00%'],
        ['Sharpe Ratio', '0.00'],
        ['', ''],
        ['Risk Metrics', ''],
        ['Max Drawdown', '0.00%'],
        ['Current Drawdown', '0.00%'],
        ['Volatility', '0.00%'],
        ['', ''],
        ['Weekly Actions', ''],
        ['Last Screener Run', 'Never'],
        ['Trades This Week', '0'],
        ['Next Rebalance', 'Sunday 19:00'],
    ]

    ws.update('A3', data)

    # Format section headers
    ws.format('A4', {'textFormat': {'bold': True, 'fontSize': 12}})
    ws.format('A10', {'textFormat': {'bold': True, 'fontSize': 12}})
    ws.format('A15', {'textFormat': {'bold': True, 'fontSize': 12}})
    ws.format('A18', {'textFormat': {'bold': True, 'fontSize': 12}})
    ws.format('A23', {'textFormat': {'bold': True, 'fontSize': 12}})

    print("✅ Portfolio Overview configured")
    return True


def setup_current_holdings(manager):
    """Set up Sheet 2: Current Holdings."""
    print("📊 Setting up Current Holdings...")

    ws = manager.get_worksheet("Current Holdings")
    if not ws:
        return False

    ws.clear()

    # Headers
    headers = [
        ['Ticker', 'Name', 'Shares', 'Avg Price', 'Current Price',
         'Value (SEK)', 'P&L (SEK)', 'P&L %', 'Weight %',
         'Score', 'Signal', 'Days Held']
    ]
    ws.update('A1', headers)

    # Format header row
    ws.format('A1:L1', {
        'textFormat': {'bold': True, 'fontSize': 11},
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })

    # Set column widths
    ws.format('A:A', {'columnWidth': 100})  # Ticker
    ws.format('B:B', {'columnWidth': 150})  # Name
    ws.format('K:K', {'columnWidth': 80})   # Signal

    # Add sample row with formulas (for reference)
    sample = [
        ['VOLV-B.ST', 'Volvo B', '100', '250.00', '260.00',
         '26000', '1000', '4.00%', '5.20%', '115', '🟢 BUY', '45']
    ]
    ws.update('A2', sample)

    # Add note
    ws.update('A50', [['Note: This sheet will be auto-updated by the weekly screener']])
    ws.format('A50', {'textFormat': {'italic': True}})

    print("✅ Current Holdings configured")
    return True


def setup_screener_results(manager):
    """Set up Sheet 3: Screener Results."""
    print("📊 Setting up Screener Results...")

    ws = manager.get_worksheet("Screener Results")
    if not ws:
        return False

    ws.clear()

    # Title
    ws.update('A1', [['Screener Results - (will be updated weekly)']])
    ws.format('A1', {'textFormat': {'bold': True, 'fontSize': 12}})

    # Headers
    headers = [
        ['Rank', 'Ticker', 'Name', 'Score', 'Price (SEK)',
         'MA200 Trend', 'Signal', 'In Portfolio']
    ]
    ws.update('A3', headers)

    ws.format('A3:H3', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })

    # Sample data
    sample = [
        ['1', 'VOLV-B.ST', 'Volvo B', '125', '260.00', 'Rising', '🟢 BUY', '✓'],
        ['2', 'ASSA-B.ST', 'Assa Abloy B', '123', '315.50', 'Rising', '🟢 BUY', ''],
        ['3', 'SAND.ST', 'Sandvik', '120', '225.00', 'Flat', '🟡 HOLD', '✓'],
    ]
    ws.update('A4', sample)

    print("✅ Screener Results configured")
    return True


def setup_trade_recommendations(manager):
    """Set up Sheet 4: Trade Recommendations."""
    print("📊 Setting up Trade Recommendations...")

    ws = manager.get_worksheet("Trade Recommendations")
    if not ws:
        return False

    ws.clear()

    # Title
    ws.update('A1', [['Trade Recommendations - (updated weekly)']])
    ws.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})

    # BUY section
    ws.update('A3', [['🟢 BUY SIGNALS']])
    ws.format('A3', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.7, 'green': 1.0, 'blue': 0.7}
    })

    buy_headers = [['Ticker', 'Score', 'Price (SEK)', 'Shares', 'Amount (SEK)', 'Reason']]
    ws.update('A4', buy_headers)
    ws.format('A4:F4', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })

    # Sample buy
    ws.update('A5', [['VOLV-B.ST', '125', '260.00', '100', '26000', 'New top scorer']])

    # SELL section
    ws.update('A10', [['🔴 SELL SIGNALS']])
    ws.format('A10', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 1.0, 'green': 0.7, 'blue': 0.7}
    })

    sell_headers = [['Ticker', 'Score', 'Current Value', 'Reason']]
    ws.update('A11', sell_headers)
    ws.format('A11:D11', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })

    # Sample sell
    ws.update('A12', [['OLD-STOCK.ST', '85', '15000', 'Score dropped below 90']])

    print("✅ Trade Recommendations configured")
    return True


def setup_performance_tracking(manager):
    """Set up Sheet 5: Performance Tracking."""
    print("📊 Setting up Performance Tracking...")

    ws = manager.get_worksheet("Performance Tracking")
    if not ws:
        return False

    ws.clear()

    # Headers
    headers = [
        ['Date', 'Total Value', 'Cash', 'Invested', 'Return %',
         'OMXS30 %', 'Alpha', 'Sharpe', 'Max DD']
    ]
    ws.update('A1', headers)

    ws.format('A1:I1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })

    # Sample data
    sample = [
        ['2026-02-13', '100000', '50000', '50000', '0.00%', '0.00%', '0.00%', '0.00', '0.00%'],
    ]
    ws.update('A2', sample)

    # Note
    ws.update('A50', [['Historical performance data will be appended weekly']])
    ws.format('A50', {'textFormat': {'italic': True}})

    print("✅ Performance Tracking configured")
    return True


def setup_dividend_tracker(manager):
    """Set up Sheet 6: Dividend Tracker."""
    print("📊 Setting up Dividend Tracker...")

    ws = manager.get_worksheet("Dividend Tracker")
    if not ws:
        return False

    ws.clear()

    # Title
    ws.update('A1', [['Dividend Tracker']])
    ws.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})

    # Headers
    headers = [
        ['Ticker', 'Name', 'Ex-Date', 'Pay Date', 'Amount/Share',
         'Shares Owned', 'Expected Dividend', 'Status']
    ]
    ws.update('A3', headers)

    ws.format('A3:H3', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
    })

    # Summary section
    ws.update('A50', [
        ['Dividend Summary'],
        ['Total YTD Dividends', '0 SEK'],
        ['Expected This Quarter', '0 SEK'],
        ['Annual Yield', '0.00%']
    ])
    ws.format('A50', {'textFormat': {'bold': True, 'fontSize': 12}})

    print("✅ Dividend Tracker configured")
    return True


def setup_isk_tax_calculator(manager):
    """Set up Sheet 7: ISK Tax Calculator."""
    print("📊 Setting up ISK Tax Calculator...")

    ws = manager.get_worksheet("ISK Tax Calculator")
    if not ws:
        return False

    ws.clear()

    # Title
    ws.update('A1', [['ISK Account Tax Calculator']])
    ws.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})

    # Info
    info = [
        ['', ''],
        ['ISK Tax Information', ''],
        ['Tax Rate (2026)', '1.065%'],
        ['Tax Basis', 'Portfolio value (not gains)'],
        ['Payment', 'Automatic quarterly deduction'],
        ['', ''],
        ['Your Tax Estimate', ''],
        ['Current Portfolio Value', '100,000 SEK'],
        ['Annual Tax Estimate', '1,065 SEK'],
        ['Quarterly Tax', '266 SEK'],
        ['Monthly Tax', '89 SEK'],
        ['', ''],
        ['Advantage vs Regular Account', ''],
        ['No capital gains tax', '✓'],
        ['No dividend tax', '✓'],
        ['Perfect for active trading', '✓'],
        ['Simple tax reporting', '✓'],
    ]
    ws.update('A2', info)

    # Format headers
    ws.format('A3', {'textFormat': {'bold': True, 'fontSize': 12}})
    ws.format('A9', {'textFormat': {'bold': True, 'fontSize': 12}})
    ws.format('A15', {'textFormat': {'bold': True, 'fontSize': 12}})

    print("✅ ISK Tax Calculator configured")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Setup Kavastu Portfolio Dashboard')
    parser.add_argument('--name', type=str, default='Kavastu Portfolio Tracker',
                       help='Name for the new spreadsheet')
    parser.add_argument('--email', type=str,
                       help='Email to share the spreadsheet with')

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("KAVASTU DASHBOARD SETUP")
    print("=" * 80)

    # Initialize manager
    manager = SheetsManager(str(CREDENTIALS_PATH))

    # Authenticate
    if not manager.authenticate():
        print("❌ Authentication failed")
        return

    # Create spreadsheet
    print(f"\n📊 Creating spreadsheet: {args.name}")
    url = manager.create_spreadsheet(args.name)

    if not url:
        print("❌ Failed to create spreadsheet")
        return

    print(f"✅ Spreadsheet created: {url}")

    # Share with email if provided
    if args.email:
        try:
            manager.spreadsheet.share(args.email, perm_type='user', role='writer')
            print(f"✅ Shared with {args.email}")
        except Exception as e:
            print(f"⚠️  Failed to share: {e}")

    # Set up all sheets
    print(f"\n{'=' * 80}")
    print("CONFIGURING SHEETS")
    print(f"{'=' * 80}\n")

    setup_portfolio_overview(manager)
    setup_current_holdings(manager)
    setup_screener_results(manager)
    setup_trade_recommendations(manager)
    setup_performance_tracking(manager)
    setup_dividend_tracker(manager)
    setup_isk_tax_calculator(manager)

    # Delete the default "Sheet1" if it exists
    try:
        sheet1 = manager.spreadsheet.worksheet("Sheet1")
        manager.spreadsheet.del_worksheet(sheet1)
        print("✅ Removed default Sheet1")
    except:
        pass

    print(f"\n{'=' * 80}")
    print("SETUP COMPLETE!")
    print(f"{'=' * 80}")
    print(f"\n📊 Your dashboard is ready: {url}")
    print("\nNext steps:")
    print("1. Open the dashboard in your browser")
    print("2. Review the structure and formatting")
    print("3. Run weekly update: python scripts/update_dashboard.py")
    print(f"4. Bookmark the URL for easy access")


if __name__ == "__main__":
    main()
