#!/usr/bin/env python3
"""
Phase 2 Backtest - Kavastu Strategy with Advanced Features

Run backtests with ATR position sizing, indicator confirmation, dynamic regime, and conviction weighting.
Configuration managed via config/backtest_config.yaml

Usage:
    python scripts/backtest_kavastu_phase2.py             # Use config file
    python scripts/backtest_kavastu_phase2.py baseline    # Test Phase 1 baseline
    python scripts/backtest_kavastu_phase2.py atr         # Test ATR sizing only
    python scripts/backtest_kavastu_phase2.py conviction  # Test conviction weighting (Phase 2.5)
    python scripts/backtest_kavastu_phase2.py full        # Test all Phase 2 features
"""

import sys
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.backtester import backtest_strategy
from src.stock_universe import get_all_swedish_stocks


def load_config(config_path: str = "config/backtest_config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_backtest(config: dict, test_mode: str = None):
    """
    Run backtest with specified configuration.

    Args:
        config: Configuration dictionary from YAML
        test_mode: Optional test mode ('baseline', 'atr', 'indicators', 'regime', 'full')
    """
    # Get stock universe
    print("Loading Swedish stock universe...")
    stocks = get_all_swedish_stocks()
    print(f"Loaded {len(stocks)} stocks\n")

    # Override feature flags based on test mode
    if test_mode:
        if test_mode == 'baseline':
            print("🧪 TEST MODE: Phase 1 Baseline (no Phase 2 features)")
            config['features']['atr_sizing']['enabled'] = False
            config['features']['indicator_confirmation']['enabled'] = False
            config['features']['dynamic_regime']['enabled'] = False
            config['features']['conviction_weighting']['enabled'] = False
        elif test_mode == 'atr':
            print("🧪 TEST MODE: ATR Position Sizing Only")
            config['features']['atr_sizing']['enabled'] = True
            config['features']['indicator_confirmation']['enabled'] = False
            config['features']['dynamic_regime']['enabled'] = False
            config['features']['conviction_weighting']['enabled'] = False
        elif test_mode == 'conviction':
            print("🧪 TEST MODE: Conviction Weighting Only (Phase 2.5)")
            config['features']['atr_sizing']['enabled'] = False
            config['features']['indicator_confirmation']['enabled'] = False
            config['features']['dynamic_regime']['enabled'] = False
            config['features']['conviction_weighting']['enabled'] = True
        elif test_mode == 'indicators':
            print("🧪 TEST MODE: Indicator Confirmation Only")
            config['features']['atr_sizing']['enabled'] = False
            config['features']['indicator_confirmation']['enabled'] = True
            config['features']['dynamic_regime']['enabled'] = False
            config['features']['conviction_weighting']['enabled'] = False
        elif test_mode == 'regime':
            print("🧪 TEST MODE: Dynamic Regime Only")
            config['features']['atr_sizing']['enabled'] = False
            config['features']['indicator_confirmation']['enabled'] = False
            config['features']['dynamic_regime']['enabled'] = True
            config['features']['conviction_weighting']['enabled'] = False
        elif test_mode == 'full':
            print("🧪 TEST MODE: Full Phase 2 (all features enabled)")
            config['features']['atr_sizing']['enabled'] = True
            config['features']['indicator_confirmation']['enabled'] = True
            config['features']['dynamic_regime']['enabled'] = True
            config['features']['conviction_weighting']['enabled'] = True

    # Display configuration
    print(f"\n{'=' * 80}")
    print("PHASE 2 CONFIGURATION")
    print(f"{'=' * 80}")
    print(f"Period: {config['start_date']} to {config['end_date']}")
    print(f"Rebalance: {config['rebalance_frequency']}")
    print(f"Initial Capital: {config['initial_capital']:,.0f} SEK")
    print(f"\nPhase 2 Features:")
    print(f"  ATR Position Sizing: {'✅ ENABLED' if config['features']['atr_sizing']['enabled'] else '❌ DISABLED'}")
    if config['features']['atr_sizing']['enabled']:
        print(f"    - Risk per position: {config['features']['atr_sizing']['account_risk_pct']}%")
        print(f"    - ATR multiplier: {config['features']['atr_sizing']['atr_multiplier']}x")
        print(f"    - Weight range: {config['features']['atr_sizing']['min_weight']}-{config['features']['atr_sizing']['max_weight']}%")

    print(f"  Indicator Confirmation: {'✅ ENABLED' if config['features']['indicator_confirmation']['enabled'] else '❌ DISABLED'}")
    if config['features']['indicator_confirmation']['enabled']:
        print(f"    - RSI period: {config['features']['indicator_confirmation']['rsi_period']}")
        print(f"    - MACD: {config['features']['indicator_confirmation']['macd_fast']}/{config['features']['indicator_confirmation']['macd_slow']}/{config['features']['indicator_confirmation']['macd_signal']}")

    print(f"  Dynamic Regime: {'✅ ENABLED' if config['features']['dynamic_regime']['enabled'] else '❌ DISABLED'}")
    if config['features']['dynamic_regime']['enabled']:
        print(f"    - Strong Bull: {config['features']['dynamic_regime']['max_holdings_strong_bull']} stocks")
        print(f"    - Bull: {config['features']['dynamic_regime']['max_holdings_bull']} stocks")
        print(f"    - Neutral: {config['features']['dynamic_regime']['max_holdings_neutral']} stocks")
        print(f"    - Bear: {config['features']['dynamic_regime']['max_holdings_bear']} stocks")
        print(f"    - Panic: {config['features']['dynamic_regime']['min_holdings_panic']} stocks")

    print(f"  Conviction Weighting: {'✅ ENABLED' if config['features']['conviction_weighting']['enabled'] else '❌ DISABLED'}")
    if config['features']['conviction_weighting']['enabled']:
        tier1_pct = config['features']['conviction_weighting']['tier1_weight_pct']
        tier1_count = config['features']['conviction_weighting']['tier1_count']
        tier2_pct = config['features']['conviction_weighting']['tier2_weight_pct']
        tier2_count = config['features']['conviction_weighting']['tier2_count']
        tier3_pct = config['features']['conviction_weighting']['tier3_weight_pct']
        print(f"    - Tier 1 (Top {tier1_count}): {tier1_pct}% of capital ({tier1_pct/tier1_count:.2f}% each)")
        print(f"    - Tier 2 (Next {tier2_count}): {tier2_pct}% of capital ({tier2_pct/tier2_count:.2f}% each)")
        print(f"    - Tier 3 (Rest): {tier3_pct}% of capital (varies)")

    print(f"{'=' * 80}\n")

    # Run backtest
    results = backtest_strategy(
        stocks=stocks,
        start_date=config['start_date'],
        end_date=config['end_date'],
        initial_capital=config['initial_capital'],
        rebalance_frequency=config['rebalance_frequency'],
        max_holdings=config.get('max_holdings', 70),
        transaction_cost=config.get('transaction_cost', 0.0025),

        # Phase 2: ATR position sizing
        use_atr_sizing=config['features']['atr_sizing']['enabled'],
        atr_account_risk=config['features']['atr_sizing'].get('account_risk_pct', 1.0),
        atr_multiplier=config['features']['atr_sizing'].get('atr_multiplier', 2.0),

        # Phase 2: Dynamic regime detection
        use_dynamic_regime=config['features']['dynamic_regime']['enabled'],
        max_holdings_dynamic=config['features']['dynamic_regime'].get('max_holdings_strong_bull', 80),

        # Phase 2.5: Conviction weighting
        use_conviction_weighting=config['features']['conviction_weighting']['enabled'],
        conviction_tier1_count=config['features']['conviction_weighting'].get('tier1_count', 15),
        conviction_tier1_weight=config['features']['conviction_weighting'].get('tier1_weight_pct', 50.0),
        conviction_tier2_count=config['features']['conviction_weighting'].get('tier2_count', 25),
        conviction_tier2_weight=config['features']['conviction_weighting'].get('tier2_weight_pct', 35.0),
        conviction_tier3_weight=config['features']['conviction_weighting'].get('tier3_weight_pct', 15.0)
    )

    # Display results
    print(f"\n{'=' * 80}")
    print("PHASE 2 BACKTEST RESULTS")
    print(f"{'=' * 80}")

    metrics = results['metrics']
    print(f"\n📊 Performance Metrics:")
    print(f"   CAGR: {metrics['cagr']:.2f}%")
    print(f"   Total Return: {metrics['total_return']:.2f}%")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")

    print(f"\n💰 Dividend Summary:")
    print(f"   Total Dividends: {metrics.get('total_dividends', 0):,.0f} SEK")
    print(f"   Dividend Yield: {metrics.get('dividend_yield', 0):.2f}% annually")

    print(f"\n🏦 ISK Tax Summary:")
    print(f"   Total ISK Tax: {metrics.get('total_isk_tax', 0):,.0f} SEK")
    print(f"   Avg Tax Rate: {metrics.get('isk_tax_rate', 0):.3f}% per year")

    if 'benchmark' in metrics:
        bench = metrics['benchmark']
        print(f"\n📈 vs OMXS30:")
        print(f"   Benchmark CAGR: {bench['cagr']:.2f}%")
        print(f"   Alpha: {metrics['cagr'] - bench['cagr']:+.2f}%")
        print(f"   Outperformance: {((1 + metrics['total_return']/100) / (1 + bench['total_return']/100) - 1) * 100:.1f}%")

    print(f"\n🎯 Phase 2 Target: 18-22% CAGR")
    if metrics['cagr'] >= 18:
        print(f"   ✅ TARGET ACHIEVED! ({metrics['cagr']:.2f}% CAGR)")
    else:
        gap = 18 - metrics['cagr']
        print(f"   Gap to target: {gap:.2f}%")

    print(f"\n{'=' * 80}\n")

    return results


def main():
    """Main entry point."""
    # Load configuration
    config = load_config()

    # Check for test mode argument
    test_mode = None
    if len(sys.argv) > 1:
        test_mode = sys.argv[1].lower()
        valid_modes = ['baseline', 'atr', 'conviction', 'indicators', 'regime', 'full']
        if test_mode not in valid_modes:
            print(f"❌ Invalid test mode: {test_mode}")
            print(f"Valid modes: {', '.join(valid_modes)}")
            sys.exit(1)

    # Run backtest
    try:
        results = run_backtest(config, test_mode)

        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        mode_suffix = f"_{test_mode}" if test_mode else "_config"
        equity_file = output_dir / f"equity_curve_phase2{mode_suffix}.csv"
        trades_file = output_dir / f"trade_log_phase2{mode_suffix}.csv"

        results['equity_curve'].to_csv(equity_file, index=False)
        results['trade_log'].to_csv(trades_file, index=False)

        print(f"💾 Results saved:")
        print(f"   Equity curve: {equity_file}")
        print(f"   Trade log: {trades_file}")

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
