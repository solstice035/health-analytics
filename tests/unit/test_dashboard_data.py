"""Tests for generate_dashboard_data.py"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_dashboard_data import (
    load_date_range,
    generate_daily_trends,
    generate_weekly_comparison,
    generate_goals_progress,
    generate_summary_stats,
    generate_heart_rate_distribution,
    calculate_health_score,
    generate_insights,
    generate_personal_records,
    main
)


@pytest.fixture
def sample_day_data():
    """Sample data for a single day."""
    return {
        'date': '2026-01-20',
        'totals': {
            'steps': 10000,
            'distance_km': 7.5,
            'active_energy_kcal': 500,
            'exercise_minutes': 45,
            'stand_hours': 12
        },
        'readings': {
            'resting_hr': 58,
            'hrv_avg': 52,
            'vo2_max': 42.5
        },
        'hr_stats': {
            'count': 100,
            'min': 55,
            'max': 145,
            'avg': 72
        }
    }


@pytest.fixture
def week_data(sample_day_data):
    """Sample data for a week."""
    data = {}
    for i in range(7):
        date = f"2026-01-{14+i:02d}"
        day = sample_day_data.copy()
        day['date'] = date
        day['totals'] = sample_day_data['totals'].copy()
        day['totals']['steps'] = 8000 + i * 1000  # Varying steps
        day['readings'] = sample_day_data['readings'].copy()
        day['hr_stats'] = sample_day_data['hr_stats'].copy()
        data[date] = day
    return data


class TestLoadDateRange:
    """Tests for load_date_range function."""

    @pytest.mark.unit
    def test_returns_empty_dict_for_no_files(self, tmp_path):
        """Should return empty dict when no files found."""
        with patch('generate_dashboard_data.HEALTH_DATA_PATH', tmp_path):
            result = load_date_range("2026-01-15", "2026-01-20")

        assert result == {}

    @pytest.mark.unit
    def test_loads_existing_files(self, tmp_path):
        """Should load data from existing files."""
        file_path = tmp_path / "HealthAutoExport-2026-01-20.json"
        file_path.write_text('{}')

        mock_raw = {'data': {'metrics': [
            {'name': 'step_count', 'units': 'count', 'data': [{'qty': 1000}]}
        ]}}

        with patch('generate_dashboard_data.HEALTH_DATA_PATH', tmp_path):
            with patch('generate_dashboard_data.read_json_safe', return_value=mock_raw):
                with patch('generate_dashboard_data.extract_all_metrics') as mock_extract:
                    mock_extract.return_value = {'step_count': {'data': [{'qty': 1000}]}}
                    with patch('generate_dashboard_data.calculate_totals', return_value={'steps': 1000}):
                        with patch('generate_dashboard_data.get_key_readings', return_value={}):
                            with patch('generate_dashboard_data.get_heart_rate_stats', return_value=None):
                                result = load_date_range("2026-01-20", "2026-01-20")

        assert "2026-01-20" in result

    @pytest.mark.unit
    def test_accepts_string_dates(self, tmp_path):
        """Should accept string date format."""
        with patch('generate_dashboard_data.HEALTH_DATA_PATH', tmp_path):
            result = load_date_range("2026-01-15", "2026-01-16")

        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_accepts_datetime_dates(self, tmp_path):
        """Should accept datetime objects."""
        start = datetime(2026, 1, 15)
        end = datetime(2026, 1, 16)

        with patch('generate_dashboard_data.HEALTH_DATA_PATH', tmp_path):
            result = load_date_range(start, end)

        assert isinstance(result, dict)


class TestGenerateDailyTrends:
    """Tests for generate_daily_trends function."""

    @pytest.mark.unit
    def test_returns_trend_structure(self, week_data):
        """Should return correct trend structure."""
        result = generate_daily_trends(week_data, days=7)

        assert 'dates' in result
        assert 'steps' in result
        assert 'distance' in result
        assert 'active_energy' in result
        assert 'exercise_minutes' in result

    @pytest.mark.unit
    def test_limits_to_specified_days(self, week_data):
        """Should limit results to specified number of days."""
        result = generate_daily_trends(week_data, days=3)

        assert len(result['dates']) == 3

    @pytest.mark.unit
    def test_extracts_correct_values(self, week_data):
        """Should extract correct values from data."""
        result = generate_daily_trends(week_data, days=7)

        # First day should have steps 8000
        assert result['steps'][0] == 8000
        # Last day should have steps 14000
        assert result['steps'][-1] == 14000

    @pytest.mark.unit
    def test_handles_missing_values(self):
        """Should handle missing metric values."""
        data = {
            '2026-01-20': {
                'totals': {},
                'readings': {}
            }
        }

        result = generate_daily_trends(data, days=1)

        assert result['steps'][0] == 0
        assert result['resting_hr'][0] == 0


class TestGenerateWeeklyComparison:
    """Tests for generate_weekly_comparison function."""

    @pytest.mark.unit
    def test_returns_weekly_structure(self, week_data):
        """Should return correct weekly structure."""
        result = generate_weekly_comparison(week_data)

        assert 'weeks' in result
        assert 'avg_steps' in result
        assert 'avg_distance' in result
        assert 'avg_energy' in result
        assert 'avg_exercise' in result

    @pytest.mark.unit
    def test_calculates_weekly_averages(self, week_data):
        """Should calculate weekly averages correctly."""
        result = generate_weekly_comparison(week_data)

        # Should have at least one week
        assert len(result['weeks']) >= 1
        assert len(result['avg_steps']) >= 1

    @pytest.mark.unit
    def test_limits_to_12_weeks(self):
        """Should limit to last 12 weeks."""
        # Create 15 weeks of data
        data = {}
        for week in range(15):
            for day in range(7):
                date = datetime(2026, 1, 1) + timedelta(weeks=week, days=day)
                date_str = date.strftime("%Y-%m-%d")
                data[date_str] = {
                    'totals': {'steps': 10000},
                    'readings': {}
                }

        result = generate_weekly_comparison(data)

        assert len(result['weeks']) <= 12


class TestGenerateGoalsProgress:
    """Tests for generate_goals_progress function."""

    @pytest.mark.unit
    def test_returns_goal_structure(self, week_data):
        """Should return correct goal structure."""
        result = generate_goals_progress(week_data, days=7)

        assert 'dates' in result
        assert 'steps_goal' in result
        assert 'stand_goal' in result
        assert 'exercise_goal' in result

    @pytest.mark.unit
    def test_marks_achieved_goals(self):
        """Should mark 1 for achieved goals."""
        data = {
            '2026-01-20': {
                'totals': {
                    'steps': 12000,     # Over 10k goal
                    'stand_hours': 14,  # Over 12 goal
                    'exercise_minutes': 45  # Over 30 goal
                },
                'readings': {}
            }
        }

        result = generate_goals_progress(data, days=1)

        assert result['steps_goal'][0] == 1
        assert result['stand_goal'][0] == 1
        assert result['exercise_goal'][0] == 1

    @pytest.mark.unit
    def test_marks_missed_goals(self):
        """Should mark 0 for missed goals."""
        data = {
            '2026-01-20': {
                'totals': {
                    'steps': 5000,       # Under 10k
                    'stand_hours': 8,    # Under 12
                    'exercise_minutes': 20  # Under 30
                },
                'readings': {}
            }
        }

        result = generate_goals_progress(data, days=1)

        assert result['steps_goal'][0] == 0
        assert result['stand_goal'][0] == 0
        assert result['exercise_goal'][0] == 0


class TestGenerateSummaryStats:
    """Tests for generate_summary_stats function."""

    @pytest.mark.unit
    def test_returns_summary_structure(self, week_data):
        """Should return correct summary structure."""
        result = generate_summary_stats(week_data, days=7)

        assert 'period' in result
        assert 'days_count' in result
        assert 'totals' in result
        assert 'averages' in result
        assert 'goals' in result

    @pytest.mark.unit
    def test_calculates_totals(self, week_data):
        """Should calculate totals correctly."""
        result = generate_summary_stats(week_data, days=7)

        assert result['totals']['steps'] > 0
        assert result['totals']['distance_km'] > 0

    @pytest.mark.unit
    def test_calculates_averages(self, week_data):
        """Should calculate averages correctly."""
        result = generate_summary_stats(week_data, days=7)

        # Average steps should be sum/7
        expected_avg = (8000+9000+10000+11000+12000+13000+14000) // 7
        assert result['averages']['steps'] == expected_avg

    @pytest.mark.unit
    def test_tracks_goal_achievements(self, week_data):
        """Should track goal achievement counts."""
        result = generate_summary_stats(week_data, days=7)

        assert 'steps_10k' in result['goals']
        assert 'achieved' in result['goals']['steps_10k']
        assert 'total' in result['goals']['steps_10k']


class TestGenerateHeartRateDistribution:
    """Tests for generate_heart_rate_distribution function."""

    @pytest.mark.unit
    def test_returns_distribution_structure(self, week_data):
        """Should return correct distribution structure."""
        result = generate_heart_rate_distribution(week_data, days=7)

        assert 'labels' in result
        assert 'values' in result

    @pytest.mark.unit
    def test_has_all_zones(self, week_data):
        """Should have all heart rate zones."""
        result = generate_heart_rate_distribution(week_data, days=7)

        expected_zones = ['resting', 'light', 'moderate', 'vigorous', 'peak']
        assert result['labels'] == expected_zones

    @pytest.mark.unit
    def test_handles_no_hr_data(self):
        """Should handle missing heart rate data."""
        data = {
            '2026-01-20': {
                'totals': {},
                'readings': {},
                'hr_stats': None
            }
        }

        result = generate_heart_rate_distribution(data, days=1)

        assert result['values'] == [0, 0, 0, 0, 0]


class TestCalculateHealthScore:
    """Tests for calculate_health_score function."""

    @pytest.mark.unit
    def test_returns_score_structure(self):
        """Should return correct score structure."""
        stats = {
            'averages': {
                'steps': 10000,
                'exercise_minutes': 30,
                'stand_hours': 12,
                'resting_hr': 58,
                'hrv': 50
            }
        }

        result = calculate_health_score(stats)

        assert 'score' in result
        assert 'description' in result
        assert 'level' in result
        assert 'breakdown' in result

    @pytest.mark.unit
    def test_excellent_score(self):
        """Should give excellent score for great metrics."""
        stats = {
            'averages': {
                'steps': 12000,
                'exercise_minutes': 45,
                'stand_hours': 12,
                'resting_hr': 55,
                'hrv': 55
            }
        }

        result = calculate_health_score(stats)

        assert result['score'] >= 85
        assert result['level'] == 'excellent'

    @pytest.mark.unit
    def test_needs_work_score(self):
        """Should give low score for poor metrics."""
        stats = {
            'averages': {
                'steps': 3000,
                'exercise_minutes': 10,
                'stand_hours': 6,
                'resting_hr': 85,
                'hrv': 20
            }
        }

        result = calculate_health_score(stats)

        assert result['score'] < 55
        assert result['level'] == 'needs_work'

    @pytest.mark.unit
    def test_handles_missing_metrics(self):
        """Should handle missing metrics gracefully."""
        stats = {'averages': {}}

        result = calculate_health_score(stats)

        assert result['score'] == 0

    @pytest.mark.unit
    def test_resting_hr_scoring_brackets(self):
        """Should score resting HR in correct brackets."""
        # Excellent HR <= 60
        stats = {'averages': {'resting_hr': 58}}
        result = calculate_health_score(stats)
        assert result['breakdown']['resting_hr'] == 15  # Full points

        # Good HR 61-70
        stats = {'averages': {'resting_hr': 65}}
        result = calculate_health_score(stats)
        assert result['breakdown']['resting_hr'] == 12  # 80%

        # Moderate HR 71-80
        stats = {'averages': {'resting_hr': 75}}
        result = calculate_health_score(stats)
        assert result['breakdown']['resting_hr'] == 9  # 60%

        # Poor HR > 80
        stats = {'averages': {'resting_hr': 85}}
        result = calculate_health_score(stats)
        assert result['breakdown']['resting_hr'] == 6  # 40%

    @pytest.mark.unit
    def test_hrv_scoring_brackets(self):
        """Should score HRV in correct brackets."""
        # Excellent HRV >= 50
        stats = {'averages': {'hrv': 55}}
        result = calculate_health_score(stats)
        assert result['breakdown']['hrv'] == 15  # Full points

        # Good HRV 40-49
        stats = {'averages': {'hrv': 45}}
        result = calculate_health_score(stats)
        assert result['breakdown']['hrv'] == 13.5  # 90%

        # Moderate HRV 30-39
        stats = {'averages': {'hrv': 35}}
        result = calculate_health_score(stats)
        assert result['breakdown']['hrv'] == 10.5  # 70%

        # Low HRV < 30
        stats = {'averages': {'hrv': 25}}
        result = calculate_health_score(stats)
        assert result['breakdown']['hrv'] == 7.5  # 50%


class TestGenerateInsights:
    """Tests for generate_insights function."""

    @pytest.mark.unit
    def test_returns_list_of_insights(self, week_data):
        """Should return a list of insights."""
        stats = generate_summary_stats(week_data, days=7)
        result = generate_insights(week_data, stats)

        assert isinstance(result, list)
        assert all(isinstance(i, dict) for i in result)

    @pytest.mark.unit
    def test_insight_structure(self, week_data):
        """Should have correct insight structure."""
        stats = generate_summary_stats(week_data, days=7)
        result = generate_insights(week_data, stats)

        for insight in result:
            assert 'type' in insight
            assert 'icon' in insight
            assert 'title' in insight
            assert 'text' in insight

    @pytest.mark.unit
    def test_returns_default_for_insufficient_data(self):
        """Should return default insight when insufficient data."""
        data = {'2026-01-20': {'totals': {}, 'readings': {}}}
        stats = {}

        result = generate_insights(data, stats)

        assert len(result) == 1
        assert result[0]['title'] == 'Collecting Data'

    @pytest.mark.unit
    def test_limits_to_four_insights(self):
        """Should limit to maximum 4 insights."""
        # Create data that would trigger many insights
        data = {}
        for i in range(14):
            date = f"2026-01-{i+1:02d}"
            data[date] = {
                'totals': {'steps': 15000 if i >= 7 else 5000, 'exercise_minutes': 45, 'stand_hours': 12},
                'readings': {'hrv_avg': 55, 'resting_hr': 55}
            }

        stats = {
            'averages': {'resting_hr': 55},
            'goals': {
                'steps_10k': {'achieved': 7, 'total': 7},
                'exercise_30m': {'achieved': 7, 'total': 7}
            }
        }

        result = generate_insights(data, stats)

        assert len(result) <= 4


class TestGeneratePersonalRecords:
    """Tests for generate_personal_records function."""

    @pytest.mark.unit
    def test_returns_records_structure(self, week_data):
        """Should return correct records structure."""
        result = generate_personal_records(week_data)

        assert 'max_steps' in result
        assert 'max_distance' in result
        assert 'max_exercise' in result
        assert 'lowest_resting_hr' in result
        assert 'highest_hrv' in result

    @pytest.mark.unit
    def test_finds_max_steps(self, week_data):
        """Should find maximum steps day."""
        result = generate_personal_records(week_data)

        # Last day has highest steps (14000)
        assert result['max_steps']['value'] == 14000
        assert result['max_steps']['date'] == '2026-01-20'

    @pytest.mark.unit
    def test_finds_lowest_resting_hr(self, week_data):
        """Should find lowest resting HR day."""
        result = generate_personal_records(week_data)

        assert result['lowest_resting_hr']['value'] == 58

    @pytest.mark.unit
    def test_handles_no_records(self):
        """Should handle data with no recordable values."""
        data = {
            '2026-01-20': {
                'totals': {},
                'readings': {}
            }
        }

        result = generate_personal_records(data)

        assert result['max_steps']['value'] == 0
        assert result['lowest_resting_hr']['value'] == 0


class TestMain:
    """Tests for main entry point."""

    @pytest.mark.unit
    def test_returns_zero_on_success(self, tmp_path, capsys):
        """Should return 0 on successful generation."""
        output_path = tmp_path / "output"
        output_path.mkdir()

        mock_data = {
            '2026-01-20': {
                'totals': {'steps': 10000, 'distance_km': 7, 'active_energy_kcal': 500, 'exercise_minutes': 30, 'stand_hours': 12},
                'readings': {'resting_hr': 58, 'hrv_avg': 50},
                'hr_stats': {'min': 55, 'max': 140, 'avg': 72, 'count': 100}
            }
        }

        with patch('generate_dashboard_data.OUTPUT_PATH', output_path):
            with patch('generate_dashboard_data.load_date_range', return_value=mock_data):
                result = main()

        assert result == 0

    @pytest.mark.unit
    def test_creates_output_files(self, tmp_path, capsys):
        """Should create all expected output files."""
        output_path = tmp_path / "output"

        mock_data = {}
        for i in range(14):
            date = f"2026-01-{i+1:02d}"
            mock_data[date] = {
                'totals': {'steps': 10000, 'distance_km': 7, 'active_energy_kcal': 500, 'exercise_minutes': 30, 'stand_hours': 12},
                'readings': {'resting_hr': 58, 'hrv_avg': 50},
                'hr_stats': {'min': 55, 'max': 140, 'avg': 72, 'count': 100}
            }

        with patch('generate_dashboard_data.OUTPUT_PATH', output_path):
            with patch('generate_dashboard_data.load_date_range', return_value=mock_data):
                main()

        expected_files = [
            'daily_trends.json',
            'weekly_comparison.json',
            'goals_progress.json',
            'summary_stats.json',
            'hr_distribution.json',
            'health_score.json',
            'insights.json',
            'personal_records.json',
            'metadata.json'
        ]

        for filename in expected_files:
            assert (output_path / filename).exists(), f"Missing {filename}"

    @pytest.mark.unit
    def test_prints_health_score(self, tmp_path, capsys):
        """Should print health score summary."""
        output_path = tmp_path / "output"

        mock_data = {
            '2026-01-20': {
                'totals': {'steps': 10000, 'distance_km': 7, 'active_energy_kcal': 500, 'exercise_minutes': 30, 'stand_hours': 12},
                'readings': {'resting_hr': 58, 'hrv_avg': 50},
                'hr_stats': None
            }
        }

        with patch('generate_dashboard_data.OUTPUT_PATH', output_path):
            with patch('generate_dashboard_data.load_date_range', return_value=mock_data):
                main()

        captured = capsys.readouterr()
        assert "HEALTH SCORE" in captured.out
        assert "Score:" in captured.out
