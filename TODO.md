# Health Analytics Dashboard - TODO List

**Project:** Apple Health Data Analytics Dashboard  
**Location:** `~/clawd/projects/health-analytics/`  
**Status:** 🟢 Fully Functional - Ready for Next Phase  
**Created:** January 27, 2026

---

## 🎯 Priority Tasks (Pick Up Here)

### 1. Deploy Dashboard 📡
**Priority:** HIGH  
**Effort:** 2-3 hours  
**Status:** Ready to deploy

**Options:**
- [ ] **Option A: Netlify/Vercel (Easiest)**
  - Set up GitHub repo
  - Connect to Netlify/Vercel
  - Configure build command: `python3 scripts/generate_dashboard_data.py`
  - Set publish directory: `dashboard`
  - Add custom domain (optional)

- [ ] **Option B: Self-Host on VPS**
  - Set up nginx
  - Configure SSL (Let's Encrypt)
  - Set up automated data sync from Mac Mini
  - See `DEPLOYMENT.md` for full guide

**Deliverable:** Publicly accessible dashboard URL

---

### 2. Automate Daily Updates 🔄
**Priority:** HIGH  
**Effort:** 1-2 hours  
**Status:** Waiting on deployment

**Tasks:**
- [ ] Set up cron job for daily data refresh
  ```bash
  # Run at 00:30 daily after Health Export sync
  30 0 * * * cd ~/clawd/projects/health-analytics && python3 scripts/generate_dashboard_data.py
  ```

- [ ] Integrate with Clawdbot for morning notifications
  - [ ] Create morning health summary message
  - [ ] Send via Telegram at 09:00 daily
  - [ ] Include: yesterday's stats, weekly trends, goal achievements

- [ ] Weekly summary reports
  - [ ] Generate comprehensive weekly report
  - [ ] Send via Telegram every Monday 09:00
  - [ ] Include: 7-day averages, personal records, insights

**Deliverable:** Automated dashboard updates + daily/weekly Telegram notifications

---

### 3. Enhanced Analysis Features 🔬
**Priority:** MEDIUM  
**Effort:** 4-6 hours  
**Status:** Ready to build

**Sleep Analysis:**
- [ ] Map sleep data structure in JSON
- [ ] Create sleep analysis script
- [ ] Calculate: total sleep, sleep efficiency, bedtime consistency
- [ ] Visualize: sleep duration trends, bedtime/wake time patterns
- [ ] Add to dashboard

**Monthly Trends:**
- [ ] Create monthly aggregation script
- [ ] Compare month-over-month changes
- [ ] Identify seasonal patterns
- [ ] Add monthly view to dashboard

**Day-of-Week Patterns:**
- [ ] Analyze weekday vs weekend differences
- [ ] Create day-of-week comparison charts
- [ ] Identify activity patterns by day
- [ ] Add to dashboard insights

**Correlation Analysis:**
- [ ] Sleep vs activity correlation
- [ ] Activity vs heart rate patterns
- [ ] Weather impact on activity (if data available)
- [ ] Create correlation matrix visualization

**Deliverable:** Enhanced analysis scripts + updated dashboard with new insights

---

### 4. Obsidian Integration 📝
**Priority:** MEDIUM  
**Effort:** 2-3 hours  
**Status:** Ready to implement

**Tasks:**
- [ ] Create daily health note template
- [ ] Auto-generate daily notes in Obsidian vault
  - Location: `~/obsidian/claude/2-Areas/Health/`
  - Format: `YYYY-MM-DD-health-summary.md`
  - Include: stats, trends, notable achievements

- [ ] Weekly health notes
  - Auto-generate every Monday
  - Location: `~/obsidian/claude/2-Areas/Health/Weekly/`
  - Include: 7-day summary, insights, goals

- [ ] Link to daily notes
  - Add health summary section to daily notes
  - Link to detailed health note
  - Include quick stats inline

**Deliverable:** Automated health notes in Obsidian vault

---

## 📊 Current Status Summary

### ✅ What's Working
- Interactive web dashboard (30-day trends, goal tracking)
- 6 command-line analysis scripts
- iCloud data sync automation
- 175 days of historical data (Aug 2025 - Jan 2026)
- 25 health metrics tracked

### 📈 Recent Data (Jan 19-25)
- **Steps:** 11,762/day avg (hit 10K+ on 5/7 days)
- **Distance:** 9.9 km/day
- **Active Energy:** 886 kcal/day
- **Exercise:** 82 min/day (met 30min goal every day!)
- **Stand Hours:** 13.4/day (exceeded 12hr goal 6/7 days)
- **Resting HR:** 57 bpm (range: 54-63)
- **HRV:** 56 ms
- **VO2 Max:** 40.9

### 🛠️ Available Scripts
```bash
# View dashboard
cd ~/clawd/projects/health-analytics && python serve.py

# Daily check
python3 scripts/daily_health_check.py

# Detailed analysis
python3 scripts/detailed_analysis.py 2026-01-25

# Weekly summary
python3 scripts/weekly_summary.py

# Generate dashboard data
python3 scripts/generate_dashboard_data.py
```

---

## 💡 Future Ideas (Backlog)

### Phase 2 Enhancements
- [ ] Mobile app integration
- [ ] Compare with friends (anonymized)
- [ ] Goal setting and tracking system
- [ ] Achievements and milestones
- [ ] Export to CSV/PDF reports
- [ ] Machine learning predictions
- [ ] Anomaly detection
- [ ] Workout type breakdown
- [ ] Nutrition tracking integration
- [ ] Weather correlation analysis

### Phase 3 Integrations
- [ ] Strava integration
- [ ] MyFitnessPal integration
- [ ] Oura Ring data (if applicable)
- [ ] Whoop data (if applicable)
- [ ] Google Fit backup
- [ ] Apple Watch complications

---

## 🔗 Related Files

- **Project Root:** `~/clawd/projects/health-analytics/`
- **Documentation:** `README.md`, `CURRENT_STATUS.md`, `NEXT_STEPS.md`
- **Deployment Guide:** `DEPLOYMENT.md`
- **Analysis Capabilities:** `ANALYSIS_CAPABILITIES.md`
- **Dashboard:** `dashboard/index.html`
- **Scripts:** `scripts/*.py`
- **Data:** Symlinked to iCloud Drive

---

## 📝 Notes for Claude Code

**When picking up this project:**

1. **Quick Start:**
   ```bash
   cd ~/clawd/projects/health-analytics
   python3 scripts/daily_health_check.py  # Verify data access
   python serve.py  # View current dashboard
   ```

2. **Data Source:**
   - Location: `~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/JSON/`
   - Files: `HealthAutoExport-YYYY-MM-DD.json` (daily exports)
   - Access: Use `scripts/icloud_helper.py` for reliable file reading

3. **Architecture:**
   - Backend: Python scripts for data analysis
   - Frontend: Static HTML/CSS/JS dashboard
   - Data Flow: iCloud → Python processing → JSON output → Dashboard visualization
   - Charts: Chart.js library

4. **Testing:**
   - Always test with recent data first
   - Use `scripts/explore_data.py` to understand JSON structure
   - Check `scripts/icloud_helper.py` for data access patterns

5. **Deployment Considerations:**
   - Dashboard is static files (easy to deploy)
   - Data generation runs locally (Mac Mini has iCloud access)
   - Consider scheduling data updates before dashboard rebuild

---

**Priority Order:** Deploy (1) → Automate (2) → Enhance (3) → Integrate (4)

**Estimated Total Time:** 9-14 hours for all priority tasks

**Ready to Start!** 🚀
