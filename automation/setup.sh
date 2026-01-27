#!/bin/bash
# Setup script for Health Analytics automation
# Run this once to enable daily dashboard refresh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_NAME="com.health-analytics.daily-refresh.plist"
PLIST_SRC="$PROJECT_DIR/automation/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"
LOGS_DIR="$PROJECT_DIR/logs"

echo "Health Analytics Automation Setup"
echo "=================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo ""

# Create logs directory
echo "Creating logs directory..."
mkdir -p "$LOGS_DIR"
echo "  Created: $LOGS_DIR"

# Check if plist exists
if [ ! -f "$PLIST_SRC" ]; then
    echo "Error: Plist file not found at $PLIST_SRC"
    exit 1
fi

# Check if already installed
if [ -f "$PLIST_DST" ]; then
    echo "Stopping existing service..."
    launchctl unload "$PLIST_DST" 2>/dev/null || true
fi

# Create LaunchAgents directory if needed
mkdir -p "$HOME/Library/LaunchAgents"

# Copy plist
echo "Installing launch agent..."
cp "$PLIST_SRC" "$PLIST_DST"
echo "  Installed: $PLIST_DST"

# Load the agent
echo "Loading launch agent..."
launchctl load "$PLIST_DST"
echo "  Loaded successfully"

echo ""
echo "Setup complete!"
echo ""
echo "The dashboard will automatically refresh daily at 7:00 AM."
echo ""
echo "Useful commands:"
echo "  Check status:    launchctl list | grep health-analytics"
echo "  Run manually:    launchctl start $PLIST_NAME"
echo "  View logs:       tail -f $LOGS_DIR/daily-refresh.log"
echo "  Disable:         launchctl unload $PLIST_DST"
echo "  Re-enable:       launchctl load $PLIST_DST"
echo ""
