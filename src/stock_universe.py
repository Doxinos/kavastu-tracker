"""Stock universe management - Get all Nordic stocks from CSV."""
import re
import pandas as pd
from typing import List, Dict
from pathlib import Path

# Share class preference: when a company has multiple share classes,
# keep the most liquid one. In Sweden: B > C > A.
_SHARE_CLASS_PRIORITY = {'B': 0, 'C': 1, 'A': 2}

# Supported exchange suffixes
_EXCHANGE_SUFFIXES = r'\.(ST|OL|CO)'


def _dedup_share_classes(tickers: List[str]) -> List[str]:
    """
    Remove duplicate share classes for the same company.
    E.g. VOLV-A.ST + VOLV-B.ST → keep VOLV-B.ST (B-shares are more liquid).
    Works for .ST, .OL, and .CO exchanges.
    """
    # Group by base company (part before -A/-B/-C)
    companies: Dict[str, List[str]] = {}
    standalone: List[str] = []

    for ticker in tickers:
        # Match pattern like VOLV-A.ST, ATCO-B.ST, INDU-C.ST (also .OL, .CO)
        m = re.match(r'^(.+)-([ABC])' + _EXCHANGE_SUFFIXES + r'$', ticker)
        if m:
            base, share_class, exchange = m.group(1), m.group(2), m.group(3)
            key = f"{base}.{exchange}"
            companies.setdefault(key, []).append((ticker, share_class))
        else:
            standalone.append(ticker)

    # For each company with multiple share classes, pick the best one
    for key, variants in companies.items():
        if len(variants) == 1:
            standalone.append(variants[0][0])
        else:
            # Sort by priority (B=0, C=1, A=2) and pick the first
            best = min(variants, key=lambda x: _SHARE_CLASS_PRIORITY.get(x[1], 99))
            standalone.append(best[0])

    return standalone


def get_all_swedish_stocks(config_path: str = "config/nordic_stocks.csv") -> List[str]:
    """
    Return list of all stock tickers from the universe CSV.
    Deduplicates share classes (keeps B over A, C over A).

    Args:
        config_path: Path to nordic_stocks.csv file

    Returns:
        List of ticker symbols (e.g., ['VOLV-B.ST', 'ERIC-B.ST', 'EQNR.OL', ...])
    """
    csv_path = Path(__file__).parent.parent / config_path

    if not csv_path.exists():
        # Backward compatibility: try old filename
        old_path = Path(__file__).parent.parent / "config/swedish_stocks.csv"
        if old_path.exists():
            csv_path = old_path
        else:
            raise FileNotFoundError(f"Stock universe file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    if 'Ticker' not in df.columns:
        raise ValueError("CSV must have a 'Ticker' column")

    return _dedup_share_classes(df['Ticker'].tolist())


def get_stock_info(config_path: str = "config/nordic_stocks.csv") -> pd.DataFrame:
    """
    Get full stock information including name, sector, market cap.

    Args:
        config_path: Path to nordic_stocks.csv file

    Returns:
        DataFrame with columns: Ticker, Name, Sector, MarketCap, LastUpdated
    """
    csv_path = Path(__file__).parent.parent / config_path

    if not csv_path.exists():
        old_path = Path(__file__).parent.parent / "config/swedish_stocks.csv"
        if old_path.exists():
            csv_path = old_path
        else:
            raise FileNotFoundError(f"Stock universe file not found: {csv_path}")

    return pd.read_csv(csv_path)


def categorize_by_market_cap(config_path: str = "config/nordic_stocks.csv") -> Dict[str, List[str]]:
    """
    Group stocks by Large/Mid/Small cap.

    Args:
        config_path: Path to nordic_stocks.csv file

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
        print(f"Loaded {len(all_stocks)} stocks")

        se = [s for s in all_stocks if s.endswith('.ST')]
        no = [s for s in all_stocks if s.endswith('.OL')]
        dk = [s for s in all_stocks if s.endswith('.CO')]
        other = [s for s in all_stocks if not any(s.endswith(x) for x in ['.ST', '.OL', '.CO'])]

        print(f"  Swedish (.ST): {len(se)}")
        print(f"  Norwegian (.OL): {len(no)}")
        print(f"  Danish (.CO): {len(dk)}")
        if other:
            print(f"  Other: {len(other)}")

        print(f"First 5: {all_stocks[:5]}")

        by_cap = categorize_by_market_cap()
        print(f"\nMarket cap breakdown:")
        print(f"  Large cap: {len(by_cap['large'])} stocks")
        print(f"  Mid cap: {len(by_cap['mid'])} stocks")
        print(f"  Small cap: {len(by_cap['small'])} stocks")

    except Exception as e:
        print(f"Error: {e}")
