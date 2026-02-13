#!/usr/bin/env python3
"""
Quick test of the screener with 10 stocks
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stock_universe import get_all_swedish_stocks
from src.screener import run_screen, format_screening_results


def main():
    """Test with small sample."""
    print("🧪 Testing Kavastu Screener")
    print("=" * 60)

    # Get first 15 stocks for quick test
    all_stocks = get_all_swedish_stocks()
    test_stocks = all_stocks[:15]

    print(f"\n📊 Testing with {len(test_stocks)} stocks:")
    print(f"   {', '.join(test_stocks[:5])}...")

    # Run screening
    results = run_screen(test_stocks, min_score=30, period="6mo")

    if not results.empty:
        print(format_screening_results(results, top_n=10))
        print(f"\n✅ Test successful! {len(results)} stocks passed.")
    else:
        print("\n⚠️  No stocks passed (might need lower threshold)")


if __name__ == "__main__":
    main()
