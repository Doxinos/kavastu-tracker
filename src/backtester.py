"""Backtesting engine for Kavastu strategy."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from .data_fetcher import fetch_stock_data, fetch_portfolio_data, fetch_dividend_data
from .ma_calculator import calculate_ma50_ma200, detect_crossover, calculate_atr
from .screener import calculate_stock_score
from .market_regime import get_market_regime, get_market_regime_dynamic
from .portfolio_manager import calculate_position_size_atr, calculate_conviction_weight, calculate_position_size_conviction


class Portfolio:
    """Track portfolio holdings and performance."""

    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings = {}  # {ticker: {'shares': int, 'entry_price': float}}
        self.history = []  # Track daily portfolio values
        self.total_dividends = 0.0  # Track total dividends received
        self.total_isk_tax = 0.0  # Track total ISK tax paid
        self.peak_value = initial_capital  # Track peak value for drawdown management

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        holdings_value = sum(
            self.holdings[ticker]['shares'] * current_prices.get(ticker, 0)
            for ticker in self.holdings
        )
        return self.cash + holdings_value

    def get_holdings_count(self) -> int:
        """Return number of stocks currently held."""
        return len(self.holdings)

    def buy(self, ticker: str, amount: float, price: float, transaction_cost: float = 0.0025):
        """Buy shares of a stock."""
        cost_with_fees = amount * (1 + transaction_cost)
        if cost_with_fees > self.cash:
            return False

        shares = int(amount / price)
        if shares <= 0:
            return False

        actual_cost = shares * price * (1 + transaction_cost)

        if ticker in self.holdings:
            # Average up
            old_shares = self.holdings[ticker]['shares']
            old_value = old_shares * self.holdings[ticker]['entry_price']
            new_value = shares * price
            total_shares = old_shares + shares
            avg_price = (old_value + new_value) / total_shares

            self.holdings[ticker] = {
                'shares': total_shares,
                'entry_price': avg_price
            }
        else:
            self.holdings[ticker] = {
                'shares': shares,
                'entry_price': price
            }

        self.cash -= actual_cost
        return True

    def sell(self, ticker: str, price: float, transaction_cost: float = 0.0025):
        """Sell all shares of a stock."""
        if ticker not in self.holdings:
            return False

        shares = self.holdings[ticker]['shares']
        proceeds = shares * price * (1 - transaction_cost)

        self.cash += proceeds
        del self.holdings[ticker]
        return True

    def sell_all(self, current_prices: Dict[str, float], transaction_cost: float = 0.0025):
        """Sell all holdings."""
        for ticker in list(self.holdings.keys()):
            if ticker in current_prices:
                self.sell(ticker, current_prices[ticker], transaction_cost)

    def collect_dividends(self, dividend_data: Dict[str, pd.Series], start_date: str, end_date: str):
        """
        Collect dividends for currently held stocks in date range.
        Dividends are automatically reinvested as cash (Kavastu's approach).

        Args:
            dividend_data: Dict mapping ticker -> dividend Series
            start_date: Start of period to check (YYYY-MM-DD)
            end_date: End of period to check (YYYY-MM-DD)

        Returns:
            Total dividends collected in this period
        """
        period_dividends = 0.0

        for ticker in self.holdings:
            if ticker not in dividend_data:
                continue

            shares = self.holdings[ticker]['shares']
            dividends = dividend_data[ticker]

            # Convert dates, handling timezone if needed
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)

            if dividends.index.tz is not None:
                # Make start/end timezone-aware to match
                start = start.tz_localize(dividends.index.tz)
                end = end.tz_localize(dividends.index.tz)

            # Filter dividends in this period
            period_divs = dividends[(dividends.index > start) & (dividends.index <= end)]

            for div_date, div_amount in period_divs.items():
                div_received = shares * div_amount
                self.cash += div_received
                period_dividends += div_received
                self.total_dividends += div_received

        return period_dividends

    def pay_isk_tax(self, portfolio_value: float, year: int = 2026):
        """
        Calculate and pay ISK (Investeringssparkonto) account tax.

        Swedish ISK tax structure:
        - Flat tax rate on portfolio value (not gains)
        - 2026 rate: 1.065% annually
        - Tax-free amount: 300,000 SEK (2026)
        - NO capital gains tax on trades

        Args:
            portfolio_value: Current total portfolio value
            year: Tax year (affects rate and tax-free amount)

        Returns:
            ISK tax paid this year
        """
        # Tax parameters by year
        if year >= 2026:
            tax_rate = 0.01065  # 1.065% for 2026
            tax_free_amount = 300000  # 300k SEK tax-free (doubled from 2025)
        else:
            # Historical rates (approximate)
            tax_rate = 0.01  # ~1% average
            tax_free_amount = 150000  # 150k SEK before 2026

        # Calculate taxable amount
        if portfolio_value <= tax_free_amount:
            return 0.0

        taxable_amount = portfolio_value - tax_free_amount
        isk_tax = taxable_amount * tax_rate

        # Deduct from cash
        self.cash -= isk_tax
        self.total_isk_tax += isk_tax

        return isk_tax

    def get_drawdown_adjustment(self, current_prices: Dict[str, float]) -> Tuple[float, float, str]:
        """
        Calculate drawdown and return position size adjustment.

        Tiered drawdown approach (manual crash management simulation):
        - 0-5% drawdown: 100% allocation (normal)
        - 5-10% drawdown: 85% allocation (slightly cautious)
        - 10-15% drawdown: 70% allocation (reduce risk)
        - 15-20% drawdown: 60% allocation (defensive)
        - >20% drawdown: 50% allocation (max defensive - simulates selling half, keeping half invested)

        Note: Never goes below 50% allocation to simulate realistic manual management
        where you stay partially invested to capture recovery.

        Args:
            current_prices: Dict of current stock prices

        Returns:
            Tuple of (drawdown_pct, size_multiplier, risk_level)
        """
        current_value = self.get_total_value(current_prices)

        # Update peak if we've reached new highs
        if current_value > self.peak_value:
            self.peak_value = current_value

        # Calculate drawdown
        drawdown_pct = ((self.peak_value - current_value) / self.peak_value) * 100

        # Determine size multiplier and risk level
        # More gradual reduction, never below 50% to allow recovery capture
        if drawdown_pct < 5:
            return drawdown_pct, 1.0, "NORMAL"
        elif drawdown_pct < 10:
            return drawdown_pct, 0.85, "CAUTIOUS"
        elif drawdown_pct < 15:
            return drawdown_pct, 0.70, "REDUCE"
        elif drawdown_pct < 20:
            return drawdown_pct, 0.60, "DEFENSIVE"
        else:
            # MAX DEFENSIVE: 50% invested, 50% cash
            # Simulates manual crash management - sell half, keep half for recovery
            return drawdown_pct, 0.50, "MAX_DEFENSIVE"


def backtest_strategy(
    stocks: List[str],
    start_date: str = "2020-01-01",
    end_date: str = "2026-01-01",
    initial_capital: float = 100000,
    rebalance_frequency: str = "monthly",  # monthly or weekly
    max_holdings: int = 70,  # Kavastu: 60-80 stocks (2-3% each)
    transaction_cost: float = 0.0025,  # 0.25% per trade
    use_atr_sizing: bool = False,  # Phase 2: ATR-based position sizing
    atr_account_risk: float = 1.0,  # Phase 2: % risk per position for ATR sizing
    atr_multiplier: float = 2.0,  # Phase 2: ATR multiplier for stop distance
    use_dynamic_regime: bool = False,  # Phase 2: Dynamic regime detection (0-80 stocks)
    max_holdings_dynamic: int = 80,  # Phase 2: Maximum holdings in strong bull regime
    use_conviction_weighting: bool = False,  # Phase 2.5: Conviction-weighted portfolio
    conviction_tier1_count: int = 15,  # Phase 2.5: Number of tier 1 stocks
    conviction_tier1_weight: float = 50.0,  # Phase 2.5: % capital in tier 1
    conviction_tier2_count: int = 25,  # Phase 2.5: Number of tier 2 stocks
    conviction_tier2_weight: float = 35.0,  # Phase 2.5: % capital in tier 2
    conviction_tier3_weight: float = 15.0  # Phase 2.5: % capital in tier 3
) -> Dict:
    """
    Backtest Kavastu strategy over historical period (Phase 2: Advanced Features).

    Args:
        stocks: List of stock tickers to include in universe
        start_date: Start date for backtest (YYYY-MM-DD)
        end_date: End date for backtest (YYYY-MM-DD)
        initial_capital: Starting capital in SEK
        rebalance_frequency: 'monthly' or 'weekly'
        max_holdings: Maximum number of stocks to hold (default 70, ignored if use_dynamic_regime=True)
        transaction_cost: Transaction cost as decimal (default 0.25%)
        use_atr_sizing: Enable ATR-based position sizing (Phase 2)
        atr_account_risk: % of portfolio to risk per position (default 1%)
        atr_multiplier: ATR multiplier for stop distance (default 2x)
        use_dynamic_regime: Enable dynamic regime detection with adaptive portfolio sizing (Phase 2)
        max_holdings_dynamic: Maximum holdings in strong bull regime (default 80)

    Returns:
        Dict with performance metrics and trade history
    """
    print(f"\n{'=' * 80}")
    print(f"KAVASTU STRATEGY BACKTEST")
    print(f"{'=' * 80}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: {initial_capital:,.0f} SEK")
    print(f"Stock Universe: {len(stocks)} stocks")
    print(f"Max Holdings: {max_holdings} stocks")
    print(f"Rebalance: {rebalance_frequency}")
    print(f"Transaction Cost: {transaction_cost * 100:.2f}%")

    # Phase 2.5 Features
    if use_conviction_weighting:
        print(f"\n🎯 Conviction Weighting ENABLED:")
        print(f"   Tier 1 (Top {conviction_tier1_count}): {conviction_tier1_weight}% of capital ({conviction_tier1_weight/conviction_tier1_count:.2f}% each)")
        print(f"   Tier 2 (Next {conviction_tier2_count}): {conviction_tier2_weight}% of capital ({conviction_tier2_weight/conviction_tier2_count:.2f}% each)")
        print(f"   Tier 3 (Remaining): {conviction_tier3_weight}% of capital (varies)")

    portfolio = Portfolio(initial_capital)

    # Generate rebalance dates
    rebalance_dates = generate_rebalance_dates(start_date, end_date, rebalance_frequency)
    print(f"\nRebalance Dates: {len(rebalance_dates)} periods")

    # Fetch dividend data for all stocks (Kavastu reinvests dividends)
    print(f"\n💰 Fetching dividend data for {len(stocks)} stocks...")
    dividend_data = fetch_dividend_data(stocks, start_date, end_date)
    dividend_paying_stocks = len(dividend_data)
    print(f"✅ Found {dividend_paying_stocks} dividend-paying stocks ({dividend_paying_stocks/len(stocks)*100:.0f}%)")

    # Track performance
    equity_curve = []
    trade_log = []
    prev_rebal_date = start_date

    # Fetch benchmark data (OMXS30)
    print(f"\n📊 Fetching benchmark data (OMXS30)...")
    benchmark_data = fetch_stock_data('^OMX', period='max')
    if benchmark_data is None or benchmark_data.empty:
        print("⚠️ Warning: Could not fetch benchmark data")
        benchmark_data = None

    # Main backtest loop
    for i, rebal_date in enumerate(rebalance_dates):
        print(f"\n{'─' * 80}")
        print(f"Rebalance {i+1}/{len(rebalance_dates)}: {rebal_date}")

        # Collect dividends from previous period
        period_dividends = portfolio.collect_dividends(dividend_data, prev_rebal_date, rebal_date)
        if period_dividends > 0:
            print(f"💰 Dividends collected: {period_dividends:,.0f} SEK (reinvested as cash)")

        # Check if year-end and apply ISK tax (once per year, at December 31)
        current_date = datetime.strptime(rebal_date, "%Y-%m-%d")
        prev_date = datetime.strptime(prev_rebal_date, "%Y-%m-%d")

        # If we've crossed into a new year, pay ISK tax for previous year
        if current_date.year > prev_date.year:
            # Calculate portfolio value before tax
            period_stocks_tax = fetch_historical_snapshot(stocks, prev_rebal_date)
            prices_before_tax = {ticker: df['Close'].iloc[-1]
                               for ticker, df in period_stocks_tax.items()
                               if not df.empty}
            value_before_tax = portfolio.get_total_value(prices_before_tax)

            # Pay ISK tax for previous year
            isk_tax_paid = portfolio.pay_isk_tax(value_before_tax, year=prev_date.year)
            if isk_tax_paid > 0:
                print(f"🏦 ISK Tax paid for {prev_date.year}: {isk_tax_paid:,.0f} SEK ({isk_tax_paid/value_before_tax*100:.3f}%)")

        # Fetch historical data up to this date
        period_stocks = fetch_historical_snapshot(stocks, rebal_date)

        if not period_stocks:
            print(f"⚠️ No data available for {rebal_date}")
            prev_rebal_date = rebal_date
            continue

        # Calculate current portfolio value
        current_prices = {ticker: df['Close'].iloc[-1]
                         for ticker, df in period_stocks.items()
                         if not df.empty}

        portfolio_value = portfolio.get_total_value(current_prices)

        print(f"Portfolio Value: {portfolio_value:,.0f} SEK")
        print(f"Cash: {portfolio.cash:,.0f} SEK ({portfolio.cash/portfolio_value*100:.1f}%)")
        print(f"Holdings: {portfolio.get_holdings_count()} stocks")

        # Record equity curve
        equity_curve.append({
            'date': rebal_date,
            'value': portfolio_value,
            'cash': portfolio.cash,
            'holdings': portfolio.get_holdings_count(),
            'dividends': portfolio.total_dividends
        })

        prev_rebal_date = rebal_date

        # Phase 2: Dynamic regime detection with adaptive portfolio sizing
        if use_dynamic_regime:
            # Calculate MAs for benchmark if not present
            if 'MA100' not in benchmark_data.columns:
                benchmark_data = calculate_ma50_ma200(benchmark_data)

            regime_info = get_market_regime_dynamic(benchmark_data, period_stocks, rebal_date)
            regime = regime_info['regime']
            target_holdings = regime_info['target_stocks']

            print(f"Market Regime: {regime} (score: {regime_info['regime_score']:.0f}/100)")
            print(f"  Index vs MA200: {regime_info['index_vs_ma200']:+.2f}%")
            print(f"  Market Breadth: {regime_info['breadth_pct']:.1f}% above MA200")
            print(f"  Volatility: {regime_info['volatility_percentile']:.0f}th percentile")
            print(f"  Target Holdings: {target_holdings} stocks")
        else:
            # Phase 1: Simple regime detection (backward compatible)
            regime = check_market_regime_historical(rebal_date)
            print(f"Market Regime: {regime.upper()}")

            # Determine target portfolio size based on regime
            if regime == 'bull':
                target_holdings = max_holdings  # 12-14 stocks
            elif regime == 'bear':
                target_holdings = 5  # 0-5 stocks, defensive
            else:
                target_holdings = 10  # 8-12 stocks, neutral

        # Apply tiered drawdown management (risk control)
        drawdown_pct, size_multiplier, risk_level = portfolio.get_drawdown_adjustment(current_prices)

        if drawdown_pct > 1:  # Only print if meaningful drawdown
            print(f"📉 Drawdown: {drawdown_pct:.1f}% | Risk Level: {risk_level} | Position Sizing: {size_multiplier*100:.0f}%")

        # Adjust target holdings based on drawdown
        adjusted_target = int(target_holdings * size_multiplier)

        if size_multiplier < 1.0:
            print(f"⚠️  Reducing positions from {target_holdings} to {adjusted_target} stocks due to drawdown")

        target_holdings = adjusted_target

        # Run screening on this date's data
        screened_stocks = screen_stocks_historical(period_stocks, rebal_date)

        if screened_stocks.empty:
            print(f"⚠️ No stocks passed screening")
            continue

        # Get top N stocks by score
        top_stocks = screened_stocks.head(target_holdings)
        target_tickers = set(top_stocks['ticker'].tolist())

        print(f"Top {len(target_tickers)} stocks: {', '.join(list(target_tickers)[:5])}...")

        # SELL: Exit holdings not in top stocks OR below MA200 (fire alarm)
        for ticker in list(portfolio.holdings.keys()):
            should_sell = False
            reason = ""

            if ticker not in target_tickers:
                should_sell = True
                reason = "Not in top stocks"
            elif ticker in period_stocks:
                df = period_stocks[ticker]
                df = calculate_ma50_ma200(df)
                current_price = df['Close'].iloc[-1]
                ma200 = df['MA200'].iloc[-1]

                if not pd.isna(ma200) and current_price < ma200:
                    should_sell = True
                    reason = "Below MA200 (fire alarm)"

            if should_sell:
                price = current_prices.get(ticker, 0)
                if price > 0:
                    portfolio.sell(ticker, price, transaction_cost)
                    trade_log.append({
                        'date': rebal_date,
                        'action': 'SELL',
                        'ticker': ticker,
                        'price': price,
                        'reason': reason
                    })
                    print(f"  SELL {ticker} @ {price:.2f} - {reason}")

        # BUY: Fill portfolio with top stocks (Kavastu 2-3% sizing)
        available_cash = portfolio.cash
        current_holdings = portfolio.get_holdings_count()
        positions_to_add = target_holdings - current_holdings

        if positions_to_add > 0 and available_cash > 0:
            total_portfolio_value = portfolio.get_total_value(current_prices)

            for stock_rank, (_, row) in enumerate(top_stocks.iterrows(), start=1):
                ticker = row['ticker']

                if ticker not in portfolio.holdings and ticker in current_prices:
                    price = current_prices[ticker]

                    # Phase 2.5: Conviction-weighted portfolio (mimics Kavastu's top 12 = 40%)
                    if use_conviction_weighting:
                        # Calculate conviction weight based on rank
                        conviction_weight = calculate_conviction_weight(
                            stock_rank, target_holdings,
                            conviction_tier1_count, conviction_tier1_weight,
                            conviction_tier2_count, conviction_tier2_weight,
                            conviction_tier3_weight
                        )

                        # Apply conviction weight to determine position size
                        shares, weight = calculate_position_size_conviction(
                            total_portfolio_value, price, conviction_weight
                        )
                        amount_per_stock = shares * price

                    # Phase 2: ATR-based position sizing (volatility-adjusted)
                    elif use_atr_sizing and ticker in period_stocks:
                        df = period_stocks[ticker]
                        # Calculate ATR if not present
                        if 'ATR' not in df.columns:
                            df['ATR'] = calculate_atr(df, period=14)

                        current_atr = df['ATR'].iloc[-1]
                        shares, weight, debug_info = calculate_position_size_atr(
                            total_portfolio_value, price, current_atr,
                            atr_account_risk, atr_multiplier
                        )
                        amount_per_stock = shares * price

                        # Log ATR sizing decision if debug info available
                        if debug_info['method'] == 'atr' and debug_info.get('constraint_applied'):
                            constraint_type = 'max' if debug_info['raw_weight'] > 5.0 else 'min'
                            # print(f"  ATR sizing: {ticker} constrained to {weight:.2f}% (raw: {debug_info['raw_weight']:.2f}%, {constraint_type} bound)")
                    else:
                        # Phase 1: Fixed 2.5% position sizing (backward compatible)
                        amount_per_stock = total_portfolio_value * 0.025

                    if portfolio.buy(ticker, amount_per_stock, price, transaction_cost):
                        trade_log.append({
                            'date': rebal_date,
                            'action': 'BUY',
                            'ticker': ticker,
                            'price': price,
                            'score': row['score']
                        })
                        print(f"  BUY {ticker} @ {price:.2f} (score: {row['score']:.1f})")

                if portfolio.get_holdings_count() >= target_holdings:
                    break

    # Final portfolio value
    final_date = rebalance_dates[-1]
    final_stocks = fetch_historical_snapshot(stocks, final_date)
    final_prices = {ticker: df['Close'].iloc[-1]
                   for ticker, df in final_stocks.items()
                   if not df.empty}
    final_value = portfolio.get_total_value(final_prices)

    print(f"\n{'=' * 80}")
    print(f"BACKTEST COMPLETE")
    print(f"{'=' * 80}")
    print(f"Final Portfolio Value: {final_value:,.0f} SEK")
    print(f"Total Return: {((final_value - initial_capital) / initial_capital * 100):.2f}%")
    print(f"\n💰 Dividend Summary:")
    print(f"   Total Dividends Collected: {portfolio.total_dividends:,.0f} SEK")
    print(f"   Dividend Yield (annual avg): {(portfolio.total_dividends / initial_capital) / ((datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days / 365.25) * 100:.2f}%")
    print(f"\n🏦 ISK Account Tax Summary:")
    print(f"   Total ISK Tax Paid: {portfolio.total_isk_tax:,.0f} SEK")
    print(f"   Average Tax Rate: {(portfolio.total_isk_tax / initial_capital) / ((datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days / 365.25) * 100:.3f}% per year")
    print(f"   Net Value (after ISK tax): {final_value:,.0f} SEK")
    print(f"   Note: ISK flat tax on value, NO capital gains tax on trades ✅")

    # Calculate metrics
    metrics = calculate_performance_metrics(
        equity_curve,
        initial_capital,
        start_date,
        end_date,
        total_dividends=portfolio.total_dividends,
        total_isk_tax=portfolio.total_isk_tax
    )

    # Calculate benchmark performance
    if benchmark_data is not None:
        benchmark_metrics = calculate_benchmark_performance(
            benchmark_data, start_date, end_date, initial_capital
        )
        metrics['benchmark'] = benchmark_metrics

    return {
        'metrics': metrics,
        'equity_curve': pd.DataFrame(equity_curve),
        'trade_log': pd.DataFrame(trade_log),
        'final_holdings': portfolio.holdings,
        'final_value': final_value
    }


def generate_rebalance_dates(start_date: str, end_date: str, frequency: str) -> List[str]:
    """Generate list of rebalance dates."""
    dates = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))

        if frequency == "monthly":
            # Move to first of next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        elif frequency == "weekly":
            current += timedelta(days=7)

    return dates


def fetch_historical_snapshot(stocks: List[str], as_of_date: str) -> Dict[str, pd.DataFrame]:
    """Fetch historical data up to a specific date."""
    # Calculate how much history we need (1 year for MA200)
    end_date = datetime.strptime(as_of_date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=400)  # Extra buffer for MA200

    stock_data = {}

    for ticker in stocks:
        df = fetch_stock_data(ticker, period='max')
        if df is not None and not df.empty:
            # Filter to only data up to as_of_date
            df = df[df.index <= as_of_date]
            if len(df) >= 200:  # Need enough for MA200
                stock_data[ticker] = df

    return stock_data


def check_market_regime_historical(as_of_date: str) -> str:
    """Check market regime as of historical date."""
    # Fetch OMXS30 up to this date
    index_data = fetch_stock_data('^OMX', period='max')
    if index_data is None or index_data.empty:
        return 'neutral'

    # Filter to date
    index_data = index_data[index_data.index <= as_of_date]
    if len(index_data) < 200:
        return 'neutral'

    # Calculate MA200
    index_data = calculate_ma50_ma200(index_data)
    current_price = index_data['Close'].iloc[-1]
    ma200 = index_data['MA200'].iloc[-1]

    if pd.isna(ma200):
        return 'neutral'

    return 'bull' if current_price > ma200 else 'bear'


def screen_stocks_historical(stock_data: Dict[str, pd.DataFrame], as_of_date: str) -> pd.DataFrame:
    """Run screening on historical data."""
    # Calculate benchmark returns
    benchmark_data = fetch_stock_data('^OMX', period='max')
    if benchmark_data is None or benchmark_data.empty:
        benchmark_returns = (0.0, 0.0)
    else:
        benchmark_data = benchmark_data[benchmark_data.index <= as_of_date]
        bench_3m = calculate_return(benchmark_data, 60)
        bench_6m = calculate_return(benchmark_data, 120)
        benchmark_returns = (bench_3m, bench_6m)

    results = []

    for ticker, df in stock_data.items():
        # Add MAs
        df = calculate_ma50_ma200(df)

        # Score the stock (without fundamentals for speed)
        metrics = calculate_stock_score(ticker, df, benchmark_returns, include_fundamentals=True)

        if metrics['score'] > 0:
            results.append(metrics)

    df_results = pd.DataFrame(results)

    if df_results.empty:
        return df_results

    # Filter: must be above MA200
    df_results = df_results[df_results['distance_ma200'] > 0]

    # Sort by score
    df_results = df_results.sort_values('score', ascending=False).reset_index(drop=True)

    return df_results


def calculate_return(df: pd.DataFrame, days: int) -> float:
    """Calculate return over N days."""
    if len(df) < days:
        return 0.0
    return ((df['Close'].iloc[-1] - df['Close'].iloc[-days]) / df['Close'].iloc[-days]) * 100


def calculate_performance_metrics(equity_curve: List[Dict], initial_capital: float,
                                 start_date: str, end_date: str, total_dividends: float = 0.0,
                                 total_isk_tax: float = 0.0) -> Dict:
    """Calculate performance metrics including dividend contribution and ISK tax impact."""
    if not equity_curve:
        return {}

    df = pd.DataFrame(equity_curve)

    # Total return (includes reinvested dividends, ISK tax already deducted from final_value)
    final_value = df['value'].iloc[-1]
    total_return = ((final_value - initial_capital) / initial_capital) * 100

    # Calculate price return (without dividends)
    price_return = ((final_value - total_dividends - initial_capital) / initial_capital) * 100
    dividend_return = (total_dividends / initial_capital) * 100

    # CAGR (net return after ISK tax - tax already deducted from portfolio value)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    years = (end - start).days / 365.25
    net_cagr = (((final_value / initial_capital) ** (1 / years)) - 1) * 100 if years > 0 else 0

    # Gross CAGR (what it would be without ISK tax)
    gross_final_value = final_value + total_isk_tax
    gross_cagr = (((gross_final_value / initial_capital) ** (1 / years)) - 1) * 100 if years > 0 else 0

    # Price-only CAGR (for comparison)
    price_only_value = final_value - total_dividends
    price_cagr = (((price_only_value / initial_capital) ** (1 / years)) - 1) * 100 if years > 0 else 0

    # ISK tax impact on CAGR
    isk_tax_drag = gross_cagr - net_cagr

    # Max Drawdown
    df['peak'] = df['value'].cummax()
    df['drawdown'] = (df['value'] - df['peak']) / df['peak'] * 100
    max_drawdown = df['drawdown'].min()

    # Volatility (annualized)
    df['returns'] = df['value'].pct_change()
    volatility = df['returns'].std() * np.sqrt(12)  # Monthly data, annualize

    # Sharpe Ratio (using net CAGR after ISK tax, assuming 2% risk-free rate)
    risk_free_rate = 0.02
    sharpe_ratio = (net_cagr / 100 - risk_free_rate) / volatility if volatility > 0 else 0

    return {
        'total_return': total_return,
        'price_return': price_return,
        'dividend_return': dividend_return,
        'cagr': net_cagr,  # Net CAGR after ISK tax
        'gross_cagr': gross_cagr,  # Gross CAGR before ISK tax
        'isk_tax_drag': isk_tax_drag,  # CAGR reduction due to ISK tax
        'price_cagr': price_cagr,
        'dividend_contribution': net_cagr - price_cagr,
        'max_drawdown': max_drawdown,
        'volatility': volatility * 100,
        'sharpe_ratio': sharpe_ratio,
        'final_value': final_value,
        'total_dividends': total_dividends,
        'total_isk_tax': total_isk_tax,
        'years': years
    }


def calculate_benchmark_performance(benchmark_data: pd.DataFrame, start_date: str,
                                   end_date: str, initial_capital: float) -> Dict:
    """Calculate buy-and-hold benchmark performance."""
    # Filter to date range
    benchmark_data = benchmark_data[(benchmark_data.index >= start_date) &
                                   (benchmark_data.index <= end_date)]

    if benchmark_data.empty:
        return {}

    start_price = benchmark_data['Close'].iloc[0]
    end_price = benchmark_data['Close'].iloc[-1]

    # Calculate return
    total_return = ((end_price - start_price) / start_price) * 100
    final_value = initial_capital * (1 + total_return / 100)

    # CAGR
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    years = (end - start).days / 365.25
    cagr = (((end_price / start_price) ** (1 / years)) - 1) * 100 if years > 0 else 0

    # Max drawdown
    benchmark_data['peak'] = benchmark_data['Close'].cummax()
    benchmark_data['drawdown'] = (benchmark_data['Close'] - benchmark_data['peak']) / benchmark_data['peak'] * 100
    max_drawdown = benchmark_data['drawdown'].min()

    return {
        'total_return': total_return,
        'cagr': cagr,
        'max_drawdown': max_drawdown,
        'final_value': final_value
    }
