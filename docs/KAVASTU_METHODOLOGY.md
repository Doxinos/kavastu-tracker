# Kavastu Methodology - Detailed Analysis

## Overview
Arne "Kavastu" Talving's trend-following strategy with AI/ML enhancements via NeuroQuant.

## Core Strategy Principles

### Primary Indicator: MA200 as "Fire Alarm"
- **Long-term trend filter**: MA200 (200-day simple moving average)
- **Fire alarm concept**: Price < MA200 → Warning signal, consider reducing/selling
- **Not a strict crossover system**: Focus on position relative to MA200 + momentum

### Secondary Indicator: MA50
- **Short-term momentum**: 50-day moving average
- **Confirmation tool**: MA50 > MA200 indicates stronger trend
- **Golden Cross**: MA50 crosses above MA200 → Accelerating uptrend
- **Death Cross**: MA50 crosses below MA200 → Weakening trend, reduce exposure

## Buy Signals

### Primary Buy Criteria
1. **Price > MA200** (required)
2. **MA200 rising** (not flat or falling)
3. **Strong fundamentals**:
   - Growing revenue (QoQ/YoY)
   - Growing profits
   - High quality (ROE, low debt)
4. **Only buy in bull trends**

### Secondary Confirmation (MA50)
- **MA50 > MA200**: Short trend above long trend
- **Golden Cross**: MA50 crosses above MA200 (confirms accelerating uptrend)
- **Momentum check**: Strengthens buy conviction

### Position Sizing & Portfolio Structure

**Kavastu maintains TWO portfolio concepts:**

1. **Helportföljen (Full Portfolio)** - 60-80+ stocks
   - His COMPLETE personal portfolio
   - Each position: Max 2-3% of total value
   - Example: 67 stocks (Aug 2025), 81 stocks (Jan 2025)
   - Dynamically adjusted weekly ("rensa det svaga")
   - Provides broad diversification and risk spreading

2. **Basportföljen (Base Portfolio)** - 12-14 stocks
   - His PUBLIC "A-team" favorites shared annually
   - Top momentum picks from the full portfolio
   - ~40% of total portfolio weight (~3-4% each)
   - Examples (2025): AAK, Lagercrantz, Mycronic, etc.
   - Marketing/educational subset, not his entire portfolio

**Key Insight:** The public "12-14 stocks" is just his highlighted picks.
His actual portfolio has 60-80+ stocks with 2-3% sizing each.

## Sell Signals

### Primary Sell Criteria
1. **Price < MA200**:
   - "Don't add more"
   - "Consider selling" (rebalance)
   - Protect capital
2. **MA200 falling**: Weakening long-term trend

### Secondary Confirmation (MA50)
- **MA50 < MA200**: Short trend below long trend
- **Death Cross**: MA50 crosses below MA200
- **Signal**: Reduce or exit position

### Market-Level Sell Signal
- **OMXSPI < MA200**:
  - Market in bear territory
  - Go liquid (80%+ cash)
  - Defensive positioning (0-5 stocks)

## Portfolio Management & Rotation

### Weekly Rotation Strategy
**Core Philosophy:** Continuous momentum capture through active rotation

Kavastu doesn't hold stocks statically. Instead, he rotates weekly to keep the portfolio aligned with the strongest trends. This is the key difference from passive strategies.

**Rotation in Practice:**
- **Frequency**: Weekly Sunday reviews (sometimes daily monitoring)
- **Full portfolio**: All 60-80+ stocks analyzed
- **Top holdings**: The 12-14 strongest (basportfölj) can change within a month
- **Criterion**: Swap weak (below MA200, underperforming) for strong (rising trends)
- **Result**: Portfolio stays overweight winners, underweight losers

**Example:**
- January 2025: Basportfölj includes AAK, Lagercrantz, Mycronic
- February 2025: "Kan se annorlunda ut om någon månad" (can look different in a month)
- If any top holding loses momentum → swap for stronger candidate
- This keeps the 40% basportfölj weight in the strongest stocks

### Weekly Review Process ("Rensa det svaga")
Kavastu reviews his FULL 60-80+ stock portfolio every week:

1. **Analyze all holdings**: Check trend (MA200) and momentum for each stock
2. **Identify weak**: Find stocks that:
   - Dropped below MA200 (fire alarm)
   - Underperforming index
   - Lost momentum/trend strength
3. **Swap for strong**: Replace weak stocks with stronger candidates
4. **Continuous rotation**: Top 12-14 "basportfölj" can change monthly
5. **Monday execution**: Execute trades Monday morning

