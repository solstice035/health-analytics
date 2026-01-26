# Apple Health Data Analytics

**Created:** January 26, 2026  
**Data Source:** Health Auto Export app → iCloud Drive  
**Location:** `~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/JSON/`

## Overview

Daily automated exports of Apple Health data in JSON format. Currently **175 days** of health data available (August 2025 - January 2026).

## Data Structure

- **Format:** Daily JSON files named `HealthAutoExport-YYYY-MM-DD.json`
- **Frequency:** Daily automated exports (synced to iCloud)
- **Date Range:** 2025-08-05 to 2026-01-26 (175 files)
- **Access:** Symlinked from iCloud Drive with automated sync handling

## Project Structure

```
health-analytics/
├── README.md              # This file
├── data/                  # Symlink to iCloud Drive health exports
├── notebooks/             # Jupyter notebooks for exploration
├── scripts/               # Python analysis scripts
│   ├── icloud_helper.py         # iCloud file access utilities
│   ├── explore_data.py          # Data structure explorer
│   ├── analyze_specific_date.py # Single-day analyzer
│   ├── daily_health_check.py    # Automated daily monitoring
│   └── sync_data.py             # (deprecated - using symlink now)
├── visualizations/        # Generated charts and reports
└── requirements.txt       # Python dependencies
```

## Data Access Method

The project uses a **symlink** to directly access health data in iCloud Drive:

```bash
data/ -> ~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/JSON/
```

All scripts include `icloud_helper.py` which handles:
- Ensuring files are downloaded from iCloud before reading
- Retrying on sync conflicts
- Checking file availability status

## Dashboard

**Interactive web dashboard** with real-time visualizations:

- **30-day activity trends** - Steps and active energy over time
- **Weekly comparison** - 12-week averages  
- **Goal progress** - Track daily achievements (10K steps, 12hr stands, 30min exercise)
- **Summary statistics** - Key metrics at a glance
- **Fully responsive** - Works on desktop, tablet, and mobile

**View dashboard:** `python serve.py` (starts server at http://localhost:8080)
**Update data:** `python3 scripts/generate_dashboard_data.py`
**Deploy:** See [DEPLOYMENT.md](DEPLOYMENT.md) for hosting options

> **Important:** Always use `python serve.py` to view the dashboard. Opening `index.html` directly will fail due to browser CORS restrictions.

## Initial Analysis Goals

1. **Activity Metrics:**
   - Daily step counts
   - Active energy burned
   - Exercise minutes
   - Stand hours

2. **Sleep Analysis:**
   - Sleep duration trends
   - Sleep quality patterns
   - Bedtime/wake time consistency

3. **Heart Rate:**
   - Resting heart rate trends
   - Heart rate variability (HRV)
   - Workout heart rate zones

4. **Trends & Correlations:**
   - Activity vs. sleep quality
   - Weekly patterns (weekday vs. weekend)
   - Monthly trends and seasonality

## Quick Start

### View the Dashboard

```bash
# Generate dashboard data
cd ~/clawd/projects/health-analytics
python3 scripts/generate_dashboard_data.py

# Start dashboard server (recommended - avoids CORS issues)
python serve.py
# Opens dashboard at http://localhost:8080

# Or use custom port
python serve.py --port 3000
```

**Note:** Opening `dashboard/index.html` directly via `file://` protocol will cause CORS errors. Always use the HTTP server via `python serve.py`.

### Command Line Analysis

```bash
# Navigate to project
cd ~/clawd/projects/health-analytics

# Run daily health check (works with iCloud sync)
python3 scripts/daily_health_check.py

# Get detailed analysis for a specific date
python3 scripts/detailed_analysis.py 2026-01-25

# View weekly summary
python3 scripts/weekly_summary.py

# Explore available data
python3 scripts/explore_data.py
```

## Data Privacy

- All data remains local (iCloud Drive)
- No external services or uploads
- Analysis runs locally on Mac Mini

## Next Steps

1. ✅ Locate data source
2. ✅ Create symlink with iCloud sync handling
3. ✅ Build iCloud-aware data access utilities
4. ⏳ Explore JSON structure in detail
5. ⏳ Build comprehensive data parser
6. ⏳ Generate visualizations and trends
7. ⏳ Set up automated daily reports
8. ⏳ Create dashboards

## Notes

- Files may be actively syncing from iCloud
- Use `cp` or `rsync` to create stable local copies for analysis
- Consider creating a cron job to copy new files daily
