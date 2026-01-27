"""Tests for weekly_summary.py"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from weekly_summary import (
    get_week_dates,
    load_week_data,
    calculate_weekly_stats,
    print_weekly_summary,
    main
)


class TestGetWeekDates:
    """Tests for get_week_dates function."""

    @pytest.mark.unit
    def test_returns_list_of_dates(self):
        """Should return a list of datetime objects."""
        result = get_week_dates()
        assert isinstance(result, list)
        assert all(isinstance(d, datetime) for d in result)

    @pytest.mark.unit
    def test_returns_seven_days_by_default(self):
        """Should return 7 days by default."""
        result = get_week_dates()
        assert len(result) == 7

    @pytest.mark.unit
    def test_returns_custom_number_of_days(self):
        """Should return custom number of days."""
        result = get_week_dates(days=14)
        assert len(result) == 14

    @pytest.mark.unit
    def test_accepts_string_end_date(self):
        """Should accept string date format."""
        result = get_week_dates("2026-01-20", days=3)
        assert len(result) == 3
        assert result[-1].strftime("%Y-%m-%d") == "2026-01-20"

    @pytest.mark.unit
    def test_dates_are_in_order(self):
        """Should return dates in chronological order."""
        result = get_week_dates("2026-01-20", days=5)
        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]

    @pytest.mark.unit
    def test_end_date_is_last(self):
        """End date should be the last in the list."""
        end = datetime(2026, 1, 20)
        result = get_week_dates(end, days=7)
        assert result[-1].date() == end.date()


class TestLoadWeekData:
    """Tests for load_week_data function."""

    @pytest.mark.unit
    def test_returns_dict(self):
        """Should return a dictionary."""
        dates = get_week_dates(days=3)
        with patch('weekly_summary.HEALTH_DATA_PATH', Path("/nonexistent")):
            result = load_week_data(dates)
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_loads_existing_files(self, tmp_path):
        """Should load data from existing files."""
        dates = [datetime(2026, 1, 20)]
        file_path = tmp_path / "HealthAutoExport-2026-01-20.json"
        file_path.write_text('{"data": {"metrics": {}}}')

        mock_metrics = {'step_count': [{'qty': '1000'}]}
        mock_totals = {'steps': 1000}
        mock_readings = {'resting_hr': 60}

        with patch('weekly_summary.HEALTH_DATA_PATH', tmp_path):
            with patch('weekly_summary.read_json_safe', return_value={'data': {'metrics': mock_metrics}}):
                with patch('weekly_summary.extract_all_metrics', return_value=mock_metrics):
                    with patch('weekly_summary.calculate_totals', return_value=mock_totals):
                        with patch('weekly_summary.get_key_readings', return_value=mock_readings):
                            result = load_week_data(dates)

        assert "2026-01-20" in result
        assert result["2026-01-20"]['totals']['steps'] == 1000

    @pytest.mark.unit
    def test_skips_missing_files(self, tmp_path):
        """Should skip dates without files."""
        dates = [datetime(2026, 1, 20), datetime(2026, 1, 21)]
        # Only create one file
        file_path = tmp_path / "HealthAutoExport-2026-01-20.json"
        file_path.write_text('{}')

        with patch('weekly_summary.HEALTH_DATA_PATH', tmp_path):
            with patch('weekly_summary.read_json_safe', return_value=None):
                result = load_week_data(dates)

        assert len(result) == 0  # No valid data


class TestCalculateWeeklyStats:
    """Tests for calculate_weekly_stats function."""

    @pytest.mark.unit
    def test_returns_none_for_empty_data(self):
        """Should return None for empty data."""
        result = calculate_weekly_stats({})
        assert result is None

    @pytest.mark.unit
    def test_calculates_averages(self):
        """Should calculate averages correctly."""
        week_data = {
            "2026-01-20": {
                'totals': {'steps': 10000},
                'readings': {'resting_hr': 60}
            },
            "2026-01-21": {
                'totals': {'steps': 8000},
                'readings': {'resting_hr': 62}
            }
        }
        result = calculate_weekly_stats(week_data)

        assert result['steps']['avg'] == 9000
        assert result['resting_hr']['avg'] == 61

    @pytest.mark.unit
    def test_calculates_min_max(self):
        """Should calculate min and max correctly."""
        week_data = {
            "2026-01-20": {'totals': {'steps': 5000}, 'readings': {}},
            "2026-01-21": {'totals': {'steps': 15000}, 'readings': {}},
            "2026-01-22": {'totals': {'steps': 10000}, 'readings': {}}
        }
        result = calculate_weekly_stats(week_data)

        assert result['steps']['min'] == 5000
        assert result['steps']['max'] == 15000

    @pytest.mark.unit
    def test_calculates_totals(self):
        """Should calculate totals correctly."""
        week_data = {
            "2026-01-20": {'totals': {'steps': 5000}, 'readings': {}},
            "2026-01-21": {'totals': {'steps': 7000}, 'readings': {}},
            "2026-01-22": {'totals': {'steps': 8000}, 'readings': {}}
        }
        result = calculate_weekly_stats(week_data)

        assert result['steps']['total'] == 20000
        assert result['steps']['count'] == 3


class TestPrintWeeklySummary:
    """Tests for print_weekly_summary function."""

    @pytest.mark.unit
    def test_prints_header(self, capsys):
        """Should print header with date range."""
        dates = [datetime(2026, 1, 14), datetime(2026, 1, 20)]
        print_weekly_summary(dates, {}, None)

        captured = capsys.readouterr()
        assert "WEEKLY HEALTH SUMMARY" in captured.out
        assert "2026-01-14" in captured.out
        assert "2026-01-20" in captured.out

    @pytest.mark.unit
    def test_prints_days_analyzed(self, capsys):
        """Should show days analyzed count."""
        dates = [datetime(2026, 1, 14 + i) for i in range(7)]
        week_data = {
            "2026-01-15": {'totals': {}, 'readings': {}},
            "2026-01-16": {'totals': {}, 'readings': {}}
        }
        print_weekly_summary(dates, week_data, None)

        captured = capsys.readouterr()
        assert "Days analyzed: 2/7" in captured.out

    @pytest.mark.unit
    def test_prints_daily_breakdown(self, capsys):
        """Should print daily breakdown table."""
        dates = [datetime(2026, 1, 20)]
        week_data = {
            "2026-01-20": {
                'totals': {'steps': 10000, 'distance_km': 7.5, 'active_energy_kcal': 500},
                'readings': {}
            }
        }
        print_weekly_summary(dates, week_data, None)

        captured = capsys.readouterr()
        assert "DAILY BREAKDOWN" in captured.out
        assert "10,000" in captured.out

    @pytest.mark.unit
    def test_prints_weekly_averages(self, capsys):
        """Should print weekly averages when stats available."""
        dates = [datetime(2026, 1, 20)]
        week_data = {}
        stats = {
            'steps': {'avg': 9500, 'total': 66500, 'values': [9500], 'count': 7},
            'distance_km': {'avg': 6.5, 'total': 45.5, 'values': [6.5], 'count': 7}
        }
        print_weekly_summary(dates, week_data, stats)

        captured = capsys.readouterr()
        assert "WEEKLY AVERAGES" in captured.out
        assert "9,500/day" in captured.out

    @pytest.mark.unit
    def test_prints_goal_achievements(self, capsys):
        """Should show goal achievement stats."""
        dates = [datetime(2026, 1, 20)]
        week_data = {}
        stats = {
            'steps': {'avg': 10000, 'total': 70000, 'values': [10000, 12000, 8000], 'count': 3},
            'stand_hours': {'avg': 11, 'total': 77, 'values': [12, 10, 11], 'count': 3}
        }
        print_weekly_summary(dates, week_data, stats)

        captured = capsys.readouterr()
        assert "GOAL ACHIEVEMENTS" in captured.out
        assert "10,000 steps" in captured.out


class TestMain:
    """Tests for main function."""

    @pytest.mark.unit
    def test_returns_zero(self, capsys):
        """Should return 0."""
        with patch.object(sys, 'argv', ['weekly_summary.py']):
            with patch('weekly_summary.load_week_data', return_value={}):
                with patch('weekly_summary.calculate_weekly_stats', return_value=None):
                    result = main()

        assert result == 0

    @pytest.mark.unit
    def test_uses_yesterday_as_default(self, capsys):
        """Should default to yesterday as end date."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        with patch('weekly_summary.load_week_data', return_value={}) as mock_load:
            with patch('weekly_summary.calculate_weekly_stats', return_value=None):
                with patch.object(sys, 'argv', ['weekly_summary.py']):
                    main()

        # Check the dates passed to load_week_data
        dates = mock_load.call_args[0][0]
        assert dates[-1].strftime("%Y-%m-%d") == yesterday

    @pytest.mark.unit
    def test_accepts_custom_end_date(self, capsys):
        """Should accept custom end date from command line."""
        with patch('weekly_summary.load_week_data', return_value={}) as mock_load:
            with patch('weekly_summary.calculate_weekly_stats', return_value=None):
                with patch.object(sys, 'argv', ['weekly_summary.py', '2026-01-15']):
                    main()

        dates = mock_load.call_args[0][0]
        assert dates[-1].strftime("%Y-%m-%d") == "2026-01-15"

    @pytest.mark.unit
    def test_accepts_custom_days(self, capsys):
        """Should accept custom number of days from command line."""
        with patch('weekly_summary.load_week_data', return_value={}) as mock_load:
            with patch('weekly_summary.calculate_weekly_stats', return_value=None):
                with patch.object(sys, 'argv', ['weekly_summary.py', '2026-01-15', '14']):
                    main()

        dates = mock_load.call_args[0][0]
        assert len(dates) == 14
