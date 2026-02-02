---
created: 2026-01-26 20:25:00
updated: 2026-01-26 21:00:00
type: project
status: active
priority: medium
tags: [p/health-analytics, tech/python, dev, project/dev, health/analytics, python, data-visualization, personal]
---

# Health Analytics Dashboard

> Interactive web dashboard for analyzing and visualizing Apple Health data with automated iCloud sync

## 📊 Project Overview

**Status:** 🟢 Complete & Deployed Locally  
**Created:** January 26, 2026  
**Location:** `~/clawd/projects/health-analytics/`  
**Repository:** Local (ready for GitHub push)

A comprehensive health analytics system that automatically syncs Apple Health exports from iCloud, processes 25+ health metrics, and presents them through an interactive web dashboard with beautiful visualizations.

## 🎯 Goals & Outcomes

### Primary Goals
- [x] Automated access to iCloud health data (no manual copying)
- [x] Parse and analyze 25 different health metrics
- [x] Create interactive web dashboard with visualizations
- [x] Track daily goals and weekly trends
- [ ] Deploy to personal domain with automated updates
- [ ] Integrate daily summaries with Clawdbot notifications

### Key Outcomes Achieved
- **175 days** of historical health data accessible
- **5 comprehensive analysis scripts** built
- **Interactive dashboard** with 30-day trends, weekly comparisons, and goal tracking
- **Automated data pipeline** via iCloud symlink
- **Deployment-ready** static web app

## 📈 Current Insights (Jan 19-25, 2026)

**Weekly Averages:**
- 🚶 Steps: 11,762/day (5/7 days hit 10K goal)
- 📏 Distance: 9.9 km/day
- 🔥 Active Energy: 886 kcal/day
- 💪 Exercise: 82 min/day (7/7 days hit 30min goal)
- 🧍 Stand Hours: 13.4/day (6/7 days hit 12hr goal)

**Health Metrics:**
- ❤️ Resting HR: 57 bpm (range: 54-63)
- 📊 HRV: 43 ms average
- 🫁 Blood Oxygen: 97%
- 🏃 VO2 Max: 40.9 ml/(kg·min)

## 🛠️ Technical Architecture

### Data Pipeline
```
Health Auto Export (iOS) 
    ↓ (automatic daily)
iCloud Drive Sync
    ↓ (symlink)
~/clawd/projects/health-analytics/data/
    ↓ (icloud_helper.py)
Python Analysis Scripts
    ↓ (generate_dashboard_data.py)
JSON Data Files
    ↓ (Chart.js)
Interactive Web Dashboard
```

### Technology Stack

**Backend Processing:**
- Python 3.11+ (data analysis)
- Custom iCloud file access utilities
- JSON data serialization

**Dashboard:**
- HTML5 + CSS3 (responsive design)
- JavaScript (ES6+)
- Chart.js 4.4+ (visualizations)
- Static site (no backend required)

**Data Source:**
- Apple Health via Health Auto Export app
- Daily automated exports to iCloud
- 175 days of historical data
- 25+ health metrics tracked

## 📁 Project Structure

```
health-analytics/
├── dashboard/
│   ├── index.html              # Main dashboard (HTML/CSS/JS)
│   ├── data/                   # Generated JSON data
│   │   ├── daily_trends.json
│   │   ├── weekly_comparison.json
│   │   ├── goals_progress.json
│   │   ├── summary_stats.json
│   │   └── metadata.json
│   ├── update.sh               # Quick update script
│   └── README.md               # Dashboard docs
│
├── scripts/
│   ├── icloud_helper.py         # iCloud file access utilities
│   ├── daily_health_check.py    # Daily monitoring
│   ├── detailed_analysis.py     # Single-day deep dive
│   ├── weekly_summary.py        # 7-day trends & goals
│   ├── generate_dashboard_data.py # Dashboard JSON generator
│   ├── explore_data.py          # Data structure explorer
│   └── analyze_specific_date.py # Date-specific analysis
│
├── data/                       # Symlink to iCloud health exports
├── notebooks/                  # Jupyter notebooks (future)
├── visualizations/             # Generated charts (future)
│
├── README.md                   # Project documentation
├── ANALYSIS_CAPABILITIES.md    # Available metrics & scripts
├── CURRENT_STATUS.md           # Technical status
├── NEXT_STEPS.md              # Action items
├── DEPLOYMENT.md              # Deployment guide
├── requirements.txt           # Python dependencies
└── .gitignore                 # Git ignore rules
```

## 🎨 Dashboard Features

### Visualizations

**30-Day Activity Trends**
- Dual-axis line chart (steps + active energy)
- Smooth curves with hover tooltips
- Shows activity patterns over time

**12-Week Comparison**
- Bar chart of weekly step averages
- Easy week-over-week comparison
- Identifies trends and consistency

**7-Day Goal Progress**
- Stacked bar chart for daily goals
- Tracks 3 goals: 10K steps, 12hr stands, 30min exercise
- Visual ✓/✗ indicators

**Summary Statistics**
- 6 stat cards with key metrics
- Green badges for goals achieved
- Real-time weekly averages

### Technical Features
- Auto-refresh every 5 minutes
- Fully responsive (mobile/tablet/desktop)
- Dark theme optimized for health data
- Interactive charts with tooltips
- Privacy-focused (data stays local)

