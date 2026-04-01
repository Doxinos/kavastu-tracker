"""Google Sheets Manager - Interface for portfolio dashboard updates."""
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from pathlib import Path

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class SheetsManager:
    """Manage Google Sheets operations for Kavastu portfolio tracking."""

    def __init__(self, credentials_path: str):
        """
        Initialize Google Sheets manager.

        Args:
            credentials_path: Path to Google service account JSON credentials
        """
        self.credentials_path = credentials_path
        self.client = None
        self.spreadsheet = None

    def authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
            print("✅ Authenticated with Google Sheets API")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

    def open_spreadsheet(self, spreadsheet_name: str):
        """
        Open a Google Spreadsheet by name.

        Args:
            spreadsheet_name: Name of the spreadsheet

        Returns:
            True if successful, False otherwise
        """
        try:
            self.spreadsheet = self.client.open(spreadsheet_name)
            print(f"✅ Opened spreadsheet: {spreadsheet_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to open spreadsheet '{spreadsheet_name}': {e}")
            return False

    def create_spreadsheet(self, title: str) -> Optional[str]:
        """
        Create a new Google Spreadsheet.

        Args:
            title: Title for the new spreadsheet

        Returns:
            Spreadsheet URL if successful, None otherwise
        """
        try:
            self.spreadsheet = self.client.create(title)

            # Share with your email so it appears in YOUR Drive (30TB), not service account's Drive
            self.spreadsheet.share('peter@diabol.se', perm_type='user', role='writer')

            url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet.id}"
            print(f"✅ Created spreadsheet: {title}")
            print(f"   URL: {url}")
            return url
        except Exception as e:
            print(f"❌ Failed to create spreadsheet: {e}")
            return None

    def get_worksheet(self, sheet_name: str):
        """
        Get a worksheet by name, create if doesn't exist.

        Args:
            sheet_name: Name of the worksheet

        Returns:
            Worksheet object or None
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet if it doesn't exist
            try:
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=20
                )
                print(f"✅ Created new worksheet: {sheet_name}")
                return worksheet
            except Exception as e:
                print(f"❌ Failed to create worksheet '{sheet_name}': {e}")
                return None

    def update_portfolio_overview(self, metrics: Dict, holdings_count: int):
        """
        Update Sheet 1: Portfolio Overview with current metrics.

        Args:
            metrics: Dict with portfolio metrics (total_value, cash, invested, etc.)
            holdings_count: Number of current holdings
        """
        ws = self.get_worksheet("Portfolio Overview")
        if not ws:
            return False

        try:
            # Header row
            ws.update('A1:B1', [['KAVASTU PORTFOLIO TRACKER', '']])
            ws.format('A1:B1', {
                'textFormat': {'bold': True, 'fontSize': 14},
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8}
            })

            # Update timestamp
            ws.update('A2', [[f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]])

            # Portfolio metrics section
            row = 4
            data = [
                ['Portfolio Metrics', ''],
                ['Total Value', f"{metrics.get('total_value', 0):,.0f} SEK"],
                ['Cash', f"{metrics.get('cash', 0):,.0f} SEK"],
                ['Invested', f"{metrics.get('invested', 0):,.0f} SEK"],
                ['Holdings', str(holdings_count)],
                ['', ''],
                ['Performance', ''],
                ['Total Return', f"{metrics.get('total_return', 0):.2f}%"],
                ['YTD Return', f"{metrics.get('ytd_return', 0):.2f}%"],
                ['30d Return', f"{metrics.get('30d_return', 0):.2f}%"],
                ['7d Return', f"{metrics.get('7d_return', 0):.2f}%"],
            ]

            ws.update(f'A{row}', data)

            # Format headers
            ws.format(f'A{row}', {'textFormat': {'bold': True}})
            ws.format(f'A{row+6}', {'textFormat': {'bold': True}})

            print("✅ Updated Portfolio Overview")
            return True

        except Exception as e:
            print(f"❌ Failed to update Portfolio Overview: {e}")
            return False

    def update_current_holdings(self, holdings: List[Dict]):
        """
        Update Sheet 2: Current Holdings with live portfolio.

        Args:
            holdings: List of dicts with ticker, shares, price, value, score, signal
        """
        ws = self.get_worksheet("Current Holdings")
        if not ws:
            return False

        try:
            # Clear existing data
            ws.clear()

            # Header row
            headers = [
                'Ticker', 'Name', 'Shares', 'Avg Price', 'Current Price',
                'Value (SEK)', 'P&L (SEK)', 'P&L %', 'Weight %',
                'Score', 'Signal', 'Days Held'
            ]
            ws.update('A1', [headers])

            # Format header
            ws.format('A1:L1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })

            # Add holdings data
            if holdings:
                data_rows = []
                for h in holdings:
                    data_rows.append([
                        h.get('ticker', ''),
                        h.get('name', ''),
                        h.get('shares', 0),
                        f"{h.get('avg_price', 0):.2f}",
                        f"{h.get('current_price', 0):.2f}",
                        f"{h.get('value', 0):.2f}",
                        f"{h.get('pnl_sek', 0):.2f}",
                        f"{h.get('pnl_pct', 0):.2f}%",
                        f"{h.get('weight', 0):.2f}%",
                        h.get('score', 0),
                        h.get('signal', 'HOLD'),
                        h.get('days_held', 0)
                    ])

                ws.update('A2', data_rows)

                # Apply conditional formatting to Signal column (K)
                # Color code: BUY=green, SELL=red, HOLD=yellow
                # Note: This requires additional formatting rules in the sheet

            print(f"✅ Updated Current Holdings ({len(holdings)} positions)")
            return True

        except Exception as e:
            print(f"❌ Failed to update Current Holdings: {e}")
            return False

    def update_screener_results(self, screener_data: pd.DataFrame):
        """
        Update Sheet 3: Screener Results with top ranked stocks.

        Args:
            screener_data: DataFrame with columns: ticker, name, score, price, signal
        """
        ws = self.get_worksheet("Screener Results")
        if not ws:
            return False

        try:
            # Clear existing data
            ws.clear()

            # Header with timestamp
            ws.update('A1', [[f"Screener Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}"]])
            ws.format('A1', {'textFormat': {'bold': True, 'fontSize': 12}})

            # Column headers
            headers = ['Rank', 'Ticker', 'Name', 'Score', 'Price (SEK)', 'Signal', 'In Portfolio']
            ws.update('A3', [headers])
            ws.format('A3:G3', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })

            # Add screener data (top 70)
            if not screener_data.empty:
                data_rows = []
                for idx, row in screener_data.head(70).iterrows():
                    data_rows.append([
                        idx + 1,  # Rank
                        row.get('ticker', ''),
                        row.get('name', ''),
                        row.get('score', 0),
                        f"{row.get('price', 0):.2f}",
                        row.get('signal', ''),
                        ''  # Will be filled by formula or script
                    ])

                ws.update('A4', data_rows)

            print(f"✅ Updated Screener Results ({len(screener_data)} stocks)")
            return True

        except Exception as e:
            print(f"❌ Failed to update Screener Results: {e}")
            return False

    def update_trade_recommendations(self, buy_list: List[Dict], sell_list: List[Dict]):
        """
        Update Trade Recommendations sheet with enhanced explanations and news.

        Args:
            buy_list: List of buy recommendations with why_buy and news
            sell_list: List of sell recommendations with why_sell and news
        """
        ws = self.get_worksheet("Trade Recommendations")
        if not ws:
            return False

        try:
            # Clear existing content
            ws.clear()

            # Title
            ws.update('A1', [['Trade Recommendations - (updated weekly)']])
            ws.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})

            current_row = 3

            # ===== BUY SIGNALS SECTION =====
            ws.update(f'A{current_row}', [[f'🟢 BUY SIGNALS ({len(buy_list)} stocks)']])
            ws.format(f'A{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 13},
                'backgroundColor': {'red': 0.7, 'green': 1.0, 'blue': 0.7}
            })

            current_row += 1
            # Headers
            ws.update(f'A{current_row}:E{current_row}', [[
                'Ticker', 'Score', 'Price (SEK)', 'Shares', 'Why Buy'
            ]])
            ws.format(f'A{current_row}:E{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })

            # Buy recommendations
            for trade in buy_list:
                current_row += 1
                ticker = trade['ticker']
                score = trade['score']
                price = trade['price']
                shares = trade.get('shares', 0)
                why_buy = trade.get('why_buy', trade.get('reason', ''))
                news = trade.get('news_headline', '')

                # Main row
                ws.update(f'A{current_row}:E{current_row}', [[
                    ticker, f"{score:.0f}", f"{price:.2f}", shares, why_buy
                ]])
                ws.format(f'A{current_row}:E{current_row}', {'textFormat': {'fontSize': 10}})

                # News row (if available)
                if news and news != 'No recent news':
                    current_row += 1
                    ws.update(f'E{current_row}', [[f'📰 {news}']])
                    ws.format(f'E{current_row}', {
                        'textFormat': {'fontSize': 9, 'italic': True},
                        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                    })

            # ===== SELL SIGNALS SECTION =====
            current_row += 3
            ws.update(f'A{current_row}', [[f'🔴 SELL SIGNALS ({len(sell_list)} stocks)']])
            ws.format(f'A{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 13},
                'backgroundColor': {'red': 1.0, 'green': 0.7, 'blue': 0.7}
            })

            current_row += 1
            # Headers
            ws.update(f'A{current_row}:D{current_row}', [[
                'Ticker', 'Score', 'Current Value', 'Why Sell'
            ]])
            ws.format(f'A{current_row}:D{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })

            # Sell recommendations
            for trade in sell_list:
                current_row += 1
                ticker = trade['ticker']
                score = trade['score']
                value = trade.get('current_value', 0)
                why_sell = trade.get('why_sell', trade.get('reason', ''))
                news = trade.get('news_headline', '')

                # Main row
                ws.update(f'A{current_row}:D{current_row}', [[
                    ticker, f"{score:.0f}", f"{value:,.0f}", why_sell
                ]])
                ws.format(f'A{current_row}:D{current_row}', {'textFormat': {'fontSize': 10}})

                # News row (if available)
                if news and news != 'No recent news':
                    current_row += 1
                    ws.update(f'D{current_row}', [[f'📰 {news}']])
                    ws.format(f'D{current_row}', {
                        'textFormat': {'fontSize': 9, 'italic': True},
                        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                    })

            # Execution notes
            current_row += 3
            ws.update(f'A{current_row}', [['⏰ Execution Notes:']])
            ws.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 12}})

            current_row += 1
            notes = [
                '1. Review each recommendation and verify on Avanza charts',
                '2. SELL positions first (Sunday 20:00) to free up capital',
                '3. BUY new positions second (Sunday 20:15) using freed capital',
                '4. Update portfolio file after all trades execute',
                '5. Position sizes are ATR-adjusted (1-5% per stock)'
            ]
            for note in notes:
                current_row += 1
                ws.update(f'A{current_row}', [[note]])
                ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})

            print("✅ Trade Recommendations sheet updated (with explanations + news)")
            return True

        except Exception as e:
            print(f"❌ Failed to update Trade Recommendations: {e}")
            return False

    def append_performance_history(self, date: str, metrics: Dict):
        """
        Append to Sheet 5: Performance Tracking with daily snapshots.

        Args:
            date: Date string (YYYY-MM-DD)
            metrics: Dict with total_value, cash, invested, return_pct
        """
        ws = self.get_worksheet("Performance Tracking")
        if not ws:
            return False

        try:
            # Check if headers exist
            if not ws.row_values(1):
                headers = ['Date', 'Total Value', 'Cash', 'Invested', 'Return %', 'OMXS30 %']
                ws.update('A1', [headers])
                ws.format('A1:F1', {'textFormat': {'bold': True}})

            # Append new row
            row_data = [
                date,
                metrics.get('total_value', 0),
                metrics.get('cash', 0),
                metrics.get('invested', 0),
                f"{metrics.get('return_pct', 0):.2f}%",
                f"{metrics.get('benchmark_return', 0):.2f}%"
            ]
            ws.append_row(row_data)

            print(f"✅ Appended performance data for {date}")
            return True

        except Exception as e:
            print(f"❌ Failed to append performance history: {e}")
            return False

    def update_executive_summary(self, portfolio_metrics: Dict, market_context: Dict,
                                 trending_data: Dict, buy_list: List, sell_list: List):
        """
        Update Executive Summary sheet (Layer 1 - Quick Glance).

        iPad-optimized single-screen view for Sunday evening trading.

        Args:
            portfolio_metrics: Portfolio value, returns, etc.
            market_context: Market news and sentiment
            trending_data: Hot and cold stocks from trending detector
            buy_list: Trade recommendations (buy)
            sell_list: Trade recommendations (sell)
        """
        ws = self.get_worksheet("Executive Summary")
        if not ws:
            # Create it if it doesn't exist
            ws = self.spreadsheet.add_worksheet(title="Executive Summary", rows=100, cols=10)

        # Clear existing content
        ws.clear()

        # ===== HEADER SECTION =====
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M')

        ws.update('A1:H1', [['KAVASTU PORTFOLIO TRACKER']])
        ws.merge_cells('A1:H1')
        ws.format('A1', {
            'textFormat': {'bold': True, 'fontSize': 18, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
            'horizontalAlignment': 'CENTER'
        })

        ws.update('A2', [[f'Last Updated: {last_updated}']])
        ws.format('A2', {'textFormat': {'italic': True, 'fontSize': 10}})

        # ===== PORTFOLIO VALUE SECTION =====
        current_row = 4
        total_value = portfolio_metrics.get('total_value', 0)
        ytd_return = portfolio_metrics.get('ytd_return', 0)
        cash = portfolio_metrics.get('cash', 0)
        invested = portfolio_metrics.get('invested', 0)

        ws.update(f'A{current_row}', [[f'💰 PORTFOLIO VALUE: {total_value:,.0f} SEK']])
        ws.update(f'F{current_row}', [[f'+{ytd_return:.1f}% (YTD)']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 16},
            'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 1.0}
        })
        ws.format(f'F{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 14},
            'backgroundColor': {'red': 0.7, 'green': 1.0, 'blue': 0.7}
        })

        current_row += 1
        ws.update(f'A{current_row}', [[f'Cash: {cash:,.0f} SEK  |  Invested: {invested:,.0f} SEK']])
        ws.format(f'A{current_row}', {'textFormat': {'fontSize': 12}})

        # ===== MARKET MOOD SECTION =====
        current_row += 2
        sentiment = market_context['sentiment_summary']['overall_sentiment'].upper()
        sentiment_emoji = '🟢' if sentiment == 'POSITIVE' else ('🔴' if sentiment == 'NEGATIVE' else '🟡')

        ws.update(f'A{current_row}', [[f'📊 MARKET MOOD: {sentiment_emoji} {sentiment}']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 14},
            'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
        })

        current_row += 1
        # Show top 3 market headlines
        headlines = market_context['articles'][:3]
        ws.update(f'A{current_row}', [['Top Headlines:']])
        ws.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 11}})

        # Import sentiment emoji function
        from src.news_fetcher import get_market_sentiment_emoji

        for article in headlines:
            current_row += 1
            emoji = get_market_sentiment_emoji(article['sentiment'])
            title = article['title'][:60] + '...' if len(article['title']) > 60 else article['title']
            ws.update(f'A{current_row}', [[f'{emoji} {title}']])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})

        # ===== TRENDING STOCKS SECTION =====
        current_row += 2
        ws.update(f'A{current_row}', [['🔥 HOT STOCKS (Trending Up)']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 13},
            'backgroundColor': {'red': 1.0, 'green': 0.85, 'blue': 0.7}
        })

        current_row += 1
        # Hot stocks table header
        ws.update(f'A{current_row}:C{current_row}', [['Ticker', 'Score', 'Why Hot']])
        ws.format(f'A{current_row}:C{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 11},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })

        # Top 3 hot stocks
        hot_stocks = trending_data.get('hot_stocks', [])[:3]
        for stock in hot_stocks:
            current_row += 1
            reason = stock['reason'][:40] + '...' if len(stock['reason']) > 40 else stock['reason']
            ws.update(f'A{current_row}:C{current_row}', [[
                stock['ticker'],
                f"{stock['trending_score']:.0f}/100",
                reason
            ]])
            ws.format(f'A{current_row}:C{current_row}', {'textFormat': {'fontSize': 10}})

        # Cold stocks
        current_row += 2
        ws.update(f'A{current_row}', [['❄️  COLD STOCKS (Trending Down)']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 13},
            'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1.0}
        })

        current_row += 1
        ws.update(f'A{current_row}:C{current_row}', [['Ticker', 'Score', 'Why Cold']])
        ws.format(f'A{current_row}:C{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 11},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })

        cold_stocks = trending_data.get('cold_stocks', [])[:2]
        for stock in cold_stocks:
            current_row += 1
            reason = stock['reason'][:40] + '...' if len(stock['reason']) > 40 else stock['reason']
            ws.update(f'A{current_row}:C{current_row}', [[
                stock['ticker'],
                f"{stock['trending_score']:.0f}/100",
                reason
            ]])
            ws.format(f'A{current_row}:C{current_row}', {'textFormat': {'fontSize': 10}})

        # ===== ACTION REQUIRED SECTION =====
        current_row += 2
        ws.update(f'A{current_row}', [['📋 ACTION REQUIRED THIS WEEK']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 14},
            'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.7}
        })

        # BUY signals
        current_row += 2
        ws.update(f'A{current_row}', [[f'🟢 BUY ({len(buy_list)} stocks)']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 12},
            'backgroundColor': {'red': 0.7, 'green': 1.0, 'blue': 0.7}
        })

        total_buy_amount = 0
        for trade in buy_list[:5]:  # Top 5 buy signals
            current_row += 1
            ticker = trade['ticker']
            score = trade.get('score', 0)
            shares = trade.get('shares', 0)
            amount = trade.get('amount', 0)
            total_buy_amount += amount

            ws.update(f'A{current_row}', [[f'{ticker}: {score:.0f}pts → Buy {shares} shares ({amount:,.0f} SEK)']])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 11}})

        if buy_list:
            current_row += 1
            ws.update(f'F{current_row}', [[f'Total: {total_buy_amount:,.0f}']])
            ws.format(f'F{current_row}', {'textFormat': {'bold': True}})

        # SELL signals
        current_row += 2
        ws.update(f'A{current_row}', [[f'🔴 SELL ({len(sell_list)} stocks)']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 12},
            'backgroundColor': {'red': 1.0, 'green': 0.7, 'blue': 0.7}
        })

        for trade in sell_list[:5]:  # Top 5 sell signals
            current_row += 1
            ticker = trade['ticker']
            score = trade.get('score', 0)
            reason = trade.get('reason', 'Score dropped')[:30]

            ws.update(f'A{current_row}', [[f'{ticker}: {score:.0f}pts → Sell ({reason})']])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 11}})

        # Execution checklist
        current_row += 2
        ws.update(f'A{current_row}', [['⏰ Execute trades: Sunday 20:00-20:30 on Avanza']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 12},
            'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.9}
        })

        current_row += 1
        checklist = [
            '[ ] 1. SELL first (free up capital)',
            '[ ] 2. BUY second (use freed capital)',
            '[ ] 3. Update portfolio file'
        ]
        for item in checklist:
            current_row += 1
            ws.update(f'A{current_row}', [[item]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 11}})

        # Set column widths for iPad optimization
        ws.update_index(0)  # Refresh

        print("✅ Executive Summary sheet updated (Layer 1)")
        return True

    def update_trending_deep_dive(self, trending_data: Dict, screener_results: pd.DataFrame):
        """
        Update Trending Stocks Deep Dive sheet (Layer 2).

        iPad landscape-optimized detailed view for analyzing momentum shifts.

        Args:
            trending_data: Hot and cold stocks from trending detector
            screener_results: Full screener results for context
        """
        from src.news_fetcher import fetch_stock_news, get_market_sentiment_emoji

        ws = self.get_worksheet("Trending Deep Dive")
        if not ws:
            # Create it if it doesn't exist
            ws = self.spreadsheet.add_worksheet(title="Trending Deep Dive", rows=200, cols=10)

        # Clear existing content
        ws.clear()

        # ===== HEADER =====
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M')

        ws.update('A1:H1', [['TRENDING STOCKS DEEP DIVE']])
        ws.merge_cells('A1:H1')
        ws.format('A1', {
            'textFormat': {'bold': True, 'fontSize': 16, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'backgroundColor': {'red': 0.3, 'green': 0.5, 'blue': 0.9},
            'horizontalAlignment': 'CENTER'
        })

        ws.update('A2', [[f'Last Updated: {last_updated}']])
        ws.format('A2', {'textFormat': {'italic': True, 'fontSize': 10}})

        current_row = 4

        # ===== HOT STOCKS SECTION =====
        ws.update(f'A{current_row}', [['🔥 HOT STOCKS - DETAILED ANALYSIS (Top 10)']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 14},
            'backgroundColor': {'red': 1.0, 'green': 0.85, 'blue': 0.7}
        })

        current_row += 2

        # Process each hot stock
        hot_stocks = trending_data.get('hot_stocks', [])[:10]
        for i, stock in enumerate(hot_stocks, 1):
            ticker = stock['ticker']
            name = stock['name']
            trending_score = stock['trending_score']
            kavastu_score = stock['kavastu_score']
            price = stock['price']
            return_4w = stock['return_4w']
            reason = stock['reason']

            # Stock header
            ws.update(f'A{current_row}', [[f"{i}. {ticker} - {name}"]])
            ws.update(f'G{current_row}', [[f"Score: {trending_score:.0f}/100"]])
            ws.format(f'A{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 12},
                'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
            })
            ws.format(f'G{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 1.0, 'green': 0.9, 'blue': 0.7}
            })

            current_row += 1

            # Key metrics
            ws.update(f'A{current_row}', [[f"  Kavastu Score: {kavastu_score:.0f}/130 | Price: {price:.2f} SEK"]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})

            current_row += 1
            ws.update(f'A{current_row}', [[f"  {reason}"]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10, 'italic': True}})

            current_row += 1

            # Fetch news (top 3 articles)
            news_articles = fetch_stock_news(ticker, max_articles=3)

            ws.update(f'A{current_row}', [['  📰 Latest News:']])
            ws.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 10}})
            current_row += 1

            if news_articles:
                for article in news_articles[:3]:
                    emoji = get_market_sentiment_emoji(article['sentiment'])
                    title = article['title'][:60] + '...' if len(article['title']) > 60 else article['title']
                    ws.update(f'A{current_row}', [[f"    {emoji} {title}"]])
                    ws.format(f'A{current_row}', {'textFormat': {'fontSize': 9}})
                    current_row += 1
            else:
                ws.update(f'A{current_row}', [["    No recent news"]])
                ws.format(f'A{current_row}', {'textFormat': {'fontSize': 9, 'italic': True}})
                current_row += 1

            # Should you buy recommendation
            ws.update(f'A{current_row}', [['  💡 Should You Buy?']])
            ws.format(f'A{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 10},
                'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.9}
            })
            current_row += 1

            # Generate buy recommendation
            if trending_score >= 75 and kavastu_score >= 110:
                recommendation = f"    ✅ YES - Strong momentum, high Kavastu score ({kavastu_score:.0f})"
                if return_4w > 30:
                    warning = f"    ⚠️  Monitor: Already up {return_4w:.1f}%, watch for pullback"
                else:
                    warning = f"    🎯 Entry: Good entry point at current levels"
            elif trending_score >= 75 and kavastu_score < 110:
                recommendation = f"    ⚠️  MAYBE - Strong trending but lower score ({kavastu_score:.0f})"
                warning = f"    🎯 Wait: Monitor for Kavastu score to improve above 110"
            else:
                recommendation = f"    ℹ️  WATCH - Moderate momentum, not top priority"
                warning = f"    🎯 Better opportunities exist in higher-scored stocks"

            ws.update(f'A{current_row}', [[recommendation]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})
            current_row += 1

            ws.update(f'A{current_row}', [[warning]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})
            current_row += 1

            # Separator
            current_row += 1

        # ===== COLD STOCKS SECTION =====
        current_row += 2
        ws.update(f'A{current_row}', [['❄️  COLD STOCKS - DETAILED ANALYSIS (Top 5)']])
        ws.format(f'A{current_row}', {
            'textFormat': {'bold': True, 'fontSize': 14},
            'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1.0}
        })

        current_row += 2

        # Process each cold stock
        cold_stocks = trending_data.get('cold_stocks', [])[:5]
        for i, stock in enumerate(cold_stocks, 1):
            ticker = stock['ticker']
            name = stock['name']
            trending_score = stock['trending_score']
            kavastu_score = stock['kavastu_score']
            price = stock['price']
            return_4w = stock['return_4w']
            reason = stock['reason']

            # Stock header
            ws.update(f'A{current_row}', [[f"{i}. {ticker} - {name}"]])
            ws.update(f'G{current_row}', [[f"Score: {trending_score:.0f}/100"]])
            ws.format(f'A{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 12},
                'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
            })
            ws.format(f'G{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1.0}
            })

            current_row += 1

            # Key metrics
            ws.update(f'A{current_row}', [[f"  Kavastu Score: {kavastu_score:.0f}/130 | Price: {price:.2f} SEK"]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})

            current_row += 1
            ws.update(f'A{current_row}', [[f"  {reason}"]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10, 'italic': True}})

            current_row += 1

            # Fetch news
            news_articles = fetch_stock_news(ticker, max_articles=2)

            ws.update(f'A{current_row}', [['  📰 Latest News:']])
            ws.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 10}})
            current_row += 1

            if news_articles:
                for article in news_articles[:2]:
                    emoji = get_market_sentiment_emoji(article['sentiment'])
                    title = article['title'][:60] + '...' if len(article['title']) > 60 else article['title']
                    ws.update(f'A{current_row}', [[f"    {emoji} {title}"]])
                    ws.format(f'A{current_row}', {'textFormat': {'fontSize': 9}})
                    current_row += 1
            else:
                ws.update(f'A{current_row}', [["    No recent news"]])
                ws.format(f'A{current_row}', {'textFormat': {'fontSize': 9, 'italic': True}})
                current_row += 1

            # Should you sell recommendation
            ws.update(f'A{current_row}', [['  💡 Should You Sell (if owned)?']])
            ws.format(f'A{current_row}', {
                'textFormat': {'bold': True, 'fontSize': 10},
                'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.95}
            })
            current_row += 1

            # Generate sell recommendation
            if kavastu_score < 90:
                recommendation = f"    ❌ YES - Below 90 threshold (current: {kavastu_score:.0f})"
                action = f"    🎯 Action: Sell on next trading day"
            elif trending_score <= 25 and kavastu_score < 100:
                recommendation = f"    ⚠️  WATCH - Cold trend, marginal score ({kavastu_score:.0f})"
                action = f"    🎯 Action: Monitor closely, sell if score drops below 90"
            else:
                recommendation = f"    ℹ️  HOLD - Weak trend but acceptable score ({kavastu_score:.0f})"
                action = f"    🎯 Action: Keep for now, watch for improvement"

            ws.update(f'A{current_row}', [[recommendation]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})
            current_row += 1

            ws.update(f'A{current_row}', [[action]])
            ws.format(f'A{current_row}', {'textFormat': {'fontSize': 10}})
            current_row += 1

            # Separator
            current_row += 1

        # Footer note
        current_row += 2
        ws.update(f'A{current_row}', [['📝 Note: This is Layer 2 detailed analysis. For quick Sunday trading, use Executive Summary (Layer 1).']])
        ws.format(f'A{current_row}', {
            'textFormat': {'italic': True, 'fontSize': 9},
            'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 1.0}
        })

        print("✅ Trending Deep Dive sheet updated (Layer 2)")
        return True


def test_sheets_connection():
    """Test Google Sheets connection and authentication."""
    print("\n" + "=" * 80)
    print("GOOGLE SHEETS CONNECTION TEST")
    print("=" * 80)

    # Path to credentials
    creds_path = Path(__file__).parent.parent / "config" / "credentials" / "claude-mcp-484313-5647d3a2a087.json"

    if not creds_path.exists():
        print(f"❌ Credentials file not found: {creds_path}")
        return False

    # Initialize manager
    manager = SheetsManager(str(creds_path))

    # Test authentication
    if not manager.authenticate():
        return False

    print("✅ Google Sheets connection successful!")
    print("\nNext steps:")
    print("1. Create a new spreadsheet: manager.create_spreadsheet('Kavastu Portfolio Tracker')")
    print("2. Or open existing: manager.open_spreadsheet('Your Spreadsheet Name')")
    print("3. Update sheets with portfolio data")

    return True


if __name__ == "__main__":
    test_sheets_connection()
