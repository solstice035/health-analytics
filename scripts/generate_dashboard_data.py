#!/usr/bin/env python3
"""
Generate Dashboard Data - Create JSON data files for the health dashboard.

This script processes Apple Health export data and generates various JSON files
for the interactive health analytics dashboard, including:
- Daily activity trends (30 days)
- Weekly comparisons (12 weeks)
- Goal progress tracking (7 days)
- Summary statistics
- Heart rate zone distribution
- Health score calculation
- Personal records and achievements
- AI-generated insights
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple

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
    """Generate heart rate zone distribution based on actual HR readings."""
    sorted_dates = sorted(data.keys())[-days:]

    # Heart rate zones (standard zones)
    zones = {
        'resting': 0,      # < 60 bpm
        'light': 0,        # 60-100 bpm
        'moderate': 0,     # 100-140 bpm
        'vigorous': 0,     # 140-170 bpm
        'peak': 0          # > 170 bpm
    }

    total_readings = 0

    for date in sorted_dates:
        day_data = data[date]
        hr_stats = day_data.get('hr_stats')

        if hr_stats:
            # Use min/max/avg to estimate zone distribution
            min_hr = hr_stats.get('min', 0)
            max_hr = hr_stats.get('max', 0)
            avg_hr = hr_stats.get('avg', 0)
            count = hr_stats.get('count', 0)

            if count > 0:
                # Estimate time in zones based on the range
                # This is a heuristic - real zone data would need individual readings
                if min_hr > 0 and max_hr > 0:
                    # Resting (usually morning readings)
                    if min_hr < 60:
                        zones['resting'] += 1

                    # Light activity (most of the day)
                    if avg_hr >= 60 and avg_hr < 100:
                        zones['light'] += 2
                    elif avg_hr < 60:
                        zones['light'] += 1

                    # Moderate (exercise)
                    if max_hr >= 100 and max_hr < 140:
                        zones['moderate'] += 1
                    elif max_hr >= 140:
                        zones['moderate'] += 1

                    # Vigorous (intense exercise)
                    if max_hr >= 140 and max_hr < 170:
                        zones['vigorous'] += 1
                    elif max_hr >= 170:
                        zones['vigorous'] += 1

                    # Peak (max effort)
                    if max_hr >= 170:
                        zones['peak'] += 1

                    total_readings += 1

    # If we have no data, return zeros
    if total_readings == 0:
        return {
            'labels': list(zones.keys()),
            'values': [0, 0, 0, 0, 0]
        }

    return {
        'labels': list(zones.keys()),
        'values': list(zones.values())
    }


def calculate_health_score(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a comprehensive health score based on activity metrics.

    Scoring weights:
    - Steps: 25 points (goal: 10,000)
    - Exercise: 25 points (goal: 30 min)
    - Stand: 20 points (goal: 12 hours)
    - Resting HR: 15 points (optimal: <=60)
    - HRV: 15 points (optimal: >=50)
    """
    weights = {
        'steps': 25,
        'exercise': 25,
        'stand': 20,
        'resting_hr': 15,
        'hrv': 15
    }

    score = 0
    breakdown = {}
    avgs = stats.get('averages', {})

    # Steps score
    steps = avgs.get('steps', 0)
    if steps > 0:
        steps_ratio = min(steps / 10000, 1.2)
        steps_score = steps_ratio * weights['steps']
        score += steps_score
        breakdown['steps'] = round(steps_score, 1)

    # Exercise score
    exercise = avgs.get('exercise_minutes', 0)
    if exercise > 0:
        exercise_ratio = min(exercise / 30, 1.5)
        exercise_score = exercise_ratio * weights['exercise']
        score += exercise_score
        breakdown['exercise'] = round(exercise_score, 1)

    # Stand hours score
    stand = avgs.get('stand_hours', 0)
    if stand > 0:
        stand_ratio = min(stand / 12, 1.2)
        stand_score = stand_ratio * weights['stand']
        score += stand_score
        breakdown['stand'] = round(stand_score, 1)

    # Resting HR score (lower is better)
    rhr = avgs.get('resting_hr', 0)
    if rhr > 0:
        if rhr <= 60:
            hr_score = weights['resting_hr']
        elif rhr <= 70:
            hr_score = weights['resting_hr'] * 0.8
        elif rhr <= 80:
            hr_score = weights['resting_hr'] * 0.6
        else:
            hr_score = weights['resting_hr'] * 0.4
        score += hr_score
        breakdown['resting_hr'] = round(hr_score, 1)

    # HRV score (higher is better)
    hrv = avgs.get('hrv', 0)
    if hrv > 0:
        if hrv >= 50:
            hrv_score = weights['hrv']
        elif hrv >= 40:
            hrv_score = weights['hrv'] * 0.9
        elif hrv >= 30:
            hrv_score = weights['hrv'] * 0.7
        else:
            hrv_score = weights['hrv'] * 0.5
        score += hrv_score
        breakdown['hrv'] = round(hrv_score, 1)

    final_score = min(round(score), 100)

    # Generate description
    if final_score >= 85:
        description = "Excellent! You're crushing your health goals."
        level = "excellent"
    elif final_score >= 70:
        description = "Great work! You're on track for good health."
        level = "good"
    elif final_score >= 55:
        description = "Good progress. A bit more activity will help."
        level = "moderate"
    else:
        description = "Room for improvement. Try to be more active."
        level = "needs_work"

    return {
        'score': final_score,
        'description': description,
        'level': level,
        'breakdown': breakdown,
        'max_score': 100
    }


