"""Screener - Filter and rank stocks using Kavastu criteria."""
import pandas as pd
from typing import List, Tuple
from .data_fetcher import fetch_portfolio_data, fetch_benchmark_returns
from .ma_calculator import (calculate_ma50_ma200, calculate_ma200_slope, get_52_week_high,
                            detect_crossover, calculate_rsi, calculate_macd, detect_macd_crossover)
from .fundamentals import fetch_fundamentals


def calculate_stock_return(df: pd.DataFrame, days: int) -> float:
    """Calculate stock return over specified days."""
    if len(df) < days:
        return 0.0

    current_price = df['Close'].iloc[-1]
    past_price = df['Close'].iloc[-days]

    return ((current_price - past_price) / past_price) * 100


def calculate_stock_score(ticker: str, df: pd.DataFrame, benchmark_returns: Tuple[float, float],
                         include_fundamentals: bool = True,
                         use_indicator_confirmation: bool = False) -> dict:
    """
    Score stock from 0-150 based on Kavastu criteria (Phase 2: with indicators).

    Scoring breakdown:
    - Technical (45 pts): Price > MA200, Triple MA alignment, rising MA200
      - Price > MA200: 20 pts (required)
      - MA50 > MA100 > MA200: 15 pts (strong uptrend)
      - MA200 rising: 10 pts
    - Relative Strength (30 pts): Outperformance vs benchmark
    - Momentum (30 pts): Distance from MA200, near 52W high
    - Quality (25 pts): Revenue growth, profit margin, ROE, dividend, low debt
    - Indicator Confirmation (20 pts, Phase 2): RSI + MACD confirmation
      - RSI 50-60 (ideal): 10 pts
      - MACD bullish crossover: 10 pts
      - Penalties: RSI >70 (overbought), MACD bearish cross

    Args:
        ticker: Stock ticker
        df: DataFrame with price data and MAs (MA50, MA100, MA200)
        benchmark_returns: Tuple of (return_3m, return_6m) for index
        include_fundamentals: Whether to include fundamental scoring (default True)
        use_indicator_confirmation: Whether to include RSI/MACD scoring (Phase 2, default False)

    Returns:
        Dict with score and metrics
    """
    score = 0.0
    metrics = {
        'ticker': ticker,
        'score': 0.0,
        'price': 0.0,
        'ma50': 0.0,
        'ma100': 0.0,
        'ma200': 0.0,
        'distance_ma200': 0.0,
        'ma50_above_ma200': False,
        'triple_ma_aligned': False,
        'ma200_rising': False,
        'relative_strength_3m': 0.0,
        'relative_strength_6m': 0.0,
        'price_vs_52w_high': 0.0,
        '52w_high': 0.0,
        'death_cross': False,
        'days_since_death_cross': None,
        'revenue_growth': None,
        'profit_margin': None,
        'roe': None,
        'quality_score': 0.0
    }

    try:
        current_price = df['Close'].iloc[-1]
        ma50 = df['MA50'].iloc[-1]
        ma100 = df['MA100'].iloc[-1] if 'MA100' in df.columns else None
        ma200 = df['MA200'].iloc[-1]

        metrics['price'] = current_price
        metrics['ma50'] = ma50
        metrics['ma200'] = ma200
        if ma100 is not None:
            metrics['ma100'] = ma100

        # Check for NaN values
        if pd.isna(ma200):
            return metrics  # Not enough data for MA200

        # Technical filter (40 points)
        # 1. Price > MA200 (required - 20 points)
        if current_price > ma200:
            score += 20
            metrics['distance_ma200'] = ((current_price - ma200) / ma200) * 100
        else:
            # If not above MA200, score is very low
            metrics['distance_ma200'] = ((current_price - ma200) / ma200) * 100
            metrics['score'] = score
            return metrics

        # 2. Triple MA System - Enhanced trend strength detection (0-15 points)
        # MA50 > MA100 > MA200: Strong uptrend (15 points)
        # MA50 > MA200 (but not both): Medium uptrend (10 points)
        # Price > MA200 only: Weak uptrend (already got 20 points above)
        if not pd.isna(ma50):
            if ma100 is not None and not pd.isna(ma100):
                # Triple MA available
                if ma50 > ma100 and ma100 > ma200:
                    score += 15  # Strong uptrend confirmation
                    metrics['ma50_above_ma200'] = True
                    metrics['triple_ma_aligned'] = True
                elif ma50 > ma200:
                    score += 10  # Medium uptrend
                    metrics['ma50_above_ma200'] = True
                    metrics['triple_ma_aligned'] = False
            else:
                # Fallback to dual MA (backward compatible)
                if ma50 > ma200:
                    score += 10
                    metrics['ma50_above_ma200'] = True

        # 3. MA200 rising (10 points)
        slope = calculate_ma200_slope(df, lookback=20)
        if slope > 0:
            score += 10
            metrics['ma200_rising'] = True

        # Detect death cross (MA50 crosses below MA200)
        crossover_info = detect_crossover(df, lookback=7)

        # Penalty for death cross (MA50 crosses below MA200)
        if crossover_info['crossed_below_ma200']:
            score -= 20  # Reduce score significantly
            metrics['death_cross'] = True
            metrics['days_since_death_cross'] = crossover_info['days_since_crossover']

        # Relative strength (30 points)
        bench_3m, bench_6m = benchmark_returns

        # 3-month relative strength
        stock_return_3m = calculate_stock_return(df, 60)  # ~3 months
        rs_3m = stock_return_3m - bench_3m
        metrics['relative_strength_3m'] = rs_3m

        # Add up to 15 points for 3M RS
        rs_3m_points = min(15, max(0, rs_3m * 0.5))  # Scale: 30% RS = 15 points
        score += rs_3m_points

        # 6-month relative strength
        stock_return_6m = calculate_stock_return(df, 120)  # ~6 months
        rs_6m = stock_return_6m - bench_6m
        metrics['relative_strength_6m'] = rs_6m

        # Add up to 15 points for 6M RS
        rs_6m_points = min(15, max(0, rs_6m * 0.5))  # Scale: 30% RS = 15 points
        score += rs_6m_points

        # Momentum (30 points)
        # 1. Distance above MA200 (up to 15 points)
        distance_points = min(15, metrics['distance_ma200'] * 1.5)  # 10% above = 15 points
        score += distance_points

        # 2. Price vs 52-week high (up to 15 points)
        high_52w = get_52_week_high(df)
        if high_52w and high_52w > 0:
            price_vs_high = (current_price / high_52w)
            metrics['price_vs_52w_high'] = price_vs_high
            metrics['52w_high'] = high_52w

            # Closer to 52w high = higher score
            high_points = min(15, price_vs_high * 15)  # At 52w high = 15 points
            score += high_points

        # Quality - Fundamentals (25 points)
        if include_fundamentals:
            fundamentals = fetch_fundamentals(ticker)
            metrics['revenue_growth'] = fundamentals.get('revenue_growth')
            metrics['profit_margin'] = fundamentals.get('profit_margin')
            metrics['roe'] = fundamentals.get('roe')
            metrics['quality_score'] = fundamentals.get('quality_score', 0)
            score += fundamentals.get('quality_score', 0)

        # Phase 2: Indicator Confirmation (0-20 bonus points)
        if use_indicator_confirmation:
            # Calculate RSI if not present
            if 'RSI' not in df.columns:
                df['RSI'] = calculate_rsi(df, period=14)

            # Calculate MACD if not present
            if 'MACD' not in df.columns:
                macd, signal, hist = calculate_macd(df)
                df['MACD'] = macd
                df['MACD_Signal'] = signal
                df['MACD_Hist'] = hist

            current_rsi = df['RSI'].iloc[-1]

            # RSI Scoring (0-10 points)
            if not pd.isna(current_rsi):
                metrics['rsi'] = current_rsi

                if 50 <= current_rsi <= 60:
                    # Ideal zone: strong but not overbought
                    score += 10
                elif 60 < current_rsi <= 70:
                    # Good zone: bullish momentum
                    score += 7
                elif 40 <= current_rsi < 50:
                    # Neutral zone
                    score += 5
                elif current_rsi > 70:
                    # Overbought penalty
                    score -= 5
                    metrics['rsi_overbought'] = True

            # MACD Scoring (0-10 points)
            macd_info = detect_macd_crossover(df, lookback=5)
            metrics.update(macd_info)

            if macd_info['bullish_crossover']:
                # Just crossed above signal line - strong buy signal
                score += 10
            elif macd_info['macd_positive'] and macd_info['histogram_rising']:
                # MACD positive and momentum increasing
                score += 7
            elif macd_info['macd_positive']:
                # MACD above zero line
                score += 4

            if macd_info['bearish_crossover']:
                # Just crossed below signal line - sell warning
                score -= 10
                metrics['macd_bearish_cross'] = True

        metrics['score'] = round(score, 1)

    except Exception as e:
        print(f"⚠️  Error scoring {ticker}: {e}")

    return metrics


