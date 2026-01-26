#!/usr/bin/env python3
"""
Detailed Health Analysis - Extract and analyze key daily metrics.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from icloud_helper import read_json_safe, get_icloud_status
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from icloud_helper import read_json_safe, get_icloud_status

HEALTH_DATA_PATH = Path(__file__).parent.parent / "data"


def extract_all_metrics(data):
    """Extract all metrics from health data into a structured dict."""
    if not data or 'data' not in data or 'metrics' not in data['data']:
        return None
    
    metrics_list = data['data']['metrics']
    result = {}
    
    for metric in metrics_list:
        name = metric.get('name', 'unknown')
        units = metric.get('units', '')
        data_points = metric.get('data', [])
        
        result[name] = {
            'units': units,
            'count': len(data_points),
            'data': data_points
        }
    
    return result


def calculate_totals(metrics):
    """Calculate daily totals for key metrics."""
    totals = {}
    
    # Step count
    if 'step_count' in metrics:
        steps = sum(float(d.get('qty', 0)) for d in metrics['step_count']['data'])
        totals['steps'] = int(steps)
    
    # Active energy
    if 'active_energy' in metrics:
        energy = sum(float(d.get('qty', 0)) for d in metrics['active_energy']['data'])
        totals['active_energy_kcal'] = int(energy)
    
    # Exercise time
    if 'apple_exercise_time' in metrics:
        exercise = sum(float(d.get('qty', 0)) for d in metrics['apple_exercise_time']['data'])
        totals['exercise_minutes'] = int(exercise)
    
    # Stand hours
    if 'apple_stand_hour' in metrics:
        stand = sum(float(d.get('qty', 0)) for d in metrics['apple_stand_hour']['data'])
        totals['stand_hours'] = int(stand)
    
    # Walking/running distance
    if 'walking_running_distance' in metrics:
        distance = sum(float(d.get('qty', 0)) for d in metrics['walking_running_distance']['data'])
        totals['distance_km'] = round(distance, 2)
    
    # Flights climbed
    if 'flights_climbed' in metrics:
        flights = sum(float(d.get('qty', 0)) for d in metrics['flights_climbed']['data'])
        totals['flights'] = int(flights)
    
    # Time in daylight
    if 'time_in_daylight' in metrics:
        daylight = sum(float(d.get('qty', 0)) for d in metrics['time_in_daylight']['data'])
        totals['daylight_minutes'] = int(daylight)
    
    return totals


def get_key_readings(metrics):
    """Get important single readings (resting HR, VO2 max, etc.)."""
    readings = {}
    
    # Resting heart rate (latest)
    if 'resting_heart_rate' in metrics and metrics['resting_heart_rate']['data']:
        hr_data = metrics['resting_heart_rate']['data']
        readings['resting_hr'] = int(float(hr_data[-1].get('qty', 0)))
    
    # VO2 Max (latest)
    if 'vo2_max' in metrics and metrics['vo2_max']['data']:
        vo2_data = metrics['vo2_max']['data']
        readings['vo2_max'] = round(float(vo2_data[-1].get('qty', 0)), 1)
    
    # Heart Rate Variability (average)
    if 'heart_rate_variability' in metrics and metrics['heart_rate_variability']['data']:
        hrv_data = metrics['heart_rate_variability']['data']
        hrv_values = [float(d.get('qty', 0)) for d in hrv_data]
        readings['hrv_avg'] = int(sum(hrv_values) / len(hrv_values))
    
    # Walking heart rate average
    if 'walking_heart_rate_average' in metrics and metrics['walking_heart_rate_average']['data']:
        whr_data = metrics['walking_heart_rate_average']['data']
        readings['walking_hr'] = int(float(whr_data[-1].get('qty', 0)))
    
    # Blood oxygen (average)
    if 'blood_oxygen_saturation' in metrics and metrics['blood_oxygen_saturation']['data']:
        o2_data = metrics['blood_oxygen_saturation']['data']
        o2_values = [float(d.get('qty', 0)) for d in o2_data]
        readings['blood_oxygen'] = int(sum(o2_values) / len(o2_values))
    
    return readings


def get_heart_rate_stats(metrics):
    """Calculate heart rate statistics."""
    if 'heart_rate' not in metrics or not metrics['heart_rate']['data']:
        return None
    
    hr_data = metrics['heart_rate']['data']
    hr_values = [float(d.get('qty', 0)) for d in hr_data if 'qty' in d]
    
    if not hr_values:
        return None
    
    return {
        'count': len(hr_values),
        'min': int(min(hr_values)),
        'max': int(max(hr_values)),
        'avg': int(sum(hr_values) / len(hr_values))
    }


def analyze_date(date_str):
    """Perform detailed analysis of a specific date."""
    file_path = HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path.name}")
        return None
    
    print("=" * 70)
    print(f"🍎 Apple Health - Detailed Analysis")
    print(f"📅 Date: {date_str}")
    print("=" * 70)
    
    # Check iCloud status
    status = get_icloud_status(file_path)
    print(f"📁 File status: {status}")
    
    # Read data
    data = read_json_safe(file_path)
    
    if data is None:
        print("❌ Could not read file (may still be syncing)")
        return None
    
    # Extract metrics
    metrics = extract_all_metrics(data)
    
    if not metrics:
        print("❌ No metrics found in file")
        return None
    
    print(f"✓ Loaded {len(metrics)} metric types\n")
    
    # Daily totals
    print("📊 DAILY TOTALS")
    print("-" * 70)
    totals = calculate_totals(metrics)
    
    if totals.get('steps'):
        print(f"🚶 Steps:              {totals['steps']:,}")
    if totals.get('distance_km'):
        print(f"📏 Distance:           {totals['distance_km']} km")
    if totals.get('active_energy_kcal'):
        print(f"🔥 Active Energy:      {totals['active_energy_kcal']} kcal")
    if totals.get('exercise_minutes'):
        print(f"💪 Exercise Time:      {totals['exercise_minutes']} minutes")
    if totals.get('stand_hours'):
        print(f"🧍 Stand Hours:        {totals['stand_hours']}/12")
    if totals.get('flights'):
        print(f"🪜 Flights Climbed:    {totals['flights']}")
    if totals.get('daylight_minutes'):
        print(f"☀️  Time in Daylight:  {totals['daylight_minutes']} minutes")
    
    # Key readings
    print("\n❤️  KEY HEALTH READINGS")
    print("-" * 70)
    readings = get_key_readings(metrics)
    
    if readings.get('resting_hr'):
        print(f"💤 Resting Heart Rate: {readings['resting_hr']} bpm")
    if readings.get('hrv_avg'):
        print(f"📊 HRV (avg):          {readings['hrv_avg']} ms")
    if readings.get('walking_hr'):
        print(f"🚶 Walking HR (avg):   {readings['walking_hr']} bpm")
    if readings.get('blood_oxygen'):
        print(f"🫁 Blood Oxygen:       {readings['blood_oxygen']}%")
    if readings.get('vo2_max'):
        print(f"🏃 VO2 Max:            {readings['vo2_max']} ml/(kg·min)")
    
    # Heart rate stats
    hr_stats = get_heart_rate_stats(metrics)
    if hr_stats:
        print(f"\n💓 HEART RATE THROUGHOUT DAY")
        print("-" * 70)
        print(f"Readings:   {hr_stats['count']}")
        print(f"Min:        {hr_stats['min']} bpm")
        print(f"Max:        {hr_stats['max']} bpm")
        print(f"Average:    {hr_stats['avg']} bpm")
    
    # Available metrics
    print(f"\n📈 AVAILABLE METRICS ({len(metrics)} total)")
    print("-" * 70)
    
    # Sort by data point count
    sorted_metrics = sorted(metrics.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for name, info in sorted_metrics[:15]:
        display_name = name.replace('_', ' ').title()
        print(f"{display_name:40} {info['count']:5} points  ({info['units']})")
    
    if len(metrics) > 15:
        print(f"... and {len(metrics) - 15} more metrics")
    
    print("\n" + "=" * 70)
    
    return {
        'totals': totals,
        'readings': readings,
        'hr_stats': hr_stats,
        'metrics': metrics
    }


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        # Default to yesterday
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
    
    result = analyze_date(date_str)
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
