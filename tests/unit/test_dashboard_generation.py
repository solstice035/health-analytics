"""
Unit tests for dashboard data generation using TDD.
"""

import pytest
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_dashboard_data import (
    generate_heart_rate_distribution,
    generate_daily_trends,
    generate_summary_stats
)


class TestHeartRateDistribution:
    """Tests for heart rate zone distribution."""

    @pytest.mark.unit
    def test_distributes_hr_into_zones(self):
        """Should distribute HR readings into correct zones."""
        # Create sample data with HR stats
        data = {
            '2026-01-25': {
                'date': '2026-01-25',
                'totals': {},
                'readings': {},
                'hr_stats': {'avg': 75, 'min': 60, 'max': 140}  # Light zone
            },
            '2026-01-24': {
                'date': '2026-01-24',
                'totals': {},
                'readings': {},
                'hr_stats': {'avg': 120, 'min': 70, 'max': 160}  # Moderate zone
            }
        }

        result = generate_heart_rate_distribution(data, days=2)

        assert result is not None
        assert 'labels' in result
        assert 'values' in result
        assert len(result['labels']) == 5
        assert len(result['values']) == 5

    @pytest.mark.unit
    def test_hr_zone_labels(self):
        """Should have correct zone labels."""
        data = {
            '2026-01-25': {
                'hr_stats': {'avg': 75}
            }
        }

        result = generate_heart_rate_distribution(data)

        expected_labels = ['resting', 'light', 'moderate', 'vigorous', 'peak']
        assert result['labels'] == expected_labels

    @pytest.mark.unit
    def test_counts_days_in_each_zone(self):
        """Should count number of days in each zone."""
        data = {
            '2026-01-25': {'hr_stats': {'avg': 50}},   # resting
            '2026-01-24': {'hr_stats': {'avg': 75}},   # light
            '2026-01-23': {'hr_stats': {'avg': 120}},  # moderate
            '2026-01-22': {'hr_stats': {'avg': 150}},  # vigorous
            '2026-01-21': {'hr_stats': {'avg': 180}},  # peak
        }

        result = generate_heart_rate_distribution(data, days=5)

        # Each zone should have 1 day
        assert result['values'][0] == 1  # resting
        assert result['values'][1] == 1  # light
        assert result['values'][2] == 1  # moderate
        assert result['values'][3] == 1  # vigorous
        assert result['values'][4] == 1  # peak

    @pytest.mark.unit
    def test_handles_missing_hr_stats(self):
        """Should handle days without HR stats."""
        data = {
            '2026-01-25': {'hr_stats': {'avg': 75}},
            '2026-01-24': {},  # No HR stats
            '2026-01-23': {'hr_stats': None},
        }

        result = generate_heart_rate_distribution(data)

        # Should only count the one valid day
        assert sum(result['values']) == 1


class TestDailyTrends:
    """Tests for daily trends generation."""

    @pytest.mark.unit
    def test_generates_parallel_arrays(self):
        """Should generate parallel arrays for dates and metrics."""
        data = {
            '2026-01-25': {
                'totals': {
                    'steps': 10000,
                    'distance_km': 8.5,
                    'active_energy_kcal': 500,
                    'exercise_minutes': 30,
                    'stand_hours': 12
                },
                'readings': {
                    'resting_hr': 60,
                    'hrv_avg': 45
                }
            }
        }

        result = generate_daily_trends(data, days=1)

        assert 'dates' in result
        assert 'steps' in result
        assert 'distance' in result
        assert len(result['dates']) == 1
        assert len(result['steps']) == 1
        assert result['dates'][0] == '2026-01-25'
        assert result['steps'][0] == 10000


class TestSummaryStats:
    """Tests for summary statistics."""

    @pytest.mark.unit
    def test_calculates_period_totals(self):
        """Should calculate totals for the period."""
        data = {
            '2026-01-25': {
                'totals': {'steps': 10000, 'distance_km': 8.0},
                'readings': {}
            },
            '2026-01-24': {
                'totals': {'steps': 12000, 'distance_km': 10.0},
                'readings': {}
            }
        }

        result = generate_summary_stats(data, days=2)

        assert result['totals']['steps'] == 22000
        assert result['totals']['distance_km'] == 18.0

    @pytest.mark.unit
    def test_calculates_averages(self):
        """Should calculate daily averages."""
        data = {
            '2026-01-25': {
                'totals': {'steps': 10000},
                'readings': {}
            },
            '2026-01-24': {
                'totals': {'steps': 12000},
                'readings': {}
            }
        }

        result = generate_summary_stats(data, days=2)

        assert result['averages']['steps'] == 11000

    @pytest.mark.unit
    def test_tracks_goal_achievements(self):
        """Should track goal achievement counts."""
        data = {
            '2026-01-25': {'totals': {'steps': 11000}, 'readings': {}},  # Hit goal
            '2026-01-24': {'totals': {'steps': 8000}, 'readings': {}},   # Missed
            '2026-01-23': {'totals': {'steps': 15000}, 'readings': {}},  # Hit goal
        }

        result = generate_summary_stats(data, days=3)

        assert result['goals']['steps_10k']['achieved'] == 2
        assert result['goals']['steps_10k']['total'] == 3
