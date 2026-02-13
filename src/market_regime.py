"""Market regime analysis - Determine bull/neutral/bear market."""
import pandas as pd
from typing import Dict
from .data_fetcher import fetch_stock_data
from .ma_calculator import calculate_ma50_ma200, calculate_atr, calculate_volatility_percentile


def get_market_regime() -> Dict[str, any]:
    """
    Analyze OMXS30 market regime.

    Returns:
        {
            'regime': 'bull' | 'neutral' | 'bear',
            'index_price': float,
            'index_ma200': float,
            'index_vs_ma200': float (percentage),
            'recommendation': str
        }
    """
    # Fetch OMXS30 index (^OMX)
    index_data = fetch_stock_data('^OMX', period='1y')

    if index_data is None or index_data.empty:
        return {
            'regime': 'unknown',
            'recommendation': 'Unable to determine market regime'
        }

    # Calculate MA200 for index
    index_data = calculate_ma50_ma200(index_data)

    current_price = index_data['Close'].iloc[-1]
    ma200 = index_data['MA200'].iloc[-1]

    if pd.isna(ma200):
        return {
            'regime': 'unknown',
            'recommendation': 'Insufficient data for MA200'
        }

    # Index position vs MA200
    index_vs_ma200 = ((current_price - ma200) / ma200) * 100

    # Determine regime based on index position
    # Bull: Index > MA200
    # Bear: Index < MA200
    if current_price > ma200:
        regime = 'bull'
        recommendation = "✅ BULL MARKET: Stay fully invested (12-14 stocks)"
    else:
        regime = 'bear'
        recommendation = "⚠️ BEAR MARKET: Go defensive (0-5 stocks, 80%+ cash)"

    return {
        'regime': regime,
        'index_price': current_price,
        'index_ma200': ma200,
        'index_vs_ma200': index_vs_ma200,
        'recommendation': recommendation
    }


