---
created: 2026-01-26 21:00:00
updated: 2026-01-26 21:00:00
type: documentation
tags: [p/health-analytics, tech/python, dev, technical, python, health/data, reference]
---

# Health Analytics - Technical Details

> Technical documentation for the health analytics system architecture, data structures, and implementation details

## 🏗️ System Architecture

### Data Flow

```mermaid
graph LR
    A[Apple Health] -->|Health Export App| B[iOS Device]
    B -->|Auto Sync| C[iCloud Drive]
    C -->|Symlink| D[Local Data Dir]
    D -->|icloud_helper.py| E[Python Scripts]
    E -->|Analysis| F[JSON Data]
    F -->|Chart.js| G[Web Dashboard]
```

### Components

**1. Data Source**
- Apple Health database on iOS
- Health Auto Export app (daily automation)
- iCloud Drive sync (~516 MB for 175 days)

**2. Data Access Layer**
- Symlink: `data/` → iCloud health exports
- `icloud_helper.py`: Handle file locking, downloads, retries
- Zero manual intervention required

**3. Analysis Engine**
- 7 Python scripts for different analysis types
- Modular design, each script standalone
- Shared utilities in `icloud_helper.py`

**4. Dashboard Generator**
- `generate_dashboard_data.py`: Transform health data to chart-ready JSON
- 5 JSON files generated (trends, comparisons, goals, stats, metadata)
- Optimized data structures for Chart.js

**5. Web Dashboard**
- Single HTML file with embedded CSS/JS
- Chart.js for visualizations
- No backend or build process
- Auto-refresh capability

## 📊 Data Structures

### Health Export JSON Format

**File naming:**
```
HealthAutoExport-YYYY-MM-DD.json
```

**Structure:**
```json
{
  "data": {
    "metrics": [
      {
        "name": "step_count",
        "units": "count",
        "data": [
          {
            "qty": 123.45,
            "date": "2026-01-25 08:30:00 +0000",
            "source": "Apple Watch"
          },
          // ... more data points
        ]
      },
      // ... 24 more metric types
    ]
  }
}
```

**Metric Types:**

| Category | Metrics | Data Points/Day |
|----------|---------|-----------------|
| Activity | steps, distance, energy, exercise, stands, flights | 500-1500 |
| Heart | heart_rate, resting_hr, walking_hr, hrv, vo2_max | 200-300 |
| Other | blood_oxygen, audio_exposure, physical_effort | 10-100 |

### Dashboard JSON Format

**daily_trends.json:**
```json
{
  "dates": ["2026-01-01", "2026-01-02", ...],
  "steps": [10234, 12456, ...],
  "distance": [8.2, 9.5, ...],
  "active_energy": [850, 920, ...],
  "exercise_minutes": [65, 72, ...],
  "stand_hours": [12, 11, ...],
  "resting_hr": [58, 57, ...],
  "hrv": [45, 43, ...]
}
```

**summary_stats.json:**
```json
{
  "period": "2026-01-19 to 2026-01-25",
  "days_count": 7,
  "totals": {
    "steps": 82334,
    "distance_km": 69.2,
    "active_energy_kcal": 6205,
    "exercise_minutes": 576
  },
  "averages": {
    "steps": 11762,
    "distance_km": 9.9,
    "active_energy_kcal": 886,
    "exercise_minutes": 82,
    "stand_hours": 13.4,
    "resting_hr": 57,
    "hrv": 43
  },
  "goals": {
    "steps_10k": {"achieved": 5, "total": 7},
    "stand_12h": {"achieved": 6, "total": 7},
    "exercise_30m": {"achieved": 7, "total": 7}
  }
}
```

## 🔧 Python Implementation

### iCloud Helper Utilities

**Key Functions:**

```python
def ensure_downloaded(file_path, timeout=30):
    """
    Ensure iCloud file is fully downloaded.
    
    - Checks file size (0 = placeholder)
    - Triggers download with brctl
    - Retries on lock errors
    - Returns True when accessible
    """

def read_json_safe(file_path, max_retries=3, retry_delay=1.0):
    """
    Safely read JSON from iCloud with retry logic.
    
    - Handles "Resource deadlock avoided" errors
    - Auto-downloads if needed
    - Retries with exponential backoff
    - Returns parsed JSON or None
    """

def get_icloud_status(file_path):
    """
    Check iCloud download status.
    
    Returns: 'downloaded', 'downloading', 'placeholder', 'unknown'
    """
```

**Why This Works:**
- iCloud files can be "placeholders" (0 bytes) until accessed
- Direct reads fail with errno 11 (Resource deadlock avoided)
- `brctl download` triggers iCloud to download the file
- Retry logic handles race conditions during sync

### Analysis Scripts Architecture

**Common Pattern:**

```python
#!/usr/bin/env python3
"""Script description."""

from pathlib import Path
from icloud_helper import read_json_safe

HEALTH_DATA_PATH = Path(__file__).parent.parent / "data"

def extract_metrics(data):
    """Parse health export JSON."""
    # Implementation
    
def analyze_date(date_str):
    """Perform analysis."""
    file_path = HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"
    data = read_json_safe(file_path)
    # Analysis logic

if __name__ == "__main__":
    # CLI interface
```

**Benefits:**
- Each script is standalone
- Shared utilities imported
- Consistent error handling
- Simple CLI interface

## 📈 Dashboard Implementation

### Chart.js Configuration

**30-Day Trends (Dual-Axis Line Chart):**

