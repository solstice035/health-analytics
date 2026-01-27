#!/usr/bin/env python3
"""
Deep Health Analytics - Comprehensive analysis of historical health data.

This module provides advanced analysis including:
- Fitness trajectory over time
- Correlation analysis between metrics
- Weekly/monthly patterns
- Trend detection and anomaly identification
- Actionable health insights
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics
import sys
from typing import Dict, List, Any, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from health_analytics.config import config


def load_all_health_data(data_dir: Optional[Path] = None) -> Dict[str, Dict[str, List[float]]]:
    """
    Load and aggregate all health data from JSON files.

    Args:
        data_dir: Path to data directory (uses config default if not provided)

    Returns:
        Dict mapping date strings to metric name -> list of values
    """
    if data_dir is None:
        data_dir = config.health_data_path

    daily = defaultdict(lambda: defaultdict(list))

    for json_file in sorted(data_dir.glob('HealthAutoExport-*.json')):
        try:
            with open(json_file) as f:
                data = json.load(f)

            date_str = json_file.stem.replace('HealthAutoExport-', '')

            for metric in data.get('data', {}).get('metrics', []):
                name = metric['name']
                points = metric.get('data', [])

                for p in points:
                    if name == 'heart_rate':
                        val = p.get('Avg', p.get('qty', 0))
                    else:
                        val = p.get('qty', 0)
                    if val:
                        daily[date_str][name].append(val)
        except Exception:
            pass

    return dict(daily)


def calculate_daily_stats(daily_data: Dict[str, Dict[str, List[float]]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate daily aggregate statistics from raw data.

    Args:
        daily_data: Raw daily metrics data

    Returns:
        Dict mapping date strings to aggregated statistics
    """
    daily_stats = {}

    for date, metrics in sorted(daily_data.items()):
        d = {}

        # Activity metrics (sum)
        d['steps'] = sum(metrics.get('step_count', [0]))
        d['distance_km'] = sum(metrics.get('walking_running_distance', [0]))
        d['flights'] = sum(metrics.get('flights_climbed', [0]))
        d['exercise_min'] = sum(metrics.get('apple_exercise_time', [0]))
        d['active_cal'] = sum(metrics.get('active_energy', [0]))
        d['stand_hours'] = len([x for x in metrics.get('apple_stand_hour', []) if x >= 1])
        d['daylight_min'] = sum(metrics.get('time_in_daylight', [0]))

        # Swimming
        d['swim_distance'] = sum(metrics.get('swimming_distance', [0]))
        d['swim_strokes'] = sum(metrics.get('swimming_stroke_count', [0]))

        # Heart metrics
        hr = metrics.get('heart_rate', [])
        if hr:
            d['hr_avg'] = statistics.mean(hr)
            d['hr_min'] = min(hr)
            d['hr_max'] = max(hr)

        rhr = metrics.get('resting_heart_rate', [])
        if rhr:
            d['resting_hr'] = rhr[0]

        hrv = metrics.get('heart_rate_variability', [])
        if hrv:
            d['hrv_avg'] = statistics.mean(hrv)

        vo2 = metrics.get('vo2_max', [])
        if vo2:
            d['vo2_max'] = vo2[-1]

        # Walking mechanics
        speed = metrics.get('walking_speed', [])
        if speed:
            d['walk_speed'] = statistics.mean(speed)

        step_len = metrics.get('walking_step_length', [])
        if step_len:
            d['step_length'] = statistics.mean(step_len)

        asymm = metrics.get('walking_asymmetry_percentage', [])
        if asymm:
            d['walk_asymmetry'] = statistics.mean(asymm)

        # Respiratory
        spo2 = metrics.get('blood_oxygen_saturation', [])
        if spo2:
            d['spo2_avg'] = statistics.mean(spo2)
            d['spo2_min'] = min(spo2)

        resp = metrics.get('respiratory_rate', [])
        if resp:
            d['resp_rate'] = statistics.mean(resp)

        daily_stats[date] = d

    return daily_stats


