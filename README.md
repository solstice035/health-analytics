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

```bash
# Navigate to project
cd ~/clawd/projects/health-analytics

# Run daily health check (works with iCloud sync)
python3 scripts/daily_health_check.py

# Explore available data
python3 scripts/explore_data.py

# Analyze a specific date
python3 scripts/analyze_specific_date.py 2026-01-25

# Optional: Set up Python environment for advanced analysis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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
