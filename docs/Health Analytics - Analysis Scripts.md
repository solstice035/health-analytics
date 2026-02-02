---
created: 2026-01-26 21:00:00
updated: 2026-01-26 21:00:00
type: reference
tags: [p/health-analytics, tech/python, dev, reference, python, health/analytics, scripts]
---

# Health Analytics - Analysis Scripts

> Complete reference for all Python analysis scripts in the health analytics system

## 📜 Script Overview

| Script | Purpose | Output | Runtime |
|--------|---------|--------|---------|
| `icloud_helper.py` | iCloud file access utilities | Helper functions | N/A |
| `daily_health_check.py` | Quick daily monitoring | Console report | < 5s |
| `detailed_analysis.py` | Single-day deep dive | Console report | < 10s |
| `weekly_summary.py` | 7-day trends & goals | Console report | < 15s |
| `generate_dashboard_data.py` | Dashboard JSON generator | 5 JSON files | < 10s |
| `explore_data.py` | Data structure explorer | Console report | < 10s |
| `analyze_specific_date.py` | Date-specific analysis | Console report | < 5s |

## 1️⃣ icloud_helper.py

**Purpose:** Core utilities for accessing iCloud Drive health data files

### Key Functions

```python
ensure_downloaded(file_path, timeout=30)
```
- Ensures an iCloud file is fully downloaded before accessing
- Triggers `brctl download` if needed
- Retries on lock errors
- Returns True when accessible

```python
read_json_safe(file_path, max_retries=3, retry_delay=1.0)
```
- Safely reads JSON from iCloud with retry logic
- Handles "Resource deadlock avoided" errors
- Auto-downloads placeholder files
- Returns parsed JSON or None on failure

```python
get_icloud_status(file_path)
```
- Checks current download status
- Returns: `'downloaded'`, `'downloading'`, `'placeholder'`, or `'unknown'`

```python
list_available_files(directory, pattern="*.json", ensure_downloaded=True)
```
- Lists files in iCloud directory
- Optionally triggers downloads
- Returns list of accessible Path objects

### Usage Example

```python
from icloud_helper import read_json_safe, get_icloud_status

file_path = "data/HealthAutoExport-2026-01-25.json"

# Check status
status = get_icloud_status(file_path)
print(f"File status: {status}")

# Read with automatic download handling
data = read_json_safe(file_path)
if data:
    print(f"Loaded {len(data)} keys")
```

## 2️⃣ daily_health_check.py

**Purpose:** Quick daily health data monitoring and freshness check

### What It Does
- Verifies today's and yesterday's health data exist
- Shows file count and date range
- Attempts to extract basic metrics from yesterday
- Reports data freshness status

### Usage

```bash
cd ~/clawd/projects/health-analytics
python3 scripts/daily_health_check.py
```

### Output Example

```
============================================================
🍎 Apple Health - Daily Check
⏰ 2026-01-26 20:33:00
============================================================
🩺 Health Data Freshness Check
   Today's date: 2026-01-26
   ✓ Today's data exists (630,298 bytes, downloaded)
   ✓ Yesterday's data exists (783,724 bytes, downloading)

📁 Total Files: 175
   First: 2025-08-05
   Latest: 2026-01-26
   Range: 175 days

📊 Yesterday's Summary (2026-01-25)
   🚶 Steps: 12,670
   🔥 Active Energy: 959 kcal
   💪 Exercise Time: 82 minutes

============================================================
✅ Daily health check complete
```

### Use Cases
- Morning routine check
- Verify exports are running
- Quick yesterday summary
- Automated monitoring (cron/launchd)

## 3️⃣ detailed_analysis.py

**Purpose:** Comprehensive single-day health analysis

### What It Shows
- **Daily Totals:** steps, distance, energy, exercise, stands, flights, daylight
- **Key Readings:** resting HR, HRV, walking HR, blood oxygen, VO2 max
- **Heart Rate Stats:** min, max, average throughout day
- **Available Metrics:** All 25 metrics with data point counts

### Usage

```bash
# Analyze a specific date
python3 scripts/detailed_analysis.py 2026-01-25

# Analyze yesterday (default)
python3 scripts/detailed_analysis.py
```

### Output Example

