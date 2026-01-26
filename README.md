# Apple Health Data Analytics

**Created:** January 26, 2026  
**Data Source:** Health Auto Export app → iCloud Drive  
**Location:** `~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/JSON/`

## Overview

Daily automated exports of Apple Health data in JSON format. Currently **175 days** of health data available (August 2025 - January 2026).

## Data Structure

- **Format:** Daily JSON files named `HealthAutoExport-YYYY-MM-DD.json`
- **Frequency:** Daily automated exports
- **Date Range:** 2025-08-05 to 2026-01-26 (175 files)

## Project Structure

```
health-analytics/
├── README.md              # This file
├── data/                  # Symlink to iCloud data (or local copies)
├── notebooks/             # Jupyter notebooks for exploration
├── scripts/               # Python analysis scripts
├── visualizations/        # Generated charts and reports
└── requirements.txt       # Python dependencies
```

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
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run initial data exploration
python scripts/explore_data.py

# Generate daily summary
python scripts/daily_summary.py --date 2026-01-25
```

## Data Privacy

- All data remains local (iCloud Drive)
- No external services or uploads
- Analysis runs locally on Mac Mini

## Next Steps

1. ✅ Locate data source (done)
2. ⏳ Create symlink or copy mechanism
3. ⏳ Explore JSON structure
4. ⏳ Build data parser
5. ⏳ Generate initial visualizations
6. ⏳ Set up automated daily reports

## Notes

- Files may be actively syncing from iCloud
- Use `cp` or `rsync` to create stable local copies for analysis
- Consider creating a cron job to copy new files daily
