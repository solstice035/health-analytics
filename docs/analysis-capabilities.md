# Health Analytics - Analysis Capabilities

**Updated:** January 26, 2026  
**Status:** ✅ Fully Functional

## 🎯 What We Can Analyze

Your Apple Health data contains **25 different health metrics** tracked daily. Here's what we discovered from your recent data:

### 📊 Activity Metrics

**Daily Tracking:**
- **Steps** - Hourly step counts throughout the day
- **Distance** - Walking/running distance in kilometers
- **Active Energy** - Calories burned through activity
- **Exercise Minutes** - Apple Watch exercise time
- **Stand Hours** - Hours with at least 1 minute of standing
- **Flights Climbed** - Stairs climbed throughout the day
- **Time in Daylight** - Minutes spent outdoors

**Advanced Movement:**
- Walking speed (km/hr)
- Walking step length (cm)
- Walking asymmetry percentage
- Walking double support percentage
- Stair speed (up and down)

### ❤️ Heart Health

**Continuous Monitoring:**
- **Heart Rate** - 200-300 readings per day
- **Resting Heart Rate** - Daily resting baseline
- **Walking Heart Rate** - Average during walks
- **Heart Rate Variability (HRV)** - Stress/recovery indicator

**Fitness Metrics:**
- **VO2 Max** - Cardiovascular fitness score
- **Cardio Recovery** - Post-exercise recovery rate

### 🫁 Other Health Metrics

- **Blood Oxygen Saturation** - Multiple readings per day
- **Environmental Audio Exposure** - Noise level tracking
- **Physical Effort** - Exertion level (kcal/hr·kg)
- **Basal Energy Burned** - Base metabolic rate

## 📈 Analysis Scripts Available

### 1. Daily Health Check (`daily_health_check.py`)

**Purpose:** Quick daily monitoring  
**Run:** `python3 scripts/daily_health_check.py`

Shows:
- Data freshness (today + yesterday available?)
- File count and date range
- Quick yesterday summary

**Use case:** Run daily to verify data syncing properly

---

### 2. Detailed Analysis (`detailed_analysis.py`)

**Purpose:** Comprehensive single-day analysis  
**Run:** `python3 scripts/detailed_analysis.py 2026-01-25`

Shows:
- All daily totals (steps, energy, exercise, etc.)
- Key health readings (resting HR, HRV, VO2 max)
- Heart rate statistics (min/max/avg)
- All available metrics with data point counts

**Output Example:**
```
🚶 Steps:              12,670
📏 Distance:           9.84 km
🔥 Active Energy:      959 kcal
💪 Exercise Time:      82 minutes
🧍 Stand Hours:        15/12
💤 Resting HR:         57 bpm
📊 HRV:                56 ms
🏃 VO2 Max:            41.1 ml/(kg·min)
```

**Use case:** Daily deep-dive into health data

---

### 3. Weekly Summary (`weekly_summary.py`)

**Purpose:** Week-over-week trends and goal tracking  
**Run:** `python3 scripts/weekly_summary.py`

Shows:
- Daily breakdown table (7 days)
- Weekly averages for all metrics
- Health metric ranges (HR, HRV, etc.)
- Goal achievements (10K steps, 12 stand hours, 30min exercise)

**Output Example:**
```
📊 WEEKLY AVERAGES
🚶 Steps:              11,762/day  (total: 82,334)
📏 Distance:           9.9 km/day  (total: 69.2 km)
🔥 Active Energy:      886 kcal/day  (total: 6,205 kcal)

🎯 GOAL ACHIEVEMENTS
✓ 10,000 steps:        5/7 days
✓ 12 stand hours:      6/7 days
✓ 30min exercise:      7/7 days
```

**Use case:** Weekly review and trend tracking

---

### 4. Data Explorer (`explore_data.py`)

**Purpose:** Understand data structure and available metrics  
**Run:** `python3 scripts/explore_data.py`

Shows:
- Total files and date range
- JSON structure breakdown
- All available metric types
- Data point counts

**Use case:** Understanding what data is available

## 📊 Your Recent Week (Jan 19-25, 2026)

**Highlights:**
- ✅ Averaged **11,762 steps/day** (hit 10K+ on 5/7 days)
- ✅ Averaged **9.9 km distance/day**
- ✅ Burned **886 kcal/day** in active energy
- ✅ **82 minutes exercise/day** (met 30min goal every day!)
- ✅ **13.4 stand hours/day** (exceeded 12hr goal 6/7 days)
- ✅ Resting HR: **57 bpm** (consistent 54-63 range)
- ✅ VO2 Max: **40.9** (good cardiovascular fitness)

**Best Day:** Tuesday, Jan 20
- 15,588 steps
- 12.7 km distance
- 1,038 kcal active energy

## 🔮 Future Capabilities (To Build)

### Phase 1: Enhanced Analysis
- [ ] Monthly trends and comparisons
- [ ] Sleep pattern analysis (when sleep data structure is mapped)
- [ ] Workout type breakdown
- [ ] Day-of-week patterns (weekday vs weekend)
- [ ] Seasonal trends

### Phase 2: Visualizations
- [ ] Step count line charts over time
- [ ] Heart rate zone distribution
- [ ] Exercise time heatmap (time of day)
- [ ] Weekly comparison bar charts
- [ ] Correlation plots (sleep vs activity, etc.)

### Phase 3: Insights & Alerts
- [ ] Anomaly detection (unusually high/low days)
- [ ] Goal streak tracking
- [ ] Recovery score (based on HRV + resting HR)
- [ ] Activity recommendations
- [ ] Weekly email reports

### Phase 4: Integration
- [ ] Push reports to Obsidian notes
- [ ] Telegram notifications via Clawdbot
- [ ] Export to CSV for external analysis
- [ ] Dashboard web interface
- [ ] Integration with other health apps

## 🛠️ Technical Implementation

**Data Access:**
- ✅ Symlinked to iCloud Drive
- ✅ Automatic download handling
- ✅ Retry logic for sync conflicts
- ✅ No manual copying needed

**Data Processing:**
- JSON parsing with error handling
- Metric aggregation (sums, averages, ranges)
- Date range filtering
- Missing data handling

**Output:**
- Formatted console reports
- Structured data dictionaries
- Ready for export to other formats

## 📝 Notes

- Data updates automatically via Health Export app → iCloud sync
- All 175 days of historical data available (Aug 2025 - present)
- Scripts work seamlessly with daily automation
- Privacy: all data stays local, no external uploads

---

**Want to add new analysis?** The scripts are modular and easy to extend. All raw data is accessible via `icloud_helper.py`.
