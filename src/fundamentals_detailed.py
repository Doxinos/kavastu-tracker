"""Detailed fundamental analysis - Quarterly/yearly reports, cash flow, valuation."""
import yfinance as yf
import pandas as pd
from typing import Dict, Optional


def fetch_detailed_fundamentals(ticker: str) -> Dict[str, any]:
    """
    Fetch comprehensive fundamental data including quarterly reports.

    Returns detailed financials:
    - Income statement (revenue, profit, margins)
    - Balance sheet (assets, liabilities, equity)
    - Cash flow (operating, investing, financing)
    - Valuation ratios (P/E, P/S, P/B, PEG)
    - Growth metrics (YoY, QoQ)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get quarterly data
        quarterly_financials = stock.quarterly_financials
        quarterly_balance_sheet = stock.quarterly_balance_sheet
        quarterly_cashflow = stock.quarterly_cashflow

        fundamentals = {
            # Basic info
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap'),
            'currency': info.get('currency', 'SEK'),

            # Valuation Ratios
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'ps_ratio': info.get('priceToSalesTrailing12Months'),
            'pb_ratio': info.get('priceToBook'),
            'peg_ratio': info.get('pegRatio'),
            'ev_to_ebitda': info.get('enterpriseToEbitda'),

            # Profitability
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'gross_margin': info.get('grossMargins'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'roic': info.get('returnOnCapital'),

            # Growth
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'revenue_per_share': info.get('revenuePerShare'),
            'eps': info.get('trailingEps'),
            'eps_forward': info.get('forwardEps'),

            # Financial Health
            'current_ratio': info.get('currentRatio'),
            'quick_ratio': info.get('quickRatio'),
            'debt_to_equity': info.get('debtToEquity'),
            'total_debt': info.get('totalDebt'),
            'total_cash': info.get('totalCash'),
            'free_cashflow': info.get('freeCashflow'),
            'operating_cashflow': info.get('operatingCashflow'),

            # Quarterly Trends (if available)
            'quarterly_revenue_trend': None,
            'quarterly_earnings_trend': None,
            'quarterly_cashflow_trend': None,
        }

        # Calculate quarterly trends
        if quarterly_financials is not None and not quarterly_financials.empty:
            fundamentals['quarterly_revenue_trend'] = extract_quarterly_trend(
                quarterly_financials, 'Total Revenue'
            )
            fundamentals['quarterly_earnings_trend'] = extract_quarterly_trend(
                quarterly_financials, 'Net Income'
            )

        if quarterly_cashflow is not None and not quarterly_cashflow.empty:
            fundamentals['quarterly_cashflow_trend'] = extract_quarterly_trend(
                quarterly_cashflow, 'Operating Cash Flow'
            )

        return fundamentals

    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e)
        }


def extract_quarterly_trend(df: pd.DataFrame, metric_name: str) -> Optional[list]:
    """Extract last 4 quarters of a metric."""
    try:
        # Try different possible names for the metric
        possible_names = [
            metric_name,
            metric_name.replace(' ', ''),
            metric_name.title(),
            metric_name.upper()
        ]

        for name in possible_names:
            if name in df.index:
                values = df.loc[name].head(4).tolist()
                # Convert to billions for readability
                values = [v / 1e9 if v and not pd.isna(v) else None for v in values]
                return values

        return None
    except:
        return None


def format_detailed_fundamentals(fundamentals: Dict) -> str:
    """Format detailed fundamentals for display."""
    if 'error' in fundamentals:
        return f"Error fetching data: {fundamentals['error']}"

    output = []

    # Header
    output.append("=" * 80)
    output.append(f"FUNDAMENTAL ANALYSIS: {fundamentals['ticker']}")
    output.append("=" * 80)
    output.append(f"Company: {fundamentals.get('company_name', 'N/A')}")
    output.append(f"Sector: {fundamentals.get('sector', 'N/A')} | Industry: {fundamentals.get('industry', 'N/A')}")

    market_cap = fundamentals.get('market_cap')
    if market_cap:
        output.append(f"Market Cap: {market_cap / 1e9:.2f}B {fundamentals.get('currency', 'SEK')}")

    # Valuation
    output.append(f"\n{'─' * 80}")
    output.append("VALUATION RATIOS")
    output.append(f"{'─' * 80}")

    pe = fundamentals.get('pe_ratio')
    forward_pe = fundamentals.get('forward_pe')
    ps = fundamentals.get('ps_ratio')
    pb = fundamentals.get('pb_ratio')
    peg = fundamentals.get('peg_ratio')

    if pe: output.append(f"P/E Ratio (Trailing): {pe:.2f}")
    if forward_pe: output.append(f"P/E Ratio (Forward): {forward_pe:.2f}")
    if ps: output.append(f"P/S Ratio: {ps:.2f}")
    if pb: output.append(f"P/B Ratio: {pb:.2f}")
    if peg: output.append(f"PEG Ratio: {peg:.2f}")

    # Profitability
    output.append(f"\n{'─' * 80}")
    output.append("PROFITABILITY")
    output.append(f"{'─' * 80}")

    profit_margin = fundamentals.get('profit_margin')
    operating_margin = fundamentals.get('operating_margin')
    gross_margin = fundamentals.get('gross_margin')
    roe = fundamentals.get('roe')
    roa = fundamentals.get('roa')

    if profit_margin: output.append(f"Profit Margin: {profit_margin * 100:.2f}%")
    if operating_margin: output.append(f"Operating Margin: {operating_margin * 100:.2f}%")
    if gross_margin: output.append(f"Gross Margin: {gross_margin * 100:.2f}%")
    if roe: output.append(f"ROE (Return on Equity): {roe * 100:.2f}%")
    if roa: output.append(f"ROA (Return on Assets): {roa * 100:.2f}%")

    # Growth
    output.append(f"\n{'─' * 80}")
    output.append("GROWTH")
    output.append(f"{'─' * 80}")

    rev_growth = fundamentals.get('revenue_growth')
    earnings_growth = fundamentals.get('earnings_growth')
    eps = fundamentals.get('eps')

    if rev_growth: output.append(f"Revenue Growth (YoY): {rev_growth * 100:+.2f}%")
    if earnings_growth: output.append(f"Earnings Growth (YoY): {earnings_growth * 100:+.2f}%")
    if eps: output.append(f"EPS (Earnings Per Share): {eps:.2f}")

    # Financial Health
    output.append(f"\n{'─' * 80}")
    output.append("FINANCIAL HEALTH")
    output.append(f"{'─' * 80}")

    current_ratio = fundamentals.get('current_ratio')
    debt_to_equity = fundamentals.get('debt_to_equity')
    total_cash = fundamentals.get('total_cash')
    free_cashflow = fundamentals.get('free_cashflow')

    if current_ratio: output.append(f"Current Ratio: {current_ratio:.2f}")
    if debt_to_equity: output.append(f"Debt/Equity: {debt_to_equity:.2f}")
    if total_cash: output.append(f"Total Cash: {total_cash / 1e9:.2f}B")
    if free_cashflow: output.append(f"Free Cash Flow: {free_cashflow / 1e9:.2f}B")

    # Quarterly Trends
    quarterly_rev = fundamentals.get('quarterly_revenue_trend')
    quarterly_earnings = fundamentals.get('quarterly_earnings_trend')
    quarterly_cf = fundamentals.get('quarterly_cashflow_trend')

    if quarterly_rev or quarterly_earnings or quarterly_cf:
        output.append(f"\n{'─' * 80}")
        output.append("QUARTERLY TRENDS (Last 4 Quarters, in Billions)")
        output.append(f"{'─' * 80}")

        if quarterly_rev:
            values = ' → '.join([f"{v:.2f}B" if v else "N/A" for v in quarterly_rev])
            output.append(f"Revenue: {values}")

        if quarterly_earnings:
            values = ' → '.join([f"{v:.2f}B" if v else "N/A" for v in quarterly_earnings])
            output.append(f"Net Income: {values}")

        if quarterly_cf:
            values = ' → '.join([f"{v:.2f}B" if v else "N/A" for v in quarterly_cf])
            output.append(f"Operating Cash Flow: {values}")

    return "\n".join(output)


def compare_fundamentals(tickers: list) -> pd.DataFrame:
    """
    Compare fundamentals across multiple stocks.

    Returns DataFrame with key metrics for comparison.
    """
    comparison = []

    for ticker in tickers:
        fund = fetch_detailed_fundamentals(ticker)

        if 'error' not in fund:
            comparison.append({
                'Ticker': ticker,
                'P/E': fund.get('pe_ratio'),
                'P/S': fund.get('ps_ratio'),
                'P/B': fund.get('pb_ratio'),
                'Profit Margin': fund.get('profit_margin'),
                'ROE': fund.get('roe'),
                'Revenue Growth': fund.get('revenue_growth'),
                'Debt/Equity': fund.get('debt_to_equity'),
                'Free CF (B)': fund.get('free_cashflow', 0) / 1e9 if fund.get('free_cashflow') else None
            })

    return pd.DataFrame(comparison)


if __name__ == "__main__":
    # Test the module
    print("Testing detailed fundamentals...\n")

    test_stocks = ['VOLV-B.ST', 'ERIC-B.ST', 'ABB.ST']

    for ticker in test_stocks:
        print(f"\n{'=' * 80}")
        fundamentals = fetch_detailed_fundamentals(ticker)
        print(format_detailed_fundamentals(fundamentals))

    print(f"\n{'=' * 80}")
    print("COMPARISON TABLE")
    print(f"{'=' * 80}")
    comparison = compare_fundamentals(test_stocks)
    print(comparison.to_string(index=False))
