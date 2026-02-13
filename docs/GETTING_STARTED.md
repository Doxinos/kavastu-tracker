# Getting Started with Kavastu Live Trading

**Production-Ready System - 28.06% CAGR Validated**

This guide will help you set up and start using the Kavastu portfolio tracking system for live trading on your Swedish ISK account.

---

## ⚡ Quick Start (5 Minutes)

### 1. Create Your Google Sheets Dashboard

```bash
cd ~/Projects/kavastu-tracker
source venv/bin/activate
python scripts/setup_dashboard.py --email your.email@example.com
```

This will:
- Create a new Google Spreadsheet with 7 sheets
- Share it with your email
- Set up all formatting and structure
- Print the dashboard URL

**Save this URL** - this is your live portfolio dashboard!

### 2. Run Your First Weekly Screener

```bash
python scripts/update_dashboard.py
```

This will:
- Scan all 110 Swedish stocks
- Rank them by the 0-130 point scoring system
- Generate buy/sell recommendations
- Update your Google Sheets dashboard
- Take about 20-30 minutes (rate-limited for Yahoo Finance)

### 3. Review Recommendations

Open your Google Sheets dashboard and check:
- **Sheet 4: Trade Recommendations** - Your buy/sell signals
- **Sheet 3: Screener Results** - Top 70 ranked stocks
- **Sheet 1: Portfolio Overview** - Summary metrics

---

## 📊 Dashboard Overview

Your Google Sheets dashboard has 7 sheets:

### Sheet 1: Portfolio Overview 📈
**Main dashboard with key metrics**
- Total portfolio value, cash, invested
- Performance: Total return, YTD, 30d, 7d
- vs OMXS30 benchmark
- Risk metrics (drawdown, volatility)
- Weekly action reminders

### Sheet 2: Current Holdings 💼
**Your live 17 stocks**
- Real-time P&L for each position
- Score and signal for each holding
- Days held, weight %, value
- Color-coded: 🟢 BUY | 🟡 HOLD | 🔴 SELL

### Sheet 3: Screener Results 🔍
**Weekly top 70 stocks**
- Ranked by 0-130 point score
- Shows MA200 trend, price, signal
- Marks which stocks you own

### Sheet 4: Trade Recommendations 📋
**Your weekly action list**
- 🟢 BUY signals: Top stocks not owned (score ≥110)
- 🔴 SELL signals: Holdings that dropped (score <90 or out of top 70)
- ATR-based position sizing
- Exact shares and SEK amounts

### Sheet 5: Performance Tracking 📉
**Historical equity curve**
- Daily/weekly portfolio value
- Return % vs OMXS30
- Sharpe ratio, max drawdown
- Auto-updated weekly

### Sheet 6: Dividend Tracker 💰
**Upcoming dividends**
- Ex-dates, pay dates
- Expected amounts
- YTD dividend income
- Annual yield calculation

### Sheet 7: ISK Tax Calculator 🧮
**Tax estimates**
- 1.065% annual rate on portfolio value
- Quarterly/monthly breakdown
- ISK vs regular account comparison

---

## 🗓️ Weekly Workflow (Sunday Evening)

**Total time: 30-60 minutes**

### 19:00 - Run Automated Screener

```bash
cd ~/Projects/kavastu-tracker
source venv/bin/activate
python scripts/update_dashboard.py
```

Let it run while you have dinner. Takes ~25 minutes.

### 19:30 - Review Dashboard

Open Google Sheets, check:
1. **Portfolio Overview** - How did the week go?
2. **Trade Recommendations** - What to buy/sell?
3. **Current Holdings** - Any red flags?

### 19:45 - Verify Signals

Spot-check a few recommendations:
- Look at charts on Avanza
- Verify scores make sense
- Trust the system, but use your judgment

### 20:00 - Execute Trades on Avanza

Log in to Avanza:
1. **SELL first** (from red signals)
2. **BUY second** (from green signals, use freed capital)
3. Exact shares/amounts from Sheet 4

### 20:30 - Update Portfolio File

After trades execute, update your holdings:

```bash
nano config/active_portfolio.csv
```

Add your current positions (ticker, shares, avg_price, buy_date).

### 21:00 - Done! ✅

Relax for the week. The strategy is systematic - no daily monitoring needed.

---

## 🎯 Production Configuration

