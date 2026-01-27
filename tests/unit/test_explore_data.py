"""Tests for explore_data.py"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from explore_data import (
    find_health_files,
    explore_file_structure,
    generate_date_coverage_report,
    main
)


class TestFindHealthFiles:
    """Tests for find_health_files function."""

    @pytest.mark.unit
    def test_returns_empty_when_path_missing(self, tmp_path, capsys):
        """Should return empty list when path doesn't exist."""
        with patch('explore_data.HEALTH_DATA_PATH', tmp_path / "nonexistent"):
            result = find_health_files()

        assert result == []
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    @pytest.mark.unit
    def test_finds_health_export_files(self, tmp_path):
        """Should find HealthAutoExport files."""
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{}')
        (tmp_path / "HealthAutoExport-2026-01-02.json").write_text('{}')
        (tmp_path / "other-file.json").write_text('{}')

        with patch('explore_data.HEALTH_DATA_PATH', tmp_path):
            result = find_health_files()

        assert len(result) == 2

    @pytest.mark.unit
    def test_returns_sorted_files(self, tmp_path):
        """Should return files in sorted order."""
        (tmp_path / "HealthAutoExport-2026-01-03.json").write_text('{}')
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{}')
        (tmp_path / "HealthAutoExport-2026-01-02.json").write_text('{}')

        with patch('explore_data.HEALTH_DATA_PATH', tmp_path):
            result = find_health_files()

        assert "2026-01-01" in str(result[0])
        assert "2026-01-03" in str(result[-1])

    @pytest.mark.unit
    def test_shows_download_status(self, tmp_path, capsys):
        """Should report downloaded vs pending files."""
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{"data": 1}')
        (tmp_path / "HealthAutoExport-2026-01-02.json").write_text('')  # Empty = not downloaded

        with patch('explore_data.HEALTH_DATA_PATH', tmp_path):
            find_health_files()

        captured = capsys.readouterr()
        assert "downloaded" in captured.out.lower()