def analyze_fitness_trajectory(daily_stats: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Analyze fitness trajectory over time using VO2 Max, RHR, and HRV.

    Returns:
        Dict containing trajectory analysis with early/late comparisons
    """
    result = {}

    # VO2 Max trend
    vo2_data = [(d, s['vo2_max']) for d, s in daily_stats.items() if 'vo2_max' in s]
    if vo2_data:
        early = [v for d, v in vo2_data[:len(vo2_data)//3]]
        late = [v for d, v in vo2_data[-len(vo2_data)//3:]]
        if early and late:
            result['vo2_max'] = {
                'early_avg': statistics.mean(early),
                'late_avg': statistics.mean(late),
                'change': statistics.mean(late) - statistics.mean(early),
                'improving': statistics.mean(late) > statistics.mean(early) + 1
            }

    # Resting HR trend
    rhr_data = [(d, s['resting_hr']) for d, s in daily_stats.items() if 'resting_hr' in s]
    if rhr_data:
        early = [v for d, v in rhr_data[:len(rhr_data)//3]]
        late = [v for d, v in rhr_data[-len(rhr_data)//3:]]
        if early and late:
            result['resting_hr'] = {
                'early_avg': statistics.mean(early),
                'late_avg': statistics.mean(late),
                'change': statistics.mean(late) - statistics.mean(early),
                'improving': statistics.mean(late) < statistics.mean(early) - 2
            }

    # HRV trend
    hrv_data = [(d, s['hrv_avg']) for d, s in daily_stats.items() if 'hrv_avg' in s]
    if hrv_data:
        early = [v for d, v in hrv_data[:len(hrv_data)//3]]
        late = [v for d, v in hrv_data[-len(hrv_data)//3:]]
        if early and late:
            result['hrv'] = {
                'early_avg': statistics.mean(early),
                'late_avg': statistics.mean(late),
                'change': statistics.mean(late) - statistics.mean(early),
                'improving': statistics.mean(late) > statistics.mean(early) + 5
            }

    return result


def analyze_weekly_patterns(daily_stats: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Analyze activity patterns by day of week.

    Returns:
        Dict mapping day names to average metrics
    """
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow_data = {day: defaultdict(list) for day in days}

    for date_str, stats in daily_stats.items():
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            dow = days[dt.weekday()]

            for key in ['steps', 'exercise_min', 'resting_hr', 'hrv_avg']:
                if stats.get(key, 0) > 0:
                    dow_data[dow][key].append(stats[key])
        except Exception:
            pass

    result = {}
    for day in days:
        result[day] = {}
        for key, values in dow_data[day].items():
            if values:
                result[day][key] = statistics.mean(values)

    return result


def analyze_monthly_progression(daily_stats: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    """
    Analyze monthly progression of key metrics.

    Returns:
        List of monthly summaries with averages
    """
    monthly = defaultdict(lambda: defaultdict(list))

    for date_str, stats in daily_stats.items():
        month = date_str[:7]
        for key, val in stats.items():
            if val and val > 0:
                monthly[month][key].append(val)

    result = []
    for month in sorted(monthly.keys()):
        m_data = {'month': month}
        for key in ['steps', 'exercise_min', 'resting_hr', 'hrv_avg', 'vo2_max']:
            values = monthly[month].get(key, [])
            if values:
                m_data[key] = statistics.mean(values)
        result.append(m_data)

    return result


def find_correlations(daily_stats: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, Any]]:
    """
    Find correlations between health metrics.

    Returns:
        Dict of correlation insights
    """
    dates = sorted(daily_stats.keys())
    correlations = {}

    # Exercise → Next day RHR
    pairs = []
    for i in range(len(dates) - 1):
        today = daily_stats[dates[i]]
        tomorrow = daily_stats[dates[i + 1]]
        if today.get('exercise_min', 0) > 0 and 'resting_hr' in tomorrow:
            pairs.append((today['exercise_min'], tomorrow['resting_hr']))

    if len(pairs) > 10:
        ex_vals = [p[0] for p in pairs]
        median_ex = statistics.median(ex_vals)
        high_ex_rhr = [p[1] for p in pairs if p[0] > median_ex]
        low_ex_rhr = [p[1] for p in pairs if p[0] <= median_ex]

        if high_ex_rhr and low_ex_rhr:
            correlations['exercise_to_rhr'] = {
                'high_exercise_threshold': median_ex,
                'high_exercise_next_rhr': statistics.mean(high_ex_rhr),
                'low_exercise_next_rhr': statistics.mean(low_ex_rhr),
                'difference': statistics.mean(low_ex_rhr) - statistics.mean(high_ex_rhr)
            }

    # Steps → Next day HRV
    pairs = []
    for i in range(len(dates) - 1):
        today = daily_stats[dates[i]]
        tomorrow = daily_stats[dates[i + 1]]
        if today.get('steps', 0) > 0 and 'hrv_avg' in tomorrow:
            pairs.append((today['steps'], tomorrow['hrv_avg']))

    if len(pairs) > 10:
        sorted_pairs = sorted(pairs, key=lambda x: x[0])
        n = len(sorted_pairs)
        terciles = [sorted_pairs[:n//3], sorted_pairs[n//3:2*n//3], sorted_pairs[2*n//3:]]

        correlations['steps_to_hrv'] = {
            'low_steps_hrv': statistics.mean([p[1] for p in terciles[0]]) if terciles[0] else 0,
            'medium_steps_hrv': statistics.mean([p[1] for p in terciles[1]]) if terciles[1] else 0,
            'high_steps_hrv': statistics.mean([p[1] for p in terciles[2]]) if terciles[2] else 0,
        }

    return correlations


def find_streaks(daily_stats: Dict[str, Dict[str, float]], goal_steps: int = 10000) -> Dict[str, Any]:
    """
    Find activity streaks and consistency metrics.

    Args:
        daily_stats: Daily statistics
        goal_steps: Step goal threshold

    Returns:
        Dict with streak information
    """
    dates = sorted(daily_stats.keys())

    # Step streak
    streak = 0
    max_streak = 0
    max_streak_end = ""
    current_streak = 0

    for date in dates:
        steps = daily_stats[date].get('steps', 0)
        if steps >= goal_steps:
            streak += 1
            if streak > max_streak:
                max_streak = streak
                max_streak_end = date
        else:
            streak = 0

    # Current streak (from most recent)
    for date in reversed(dates):
        if daily_stats[date].get('steps', 0) >= goal_steps:
            current_streak += 1
        else:
            break

    # Exercise consistency
    ex_days = [d for d in dates if daily_stats[d].get('exercise_min', 0) >= 30]

    return {
        'longest_step_streak': max_streak,
        'longest_streak_end': max_streak_end,
        'current_streak': current_streak,
        'exercise_days': len(ex_days),
        'total_days': len(dates),
        'exercise_consistency': len(ex_days) / len(dates) if dates else 0
    }


def find_personal_records(daily_stats: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, Any]]:
    """
    Find all-time personal records.

    Returns:
        Dict of records with values and dates
    """
    records = {}

    # Maximum records
    max_metrics = [
        ('max_steps', 'steps'),
        ('max_distance', 'distance_km'),
        ('max_exercise', 'exercise_min'),
        ('max_flights', 'flights'),
        ('max_swim_distance', 'swim_distance'),
        ('highest_hrv', 'hrv_avg'),
        ('highest_hr', 'hr_max'),
    ]

    for record_name, metric_name in max_metrics:
        vals = [(d, s[metric_name]) for d, s in daily_stats.items() if s.get(metric_name, 0) > 0]
        if vals:
            best_date, best_val = max(vals, key=lambda x: x[1])
            records[record_name] = {'value': best_val, 'date': best_date}

    # Minimum records (lower is better)
    min_metrics = [
        ('lowest_resting_hr', 'resting_hr'),
        ('lowest_hr', 'hr_min'),
    ]

    for record_name, metric_name in min_metrics:
        vals = [(d, s[metric_name]) for d, s in daily_stats.items() if s.get(metric_name, 0) > 0]
        if vals:
            best_date, best_val = min(vals, key=lambda x: x[1])
            records[record_name] = {'value': best_val, 'date': best_date}

    return records


def detect_anomalies(daily_stats: Dict[str, Dict[str, float]]) -> Dict[str, List[Tuple[str, float]]]:
    """
    Detect anomalous days (potential stress, illness, or intense workouts).

    Returns:
        Dict of anomaly types with list of (date, value) tuples
    """
    anomalies = {}

    # Low HRV days (potential stress/illness)
    hrv_data = [(d, s['hrv_avg']) for d, s in daily_stats.items() if 'hrv_avg' in s]
    if len(hrv_data) > 10:
        avg_hrv = statistics.mean([h[1] for h in hrv_data])
        std_hrv = statistics.stdev([h[1] for h in hrv_data])
        low_hrv = [(d, h) for d, h in hrv_data if h < avg_hrv - 1.5 * std_hrv]
        if low_hrv:
            anomalies['low_hrv_days'] = sorted(low_hrv, key=lambda x: x[1])[:10]
            anomalies['hrv_avg'] = avg_hrv

    # High intensity workout days
    hr_max_data = [(d, s['hr_max']) for d, s in daily_stats.items() if 'hr_max' in s]
    if len(hr_max_data) > 10:
        avg_max = statistics.mean([h[1] for h in hr_max_data])
        std_max = statistics.stdev([h[1] for h in hr_max_data])
        high_intensity = [(d, h) for d, h in hr_max_data if h > avg_max + 1.5 * std_max]
        if high_intensity:
            anomalies['high_intensity_days'] = sorted(high_intensity, key=lambda x: -x[1])[:10]

    return anomalies


def compare_recent_to_previous(daily_stats: Dict[str, Dict[str, float]], days: int = 30) -> Dict[str, Dict[str, float]]:
    """
    Compare recent period to previous period.

    Args:
        daily_stats: Daily statistics
        days: Number of days for each period

    Returns:
        Dict of metric comparisons
    """
    dates = sorted(daily_stats.keys())

    if len(dates) < days * 2:
        return {}

    recent = {d: s for d, s in daily_stats.items() if d >= dates[-days]}
    previous = {d: s for d, s in daily_stats.items() if dates[-(days*2)] <= d < dates[-days]}

    metrics_to_compare = ['steps', 'exercise_min', 'resting_hr', 'hrv_avg', 'vo2_max']
    comparisons = {}

    for metric in metrics_to_compare:
        recent_vals = [s[metric] for s in recent.values() if metric in s and s[metric] > 0]
        prev_vals = [s[metric] for s in previous.values() if metric in s and s[metric] > 0]

        if recent_vals and prev_vals:
            recent_avg = statistics.mean(recent_vals)
            prev_avg = statistics.mean(prev_vals)
            change = recent_avg - prev_avg
            pct_change = 100 * change / prev_avg if prev_avg else 0

            comparisons[metric] = {
                'recent_avg': recent_avg,
                'previous_avg': prev_avg,
                'change': change,
                'pct_change': pct_change
            }

    return comparisons


def generate_health_report(daily_stats: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Generate comprehensive health report.

    Returns:
        Dict containing all analysis results
    """
    return {
        'overview': {
            'total_days': len(daily_stats),
            'date_range': {
                'start': min(daily_stats.keys()) if daily_stats else None,
                'end': max(daily_stats.keys()) if daily_stats else None
            }
        },
        'fitness_trajectory': analyze_fitness_trajectory(daily_stats),
        'weekly_patterns': analyze_weekly_patterns(daily_stats),
        'monthly_progression': analyze_monthly_progression(daily_stats),
        'correlations': find_correlations(daily_stats),
        'streaks': find_streaks(daily_stats),
        'personal_records': find_personal_records(daily_stats),
        'anomalies': detect_anomalies(daily_stats),
        'recent_vs_previous': compare_recent_to_previous(daily_stats)
    }


def generate_actionable_insights(report: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate actionable insights from the health report.

    Args:
        report: Output from generate_health_report

    Returns:
        List of insight dicts with type, title, and text
    """
    insights = []

    # Fitness trajectory insights
    trajectory = report.get('fitness_trajectory', {})

    if trajectory.get('vo2_max', {}).get('improving'):
        change = trajectory['vo2_max']['change']
        insights.append({
            'type': 'positive',
            'icon': '🏃',
            'title': 'VO2 Max Improving',
            'text': f"Your cardiorespiratory fitness has improved by {change:.1f} ml/kg/min. Keep up the aerobic training!"
        })

    if trajectory.get('resting_hr', {}).get('improving'):
        insights.append({
            'type': 'positive',
            'icon': '❤️',
            'title': 'Heart Efficiency Improving',
            'text': "Your resting heart rate is trending lower, indicating improved cardiovascular efficiency."
        })

    # Streak insights
    streaks = report.get('streaks', {})
    if streaks.get('current_streak', 0) >= 7:
        insights.append({
            'type': 'positive',
            'icon': '🔥',
            'title': f"{streaks['current_streak']}-Day Streak!",
            'text': f"You're on a {streaks['current_streak']}-day streak of hitting 10K steps. Your record is {streaks['longest_step_streak']} days!"
        })

    if streaks.get('exercise_consistency', 0) >= 0.7:
        pct = int(streaks['exercise_consistency'] * 100)
        insights.append({
            'type': 'positive',
            'icon': '💪',
            'title': 'Exercise Champion',
            'text': f"You've exercised 30+ minutes on {pct}% of days. Excellent consistency!"
        })

    # Anomaly warnings
    anomalies = report.get('anomalies', {})
    if anomalies.get('low_hrv_days'):
        recent_low = [d for d, v in anomalies['low_hrv_days'] if d >= report['overview']['date_range']['end'][:8]]
        if recent_low:
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': 'Recovery Alert',
                'text': f"Your HRV was unusually low recently. Consider extra rest and stress management."
            })

    # Recent trend insights
    trends = report.get('recent_vs_previous', {})

    if trends.get('exercise_min', {}).get('pct_change', 0) > 20:
        insights.append({
            'type': 'positive',
            'icon': '📈',
            'title': 'Exercise Trending Up',
            'text': f"Your exercise time increased {trends['exercise_min']['pct_change']:.0f}% vs last month!"
        })

    if trends.get('resting_hr', {}).get('pct_change', 0) > 5:
        insights.append({
            'type': 'warning',
            'icon': '💓',
            'title': 'Resting HR Elevated',
            'text': "Your resting heart rate has increased recently. This could indicate stress, fatigue, or overtraining."
        })

    # Correlation-based insights
    correlations = report.get('correlations', {})
    steps_hrv = correlations.get('steps_to_hrv', {})
    if steps_hrv:
        best = max(['low_steps_hrv', 'medium_steps_hrv', 'high_steps_hrv'],
                   key=lambda k: steps_hrv.get(k, 0))
        if best == 'high_steps_hrv':
            insights.append({
                'type': 'neutral',
                'icon': '👣',
                'title': 'Steps & Recovery',
                'text': "Your data shows higher step counts (12K+) correlate with better next-day HRV. Movement aids recovery!"
            })

    return insights[:6]  # Return top 6 insights


def save_deep_analysis(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run full analysis and save results to JSON files.

    Args:
        output_dir: Output directory (uses config dashboard_data_path if not provided)

    Returns:
        The generated health report
    """
    if output_dir is None:
        output_dir = config.dashboard_data_path

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load and process data
    daily_data = load_all_health_data()
    daily_stats = calculate_daily_stats(daily_data)

    # Generate report
    report = generate_health_report(daily_stats)
    insights = generate_actionable_insights(report)

    # Save files
    with open(output_dir / 'deep_analysis.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)

    with open(output_dir / 'deep_insights.json', 'w') as f:
        json.dump(insights, f, indent=2)

    with open(output_dir / 'monthly_progression.json', 'w') as f:
        json.dump(report['monthly_progression'], f, indent=2)

    with open(output_dir / 'weekly_patterns.json', 'w') as f:
        json.dump(report['weekly_patterns'], f, indent=2)

    with open(output_dir / 'all_personal_records.json', 'w') as f:
        json.dump(report['personal_records'], f, indent=2, default=str)

    with open(output_dir / 'correlations.json', 'w') as f:
        json.dump(report['correlations'], f, indent=2)

    print(f"Deep analysis saved to {output_dir}")
    print(f"  - deep_analysis.json (full report)")
    print(f"  - deep_insights.json ({len(insights)} insights)")
    print(f"  - monthly_progression.json")
    print(f"  - weekly_patterns.json")
    print(f"  - all_personal_records.json")
    print(f"  - correlations.json")

    return report


if __name__ == '__main__':
    report = save_deep_analysis()

    print("\n" + "=" * 60)
    print("DEEP ANALYSIS SUMMARY")
    print("=" * 60)

    overview = report['overview']
    print(f"\nAnalyzed {overview['total_days']} days")
    print(f"From {overview['date_range']['start']} to {overview['date_range']['end']}")

    print("\n📊 Monthly Progression:")
    for month in report['monthly_progression'][-3:]:
        print(f"  {month['month']}: {month.get('steps', 0):,.0f} steps, {month.get('exercise_min', 0):.0f} min exercise")

    print("\n🏆 Personal Records:")
    for name, record in list(report['personal_records'].items())[:5]:
        print(f"  {name}: {record['value']:.1f} ({record['date']})")

    print("\n💡 Insights:")
    for insight in generate_actionable_insights(report):
        print(f"  {insight['icon']} {insight['title']}")
