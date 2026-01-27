# Resume Health Analytics Project

**Quick start guide to resume where we left off**

---

## Quick Resume

```bash
# 1. Navigate and activate
cd ~/clawd/projects/health-analytics
source venv/bin/activate

# 2. Verify everything works
pytest tests/ -v --tb=short
./health status

# 3. Start dashboard
./health dashboard
```

---

## Current Status

```
Code Coverage:    42%
Tests Passing:    231/231 (100%)
Tasks Completed:  10/10 (100%)
```

---

## What's Built

### Core Functionality
- **Unified CLI** (`./health`) - Single entry point with 11 subcommands
- **Dashboard** - Interactive multi-tab health data visualization
- **Caching Layer** - JSON-based caching with auto-invalidation
- **Configuration System** - Centralized config with env var overrides
- **Daily Automation** - launchd service for automatic refresh at 7 AM

### CLI Commands
```bash
./health status      # System status overview
./health dashboard   # Start dashboard server
./health generate    # Generate dashboard data
./health daily       # Daily health check
./health analyze     # Analyze specific date
./health weekly      # Weekly summary
./health deep        # Deep analysis
./health cache       # Cache management (stats/clear/warm)
./health config      # Show configuration
./health explore     # Explore data structure
```

### Testing
- **Unit Tests** - 190+ tests covering analytics, config, cache, CLI
- **Integration Tests** - Dashboard resilience, error recovery
- **E2E Tests** - Playwright browser tests for UI/UX

---

## Key Files

### Entry Points
- `health` - Unified CLI script (executable)
- `serve.py` - Dashboard HTTP server
- `dashboard/index.html` - Interactive dashboard

### Core Modules
- `src/health_analytics/config.py` - Configuration management
- `src/health_analytics/cache.py` - Caching layer
- `src/health_analytics/analytics.py` - Analytics engine

### Scripts
- `scripts/generate_dashboard_data.py` - Data generation
- `scripts/daily_health_check.py` - Daily checks
- `scripts/deep_analysis.py` - Comprehensive analysis
- `scripts/icloud_helper.py` - iCloud file access

### Automation
- `automation/setup.sh` - Install daily refresh service
- `automation/com.health-analytics.daily-refresh.plist` - launchd config

### Tests
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - Playwright E2E tests

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# E2E tests only
pytest tests/e2e/ -v

# With coverage
pytest tests/ --cov=scripts --cov-report=html
open htmlcov/index.html
```

---

## Automation Setup

```bash
# Install daily refresh (runs at 7 AM)
./automation/setup.sh

# Check status
launchctl list | grep health-analytics

# View logs
tail -f logs/daily-refresh.log
```

---

## Completed Tasks

1. Testing infrastructure
2. icloud_helper tests and fixes
3. Dashboard CORS fix (serve.py)
4. HR distribution chart
5. Configuration system
6. Package structure (src/health_analytics/)
7. Dashboard error recovery (per-section)
8. Deep analysis module
9. Caching layer
10. Unified CLI interface
11. Daily automation (launchd)
12. E2E Playwright tests

---

## Architecture

```
health-analytics/
├── health                  # CLI entry point
├── serve.py               # Dashboard server
├── dashboard/
│   ├── index.html         # Multi-tab dashboard
│   └── data/              # Generated JSON data
├── src/health_analytics/  # Core library
│   ├── config.py          # Configuration
│   ├── cache.py           # Caching
│   └── analytics.py       # Analytics
├── scripts/               # Analysis scripts
├── automation/            # launchd service
└── tests/
    ├── unit/              # Unit tests
    ├── integration/       # Integration tests
    └── e2e/               # Playwright E2E tests
```

---

## Environment Variables

- `HEALTH_DATA_PATH` - Override health data location
- `DASHBOARD_DATA_PATH` - Override dashboard data location
- `HEALTH_ANALYTICS_CACHE_DIR` - Override cache directory

---

## Troubleshooting

### Tests Failing?
```bash
rm -rf .pytest_cache htmlcov .coverage
pip install -r requirements.txt
pytest tests/ -v
```

### Dashboard Not Loading?
```bash
./health status        # Check data paths
./health generate      # Regenerate data
./health dashboard     # Start server
```

### Import Errors?
```bash
source venv/bin/activate
which python  # Should show venv/bin/python
```