def get_market_regime_dynamic(
    index_data: pd.DataFrame,
    stock_universe_data: Dict[str, pd.DataFrame],
    as_of_date: str
) -> Dict:
    """
    Phase 2: Multi-factor dynamic regime detection with portfolio sizing.

    Factors (100-point scale):
    1. Index vs MA50/MA100/MA200 (0-40 points)
    2. Market breadth - % stocks above MA200 (0-30 points)
    3. Market volatility - ATR percentile inverse (0-30 points)

    Regimes and portfolio sizing:
    - STRONG_BULL (75-100 pts): 60-80 stocks, fully invested
    - BULL (55-74 pts): 40-60 stocks, mostly invested
    - NEUTRAL (35-54 pts): 20-40 stocks, moderate positioning
    - BEAR (20-34 pts): 5-20 stocks, defensive
    - PANIC (0-19 pts): 0-5 stocks, capital preservation

    Args:
        index_data: DataFrame with OMXS30 index data (must have MA50, MA100, MA200)
        stock_universe_data: Dict mapping ticker -> DataFrame for all stocks
        as_of_date: Date for regime assessment (YYYY-MM-DD)

    Returns:
        Dict with regime classification and portfolio sizing recommendation
    """
    regime_score = 0.0

    # Get current index values
    index_price = index_data['Close'].iloc[-1]
    ma50 = index_data['MA50'].iloc[-1]
    ma100 = index_data['MA100'].iloc[-1] if 'MA100' in index_data.columns else None
    ma200 = index_data['MA200'].iloc[-1]

    # Factor 1: Index position relative to MAs (0-40 points)
    index_vs_ma200 = ((index_price - ma200) / ma200) * 100 if not pd.isna(ma200) else 0

    if index_price > ma200:
        regime_score += 20  # Base points for being above MA200

        # Triple MA alignment bonus
        if ma100 is not None and not pd.isna(ma100) and not pd.isna(ma50):
            if ma50 > ma100 > ma200:
                # Perfect triple MA alignment - very bullish
                regime_score += 20
            elif ma50 > ma200:
                # At least MA50 > MA200 - moderately bullish
                regime_score += 10
    elif index_vs_ma200 > -5:
        # Just below MA200 (within 5%) - minor penalty
        regime_score += 5

    # Factor 2: Market breadth - % of stocks above MA200 (0-30 points)
    stocks_above_ma200 = 0
    total_stocks = 0

    for ticker, df in stock_universe_data.items():
        if df.empty or 'MA200' not in df.columns or len(df) == 0:
            continue

        total_stocks += 1
        current_price = df['Close'].iloc[-1]
        stock_ma200 = df['MA200'].iloc[-1]

        if not pd.isna(stock_ma200) and current_price > stock_ma200:
            stocks_above_ma200 += 1

    breadth_pct = (stocks_above_ma200 / total_stocks) * 100 if total_stocks > 0 else 0

    # Breadth scoring
    if breadth_pct > 70:
        regime_score += 30  # Excellent breadth
    elif breadth_pct > 50:
        regime_score += 20  # Good breadth
    elif breadth_pct > 30:
        regime_score += 10  # Moderate breadth
    elif breadth_pct > 15:
        regime_score += 5   # Weak breadth

    # Factor 3: Market volatility - inverse relationship (0-30 points)
    # Low volatility = bullish, high volatility = bearish
    if 'ATR' not in index_data.columns:
        index_data['ATR'] = calculate_atr(index_data, period=14)

    volatility_pct = calculate_volatility_percentile(index_data, lookback=252)

    # Inverse scoring: lower volatility = higher score
    if volatility_pct < 30:
        regime_score += 30  # Very low volatility - calm market
    elif volatility_pct < 50:
        regime_score += 20  # Below average volatility
    elif volatility_pct < 70:
        regime_score += 10  # Above average volatility
    elif volatility_pct < 85:
        regime_score += 5   # High volatility

    # Classify regime based on total score (0-100)
    if regime_score >= 75:
        regime = "STRONG_BULL"
        target_stocks = 80
        description = "Strong bull market - fully invested, maximum diversification"
    elif regime_score >= 55:
        regime = "BULL"
        target_stocks = 60
        description = "Bull market - mostly invested, good diversification"
    elif regime_score >= 35:
        regime = "NEUTRAL"
        target_stocks = 40
        description = "Neutral market - moderate positioning, selective"
    elif regime_score >= 20:
        regime = "BEAR"
        target_stocks = 20
        description = "Bear market - defensive positioning, high quality only"
    else:
        regime = "PANIC"
        target_stocks = 5
        description = "Panic/Crisis - capital preservation, minimal exposure"

    return {
        'regime': regime,
        'regime_score': round(regime_score, 1),
        'target_stocks': target_stocks,
        'description': description,
        'index_vs_ma200': round(index_vs_ma200, 2),
        'breadth_pct': round(breadth_pct, 1),
        'volatility_percentile': round(volatility_pct, 1),
        'as_of_date': as_of_date
    }


def calculate_watchlist_health(watchlist_df: pd.DataFrame) -> float:
    """
    Calculate % of watchlist stocks above MA200.

    Args:
        watchlist_df: DataFrame from screener with 'distance_ma200' column

    Returns:
        Percentage of stocks above MA200
    """
    if watchlist_df.empty:
        return 0.0

    # Count stocks with positive distance from MA200
    above_ma200 = (watchlist_df['distance_ma200'] > 0).sum()
    total = len(watchlist_df)

    return (above_ma200 / total) * 100 if total > 0 else 0.0


def get_position_sizing_recommendation(
    regime: str,
    watchlist_health: float
) -> Dict[str, any]:
    """
    Kavastu position sizing based on market regime.

    Args:
        regime: 'bull', 'neutral', or 'bear'
        watchlist_health: % of watchlist above MA200

    Returns:
        {
            'target_stocks': str,
            'target_cash_pct': str,
            'reasoning': str
        }
    """
    if regime == 'bull' and watchlist_health > 70:
        return {
            'target_stocks': '12-14',
            'target_cash_pct': '0-10%',
            'reasoning': 'Strong bull market - fully invested'
        }
    elif regime == 'bear' or watchlist_health < 30:
        return {
            'target_stocks': '0-5',
            'target_cash_pct': '80-100%',
            'reasoning': 'Bear market or weak breadth - capital preservation'
        }
    else:  # Neutral
        return {
            'target_stocks': '8-12',
            'target_cash_pct': '20-40%',
            'reasoning': 'Neutral market - moderate positioning'
        }
