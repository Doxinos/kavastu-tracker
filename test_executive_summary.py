#!/usr/bin/env python3
"""
Quick test for Executive Summary sheet integration.
Tests that the update_executive_summary method works with mock data.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.sheets_manager import SheetsManager
from datetime import datetime

# Configuration
CREDENTIALS_PATH = Path(__file__).parent / "config" / "credentials" / "claude-mcp-484313-5647d3a2a087.json"
TEST_SPREADSHEET = "Kavastu Portfolio Tracker"

# Mock data for testing
portfolio_metrics = {
    'total_value': 250000,
    'cash': 50000,
    'invested': 200000,
    'holdings_count': 15,
    'ytd_return': 15.5,
    'total_return': 28.3,
    '30d_return': 2.1,
    '7d_return': 0.5
}

market_context = {
    'articles': [
        {
            'title': 'Swedish stocks rally on strong earnings from Volvo and Ericsson',
            'sentiment': 'positive',
            'source': 'Di',
            'published': datetime.now()
        },
        {
            'title': 'Central bank holds rates steady as inflation moderates',
            'sentiment': 'neutral',
            'source': 'SvD',
            'published': datetime.now()
        },
        {
            'title': 'OMXS30 reaches new yearly high on tech sector strength',
            'sentiment': 'positive',
            'source': 'E24',
            'published': datetime.now()
        }
    ],
    'sentiment_summary': {
        'overall_sentiment': 'positive',
        'positive_count': 8,
        'negative_count': 2,
        'neutral_count': 5
    },
    'total_articles': 15
}

trending_data = {
    'hot_stocks': [
        {
            'ticker': 'CTM.ST',
            'name': 'Coloplast',
            'trending_score': 100,
            'kavastu_score': 125,
            'reason': '+36% return, volume +66%',
            'return_4w': 12.5
        },
        {
            'ticker': 'INDU-C.ST',
            'name': 'Industrivärden C',
            'trending_score': 95,
            'kavastu_score': 122,
            'reason': '+28% return, outperform +23%',
            'return_4w': 9.2
        },
        {
            'ticker': 'ATCO-A.ST',
            'name': 'Atlas Copco A',
            'trending_score': 92,
            'kavastu_score': 120,
            'reason': '+25% return, volume +45%',
            'return_4w': 8.8
        }
    ],
    'cold_stocks': [
        {
            'ticker': 'BOUL.ST',
            'name': 'Boulebar',
            'trending_score': 0,
            'kavastu_score': 65,
            'reason': '-16% return, underperform',
            'return_4w': -5.2
        },
        {
            'ticker': 'AAK.ST',
            'name': 'AAK',
            'trending_score': 5,
            'kavastu_score': 72,
            'reason': '-12% return, volume down',
            'return_4w': -3.8
        }
    ]
}

buy_list = [
    {
        'ticker': 'VOLV-B.ST',
        'score': 120,
        'price': 260.50,
        'shares': 95,
        'amount': 24747.50,
        'reason': 'Score 120 (top 70, not owned)'
    },
    {
        'ticker': 'ERIC-B.ST',
        'score': 115,
        'price': 110.00,
        'shares': 180,
        'amount': 19800.00,
        'reason': 'Score 115 (strong momentum)'
    },
    {
        'ticker': 'SAND.ST',
        'score': 112,
        'price': 240.90,
        'shares': 88,
        'amount': 21199.20,
        'reason': 'Score 112 (breakout)'
    }
]

sell_list = [
    {
        'ticker': 'OLD-A.ST',
        'score': 85,
        'current_value': 15000,
        'reason': 'Score dropped below 90'
    },
    {
        'ticker': 'WEAK.ST',
        'score': 78,
        'current_value': 12000,
        'reason': 'Dropped out of top 70'
    }
]

def main():
    print("\n" + "=" * 80)
    print("TESTING EXECUTIVE SUMMARY SHEET")
    print("=" * 80)

    # Initialize sheets manager
    manager = SheetsManager(str(CREDENTIALS_PATH))

    if not manager.authenticate():
        print("❌ Failed to authenticate with Google Sheets")
        return False

    if not manager.open_spreadsheet(TEST_SPREADSHEET):
        print(f"❌ Failed to open spreadsheet '{TEST_SPREADSHEET}'")
        return False

    # Test the update_executive_summary method
    print("\n📊 Testing update_executive_summary()...")
    try:
        result = manager.update_executive_summary(
            portfolio_metrics=portfolio_metrics,
            market_context=market_context,
            trending_data=trending_data,
            buy_list=buy_list,
            sell_list=sell_list
        )

        if result:
            print("\n✅ Executive Summary test PASSED!")
            print(f"\nView the sheet at: https://docs.google.com/spreadsheets/d/{manager.spreadsheet.id}")
            print("\nExpected sections:")
            print("  - Portfolio Value: 250,000 SEK (+15.5% YTD)")
            print("  - Market Mood: POSITIVE")
            print("  - Hot Stocks: CTM.ST, INDU-C.ST, ATCO-A.ST")
            print("  - Cold Stocks: BOUL.ST, AAK.ST")
            print("  - Buy Signals: 3 stocks")
            print("  - Sell Signals: 2 stocks")
            print("  - Execution checklist")
            return True
        else:
            print("\n❌ Executive Summary test FAILED")
            return False

    except Exception as e:
        print(f"\n❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
