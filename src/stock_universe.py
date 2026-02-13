"""Stock universe management - Get all Swedish stocks from CSV."""
import pandas as pd
from typing import List, Dict
from pathlib import Path


def get_all_swedish_stocks(config_path: str = "config/swedish_stocks.csv") -> List[str]:
    """
    Return list of all Swedish stock tickers with .ST suffix.

    Args:
        config_path: Path to swedish_stocks.csv file

    Returns:
        List of ticker symbols (e.g., ['VOLV-B.ST', 'ERIC-B.ST', ...])
    """
    csv_path = Path(__file__).parent.parent / config_path

    if not csv_path.exists():
        raise FileNotFoundError(f"Stock universe file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    if 'Ticker' not in df.columns:
        raise ValueError("CSV must have a 'Ticker' column")

    return df['Ticker'].tolist()


def get_stock_info(config_path: str = "config/swedish_stocks.csv") -> pd.DataFrame:
    """
    Get full stock information including name, sector, market cap.

    Args:
        config_path: Path to swedish_stocks.csv file

    Returns:
        DataFrame with columns: Ticker, Name, Sector, MarketCap, LastUpdated
    """
    csv_path = Path(__file__).parent.parent / config_path

    if not csv_path.exists():
        raise FileNotFoundError(f"Stock universe file not found: {csv_path}")

    return pd.read_csv(csv_path)


def categorize_by_market_cap(config_path: str = "config/swedish_stocks.csv") -> Dict[str, List[str]]:
    """
    Group stocks by Large/Mid/Small cap.

    Args:
        config_path: Path to swedish_stocks.csv file

    Returns:
        Dict mapping market cap to list of tickers:
        {'large': ['VOLV-B.ST', ...], 'mid': [...], 'small': [...]}
    """
    df = get_stock_info(config_path)

    result = {
        'large': [],
        'mid': [],
        'small': []
    }

    for _, row in df.iterrows():
        market_cap = row['MarketCap'].lower()
        ticker = row['Ticker']

        if market_cap in result:
            result[market_cap].append(ticker)

    return result


if __name__ == "__main__":
    # Test the module
    print("Testing stock_universe.py...")

    try:
        all_stocks = get_all_swedish_stocks()
        print(f"✅ Loaded {len(all_stocks)} Swedish stocks")
        print(f"First 5: {all_stocks[:5]}")

        by_cap = categorize_by_market_cap()
        print(f"\n📊 Market cap breakdown:")
        print(f"  Large cap: {len(by_cap['large'])} stocks")
        print(f"  Mid cap: {len(by_cap['mid'])} stocks")
        print(f"  Small cap: {len(by_cap['small'])} stocks")

    except Exception as e:
        print(f"❌ Error: {e}")