```
======================================================================
🍎 Apple Health - Detailed Analysis
📅 Date: 2026-01-25
======================================================================
📁 File status: downloaded
✓ Loaded 25 metric types

📊 DAILY TOTALS
----------------------------------------------------------------------
🚶 Steps:              12,670
📏 Distance:           9.84 km
🔥 Active Energy:      959 kcal
💪 Exercise Time:      82 minutes
🧍 Stand Hours:        15/12
🪜 Flights Climbed:    28
☀️  Time in Daylight:  79 minutes

❤️  KEY HEALTH READINGS
----------------------------------------------------------------------
💤 Resting Heart Rate: 57 bpm
📊 HRV (avg):          56 ms
🚶 Walking HR (avg):   89 bpm
🫁 Blood Oxygen:       97%
🏃 VO2 Max:            41.1 ml/(kg·min)

💓 HEART RATE THROUGHOUT DAY
----------------------------------------------------------------------
Readings:   285
Min:        52 bpm
Max:        145 bpm
Average:    78 bpm

📈 AVAILABLE METRICS (25 total)
----------------------------------------------------------------------
Basal Energy Burned                       1401 points  (kJ)
Active Energy                              809 points  (kcal)
Step Count                                 521 points  (count)
...
======================================================================
```

### Use Cases
- Deep dive into specific day
- Compare different days
- Verify data completeness
- Track personal records

## 4️⃣ weekly_summary.py

**Purpose:** 7-day trend analysis with goal tracking

### What It Shows
- **Daily Breakdown Table:** 7 days of key metrics
- **Weekly Averages:** Steps, distance, energy, exercise, HR, HRV
- **Goal Achievements:** 10K steps, 12hr stands, 30min exercise

### Usage

```bash
# Past 7 days ending yesterday
python3 scripts/weekly_summary.py

# Specific end date
python3 scripts/weekly_summary.py 2026-01-25

# Custom number of days
python3 scripts/weekly_summary.py 2026-01-25 14  # Last 14 days
```

### Output Example

```
================================================================================
📊 WEEKLY HEALTH SUMMARY
📅 Week: 2026-01-19 to 2026-01-25
📈 Days analyzed: 7/7
================================================================================

📆 DAILY BREAKDOWN
--------------------------------------------------------------------------------
Date            Steps Distance   Energy Exercise Stands
--------------------------------------------------------------------------------
Mon 2026-01-19    8,996    8.3km  752kcal    66min  14/12
Tue 2026-01-20   15,588   12.7km 1038kcal    93min  14/12
Wed 2026-01-21   11,066    9.0km  800kcal    78min  14/12
...

📊 WEEKLY AVERAGES
--------------------------------------------------------------------------------
🚶 Steps:              11,762/day  (total: 82,334)
📏 Distance:           9.9 km/day  (total: 69.2 km)
🔥 Active Energy:      886 kcal/day  (total: 6,205 kcal)
...

🎯 GOAL ACHIEVEMENTS
--------------------------------------------------------------------------------
✓ 10,000 steps:        5/7 days
✓ 12 stand hours:      6/7 days
✓ 30min exercise:      7/7 days
================================================================================
```

### Use Cases
- Weekly review routine
- Track goal consistency
- Compare weeks
- Share weekly progress

## 5️⃣ generate_dashboard_data.py

**Purpose:** Generate JSON data files for web dashboard

### What It Creates

| File | Content | Size |
|------|---------|------|
| `daily_trends.json` | 30 days of activity metrics | ~2.5 KB |
| `weekly_comparison.json` | 12 weeks of averages | ~400 B |
| `goals_progress.json` | 7 days of goal achievements | ~360 B |
| `summary_stats.json` | Weekly summary statistics | ~600 B |
| `hr_distribution.json` | Heart rate zone breakdown | ~145 B |
| `metadata.json` | Generation timestamp & data range | ~180 B |

### Usage

```bash
python3 scripts/generate_dashboard_data.py
```

### Output Example

```
🏗️  Generating Health Dashboard Data...
============================================================
📅 Loading data from 2025-12-26 to 2026-01-25...
✓ Loaded 31 days of data

📊 Generating visualizations...
  ✓ daily_trends.json (30-day activity)
  ✓ weekly_comparison.json (12-week trends)
  ✓ goals_progress.json (7-day goals)
  ✓ summary_stats.json (weekly summary)
  ✓ hr_distribution.json (HR zones)
  ✓ metadata.json

✅ Dashboard data generated successfully!
📁 Output directory: /Users/nick/clawd/projects/health-analytics/dashboard/data

💡 Next: Open dashboard/index.html in a browser
```

