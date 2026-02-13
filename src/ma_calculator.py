"""MA calculator - Calculate MA50/MA100/MA200 and detect crossovers."""
import pandas as pd
from typing import Dict, Optional, Tuple


def calculate_ma(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate simple moving average.

    Args:
        prices: Series of closing prices
        window: Window size (50, 200, etc.)

    Returns:
        Series of MA values
    """
    return prices.rolling(window=window).mean()


def calculate_ma50_ma200(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add MA50, MA100, and MA200 columns to price DataFrame.

    Triple MA system for trend strength detection:
    - MA50 > MA100 > MA200: Strong uptrend (highest conviction)
    - MA50 > MA200 (but MA100 < MA200): Early uptrend (medium conviction)
    - Price > MA200 only: Weak uptrend (low conviction)

    Args:
        df: DataFrame with 'Close' column

    Returns:
        Original DataFrame with MA50, MA100, and MA200 columns added
    """
    df = df.copy()

    df['MA50'] = calculate_ma(df['Close'], 50)
    df['MA100'] = calculate_ma(df['Close'], 100)
    df['MA200'] = calculate_ma(df['Close'], 200)

    return df


def calculate_ma_custom(df: pd.DataFrame, periods: Tuple[int, int, int]) -> pd.DataFrame:
    """
    Calculate custom MA periods and map to standard column names.

    This enables MA parameter optimization (Feature 4) by allowing flexible
    MA periods (e.g., (40, 100, 180) instead of fixed (50, 100, 200)).
    The results are mapped to standard names (MA50, MA100, MA200) to maintain
    backward compatibility with existing code.

    Args:
        df: DataFrame with 'Close' column
        periods: Tuple of (fast, medium, slow) MA periods
                 e.g., (40, 100, 180) or (60, 120, 220)

    Returns:
        Original DataFrame with custom MA columns added and mapped to standard names

    Example:
        # Test MA(40, 100, 180) instead of default (50, 100, 200)
        df = calculate_ma_custom(df, periods=(40, 100, 180))
        # Now df has MA40, MA100, MA180 columns
        # PLUS MA50, MA100, MA200 aliased to the custom periods
    """
    df = df.copy()
    fast, medium, slow = periods

    # Calculate MAs with custom periods
    df[f'MA{fast}'] = calculate_ma(df['Close'], fast)
    df[f'MA{medium}'] = calculate_ma(df['Close'], medium)
    df[f'MA{slow}'] = calculate_ma(df['Close'], slow)

    # Map to standard names for backward compatibility
    # This allows the rest of the code to use 'MA50', 'MA100', 'MA200'
    # without knowing the actual periods used
    df['MA50'] = df[f'MA{fast}']
    df['MA100'] = df[f'MA{medium}']
    df['MA200'] = df[f'MA{slow}']

    return df


def detect_crossover(df: pd.DataFrame, lookback: int = 7) -> Dict[str, any]:
    """
    Detect if stock crossed MA200 recently.

    Args:
        df: DataFrame with Close, MA50, MA200 columns
        lookback: Days to look back for crossover (default 7)

    Returns:
        Dict with crossover info:
        {
            'crossed_below_ma200': bool,
            'crossed_above_ma200': bool,
            'current_position': 'above' | 'below' | 'unknown',
            'distance_from_ma200': float (percentage),
            'ma50_above_ma200': bool (golden cross),
            'days_since_crossover': int or None
        }
    """
    result = {
        'crossed_below_ma200': False,
        'crossed_above_ma200': False,
        'current_position': 'unknown',
        'distance_from_ma200': 0.0,
        'ma50_above_ma200': False,
        'days_since_crossover': None
    }

    if len(df) < lookback + 1:
        return result

    # Get recent data
    recent = df.tail(lookback + 1)

    # Check if we have valid MA200 values
    if recent['MA200'].isna().all():
        return result

    current_price = recent['Close'].iloc[-1]
    current_ma200 = recent['MA200'].iloc[-1]
    current_ma50 = recent['MA50'].iloc[-1]

    if pd.isna(current_ma200):
        return result

    # Current position
    if current_price > current_ma200:
        result['current_position'] = 'above'
    else:
        result['current_position'] = 'below'

    # Distance from MA200
    result['distance_from_ma200'] = ((current_price - current_ma200) / current_ma200) * 100

    # MA50 above MA200 (golden cross)
    if not pd.isna(current_ma50) and not pd.isna(current_ma200):
        result['ma50_above_ma200'] = current_ma50 > current_ma200

    # Detect crossovers in lookback period
    for i in range(len(recent) - 1):
        prev_price = recent['Close'].iloc[i]
        prev_ma200 = recent['MA200'].iloc[i]
        next_price = recent['Close'].iloc[i + 1]
        next_ma200 = recent['MA200'].iloc[i + 1]

        if pd.isna(prev_ma200) or pd.isna(next_ma200):
            continue

        # Crossed below MA200
        if prev_price >= prev_ma200 and next_price < next_ma200:
            result['crossed_below_ma200'] = True
            result['days_since_crossover'] = len(recent) - i - 2

        # Crossed above MA200
        if prev_price <= prev_ma200 and next_price > next_ma200:
            result['crossed_above_ma200'] = True
            result['days_since_crossover'] = len(recent) - i - 2

    return result


def calculate_ma200_slope(df: pd.DataFrame, lookback: int = 20) -> float:
    """
    Calculate MA200 slope to determine if trend is rising.

    Args:
        df: DataFrame with MA200 column
        lookback: Days to calculate slope over

    Returns:
        Slope value (positive = rising, negative = falling)
    """
    if len(df) < lookback:
        return 0.0

    recent_ma200 = df['MA200'].tail(lookback)

    if recent_ma200.isna().all():
        return 0.0

    # Simple linear regression slope
    ma200_start = recent_ma200.iloc[0]
    ma200_end = recent_ma200.iloc[-1]

    if pd.isna(ma200_start) or pd.isna(ma200_end):
        return 0.0

    slope = (ma200_end - ma200_start) / lookback

    return slope


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range for volatility measurement.

    The ATR measures market volatility by decomposing the entire range of an asset
    price for that period. Higher ATR = higher volatility.

    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns
        period: Window size for ATR calculation (default 14)

    Returns:
        Series of ATR values
    """
    high = df['High']
    low = df['Low']
    close = df['Close']

    # True Range is the greatest of:
    # 1. Current High - Current Low
    # 2. Abs(Current High - Previous Close)
    # 3. Abs(Current Low - Previous Close)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def calculate_volatility_percentile(df: pd.DataFrame, lookback: int = 252) -> float:
    """
    Calculate current volatility percentile (0-100) over lookback period.

    This tells us if current volatility is high or low compared to historical levels.
    High percentile (>70) = high volatility = smaller position sizes
    Low percentile (<30) = low volatility = larger position sizes

    Args:
        df: DataFrame with 'ATR' column
        lookback: Days to calculate percentile over (default 252 = 1 year)

    Returns:
        Percentile value (0-100), or 50.0 if insufficient data
    """
    if 'ATR' not in df.columns or len(df) < lookback:
        return 50.0

    recent_atr = df['ATR'].tail(lookback)
    current_atr = df['ATR'].iloc[-1]

    if pd.isna(current_atr):
        return 50.0

    # Calculate percentile: what % of recent ATR values are below current
    percentile = (recent_atr < current_atr).sum() / len(recent_atr) * 100

    return percentile


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).

    RSI measures momentum on a scale of 0-100:
    - RSI > 70: Overbought (potential reversal down)
    - RSI 50-70: Bullish momentum
    - RSI 40-50: Neutral
    - RSI < 30: Oversold (potential reversal up)

    For Kavastu strategy, we prefer RSI 50-60 (strong but not overbought).

    Args:
        df: DataFrame with 'Close' column
        period: Window size (default 14)

    Returns:
        Series of RSI values (0-100)
    """
    delta = df['Close'].diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    MACD shows trend direction and momentum:
    - MACD > Signal: Bullish
    - MACD < Signal: Bearish
    - Crossover up: Buy signal
    - Crossover down: Sell signal

    Args:
        df: DataFrame with 'Close' column
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)

    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def detect_macd_crossover(df: pd.DataFrame, lookback: int = 5) -> Dict[str, any]:
    """
    Detect recent MACD crossover signals.

    Args:
        df: DataFrame with MACD, MACD_Signal, MACD_Hist columns
        lookback: Days to look back for crossover (default 5)

    Returns:
        Dict with crossover info:
        {
            'bullish_crossover': bool (MACD crossed above signal),
            'bearish_crossover': bool (MACD crossed below signal),
            'macd_positive': bool (MACD above zero line),
            'histogram_rising': bool (momentum increasing)
        }
    """
    result = {
        'bullish_crossover': False,
        'bearish_crossover': False,
        'macd_positive': False,
        'histogram_rising': False
    }

    if 'MACD' not in df.columns or len(df) < lookback + 1:
        return result

    recent = df.tail(lookback + 1)
    current_macd = recent['MACD'].iloc[-1]
    current_signal = recent['MACD_Signal'].iloc[-1]

    # MACD position relative to zero
    result['macd_positive'] = current_macd > 0

    # Check histogram trend (increasing momentum)
    if 'MACD_Hist' in df.columns:
        hist_recent = recent['MACD_Hist'].tail(3)
        if len(hist_recent) >= 2:
            result['histogram_rising'] = hist_recent.iloc[-1] > hist_recent.iloc[-2]

    # Detect crossovers in lookback period
    for i in range(len(recent) - 1):
        prev_macd = recent['MACD'].iloc[i]
        prev_signal = recent['MACD_Signal'].iloc[i]
        next_macd = recent['MACD'].iloc[i + 1]
        next_signal = recent['MACD_Signal'].iloc[i + 1]

        if pd.isna(prev_macd) or pd.isna(next_macd):
            continue

        # Bullish crossover (MACD crosses above signal)
        if prev_macd <= prev_signal and next_macd > next_signal:
            result['bullish_crossover'] = True

        # Bearish crossover (MACD crosses below signal)
        if prev_macd >= prev_signal and next_macd < next_signal:
            result['bearish_crossover'] = True

    return result