## 📊 Available Health Metrics

**Activity (9 metrics):**
- Steps, distance, active energy
- Exercise minutes, stand hours
- Flights climbed, time in daylight
- Walking speed, step length, asymmetry

**Heart Health (6 metrics):**
- Heart rate (200-300 readings/day)
- Resting heart rate, walking HR
- Heart rate variability (HRV)
- VO2 max, cardio recovery

**Other Metrics (10+):**
- Blood oxygen saturation
- Environmental audio exposure
- Physical effort levels
- Basal energy burned
- Stair speeds (up/down)
- Walking support percentages

*Total: 25+ metrics tracked daily*

## 🚀 Usage

### View Dashboard Locally

```bash
# Generate latest data
cd ~/clawd/projects/health-analytics
python3 scripts/generate_dashboard_data.py

# Open in browser
open dashboard/index.html
```

### Quick Update

```bash
cd ~/clawd/projects/health-analytics/dashboard
./update.sh
```

### Command-Line Analysis

```bash
# Daily health check
python3 scripts/daily_health_check.py

# Detailed single-day analysis
python3 scripts/detailed_analysis.py 2026-01-25

# Weekly summary with goals
python3 scripts/weekly_summary.py

# Explore data structure
python3 scripts/explore_data.py
```

## 🌐 Deployment Options

Dashboard is deployment-ready as a static web app:

### Option 1: Static Hosting (Recommended)
- Netlify, Vercel, Cloudflare Pages
- Free SSL included
- Automated updates via GitHub Actions

### Option 2: Self-Hosted VPS
- Full control with nginx
- Automated rsync from Mac Mini
- Basic auth for privacy
- Let's Encrypt SSL

### Option 3: GitHub Pages
- Free hosting
- Version controlled
- Automated builds

**See:** `DEPLOYMENT.md` for complete setup guides

## 🔐 Privacy & Security

**Data Privacy:**
- All health data stays local
- No external services or APIs
- JSON data files git-ignored
- Dashboard HTML/JS is public-safe

**Security Considerations:**
- Use HTTPS when deployed
- Consider basic auth or OAuth
- IP whitelist option available
- VPN access for maximum security

## 🔄 Automation

### Current Automation
- Health Export app → iCloud (automatic daily)
- Scripts use iCloud symlink (automatic access)
- Dashboard auto-refresh (5 minutes when open)

### Planned Automation
- [ ] Launchd job for daily data generation
- [ ] Automated deployment to web server
- [ ] Daily summary notifications via Clawdbot
- [ ] Weekly summary emails

## 📋 Next Steps

### Immediate (This Week)
- [ ] Deploy dashboard to personal domain
- [ ] Set up automated daily sync script
- [ ] Configure nginx with SSL
- [ ] Test mobile access

### Short Term (This Month)
- [ ] Integrate with Clawdbot for notifications
- [ ] Add monthly trend analysis
- [ ] Build sleep analysis charts
- [ ] Create correlation visualizations

### Long Term (Future)
- [ ] Machine learning predictions
- [ ] Anomaly detection & alerts
- [ ] Compare with historical averages
- [ ] Export reports to Obsidian
- [ ] Multi-device sync dashboard

## 🔗 Related Notes

- [[Health Analytics - Technical Details]]
- [[Health Analytics - Analysis Scripts]]
- [[Health Analytics - Deployment Guide]]
- [[ClawdBot Set-up|ClawdBot Setup]]
- [[Productivity|Productivity Tools]]

## 📝 Development Log

**2026-01-26 (Evening):**
- ✅ Project created and structured
- ✅ Solved iCloud file access (symlink + helper utilities)
- ✅ Built 7 comprehensive analysis scripts
- ✅ Created interactive web dashboard
- ✅ Tested with 175 days of health data
- ✅ Generated visualizations (30-day trends, weekly comparison, goal tracking)
- ✅ Documented deployment options
- ✅ Ready for GitHub push
- ✅ Ready for domain deployment

**Key Decisions:**
- Used symlink instead of copying (preserves daily automation)
- Built iCloud helper utilities to handle sync conflicts
- Static dashboard (no backend) for easy deployment
- Chart.js for interactive visualizations
- Privacy-first approach (local data only)

## 💡 Lessons Learned

1. **iCloud File Access:** Direct reads fail with "Resource deadlock avoided" - solution was custom helper with `brctl` triggers and retry logic

2. **Data Structure:** Health Export uses metric-based JSON (25 types), each with timestamp and quantity arrays

3. **Dashboard Design:** Dark theme + Chart.js provides professional health analytics look

4. **Deployment Strategy:** Static site approach allows flexible hosting without server requirements

## 🎯 Success Metrics

- [x] Access 100% of health data automatically
- [x] Parse all 25 available health metrics
- [x] Create functional dashboard with 3+ visualizations
- [x] Mobile-responsive design
- [x] < 30 second data generation time
- [ ] Live deployment on personal domain
- [ ] Daily automated updates
- [ ] Integration with notification system

---

**Project Value:** Personal health insights, automated tracking, beautiful visualizations  
**Time Investment:** ~6 hours initial build  
**Maintenance:** ~5 min/week for monitoring  
**ROI:** High - daily health visibility & trend awareness
