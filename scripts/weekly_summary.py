#!/usr/bin/env python3
"""
Weekly Health Summary - Analyze trends over the past week.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add src to path for config module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from icloud_helper import read_json_safe
    from detailed_analysis import extract_all_metrics, calculate_totals, get_key_readings
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from icloud_helper import read_json_safe
    from detailed_analysis import extract_all_metrics, calculate_totals, get_key_readings

# Use centralized config
try:
    from health_analytics.config import config
    HEALTH_DATA_PATH = config.health_data_path
except ImportError:
    HEALTH_DATA_PATH = Path(__file__).parent.parent / "data"


def get_week_dates(end_date=None, days=7):
    """Get list of dates for the past week."""
    if end_date is None:
        end_date = datetime.now()
    elif isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    dates = []
    for i in range(days - 1, -1, -1):
        date = end_date - timedelta(days=i)
        dates.append(date)
    
    return dates


def load_week_data(dates):
    """Load health data for a list of dates."""
    week_data = {}
    
    for date in dates:
        date_str = date.strftime("%Y-%m-%d")
        file_path = HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"
        
        if not file_path.exists():
            continue
        
        data = read_json_safe(file_path)
        if data:
            metrics = extract_all_metrics(data)
            if metrics:
                week_data[date_str] = {
                    'totals': calculate_totals(metrics),
                    'readings': get_key_readings(metrics),
                    'date': date
                }
    
    return week_data


def calculate_weekly_stats(week_data):
    """Calculate weekly statistics."""
    if not week_data:
        return None
    
    stats = defaultdict(list)
    
    for date_str, day_data in week_data.items():
        totals = day_data['totals']
        readings = day_data['readings']
        
        # Collect totals
        for key, value in totals.items():
            stats[key].append(value)
        
        # Collect readings
        for key, value in readings.items():
            stats[key].append(value)
    
    # Calculate averages and totals
    summary = {}
    
    for key, values in stats.items():
        if not values:
            continue
        
        summary[key] = {
            'values': values,
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'total': sum(values),
            'count': len(values)
        }
    
    return summary


def print_weekly_summary(dates, week_data, stats):
    """Print formatted weekly summary."""
    print("=" * 80)
    print("📊 WEEKLY HEALTH SUMMARY")
    start = dates[0].strftime("%Y-%m-%d")
    end = dates[-1].strftime("%Y-%m-%d")
    print(f"📅 Week: {start} to {end}")
    print(f"📈 Days analyzed: {len(week_data)}/{len(dates)}")
    print("=" * 80)
    
    # Daily breakdown
    print("\n📆 DAILY BREAKDOWN")
    print("-" * 80)
    print(f"{'Date':<12} {'Steps':>8} {'Distance':>8} {'Energy':>8} {'Exercise':>8} {'Stands':>6}")
    print("-" * 80)
    
    for date in dates:
        date_str = date.strftime("%Y-%m-%d")
        day_name = date.strftime("%a")
        
        if date_str in week_data:
            day = week_data[date_str]
            totals = day['totals']
            
            steps = f"{totals.get('steps', 0):,}" if totals.get('steps') else "-"
            distance = f"{totals.get('distance_km', 0):.1f}km" if totals.get('distance_km') else "-"
            energy = f"{totals.get('active_energy_kcal', 0)}kcal" if totals.get('active_energy_kcal') else "-"
            exercise = f"{totals.get('exercise_minutes', 0)}min" if totals.get('exercise_minutes') else "-"
            stands = f"{totals.get('stand_hours', 0)}/12" if totals.get('stand_hours') else "-"
            
            print(f"{day_name} {date_str} {steps:>8} {distance:>8} {energy:>8} {exercise:>8} {stands:>6}")
        else:
            print(f"{day_name} {date_str}  (no data)")
    
    # Weekly averages
    if stats:
        print("\n📊 WEEKLY AVERAGES")
        print("-" * 80)
        
        if 'steps' in stats:
            avg = int(stats['steps']['avg'])
            total = int(stats['steps']['total'])
            print(f"🚶 Steps:              {avg:,}/day  (total: {total:,})")
        
        if 'distance_km' in stats:
            avg = stats['distance_km']['avg']
            total = stats['distance_km']['total']
            print(f"📏 Distance:           {avg:.1f} km/day  (total: {total:.1f} km)")
        
        if 'active_energy_kcal' in stats:
            avg = int(stats['active_energy_kcal']['avg'])
            total = int(stats['active_energy_kcal']['total'])
            print(f"🔥 Active Energy:      {avg} kcal/day  (total: {total:,} kcal)")
        
        if 'exercise_minutes' in stats:
            avg = int(stats['exercise_minutes']['avg'])
            total = int(stats['exercise_minutes']['total'])
            print(f"💪 Exercise:           {avg} min/day  (total: {total} min)")
        
        if 'stand_hours' in stats:
            avg = stats['stand_hours']['avg']
            print(f"🧍 Stand Hours:        {avg:.1f}/day")
        
        if 'flights' in stats:
            avg = int(stats['flights']['avg'])
            total = int(stats['flights']['total'])
            print(f"🪜 Flights:            {avg}/day  (total: {total})")
        
        print("\n❤️  HEALTH METRICS")
        print("-" * 80)
        
        if 'resting_hr' in stats:
            avg = int(stats['resting_hr']['avg'])
            min_hr = int(stats['resting_hr']['min'])
            max_hr = int(stats['resting_hr']['max'])
            print(f"💤 Resting HR:         {avg} bpm  (range: {min_hr}-{max_hr})")
        
        if 'hrv_avg' in stats:
            avg = int(stats['hrv_avg']['avg'])
            print(f"📊 HRV:                {avg} ms avg")
        
        if 'blood_oxygen' in stats:
            avg = int(stats['blood_oxygen']['avg'])
            print(f"🫁 Blood Oxygen:       {avg}%")
        
        if 'vo2_max' in stats:
            avg = stats['vo2_max']['avg']
            print(f"🏃 VO2 Max:            {avg:.1f} ml/(kg·min)")
        
        # Goal achievements
        print("\n🎯 GOAL ACHIEVEMENTS")
        print("-" * 80)
        
        if 'steps' in stats:
            days_10k = sum(1 for v in stats['steps']['values'] if v >= 10000)
            print(f"✓ 10,000 steps:        {days_10k}/{stats['steps']['count']} days")
        
        if 'stand_hours' in stats:
            days_12h = sum(1 for v in stats['stand_hours']['values'] if v >= 12)
            print(f"✓ 12 stand hours:      {days_12h}/{stats['stand_hours']['count']} days")
        
        if 'exercise_minutes' in stats:
            days_30m = sum(1 for v in stats['exercise_minutes']['values'] if v >= 30)
            print(f"✓ 30min exercise:      {days_30m}/{stats['exercise_minutes']['count']} days")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    # Get week to analyze (default: past 7 days ending yesterday)
    if len(sys.argv) > 1:
        end_date = sys.argv[1]
    else:
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    dates = get_week_dates(end_date, days)
    week_data = load_week_data(dates)
    stats = calculate_weekly_stats(week_data)
    
    print_weekly_summary(dates, week_data, stats)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
