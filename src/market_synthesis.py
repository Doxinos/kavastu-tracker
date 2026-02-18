"""
Market Synthesis - Cross-reference MarketMate analysis with our technical model.

When a new MarketMate YouTube video arrives, this module compares their regime call,
stock picks, and signals against our own screener data and regime detection to produce
a unified alignment summary.
"""
from typing import Dict, List, Optional
from datetime import datetime
from .database import PortfolioDB
from .market_regime import get_market_regime


# Map MarketMate regime labels to a numeric scale for comparison
REGIME_SCALE = {
    'BULL': 2,
    'BULL_WITH_SHORT_TERM_PULLBACK': 1,
    'NEUTRAL': 0,
    'BEAR': -1,
    'UNKNOWN': 0,
    # Our regime labels
    'bull': 2,
    'bear': -1,
    'unknown': 0,
    'STRONG_BULL': 3,
    'PANIC': -2,
}


def generate_market_synthesis() -> Dict:
    """
    Cross-reference latest MarketMate YouTube analysis with our technical model.

    Returns a synthesis dict with:
    - regime_alignment: how the two views compare
    - overlapping_stocks: stocks both systems flag
    - conflicts: where the two systems disagree
    - portfolio_impact: actionable summary
    """
    with PortfolioDB() as db:
        # Get latest MarketMate YouTube analysis
        all_analyses = db.get_market_analyses(limit=30)
        mm_youtube = None
        for a in all_analyses:
            if a.get('source_type') == 'youtube' and a.get('regime'):
                mm_youtube = a
                break

        if not mm_youtube:
            return {
                'available': False,
                'reason': 'Ingen MarketMate-video analyserad ännu',
            }

        # Get latest MarketMate website buy signals
        mm_website = [a for a in all_analyses if a.get('source_type') == 'website']
        mm_buy_tickers = set()
        mm_sell_tickers = set()
        for a in mm_website:
            for sig in (a.get('buy_signals') or []):
                if sig.get('ticker'):
                    mm_buy_tickers.add(sig['ticker'])
            for sig in (a.get('sell_signals') or []):
                if sig.get('ticker'):
                    mm_sell_tickers.add(sig['ticker'])

        # Also get buy/sell from the YouTube video itself
        for sig in (mm_youtube.get('buy_signals') or []):
            if sig.get('ticker'):
                mm_buy_tickers.add(sig['ticker'])
        for sig in (mm_youtube.get('sell_signals') or []):
            if sig.get('ticker'):
                mm_sell_tickers.add(sig['ticker'])

        # Get our latest screener data (most recent week)
        screener_df = db.get_screener_history(weeks=1)
        our_top_stocks = {}
        our_hot_stocks = set()
        our_cold_stocks = set()

        if not screener_df.empty:
            # Get the latest date's results
            latest_date = screener_df['date'].max()
            latest = screener_df[screener_df['date'] == latest_date]

            for _, row in latest.iterrows():
                ticker = row['ticker']
                our_top_stocks[ticker] = {
                    'rank': row.get('rank', 0),
                    'score': row.get('score', 0),
                    'trending_score': row.get('trending_score', 0),
                    'trending_classification': row.get('trending_classification', ''),
                    'ma200_trend': row.get('ma200_trend', ''),
                }
                if row.get('trending_classification') == 'HOT':
                    our_hot_stocks.add(ticker)
                elif row.get('trending_classification') == 'COLD':
                    our_cold_stocks.add(ticker)

    # Get our live regime
    our_regime = get_market_regime()

    # === 1. REGIME ALIGNMENT ===
    mm_regime = mm_youtube.get('regime', 'UNKNOWN')
    our_regime_label = our_regime.get('regime', 'unknown')

    mm_score = REGIME_SCALE.get(mm_regime, 0)
    our_score = REGIME_SCALE.get(our_regime_label, 0)
    score_diff = abs(mm_score - our_score)

    if score_diff == 0:
        alignment = 'STRONG'
        alignment_label = 'Samstämmig'
        alignment_description = f'Båda systemen ser {_regime_swedish(mm_regime)}.'
    elif score_diff == 1:
        alignment = 'MODERATE'
        alignment_label = 'Delvis samstämmig'
        if mm_score < our_score:
            alignment_description = f'MarketMate är mer försiktig ({_regime_swedish(mm_regime)}) än vår modell ({_regime_swedish(our_regime_label)}).'
        else:
            alignment_description = f'MarketMate är mer positiv ({_regime_swedish(mm_regime)}) än vår modell ({_regime_swedish(our_regime_label)}).'
    else:
        alignment = 'DIVERGENT'
        alignment_label = 'Avvikande'
        alignment_description = f'MarketMate ser {_regime_swedish(mm_regime)} medan vår modell ser {_regime_swedish(our_regime_label)}. Stor skillnad - var försiktig!'

    # === 2. STOCK OVERLAP ===
    mm_all_tickers = set(mm_youtube.get('tickers_mentioned', []))
    mm_all_tickers.update(mm_buy_tickers)

    # Stocks MarketMate likes that we also rank high
    double_confirmed = []
    for ticker in mm_buy_tickers:
        if ticker in our_top_stocks:
            info = our_top_stocks[ticker]
            double_confirmed.append({
                'ticker': ticker,
                'our_score': info['score'],
                'our_rank': info['rank'],
                'our_trending': info['trending_classification'],
                'mm_signal': 'BUY',
            })

    # Stocks MarketMate mentions that we also track
    mentioned_overlap = []
    for ticker in mm_all_tickers:
        if ticker in our_top_stocks and ticker not in mm_buy_tickers:
            info = our_top_stocks[ticker]
            mentioned_overlap.append({
                'ticker': ticker,
                'our_score': info['score'],
                'our_rank': info['rank'],
                'our_trending': info['trending_classification'],
            })

    # === 3. CONFLICTS ===
    conflicts = []

    # MarketMate buys but we rate COLD
    for ticker in mm_buy_tickers:
        if ticker in our_cold_stocks:
            info = our_top_stocks[ticker]
            conflicts.append({
                'ticker': ticker,
                'type': 'MM_BUY_WE_COLD',
                'description': f'MarketMate köper {ticker} men vår modell klassar den som COLD ({info["score"]:.0f}/130)',
            })

    # MarketMate sells but we rate HOT
    for ticker in mm_sell_tickers:
        if ticker in our_hot_stocks:
            info = our_top_stocks[ticker]
            conflicts.append({
                'ticker': ticker,
                'type': 'MM_SELL_WE_HOT',
                'description': f'MarketMate säljer/shortar {ticker} men vår modell klassar den som HOT ({info["score"]:.0f}/130)',
            })

    # === 4. PORTFOLIO IMPACT ===
    impact_points = []

    # Regime-based advice
    if alignment == 'STRONG' and mm_score >= 1:
        impact_points.append('Båda systemen är positiva - håll nuvarande exponering eller öka.')
    elif alignment == 'STRONG' and mm_score <= -1:
        impact_points.append('Båda systemen varnar - reducera exponering och öka kassa.')
    elif mm_score < our_score:
        impact_points.append(f'MarketMate mer försiktig - överväg att höja kassanivån något.')
    elif mm_score > our_score:
        impact_points.append(f'MarketMate mer positiv - våra tekniska signaler hänger inte med ännu.')

    # Short-term pullback warning
    if mm_regime == 'BULL_WITH_SHORT_TERM_PULLBACK':
        impact_points.append('MarketMate flaggar för rekyl 3-5% på kort sikt - undvik att köpa precis nu, vänta på dippen.')

    # Double-confirmed stocks
    if double_confirmed:
        tickers_str = ', '.join([d['ticker'] for d in double_confirmed])
        impact_points.append(f'Dubbelbekräftade köp: {tickers_str} - starkaste signalerna.')

    # Conflicts
    if conflicts:
        for c in conflicts:
            impact_points.append(f'Varning: {c["description"]}')

    # SP500 target from MarketMate
    targets = mm_youtube.get('targets', {})
    if targets.get('sp500_target'):
        impact_points.append(f'MarketMate S&P 500 target: {targets["sp500_target"]}')

    return {
        'available': True,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'mm_video_date': mm_youtube.get('date', ''),
        'mm_video_title': mm_youtube.get('title', ''),
        'mm_video_url': mm_youtube.get('url', ''),

        # Regime comparison
        'regime': {
            'mm_regime': mm_regime,
            'our_regime': our_regime_label,
            'mm_index_view': mm_youtube.get('summary', ''),
            'our_index_vs_ma200': our_regime.get('index_vs_ma200'),
            'alignment': alignment,
            'alignment_label': alignment_label,
            'alignment_description': alignment_description,
        },

        # Stock cross-reference
        'double_confirmed': double_confirmed,
        'mentioned_overlap': mentioned_overlap,
        'mm_buy_tickers': sorted(list(mm_buy_tickers)),
        'mm_sell_tickers': sorted(list(mm_sell_tickers)),
        'conflicts': conflicts,

        # Portfolio guidance
        'portfolio_impact': impact_points,

        # Raw targets from MarketMate
        'targets': targets,
    }


def _regime_swedish(regime: str) -> str:
    """Translate regime label to Swedish description."""
    translations = {
        'BULL': 'bull-marknad',
        'BULL_WITH_SHORT_TERM_PULLBACK': 'bull med väntad rekyl',
        'BEAR': 'bear-marknad',
        'NEUTRAL': 'neutral marknad',
        'UNKNOWN': 'okänd marknad',
        'STRONG_BULL': 'stark bull-marknad',
        'PANIC': 'panik/kris',
        'bull': 'bull-marknad',
        'bear': 'bear-marknad',
        'unknown': 'okänt läge',
    }
    return translations.get(regime, regime)