```javascript
new Chart(ctx, {
    type: 'line',
    data: {
        labels: dates,
        datasets: [{
            label: 'Steps',
            data: steps,
            borderColor: '#007AFF',
            yAxisID: 'y'  // Left axis
        }, {
            label: 'Active Energy',
            data: energy,
            borderColor: '#FF9500',
            yAxisID: 'y1'  // Right axis
        }]
    },
    options: {
        scales: {
            y: { position: 'left', title: { text: 'Steps' } },
            y1: { position: 'right', title: { text: 'Energy' } }
        }
    }
});
```

**Weekly Comparison (Bar Chart):**

```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: weeks,
        datasets: [{
            label: 'Avg Steps',
            data: avgSteps,
            backgroundColor: '#007AFF'
        }]
    }
});
```

**Goal Progress (Stacked Bars):**

```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Mon', 'Tue', 'Wed', ...],
        datasets: [{
            label: '10K Steps',
            data: [1, 1, 1, 0, 1, 1, 1],  // 1=achieved, 0=missed
            backgroundColor: '#007AFF'
        }, {
            label: '12 Stand Hours',
            data: [1, 1, 1, 0, 1, 1, 1],
            backgroundColor: '#34C759'
        }, {
            label: '30min Exercise',
            data: [1, 1, 1, 1, 1, 1, 1],
            backgroundColor: '#FF9500'
        }]
    }
});
```

### Performance Optimizations

**Data Loading:**
- JSON files cached in browser for 5 minutes
- Lazy loading (charts render on scroll if needed)
- Minimal data points (30 days vs 175 days available)

**Chart Rendering:**
- Chart.js animations disabled for faster load
- Responsive resize debounced
- Data pre-aggregated in Python (no client-side heavy processing)

**File Sizes:**
- `daily_trends.json`: ~2.5 KB
- `weekly_comparison.json`: ~400 bytes
- `summary_stats.json`: ~600 bytes
- Total: < 5 KB for all data

## 🔒 Security Considerations

### Data Privacy

**Local-Only Processing:**
- All analysis runs on Mac Mini
- No external API calls (except Chart.js CDN)
- Health data never leaves local network
- JSON files explicitly git-ignored

**iCloud Security:**
- Files stay in Apple's iCloud Drive
- End-to-end encryption (if enabled on account)
- Symlink provides read-only access

### Deployment Security

**Recommended Practices:**

1. **HTTPS Always**
   - Let's Encrypt for free SSL
   - Cloudflare for automatic SSL

2. **Authentication**
   - Basic HTTP auth (nginx)
   - OAuth/SSO (Cloudflare Access, Auth0)
   - VPN access (Tailscale, WireGuard)
   - IP whitelist

3. **Access Control**
   ```nginx
   # Basic auth example
   auth_basic "Health Dashboard";
   auth_basic_user_file /etc/nginx/.htpasswd;
   
   # IP whitelist example
   allow 1.2.3.4;  # Your IP
   deny all;
   ```

## 🚀 Performance Metrics

**Data Generation:**
- 30 days: ~8 seconds
- 90 days: ~25 seconds
- 175 days: ~45 seconds

**Dashboard Load Time:**
- Initial load: < 1 second
- Chart render: < 500ms
- Auto-refresh: < 200ms

**Memory Usage:**
- Python scripts: ~50 MB
- Dashboard (browser): ~30 MB

**Storage:**
- Source data: 516 MB (175 days)
- Generated JSON: < 5 KB
- Dashboard code: ~16 KB

## 🔧 Troubleshooting

### Common Issues

**"Resource deadlock avoided"**
- *Cause:* iCloud file still syncing
- *Solution:* `icloud_helper.py` handles automatically with retries

**Charts not rendering**
- *Cause:* JSON files missing or malformed
- *Solution:* Re-run `generate_dashboard_data.py`

**Stale data**
- *Cause:* Browser cache
- *Solution:* Hard refresh (Cmd+Shift+R)

**No data for today**
- *Cause:* Health Export runs once daily (usually morning)
- *Solution:* Expected behavior, yesterday's data is latest complete

## 📚 Dependencies

### Python

```txt
# No external dependencies for core functionality!
# Standard library only:
- json (JSON parsing)
- pathlib (file paths)
- datetime (date handling)
- collections (data structures)
- subprocess (brctl for iCloud)
```

**Optional (for future enhancements):**
```txt
pandas>=2.0.0         # Advanced data manipulation
numpy>=1.24.0         # Numerical operations
matplotlib>=3.7.0     # Static charts
plotly>=5.14.0        # Interactive plots
jupyter>=1.0.0        # Notebooks
```

### JavaScript

```html
<!-- Only external dependency -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
```

## 🔗 References

- [[Health Analytics|Main Project Page]]
- [[Health Analytics - Analysis Scripts|Analysis Scripts]]
- [[Health Analytics - Deployment Guide|Deployment Guide]]

## 📝 Technical Decisions

**Why symlink instead of copy?**
- Preserves daily automation
- No manual sync needed
- Always access latest data
- Saves disk space

**Why Python standard library only?**
- Faster execution
- No dependency management
- Simpler deployment
- Smaller footprint

**Why static dashboard?**
- No backend required
- Deploy anywhere
- Fast loading
- Easy to maintain

**Why Chart.js?**
- Lightweight (< 200KB)
- Beautiful defaults
- Good documentation
- Active development

---

**Maintained by:** Nick  
**Last updated:** 2026-01-26  
**Version:** 1.0
