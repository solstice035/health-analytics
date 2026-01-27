# Apple Health Data Analytics

**A comprehensive health data analysis and visualization platform**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Tests](https://img.shields.io/badge/Tests-212%20passing-green)
![Coverage](https://img.shields.io/badge/Coverage-42%25-yellow)

## Overview

Daily automated exports of Apple Health data in JSON format. Includes an interactive dashboard with trend analysis, goal tracking, and health insights.

**Data Source:** Health Auto Export app → iCloud Drive
**Data Range:** 176 days (August 2025 - January 2026)
**Dashboard:** Interactive multi-tab dashboard with deep analysis

## Features

- **Interactive Dashboard** - Real-time visualizations with per-section error recovery
- **Unified CLI** - Single command interface for all operations
- **Smart Caching** - Automatic cache invalidation for faster data access
- **iCloud Integration** - Seamless sync with automatic download handling
- **Daily Automation** - launchd-based scheduled data refresh
- **Comprehensive Testing** - 212 tests with TDD approach

## Quick Start

### Using the CLI

```bash
cd ~/clawd/projects/health-analytics
source venv/bin/activate

# Check system status
./health status

# Start the dashboard
./health dashboard

# Generate fresh dashboard data
./health generate

# Run daily health check
./health daily

# View cache statistics
./health cache stats
```

### Available Commands

| Command | Description |
|---------|-------------|
| `health dashboard` | Start the dashboard server (default: port 8080) |
| `health generate` | Generate dashboard data files |
| `health daily` | Run daily health check |
| `health analyze DATE` | Analyze a specific date |
| `health weekly` | Generate weekly summary |
| `health deep` | Run deep analysis |
| `health config` | Show configuration |
| `health status` | Show system status |
| `health cache stats` | Show cache statistics |
| `health cache clear` | Clear the cache |
| `health cache warm` | Pre-load data into cache |

## Dashboard

The interactive dashboard provides:

### Overview Tab
- **Health Score** - Weighted composite score based on activity, exercise, and vitals
- **Quick Stats** - Steps, distance, active energy, exercise minutes
- **Daily Goals** - 10K steps, 12hr stands, 30min exercise tracking
- **Activity Trends** - 30-day charts for all metrics
- **HR Distribution** - Doughnut chart with 5 heart rate zones

### Deep Analysis Tabs
- **Trends** - Monthly progression and weekly patterns
- **Fitness** - VO2 Max tracking and metric correlations
- **Heart** - Monthly HR trends and high-intensity day detection
- **Records** - Personal records and achievement streaks
- **Insights** - AI-generated health insights with recommendations

### Error Recovery
The dashboard includes per-section error handling:
- Graceful degradation when data files are missing
- User-friendly error messages
- Retry buttons for failed sections
- Visual status indicator (green/orange/red)

## Project Structure

```
health-analytics/
├── health                      # Unified CLI (executable)
├── serve.py                    # Dashboard HTTP server
├── dashboard/
│   ├── index.html             # Interactive multi-tab dashboard
│   └── data/                  # Generated JSON data files
├── scripts/
│   ├── icloud_helper.py       # iCloud file access utilities
│   ├── generate_dashboard_data.py
│   ├── deep_analysis.py       # Comprehensive analysis module
│   ├── daily_health_check.py
│   ├── weekly_summary.py
│   └── ...
├── src/health_analytics/
│   ├── config.py              # Centralized configuration
│   └── cache.py               # Disk-based caching layer
├── tests/
│   ├── unit/                  # Unit tests (212 tests)
│   └── integration/           # Integration tests
├── automation/
│   ├── setup.sh               # Automation setup script
│   └── com.health-analytics.daily-refresh.plist
├── data/                      # Symlink to iCloud health exports
└── logs/                      # Log files for automation
```

## Configuration

The project uses centralized configuration via `src/health_analytics/config.py`:

```python
from health_analytics.config import config

# Access paths
data_path = config.health_data_path
dashboard_path = config.dashboard_data_path
cache_dir = config.cache_dir
```

Environment variable overrides:
- `HEALTH_DATA_PATH` - Override health data location
- `DASHBOARD_DATA_PATH` - Override dashboard data location
- `HEALTH_ANALYTICS_CACHE_DIR` - Override cache directory

## Automation

Enable daily automatic dashboard refresh:

```bash
# Run the setup script
./automation/setup.sh

# Check if running
launchctl list | grep health-analytics

# View logs
tail -f logs/daily-refresh.log

# Disable
launchctl unload ~/Library/LaunchAgents/com.health-analytics.daily-refresh.plist
```

The dashboard automatically refreshes at 7:00 AM daily.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=scripts --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_cache.py -v

# Run only unit tests
pytest tests/ -m unit -v
```

Current status: **212 tests passing, 42% coverage**

## Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests with watch mode
ptw tests/ -v
```

## Data Privacy

- All data remains local (iCloud Drive)
- No external services or uploads
- Analysis runs locally on your machine

## Recent Updates

### v2.0 (January 2026)
- Added unified CLI interface with 10+ commands
- Implemented caching layer for 3x faster data access
- Added per-section error recovery in dashboard
- Added deep analysis module with trend detection
- Added automated daily refresh via launchd
- Expanded to 212 tests with TDD approach

### v1.0 (January 2026)
- Initial dashboard with activity trends
- iCloud-aware data access
- Basic data exploration scripts

## License

Private project - personal health data analysis.
