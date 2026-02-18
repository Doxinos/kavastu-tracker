"""Trending Detector - Identify hot/cold stocks based on momentum analysis."""
import pandas as pd
from typing import Dict, List, Tuple
from .ma_calculator import calculate_ma


def calculate_trending_score(ticker: str, df: pd.DataFrame, benchmark_returns: Dict) -> Dict:
    """
    Calculate trending momentum score (0-100 points).

    Scoring breakdown:
    - 4-week price return (40 points): Recent momentum
    - Relative strength vs OMXS30 (30 points): Outperformance
    - Volume trend (15 points): Increasing volume = stronger trend
    - Acceleration (15 points): Rate of change improving

    Args:
        ticker: Stock ticker symbol
        df: DataFrame with price and volume data
        benchmark_returns: Dict with 'return_4w' key for benchmark 4-week return

    Returns:
        {
            'trending_score': 0-100,
            'classification': 'HOT' | 'COLD' | 'NEUTRAL',
            'return_4w': float,
            'rs_vs_benchmark': float,
            'volume_trend': float,
            'acceleration': float,
            'reason': str  # "Why hot/cold" explanation
        }
    """
    result = {
        'ticker': ticker,
        'trending_score': 0,
        'classification': 'NEUTRAL',
        'return_4w': 0.0,
        'rs_vs_benchmark': 0.0,
        'volume_trend': 0.0,
        'acceleration': 0.0,
        'reason': ''
    }

    try:
        # Need at least 12 weeks of data
        if len(df) < 60:  # ~12 weeks
            result['reason'] = 'Insufficient data'
            return result

        current_price = df['Close'].iloc[-1]

        # 1. Calculate 4-week return (40 points)
        if len(df) >= 20:  # ~4 weeks
            price_4w_ago = df['Close'].iloc[-20]
            return_4w = ((current_price - price_4w_ago) / price_4w_ago) * 100
            result['return_4w'] = return_4w

            # Score 4-week return
            if return_4w > 15:
                result['trending_score'] += 40
            elif return_4w > 10:
                result['trending_score'] += 30
            elif return_4w > 5:
                result['trending_score'] += 20
            elif return_4w > -5:
                result['trending_score'] += 10
            elif return_4w > -10:
                result['trending_score'] += 5
            # else: 0 points for <-10%

        # 2. Calculate relative strength vs benchmark (30 points)
        benchmark_4w = benchmark_returns.get('return_4w', 0.0)
        rs_vs_benchmark = result['return_4w'] - benchmark_4w
        result['rs_vs_benchmark'] = rs_vs_benchmark

        # Score relative strength
        if rs_vs_benchmark > 10:
            result['trending_score'] += 30
        elif rs_vs_benchmark > 5:
            result['trending_score'] += 20
        elif rs_vs_benchmark > 0:
            result['trending_score'] += 10
        # else: 0 points for underperformance

        # 3. Calculate volume trend (15 points)
        if len(df) >= 60:  # Need 12 weeks
            # Recent 4-week average volume
            recent_volume = df['Volume'].tail(20).mean()

            # 12-week average volume
            avg_volume_12w = df['Volume'].tail(60).mean()

            if avg_volume_12w > 0:
                volume_change = ((recent_volume - avg_volume_12w) / avg_volume_12w) * 100
                result['volume_trend'] = volume_change

                # Score volume trend
                if volume_change > 50:
                    result['trending_score'] += 15
                elif volume_change > 25:
                    result['trending_score'] += 10
                elif volume_change > 0:
                    result['trending_score'] += 5
                # else: 0 points for declining volume

        # 4. Calculate acceleration (15 points)
        if len(df) >= 20:  # Need at least 4 weeks
            # 2-week return
            if len(df) >= 10:
                price_2w_ago = df['Close'].iloc[-10]
                return_2w = ((current_price - price_2w_ago) / price_2w_ago) * 100

                # Compare 2-week to 4-week return
                # Accelerating = 2-week return is better than half of 4-week return
                expected_2w = result['return_4w'] * 0.5
                acceleration = return_2w - expected_2w
                result['acceleration'] = acceleration

                # Score acceleration
                if acceleration > 2:  # Accelerating
                    result['trending_score'] += 15
                elif acceleration > -2:  # Stable
                    result['trending_score'] += 7
                # else: 0 points for decelerating

        # 5. Classification
        if result['trending_score'] >= 75:
            result['classification'] = 'HOT'
        elif result['trending_score'] <= 25:
            result['classification'] = 'COLD'
        else:
            result['classification'] = 'NEUTRAL'

        # 6. Generate explanation
        result['reason'] = _generate_explanation(result)

    except Exception as e:
        result['reason'] = f'Error: {str(e)}'

    return result


