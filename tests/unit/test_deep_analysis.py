"""
Tests for deep health analytics functions.

These tests verify the deep analysis module works correctly:
- Data loading and aggregation
- Fitness trajectory calculation
- Weekly/monthly pattern analysis
- Correlation detection
- Streak tracking
- Personal records
- Anomaly detection
- Insight generation
"""

import pytest
from pathlib import Path
import sys
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from deep_analysis import (
    calculate_daily_stats,
    analyze_fitness_trajectory,
    analyze_weekly_patterns,
    analyze_monthly_progression,
    find_correlations,
    find_streaks,
    find_personal_records,
    detect_anomalies,
    compare_recent_to_previous,
    generate_health_report,
    generate_actionable_insights
)


class TestCalculateDailyStats:
    """Tests for daily statistics calculation."""

    @pytest.mark.unit
    def test_aggregates_step_count(self):
        """Should sum all step counts for a day."""
        daily_data = {
            '2026-01-25': {
                'step_count': [100, 200, 300, 400]
            }
        }

        result = calculate_daily_stats(daily_data)

        assert result['2026-01-25']['steps'] == 1000

    @pytest.mark.unit
    def test_calculates_heart_rate_averages(self):
        """Should calculate HR min, avg, max."""
        daily_data = {
            '2026-01-25': {
                'heart_rate': [60, 70, 80, 90, 100]
            }
        }

        result = calculate_daily_stats(daily_data)

        assert result['2026-01-25']['hr_avg'] == 80
        assert result['2026-01-25']['hr_min'] == 60
        assert result['2026-01-25']['hr_max'] == 100

    @pytest.mark.unit
    def test_extracts_resting_hr(self):
        """Should use first resting HR reading."""
        daily_data = {
            '2026-01-25': {
                'resting_heart_rate': [58, 60]
            }
        }

        result = calculate_daily_stats(daily_data)

        assert result['2026-01-25']['resting_hr'] == 58

    @pytest.mark.unit
    def test_calculates_hrv_average(self):
        """Should average HRV readings."""
        daily_data = {
            '2026-01-25': {
                'heart_rate_variability': [30, 40, 50]
            }
        }

        result = calculate_daily_stats(daily_data)

        assert result['2026-01-25']['hrv_avg'] == 40

    @pytest.mark.unit
    def test_handles_empty_data(self):
        """Should handle empty metrics."""
        daily_data = {
            '2026-01-25': {}
        }

        result = calculate_daily_stats(daily_data)

        assert result['2026-01-25']['steps'] == 0

    @pytest.mark.unit
    def test_aggregates_swimming_data(self):
        """Should sum swimming distance and strokes."""
        daily_data = {
            '2026-01-25': {
                'swimming_distance': [100, 200, 300],
                'swimming_stroke_count': [50, 100, 150]
            }
        }

        result = calculate_daily_stats(daily_data)

        assert result['2026-01-25']['swim_distance'] == 600
        assert result['2026-01-25']['swim_strokes'] == 300


class TestFitnessTrajectory:
    """Tests for fitness trajectory analysis."""

    @pytest.fixture
    def improving_stats(self):
        """Generate stats showing improvement over time."""
        stats = {}
        for i in range(90):
            date = f"2025-{10 + i // 30:02d}-{(i % 30) + 1:02d}"
            # VO2 improving from 35 to 40
            stats[date] = {
                'vo2_max': 35 + (i * 0.05),
                'resting_hr': 65 - (i * 0.1),  # RHR decreasing
                'hrv_avg': 30 + (i * 0.15)  # HRV increasing
            }
        return stats

    @pytest.mark.unit
    def test_detects_vo2_improvement(self, improving_stats):
        """Should detect VO2 max improvement."""
        result = analyze_fitness_trajectory(improving_stats)

        assert result['vo2_max']['improving'] is True
        assert result['vo2_max']['change'] > 0

    @pytest.mark.unit
    def test_detects_rhr_improvement(self, improving_stats):
        """Should detect resting HR improvement (lower)."""
        result = analyze_fitness_trajectory(improving_stats)

        assert result['resting_hr']['change'] < 0

    @pytest.mark.unit
    def test_detects_hrv_improvement(self, improving_stats):
        """Should detect HRV improvement (higher)."""
        result = analyze_fitness_trajectory(improving_stats)

        assert result['hrv']['change'] > 0

    @pytest.mark.unit
    def test_handles_missing_metrics(self):
        """Should handle missing metrics gracefully."""
        stats = {
            '2025-10-01': {'steps': 10000},
            '2025-10-02': {'steps': 11000}
        }

        result = analyze_fitness_trajectory(stats)

        assert 'vo2_max' not in result
        assert 'resting_hr' not in result


