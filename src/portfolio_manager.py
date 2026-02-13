"""Portfolio management - Track holdings and generate trade recommendations."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class Portfolio:
    """Manage active portfolio holdings."""

    def __init__(self, portfolio_path: str = "config/active_portfolio.csv"):
        self.portfolio_path = Path(portfolio_path)
        self.holdings = self.load_holdings()

    def load_holdings(self) -> pd.DataFrame:
        """Load current holdings from CSV."""
        if self.portfolio_path.exists():
            df = pd.read_csv(self.portfolio_path)
            return df
        else:
            # Create empty portfolio
            return pd.DataFrame(columns=[
                'ticker', 'shares', 'entry_price', 'entry_date',
                'current_price', 'current_value', 'gain_loss_pct'
            ])

    def save_holdings(self):
        """Save holdings to CSV."""
        self.portfolio_path.parent.mkdir(exist_ok=True)
        self.holdings.to_csv(self.portfolio_path, index=False)

    def get_tickers(self) -> List[str]:
        """Get list of currently held tickers."""
        if self.holdings.empty:
            return []
        return self.holdings['ticker'].tolist()

    def get_holdings_count(self) -> int:
        """Get number of stocks currently held."""
        return len(self.holdings)

    def update_prices(self, current_prices: Dict[str, float]):
        """Update current prices and calculate gains/losses."""
        for ticker, price in current_prices.items():
            if ticker in self.holdings['ticker'].values:
                idx = self.holdings[self.holdings['ticker'] == ticker].index[0]
                self.holdings.loc[idx, 'current_price'] = price

                entry_price = self.holdings.loc[idx, 'entry_price']
                shares = self.holdings.loc[idx, 'shares']

                self.holdings.loc[idx, 'current_value'] = shares * price
                self.holdings.loc[idx, 'gain_loss_pct'] = ((price - entry_price) / entry_price) * 100

    def add_holding(self, ticker: str, shares: int, entry_price: float):
        """Add a new holding."""
        new_holding = pd.DataFrame([{
            'ticker': ticker,
            'shares': shares,
            'entry_price': entry_price,
            'entry_date': datetime.now().strftime('%Y-%m-%d'),
            'current_price': entry_price,
            'current_value': shares * entry_price,
            'gain_loss_pct': 0.0
        }])
        self.holdings = pd.concat([self.holdings, new_holding], ignore_index=True)

    def remove_holding(self, ticker: str):
        """Remove a holding (sell)."""
        self.holdings = self.holdings[self.holdings['ticker'] != ticker]

    def get_total_value(self) -> float:
        """Get total portfolio value."""
        if self.holdings.empty:
            return 0.0
        return self.holdings['current_value'].sum()

    def get_position_weight(self, ticker: str) -> float:
        """Get position weight as percentage of total portfolio."""
        total_value = self.get_total_value()
        if total_value == 0:
            return 0.0

        if ticker not in self.holdings['ticker'].values:
            return 0.0

        position_value = self.holdings[self.holdings['ticker'] == ticker]['current_value'].iloc[0]
        return (position_value / total_value) * 100


def calculate_position_size(
    total_capital: float,
    stock_price: float,
    target_weight: float = 2.5,
    max_weight: float = 3.0
) -> Tuple[int, float]:
    """
    Calculate position size for Kavastu's 2-3% position sizing.

    Args:
        total_capital: Total portfolio value
        stock_price: Current stock price
        target_weight: Target position weight in % (default 2.5%)
        max_weight: Maximum position weight in % (default 3.0%)

    Returns:
        Tuple of (shares to buy, actual weight %)
    """
    target_value = total_capital * (target_weight / 100)
    shares = int(target_value / stock_price)

    # Calculate actual weight
    actual_value = shares * stock_price
    actual_weight = (actual_value / total_capital) * 100

    # Ensure we don't exceed max weight
    if actual_weight > max_weight:
        # Reduce shares
        max_value = total_capital * (max_weight / 100)
        shares = int(max_value / stock_price)
        actual_weight = (shares * stock_price / total_capital) * 100

    return shares, actual_weight


def calculate_position_size_atr(
    total_capital: float,
    stock_price: float,
    atr: float,
    account_risk_pct: float = 1.0,
    atr_multiplier: float = 2.0,
    min_weight: float = 1.0,
    max_weight: float = 5.0,
    target_weight: float = 2.5
) -> Tuple[int, float, Dict]:
    """
    Calculate ATR-based position size (volatility-adjusted).

    Formula: Position Size = (Account Risk $) / (ATR × Multiplier)

    High volatility → smaller position (more risk per share → buy fewer shares)
    Low volatility → larger position (less risk per share → buy more shares)

    Example:
        Portfolio: $100,000
        Stock price: $100
        ATR: $5 (high volatility)
        Risk: 1% = $1,000
        Stop distance: $5 × 2 = $10
        Position: $1,000 / $10 × $100 = $10,000 (10% weight)
        But constrained to max_weight (5%), so: $5,000 = 50 shares

    Args:
        total_capital: Total portfolio value
        stock_price: Current stock price
        atr: Average True Range (volatility measure in $ terms)
        account_risk_pct: % of portfolio to risk per position (default 1%)
        atr_multiplier: ATR multiplier for stop distance (default 2x)
        min_weight: Minimum position weight % (default 1%)
        max_weight: Maximum position weight % (default 5%)
        target_weight: Fallback weight if ATR invalid (default 2.5%)

    Returns:
        Tuple of (shares, actual_weight_%, debug_info)
    """
    # Fallback to fixed sizing if ATR is invalid
    if pd.isna(atr) or atr <= 0:
        shares, actual_weight = calculate_position_size(
            total_capital, stock_price, target_weight, max_weight
        )
        return shares, actual_weight, {
            'method': 'fixed',
            'reason': 'Invalid ATR',
            'atr': atr
        }

    # Calculate risk-based position size
    risk_dollars = total_capital * (account_risk_pct / 100)
    stop_distance = atr * atr_multiplier
    position_dollars = risk_dollars / stop_distance * stock_price

    # Calculate weight percentage
    raw_weight = (position_dollars / total_capital) * 100

    # Constrain to min/max bounds
    constrained_weight = max(min_weight, min(max_weight, raw_weight))

    # Calculate shares
    shares = int((total_capital * constrained_weight / 100) / stock_price)
    actual_weight = (shares * stock_price / total_capital) * 100

    # Debug info
    debug_info = {
        'method': 'atr',
        'atr': atr,
        'risk_dollars': risk_dollars,
        'stop_distance': stop_distance,
        'raw_weight': raw_weight,
        'constrained_weight': constrained_weight,
        'constraint_applied': raw_weight != constrained_weight
    }

    return shares, actual_weight, debug_info


def calculate_conviction_weight(
    stock_rank: int,
    total_stocks: int,
    tier1_count: int = 15,
    tier1_weight_pct: float = 50.0,
    tier2_count: int = 25,
    tier2_weight_pct: float = 35.0,
    tier3_weight_pct: float = 15.0
) -> float:
    """
    Calculate conviction-based position weight based on stock rank.

    Mimics Kavastu's structure: Top 10-12 holdings = 40% of portfolio.
    Our adaptation: 3-tier system with decreasing weights.

    Tier 1 (Top 15): 50% of capital divided equally (3.3% each)
    Tier 2 (Next 25): 35% of capital divided equally (1.4% each)
    Tier 3 (Rest): 15% of capital divided equally (varies)

    Args:
        stock_rank: Rank of stock in sorted list (1 = best, higher = worse)
        total_stocks: Total number of stocks in portfolio
        tier1_count: Number of stocks in tier 1 (default 15)
        tier1_weight_pct: Percentage of capital for tier 1 (default 50%)
        tier2_count: Number of stocks in tier 2 (default 25)
        tier2_weight_pct: Percentage of capital for tier 2 (default 35%)
        tier3_weight_pct: Percentage of capital for tier 3 (default 15%)

    Returns:
        Target weight percentage for this stock (e.g., 3.3 for tier 1 stock)

    Example:
        Portfolio of 50 stocks:
        - Rank 1-15: 50% / 15 = 3.33% each
        - Rank 16-40: 35% / 25 = 1.40% each
        - Rank 41-50: 15% / 10 = 1.50% each
    """
    # Tier 1: Top N stocks (highest conviction)
    if stock_rank <= tier1_count:
        return tier1_weight_pct / tier1_count

    # Tier 2: Next N stocks (moderate conviction)
    elif stock_rank <= tier1_count + tier2_count:
        return tier2_weight_pct / tier2_count

    # Tier 3: Remaining stocks (low conviction, diversification)
    else:
        tier3_count = max(1, total_stocks - tier1_count - tier2_count)
        return tier3_weight_pct / tier3_count


def calculate_position_size_conviction(
    total_capital: float,
    stock_price: float,
    conviction_weight: float,
    max_weight: float = 5.0
) -> Tuple[int, float]:
    """
    Calculate position size based on conviction weight.

    Args:
        total_capital: Total portfolio value
        stock_price: Current stock price
        conviction_weight: Target weight % from conviction tier (e.g., 3.3)
        max_weight: Maximum weight cap (default 5%)

    Returns:
        Tuple of (shares, actual_weight_%)
    """
    # Cap at max weight for risk management
    target_weight = min(conviction_weight, max_weight)

    # Calculate shares
    position_value = total_capital * (target_weight / 100)
    shares = int(position_value / stock_price)

    # Calculate actual weight
    actual_weight = (shares * stock_price / total_capital) * 100

    return shares, actual_weight


def identify_base_portfolio(
    holdings_df: pd.DataFrame,
    top_n: int = 14
) -> pd.DataFrame:
    """
    Identify top 12-14 holdings as "basportfölj" (base portfolio).

    These are the strongest momentum picks, representing ~40% of total weight.

    Args:
        holdings_df: DataFrame with all holdings and their scores/metrics
        top_n: Number of top holdings to identify (default 14)

    Returns:
        DataFrame with top N holdings sorted by score
    """
    if holdings_df.empty:
        return holdings_df

    # Sort by score descending
    base_portfolio = holdings_df.nlargest(top_n, 'score')

    return base_portfolio


def compare_holdings_vs_watchlist(
    holdings: List[str],
    watchlist_df: pd.DataFrame,
    holdings_scores: Dict[str, float],
    target_count: int = 60
) -> Dict[str, List]:
    """
    Compare current holdings vs top-ranked stocks for weekly rotation.

    Kavastu strategy: Hold 60-80 stocks, each 2-3% weight.
    Weekly rotation: "Clean out the weak" - replace underperformers.

    Args:
        holdings: List of currently held tickers
        watchlist_df: DataFrame from screener with all ranked stocks
        holdings_scores: Dict mapping held ticker to current score
        target_count: Target number of holdings (default 60 for full portfolio)

    Returns:
        Dict with 'sell', 'buy', 'hold', and 'rotate' lists
    """
    recommendations = {
        'sell': [],    # Sell these (weak performers, below MA200)
        'buy': [],     # Buy these (strong candidates to fill slots)
        'hold': [],    # Keep these (still strong)
        'rotate': []   # Rotation suggestions (swap weak for strong)
    }

    # Get top N stocks from watchlist (for 60-80 portfolio, look at top 100)
    top_stocks = watchlist_df.head(min(target_count * 2, 100))
    top_tickers = set(top_stocks['ticker'].tolist())

    # Analyze current holdings
    holdings_with_scores = []
    for ticker in holdings:
        current_score = holdings_scores.get(ticker, 0)

        # Find rank in watchlist
        if ticker in watchlist_df['ticker'].values:
            rank = watchlist_df[watchlist_df['ticker'] == ticker].index[0] + 1
        else:
            rank = 999  # Not in top stocks

        holdings_with_scores.append({
            'ticker': ticker,
            'score': current_score,
            'rank': rank,
            'in_top': ticker in top_tickers
        })

    # Sort holdings by score to identify weak vs strong
    holdings_with_scores.sort(key=lambda x: x['score'], reverse=True)

    # Categorize holdings
    for holding in holdings_with_scores:
        ticker = holding['ticker']
        score = holding['score']
        rank = holding['rank']

        if holding['in_top']:
            # Still in top stocks - keep it
            recommendations['hold'].append({
                'ticker': ticker,
                'score': score,
                'rank': rank,
                'reason': f'Ranked #{rank}, still strong'
            })
        else:
            # Fell out of top stocks - mark for potential sale
            recommendations['sell'].append({
                'ticker': ticker,
                'score': score,
                'rank': rank,
                'reason': f'Dropped to rank #{rank}, lost momentum'
            })

    # Find buy candidates (top stocks not currently held)
    current_holdings_set = set(holdings)
    buy_candidates = top_stocks[~top_stocks['ticker'].isin(current_holdings_set)]

    # Calculate slots available
    current_count = len(holdings)
    sells_count = len(recommendations['sell'])
    slots_available = target_count - (current_count - sells_count)

    # Recommend buys to reach target count
    if slots_available > 0:
        for idx, row in buy_candidates.head(slots_available).iterrows():
            recommendations['buy'].append({
                'ticker': row['ticker'],
                'score': row['score'],
                'rank': idx + 1,
                'reason': f'Strong momentum (rank #{idx + 1})'
            })

    # Generate rotation suggestions (swap weakest holdings for strongest candidates)
    # Only if portfolio is near target size
    if abs(current_count - target_count) <= 5 and recommendations['sell']:
        weak_holdings = sorted(recommendations['sell'], key=lambda x: x['score'])[:5]
        strong_candidates = buy_candidates.head(5)

        for weak, (_, strong) in zip(weak_holdings, strong_candidates.iterrows()):
            if strong['score'] > weak['score'] + 10:  # Significant score improvement
                recommendations['rotate'].append({
                    'sell': weak['ticker'],
                    'sell_score': weak['score'],
                    'buy': strong['ticker'],
                    'buy_score': strong['score'],
                    'improvement': strong['score'] - weak['score'],
                    'reason': f"Swap weak {weak['ticker']} (score {weak['score']:.1f}) for strong {strong['ticker']} (score {strong['score']:.1f})"
                })

    return recommendations


def detect_weak_holdings(
    holdings_metrics: pd.DataFrame,
    min_score: float = 60,
    max_distance_below_ma200: float = -3.0
) -> List[Dict]:
    """
    Detect holdings that have become weak.

    Args:
        holdings_metrics: DataFrame with current metrics for all holdings
        min_score: Minimum acceptable score (default 60)
        max_distance_below_ma200: Max % below MA200 before alert (default -3%)

    Returns:
        List of weak holdings with alerts
    """
    weak_holdings = []

    for idx, row in holdings_metrics.iterrows():
        alerts = []

        # Check score
        if row['score'] < min_score:
            alerts.append(f"Score dropped to {row['score']:.1f}")

        # Check MA200 distance
        if row['distance_ma200'] < max_distance_below_ma200:
            alerts.append(f"{row['distance_ma200']:.1f}% below MA200")

        # Check death cross
        if row.get('death_cross', False):
            alerts.append("Death cross detected")

        if alerts:
            weak_holdings.append({
                'ticker': row['ticker'],
                'alerts': alerts,
                'score': row['score'],
                'distance_ma200': row['distance_ma200']
            })

    return weak_holdings


def format_trade_recommendations(recommendations: Dict[str, List]) -> str:
    """Format trade recommendations for display."""
    output = []

    output.append("=" * 80)
    output.append("WEEKLY TRADE RECOMMENDATIONS (Execute Monday Morning)")
    output.append("=" * 80)

    # Rotation suggestions (most important - swap weak for strong)
    if recommendations.get('rotate'):
        output.append(f"\n🔄 ROTATION SUGGESTIONS ({len(recommendations['rotate'])} swaps):")
        output.append("   \"Rensa det svaga\" - Swap weak holdings for stronger momentum:")
        for item in recommendations['rotate']:
            output.append(f"   SELL {item['sell']:<10} (score {item['sell_score']:.1f}) → BUY {item['buy']:<10} (score {item['buy_score']:.1f}) [+{item['improvement']:.1f}]")

    # Sells
    if recommendations['sell']:
        output.append(f"\n🔴 SELL ({len(recommendations['sell'])} stocks):")
        for item in recommendations['sell'][:10]:  # Show top 10
            output.append(f"   {item['ticker']:<12} Score: {item['score']:<6.1f} Rank: #{item.get('rank', 'N/A'):<4} {item['reason']}")
        if len(recommendations['sell']) > 10:
            output.append(f"   ... and {len(recommendations['sell']) - 10} more weak holdings")
    else:
        output.append(f"\n✅ No sells needed")

    # Buys
    if recommendations['buy']:
        output.append(f"\n🟢 BUY ({len(recommendations['buy'])} stocks):")
        for item in recommendations['buy'][:10]:  # Show top 10
            output.append(f"   {item['ticker']:<12} Score: {item['score']:<6.1f} Rank: #{item.get('rank', 'N/A'):<4} {item['reason']}")
        if len(recommendations['buy']) > 10:
            output.append(f"   ... and {len(recommendations['buy']) - 10} more buy candidates")
    else:
        output.append(f"\n✅ No buys needed (portfolio is at target size)")

    # Holds
    if recommendations['hold']:
        output.append(f"\n⚪ HOLD ({len(recommendations['hold'])} stocks):")
        # Show top 14 (basportfölj)
        top_holds = sorted(recommendations['hold'], key=lambda x: x['score'], reverse=True)
        output.append("\n   📊 BASPORTFÖLJ (Top 14 strongest holdings):")
        for item in top_holds[:14]:
            output.append(f"      {item['ticker']:<12} Score: {item['score']:<6.1f} Rank: #{item.get('rank', 'N/A'):<4}")

        if len(recommendations['hold']) > 14:
            output.append(f"\n   ... and {len(recommendations['hold']) - 14} more holdings in full portfolio")

    return "\n".join(output)
