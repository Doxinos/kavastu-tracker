#!/bin/bash
# Setup crontab for Kavastu weekly automation
# Runs every Sunday at 19:00

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up Kavastu weekly automation cron job..."
echo "This will run every Sunday at 19:00"
echo ""

# Create cron job entry
CRON_JOB="0 19 * * 0 $SCRIPT_DIR/run_weekly.sh >> $PROJECT_DIR/logs/automation.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_weekly.sh"; then
    echo "⚠️  Cron job already exists. Remove it first with:"
    echo "   crontab -e"
    echo "   Then delete the line containing 'run_weekly.sh'"
    exit 1
fi

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job installed successfully!"
    echo ""
    echo "Schedule: Every Sunday at 19:00"
    echo "Script:   $SCRIPT_DIR/run_weekly.sh"
    echo "Logs:     $PROJECT_DIR/logs/automation.log"
    echo ""
    echo "To view cron jobs:"
    echo "   crontab -l"
    echo ""
    echo "To remove this cron job:"
    echo "   crontab -e"
    echo "   (Delete the line containing 'run_weekly.sh')"
    echo ""
    echo "Next run: This Sunday at 19:00"
else
    echo "❌ Failed to install cron job"
    exit 1
fi