class TestWeeklyPatterns:
    """Tests for weekly pattern analysis."""

    @pytest.fixture
    def week_data(self):
        """Generate one week of data."""
        # Jan 5 2026 is Monday
        return {
            '2026-01-05': {'steps': 8000, 'exercise_min': 30},   # Mon
            '2026-01-06': {'steps': 12000, 'exercise_min': 60},  # Tue
            '2026-01-07': {'steps': 10000, 'exercise_min': 45},  # Wed
            '2026-01-08': {'steps': 11000, 'exercise_min': 50},  # Thu
            '2026-01-09': {'steps': 9000, 'exercise_min': 35},   # Fri
            '2026-01-10': {'steps': 15000, 'exercise_min': 90},  # Sat
            '2026-01-11': {'steps': 14000, 'exercise_min': 80},  # Sun
        }

    @pytest.mark.unit
    def test_calculates_day_averages(self, week_data):
        """Should calculate averages per day of week."""
        result = analyze_weekly_patterns(week_data)

        assert 'Mon' in result
        assert 'Sat' in result
        assert result['Mon']['steps'] == 8000
        assert result['Sat']['steps'] == 15000

    @pytest.mark.unit
    def test_all_days_present(self, week_data):
        """Should have all seven days."""
        result = analyze_weekly_patterns(week_data)

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in days:
            assert day in result


class TestMonthlyProgression:
    """Tests for monthly progression analysis."""

    @pytest.mark.unit
    def test_groups_by_month(self):
        """Should group stats by month."""
        stats = {
            '2025-10-01': {'steps': 10000, 'exercise_min': 30},
            '2025-10-15': {'steps': 12000, 'exercise_min': 45},
            '2025-11-01': {'steps': 11000, 'exercise_min': 40},
            '2025-11-15': {'steps': 13000, 'exercise_min': 60},
        }

        result = analyze_monthly_progression(stats)

        assert len(result) == 2
        assert result[0]['month'] == '2025-10'
        assert result[1]['month'] == '2025-11'

    @pytest.mark.unit
    def test_calculates_monthly_averages(self):
        """Should average metrics per month."""
        stats = {
            '2025-10-01': {'steps': 10000},
            '2025-10-02': {'steps': 14000},
        }

        result = analyze_monthly_progression(stats)

        assert result[0]['steps'] == 12000


class TestFindStreaks:
    """Tests for streak detection."""

    @pytest.mark.unit
    def test_finds_step_streak(self):
        """Should find longest 10K step streak."""
        stats = {
            '2025-10-01': {'steps': 10000},
            '2025-10-02': {'steps': 11000},
            '2025-10-03': {'steps': 12000},
            '2025-10-04': {'steps': 5000},  # Break
            '2025-10-05': {'steps': 10000},
        }

        result = find_streaks(stats)

        assert result['longest_step_streak'] == 3
        assert result['longest_streak_end'] == '2025-10-03'

    @pytest.mark.unit
    def test_calculates_exercise_consistency(self):
        """Should calculate exercise consistency percentage."""
        stats = {
            '2025-10-01': {'exercise_min': 30},
            '2025-10-02': {'exercise_min': 45},
            '2025-10-03': {'exercise_min': 10},  # Below 30
            '2025-10-04': {'exercise_min': 60},
        }

        result = find_streaks(stats)

        assert result['exercise_days'] == 3
        assert result['total_days'] == 4
        assert result['exercise_consistency'] == 0.75

    @pytest.mark.unit
    def test_current_streak(self):
        """Should track current ongoing streak."""
        stats = {
            '2025-10-01': {'steps': 5000},  # Break earlier
            '2025-10-02': {'steps': 10000},
            '2025-10-03': {'steps': 11000},
            '2025-10-04': {'steps': 12000},
        }

        result = find_streaks(stats)

        assert result['current_streak'] == 3


