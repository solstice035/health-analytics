"""Tests for analyze_specific_date.py"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from analyze_specific_date import analyze_date


class TestAnalyzeDate:
    """Tests for analyze_date function."""

    @pytest.fixture
    def sample_health_data(self):
        """Sample health data structure."""
        return {
            "data": {
                "metrics": {
                    "step_count": [
                        {"qty": "1000", "date": "2026-01-20"},
                        {"qty": "500", "date": "2026-01-20"}
                    ],
                    "active_energy": [
                        {"qty": "250.5", "date": "2026-01-20"}
                    ],
                    "resting_heart_rate": [
                        {"qty": "62", "date": "2026-01-20"}
                    ],
                    "sleep_analysis": [
                        {"value": "InBed", "date": "2026-01-20"}
                    ],
                    "distance_walking_running": [
                        {"qty": "2.5", "date": "2026-01-20"}
                    ],
                    "flights_climbed": [
                        {"qty": "10", "date": "2026-01-20"}
                    ]
                },
                "workouts": []
            }
        }

    @pytest.mark.unit
    def test_analyze_nonexistent_date(self, tmp_path, capsys):
        """Should report file not found for missing date."""
        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            analyze_date("2099-12-31")

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    @pytest.mark.unit
    def test_analyze_existing_date(self, tmp_path, sample_health_data, capsys):
        """Should analyze existing health data file."""
        data_file = tmp_path / "HealthAutoExport-2026-01-20.json"
        data_file.write_text(json.dumps(sample_health_data))

        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            with patch('analyze_specific_date.get_icloud_status', return_value="local"):
                with patch('analyze_specific_date.read_json_safe', return_value=sample_health_data):
                    analyze_date("2026-01-20")

        captured = capsys.readouterr()
        assert "Analyzing" in captured.out
        assert "metrics" in captured.out.lower()

    @pytest.mark.unit
    def test_analyze_shows_icloud_status(self, tmp_path, sample_health_data, capsys):
        """Should display iCloud sync status."""
        data_file = tmp_path / "HealthAutoExport-2026-01-20.json"
        data_file.write_text(json.dumps(sample_health_data))

        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            with patch('analyze_specific_date.get_icloud_status', return_value="synced"):
                with patch('analyze_specific_date.read_json_safe', return_value=sample_health_data):
                    analyze_date("2026-01-20")

        captured = capsys.readouterr()
        assert "iCloud status" in captured.out

    @pytest.mark.unit
    def test_analyze_handles_unreadable_file(self, tmp_path, capsys):
        """Should handle files that can't be read."""
        data_file = tmp_path / "HealthAutoExport-2026-01-20.json"
        data_file.write_text("invalid json")

        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            with patch('analyze_specific_date.get_icloud_status', return_value="syncing"):
                with patch('analyze_specific_date.read_json_safe', return_value=None):
                    analyze_date("2026-01-20")

        captured = capsys.readouterr()
        assert "could not read" in captured.out.lower()

    @pytest.mark.unit
    def test_analyze_shows_top_level_keys(self, tmp_path, sample_health_data, capsys):
        """Should show top-level keys in the data."""
        data_file = tmp_path / "HealthAutoExport-2026-01-20.json"
        data_file.write_text(json.dumps(sample_health_data))

        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            with patch('analyze_specific_date.get_icloud_status', return_value="local"):
                with patch('analyze_specific_date.read_json_safe', return_value=sample_health_data):
                    analyze_date("2026-01-20")

        captured = capsys.readouterr()
        assert "Top-level keys" in captured.out

    @pytest.mark.unit
    def test_analyze_shows_step_count(self, tmp_path, sample_health_data, capsys):
        """Should calculate and show step count."""
        data_file = tmp_path / "HealthAutoExport-2026-01-20.json"
        data_file.write_text(json.dumps(sample_health_data))

        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            with patch('analyze_specific_date.get_icloud_status', return_value="local"):
                with patch('analyze_specific_date.read_json_safe', return_value=sample_health_data):
                    analyze_date("2026-01-20")

        captured = capsys.readouterr()
        assert "step_count" in captured.out
        assert "1500" in captured.out  # 1000 + 500

    @pytest.mark.unit
    def test_analyze_handles_empty_metrics(self, tmp_path, capsys):
        """Should handle data with empty metrics."""
        data = {"data": {"metrics": {}}}
        data_file = tmp_path / "HealthAutoExport-2026-01-20.json"
        data_file.write_text(json.dumps(data))

        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            with patch('analyze_specific_date.get_icloud_status', return_value="local"):
                with patch('analyze_specific_date.read_json_safe', return_value=data):
                    analyze_date("2026-01-20")

        # Should not crash
        captured = capsys.readouterr()
        assert "Analyzing" in captured.out

    @pytest.mark.unit
    def test_analyze_handles_nested_categories(self, tmp_path, capsys):
        """Should show nested categories correctly."""
        data = {
            "data": {
                "metrics": {
                    "metric1": [{"qty": 1}],
                    "metric2": [{"qty": 2}],
                    "metric3": [{"qty": 3}],
                    "metric4": [{"qty": 4}],
                    "metric5": [{"qty": 5}],
                    "metric6": [{"qty": 6}],  # Should trigger "and X more"
                },
                "workouts": {
                    "running": [],
                    "walking": []
                }
            }
        }
        data_file = tmp_path / "HealthAutoExport-2026-01-20.json"
        data_file.write_text(json.dumps(data))

        with patch('analyze_specific_date.HEALTH_DATA_PATH', tmp_path):
            with patch('analyze_specific_date.get_icloud_status', return_value="local"):
                with patch('analyze_specific_date.read_json_safe', return_value=data):
                    analyze_date("2026-01-20")

        captured = capsys.readouterr()
        assert "Available Metrics" in captured.out
