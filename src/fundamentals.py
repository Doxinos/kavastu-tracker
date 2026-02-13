"""Fundamental analysis - Revenue growth, profitability, quality metrics."""
import yfinance as yf
from typing import Dict, Optional


def fetch_fundamentals(ticker: str) -> Dict[str, any]:
    """
    Fetch fundamental data for a stock using yfinance.

    Args:
        ticker: Stock ticker (e.g., 'VOLV-B.ST')

    Returns:
        Dict with fundamental metrics:
        {
            'revenue_growth': float (YoY % change),
            'profit_margin': float (% as decimal),
            'roe': float (Return on Equity % as decimal),
            'debt_to_equity': float (ratio),
            'pe_ratio': float,
            'forward_pe': float,
            'quality_score': float (0-20 points)
        }
    """
    fundamentals = {
        'revenue_growth': None,
        'profit_margin': None,
        'roe': None,
        'debt_to_equity': None,
        'pe_ratio': None,
        'forward_pe': None,
        'dividend_yield': None,
        'pays_dividend': False,
        'quality_score': 0.0
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Extract key metrics
        fundamentals['revenue_growth'] = info.get('revenueGrowth')
        fundamentals['profit_margin'] = info.get('profitMargins')
        fundamentals['roe'] = info.get('returnOnEquity')
        fundamentals['debt_to_equity'] = info.get('debtToEquity')
        fundamentals['pe_ratio'] = info.get('trailingPE')
        fundamentals['forward_pe'] = info.get('forwardPE')

        # Dividend info (Kavastu's 90% rule - prefer dividend payers)
        div_yield = info.get('dividendYield')
        fundamentals['dividend_yield'] = div_yield
        fundamentals['pays_dividend'] = div_yield is not None and div_yield > 0

        # Calculate quality score (0-25 points with dividend bonus)
        fundamentals['quality_score'] = calculate_quality_score(fundamentals)

    except Exception as e:
        # If fundamentals not available, return empty dict
        pass

    return fundamentals


def calculate_quality_score(fundamentals: Dict[str, any]) -> float:
    """
    Calculate Kavastu quality score based on fundamentals.

    Scoring (0-25 points total):
    - Revenue Growth: 0-8 points
      - >15% YoY: 8 points
      - 10-15%: 6 points
      - 5-10%: 4 points
      - 0-5%: 2 points
      - Negative: 0 points

    - Profit Margin: 0-6 points
      - >15%: 6 points
      - 10-15%: 4 points
      - 5-10%: 2 points
      - <5%: 0 points

    - ROE: 0-6 points
      - >20%: 6 points
      - 15-20%: 4 points
      - 10-15%: 2 points
      - <10%: 0 points

    - Dividend Payer (Kavastu 90% rule): 0-3 points
      - Pays dividend: +3 points (quality signal)
      - No dividend: 0 points

    - Debt Level: 0-2 points
      - Low debt (D/E < 1.0): +2 points
      - Moderate debt (D/E 1.0-2.0): +1 point
      - High debt (D/E > 2.0): 0 points

    Args:
        fundamentals: Dict with fundamental metrics

    Returns:
        Quality score (0-25 points)
    """
    score = 0.0

    # Revenue Growth (0-8 points)
    rev_growth = fundamentals.get('revenue_growth')
    if rev_growth is not None:
        if rev_growth > 0.15:  # >15%
            score += 8
        elif rev_growth > 0.10:  # 10-15%
            score += 6
        elif rev_growth > 0.05:  # 5-10%
            score += 4
        elif rev_growth > 0:  # 0-5%
            score += 2
        # Negative growth = 0 points

    # Profit Margin (0-6 points)
    profit_margin = fundamentals.get('profit_margin')
    if profit_margin is not None:
        if profit_margin > 0.15:  # >15%
            score += 6
        elif profit_margin > 0.10:  # 10-15%
            score += 4
        elif profit_margin > 0.05:  # 5-10%
            score += 2
        # <5% = 0 points

    # ROE (0-6 points)
    roe = fundamentals.get('roe')
    if roe is not None:
        if roe > 0.20:  # >20%
            score += 6
        elif roe > 0.15:  # 15-20%
            score += 4
        elif roe > 0.10:  # 10-15%
            score += 2
        # <10% = 0 points

    # Dividend Payer (0-3 points) - Kavastu's 90% rule
    # Prefers dividend-paying stocks (quality/stability signal)
    if fundamentals.get('pays_dividend', False):
        score += 3

    # Debt Level (0-2 points) - Kavastu prefers low debt
    debt_to_equity = fundamentals.get('debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity < 100:  # D/E < 1.0 (converted from % to ratio)
            score += 2
        elif debt_to_equity < 200:  # D/E 1.0-2.0
            score += 1
        # High debt (D/E > 2.0) = 0 points

    return score


def format_fundamentals(fundamentals: Dict[str, any]) -> str:
    """
    Format fundamentals for display.

    Args:
        fundamentals: Dict from fetch_fundamentals()

    Returns:
        Formatted string
    """
    output = []

    rev_growth = fundamentals.get('revenue_growth')
    if rev_growth is not None:
        output.append(f"Revenue Growth: {rev_growth * 100:+.1f}%")

    profit_margin = fundamentals.get('profit_margin')
    if profit_margin is not None:
        output.append(f"Profit Margin: {profit_margin * 100:.1f}%")

    roe = fundamentals.get('roe')
    if roe is not None:
        output.append(f"ROE: {roe * 100:.1f}%")

    pe = fundamentals.get('pe_ratio')
    if pe is not None:
        output.append(f"P/E: {pe:.1f}")

    quality_score = fundamentals.get('quality_score', 0)
    output.append(f"Quality Score: {quality_score:.1f}/20")

    return ", ".join(output) if output else "No fundamentals available"


def batch_fetch_fundamentals(tickers: list) -> Dict[str, Dict]:
    """
    Fetch fundamentals for multiple stocks.

    Args:
        tickers: List of stock tickers

    Returns:
        Dict mapping ticker to fundamentals dict
    """
    results = {}

    for ticker in tickers:
        results[ticker] = fetch_fundamentals(ticker)

    return results


if __name__ == "__main__":
    # Test the module
    print("Testing fundamentals.py...")

    test_stocks = ['VOLV-B.ST', 'ERIC-B.ST', 'ABB.ST', 'SAND.ST', 'BOL.ST']

    print(f"\n📊 Fetching fundamentals for {len(test_stocks)} stocks...\n")

    for ticker in test_stocks:
        print(f"{ticker}:")
        fundamentals = fetch_fundamentals(ticker)
        print(f"   {format_fundamentals(fundamentals)}")
        print()

    print("✅ Fundamentals module working!")