def run_screen(stocks: List[str], min_score: float = 50, period: str = "1y") -> pd.DataFrame:
    """
    Screen all Swedish stocks and return ranked list.

    Args:
        stocks: List of stock tickers to screen
        min_score: Minimum score to pass (default 50)
        period: Historical period to fetch

    Returns:
        DataFrame with ranked stocks and metrics
    """
    print(f"\n🔍 Kavastu Stock Screener")
    print(f"{'=' * 50}")
    print(f"Screening {len(stocks)} stocks with min score {min_score}")

    # Fetch benchmark returns
    print(f"\n📊 Fetching benchmark (OMXS30) returns...")
    benchmark_returns = fetch_benchmark_returns()
    print(f"   3M return: {benchmark_returns[0]:.2f}%")
    print(f"   6M return: {benchmark_returns[1]:.2f}%")

    # Fetch all stock data
    print(f"\n📥 Fetching stock data...")
    stock_data = fetch_portfolio_data(stocks, period=period)

    # Score all stocks
    print(f"\n📊 Scoring stocks...")
    results = []

    for ticker, df in stock_data.items():
        # Add MAs
        df = calculate_ma50_ma200(df)

        # Score the stock
        metrics = calculate_stock_score(ticker, df, benchmark_returns)

        if metrics['score'] > 0:  # Only include stocks with some score
            results.append(metrics)

    # Convert to DataFrame
    df_results = pd.DataFrame(results)

    if df_results.empty:
        print(f"\n⚠️  No stocks passed the screen")
        return df_results

    # Filter by minimum score
    df_results = df_results[df_results['score'] >= min_score]

    # Sort by score descending
    df_results = df_results.sort_values('score', ascending=False).reset_index(drop=True)

    print(f"\n✅ {len(df_results)} stocks passed the screen (score >= {min_score})")

    return df_results