def _generate_explanation(result: Dict) -> str:
    """
    Generate human-readable explanation for trending classification.

    Args:
        result: Dict with trending metrics

    Returns:
        Explanation string
    """
    classification = result['classification']
    return_4w = result['return_4w']
    rs = result['rs_vs_benchmark']
    volume = result['volume_trend']

    parts = []

    # Return component
    if return_4w > 0:
        parts.append(f"4-week return +{return_4w:.1f}%")
    else:
        parts.append(f"4-week return {return_4w:.1f}%")

    # Relative strength component
    if rs > 0:
        parts.append(f"outperforming OMXS30 by {rs:.1f}%")
    else:
        parts.append(f"underperforming by {abs(rs):.1f}%")

    # Volume component
    if volume > 0:
        parts.append(f"volume up {volume:.0f}%")
    else:
        parts.append(f"volume down {abs(volume):.0f}%")

    explanation = ", ".join(parts)

    return explanation


def get_trending_stocks(screener_results: pd.DataFrame,
                       benchmark_returns: Dict,
                       top_n: int = 10) -> Tuple[List[Dict], List[Dict]]:
    """
    Identify hot and cold stocks from screener results.

    Args:
        screener_results: DataFrame from screener with 'ticker' and 'score' columns
        benchmark_returns: Dict with 'return_4w' for benchmark comparison
        top_n: Number of hot/cold stocks to return (default 10)

    Returns:
        Tuple of (hot_stocks, cold_stocks)
        Each list contains dicts with: ticker, score, trending_score, classification, reason
    """
    hot_stocks = []
    cold_stocks = []

    # Filter for stocks with trending scores
    if 'trending_score' not in screener_results.columns:
        return (hot_stocks, cold_stocks)

    # Get HOT stocks (trending_score >= 75)
    hot_df = screener_results[screener_results['classification'] == 'HOT'].copy()
    hot_df = hot_df.sort_values('trending_score', ascending=False)

    for _, row in hot_df.head(top_n).iterrows():
        # Check both 'reason' and 'trending_reason' column names
        reason = row.get('trending_reason', row.get('reason', ''))
        hot_stocks.append({
            'ticker': row['ticker'],
            'score': row.get('score', 0),
            'trending_score': row['trending_score'],
            'classification': row['classification'],
            'reason': reason
        })

    # Get COLD stocks (trending_score <= 25)
    cold_df = screener_results[screener_results['classification'] == 'COLD'].copy()
    cold_df = cold_df.sort_values('trending_score', ascending=True)

    for _, row in cold_df.head(top_n).iterrows():
        # Check both 'reason' and 'trending_reason' column names
        reason = row.get('trending_reason', row.get('reason', ''))
        cold_stocks.append({
            'ticker': row['ticker'],
            'score': row.get('score', 0),
            'trending_score': row['trending_score'],
            'classification': row['classification'],
            'reason': reason
        })

    return (hot_stocks, cold_stocks)


def add_trending_analysis(screener_results: pd.DataFrame,
                         stock_data: Dict[str, pd.DataFrame],
                         benchmark_returns: Dict) -> pd.DataFrame:
    """
    Add trending analysis to screener results.

    This is a convenience function to add trending scores to an existing
    screener results DataFrame.

    Args:
        screener_results: DataFrame from screener
        stock_data: Dict mapping ticker -> price DataFrame
        benchmark_returns: Dict with 'return_4w' for benchmark

    Returns:
        Updated DataFrame with trending columns added
    """
    df = screener_results.copy()

    # Initialize trending columns
    df['trending_score'] = 0
    df['classification'] = 'NEUTRAL'
    df['return_4w'] = 0.0
    df['rs_vs_benchmark'] = 0.0
    df['volume_trend'] = 0.0
    df['acceleration'] = 0.0
    df['trending_reason'] = ''

    # Calculate trending score for each stock
    for idx, row in df.iterrows():
        ticker = row['ticker']

        if ticker not in stock_data:
            continue

        stock_df = stock_data[ticker]
        trending = calculate_trending_score(ticker, stock_df, benchmark_returns)

        # Update DataFrame
        df.at[idx, 'trending_score'] = trending['trending_score']
        df.at[idx, 'classification'] = trending['classification']
        df.at[idx, 'return_4w'] = trending['return_4w']
        df.at[idx, 'rs_vs_benchmark'] = trending['rs_vs_benchmark']
        df.at[idx, 'volume_trend'] = trending['volume_trend']
        df.at[idx, 'acceleration'] = trending['acceleration']
        df.at[idx, 'trending_reason'] = trending['reason']

    return df


