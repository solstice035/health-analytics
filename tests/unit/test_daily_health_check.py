"""Tests for daily_health_check.py"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from daily_health_check import (
    get_yesterday_file,
    get_today_file,
    check_data_freshness,
    extract_key_metrics,
    generate_daily_summary,
    check_file_count,
    main
)


class TestGetYesterdayFile:
    """Tests for get_yesterday_file function."""

    @pytest.mark.unit
    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_yesterday_file()
        assert isinstance(result, Path)

    @pytest.mark.unit
    def test_filename_contains_yesterday_date(self):
        """Should contain yesterday's date in filename."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = get_yesterday_file()
        assert yesterday in str(result)

    @pytest.mark.unit
    def test_filename_format(self):
        """Should use HealthAutoExport format."""
        result = get_yesterday_file()
        assert "HealthAutoExport-" in result.name
        assert result.suffix == ".json"


class TestGetTodayFile:
    """Tests for get_today_file function."""

    @pytest.mark.unit
    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_today_file()
        assert isinstance(result, Path)

    @pytest.mark.unit
    def test_filename_contains_today_date(self):
        """Should contain today's date in filename."""
        today = datetime.now().strftime("%Y-%m-%d")
        result = get_today_file()
        assert today in str(result)


class TestExtractKeyMetrics:
    """Tests for extract_key_metrics function."""

    @pytest.mark.unit
    def test_returns_none_for_none_data(self):
        """Should return None for None input."""
        result = extract_key_metrics(None)
        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_empty_data(self):
        """Should return None for empty data."""
        result = extract_key_metrics({})
        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_no_data_key(self):
        """Should return None when 'data' key missing."""
        result = extract_key_metrics({"other": "stuff"})
        assert result is None

    @pytest.mark.unit
    def test_extracts_step_count(self):
        """Should extract total step count."""
        data = {
            "data": {
                "metrics": {
                    "step_count": [
                        {"qty": "1000"},
                        {"qty": "500"},
                        {"qty": "250"}
                    ]
                }
            }
        }
        result = extract_key_metrics(data)
        assert result['steps'] == 1750

    @pytest.mark.unit
    def test_extracts_active_energy(self):
        """Should extract active energy."""
        data = {
            "data": {
                "metrics": {
                    "active_energy": [
                        {"qty": "100.5"},
                        {"qty": "50.25"}
                    ]
                }
            }
        }
        result = extract_key_metrics(data)
        assert result['active_energy_kcal'] == 150

    @pytest.mark.unit
    def test_extracts_resting_hr(self):
        """Should extract resting heart rate (last value)."""
        data = {
            "data": {
                "metrics": {
                    "resting_heart_rate": [
                        {"qty": "65"},
                        {"qty": "62"},
                        {"qty": "60"}
                    ]
                }
            }
        }
        result = extract_key_metrics(data)
        assert result['resting_hr'] == 60  # Last value

    @pytest.mark.unit
    def test_extracts_sleep_records(self):
        """Should count sleep analysis records."""
        data = {
            "data": {
                "metrics": {
                    "sleep_analysis": [
                        {"value": "InBed"},
                        {"value": "Asleep"},
                        {"value": "Awake"}
                    ]
                }
            }
        }
        result = extract_key_metrics(data)
        assert result['sleep_records'] == 3

    @pytest.mark.unit
    def test_handles_empty_metrics(self):
        """Should return empty dict for no metrics."""
        data = {"data": {"metrics": {}}}
        result = extract_key_metrics(data)
        assert result == {}

    @pytest.mark.unit
    def test_handles_missing_qty(self):
        """Should handle records without qty field."""
        data = {
            "data": {
                "metrics": {
                    "step_count": [
                        {"qty": "100"},
                        {"value": "no qty"},  # Missing qty
                        {"qty": "50"}
                    ]
                }
            }
        }
        result = extract_key_metrics(data)
        assert result['steps'] == 150


