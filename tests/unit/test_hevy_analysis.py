"""
Unit tests for hevy_analysis module.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from hevy_analysis import (
    extract_workout_metrics,
    calculate_workout_totals,
    get_workout_records,
    get_muscle_group_stats,
    get_weekly_summary,
    _parse_workout,
    _parse_exercise,
    _extract_date,
    _calculate_duration
)


@pytest.fixture
def sample_hevy_data():
    """Load sample Hevy data from fixture file."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    with open(fixtures_dir / "sample_hevy_data.json") as f:
        return json.load(f)


@pytest.fixture
def parsed_workouts(sample_hevy_data):
    """Get parsed workouts from sample data."""
    return extract_workout_metrics(sample_hevy_data)


class TestExtractWorkoutMetrics:
    """Tests for extract_workout_metrics function."""

    @pytest.mark.unit
    def test_extracts_all_workouts(self, sample_hevy_data):
        """Should extract all workouts from API response."""
        workouts = extract_workout_metrics(sample_hevy_data)
        assert len(workouts) == 3

    @pytest.mark.unit
    def test_returns_empty_for_none(self):
        """Should return empty list for None input."""
        result = extract_workout_metrics(None)
        assert result == []

    @pytest.mark.unit
    def test_returns_empty_for_empty_dict(self):
        """Should return empty list for empty dict."""
        result = extract_workout_metrics({})
        assert result == []

    @pytest.mark.unit
    def test_workout_has_required_fields(self, parsed_workouts):
        """Should include all required fields in parsed workout."""
        workout = parsed_workouts[0]

        assert 'id' in workout
        assert 'name' in workout
        assert 'date' in workout
        assert 'start_time' in workout
        assert 'exercises' in workout
        assert 'total_volume_kg' in workout
        assert 'total_sets' in workout
        assert 'muscle_groups' in workout

    @pytest.mark.unit
    def test_calculates_total_volume(self, parsed_workouts):
        """Should calculate total volume correctly."""
        # Find the Push Day workout
        push_day = next(w for w in parsed_workouts if w['name'] == 'Push Day')

        # Volume = sum of (reps * weight) for working sets
        # Bench: (8*80) + (8*80) + (6*85) = 640 + 640 + 510 = 1790
        # OHP: (10*40) + (8*45) + (8*45) = 400 + 360 + 360 = 1120
        # Triceps: (12*25) + (12*25) + (10*27.5) = 300 + 300 + 275 = 875
        # Total = 3785
        assert push_day['total_volume_kg'] == pytest.approx(3785, rel=0.01)

    @pytest.mark.unit
    def test_extracts_muscle_groups(self, parsed_workouts):
        """Should extract unique muscle groups."""
        push_day = next(w for w in parsed_workouts if w['name'] == 'Push Day')

        assert 'chest' in push_day['muscle_groups']
        assert 'shoulders' in push_day['muscle_groups']
        assert 'triceps' in push_day['muscle_groups']

    @pytest.mark.unit
    def test_workouts_sorted_by_date(self, parsed_workouts):
        """Should sort workouts by date (newest first)."""
        dates = [w['date'] for w in parsed_workouts]
        assert dates == sorted(dates, reverse=True)


class TestParseExercise:
    """Tests for _parse_exercise function."""

    @pytest.mark.unit
    def test_calculates_exercise_volume(self):
        """Should calculate volume for working sets only."""
        exercise_data = {
            'name': 'Bench Press',
            'muscle_group': 'chest',
            'sets': [
                {'reps': 10, 'weight_kg': 60, 'type': 'warmup'},
                {'reps': 8, 'weight_kg': 80, 'type': 'working'},
                {'reps': 8, 'weight_kg': 80, 'type': 'working'}
            ]
        }

        result = _parse_exercise(exercise_data)

        # Only working sets: (8*80) + (8*80) = 1280
        assert result['volume_kg'] == pytest.approx(1280, rel=0.01)

    @pytest.mark.unit
    def test_tracks_max_weight(self):
        """Should track maximum weight used."""
        exercise_data = {
            'name': 'Squat',
            'muscle_group': 'legs',
            'sets': [
                {'reps': 5, 'weight_kg': 80, 'type': 'working'},
                {'reps': 5, 'weight_kg': 100, 'type': 'working'},
                {'reps': 3, 'weight_kg': 120, 'type': 'working'}
            ]
        }

        result = _parse_exercise(exercise_data)

        assert result['max_weight_kg'] == 120

    @pytest.mark.unit
    def test_counts_total_sets(self):
        """Should count all sets including warmups."""
        exercise_data = {
            'name': 'Deadlift',
            'muscle_group': 'back',
            'sets': [
                {'reps': 5, 'weight_kg': 60, 'type': 'warmup'},
                {'reps': 5, 'weight_kg': 100, 'type': 'warmup'},
                {'reps': 5, 'weight_kg': 140, 'type': 'working'},
                {'reps': 3, 'weight_kg': 160, 'type': 'working'}
            ]
        }

        result = _parse_exercise(exercise_data)

        assert result['set_count'] == 4


