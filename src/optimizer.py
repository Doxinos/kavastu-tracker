"""MA Parameter Optimizer - Walk-forward optimization for MA periods.

Feature 4: Test different MA parameter sets to find optimal values.
Uses walk-forward analysis to avoid overfitting.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from .backtester import backtest_strategy
from .ma_calculator import calculate_ma_custom


def walk_forward_optimization(
    stocks: List[str],
    start_date: str,
    end_date: str,
    train_months: int = 12,
    test_months: int = 6,
    ma_parameter_sets: List[Tuple[int, int, int]] = None,
    initial_capital: float = 100000,
    rebalance_frequency: str = "weekly"
) -> Dict:
    """
    Walk-forward optimization of MA parameters.

    Process:
    1. Split time into overlapping train/test windows
    2. For each window:
       - Train: Test all parameter sets, pick best by composite score
       - Test: Validate best parameters on unseen data
    3. Aggregate results to identify most robust parameters

    Args:
        stocks: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        train_months: Training window size (default 12)
        test_months: Testing window size (default 6)
        ma_parameter_sets: List of (fast, medium, slow) MA periods to test
                          Default: [(40,100,180), (50,100,200), (60,120,220), (50,120,240)]
        initial_capital: Starting capital
        rebalance_frequency: "weekly" or "monthly"

    Returns:
        Dict with:
        - 'best_parameters': Tuple of best MA periods
        - 'parameter_performance': Dict mapping parameters -> list of test CAGRs
        - 'windows': List of train/test window results
        - 'summary_stats': Aggregate statistics
    """
    if ma_parameter_sets is None:
        ma_parameter_sets = [
            (40, 100, 180),   # Faster reactions
            (50, 100, 200),   # Default (current)
            (60, 120, 220),   # Slower, more stable
            (50, 120, 240)    # Hybrid approach
        ]

    print(f"🔍 Walk-Forward Optimization")
    print(f"   Period: {start_date} to {end_date}")
    print(f"   Train/Test: {train_months}/{test_months} months")
    print(f"   Testing {len(ma_parameter_sets)} parameter sets:")
    for params in ma_parameter_sets:
        print(f"      MA({params[0]}, {params[1]}, {params[2]})")
    print()

    # Generate train/test windows
    windows = generate_train_test_windows(start_date, end_date, train_months, test_months)
    print(f"   Generated {len(windows)} train/test windows\n")

    # Track performance for each parameter set
    parameter_performance = {params: [] for params in ma_parameter_sets}
    window_results = []

    for i, window in enumerate(windows):
        print(f"📊 Window {i+1}/{len(windows)}")
        print(f"   Train: {window['train_start']} to {window['train_end']}")
        print(f"   Test:  {window['test_start']} to {window['test_end']}")

        # Phase 1: Train - test all parameters
        train_results = {}
        for params in ma_parameter_sets:
            print(f"      Testing MA({params[0]}, {params[1]}, {params[2]})...", end=" ")

            result = backtest_strategy_with_params(
                stocks=stocks,
                start_date=window['train_start'],
                end_date=window['train_end'],
                ma_params=params,
                initial_capital=initial_capital,
                rebalance_frequency=rebalance_frequency
            )

            metrics = result['metrics']
            cagr = metrics['cagr']
            sharpe = metrics['sharpe_ratio']
            max_dd = metrics['max_drawdown']

            # Composite score: prioritize CAGR, reward Sharpe, penalize drawdown
            score = cagr * 0.7 + sharpe * 5 - abs(max_dd) * 0.3

            train_results[params] = {
                'cagr': cagr,
                'sharpe': sharpe,
                'max_drawdown': max_dd,
                'score': score
            }

            print(f"CAGR: {cagr:.2f}%, Score: {score:.2f}")

        # Select best parameters based on training
        best_params = max(train_results.keys(), key=lambda p: train_results[p]['score'])
        best_score = train_results[best_params]['score']
        print(f"\n   ✅ Best in training: MA({best_params[0]}, {best_params[1]}, {best_params[2]}) (score: {best_score:.2f})")

        # Phase 2: Test - validate on unseen data
        print(f"   🧪 Testing on validation period...")
        test_result = backtest_strategy_with_params(
            stocks=stocks,
            start_date=window['test_start'],
            end_date=window['test_end'],
            ma_params=best_params,
            initial_capital=initial_capital,
            rebalance_frequency=rebalance_frequency
        )

        test_cagr = test_result['metrics']['cagr']
        test_sharpe = test_result['metrics']['sharpe_ratio']
        parameter_performance[best_params].append(test_cagr)

        print(f"   📈 Test CAGR: {test_cagr:.2f}% (Sharpe: {test_sharpe:.2f})\n")

        window_results.append({
            'window': i + 1,
            'train_results': train_results,
            'best_params': best_params,
            'test_cagr': test_cagr,
            'test_sharpe': test_sharpe
        })

    # Aggregate results
    print(f"\n{'='*80}")
    print("OPTIMIZATION RESULTS")
    print(f"{'='*80}\n")

    avg_performance = {}
    for params, test_cagrs in parameter_performance.items():
        if test_cagrs:
            avg_cagr = np.mean(test_cagrs)
            std_cagr = np.std(test_cagrs)
            consistency = len(test_cagrs)  # How often was this chosen?
            avg_performance[params] = {
                'avg_cagr': avg_cagr,
                'std_cagr': std_cagr,
                'consistency': consistency,
                'test_cagrs': test_cagrs
            }

            print(f"MA({params[0]}, {params[1]}, {params[2]}):")
            print(f"   Avg Test CAGR: {avg_cagr:.2f}% ± {std_cagr:.2f}%")
            print(f"   Selected: {consistency}/{len(windows)} times")
            print()

    # Identify best overall parameters
    best_overall = max(
        avg_performance.keys(),
        key=lambda p: avg_performance[p]['avg_cagr']
    )

    print(f"🏆 Best Overall Parameters: MA({best_overall[0]}, {best_overall[1]}, {best_overall[2]})")
    print(f"   Average CAGR: {avg_performance[best_overall]['avg_cagr']:.2f}%")
    print(f"   Consistency: {avg_performance[best_overall]['consistency']}/{len(windows)} windows")
    print(f"{'='*80}\n")

    return {
        'best_parameters': best_overall,
        'parameter_performance': parameter_performance,
        'avg_performance': avg_performance,
        'windows': window_results,
        'summary_stats': {
            'total_windows': len(windows),
            'best_avg_cagr': avg_performance[best_overall]['avg_cagr'],
            'best_std_cagr': avg_performance[best_overall]['std_cagr'],
            'best_consistency': avg_performance[best_overall]['consistency']
        }
    }


def generate_train_test_windows(
    start_date: str,
    end_date: str,
    train_months: int,
    test_months: int
) -> List[Dict]:
    """
    Generate overlapping train/test windows for walk-forward analysis.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        train_months: Training window size in months
        test_months: Testing window size in months

    Returns:
        List of dicts with train_start, train_end, test_start, test_end

    Example:
        With train=12, test=6:
        Window 1: Train [2020-01 to 2021-01], Test [2021-01 to 2021-07]
        Window 2: Train [2020-07 to 2021-07], Test [2021-07 to 2022-01]
        ...
    """
    windows = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while True:
        train_start = current
        train_end = train_start + timedelta(days=train_months * 30)
        test_start = train_end
        test_end = test_start + timedelta(days=test_months * 30)

        # Stop if test window exceeds end date
        if test_end > end:
            break

        windows.append({
            'train_start': train_start.strftime("%Y-%m-%d"),
            'train_end': train_end.strftime("%Y-%m-%d"),
            'test_start': test_start.strftime("%Y-%m-%d"),
            'test_end': test_end.strftime("%Y-%m-%d")
        })

        # Slide forward by test_months (creates overlap)
        current = test_start

    return windows


def backtest_strategy_with_params(
    stocks: List[str],
    start_date: str,
    end_date: str,
    ma_params: Tuple[int, int, int],
    initial_capital: float = 100000,
    rebalance_frequency: str = "weekly"
) -> Dict:
    """
    Run backtest with custom MA parameters.

    This is a wrapper around backtest_strategy() that:
    1. Temporarily overrides MA calculation to use custom periods
    2. Runs the backtest
    3. Returns results

    Args:
        stocks: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        ma_params: Tuple of (fast, medium, slow) MA periods
        initial_capital: Starting capital
        rebalance_frequency: "weekly" or "monthly"

    Returns:
        Backtest results dict (same as backtest_strategy())

    Note:
        Currently uses standard backtest_strategy() with default (50,100,200).
        TODO: Modify backtester to accept ma_params parameter to enable custom periods.
              For now, this returns standard results as placeholder.
    """
    # TODO: Integrate calculate_ma_custom() into backtester
    # For now, run with default parameters as placeholder
    # Once backtester supports ma_params, this will use custom periods

    results = backtest_strategy(
        stocks=stocks,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        rebalance_frequency=rebalance_frequency,
        max_holdings=70,
        transaction_cost=0.0025,
        use_atr_sizing=False,
        use_dynamic_regime=False
    )

    return results


def compare_parameter_sets(
    stocks: List[str],
    start_date: str,
    end_date: str,
    parameter_sets: List[Tuple[int, int, int]],
    initial_capital: float = 100000
) -> pd.DataFrame:
    """
    Simple comparison of different MA parameter sets (no walk-forward).

    Useful for quick testing before full optimization.

    Args:
        stocks: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        parameter_sets: List of (fast, medium, slow) tuples
        initial_capital: Starting capital

    Returns:
        DataFrame with comparison results
    """
    results = []

    for params in parameter_sets:
        print(f"Testing MA({params[0]}, {params[1]}, {params[2]})...")

        result = backtest_strategy_with_params(
            stocks=stocks,
            start_date=start_date,
            end_date=end_date,
            ma_params=params,
            initial_capital=initial_capital
        )

        metrics = result['metrics']
        results.append({
            'MA_Fast': params[0],
            'MA_Medium': params[1],
            'MA_Slow': params[2],
            'CAGR': metrics['cagr'],
            'Sharpe': metrics['sharpe_ratio'],
            'Max_DD': metrics['max_drawdown'],
            'Total_Return': metrics['total_return']
        })

    df = pd.DataFrame(results)
    df = df.sort_values('CAGR', ascending=False).reset_index(drop=True)

    print(f"\n{'='*80}")
    print("PARAMETER COMPARISON")
    print(f"{'='*80}")
    print(df.to_string(index=False))
    print(f"{'='*80}\n")

    return df


if __name__ == "__main__":
    """
    Example usage of optimizer.

    Usage:
        python -m src.optimizer
    """
    from .stock_universe import get_all_swedish_stocks

    print("MA Parameter Optimizer - Feature 4")
    print("="*80)

    # Load stock universe
    stocks = get_all_swedish_stocks()
    print(f"Loaded {len(stocks)} Swedish stocks\n")

    # Quick comparison (no walk-forward)
    print("1. Quick Comparison Test")
    print("-" * 80)
    parameter_sets = [
        (40, 100, 180),
        (50, 100, 200),
        (60, 120, 220)
    ]

    compare_parameter_sets(
        stocks=stocks,
        start_date="2024-01-01",
        end_date="2025-12-31",
        parameter_sets=parameter_sets
    )

    # Full walk-forward optimization
    print("\n2. Walk-Forward Optimization")
    print("-" * 80)
    results = walk_forward_optimization(
        stocks=stocks,
        start_date="2023-01-01",
        end_date="2026-01-31",
        train_months=12,
        test_months=6
    )

    print(f"\n🎯 Recommended MA Parameters: {results['best_parameters']}")
