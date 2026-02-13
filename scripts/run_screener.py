#!/usr/bin/env python3
"""
Run Kavastu Stock Screener
Scans all Swedish stocks and outputs top 60-80 by score.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stock_universe import get_all_swedish_stocks
from src.screener import run_screen, format_screening_results
from src.market_regime import (
    get_market_regime,
    calculate_watchlist_health,
    get_position_sizing_recommendation
)


def main():
    """Run the screener."""
    print("🔍 Kavastu Stock Screener")
    print("=" * 80)

    try:
        # Get all Swedish stocks
        all_stocks = get_all_swedish_stocks()
        print(f"\n📊 Loaded {len(all_stocks)} Swedish stocks from universe")

        # Run screening (lower threshold for testing)
        print("\n⚙️  Running screening with Kavastu criteria...")
        print("   - Technical: Price > MA200, MA50 > MA200, rising MA200")
        print("   - Relative Strength: vs OMXS30 index")
        print("   - Momentum: Distance from MA200, near 52W high")

        results = run_screen(all_stocks, min_score=40, period="1y")

        if results.empty:
            print("\n⚠️  No stocks passed the screen")
            return

        # Display results
        print(format_screening_results(results, top_n=20))

        # Market Regime Analysis
        print("\n" + "=" * 80)
        print("MARKET REGIME ANALYSIS")
        print("=" * 80)

        regime_info = get_market_regime()

        if regime_info['regime'] != 'unknown':
            print(f"\n📊 OMXS30 Index:")
            print(f"   Current: {regime_info['index_price']:.2f}")
            print(f"   MA200: {regime_info['index_ma200']:.2f}")
            print(f"   Distance: {regime_info['index_vs_ma200']:+.2f}%")
            print(f"\n🎯 Market Regime: {regime_info['regime'].upper()}")

            watchlist_health = calculate_watchlist_health(results)
            print(f"\n📈 Watchlist Health: {watchlist_health:.1f}% above MA200")

            position_rec = get_position_sizing_recommendation(
                regime_info['regime'],
                watchlist_health
            )
            print(f"\n💰 POSITION SIZING RECOMMENDATION:")
            print(f"   Target Holdings: {position_rec['target_stocks']} stocks")
            print(f"   Target Cash: {position_rec['target_cash_pct']}")
            print(f"   Reasoning: {position_rec['reasoning']}")
            print(f"\n{regime_info['recommendation']}")
        else:
            print(f"\n⚠️ {regime_info['recommendation']}")

        # Save top 80 to watchlist
        top_80 = results.head(80)
        watchlist_path = Path(__file__).parent.parent / "config" / "watchlist.csv"
        top_80.to_csv(watchlist_path, index=False)
        print(f"\n✅ Saved top {len(top_80)} stocks to watchlist: {watchlist_path}")

        print(f"\n💡 Next steps:")
        print(f"   1. Review the watchlist in config/watchlist.csv")
        print(f"   2. Add your active holdings to track")
        print(f"   3. Run weekly_check.py for buy/sell signals")

    except Exception as e:
        print(f"\n❌ Error running screener: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
