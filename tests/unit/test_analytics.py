"""
Tests for health analytics functions (health score, insights, personal records).

These tests use TDD to verify the analytics logic works correctly.
"""

import pytest
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_dashboard_data import (
    calculate_health_score,
    generate_insights,
    generate_personal_records
)


class TestHealthScoreCalculation:
    """Tests for health score calculation."""

    @pytest.mark.unit
    def test_calculates_maximum_score_for_excellent_metrics(self):
        """Should calculate high score for excellent health metrics."""
        stats = {
            'averages': {
                'steps': 15000,           # Well above 10k goal
                'exercise_minutes': 60,   # Double the 30min goal
                'stand_hours': 14,        # Above 12hr goal
                'resting_hr': 55,         # Athletic range
                'hrv': 55                 # Excellent HRV
            }
        }

        result = calculate_health_score(stats)

        assert result['score'] >= 90
        assert result['level'] == 'excellent'
        assert 'breakdown' in result
        assert result['max_score'] == 100

    @pytest.mark.unit
    def test_calculates_lower_score_for_sedentary_lifestyle(self):
        """Should calculate lower score for sedentary lifestyle."""
        stats = {
            'averages': {
                'steps': 3000,            # Way below goal
                'exercise_minutes': 10,   # Below goal
                'stand_hours': 6,         # Half the goal
                'resting_hr': 85,         # Elevated
                'hrv': 20                 # Low
            }
        }

        result = calculate_health_score(stats)

        assert result['score'] < 50
        assert result['level'] in ['moderate', 'needs_work']

    @pytest.mark.unit
    def test_handles_missing_metrics_gracefully(self):
        """Should handle missing metrics without crashing."""
        stats = {
            'averages': {
                'steps': 10000
                # All other metrics missing
            }
        }

        result = calculate_health_score(stats)

        assert 0 <= result['score'] <= 100
        assert result['breakdown']['steps'] > 0

    @pytest.mark.unit
    def test_handles_empty_averages(self):
        """Should handle empty averages dict."""
        stats = {'averages': {}}

        result = calculate_health_score(stats)

        assert result['score'] == 0
        assert result['level'] == 'needs_work'

    @pytest.mark.unit
    def test_handles_zero_values(self):
        """Should handle zero metric values."""
        stats = {
            'averages': {
                'steps': 0,
                'exercise_minutes': 0,
                'stand_hours': 0,
                'resting_hr': 0,
                'hrv': 0
            }
        }

        result = calculate_health_score(stats)

        assert result['score'] == 0

    @pytest.mark.unit
    def test_caps_score_at_100(self):
        """Should cap score at 100 even with exceptional metrics."""
        stats = {
            'averages': {
                'steps': 25000,           # 250% of goal
                'exercise_minutes': 120,  # 400% of goal
                'stand_hours': 18,        # 150% of goal
                'resting_hr': 45,         # Very athletic
                'hrv': 80                 # Exceptional
            }
        }

        result = calculate_health_score(stats)

        assert result['score'] <= 100
        assert result['max_score'] == 100

    @pytest.mark.unit
    def test_breakdown_contains_all_scored_components(self):
        """Should include all scored components in breakdown."""
        stats = {
            'averages': {
                'steps': 10000,
                'exercise_minutes': 30,
                'stand_hours': 12,
                'resting_hr': 60,
                'hrv': 40
            }
        }

        result = calculate_health_score(stats)

        assert 'steps' in result['breakdown']
        assert 'exercise' in result['breakdown']
        assert 'stand' in result['breakdown']
        assert 'resting_hr' in result['breakdown']
        assert 'hrv' in result['breakdown']


