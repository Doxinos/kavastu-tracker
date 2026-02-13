#!/usr/bin/env python3
"""
Analyze Fundamentals - Deep dive into company financials.

Usage:
  python analyze_fundamentals.py VOLV-B.ST              # Single stock
  python analyze_fundamentals.py VOLV-B.ST ERIC-B.ST   # Multiple stocks
  python analyze_fundamentals.py --portfolio            # All portfolio holdings
  python analyze_fundamentals.py --top10                # Top 10 from screener
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fundamentals_detailed import (
    fetch_detailed_fundamentals,
    format_detailed_fundamentals,
    compare_fundamentals
)
from src.portfolio_manager import Portfolio
from src.stock_universe import get_all_swedish_stocks
from src.screener import run_screen


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python analyze_fundamentals.py TICKER1 [TICKER2 ...]")
        print("  python analyze_fundamentals.py --portfolio")
        print("  python analyze_fundamentals.py --top10")
        return

    tickers = []

    # Handle special flags
    if '--portfolio' in sys.argv:
        print("📊 Analyzing portfolio holdings...\n")
        portfolio = Portfolio()
        tickers = portfolio.get_tickers()

        if not tickers:
            print("⚠️ No holdings found in portfolio")
            return

    elif '--top10' in sys.argv:
        print("📊 Analyzing top 10 stocks from screener...\n")
        all_stocks = get_all_swedish_stocks()
        results = run_screen(all_stocks, min_score=40, period='1y')

        if results.empty:
            print("⚠️ No stocks passed screening")
            return

        tickers = results.head(10)['ticker'].tolist()

    else:
        # Individual tickers provided
        tickers = [arg for arg in sys.argv[1:] if not arg.startswith('--')]

    print(f"Analyzing {len(tickers)} stocks: {', '.join(tickers)}\n")

    # If multiple stocks, show comparison table first
    if len(tickers) > 1:
        print("=" * 100)
        print("COMPARISON TABLE")
        print("=" * 100)
        comparison = compare_fundamentals(tickers)

        # Format percentages
        if 'Profit Margin' in comparison.columns:
            comparison['Profit Margin'] = comparison['Profit Margin'].apply(
                lambda x: f"{x*100:.1f}%" if x else "N/A"
            )
        if 'ROE' in comparison.columns:
            comparison['ROE'] = comparison['ROE'].apply(
                lambda x: f"{x*100:.1f}%" if x else "N/A"
            )
        if 'Revenue Growth' in comparison.columns:
            comparison['Revenue Growth'] = comparison['Revenue Growth'].apply(
                lambda x: f"{x*100:+.1f}%" if x else "N/A"
            )

        print(comparison.to_string(index=False))
        print()

    # Detailed analysis for each stock
    for ticker in tickers:
        fundamentals = fetch_detailed_fundamentals(ticker)
        print(format_detailed_fundamentals(fundamentals))
        print("\n")


if __name__ == "__main__":
    main()