class TestExploreFileStructure:
    """Tests for explore_file_structure function."""

    @pytest.mark.unit
    def test_returns_none_for_unreadable_file(self, tmp_path, capsys):
        """Should return None when file can't be read."""
        file_path = tmp_path / "test.json"
        file_path.write_text("invalid")

        with patch('explore_data.get_icloud_status', return_value="syncing"):
            with patch('explore_data.read_json_safe', return_value=None):
                result = explore_file_structure(file_path)

        assert result is None

    @pytest.mark.unit
    def test_shows_top_level_keys(self, tmp_path, capsys):
        """Should display top-level keys."""
        file_path = tmp_path / "test.json"
        data = {"key1": "value", "key2": [1, 2, 3], "key3": {"nested": "data"}}
        file_path.write_text(json.dumps(data))

        with patch('explore_data.get_icloud_status', return_value="local"):
            with patch('explore_data.read_json_safe', return_value=data):
                result = explore_file_structure(file_path)

        assert result == data
        captured = capsys.readouterr()
        assert "Top-level keys" in captured.out

    @pytest.mark.unit
    def test_shows_metrics_count(self, tmp_path, capsys):
        """Should show metric data point counts."""
        file_path = tmp_path / "test.json"
        data = {
            "data": {
                "metrics": {
                    "step_count": [{"qty": 1}, {"qty": 2}, {"qty": 3}],
                    "heart_rate": [{"qty": 60}]
                }
            }
        }
        file_path.write_text(json.dumps(data))

        with patch('explore_data.get_icloud_status', return_value="local"):
            with patch('explore_data.read_json_safe', return_value=data):
                explore_file_structure(file_path)

        captured = capsys.readouterr()
        assert "Health Metrics Found" in captured.out
        assert "step_count" in captured.out
        assert "3 data points" in captured.out

    @pytest.mark.unit
    def test_shows_icloud_status(self, tmp_path, capsys):
        """Should display iCloud status."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{}')

        with patch('explore_data.get_icloud_status', return_value="evicted"):
            with patch('explore_data.read_json_safe', return_value={}):
                explore_file_structure(file_path)

        captured = capsys.readouterr()
        assert "iCloud status" in captured.out


class TestGenerateDateCoverageReport:
    """Tests for generate_date_coverage_report function."""

    @pytest.mark.unit
    def test_handles_empty_files(self, capsys):
        """Should handle empty file list."""
        generate_date_coverage_report([])

        captured = capsys.readouterr()
        assert "No files to analyze" in captured.out

    @pytest.mark.unit
    def test_shows_date_range(self, tmp_path, capsys):
        """Should show date range of files."""
        files = [
            tmp_path / "HealthAutoExport-2026-01-01.json",
            tmp_path / "HealthAutoExport-2026-01-15.json",
            tmp_path / "HealthAutoExport-2026-01-30.json"
        ]
        for f in files:
            f.write_text('{}')

        generate_date_coverage_report(files)

        captured = capsys.readouterr()
        assert "First export" in captured.out
        assert "2026-01-01" in captured.out
        assert "2026-01-30" in captured.out

    @pytest.mark.unit
    def test_shows_total_days(self, tmp_path, capsys):
        """Should show total number of days."""
        files = [
            tmp_path / "HealthAutoExport-2026-01-01.json",
            tmp_path / "HealthAutoExport-2026-01-02.json",
            tmp_path / "HealthAutoExport-2026-01-03.json"
        ]
        for f in files:
            f.write_text('{}')

        generate_date_coverage_report(files)

        captured = capsys.readouterr()
        assert "Total days: 3" in captured.out

    @pytest.mark.unit
    def test_reports_missing_days(self, tmp_path, capsys):
        """Should report missing days in coverage."""
        files = [
            tmp_path / "HealthAutoExport-2026-01-01.json",
            tmp_path / "HealthAutoExport-2026-01-10.json"  # Gap of 8 days
        ]
        for f in files:
            f.write_text('{}')

        generate_date_coverage_report(files)

        captured = capsys.readouterr()
        assert "Missing" in captured.out

    @pytest.mark.unit
    def test_handles_invalid_filenames(self, tmp_path, capsys):
        """Should skip files with invalid date formats."""
        files = [
            tmp_path / "HealthAutoExport-2026-01-01.json",
            tmp_path / "HealthAutoExport-invalid.json",
            tmp_path / "HealthAutoExport-2026-01-02.json"
        ]
        for f in files:
            f.write_text('{}')

        generate_date_coverage_report(files)

        captured = capsys.readouterr()
        assert "Total days: 2" in captured.out


class TestMain:
    """Tests for main function."""

    @pytest.mark.unit
    def test_returns_error_when_no_files(self, tmp_path, capsys):
        """Should return 1 when no files found."""
        with patch('explore_data.HEALTH_DATA_PATH', tmp_path):
            result = main()

        assert result == 1

    @pytest.mark.unit
    def test_returns_success_with_files(self, tmp_path, capsys):
        """Should return 0 when files found and analyzed."""
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{}')

        with patch('explore_data.HEALTH_DATA_PATH', tmp_path):
            with patch('explore_data.get_icloud_status', return_value="local"):
                with patch('explore_data.read_json_safe', return_value={}):
                    result = main()

        assert result == 0

    @pytest.mark.unit
    def test_explores_latest_file(self, tmp_path, capsys):
        """Should explore the most recent file."""
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{}')
        (tmp_path / "HealthAutoExport-2026-01-15.json").write_text('{}')

        with patch('explore_data.HEALTH_DATA_PATH', tmp_path):
            with patch('explore_data.get_icloud_status', return_value="local"):
                with patch('explore_data.read_json_safe', return_value={}):
                    main()

        captured = capsys.readouterr()
        assert "2026-01-15" in captured.out

    @pytest.mark.unit
    def test_shows_next_steps_on_success(self, tmp_path, capsys):
        """Should show next steps when analysis succeeds."""
        (tmp_path / "HealthAutoExport-2026-01-01.json").write_text('{}')

        with patch('explore_data.HEALTH_DATA_PATH', tmp_path):
            with patch('explore_data.get_icloud_status', return_value="local"):
                with patch('explore_data.read_json_safe', return_value={"data": {}}):
                    main()

        captured = capsys.readouterr()
        assert "Next steps" in captured.out
