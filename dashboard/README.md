# Health Analytics Dashboard

Interactive web dashboard for visualizing Apple Health data.

## 📊 Features

- **30-Day Activity Trends** - Steps and active energy over time
- **Weekly Comparison** - 12-week step count averages
- **7-Day Goal Progress** - Track daily goal achievements
- **Summary Statistics** - Key metrics at a glance

**Visualizations Include:**
- Steps, distance, active energy, exercise time
- Heart rate and HRV
- Goal tracking (10K steps, 12 stand hours, 30min exercise)

## 🚀 Quick Start

### View Locally

1. **Generate dashboard data:**
   ```bash
   cd ~/clawd/projects/health-analytics
   python3 scripts/generate_dashboard_data.py
   ```

2. **Open dashboard:**
   ```bash
   open dashboard/index.html
   ```

### Update Dashboard

Run the update script to refresh with latest data:
```bash
cd ~/clawd/projects/health-analytics/dashboard
./update.sh
```

Or manually:
```bash
cd ~/clawd/projects/health-analytics
python3 scripts/generate_dashboard_data.py
```

## 🌐 Deployment

The dashboard is a static web app (HTML + JavaScript + JSON data). Deploy to any web server:

### Option 1: Simple HTTP Server (Local Testing)

```bash
cd ~/clawd/projects/health-analytics/dashboard
python3 -m http.server 8000
# Visit http://localhost:8000
```

### Option 2: Personal Domain (Production)

The dashboard can be deployed to your personal domain. You'll need:

1. **Web server** (nginx, Apache, or static hosting like Netlify/Vercel)
2. **Domain name** pointed to your server
3. **SSL certificate** (Let's Encrypt recommended)

**File structure to deploy:**
```
your-domain.com/health/
├── index.html          (Dashboard)
├── data/               (JSON data files)
│   ├── daily_trends.json
│   ├── weekly_comparison.json
│   ├── goals_progress.json
│   ├── summary_stats.json
│   ├── hr_distribution.json
│   └── metadata.json
```

**For automated updates on your server:**

1. Set up SSH access to your web server
2. Create an update script that:
   - Generates fresh JSON data locally
   - Syncs to your web server via rsync/scp
   - Or: Run the generation script directly on the server

Example rsync command:
```bash
rsync -avz ~/clawd/projects/health-analytics/dashboard/ \
  user@your-domain.com:/var/www/health/
```

### Option 3: Automated Deployment with GitHub Actions

Push dashboard to GitHub, use GitHub Pages or Actions to:
1. Generate data from health exports
2. Deploy to hosting service
3. Update on schedule or manual trigger

## 🔄 Auto-Refresh

The dashboard automatically refreshes data every 5 minutes when open in browser.

To update the underlying data:
- Run `./update.sh` or the generate script
- Set up a cron job for automatic updates:

```bash
# Update dashboard data every day at 8 AM
0 8 * * * cd /Users/nick/clawd/projects/health-analytics && python3 scripts/generate_dashboard_data.py
```

## 📁 Data Files

The dashboard loads from these JSON files in `data/`:

- `daily_trends.json` - 30 days of daily metrics
- `weekly_comparison.json` - 12 weeks of averages
- `goals_progress.json` - 7-day goal achievements
- `summary_stats.json` - Current week statistics
- `hr_distribution.json` - Heart rate zone breakdown
- `metadata.json` - Generation timestamp and data range

## 🎨 Customization

### Colors

Edit CSS variables in `index.html`:
```css
:root {
    --accent-blue: #007AFF;
    --accent-green: #34C759;
    --accent-orange: #FF9500;
    /* ... */
}
```

### Goals

Edit goal thresholds in `generate_dashboard_data.py`:
- Steps: currently 10,000
- Stand hours: currently 12
- Exercise: currently 30 minutes

### Charts

Charts use [Chart.js](https://www.chartjs.org/). Customize in the `<script>` section of `index.html`.

## 🔒 Privacy & Security

**Important:** This dashboard displays personal health data!

- Use HTTPS when deploying to web
- Consider authentication (basic auth, OAuth, etc.)
- Don't commit `data/*.json` files to public repos
- The dashboard itself is safe to share (it's just HTML/JS)
- Keep the JSON data files private

## 📱 Mobile Support

Dashboard is fully responsive and works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Tablets
- Smartphones

## 🛠️ Technical Details

**Technologies:**
- HTML5, CSS3, JavaScript (ES6+)
- [Chart.js](https://www.chartjs.org/) for visualizations
- No backend required - fully static

**Browser Requirements:**
- Modern browser with ES6 support
- JavaScript enabled
- Local file access or web server for AJAX (JSON loading)

## 📈 Future Enhancements

Potential additions:
- More chart types (heatmaps, scatter plots)
- Date range selector
- Export data as CSV
- Sleep analysis charts
- Monthly/yearly views
- Comparison with historical averages
- Dark/light mode toggle

---

**Generated:** January 26, 2026  
**Data Source:** Apple Health via Health Auto Export app