class TestPersonalRecords:
    """Tests for personal records tracking."""

    @pytest.fixture
    def sample_stats(self):
        """Generate sample stats with clear records."""
        return {
            '2025-10-01': {
                'steps': 15000,
                'exercise_min': 60,
                'resting_hr': 55,
                'hrv_avg': 45,
                'hr_max': 150
            },
            '2025-10-02': {
                'steps': 20000,  # Record
                'exercise_min': 90,  # Record
                'resting_hr': 50,  # Record (lowest)
                'hrv_avg': 60,  # Record (highest)
                'hr_max': 160  # Record
            },
            '2025-10-03': {
                'steps': 10000,
                'exercise_min': 30,
                'resting_hr': 58,
                'hrv_avg': 40,
                'hr_max': 140
            }
        }

    @pytest.mark.unit
    def test_finds_max_steps(self, sample_stats):
        """Should find maximum steps record."""
        result = find_personal_records(sample_stats)

        assert result['max_steps']['value'] == 20000
        assert result['max_steps']['date'] == '2025-10-02'

    @pytest.mark.unit
    def test_finds_lowest_resting_hr(self, sample_stats):
        """Should find lowest resting HR (best)."""
        result = find_personal_records(sample_stats)

        assert result['lowest_resting_hr']['value'] == 50
        assert result['lowest_resting_hr']['date'] == '2025-10-02'

    @pytest.mark.unit
    def test_finds_highest_hrv(self, sample_stats):
        """Should find highest HRV (best)."""
        result = find_personal_records(sample_stats)

        assert result['highest_hrv']['value'] == 60
        assert result['highest_hrv']['date'] == '2025-10-02'


class TestAnomalyDetection:
    """Tests for anomaly detection."""

    @pytest.mark.unit
    def test_detects_low_hrv_days(self):
        """Should flag unusually low HRV days."""
        stats = {}
        # Normal days
        for i in range(20):
            stats[f'2025-10-{i+1:02d}'] = {'hrv_avg': 40}
        # Anomaly day
        stats['2025-10-21'] = {'hrv_avg': 15}

        result = detect_anomalies(stats)

        assert 'low_hrv_days' in result
        low_days = [d for d, v in result['low_hrv_days']]
        assert '2025-10-21' in low_days

    @pytest.mark.unit
    def test_detects_high_intensity_days(self):
        """Should flag high intensity workout days."""
        stats = {}
        # Normal days
        for i in range(20):
            stats[f'2025-10-{i+1:02d}'] = {'hr_max': 140}
        # High intensity day
        stats['2025-10-21'] = {'hr_max': 180}

        result = detect_anomalies(stats)

        assert 'high_intensity_days' in result
        high_days = [d for d, v in result['high_intensity_days']]
        assert '2025-10-21' in high_days


class TestTrendComparison:
    """Tests for recent vs previous comparison."""

    @pytest.mark.unit
    def test_compares_periods(self):
        """Should compare recent 30 days to previous 30."""
        stats = {}
        # Previous 30 days - lower activity
        for i in range(30):
            stats[f'2025-10-{i+1:02d}'] = {'steps': 8000, 'exercise_min': 30}
        # Recent 30 days - higher activity
        for i in range(30):
            stats[f'2025-11-{i+1:02d}'] = {'steps': 12000, 'exercise_min': 60}

        result = compare_recent_to_previous(stats, days=30)

        assert result['steps']['recent_avg'] == 12000
        assert result['steps']['previous_avg'] == 8000
        assert result['steps']['pct_change'] == 50.0

    @pytest.mark.unit
    def test_handles_insufficient_data(self):
        """Should return empty if not enough data."""
        stats = {
            '2025-10-01': {'steps': 10000}
        }

        result = compare_recent_to_previous(stats, days=30)

        assert result == {}


