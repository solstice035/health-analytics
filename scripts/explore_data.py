#!/usr/bin/env python3
"""
Apple Health Data Explorer
Analyzes the structure and contents of Health Auto Export JSON files.
"""

import json
import os
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import sys

# Path to the iCloud health data
HEALTH_DATA_PATH = Path.home() / "Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/JSON"

def find_health_files():
    """Find all JSON health export files."""
    if not HEALTH_DATA_PATH.exists():
        print(f"❌ Health data path not found: {HEALTH_DATA_PATH}")
        return []
    
    files = sorted(HEALTH_DATA_PATH.glob("HealthAutoExport-*.json"))
    print(f"📊 Found {len(files)} health data files")
    return files

def explore_file_structure(file_path, max_attempts=3):
    """Explore the structure of a single health data file."""
    print(f"\n📁 Analyzing: {file_path.name}")
    
    # Try to read the file (may fail if syncing)
    for attempt in range(max_attempts):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            break
        except (OSError, json.JSONDecodeError) as e:
            if attempt < max_attempts - 1:
                print(f"⚠️  Attempt {attempt + 1} failed (file may be syncing), retrying...")
                import time
                time.sleep(1)
            else:
                print(f"❌ Could not read file after {max_attempts} attempts: {e}")
                return None
    
    # Analyze top-level structure
    print(f"\n🔑 Top-level keys:")
    for key in data.keys():
        value = data[key]
        value_type = type(value).__name__
        
        if isinstance(value, dict):
            print(f"  • {key}: {value_type} with {len(value)} keys")
        elif isinstance(value, list):
            print(f"  • {key}: {value_type} with {len(value)} items")
        else:
            print(f"  • {key}: {value_type} = {value}")
    
    # Analyze data metrics
    if 'data' in data and isinstance(data['data'], dict):
        print(f"\n📈 Health Metrics Found:")
        metric_counts = defaultdict(int)
        
        for category, metrics in data['data'].items():
            if isinstance(metrics, dict):
                for metric, values in metrics.items():
                    if isinstance(values, list):
                        metric_counts[metric] = len(values)
        
        # Show top metrics by data point count
        sorted_metrics = sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)
        for metric, count in sorted_metrics[:15]:
            print(f"  • {metric}: {count} data points")
    
    return data

def generate_date_coverage_report(files):
    """Generate a report of date coverage."""
    print(f"\n📅 Date Coverage:")
    
    if not files:
        print("  No files to analyze")
        return
    
    dates = []
    for f in files:
        # Extract date from filename: HealthAutoExport-YYYY-MM-DD.json
        try:
            date_str = f.stem.replace("HealthAutoExport-", "")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(date_obj)
        except ValueError:
            continue
    
    if dates:
        dates.sort()
        print(f"  • First export: {dates[0].strftime('%Y-%m-%d')}")
        print(f"  • Latest export: {dates[-1].strftime('%Y-%m-%d')}")
        print(f"  • Total days: {len(dates)}")
        print(f"  • Date range: {(dates[-1] - dates[0]).days + 1} days")
        
        # Check for gaps
        expected_days = (dates[-1] - dates[0]).days + 1
        if len(dates) < expected_days:
            print(f"  ⚠️  Missing {expected_days - len(dates)} days")

def main():
    """Main exploration routine."""
    print("🍎 Apple Health Data Explorer")
    print("=" * 50)
    
    # Find all files
    files = find_health_files()
    
    if not files:
        print("\n❌ No health data files found. Check:")
        print(f"   1. Health Auto Export app is installed and running")
        print(f"   2. iCloud Drive is syncing")
        print(f"   3. Path is correct: {HEALTH_DATA_PATH}")
        return 1
    
    # Generate date coverage report
    generate_date_coverage_report(files)
    
    # Explore the most recent file
    if files:
        latest_file = files[-1]
        data = explore_file_structure(latest_file)
        
        if data:
            print("\n✅ Successfully analyzed health data structure")
            print(f"💡 Next steps:")
            print(f"   • Run daily_summary.py to generate activity report")
            print(f"   • Use Jupyter notebook for interactive exploration")
            print(f"   • Create visualizations with generate_charts.py")
        else:
            print("\n⚠️  Could not analyze file (may still be syncing)")
            print("   Try again in a few moments")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
