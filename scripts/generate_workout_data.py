#!/usr/bin/env python3
"""
Generate Workout Dashboard Data - Create JSON data files for workout visualizations.

This script processes Hevy workout data and generates JSON files for the dashboard:
- workout_trends.json - 30-day workout activity (volume, frequency, duration)
- workout_summary.json - 7-day summary statistics
- muscle_groups.json - Volume distribution by muscle group
- exercise_prs.json - Personal records by exercise
- workout_insights.json - Training insights and recommendations
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from hevy_helper import (
        fetch_and_cache_workouts,
        fetch_and_cache_exercise_templates,
        get_hevy_status,
        HevyAPIError
    )
    from hevy_analysis import (
        extract_workout_metrics,
        calculate_workout_totals,
        get_workout_records,
        get_muscle_group_stats,
        get_weekly_summary
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from hevy_helper import (
        fetch_and_cache_workouts,
        fetch_and_cache_exercise_templates,
        get_hevy_status,
        HevyAPIError
    )
    from hevy_analysis import (
        extract_workout_metrics,
        calculate_workout_totals,
        get_workout_records,
        get_muscle_group_stats,
        get_weekly_summary
    )

# Use centralized config
try:
    from health_analytics.config import config
    OUTPUT_PATH = config.dashboard_data_path
except ImportError:
    OUTPUT_PATH = Path(__file__).parent.parent / "dashboard" / "data"


def generate_workout_trends(workouts: List[Dict], days: int = 30) -> Dict[str, Any]:
    """
    Generate daily workout trend data for the past N days.

    Args:
        workouts: List of parsed workouts
        days: Number of days to include

    Returns:
        Dict with dates and daily metrics arrays
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)

    trends = {
        'dates': [],
        'workout_count': [],
        'volume_kg': [],
        'duration_minutes': [],
        'sets': [],
        'exercises': []
    }

    current = start_date
    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        totals = calculate_workout_totals(workouts, date_str)

        trends['dates'].append(date_str)
        trends['workout_count'].append(totals.get('workout_count', 0))
        trends['volume_kg'].append(totals.get('total_volume_kg', 0))
        trends['duration_minutes'].append(totals.get('workout_duration_minutes', 0))
        trends['sets'].append(totals.get('total_sets', 0))
        trends['exercises'].append(totals.get('exercise_count', 0))

        current += timedelta(days=1)

    return trends