**Key principle:** "Finns det ingen styrka byter jag till aktier där det finns styrka"
("If there's no strength, I switch to stocks where there is strength")

### Market Regimes
Adjust full portfolio size (60-80 stocks) based on market conditions:

1. **Bull Market** (>70% of universe above MA200):
   - Fully invested: 60-80 stocks (2-3% each)
   - Top 12-14 basportfölj at ~3-4% each (~40% weight)
   - Aggressive positioning
   - Continuous rotation to strongest stocks

2. **Neutral Market** (30-70% above MA200):
   - Moderate: 40-60 stocks
   - Selective buying
   - Monitor closely
   - Higher cash allocation (20-30%)

3. **Bear Market** (<30% above MA200):
   - Defensive: 0-20 stocks (only strongest survivors)
   - 70-90%+ cash
   - Capital preservation mode
   - Wait for bull market return

## AI/ML Enhancement (NeuroQuant)

### Data Processing
- **Large-scale analysis**: Revenue, profit, macro data
- **Growth calculations**: QoQ/YoY revenue growth
- **Noise filtering**: Remove false signals
- **Helicopter view**: Overall market perspective
- **Time savings**: vs manual text-tv screening

### Backtesting
- **Historical validation**: Test MA200/momentum rules across market cycles
- **Optimization**: Find best parameters for different conditions
- **Risk metrics**: Sharpe ratio, max drawdown, win rate

### Signal Generation
- **Trend & Trade Range models**: Equilibrium trend + momentum
- **Buy/sell levels**: Precise entry/exit points
- **Timing enhancement**: Complements MA200 for better timing

### Risk Management
- **Turning point detection**: ML identifies market reversals
- **Volatility analysis**: Adjust position sizing
- **Capital protection**: Early warning in bear markets

## Historical Backtesting Results (Swedish Market)

### MA200 Strategy Performance
| Period | Strategy | CAGR | Max DD | Buy-Hold (Index) |
|--------|----------|------|---------|------------------|
| 1991-2010 (OMXS30) | MA50 under > MA200: liquid | ~10-12% | -22% | 9.5% / -65% |
| 1901-2018 (OMXS) | Price > MA200 (10-month) | 12.2% | -22% | 9.5% / -65% |
| 1901-2017 (OMXS) | MA10 (liquid MA200) | 12% | Lower | 9.6% |
| 2005-2018 (OMXS30) | Close > MA200 | Edge 1.85%/trade | -25.5% | – |

### Key Findings
✅ **Advantages**:
- Reduces major drawdowns (2008: -28% vs -50%)
- Higher Sharpe ratio (risk-adjusted returns)
- Better capital preservation in bear markets

⚠️ **Drawbacks**:
- Whipsaw signals in sideways markets (false crossovers)
- Underperforms in strong bull markets (out of market temporarily)
- Transaction costs from rebalancing

## Kavastu's Performance

### Verified Results
- **2014-2021**: 37.9% annual return (vs OMXSPI 12.3%)
- **2024**: 18.5% (base portfolio) vs OMXSPI ~6%
- **Total**: +900% from start (Avanza portfolio verified by Dagens Industri)

### Key Success Factors
1. **Discipline**: Strict adherence to rules
2. **Emotion management**: Systematic approach removes fear/greed
3. **Capital preservation**: MA200 fire alarm prevents big losses
4. **Consistency**: Weekly reviews maintain process

## Implementation Notes

### Not a Pure Crossover Strategy
- ❌ Don't wait for perfect golden/death crosses (too slow)
- ✅ Focus on: Position relative to MA200 + momentum + fundamentals
- ✅ Use MA50 as confirmation, not trigger

### Weekly Review Critical
- **Frequency**: Weekly (Kavastu reviews daily, we do weekly)
- **Process**: Screen all watchlist stocks
- **Actions**: Remove weak, add strong, rebalance portfolio
- **Mindset**: Gardening analogy - "weed out the weak, water the strong"

### Combine Technical + Fundamental
- **Technical**: MA200, MA50, momentum, relative strength
- **Fundamental**: Revenue growth, profit growth, quality metrics
- **Both required**: Technical timing + fundamental strength

## References
- Dagens Industri - Kavastu verified returns
- BörsKollen - 2024 performance
- NeuroQuant AI - ML enhancement methodology
- Historical Swedish market data (1901-2026)

---

**Bottom line**: Kavastu's success comes from systematic trend-following (MA200 fire alarm) + fundamental strength + disciplined execution + AI-enhanced screening.