def generate_insights(data: Dict[str, Any], stats: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate AI-like insights based on health data patterns."""
    insights = []
    sorted_dates = sorted(data.keys())

    if len(sorted_dates) < 7:
        return [{'type': 'neutral', 'icon': '📊', 'title': 'Collecting Data',
                 'text': 'Keep logging your health data for personalized insights.'}]

    # Steps trend analysis
    recent_dates = sorted_dates[-7:]
    prior_dates = sorted_dates[-14:-7] if len(sorted_dates) >= 14 else []

    recent_steps = [data[d]['totals'].get('steps', 0) for d in recent_dates]
    recent_avg = sum(recent_steps) / len(recent_steps) if recent_steps else 0

    if prior_dates:
        prior_steps = [data[d]['totals'].get('steps', 0) for d in prior_dates]
        prior_avg = sum(prior_steps) / len(prior_steps) if prior_steps else 0

        if prior_avg > 0:
            change = ((recent_avg - prior_avg) / prior_avg) * 100

            if change > 10:
                insights.append({
                    'type': 'positive',
                    'icon': '📈',
                    'title': 'Steps Trending Up',
                    'text': f'Your step count is up {int(change)}% compared to last week. Keep up the momentum!'
                })
            elif change < -10:
                insights.append({
                    'type': 'warning',
                    'icon': '📉',
                    'title': 'Activity Dip Detected',
                    'text': f'Your steps are down {int(abs(change))}% from last week. Try adding a short walk today.'
                })

    # Goal achievements
    if stats.get('goals'):
        steps_achieved = stats['goals'].get('steps_10k', {}).get('achieved', 0)
        exercise_achieved = stats['goals'].get('exercise_30m', {}).get('achieved', 0)
        total_days = stats['goals'].get('steps_10k', {}).get('total', 7)

        if steps_achieved >= total_days:
            insights.append({
                'type': 'positive',
                'icon': '🏆',
                'title': 'Perfect Step Week!',
                'text': 'You hit 10,000 steps every day this week! Amazing consistency.'
            })

        if exercise_achieved == total_days:
            insights.append({
                'type': 'positive',
                'icon': '💪',
                'title': 'Exercise Champion',
                'text': 'Full week of 30+ minute workouts. Your body thanks you!'
            })

    # HRV insight
    recent_hrv = [data[d]['readings'].get('hrv_avg', 0) for d in recent_dates[-3:]]
    recent_hrv = [h for h in recent_hrv if h > 0]
    if recent_hrv:
        avg_hrv = sum(recent_hrv) / len(recent_hrv)

        if avg_hrv >= 50:
            insights.append({
                'type': 'positive',
                'icon': '💚',
                'title': 'Great Recovery',
                'text': f'Your HRV of {int(avg_hrv)}ms indicates excellent recovery and low stress.'
            })
        elif avg_hrv < 30:
            insights.append({
                'type': 'warning',
                'icon': '😴',
                'title': 'Consider Rest',
                'text': 'Your HRV suggests your body might need more recovery time.'
            })

    # Resting HR insight
    if stats.get('averages', {}).get('resting_hr', 0) < 60:
        insights.append({
            'type': 'positive',
            'icon': '❤️',
            'title': 'Athletic Heart Rate',
            'text': f"Resting HR of {stats['averages']['resting_hr']} bpm is in the athletic range!"
        })

    # Personal record check
    max_steps_day = max(recent_dates, key=lambda d: data[d]['totals'].get('steps', 0))
    max_steps = data[max_steps_day]['totals'].get('steps', 0)

    if max_steps >= 15000:
        insights.append({
            'type': 'positive',
            'icon': '⭐',
            'title': 'Outstanding Activity Day',
            'text': f'You walked {max_steps:,} steps on {max_steps_day}!'
        })

    # Default insight if none generated
    if not insights:
        insights.append({
            'type': 'neutral',
            'icon': '📊',
            'title': 'Keep Tracking',
            'text': 'Continue logging your health data for personalized insights.'
        })

    return insights[:4]  # Max 4 insights


def generate_personal_records(data: Dict[str, Any]) -> Dict[str, Any]:
    """Track personal records and achievements."""
    records = {
        'max_steps': {'value': 0, 'date': None},
        'max_distance': {'value': 0, 'date': None},
        'max_exercise': {'value': 0, 'date': None},
        'lowest_resting_hr': {'value': 999, 'date': None},
        'highest_hrv': {'value': 0, 'date': None}
    }

    for date, day_data in data.items():
        totals = day_data.get('totals', {})
        readings = day_data.get('readings', {})

        # Max steps
        steps = totals.get('steps', 0)
        if steps > records['max_steps']['value']:
            records['max_steps'] = {'value': steps, 'date': date}

        # Max distance
        distance = totals.get('distance_km', 0)
        if distance > records['max_distance']['value']:
            records['max_distance'] = {'value': distance, 'date': date}

        # Max exercise
        exercise = totals.get('exercise_minutes', 0)
        if exercise > records['max_exercise']['value']:
            records['max_exercise'] = {'value': exercise, 'date': date}

        # Lowest resting HR
        rhr = readings.get('resting_hr', 0)
        if 0 < rhr < records['lowest_resting_hr']['value']:
            records['lowest_resting_hr'] = {'value': rhr, 'date': date}

        # Highest HRV
        hrv = readings.get('hrv_avg', 0)
        if hrv > records['highest_hrv']['value']:
            records['highest_hrv'] = {'value': hrv, 'date': date}

    # Clean up any unset records
    if records['lowest_resting_hr']['value'] == 999:
        records['lowest_resting_hr'] = {'value': 0, 'date': None}

    return records


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

    # 6. Health score
    health_score = calculate_health_score(summary_stats)
    with open(OUTPUT_PATH / "health_score.json", "w") as f:
        json.dump(health_score, f, indent=2)
    print(f"  ✓ health_score.json (Score: {health_score['score']}/100)")

    # 7. AI Insights
    insights = generate_insights(all_data, summary_stats)
    with open(OUTPUT_PATH / "insights.json", "w") as f:
        json.dump({'insights': insights}, f, indent=2)
    print(f"  ✓ insights.json ({len(insights)} insights)")

    # 8. Personal records
    records = generate_personal_records(all_data)
    with open(OUTPUT_PATH / "personal_records.json", "w") as f:
        json.dump(records, f, indent=2)
    print("  ✓ personal_records.json")

    # 9. Metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'data_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'days_loaded': len(all_data)
        },
        'last_update': sorted(all_data.keys())[-1] if all_data else None,
        'version': '2.0.0',
        'features': [
            'daily_trends',
            'weekly_comparison',
            'goals_progress',
            'summary_stats',
            'hr_distribution',
            'health_score',
            'insights',
            'personal_records'
        ]
    }
    with open(OUTPUT_PATH / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print("  ✓ metadata.json")

    print("\n" + "=" * 60)
    print("📈 HEALTH SCORE SUMMARY")
    print("=" * 60)
    print(f"  Score: {health_score['score']}/100 ({health_score['level']})")
    print(f"  {health_score['description']}")

    if health_score.get('breakdown'):
        print("\n  Breakdown:")
        for key, value in health_score['breakdown'].items():
            print(f"    {key.replace('_', ' ').title()}: {value} pts")

    print("\n" + "=" * 60)
    print("✅ Dashboard data generated successfully!")
    print(f"📁 Output directory: {OUTPUT_PATH}")
    print(f"\n💡 Run: python serve.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