def generate_workout_summary(workouts: List[Dict], days: int = 7) -> Dict[str, Any]:
    """
    Generate workout summary statistics for a period.

    Args:
        workouts: List of parsed workouts
        days: Number of days to summarize

    Returns:
        Summary statistics dict
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [w for w in workouts if w.get('date', '') >= cutoff]

    if not recent:
        return {
            'period_days': days,
            'workout_count': 0,
            'avg_workouts_per_week': 0,
            'total_volume_kg': 0,
            'total_sets': 0,
            'total_reps': 0,
            'total_duration_minutes': 0,
            'avg_workout_duration': 0,
            'unique_exercises': 0,
            'training_days': 0
        }

    # Get unique training days
    training_days = len(set(w['date'] for w in recent))

    # Calculate totals
    total_duration = sum(w['duration_minutes'] for w in recent)

    # Get unique exercises
    all_exercises = set()
    for w in recent:
        for e in w.get('exercises', []):
            all_exercises.add(e['name'])

    return {
        'period_days': days,
        'workout_count': len(recent),
        'avg_workouts_per_week': round(len(recent) / (days / 7), 1),
        'total_volume_kg': round(sum(w['total_volume_kg'] for w in recent), 0),
        'total_sets': sum(w['total_sets'] for w in recent),
        'total_reps': sum(w['total_reps'] for w in recent),
        'total_duration_minutes': total_duration,
        'avg_workout_duration': round(total_duration / len(recent)) if recent else 0,
        'unique_exercises': len(all_exercises),
        'training_days': training_days
    }


def generate_muscle_group_data(workouts: List[Dict], days: int = 7) -> Dict[str, Any]:
    """
    Generate muscle group distribution data for charts.

    Args:
        workouts: List of parsed workouts
        days: Period to analyze

    Returns:
        Dict formatted for pie/bar charts
    """
    stats = get_muscle_group_stats(workouts, days=days)

    volume_dist = stats.get('volume_distribution', {})
    total_volume = sum(volume_dist.values())

    # Sort by volume (descending)
    sorted_groups = sorted(volume_dist.items(), key=lambda x: x[1], reverse=True)

    labels = [g[0].title() for g in sorted_groups]
    volumes = [g[1] for g in sorted_groups]
    percentages = [
        round(v / total_volume * 100, 1) if total_volume > 0 else 0
        for v in volumes
    ]

    return {
        'labels': labels,
        'volume_kg': volumes,
        'percentages': percentages,
        'sets': [stats['sets_distribution'].get(g[0], 0) for g in sorted_groups],
        'frequency': [stats['frequency_distribution'].get(g[0], 0) for g in sorted_groups],
        'total_volume_kg': round(total_volume, 0)
    }


def generate_exercise_prs(workouts: List[Dict], limit: int = 20) -> Dict[str, Any]:
    """
    Generate personal records data for each exercise.

    Args:
        workouts: List of parsed workouts
        limit: Maximum number of exercises to include

    Returns:
        Dict with exercise PR data
    """
    records = get_workout_records(workouts)

    # Sort by max weight (descending)
    sorted_records = sorted(
        records.items(),
        key=lambda x: x[1]['max_weight_kg'],
        reverse=True
    )[:limit]

    prs = {
        'exercises': [],
        'generated_at': datetime.now().isoformat()
    }

    for name, record in sorted_records:
        prs['exercises'].append({
            'name': name,
            'max_weight_kg': record['max_weight_kg'],
            'max_weight_date': record['max_weight_date'],
            'max_volume_kg': record['max_volume_kg'],
            'max_volume_date': record['max_volume_date'],
            'total_sessions': record['total_sessions']
        })

    return prs


def generate_workout_insights(
    workouts: List[Dict],
    summary: Dict[str, Any],
    muscle_stats: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Generate training insights based on workout patterns.

    Args:
        workouts: List of parsed workouts
        summary: Summary statistics
        muscle_stats: Muscle group statistics

    Returns:
        List of insight dicts
    """
    insights = []

    if not workouts:
        return [{
            'type': 'neutral',
            'icon': '📊',
            'title': 'Start Tracking',
            'text': 'Sync your Hevy workouts to see training insights.'
        }]

    # Workout frequency insight
    avg_per_week = summary.get('avg_workouts_per_week', 0)
    if avg_per_week >= 4:
        insights.append({
            'type': 'positive',
            'icon': '💪',
            'title': 'Consistent Training',
            'text': f"Averaging {avg_per_week} workouts/week. Great consistency!"
        })
    elif avg_per_week >= 2:
        insights.append({
            'type': 'neutral',
            'icon': '📈',
            'title': 'Good Progress',
            'text': f"Training {avg_per_week}x per week. Try adding one more session."
        })
    elif avg_per_week > 0:
        insights.append({
            'type': 'warning',
            'icon': '📉',
            'title': 'Training Opportunity',
            'text': 'Consider increasing workout frequency for better results.'
        })

    # Volume insight
    total_volume = summary.get('total_volume_kg', 0)
    if total_volume > 20000:
        insights.append({
            'type': 'positive',
            'icon': '🏋️',
            'title': 'High Volume Week',
            'text': f"Moved {total_volume:,.0f} kg this week. Impressive work!"
        })
    elif total_volume > 10000:
        insights.append({
            'type': 'positive',
            'icon': '🔥',
            'title': 'Solid Training',
            'text': f"Total volume of {total_volume:,.0f} kg. Keep pushing!"
        })

    # Muscle balance insight
    percentages = muscle_stats.get('percentages', [])
    labels = muscle_stats.get('labels', [])

    if percentages and labels:
        max_pct = max(percentages)
        dominant_group = labels[percentages.index(max_pct)]

        if max_pct > 40:
            insights.append({
                'type': 'warning',
                'icon': '⚖️',
                'title': 'Training Focus',
                'text': f"{dominant_group} dominates at {max_pct}% of volume. Consider balance."
            })

    # Workout duration insight
    avg_duration = summary.get('avg_workout_duration', 0)
    if avg_duration > 90:
        insights.append({
            'type': 'neutral',
            'icon': '⏱️',
            'title': 'Marathon Sessions',
            'text': f"Avg workout is {avg_duration} min. Shorter, focused sessions can be effective too."
        })
    elif 45 <= avg_duration <= 75:
        insights.append({
            'type': 'positive',
            'icon': '✅',
            'title': 'Optimal Duration',
            'text': f"Your {avg_duration}-min workouts hit the sweet spot for gains."
        })

    # Recent PR check
    records = get_workout_records(workouts)
    recent_prs = []
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    for name, record in records.items():
        if record['max_weight_date'] and record['max_weight_date'] >= week_ago:
            recent_prs.append((name, record['max_weight_kg']))

    if recent_prs:
        pr_name, pr_weight = max(recent_prs, key=lambda x: x[1])
        insights.append({
            'type': 'positive',
            'icon': '🏆',
            'title': 'New Personal Record!',
            'text': f"Hit {pr_weight}kg on {pr_name} this week!"
        })

    # Default if no insights
    if not insights:
        insights.append({
            'type': 'neutral',
            'icon': '💪',
            'title': 'Keep Training',
            'text': 'Continue logging workouts for personalized insights.'
        })

    return insights[:4]  # Max 4 insights


