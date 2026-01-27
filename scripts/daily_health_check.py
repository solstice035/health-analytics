#!/usr/bin/env python3
"""
Daily Health Check - Automated health data monitoring.

Runs daily to:
1. Check for new health data files from iCloud
2. Ensure recent files are accessible
3. Generate a quick summary of yesterday's data
4. Alert if data is missing or stale

Designed to run via cron or launchd.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add src to path for config module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import iCloud helper
try:
    from icloud_helper import read_json_safe, get_icloud_status
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from icloud_helper import read_json_safe, get_icloud_status

# Use centralized config
try:
    from health_analytics.config import config
    HEALTH_DATA_PATH = config.health_data_path
except ImportError:
    HEALTH_DATA_PATH = Path(__file__).parent.parent / "data"


def get_yesterday_file():
    """Get the file path for yesterday's data."""
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    return HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"


def get_today_file():
    """Get the file path for today's data."""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    return HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"


def check_data_freshness():
    """Check if health data is up to date."""
    today_file = get_today_file()
    yesterday_file = get_yesterday_file()
    
    print("🩺 Health Data Freshness Check")
    print(f"   Today's date: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Check today's file
    if today_file.exists():
        status = get_icloud_status(today_file)
        size = today_file.stat().st_size
        print(f"   ✓ Today's data exists ({size:,} bytes, {status})")
    else:
        print(f"   ⚠️  Today's data not yet available")
    
    # Check yesterday's file
    if yesterday_file.exists():
        status = get_icloud_status(yesterday_file)
        size = yesterday_file.stat().st_size
        print(f"   ✓ Yesterday's data exists ({size:,} bytes, {status})")
        return True
    else:
        print(f"   ❌ Yesterday's data missing!")
        return False


def extract_key_metrics(data):
    """Extract key daily metrics from health data."""
    if not data or 'data' not in data:
        return None
    
    metrics = {}
    
    try:
        health_data = data['data'].get('metrics', {})
        
        # Extract common metrics
        if 'step_count' in health_data:
            steps = health_data['step_count']
            if steps:
                total_steps = sum(float(s.get('qty', 0)) for s in steps)
                metrics['steps'] = int(total_steps)
        
        if 'active_energy' in health_data:
            energy = health_data['active_energy']
            if energy:
                total_energy = sum(float(e.get('qty', 0)) for e in energy)
                metrics['active_energy_kcal'] = int(total_energy)
        
        if 'resting_heart_rate' in health_data:
            hr = health_data['resting_heart_rate']
            if hr:
                # Get most recent reading
                metrics['resting_hr'] = int(float(hr[-1].get('qty', 0)))
        
        if 'sleep_analysis' in health_data:
            sleep = health_data['sleep_analysis']
            if sleep:
                # Calculate total sleep duration (simplified)
                metrics['sleep_records'] = len(sleep)
        
    except Exception as e:
        print(f"   ⚠️  Error extracting metrics: {e}")
    
    return metrics


def generate_daily_summary():
    """Generate a summary of yesterday's health data."""
    yesterday_file = get_yesterday_file()
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n📊 Yesterday's Summary ({yesterday_date})")
    
    if not yesterday_file.exists():
        print("   ❌ No data available")
        return
    
    # Read the data
    data = read_json_safe(yesterday_file)
    
    if data is None:
        print("   ⚠️  Could not read file (may be syncing)")
        return
    
    # Extract metrics
    metrics = extract_key_metrics(data)
    
    if metrics:
        if 'steps' in metrics:
            print(f"   🚶 Steps: {metrics['steps']:,}")
        
        if 'active_energy_kcal' in metrics:
            print(f"   🔥 Active Energy: {metrics['active_energy_kcal']} kcal")
        
        if 'resting_hr' in metrics:
            print(f"   ❤️  Resting HR: {metrics['resting_hr']} bpm")
        
        if 'sleep_records' in metrics:
            print(f"   😴 Sleep Records: {metrics['sleep_records']}")
        
        if not metrics:
            print("   ℹ️  No activity data found")
    else:
        print("   ⚠️  Could not extract metrics")


def check_file_count():
    """Check total number of health data files."""
    if not HEALTH_DATA_PATH.exists():
        print("\n❌ Health data path not found!")
        return 0
    
    files = list(HEALTH_DATA_PATH.glob("HealthAutoExport-*.json"))
    
    print(f"\n📁 Total Files: {len(files)}")
    
    if files:
        # Get date range
        dates = []
        for f in files:
            try:
                date_str = f.stem.replace("HealthAutoExport-", "")
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_obj)
            except ValueError:
                continue
        
        if dates:
            dates.sort()
            print(f"   First: {dates[0].strftime('%Y-%m-%d')}")
            print(f"   Latest: {dates[-1].strftime('%Y-%m-%d')}")
            print(f"   Range: {(dates[-1] - dates[0]).days + 1} days")
    
    return len(files)


def main():
    """Main daily check routine."""
    print("=" * 60)
    print("🍎 Apple Health - Daily Check")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check if data path exists
    if not HEALTH_DATA_PATH.exists():
        print("\n❌ Health data path not found!")
        print(f"   Expected: {HEALTH_DATA_PATH}")
        return 1
    
    # Check freshness
    is_fresh = check_data_freshness()
    
    # Check file count
    total_files = check_file_count()
    
    # Generate yesterday's summary
    if is_fresh:
        generate_daily_summary()
    
    print("\n" + "=" * 60)
    print("✅ Daily health check complete")
    
    return 0 if is_fresh and total_files > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
