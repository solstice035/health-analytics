#!/bin/bash
# Update Health Dashboard Data
# Run this script to refresh the dashboard with latest health data

cd "$(dirname "$0")/.."

echo "🔄 Updating Health Dashboard..."
python3 scripts/generate_dashboard_data.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dashboard updated successfully!"
    echo "📊 View at: file://$(pwd)/dashboard/index.html"
else
    echo "❌ Dashboard update failed"
    exit 1
fi