class TestCalculateWorkoutTotals:
    """Tests for calculate_workout_totals function."""

    @pytest.mark.unit
    def test_calculates_daily_totals(self, parsed_workouts):
        """Should calculate totals for a specific date."""
        # Push Day is on 2026-01-25
        totals = calculate_workout_totals(parsed_workouts, '2026-01-25')

        assert totals['workout_count'] == 1
        assert totals['total_volume_kg'] > 0
        assert totals['total_sets'] > 0

    @pytest.mark.unit
    def test_returns_empty_for_no_workouts(self, parsed_workouts):
        """Should return empty dict when no workouts on date."""
        totals = calculate_workout_totals(parsed_workouts, '2026-01-01')

        assert totals == {}

    @pytest.mark.unit
    def test_aggregates_multiple_workouts(self):
        """Should aggregate multiple workouts on same day."""
        workouts = [
            {
                'date': '2026-01-25',
                'total_volume_kg': 1000,
                'total_sets': 10,
                'total_reps': 80,
                'duration_minutes': 45,
                'exercise_count': 3,
                'muscle_groups': ['chest', 'shoulders']
            },
            {
                'date': '2026-01-25',
                'total_volume_kg': 500,
                'total_sets': 5,
                'total_reps': 40,
                'duration_minutes': 30,
                'exercise_count': 2,
                'muscle_groups': ['arms']
            }
        ]

        totals = calculate_workout_totals(workouts, '2026-01-25')

        assert totals['workout_count'] == 2
        assert totals['total_volume_kg'] == 1500
        assert totals['total_sets'] == 15


class TestGetWorkoutRecords:
    """Tests for get_workout_records function."""

    @pytest.mark.unit
    def test_extracts_max_weights(self, parsed_workouts):
        """Should extract max weight for each exercise."""
        records = get_workout_records(parsed_workouts)

        assert 'Bench Press' in records
        assert records['Bench Press']['max_weight_kg'] == 85

    @pytest.mark.unit
    def test_tracks_record_dates(self, parsed_workouts):
        """Should track date of max weight."""
        records = get_workout_records(parsed_workouts)

        assert records['Bench Press']['max_weight_date'] == '2026-01-25'

    @pytest.mark.unit
    def test_counts_exercise_sessions(self, parsed_workouts):
        """Should count total sessions for each exercise."""
        records = get_workout_records(parsed_workouts)

        # Each exercise appears once in sample data
        assert records['Bench Press']['total_sessions'] == 1
        assert records['Squat']['total_sessions'] == 1


class TestGetMuscleGroupStats:
    """Tests for get_muscle_group_stats function."""

    @pytest.mark.unit
    def test_calculates_volume_distribution(self, parsed_workouts):
        """Should calculate volume by muscle group."""
        stats = get_muscle_group_stats(parsed_workouts, days=30)

        assert 'volume_distribution' in stats
        assert 'legs' in stats['volume_distribution']
        assert 'back' in stats['volume_distribution']
        assert 'chest' in stats['volume_distribution']

    @pytest.mark.unit
    def test_calculates_percentages(self, parsed_workouts):
        """Should calculate percentage of total volume."""
        stats = get_muscle_group_stats(parsed_workouts, days=30)

        assert 'volume_percentages' in stats
        total_pct = sum(stats['volume_percentages'].values())
        assert total_pct == pytest.approx(100, rel=0.1)

    @pytest.mark.unit
    def test_respects_date_range(self, parsed_workouts):
        """Should only include workouts within date range."""
        # With days=1, should only include most recent workout
        stats = get_muscle_group_stats(parsed_workouts, days=1)

        # Most recent is Leg Day (2026-01-29)
        assert stats['workout_count'] <= 1


class TestHelperFunctions:
    """Tests for helper functions."""

    @pytest.mark.unit
    def test_extract_date_iso_format(self):
        """Should extract date from ISO timestamp."""
        result = _extract_date('2026-01-25T10:00:00Z')
        assert result == '2026-01-25'

    @pytest.mark.unit
    def test_extract_date_with_timezone(self):
        """Should handle timezone in timestamp."""
        result = _extract_date('2026-01-25T10:00:00+00:00')
        assert result == '2026-01-25'

    @pytest.mark.unit
    def test_extract_date_empty_string(self):
        """Should return today for empty string."""
        result = _extract_date('')
        assert len(result) == 10  # YYYY-MM-DD format

    @pytest.mark.unit
    def test_calculate_duration(self):
        """Should calculate workout duration in minutes."""
        result = _calculate_duration(
            '2026-01-25T10:00:00Z',
            '2026-01-25T11:15:00Z'
        )
        assert result == 75

    @pytest.mark.unit
    def test_calculate_duration_empty(self):
        """Should return 0 for empty timestamps."""
        result = _calculate_duration('', '')
        assert result == 0


class TestGetWeeklySummary:
    """Tests for get_weekly_summary function."""

    @pytest.mark.unit
    def test_returns_weekly_summaries(self, parsed_workouts):
        """Should return list of weekly summaries."""
        summaries = get_weekly_summary(parsed_workouts, weeks=4)

        assert len(summaries) == 4
        assert all('week_start' in s for s in summaries)
        assert all('workout_count' in s for s in summaries)

    @pytest.mark.unit
    def test_calculates_weekly_totals(self, parsed_workouts):
        """Should calculate totals for each week."""
        summaries = get_weekly_summary(parsed_workouts, weeks=4)

        # Find week with workouts
        week_with_data = next((s for s in summaries if s['workout_count'] > 0), None)

        if week_with_data:
            assert week_with_data['total_volume_kg'] > 0
            assert week_with_data['total_sets'] > 0
