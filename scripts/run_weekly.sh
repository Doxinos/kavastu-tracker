#!/bin/bash
# Weekly Kavastu Automation Runner
# Runs every Sunday at 19:00

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run automation with default portfolio values
# TODO: Update these values with your actual portfolio data
python scripts/weekly_automation.py \
    --portfolio-value 100000 \
    --cash 10000

# Sync database to Railway production
echo "Syncing database to Railway..."
RAILWAY_URL="https://web-production-a1855.up.railway.app"
SYNC_RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -F "file=@$PROJECT_DIR/data/portfolio.db" \
  "$RAILWAY_URL/api/admin/sync-db?secret=kavastu2026sync")

if [ "$SYNC_RESULT" = "200" ]; then
    echo "✅ Database synced to Railway" >> "$PROJECT_DIR/logs/automation.log"
else
    echo "⚠️  Railway sync failed (HTTP $SYNC_RESULT)" >> "$PROJECT_DIR/logs/automation.log"
fi

# Deactivate virtual environment
deactivate

# Log completion
echo "Weekly automation completed at $(date)" >> "$PROJECT_DIR/logs/automation.log"