class TestHealthReport:
    """Tests for full health report generation."""

    @pytest.fixture
    def comprehensive_stats(self):
        """Generate comprehensive sample data."""
        stats = {}
        for i in range(90):
            date = f"2025-{10 + i // 30:02d}-{(i % 30) + 1:02d}"
            stats[date] = {
                'steps': 10000 + (i * 100),
                'exercise_min': 30 + (i % 30),
                'resting_hr': 60 - (i * 0.1),
                'hrv_avg': 35 + (i * 0.1),
                'vo2_max': 38 + (i * 0.02),
                'hr_max': 140 + (i % 20)
            }
        return stats

    @pytest.mark.unit
    def test_generates_complete_report(self, comprehensive_stats):
        """Should generate report with all sections."""
        report = generate_health_report(comprehensive_stats)

        assert 'overview' in report
        assert 'fitness_trajectory' in report
        assert 'weekly_patterns' in report
        assert 'monthly_progression' in report
        assert 'correlations' in report
        assert 'streaks' in report
        assert 'personal_records' in report
        assert 'anomalies' in report
        assert 'recent_vs_previous' in report

    @pytest.mark.unit
    def test_overview_contains_date_range(self, comprehensive_stats):
        """Should include date range in overview."""
        report = generate_health_report(comprehensive_stats)

        assert report['overview']['total_days'] == 90
        assert 'start' in report['overview']['date_range']
        assert 'end' in report['overview']['date_range']


class TestInsightGeneration:
    """Tests for actionable insight generation."""

    @pytest.mark.unit
    def test_generates_vo2_insight_when_improving(self):
        """Should generate positive insight for VO2 improvement."""
        report = {
            'overview': {'date_range': {'end': '2025-12-01'}},
            'fitness_trajectory': {
                'vo2_max': {'improving': True, 'change': 2.5}
            },
            'streaks': {'current_streak': 3, 'longest_step_streak': 10, 'exercise_consistency': 0.5},
            'anomalies': {},
            'recent_vs_previous': {},
            'correlations': {}
        }

        insights = generate_actionable_insights(report)

        vo2_insights = [i for i in insights if 'VO2' in i['title']]
        assert len(vo2_insights) == 1
        assert vo2_insights[0]['type'] == 'positive'

    @pytest.mark.unit
    def test_generates_streak_insight(self):
        """Should generate insight for active streaks."""
        report = {
            'overview': {'date_range': {'end': '2025-12-01'}},
            'fitness_trajectory': {},
            'streaks': {
                'current_streak': 14,
                'longest_step_streak': 20,
                'exercise_consistency': 0.5
            },
            'anomalies': {},
            'recent_vs_previous': {},
            'correlations': {}
        }

        insights = generate_actionable_insights(report)

        streak_insights = [i for i in insights if 'Streak' in i['title']]
        assert len(streak_insights) == 1
        assert '14' in streak_insights[0]['title']

    @pytest.mark.unit
    def test_limits_insights_count(self):
        """Should return maximum 6 insights."""
        report = {
            'overview': {'date_range': {'end': '2025-12-01'}},
            'fitness_trajectory': {
                'vo2_max': {'improving': True, 'change': 2},
                'resting_hr': {'improving': True, 'change': -3},
                'hrv': {'improving': True, 'change': 10}
            },
            'streaks': {
                'current_streak': 14,
                'longest_step_streak': 20,
                'exercise_consistency': 0.8
            },
            'anomalies': {'low_hrv_days': [('2025-11-30', 20)]},
            'recent_vs_previous': {
                'exercise_min': {'pct_change': 30},
                'resting_hr': {'pct_change': 10}
            },
            'correlations': {
                'steps_to_hrv': {
                    'low_steps_hrv': 35,
                    'medium_steps_hrv': 38,
                    'high_steps_hrv': 42
                }
            }
        }

        insights = generate_actionable_insights(report)

        assert len(insights) <= 6

    @pytest.mark.unit
    def test_insight_structure(self):
        """Should return insights with correct structure."""
        report = {
            'overview': {'date_range': {'end': '2025-12-01'}},
            'fitness_trajectory': {'vo2_max': {'improving': True, 'change': 2}},
            'streaks': {'current_streak': 3, 'longest_step_streak': 10, 'exercise_consistency': 0.5},
            'anomalies': {},
            'recent_vs_previous': {},
            'correlations': {}
        }

        insights = generate_actionable_insights(report)

        for insight in insights:
            assert 'type' in insight
            assert 'icon' in insight
            assert 'title' in insight
            assert 'text' in insight
            assert insight['type'] in ['positive', 'warning', 'neutral']