### Use Cases
- Update dashboard with latest data
- Scheduled automation (cron/launchd)
- Pre-deployment data generation
- Testing dashboard changes

### Automation Example

**Launchd plist** (`~/Library/LaunchAgents/com.health.dashboard.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.health.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/nick/clawd/projects/health-analytics/scripts/generate_dashboard_data.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Load with: `launchctl load ~/Library/LaunchAgents/com.health.dashboard.plist`

## 6️⃣ explore_data.py

**Purpose:** Understand health data structure and available metrics

### What It Shows
- Total files and date coverage
- Data completeness check
- Top-level JSON structure
- All available metrics with data point counts

### Usage

```bash
python3 scripts/explore_data.py
```

### Output Example

```
🍎 Apple Health Data Explorer
==================================================
📊 Found 175 health data files
   175 files appear downloaded, 0 may need sync

📅 Date Coverage:
  • First export: 2025-08-05
  • Latest export: 2026-01-26
  • Total days: 175
  • Date range: 175 days

📁 Analyzing: HealthAutoExport-2026-01-26.json
   iCloud status: downloaded

🔑 Top-level keys:
  • data: dict with 1 keys

📈 Health Metrics Found:
  • Basal Energy Burned: 1401 points (kJ)
  • Active Energy: 809 points (kcal)
  • Step Count: 521 points (count)
  ...

✅ Successfully analyzed health data structure
```

### Use Cases
- First-time data exploration
- Verify data availability
- Understand JSON structure
- Check for new metrics

## 7️⃣ analyze_specific_date.py

**Purpose:** Quick analysis of a single date (simplified version of detailed_analysis.py)

### Usage

```bash
python3 scripts/analyze_specific_date.py 2026-01-20
```

### Output Example

```
📊 Analyzing: HealthAutoExport-2026-01-20.json
   iCloud status: downloaded

🔑 Top-level keys: data

📈 Available Metrics:
  • metrics

📊 Daily Summary:
  • step_count: 15,588
  • active_energy: 1,038 kcal
  • ...
```

### Use Cases
- Quick date check
- Scripting/automation
- Minimal output needed

## 🔄 Common Workflows

### Daily Routine

```bash
# Morning check
python3 scripts/daily_health_check.py

# Detailed look at yesterday
python3 scripts/detailed_analysis.py
```

### Weekly Review

```bash
# Generate weekly summary
python3 scripts/weekly_summary.py

# Update dashboard
python3 scripts/generate_dashboard_data.py

# Open dashboard
open dashboard/index.html
```

### Automated Monitoring

```bash
# Add to crontab or launchd

# Daily dashboard update at 8 AM
0 8 * * * cd ~/clawd/projects/health-analytics && python3 scripts/generate_dashboard_data.py

# Weekly summary email every Monday
0 9 * * 1 cd ~/clawd/projects/health-analytics && python3 scripts/weekly_summary.py | mail -s "Weekly Health Summary" you@email.com
```

## 🔧 Extending the Scripts

### Adding New Metrics

```python
def extract_new_metric(metrics):
    """Extract a new metric type."""
    if 'new_metric_name' in metrics:
        values = metrics['new_metric_name']['data']
        # Process values
        return processed_data
    return None
```

### Creating New Analysis

```python
#!/usr/bin/env python3
"""Custom analysis script."""

from pathlib import Path
from icloud_helper import read_json_safe
from detailed_analysis import extract_all_metrics

HEALTH_DATA_PATH = Path(__file__).parent.parent / "data"

def your_custom_analysis(date_str):
    """Your analysis logic."""
    file_path = HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"
    data = read_json_safe(file_path)
    
    if data:
        metrics = extract_all_metrics(data)
        # Your analysis here
    
if __name__ == "__main__":
    your_custom_analysis("2026-01-25")
```

## 📚 Related Documentation

- [[Health Analytics|Main Project]]
- [[Health Analytics - Technical Details|Technical Details]]
- [[Health Analytics - Deployment Guide|Deployment Guide]]

---

**Quick Reference Card**

```bash
# Daily check
python3 scripts/daily_health_check.py

# Single day analysis
python3 scripts/detailed_analysis.py 2026-01-25

# Weekly summary
python3 scripts/weekly_summary.py

# Update dashboard
python3 scripts/generate_dashboard_data.py

# Explore data
python3 scripts/explore_data.py
```
