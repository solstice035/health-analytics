#!/usr/bin/env python3
"""
Hevy Analysis - Extract and analyze workout metrics from Hevy data.

Functions follow the pattern established in detailed_analysis.py:
- extract_workout_metrics(data) - raw API response to structured data
- calculate_workout_totals(workouts, date_str) - daily aggregations
- get_workout_records(workouts) - personal records by exercise
- get_muscle_group_stats(workouts, days) - muscle group distribution
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Exercise name to muscle group mapping (keywords to match)
MUSCLE_GROUP_KEYWORDS = {
    # Chest
    'chest': ['bench press', 'incline press', 'decline press', 'chest press',
              'dumbbell fly', 'cable fly', 'push up', 'pushup', 'pec deck',
              'chest fly', 'floor press'],
    # Back
    'back': ['deadlift', 'row', 'pull up', 'pullup', 'chin up', 'chinup',
             'lat pulldown', 'pulldown', 'pull-up', 'chin-up', 'shrug',
             'back extension', 'hyperextension', 'seated row', 'cable row',
             't-bar', 'rack pull'],
    # Shoulders
    'shoulders': ['shoulder press', 'overhead press', 'ohp', 'military press',
                  'lateral raise', 'front raise', 'rear delt', 'face pull',
                  'upright row', 'arnold press', 'delt'],
    # Arms
    'arms': ['bicep', 'curl', 'hammer curl', 'preacher curl', 'concentration',
             'tricep', 'pushdown', 'skull crusher', 'tricep extension',
             'close grip', 'kickback', 'dip'],
    # Legs
    'legs': ['squat', 'leg press', 'leg extension', 'lunge', 'hack squat',
             'front squat', 'romanian deadlift', 'rdl', 'leg curl',
             'hamstring', 'glute', 'hip thrust', 'good morning', 'stiff leg',
             'calf raise', 'calf press', 'single leg', 'split squat',
             'step up', 'goblet'],
    # Core
    'core': ['crunch', 'sit up', 'situp', 'plank', 'leg raise', 'ab ',
             'cable crunch', 'russian twist', 'wood chop', 'hollow',
             'dead bug', 'mountain climber'],
    # Cardio
    'cardio': ['treadmill', 'elliptical', 'bike', 'rowing', 'run', 'walk',
               'cycling', 'stair', 'jump rope', 'burpee', 'cardio',
               'hiit', 'sprint'],
}


def infer_muscle_group(exercise_name: str) -> str:
    """
    Infer muscle group from exercise name using keyword matching.

    Args:
        exercise_name: Name of the exercise

    Returns:
        Muscle group string (lowercase)
    """
    name_lower = exercise_name.lower()

    for group, keywords in MUSCLE_GROUP_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return group

    return 'other'


def extract_workout_metrics(
    api_response: Optional[Dict[str, Any]],
    template_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Extract workouts from API response into structured format.

    Handles various possible API response formats. The Hevy API structure
    may vary, so we try multiple possible keys.

    Args:
        api_response: Raw API response
        template_map: Optional dict mapping exercise_template_id to template data
                     (includes primary_muscle_group). If not provided, muscle
                     groups are inferred from exercise names.

    Returns:
        List of structured workout dicts
    """
    if not api_response:
        return []

    # Try to find workouts in various possible locations
    workouts_raw = (
        api_response.get('workouts') or
        api_response.get('data') or
        api_response.get('results') or
        (api_response if isinstance(api_response, list) else [])
    )

    if not isinstance(workouts_raw, list):
        workouts_raw = [workouts_raw] if workouts_raw else []

    workouts = []
    for w in workouts_raw:
        if not isinstance(w, dict):
            continue

        workout = _parse_workout(w, template_map)
        if workout:
            workouts.append(workout)

    # Sort by date (newest first)
    workouts.sort(key=lambda x: x.get('start_time', ''), reverse=True)

    return workouts


