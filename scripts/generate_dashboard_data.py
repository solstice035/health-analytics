#!/usr/bin/env python3
"""
Generate Dashboard Data - Create JSON data files for the health dashboard.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from icloud_helper import read_json_safe
    from detailed_analysis import extract_all_metrics, calculate_totals, get_key_readings, get_heart_rate_stats
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from icloud_helper import read_json_safe
    from detailed_analysis import extract_all_metrics, calculate_totals, get_key_readings, get_heart_rate_stats

HEALTH_DATA_PATH = Path(__file__).parent.parent / "data"
OUTPUT_PATH = Path(__file__).parent.parent / "dashboard" / "data"


def load_date_range(start_date, end_date):
    """Load health data for a date range."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    data = {}
    current = start_date
    
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        file_path = HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"
        
        if file_path.exists():
            raw_data = read_json_safe(file_path)
            if raw_data:
                metrics = extract_all_metrics(raw_data)
                if metrics:
                    data[date_str] = {
                        'date': date_str,
                        'totals': calculate_totals(metrics),
                        'readings': get_key_readings(metrics),
                        'hr_stats': get_heart_rate_stats(metrics)
                    }
        
        current += timedelta(days=1)
    
    return data


def generate_daily_trends(data, days=30):
    """Generate daily trend data for the past N days."""
    # Sort by date
    sorted_dates = sorted(data.keys())[-days:]
    
    trends = {
        'dates': [],
        'steps': [],
        'distance': [],
        'active_energy': [],
        'exercise_minutes': [],
        'stand_hours': [],
        'resting_hr': [],
        'hrv': []
    }
    
    for date in sorted_dates:
        day_data = data[date]
        totals = day_data['totals']
        readings = day_data['readings']
        
        trends['dates'].append(date)
        trends['steps'].append(totals.get('steps', 0))
        trends['distance'].append(totals.get('distance_km', 0))
        trends['active_energy'].append(totals.get('active_energy_kcal', 0))
        trends['exercise_minutes'].append(totals.get('exercise_minutes', 0))
        trends['stand_hours'].append(totals.get('stand_hours', 0))
        trends['resting_hr'].append(readings.get('resting_hr', 0))
        trends['hrv'].append(readings.get('hrv_avg', 0))
    
    return trends


def generate_weekly_comparison(data):
    """Generate weekly comparison data."""
    sorted_dates = sorted(data.keys())
    
    # Group by week
    weeks = defaultdict(lambda: {
        'dates': [],
        'steps': [],
        'distance': [],
        'active_energy': [],
        'exercise': []
    })
    
    for date_str in sorted_dates:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        week_num = date_obj.isocalendar()[1]
        year = date_obj.year
        week_key = f"{year}-W{week_num:02d}"
        
        day_data = data[date_str]
        totals = day_data['totals']
        
        weeks[week_key]['dates'].append(date_str)
        weeks[week_key]['steps'].append(totals.get('steps', 0))
        weeks[week_key]['distance'].append(totals.get('distance_km', 0))
        weeks[week_key]['active_energy'].append(totals.get('active_energy_kcal', 0))
        weeks[week_key]['exercise'].append(totals.get('exercise_minutes', 0))
    
    # Calculate weekly averages
    weekly_data = {
        'weeks': [],
        'avg_steps': [],
        'avg_distance': [],
        'avg_energy': [],
        'avg_exercise': []
    }
    
    for week in sorted(weeks.keys())[-12:]:  # Last 12 weeks
        week_info = weeks[week]
        
        weekly_data['weeks'].append(week)
        weekly_data['avg_steps'].append(int(sum(week_info['steps']) / len(week_info['steps'])) if week_info['steps'] else 0)
        weekly_data['avg_distance'].append(round(sum(week_info['distance']) / len(week_info['distance']), 1) if week_info['distance'] else 0)
        weekly_data['avg_energy'].append(int(sum(week_info['active_energy']) / len(week_info['active_energy'])) if week_info['active_energy'] else 0)
        weekly_data['avg_exercise'].append(int(sum(week_info['exercise']) / len(week_info['exercise'])) if week_info['exercise'] else 0)
    
    return weekly_data


def generate_goals_progress(data, days=7):
    """Generate goal achievement data."""
    sorted_dates = sorted(data.keys())[-days:]
    
    goals = {
        'dates': [],
        'steps_goal': [],      # 10,000 steps
        'stand_goal': [],      # 12 hours
        'exercise_goal': []    # 30 minutes
    }
    
    for date in sorted_dates:
        day_data = data[date]
        totals = day_data['totals']
        
        goals['dates'].append(date)
        goals['steps_goal'].append(1 if totals.get('steps', 0) >= 10000 else 0)
        goals['stand_goal'].append(1 if totals.get('stand_hours', 0) >= 12 else 0)
        goals['exercise_goal'].append(1 if totals.get('exercise_minutes', 0) >= 30 else 0)
    
    return goals