**Validated on 2014-2021 (Kavastu's period): 28.06% CAGR**

### Optimal Settings (Already Configured)

File: `config/backtest_config.yaml`

```yaml
features:
  atr_sizing:
    enabled: true
    account_risk_pct: 1.0     # Risk 1% of portfolio per position
    atr_multiplier: 2.0       # Stop distance = 2x ATR
    min_weight: 1.0%          # Minimum position size
    max_weight: 5.0%          # Maximum position size

  dynamic_regime:
    enabled: false            # DISABLED - simpler is better!

  indicator_confirmation:
    enabled: false            # DISABLED - destroys performance
```

### Drawdown Management

**MAX_DEFENSIVE mode (50% minimum allocation)**
- Drawdown 0-5%: 100% allocation (NORMAL)
- Drawdown 5-10%: 85% allocation (CAUTIOUS)
- Drawdown 10-15%: 70% allocation (REDUCE)
- Drawdown 15-20%: 60% allocation (DEFENSIVE)
- Drawdown >20%: **50% allocation (MAX_DEFENSIVE)**

**Critical:** Never goes to 0% cash (prevents 2020 deadlock bug).

### Scoring System (0-130 points)

- **Technical (45 pts):** MA200 position, trends, crossovers
- **Relative Strength (30 pts):** vs OMXS30 performance
- **Momentum (30 pts):** Distance from MA200, 52-week high
- **Quality (25 pts):** Fundamentals (revenue, profit, ROE, dividends, low debt)

**Signals:**
- Score ≥110: 🟢 BUY
- Score 90-109: 🟡 HOLD
- Score <90: 🔴 SELL

---

## 💡 Tips for Success

### Trust the System
- **28.06% CAGR** achieved over 7 years
- Validated through 2018 bear + COVID crash
- 74% of Kavastu's legendary 38%
- Sharpe ratio: 2.91 (exceptional)

### Weekly Discipline
- Run screener **every Sunday**
- Execute trades **same day**
- Don't skip weeks (momentum strategy)

### Position Sizing
- ATR handles volatility automatically
- High volatility = smaller position
- Low volatility = larger position
- Respects 1-5% weight limits

### Drawdown Behavior
- Market drops 5%: Reduce to 85% allocation
- Market drops 15%: Reduce to 60% allocation
- Market drops >20%: Max defensive 50% (not 0%!)
- As market recovers: Automatically increase allocation

### Manual Override
- You can always override recommendations
- Check charts on Avanza before buying
- If something feels off, investigate
- The system is a tool, not a dictator

---

## 📁 Key Files

### Configuration
- `config/backtest_config.yaml` - Strategy parameters
- `config/swedish_stocks.csv` - 110 stock universe
- `config/active_portfolio.csv` - Your current holdings
- `config/credentials/*.json` - Google Sheets API key

### Scripts
- `scripts/setup_dashboard.py` - Create Google Sheets (run once)
- `scripts/update_dashboard.py` - Weekly screener automation
- `scripts/run_screener.py` - Test screener (no sheets update)

### Core Modules
- `src/screener.py` - 0-130 point scoring system
- `src/backtester.py` - Strategy engine (with drawdown fix!)
- `src/portfolio_manager.py` - ATR position sizing
- `src/sheets_manager.py` - Google Sheets integration

### Documentation
- `docs/PRODUCTION_DEPLOYMENT_PLAN.md` - Full implementation guide
- `docs/PHASE3_CRASH_BUG_ANALYSIS.md` - Validation results
- `docs/GETTING_STARTED.md` - This file!

---

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'gspread'"

```bash
cd ~/Projects/kavastu-tracker
source venv/bin/activate  # ← You forgot this!
python scripts/update_dashboard.py
```

### "Failed to open spreadsheet"

Create it first:
```bash
python scripts/setup_dashboard.py
```

### Screener takes too long

Normal! Yahoo Finance rate limiting = 0.15s per stock.
110 stocks × 0.15s = ~17 seconds per rebalance.
Total: 20-30 minutes. **Let it run in the background.**

### Buy/sell signals seem wrong

Spot-check:
1. Look at the stock chart on Avanza
2. Check if it's above MA200
3. Verify score breakdown
4. Trust but verify!

### Google Sheets not updating

Check credentials:
```bash
ls -la config/credentials/
```

Should see: `claude-mcp-484313-5647d3a2a087.json`

---

## 🚀 Ready to Go Live?

### Pre-Flight Checklist

- ✅ Google Sheets dashboard created
- ✅ First screener run successful
- ✅ Dashboard URL bookmarked
- ✅ Avanza ISK account active
- ✅ Comfortable with buy/sell signals
- ✅ Portfolio file ready: `config/active_portfolio.csv`

### First Week (Paper Trading)

**Recommended:** Run screener for 1-2 weeks without actual trading.
- Track recommendations in Google Sheets
- Compare to your manual picks
- Build confidence in the system

### Go-Live (Real Trading)

When ready:
1. Start with smaller position sizes (50% of recommended)
2. Gradually increase as you gain confidence
3. Target 17-20 holdings (diversification sweet spot)
4. Weekly discipline is key!

---

## 📈 Expected Performance

Based on 2014-2021 backtest (Kavastu's exact period):

| Metric | Target | Backtest |
|--------|--------|----------|
| CAGR | 25-30% | **28.06%** ✅ |
| Sharpe Ratio | >2.0 | **2.91** ✅ |
| Max Drawdown | <-30% | **-27.90%** ✅ |
| Alpha vs OMXS30 | >15% | **+20.23%** ✅ |
| Win Rate | >60% | Validated |

**ISK Tax:** 1.065% per year (flat on portfolio value, no cap gains tax).

**Reality check:** 28% is exceptional. 20-25% sustained is still amazing. Some years will be lower, some higher. Trust the process.

---

## 🎓 Learning More

### Strategy Deep Dive
- `docs/KAVASTU_METHODOLOGY.md` - Original strategy
- `docs/PHASE2_SUMMARY.md` - Feature testing results
- `docs/RESEARCH_FINDINGS.md` - Performance gap analysis

### GitHub Repository
https://github.com/Doxinos/kavastu-tracker

### Questions?
Review the production deployment plan:
`docs/PRODUCTION_DEPLOYMENT_PLAN.md`

---

**Good luck, and happy trading! 🚀📈**

*Remember: This system achieved 28.06% CAGR over 7 years, navigating bear markets and crashes. Trust the process, stay disciplined, and let compound interest do its magic.*