def _parse_workout(
    w: Dict[str, Any],
    template_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """Parse a single workout from the API response."""
    # Extract start time (try various possible keys)
    start_time = (
        w.get('start_time') or
        w.get('startTime') or
        w.get('started_at') or
        w.get('date') or
        ''
    )

    # Extract end time
    end_time = (
        w.get('end_time') or
        w.get('endTime') or
        w.get('ended_at') or
        w.get('completed_at') or
        ''
    )

    # Parse date from start_time
    date_str = _extract_date(start_time)

    workout = {
        'id': w.get('id') or w.get('workout_id') or '',
        'name': w.get('name') or w.get('title') or 'Workout',
        'date': date_str,
        'start_time': start_time,
        'end_time': end_time,
        'duration_minutes': _calculate_duration(start_time, end_time),
        'exercises': [],
        'total_volume_kg': 0,
        'total_sets': 0,
        'total_reps': 0,
        'muscle_groups': []
    }

    # Parse exercises
    exercises_raw = (
        w.get('exercises') or
        w.get('exercise_data') or
        []
    )

    muscle_groups_set = set()

    for e in exercises_raw:
        if not isinstance(e, dict):
            continue

        exercise = _parse_exercise(e, template_map)
        if exercise:
            workout['exercises'].append(exercise)
            workout['total_volume_kg'] += exercise['volume_kg']
            workout['total_sets'] += exercise['set_count']
            workout['total_reps'] += exercise['total_reps']
            if exercise['muscle_group']:
                muscle_groups_set.add(exercise['muscle_group'])

    workout['muscle_groups'] = list(muscle_groups_set)
    workout['exercise_count'] = len(workout['exercises'])

    return workout


def _parse_exercise(
    e: Dict[str, Any],
    template_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """Parse a single exercise from workout data."""
    # Get exercise name (Hevy API uses 'title')
    name = e.get('title') or e.get('name') or e.get('exercise_name') or 'Unknown'

    # Get muscle group from template map using exercise_template_id
    template_id = e.get('exercise_template_id')
    muscle_group = None

    if template_map and template_id and template_id in template_map:
        template = template_map[template_id]
        muscle_group = template.get('primary_muscle_group', '')

    # Fallback: try to get from exercise data directly, then infer from name
    if not muscle_group:
        muscle_group = (
            e.get('muscle_group') or
            e.get('primary_muscle_group') or
            e.get('category') or
            ''
        )
    if not muscle_group or muscle_group == 'other':
        muscle_group = infer_muscle_group(name)

    exercise = {
        'name': name,
        'muscle_group': muscle_group.lower(),
        'sets': [],
        'volume_kg': 0,
        'max_weight_kg': 0,
        'total_reps': 0,
        'set_count': 0
    }

    # Parse sets
    sets_raw = e.get('sets') or e.get('set_data') or []

    for s in sets_raw:
        if not isinstance(s, dict):
            continue

        # Extract reps and weight (try various keys)
        reps = int(s.get('reps') or s.get('repetitions') or 0)
        weight = float(s.get('weight_kg') or s.get('weight') or 0)

        # Convert lbs to kg if needed
        if s.get('weight_unit') == 'lbs' or s.get('unit') == 'lb':
            weight = weight * 0.453592

        set_type = s.get('type') or s.get('set_type') or 'working'

        exercise['sets'].append({
            'reps': reps,
            'weight_kg': round(weight, 1),
            'type': set_type
        })

        # Only count working sets for volume
        if set_type.lower() in ('working', 'normal', 'drop', 'dropset'):
            exercise['volume_kg'] += reps * weight
            exercise['total_reps'] += reps

        exercise['max_weight_kg'] = max(exercise['max_weight_kg'], weight)
        exercise['set_count'] += 1

    exercise['volume_kg'] = round(exercise['volume_kg'], 1)
    exercise['max_weight_kg'] = round(exercise['max_weight_kg'], 1)

    return exercise


def _extract_date(timestamp: str) -> str:
    """Extract YYYY-MM-DD date from various timestamp formats."""
    if not timestamp:
        return datetime.now().strftime('%Y-%m-%d')

    # Try to parse ISO format
    for fmt in [
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d'
    ]:
        try:
            dt = datetime.strptime(timestamp[:26].replace('Z', ''), fmt.replace('Z', '').replace('%z', ''))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Fallback: try to extract date portion
    if len(timestamp) >= 10:
        return timestamp[:10]

    return datetime.now().strftime('%Y-%m-%d')


def _calculate_duration(start: str, end: str) -> int:
    """Calculate workout duration in minutes."""
    if not start or not end:
        return 0

    try:
        # Parse timestamps
        for fmt in [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S'
        ]:
            try:
                start_dt = datetime.strptime(start[:26].replace('Z', ''), fmt.replace('Z', ''))
                end_dt = datetime.strptime(end[:26].replace('Z', ''), fmt.replace('Z', ''))
                return max(0, int((end_dt - start_dt).total_seconds() / 60))
            except ValueError:
                continue
    except Exception:
        pass

    return 0


def calculate_workout_totals(workouts: List[Dict], date_str: str) -> Dict[str, Any]:
    """
    Calculate daily workout totals (mirrors detailed_analysis.calculate_totals pattern).

    Args:
        workouts: List of parsed workouts
        date_str: Date in YYYY-MM-DD format

    Returns:
        Dict with daily totals or empty dict if no workouts
    """
    day_workouts = [w for w in workouts if w.get('date') == date_str]

    if not day_workouts:
        return {}

    return {
        'workout_count': len(day_workouts),
        'total_volume_kg': round(sum(w['total_volume_kg'] for w in day_workouts), 1),
        'total_sets': sum(w['total_sets'] for w in day_workouts),
        'total_reps': sum(w['total_reps'] for w in day_workouts),
        'workout_duration_minutes': sum(w['duration_minutes'] for w in day_workouts),
        'exercise_count': sum(w['exercise_count'] for w in day_workouts),
        'muscle_groups': list(set(
            mg for w in day_workouts for mg in w['muscle_groups']
        ))
    }


def get_workout_records(workouts: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """
    Extract personal records for each exercise.

    Args:
        workouts: List of parsed workouts

    Returns:
        Dict mapping exercise names to their records
    """
    records = defaultdict(lambda: {
        'max_weight_kg': 0,
        'max_weight_date': None,
        'max_volume_kg': 0,
        'max_volume_date': None,
        'total_sessions': 0
    })

    for workout in workouts:
        workout_date = workout.get('date')

        for exercise in workout.get('exercises', []):
            name = exercise['name']
            records[name]['total_sessions'] += 1

            # Track max weight
            if exercise['max_weight_kg'] > records[name]['max_weight_kg']:
                records[name]['max_weight_kg'] = exercise['max_weight_kg']
                records[name]['max_weight_date'] = workout_date

            # Track max volume (single exercise volume)
            if exercise['volume_kg'] > records[name]['max_volume_kg']:
                records[name]['max_volume_kg'] = exercise['volume_kg']
                records[name]['max_volume_date'] = workout_date

    return dict(records)


def get_muscle_group_stats(
    workouts: List[Dict],
    days: int = 7
) -> Dict[str, Any]:
    """
    Analyze muscle group distribution over a period.

    Args:
        workouts: List of parsed workouts
        days: Number of days to analyze

    Returns:
        Dict with volume and frequency distributions
    """
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent_workouts = [w for w in workouts if w.get('date', '') >= cutoff_date]

    volume_by_group = defaultdict(float)
    frequency_by_group = defaultdict(int)
    sets_by_group = defaultdict(int)

    for workout in recent_workouts:
        for exercise in workout.get('exercises', []):
            group = exercise['muscle_group']
            volume_by_group[group] += exercise['volume_kg']
            frequency_by_group[group] += 1
            sets_by_group[group] += exercise['set_count']

    # Round volumes
    volume_by_group = {k: round(v, 1) for k, v in volume_by_group.items()}

    # Calculate percentages
    total_volume = sum(volume_by_group.values())
    volume_percentages = {}
    if total_volume > 0:
        volume_percentages = {
            k: round(v / total_volume * 100, 1)
            for k, v in volume_by_group.items()
        }

    return {
        'period_days': days,
        'workout_count': len(recent_workouts),
        'volume_distribution': dict(volume_by_group),
        'volume_percentages': volume_percentages,
        'frequency_distribution': dict(frequency_by_group),
        'sets_distribution': dict(sets_by_group)
    }


def get_weekly_summary(workouts: List[Dict], weeks: int = 4) -> List[Dict[str, Any]]:
    """
    Generate weekly workout summaries.

    Args:
        workouts: List of parsed workouts
        weeks: Number of weeks to summarize

    Returns:
        List of weekly summary dicts
    """
    summaries = []
    today = datetime.now()

    for week_offset in range(weeks):
        # Calculate week boundaries (Monday to Sunday)
        week_end = today - timedelta(days=today.weekday() + 7 * week_offset)
        week_start = week_end - timedelta(days=6)

        start_str = week_start.strftime('%Y-%m-%d')
        end_str = week_end.strftime('%Y-%m-%d')

        week_workouts = [
            w for w in workouts
            if start_str <= w.get('date', '') <= end_str
        ]

        if not week_workouts:
            summaries.append({
                'week_start': start_str,
                'week_end': end_str,
                'workout_count': 0,
                'total_volume_kg': 0,
                'total_sets': 0,
                'avg_duration': 0
            })
            continue

        total_duration = sum(w['duration_minutes'] for w in week_workouts)

        summaries.append({
            'week_start': start_str,
            'week_end': end_str,
            'workout_count': len(week_workouts),
            'total_volume_kg': round(sum(w['total_volume_kg'] for w in week_workouts), 1),
            'total_sets': sum(w['total_sets'] for w in week_workouts),
            'avg_duration': round(total_duration / len(week_workouts)) if week_workouts else 0,
            'muscle_groups': list(set(mg for w in week_workouts for mg in w['muscle_groups']))
        })

    return summaries


def analyze_workouts(workouts: List[Dict]) -> None:
    """Print detailed workout analysis (similar to detailed_analysis.analyze_date)."""
    if not workouts:
        print("No workouts found")
        return

    print("=" * 70)
    print("🏋️ Hevy Workout Analysis")
    print("=" * 70)

    # Recent activity
    print(f"\n📊 WORKOUT SUMMARY (Last 7 Days)")
    print("-" * 70)

    stats = get_muscle_group_stats(workouts, days=7)
    print(f"Workouts:          {stats['workout_count']}")

    total_volume = sum(stats['volume_distribution'].values())
    print(f"Total Volume:      {total_volume:,.0f} kg")

    total_sets = sum(stats['sets_distribution'].values())
    print(f"Total Sets:        {total_sets}")

    # Muscle group breakdown
    if stats['volume_distribution']:
        print(f"\n💪 MUSCLE GROUP VOLUME")
        print("-" * 70)
        sorted_groups = sorted(
            stats['volume_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for group, volume in sorted_groups:
            pct = stats['volume_percentages'].get(group, 0)
            bar = "█" * int(pct / 5)
            print(f"{group.title():15} {volume:8,.0f} kg  {pct:5.1f}%  {bar}")

    # Personal records
    print(f"\n🏆 PERSONAL RECORDS")
    print("-" * 70)
    records = get_workout_records(workouts)
    sorted_records = sorted(
        records.items(),
        key=lambda x: x[1]['max_weight_kg'],
        reverse=True
    )[:10]

    for name, record in sorted_records:
        print(f"{name:30} {record['max_weight_kg']:6.1f} kg ({record['max_weight_date']})")

    # Recent workouts
    print(f"\n📅 RECENT WORKOUTS")
    print("-" * 70)
    for workout in workouts[:5]:
        duration = workout['duration_minutes']
        volume = workout['total_volume_kg']
        exercises = workout['exercise_count']
        print(f"{workout['date']}  {workout['name']:25} {duration:3}min  {volume:6.0f}kg  {exercises} exercises")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Test with cached data
    try:
        from hevy_helper import fetch_and_cache_workouts, get_hevy_status

        status = get_hevy_status()
        if not status['configured']:
            print("Hevy not configured. Set HEVY_API and HEVY_USERNAME in .env")
            sys.exit(1)

        print("Fetching workout data...")
        data = fetch_and_cache_workouts()

        if data:
            workouts = extract_workout_metrics(data)
            print(f"Loaded {len(workouts)} workouts\n")
            analyze_workouts(workouts)
        else:
            print("No data returned from API")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