class TestCheckDataFreshness:
    """Tests for check_data_freshness function."""

    @pytest.mark.unit
    def test_returns_true_when_yesterday_exists(self, tmp_path, capsys):
        """Should return True when yesterday's file exists."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_file = tmp_path / f"HealthAutoExport-{yesterday}.json"
        yesterday_file.write_text('{"test": 1}')

        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            with patch('daily_health_check.get_icloud_status', return_value="local"):
                result = check_data_freshness()

        assert result is True

    @pytest.mark.unit
    def test_returns_false_when_yesterday_missing(self, tmp_path, capsys):
        """Should return False when yesterday's file is missing."""
        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            result = check_data_freshness()

        assert result is False
        captured = capsys.readouterr()
        assert "missing" in captured.out.lower()

    @pytest.mark.unit
    def test_reports_today_available(self, tmp_path, capsys):
        """Should report when today's file is available."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        (tmp_path / f"HealthAutoExport-{today}.json").write_text('{}')
        (tmp_path / f"HealthAutoExport-{yesterday}.json").write_text('{}')

        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            with patch('daily_health_check.get_icloud_status', return_value="local"):
                check_data_freshness()

        captured = capsys.readouterr()
        assert "Today's data exists" in captured.out


class TestCheckFileCount:
    """Tests for check_file_count function."""

    @pytest.mark.unit
    def test_returns_zero_when_path_missing(self, tmp_path, capsys):
        """Should return 0 when path doesn't exist."""
        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path / "nonexistent"):
            result = check_file_count()

        assert result == 0

    @pytest.mark.unit
    def test_counts_health_files(self, tmp_path):
        """Should count HealthAutoExport files."""
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{}')
        (tmp_path / "HealthAutoExport-2026-01-02.json").write_text('{}')
        (tmp_path / "HealthAutoExport-2026-01-03.json").write_text('{}')
        (tmp_path / "other-file.json").write_text('{}')  # Should not count

        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            result = check_file_count()

        assert result == 3

    @pytest.mark.unit
    def test_shows_date_range(self, tmp_path, capsys):
        """Should display date range of files."""
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{}')
        (tmp_path / "HealthAutoExport-2026-01-15.json").write_text('{}')

        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            check_file_count()

        captured = capsys.readouterr()
        assert "2026-01-01" in captured.out
        assert "2026-01-15" in captured.out


class TestGenerateDailySummary:
    """Tests for generate_daily_summary function."""

    @pytest.mark.unit
    def test_reports_no_data(self, tmp_path, capsys):
        """Should report when no data available."""
        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            generate_daily_summary()

        captured = capsys.readouterr()
        assert "No data available" in captured.out

    @pytest.mark.unit
    def test_shows_metrics(self, tmp_path, capsys):
        """Should display extracted metrics."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        data = {
            "data": {
                "metrics": {
                    "step_count": [{"qty": "10000"}],
                    "active_energy": [{"qty": "500"}],
                    "resting_heart_rate": [{"qty": "62"}],
                    "sleep_analysis": [{"value": "asleep"}]
                }
            }
        }
        (tmp_path / f"HealthAutoExport-{yesterday}.json").write_text(json.dumps(data))

        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            with patch('daily_health_check.read_json_safe', return_value=data):
                generate_daily_summary()

        captured = capsys.readouterr()
        assert "Steps" in captured.out
        assert "10,000" in captured.out


class TestMain:
    """Tests for main function."""

    @pytest.mark.unit
    def test_returns_error_when_path_missing(self, tmp_path):
        """Should return 1 when data path doesn't exist."""
        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path / "nonexistent"):
            result = main()

        assert result == 1

    @pytest.mark.unit
    def test_returns_success_with_data(self, tmp_path):
        """Should return 0 when data is available."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        data = {"data": {"metrics": {"step_count": [{"qty": "1000"}]}}}
        (tmp_path / f"HealthAutoExport-{yesterday}.json").write_text(json.dumps(data))

        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            with patch('daily_health_check.get_icloud_status', return_value="local"):
                with patch('daily_health_check.read_json_safe', return_value=data):
                    result = main()

        assert result == 0

    @pytest.mark.unit
    def test_returns_error_when_no_files(self, tmp_path):
        """Should return 1 when no files exist."""
        with patch('daily_health_check.HEALTH_DATA_PATH', tmp_path):
            result = main()

        assert result == 1