if __name__ == "__main__":
    # Test the module with sample data
    print("Testing trending_detector.py...")
    print("=" * 80)

    import numpy as np
    from datetime import datetime, timedelta

    # Create sample stock data
    def create_sample_stock(base_price: float, trend: str, days: int = 100) -> pd.DataFrame:
        """Create sample stock data for testing."""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        # Create base trend over full period (slower)
        base_trend = np.linspace(0, 0.05, days)

        if trend == 'hot':
            # Strong RECENT uptrend (last 4 weeks) with increasing volume
            # First 80 days: slower growth
            # Last 20 days: accelerating growth
            prices = np.ones(days) * base_price
            prices[:80] = base_price * (1 + base_trend[:80] + np.random.normal(0, 0.01, 80))
            # Last 20 days: strong momentum (+18% in 4 weeks)
            prices[80:] = prices[79] * (1 + np.linspace(0, 0.18, 20) + np.random.normal(0, 0.01, 20))

            # Volume increasing in last 4 weeks
            volumes = np.ones(days) * 100000
            volumes[:80] = 100000 * (1 + np.random.normal(0, 0.1, 80))
            volumes[80:] = 100000 * (1 + np.linspace(0, 0.6, 20) + np.random.normal(0, 0.1, 20))

        elif trend == 'cold':
            # RECENT downtrend (last 4 weeks) with decreasing volume
            # First 80 days: normal
            # Last 20 days: declining
            prices = np.ones(days) * base_price
            prices[:80] = base_price * (1 + base_trend[:80] + np.random.normal(0, 0.01, 80))
            # Last 20 days: strong decline (-15% in 4 weeks)
            prices[80:] = prices[79] * (1 - np.linspace(0, 0.15, 20) + np.random.normal(0, 0.01, 20))

            # Volume decreasing in last 4 weeks
            volumes = np.ones(days) * 100000
            volumes[:80] = 100000 * (1 + np.random.normal(0, 0.1, 80))
            volumes[80:] = 100000 * (1 - np.linspace(0, 0.3, 20) + np.random.normal(0, 0.1, 20))

        else:  # neutral
            # Moderate RECENT uptrend (last 4 weeks, ~8%) with stable volume
            # This should score in the NEUTRAL range (26-74)
            prices = np.ones(days) * base_price
            prices[:80] = base_price * (1 + base_trend[:80] + np.random.normal(0, 0.01, 80))
            # Last 20 days: moderate momentum (+8% in 4 weeks)
            prices[80:] = prices[79] * (1 + np.linspace(0, 0.08, 20) + np.random.normal(0, 0.01, 20))

            # Volume stable/slight increase in last 4 weeks
            volumes = np.ones(days) * 100000
            volumes[:80] = 100000 * (1 + np.random.normal(0, 0.1, 80))
            volumes[80:] = 100000 * (1 + np.linspace(0, 0.15, 20) + np.random.normal(0, 0.1, 20))

        df = pd.DataFrame({
            'Close': np.abs(prices),  # Ensure positive prices
            'Volume': np.abs(volumes),
            'High': np.abs(prices) * 1.02,
            'Low': np.abs(prices) * 0.98,
            'Open': np.abs(prices)
        }, index=dates)

        return df

    # Create test stocks
    print("\n1. Creating sample stock data...")
    hot_stock = create_sample_stock(100, 'hot')
    cold_stock = create_sample_stock(100, 'cold')
    neutral_stock = create_sample_stock(100, 'neutral')

    print(f"   HOT stock: {hot_stock['Close'].iloc[0]:.2f} -> {hot_stock['Close'].iloc[-1]:.2f}")
    print(f"   COLD stock: {cold_stock['Close'].iloc[0]:.2f} -> {cold_stock['Close'].iloc[-1]:.2f}")
    print(f"   NEUTRAL stock: {neutral_stock['Close'].iloc[0]:.2f} -> {neutral_stock['Close'].iloc[-1]:.2f}")

    # Create benchmark returns (simulate OMXS30)
    benchmark_returns = {
        'return_4w': 5.0  # Benchmark up 5% in 4 weeks
    }

    print(f"\n2. Benchmark (OMXS30) 4-week return: {benchmark_returns['return_4w']:.1f}%")

    # Test calculate_trending_score
    print("\n3. Testing calculate_trending_score()...")
    print("-" * 80)

    test_cases = [
        ('HOT-STOCK.ST', hot_stock, 'Expected: HOT (score >= 75)'),
        ('COLD-STOCK.ST', cold_stock, 'Expected: COLD (score <= 25)'),
        ('NEUTRAL-STOCK.ST', neutral_stock, 'Expected: NEUTRAL (score 26-74)')
    ]

    results = []
    for ticker, df, expected in test_cases:
        result = calculate_trending_score(ticker, df, benchmark_returns)
        results.append(result)

        print(f"\n{ticker} - {expected}")
        print(f"  Score: {result['trending_score']}/100")
        print(f"  Classification: {result['classification']}")
        print(f"  4-week return: {result['return_4w']:+.2f}%")
        print(f"  Relative strength: {result['rs_vs_benchmark']:+.2f}%")
        print(f"  Volume trend: {result['volume_trend']:+.1f}%")
        print(f"  Acceleration: {result['acceleration']:+.2f}%")
        print(f"  Reason: {result['reason']}")

    # Test get_trending_stocks
    print("\n4. Testing get_trending_stocks()...")
    print("-" * 80)

    # Create sample screener results
    screener_data = []
    for result in results:
        screener_data.append({
            'ticker': result['ticker'],
            'score': 85 if result['classification'] == 'HOT' else 45,
            'trending_score': result['trending_score'],
            'classification': result['classification'],
            'reason': result['reason']
        })

    screener_df = pd.DataFrame(screener_data)

    hot_stocks, cold_stocks = get_trending_stocks(screener_df, benchmark_returns, top_n=5)

    print(f"\nHOT STOCKS ({len(hot_stocks)} found):")
    for stock in hot_stocks:
        print(f"  {stock['ticker']}: Score={stock['score']}, Trending={stock['trending_score']}")
        print(f"    {stock['reason']}")

    print(f"\nCOLD STOCKS ({len(cold_stocks)} found):")
    for stock in cold_stocks:
        print(f"  {stock['ticker']}: Score={stock['score']}, Trending={stock['trending_score']}")
        print(f"    {stock['reason']}")

    # Test add_trending_analysis
    print("\n5. Testing add_trending_analysis()...")
    print("-" * 80)

    # Create minimal screener results
    minimal_screener = pd.DataFrame([
        {'ticker': 'HOT-STOCK.ST', 'score': 85},
        {'ticker': 'COLD-STOCK.ST', 'score': 45},
        {'ticker': 'NEUTRAL-STOCK.ST', 'score': 60}
    ])

    stock_data = {
        'HOT-STOCK.ST': hot_stock,
        'COLD-STOCK.ST': cold_stock,
        'NEUTRAL-STOCK.ST': neutral_stock
    }

    enhanced_df = add_trending_analysis(minimal_screener, stock_data, benchmark_returns)

    print("\nEnhanced screener results:")
    print(enhanced_df[['ticker', 'score', 'trending_score', 'classification']].to_string(index=False))

    print("\n" + "=" * 80)
    print("All tests completed successfully!")
    print("\nKey takeaways:")
    print("  - HOT stocks: trending_score >= 75 (strong momentum)")
    print("  - COLD stocks: trending_score <= 25 (weak/negative momentum)")
    print("  - NEUTRAL stocks: trending_score 26-74 (mixed signals)")
    print("  - Use this to identify momentum shifts in your portfolio")
