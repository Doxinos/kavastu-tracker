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

            # Share with your email (update this with your actual email)
            # self.spreadsheet.share('your.email@example.com', perm_type='user', role='writer')

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
        Update Sheet 4: Trade Recommendations with buy/sell signals.

        Args:
            buy_list: List of dicts with ticker, score, price, shares, amount
            sell_list: List of dicts with ticker, score, current_value, reason
        """
        ws = self.get_worksheet("Trade Recommendations")
        if not ws:
            return False

        try:
            # Clear existing data
            ws.clear()

            # Header
            ws.update('A1', [[f"Trade Recommendations - {datetime.now().strftime('%Y-%m-%d')}"]])
            ws.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})

            # BUY section
            row = 3
            ws.update(f'A{row}', [['🟢 BUY SIGNALS']])
            ws.format(f'A{row}', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.7, 'green': 1.0, 'blue': 0.7}
            })

            buy_headers = ['Ticker', 'Score', 'Price (SEK)', 'Shares', 'Amount (SEK)', 'Reason']
            ws.update(f'A{row+1}', [buy_headers])

            if buy_list:
                buy_data = []
                for b in buy_list:
                    buy_data.append([
                        b.get('ticker', ''),
                        b.get('score', 0),
                        f"{b.get('price', 0):.2f}",
                        b.get('shares', 0),
                        f"{b.get('amount', 0):.2f}",
                        b.get('reason', 'New buy signal')
                    ])
                ws.update(f'A{row+2}', buy_data)

            # SELL section
            sell_row = row + len(buy_list) + 4
            ws.update(f'A{sell_row}', [['🔴 SELL SIGNALS']])
            ws.format(f'A{sell_row}', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 1.0, 'green': 0.7, 'blue': 0.7}
            })

            sell_headers = ['Ticker', 'Score', 'Current Value', 'Reason']
            ws.update(f'A{sell_row+1}', [sell_headers])

            if sell_list:
                sell_data = []
                for s in sell_list:
                    sell_data.append([
                        s.get('ticker', ''),
                        s.get('score', 0),
                        f"{s.get('current_value', 0):.2f}",
                        s.get('reason', 'Score dropped below 90')
                    ])
                ws.update(f'A{sell_row+2}', sell_data)

            print(f"✅ Updated Trade Recommendations ({len(buy_list)} buys, {len(sell_list)} sells)")
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