def format_screening_results(df: pd.DataFrame, top_n: int = 10) -> str:
    """
    Format screening results for display.

    Args:
        df: DataFrame from run_screen()
        top_n: Number of top stocks to show

    Returns:
        Formatted string
    """
    if df.empty:
        return "No stocks passed the screen"

    # Check if we have quality scores
    has_quality = 'quality_score' in df.columns and df['quality_score'].notna().any()

    output = []
    if has_quality:
        output.append(f"\n{'=' * 108}")
        output.append(f"Top {min(top_n, len(df))} Stocks by Kavastu Score (Max: 125pts)")
        output.append(f"{'=' * 108}")
        output.append(f"{'Rank':<6}{'Ticker':<15}{'Score':<8}{'Price':<10}{'vs MA200':<12}{'Quality':<10}{'Death Cross':<15}")
        output.append(f"{'-' * 108}")
    else:
        output.append(f"\n{'=' * 90}")
        output.append(f"Top {min(top_n, len(df))} Stocks by Kavastu Score")
        output.append(f"{'=' * 90}")
        output.append(f"{'Rank':<6}{'Ticker':<15}{'Score':<8}{'Price':<10}{'vs MA200':<12}{'Death Cross':<15}{'RS 3M':<10}")
        output.append(f"{'-' * 90}")

    for idx, row in df.head(top_n).iterrows():
        # Death cross indicator
        if row.get('death_cross', False):
            days_ago = row.get('days_since_death_cross', 0)
            death_indicator = f"✓ ({days_ago}d ago)" if days_ago else "✓"
        else:
            death_indicator = "✗"

        if has_quality:
            quality_score = row.get('quality_score', 0)
            output.append(
                f"{idx+1:<6}{row['ticker']:<15}{row['score']:<8.1f}{row['price']:<10.2f}"
                f"{row['distance_ma200']:>+10.2f}%  {quality_score:<10.1f}{death_indicator:<15}"
            )
        else:
            output.append(
                f"{idx+1:<6}{row['ticker']:<15}{row['score']:<8.1f}{row['price']:<10.2f}"
                f"{row['distance_ma200']:>+10.2f}%  {death_indicator:<15}{row['relative_strength_3m']:>+8.2f}%"
            )

    return "\n".join(output)


if __name__ == "__main__":
    # Test the module
    print("Testing screener.py...")

    import sys
    sys.path.append('..')
    from src.stock_universe import get_all_swedish_stocks

    # Test with small sample
    all_stocks = get_all_swedish_stocks()
    test_stocks = all_stocks[:10]  # First 10 stocks

    print(f"\n📊 Testing screener with {len(test_stocks)} stocks...")

    results = run_screen(test_stocks, min_score=30)  # Lower threshold for testing

    if not results.empty:
        print(format_screening_results(results, top_n=5))
    else:
        print("❌ No results")