def get_52_week_high(df: pd.DataFrame) -> Optional[float]:
    """
    Get 52-week high price.

    Args:
        df: DataFrame with 'High' column

    Returns:
        52-week high price, or None if not enough data
    """
    if len(df) < 252:  # ~1 year of trading days
        # Use whatever data we have
        return df['High'].max()

    return df['High'].tail(252).max()


if __name__ == "__main__":
    # Test the module
    print("Testing ma_calculator.py...")

    import sys
    sys.path.append('..')
    from src.data_fetcher import fetch_stock_data

    # Test with Volvo B
    print("\n📊 Testing with VOLV-B.ST...")
    df = fetch_stock_data('VOLV-B.ST', period='1y')

    if df is not None:
        # Add MAs
        df = calculate_ma50_ma200(df)

        print(f"✅ Calculated MAs")
        print(f"   Current price: {df['Close'].iloc[-1]:.2f}")
        print(f"   MA50: {df['MA50'].iloc[-1]:.2f}")
        print(f"   MA200: {df['MA200'].iloc[-1]:.2f}")

        # Detect crossover
        crossover = detect_crossover(df)
        print(f"\n📈 Crossover analysis:")
        print(f"   Position: {crossover['current_position']}")
        print(f"   Distance from MA200: {crossover['distance_from_ma200']:.2f}%")
        print(f"   MA50 > MA200: {crossover['ma50_above_ma200']}")
        print(f"   Crossed below (last 7 days): {crossover['crossed_below_ma200']}")
        print(f"   Crossed above (last 7 days): {crossover['crossed_above_ma200']}")

        # MA200 slope
        slope = calculate_ma200_slope(df)
        print(f"\n📊 MA200 slope: {slope:.4f} ({'rising' if slope > 0 else 'falling'})")

        # 52-week high
        high_52w = get_52_week_high(df)
        print(f"   52-week high: {high_52w:.2f}")
