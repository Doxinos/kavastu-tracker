# Kavastu Weekly Automation

Automated weekly stock screening and portfolio tracking system.

---

## What It Does

Every **Sunday at 19:00**, the automation:

1. **Screens all 113 Swedish stocks** - Calculates Kavastu scores (0-130) and trending classifications (HOT/COLD)
2. **Saves to database** - Stores portfolio snapshot + top 50 stocks in SQLite database
3. **Generates recommendations** - Creates BUY/SELL signals based on scoring criteria
4. **Creates weekly report** - Saves text summary to `reports/` directory

---

## Setup (One-Time)

### 1. Install the Cron Job

```bash
cd /Users/peter/Projects/kavastu-tracker
./scripts/setup_cron.sh
```

This will:
- Add cron job to run every Sunday at 19:00
- Create automation log file at `logs/automation.log`
- Confirm installation

### 2. Update Portfolio Values (Before First Run)

Edit `scripts/run_weekly.sh` and update these values with your actual portfolio data:

```bash
python scripts/weekly_automation.py \
    --portfolio-value 100000 \    # <-- Your actual total portfolio value
    --cash 10000                  # <-- Your actual cash balance
```

---

## Manual Run (Testing)

To test the automation manually:

```bash
cd /Users/peter/Projects/kavastu-tracker
source venv/bin/activate
python scripts/weekly_automation.py --portfolio-value 100000 --cash 10000
```

This will:
- Run the screener on all stocks (~15-20 minutes)
- Save results to database
- Generate weekly summary report
- Print summary to console

---

## Output Files

### Weekly Summary Reports
Location: `reports/weekly_summary_YYYY-MM-DD.txt`

Example:
```
================================================================================
KAVASTU WEEKLY SUMMARY - 2026-02-14
================================================================================

📊 PORTFOLIO SNAPSHOT
   Total Value:         100,000 SEK
   Cash:                 10,000 SEK
   Invested:             90,000 SEK
   Week Return:            0.00%

🏆 TOP 10 STOCKS
    1. SAND.ST      Score: 117.3  🔥 Trending:  80/100
    2. BOL.ST       Score: 116.3  ➖ Trending:  65/100
    3. ABB.ST       Score: 110.8  🔥 Trending:  75/100

🎯 TRADE RECOMMENDATIONS
   🟢 BUY SIGNALS: 1
      ABB.ST: Score 111/130 (Top Tier) • Trending HOT (75/100) • Above MA200
```

### Database
Location: `data/portfolio.db`

Tables:
- `weekly_snapshots` - Portfolio value, returns, holdings count
- `screener_results` - Top 50 stocks per week
- `trade_history` - Buy/sell transactions (when implemented)
- `holdings` - Current positions (when implemented)

### Logs
Location: `logs/automation.log`

Contains:
- Automation run timestamps
- Errors/warnings
- Completion confirmations

---

## Managing the Cron Job

### View Current Cron Jobs
```bash
crontab -l
```

### Edit Cron Jobs
```bash
crontab -e
```

### Remove Kavastu Automation
```bash
crontab -e
# Delete the line containing "run_weekly.sh"
```

---

## BUY Signal Criteria

A stock gets a BUY signal when:
1. **Kavastu Score ≥ 100** (top tier stocks)
2. **Trending Score ≥ 70** (HOT classification)
3. **Above MA200** (long-term uptrend)

Example BUY signal:
```
ABB.ST: Score 111/130 (Top Tier) • Trending HOT (75/100) • Above MA200
```

---

## Troubleshooting

### Automation Didn't Run
Check the log file:
```bash
tail -50 /Users/peter/Projects/kavastu-tracker/logs/automation.log
```

Common issues:
- Virtual environment not activated → Check `run_weekly.sh`
- Yahoo Finance rate limits → Wait 15 minutes, try again
- Python dependencies missing → Run `pip install -r requirements.txt`

### Database Growing Too Large
The database auto-manages size:
- Portfolio snapshots: Kept forever (~1 KB/week)
- Screener results: 1 year retention, then auto-deleted (~30 KB/week)

Manual cleanup (optional):
```bash
python -c "from src.database import PortfolioDB; db = PortfolioDB(); db.cleanup_old_data(keep_weeks=52)"
```

### Update Portfolio Values Mid-Week
Edit `scripts/run_weekly.sh` anytime. Changes take effect next Sunday.

---

## Next Steps

### Phase 5: API Layer (Planned)
- FastAPI REST API for data access
- Endpoints: `/api/latest`, `/api/history`, `/api/trending`
- Enable web dashboard integration

### Phase 6: Web Dashboard (Planned)
- Next.js + React frontend
- iPad-optimized UI
- Real-time portfolio tracking
- Historical performance charts

---

## Notes

- **Runtime:** ~15-20 minutes for full screener (113 stocks)
- **Data retention:** Portfolio snapshots kept forever, screener results for 1 year
- **Storage:** ~30 KB per week = 1.5 MB per year
- **ISK tax requirement:** Database maintains complete trade history for 1.065% flat tax calculation