def generate_summary_stats(data, days=7):
    """Generate summary statistics for the dashboard."""
    sorted_dates = sorted(data.keys())[-days:]
    
    stats = {
        'period': f"{sorted_dates[0]} to {sorted_dates[-1]}",
        'days_count': len(sorted_dates),
        'totals': {},
        'averages': {},
        'goals': {}
    }
    
    # Collect all values
    steps = []
    distance = []
    energy = []
    exercise = []
    stands = []
    resting_hr = []
    hrv = []
    
    for date in sorted_dates:
        day_data = data[date]
        totals = day_data['totals']
        readings = day_data['readings']
        
        steps.append(totals.get('steps', 0))
        distance.append(totals.get('distance_km', 0))
        energy.append(totals.get('active_energy_kcal', 0))
        exercise.append(totals.get('exercise_minutes', 0))
        stands.append(totals.get('stand_hours', 0))
        if readings.get('resting_hr'):
            resting_hr.append(readings['resting_hr'])
        if readings.get('hrv_avg'):
            hrv.append(readings['hrv_avg'])
    
    # Calculate totals
    stats['totals']['steps'] = sum(steps)
    stats['totals']['distance_km'] = round(sum(distance), 1)
    stats['totals']['active_energy_kcal'] = sum(energy)
    stats['totals']['exercise_minutes'] = sum(exercise)
    
    # Calculate averages
    stats['averages']['steps'] = int(sum(steps) / len(steps)) if steps else 0
    stats['averages']['distance_km'] = round(sum(distance) / len(distance), 1) if distance else 0
    stats['averages']['active_energy_kcal'] = int(sum(energy) / len(energy)) if energy else 0
    stats['averages']['exercise_minutes'] = int(sum(exercise) / len(exercise)) if exercise else 0
    stats['averages']['stand_hours'] = round(sum(stands) / len(stands), 1) if stands else 0
    stats['averages']['resting_hr'] = int(sum(resting_hr) / len(resting_hr)) if resting_hr else 0
    stats['averages']['hrv'] = int(sum(hrv) / len(hrv)) if hrv else 0
    
    # Goal achievements
    stats['goals']['steps_10k'] = {
        'achieved': sum(1 for s in steps if s >= 10000),
        'total': len(steps)
    }
    stats['goals']['stand_12h'] = {
        'achieved': sum(1 for s in stands if s >= 12),
        'total': len(stands)
    }
    stats['goals']['exercise_30m'] = {
        'achieved': sum(1 for e in exercise if e >= 30),
        'total': len(exercise)
    }
    
    return stats


def generate_heart_rate_distribution(data, days=7):
    """Generate heart rate zone distribution."""
    sorted_dates = sorted(data.keys())[-days:]
    
    # Heart rate zones (rough approximation, adjust based on age)
    zones = {
        'resting': 0,      # < 60
        'light': 0,        # 60-100
        'moderate': 0,     # 100-140
        'vigorous': 0,     # 140-170
        'peak': 0          # > 170
    }
    
    for date in sorted_dates:
        day_data = data[date]
        hr_stats = day_data.get('hr_stats')
        
        if hr_stats:
            # This is simplified - ideally we'd analyze all HR readings
            # For now, distribute based on min/max/avg
            avg = hr_stats.get('avg', 0)
            
            if avg < 60:
                zones['resting'] += 1
            elif avg < 100:
                zones['light'] += 1
            elif avg < 140:
                zones['moderate'] += 1
            elif avg < 170:
                zones['vigorous'] += 1
            else:
                zones['peak'] += 1
    
    return {
        'labels': list(zones.keys()),
        'values': list(zones.values())
    }


def main():
    """Generate all dashboard data files."""
    print("🏗️  Generating Health Dashboard Data...")
    print("=" * 60)
    
    # Ensure output directory exists
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    
    # Determine date range (last 30 days for faster initial load)
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Loading data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    # Load all data
    all_data = load_date_range(start_date, end_date)
    print(f"✓ Loaded {len(all_data)} days of data")
    
    # Generate various data files
    print("\n📊 Generating visualizations...")
    
    # 1. Daily trends (30 days)
    daily_trends = generate_daily_trends(all_data, days=30)
    with open(OUTPUT_PATH / "daily_trends.json", "w") as f:
        json.dump(daily_trends, f, indent=2)
    print("  ✓ daily_trends.json (30-day activity)")
    
    # 2. Weekly comparison (12 weeks)
    weekly_comparison = generate_weekly_comparison(all_data)
    with open(OUTPUT_PATH / "weekly_comparison.json", "w") as f:
        json.dump(weekly_comparison, f, indent=2)
    print("  ✓ weekly_comparison.json (12-week trends)")
    
    # 3. Goals progress (7 days)
    goals_progress = generate_goals_progress(all_data, days=7)
    with open(OUTPUT_PATH / "goals_progress.json", "w") as f:
        json.dump(goals_progress, f, indent=2)
    print("  ✓ goals_progress.json (7-day goals)")
    
    # 4. Summary stats (7 days)
    summary_stats = generate_summary_stats(all_data, days=7)
    with open(OUTPUT_PATH / "summary_stats.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("  ✓ summary_stats.json (weekly summary)")
    
    # 5. Heart rate distribution (7 days)
    hr_distribution = generate_heart_rate_distribution(all_data, days=7)
    with open(OUTPUT_PATH / "hr_distribution.json", "w") as f:
        json.dump(hr_distribution, f, indent=2)
    print("  ✓ hr_distribution.json (HR zones)")
    
    # 6. Metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'data_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'days_loaded': len(all_data)
        },
        'last_update': sorted(all_data.keys())[-1] if all_data else None
    }
    with open(OUTPUT_PATH / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print("  ✓ metadata.json")
    
    print("\n✅ Dashboard data generated successfully!")
    print(f"📁 Output directory: {OUTPUT_PATH}")
    print("\n💡 Next: Open dashboard/index.html in a browser")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