def main():
    """Generate all workout dashboard data files."""
    print("🏋️ Generating Workout Dashboard Data...")
    print("=" * 60)

    # Check Hevy configuration
    status = get_hevy_status()
    if not status['configured']:
        print("❌ Hevy not configured")
        print("   Set HEVY_API in .env file")
        return 1

    print("📡 Fetching data from Hevy API...")

    # Fetch exercise templates for muscle group lookup
    try:
        template_map = fetch_and_cache_exercise_templates()
        print(f"  ✓ {len(template_map)} exercise templates")
    except HevyAPIError as e:
        print(f"  ⚠️  Could not fetch templates: {e}")
        template_map = {}

    # Fetch workout data
    try:
        api_response = fetch_and_cache_workouts()
    except HevyAPIError as e:
        print(f"❌ API Error: {e}")
        return 1

    if not api_response:
        print("❌ Could not fetch workout data")
        return 1

    # Parse workouts with template map for accurate muscle groups
    workouts = extract_workout_metrics(api_response, template_map)
    print(f"  ✓ {len(workouts)} workouts")

    if not workouts:
        print("⚠️  No workouts found in response")
        print(f"   Response keys: {list(api_response.keys())}")
        # Still generate empty files so dashboard doesn't break
        workouts = []

    # Ensure output directory exists
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    print("\n📊 Generating workout visualizations...")

    # 1. Workout trends (30 days)
    trends = generate_workout_trends(workouts, days=30)
    with open(OUTPUT_PATH / "workout_trends.json", "w") as f:
        json.dump(trends, f, indent=2)
    training_days = sum(1 for c in trends['workout_count'] if c > 0)
    print(f"  ✓ workout_trends.json ({training_days} training days)")

    # 2. Workout summary (7 days)
    summary = generate_workout_summary(workouts, days=7)
    with open(OUTPUT_PATH / "workout_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  ✓ workout_summary.json ({summary['workout_count']} workouts)")

    # 3. Muscle groups (use 30 days to match trends)
    muscle_data = generate_muscle_group_data(workouts, days=30)
    with open(OUTPUT_PATH / "muscle_groups.json", "w") as f:
        json.dump(muscle_data, f, indent=2)
    print(f"  ✓ muscle_groups.json ({len(muscle_data['labels'])} groups)")

    # 4. Exercise PRs
    prs = generate_exercise_prs(workouts, limit=20)
    with open(OUTPUT_PATH / "exercise_prs.json", "w") as f:
        json.dump(prs, f, indent=2)
    print(f"  ✓ exercise_prs.json ({len(prs['exercises'])} exercises)")

    # 5. Workout insights
    insights = generate_workout_insights(workouts, summary, muscle_data)
    with open(OUTPUT_PATH / "workout_insights.json", "w") as f:
        json.dump({'insights': insights}, f, indent=2)
    print(f"  ✓ workout_insights.json ({len(insights)} insights)")

    # Print summary
    print("\n" + "=" * 60)
    print("📈 WORKOUT SUMMARY (Last 7 Days)")
    print("=" * 60)
    print(f"  Workouts:      {summary['workout_count']}")
    print(f"  Volume:        {summary['total_volume_kg']:,.0f} kg")
    print(f"  Total Sets:    {summary['total_sets']}")
    print(f"  Avg Duration:  {summary['avg_workout_duration']} min")

    if muscle_data['labels']:
        print(f"\n  Top Muscle Groups:")
        for i, (label, pct) in enumerate(zip(muscle_data['labels'][:3], muscle_data['percentages'][:3])):
            print(f"    {i+1}. {label}: {pct}%")

    print("\n" + "=" * 60)
    print("✅ Workout data generated successfully!")
    print(f"📁 Output directory: {OUTPUT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