class TestInsightGeneration:
    """Tests for AI insight generation."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample health data for 14 days."""
        data = {}
        for i in range(14):
            date = f"2026-01-{(12 + i):02d}"
            data[date] = {
                'totals': {
                    'steps': 10000 + (i * 500),  # Increasing trend
                    'exercise_minutes': 35,
                    'distance_km': 8.0
                },
                'readings': {
                    'resting_hr': 58,
                    'hrv_avg': 45
                }
            }
        return data

    @pytest.fixture
    def sample_stats(self):
        """Generate sample summary stats."""
        return {
            'averages': {
                'steps': 12000,
                'exercise_minutes': 35,
                'stand_hours': 13,
                'resting_hr': 58,
                'hrv': 45
            },
            'goals': {
                'steps_10k': {'achieved': 6, 'total': 7},
                'exercise_30m': {'achieved': 7, 'total': 7},
                'stand_12h': {'achieved': 5, 'total': 7}
            }
        }

    @pytest.mark.unit
    def test_generates_positive_insight_for_exercise_champion(self, sample_data, sample_stats):
        """Should generate positive insight when exercise goal hit every day."""
        insights = generate_insights(sample_data, sample_stats)

        # Find exercise champion insight
        exercise_insights = [i for i in insights if 'Exercise' in i.get('title', '')]

        assert len(exercise_insights) == 1
        assert exercise_insights[0]['type'] == 'positive'

    @pytest.mark.unit
    def test_generates_insight_for_athletic_hr(self, sample_data, sample_stats):
        """Should generate insight for athletic resting heart rate."""
        # Set resting HR below 60
        sample_stats['averages']['resting_hr'] = 55

        insights = generate_insights(sample_data, sample_stats)

        hr_insights = [i for i in insights if 'Heart Rate' in i.get('title', '')]
        assert len(hr_insights) == 1
        assert hr_insights[0]['type'] == 'positive'

    @pytest.mark.unit
    def test_limits_insights_to_four(self, sample_data, sample_stats):
        """Should return maximum of 4 insights."""
        insights = generate_insights(sample_data, sample_stats)

        assert len(insights) <= 4

    @pytest.mark.unit
    def test_returns_default_insight_with_minimal_data(self):
        """Should return default insight when not enough data."""
        data = {
            '2026-01-25': {
                'totals': {'steps': 10000},
                'readings': {}
            }
        }
        stats = {'averages': {'steps': 10000}, 'goals': {}}

        insights = generate_insights(data, stats)

        assert len(insights) >= 1
        assert insights[0]['type'] == 'neutral'

    @pytest.mark.unit
    def test_insight_structure(self, sample_data, sample_stats):
        """Should return insights with correct structure."""
        insights = generate_insights(sample_data, sample_stats)

        for insight in insights:
            assert 'type' in insight
            assert 'icon' in insight
            assert 'title' in insight
            assert 'text' in insight
            assert insight['type'] in ['positive', 'warning', 'neutral']


class TestPersonalRecords:
    """Tests for personal records tracking."""

    @pytest.fixture
    def sample_data_with_records(self):
        """Generate sample data with clear records."""
        return {
            '2026-01-25': {
                'totals': {'steps': 20000, 'distance_km': 15.0, 'exercise_minutes': 90},
                'readings': {'resting_hr': 52, 'hrv_avg': 55}
            },
            '2026-01-24': {
                'totals': {'steps': 10000, 'distance_km': 8.0, 'exercise_minutes': 30},
                'readings': {'resting_hr': 58, 'hrv_avg': 45}
            },
            '2026-01-23': {
                'totals': {'steps': 8000, 'distance_km': 6.0, 'exercise_minutes': 25},
                'readings': {'resting_hr': 60, 'hrv_avg': 40}
            }
        }

    @pytest.mark.unit
    def test_tracks_max_steps(self, sample_data_with_records):
        """Should track maximum steps record."""
        records = generate_personal_records(sample_data_with_records)

        assert records['max_steps']['value'] == 20000
        assert records['max_steps']['date'] == '2026-01-25'

    @pytest.mark.unit
    def test_tracks_max_distance(self, sample_data_with_records):
        """Should track maximum distance record."""
        records = generate_personal_records(sample_data_with_records)

        assert records['max_distance']['value'] == 15.0
        assert records['max_distance']['date'] == '2026-01-25'

    @pytest.mark.unit
    def test_tracks_max_exercise(self, sample_data_with_records):
        """Should track maximum exercise record."""
        records = generate_personal_records(sample_data_with_records)

        assert records['max_exercise']['value'] == 90
        assert records['max_exercise']['date'] == '2026-01-25'

    @pytest.mark.unit
    def test_tracks_lowest_resting_hr(self, sample_data_with_records):
        """Should track lowest resting heart rate record."""
        records = generate_personal_records(sample_data_with_records)

        assert records['lowest_resting_hr']['value'] == 52
        assert records['lowest_resting_hr']['date'] == '2026-01-25'

    @pytest.mark.unit
    def test_tracks_highest_hrv(self, sample_data_with_records):
        """Should track highest HRV record."""
        records = generate_personal_records(sample_data_with_records)

        assert records['highest_hrv']['value'] == 55
        assert records['highest_hrv']['date'] == '2026-01-25'

    @pytest.mark.unit
    def test_handles_empty_data(self):
        """Should handle empty data gracefully."""
        records = generate_personal_records({})

        assert records['max_steps']['value'] == 0
        assert records['max_steps']['date'] is None

    @pytest.mark.unit
    def test_handles_missing_metrics(self):
        """Should handle missing metrics in data."""
        data = {
            '2026-01-25': {
                'totals': {'steps': 10000},  # Missing other totals
                'readings': {}  # Missing readings
            }
        }

        records = generate_personal_records(data)

        assert records['max_steps']['value'] == 10000
        assert records['max_distance']['value'] == 0
        assert records['lowest_resting_hr']['value'] == 0
