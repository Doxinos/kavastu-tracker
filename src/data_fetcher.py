"""Data fetcher - Fetch Swedish stock data from yfinance."""
import yfinance as yf
import pandas as pd
import time
from typing import List, Dict, Optional
from datetime import datetime

# Rate limiting to avoid Yahoo Finance API throttling
RATE_LIMIT_DELAY = 0.15  # 150ms delay between requests (safe for backtesting)


def fetch_stock_data(ticker: str, period: str = "1y", delay: float = RATE_LIMIT_DELAY) -> Optional[pd.DataFrame]:
    """
    Fetch historical data for a Swedish stock.

    Args:
        ticker: Stock ticker with .ST suffix (e.g., 'VOLV-B.ST')
        period: Time period ('1y', '6mo', '3mo', etc.)
        delay: Delay in seconds after fetch to avoid rate limiting (default 0.15s)

    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume
        Returns None if data fetch fails
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        # Rate limiting delay
        if delay > 0:
            time.sleep(delay)

        if df.empty:
            print(f"⚠️  No data for {ticker}")
            return None

        return df

    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None


def fetch_current_price(ticker: str) -> Optional[float]:
    """
    Get current/latest closing price.

    Args:
        ticker: Stock ticker with .ST suffix

    Returns:
        Latest closing price, or None if unavailable
    """
    try:
        df = fetch_stock_data(ticker, period="5d")
        if df is not None and not df.empty:
            return float(df['Close'].iloc[-1])
        return None

    except Exception as e:
        print(f"❌ Error fetching price for {ticker}: {e}")
        return None


def fetch_portfolio_data(tickers: List[str], period: str = "1y", delay: float = RATE_LIMIT_DELAY) -> Dict[str, pd.DataFrame]:
    """
    Batch fetch data for all stocks in portfolio.

    Args:
        tickers: List of stock tickers
        period: Time period to fetch
        delay: Delay in seconds between requests (default 0.15s)

    Returns:
        Dict mapping ticker -> DataFrame
        Skips tickers that fail to fetch
    """
    results = {}
    total = len(tickers)

    print(f"📥 Fetching data for {total} stocks (rate limited: {delay}s delay)...")

    for i, ticker in enumerate(tickers, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{total} stocks...")

        df = fetch_stock_data(ticker, period, delay=delay)
        if df is not None:
            results[ticker] = df

    print(f"✅ Successfully fetched {len(results)}/{total} stocks")

    if len(results) < total:
        failed = total - len(results)
        print(f"⚠️  {failed} stocks failed to fetch")

    return results


def fetch_dividend_history(ticker: str, start_date: str, end_date: str, delay: float = RATE_LIMIT_DELAY) -> pd.Series:
    """
    Fetch dividend history for a stock within a date range.

    Args:
        ticker: Stock ticker with .ST suffix
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        delay: Delay in seconds after fetch (default 0.15s)

    Returns:
        pandas Series with dividend amounts indexed by date
        Returns empty Series if no dividends or error
    """
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends

        # Rate limiting delay
        if delay > 0:
            time.sleep(delay)

        if dividends.empty:
            return pd.Series(dtype=float)

        # Filter by date range
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        # Ensure timezone-aware comparison if needed
        if dividends.index.tz is not None:
            start = start.tz_localize(dividends.index.tz)
            end = end.tz_localize(dividends.index.tz)

        filtered = dividends[(dividends.index >= start) & (dividends.index <= end)]
        return filtered

    except Exception as e:
        # Silently return empty Series - many stocks don't pay dividends
        return pd.Series(dtype=float)


def fetch_dividend_data(tickers: List[str], start_date: str, end_date: str, delay: float = RATE_LIMIT_DELAY) -> Dict[str, pd.Series]:
    """
    Fetch dividend history for multiple stocks.

    Args:
        tickers: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        delay: Delay in seconds between requests (default 0.15s)

    Returns:
        Dict mapping ticker -> dividend Series
        Only includes tickers with dividends
    """
    results = {}

    for ticker in tickers:
        dividends = fetch_dividend_history(ticker, start_date, end_date, delay=delay)
        if not dividends.empty:
            results[ticker] = dividends

    return results


def fetch_benchmark_returns(benchmark_ticker: str = "^OMX") -> tuple:
    """
    Fetch OMXS30 index returns for relative strength calculation.

    Args:
        benchmark_ticker: Ticker for OMXS30 index

    Returns:
        Tuple of (return_3m, return_6m) as percentages
    """
    try:
        df = fetch_stock_data(benchmark_ticker, period="1y")

        if df is None or df.empty:
            print("⚠️  Using default benchmark returns (0%)")
            return (0.0, 0.0)

        # Calculate returns
        current_price = df['Close'].iloc[-1]

        # 3-month return
        if len(df) >= 60:  # ~3 months of trading days
            price_3m_ago = df['Close'].iloc[-60]
            return_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
        else:
            return_3m = 0.0

        # 6-month return
        if len(df) >= 120:  # ~6 months of trading days
            price_6m_ago = df['Close'].iloc[-120]
            return_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        else:
            return_6m = 0.0

        return (return_3m, return_6m)

    except Exception as e:
        print(f"❌ Error fetching benchmark: {e}")
        return (0.0, 0.0)


if __name__ == "__main__":
    # Test the module
    print("Testing data_fetcher.py...")

    # Test with a few Swedish stocks
    test_tickers = ['VOLV-B.ST', 'ERIC-B.ST', 'ABB.ST']

    print(f"\n📊 Testing individual stock fetch...")
    for ticker in test_tickers[:1]:  # Test just one
        df = fetch_stock_data(ticker, period="1mo")
        if df is not None:
            print(f"✅ {ticker}: {len(df)} days of data")
            print(f"   Latest price: {df['Close'].iloc[-1]:.2f}")
        else:
            print(f"❌ {ticker}: Failed to fetch")

    print(f"\n📊 Testing batch fetch...")
    data = fetch_portfolio_data(test_tickers, period="1mo")
    print(f"✅ Fetched {len(data)} stocks")

    print(f"\n📊 Testing benchmark returns...")
    ret_3m, ret_6m = fetch_benchmark_returns()
    print(f"✅ OMXS30 returns: 3M={ret_3m:.2f}%, 6M={ret_6m:.2f}%")
