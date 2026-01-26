"""
Unit tests for icloud_helper module using TDD approach.
"""

import json
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, call
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from icloud_helper import (
    ensure_downloaded,
    list_available_files,
    read_json_safe,
    get_icloud_status
)


class TestEnsureDownloaded:
    """Tests for ensure_downloaded function."""

    @pytest.mark.unit
    def test_returns_false_when_file_not_exists(self, tmp_path):
        """Should return False when file doesn't exist."""
        non_existent = tmp_path / "missing.json"
        result = ensure_downloaded(non_existent)
        assert result is False

    @pytest.mark.unit
    def test_returns_true_when_file_ready(self, tmp_path):
        """Should return True when file exists and is readable."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"data": "test"}')

        result = ensure_downloaded(test_file)
        assert result is True

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_triggers_download_for_zero_byte_file(self, mock_run, tmp_path):
        """Should trigger download when file is zero bytes (placeholder)."""
        placeholder = tmp_path / "placeholder.json"
        placeholder.touch()  # Create empty file

        with patch('time.sleep'):  # Speed up test
            result = ensure_downloaded(placeholder, timeout=1)

        # Verify brctl download was called
        assert mock_run.called
        assert 'brctl' in str(mock_run.call_args)
        assert 'download' in str(mock_run.call_args)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_handles_resource_deadlock(self, mock_run, tmp_path):
        """Should retry when encountering resource deadlock error."""
        test_file = tmp_path / "locked.json"
        test_file.write_text('{"data": "test"}')

        # Simulate deadlock on first open, success on second
        mock_file = mock_open(read_data=b'test')
        side_effects = [
            OSError("Resource deadlock avoided"),
            mock_file.return_value
        ]

        with patch('builtins.open', side_effect=side_effects):
            with patch('time.sleep'):
                result = ensure_downloaded(test_file, timeout=2)

        # Should have triggered download
        assert mock_run.called

    @pytest.mark.unit
    def test_respects_timeout(self, tmp_path):
        """Should return False when timeout is exceeded."""
        placeholder = tmp_path / "placeholder.json"
        placeholder.touch()

        with patch('subprocess.run'):
            with patch('time.sleep') as mock_sleep:
                result = ensure_downloaded(placeholder, timeout=0.1)

        # Should timeout and return False
        assert result is False


class TestListAvailableFiles:
    """Tests for list_available_files function."""

    @pytest.mark.unit
    def test_lists_json_files(self, temp_health_data_dir):
        """Should list all JSON files in directory."""
        files = list_available_files(temp_health_data_dir, ensure_downloaded=False)

        assert len(files) == 7
        assert all(f.suffix == '.json' for f in files)
        assert all(f.name.startswith('HealthAutoExport') for f in files)

    @pytest.mark.unit
    def test_filters_by_pattern(self, tmp_path):
        """Should filter files by glob pattern."""
        # Create various files
        (tmp_path / "file1.json").touch()
        (tmp_path / "file2.json").touch()
        (tmp_path / "file3.txt").touch()
        (tmp_path / "data.json").touch()

        # Filter for specific pattern
        files = list_available_files(tmp_path, pattern="file*.json", ensure_downloaded=False)

        assert len(files) == 2
        assert all('file' in f.name for f in files)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_triggers_download_for_placeholders(self, mock_run, tmp_path):
        """Should trigger download for zero-byte placeholder files."""
        (tmp_path / "file1.json").touch()  # Zero bytes
        file2 = tmp_path / "file2.json"
        file2.write_text('{"data": "test"}')

        files = list_available_files(tmp_path, ensure_downloaded=True)

        # Should trigger download for placeholder
        assert mock_run.called
        # Both files returned (implementation doesn't filter placeholders in list)
        assert len(files) == 2

    @pytest.mark.unit
    def test_returns_empty_list_for_non_existent_dir(self, tmp_path):
        """Should handle non-existent directory gracefully."""
        non_existent = tmp_path / "missing"

        # Implementation returns empty list rather than raising error
        files = list_available_files(non_existent, ensure_downloaded=False)
        assert files == []


class TestReadJsonSafe:
    """Tests for read_json_safe function."""

    @pytest.mark.unit
    def test_reads_valid_json(self, mock_icloud_file):
        """Should successfully read valid JSON file."""
        result = read_json_safe(mock_icloud_file)

        assert result is not None
        assert 'exportDate' in result
        assert 'data' in result
        assert result['data']['metrics'][0]['name'] == 'step_count'

    @pytest.mark.unit
    def test_returns_none_for_non_existent_file(self, tmp_path):
        """Should return None when file doesn't exist."""
        non_existent = tmp_path / "missing.json"

        result = read_json_safe(non_existent)

        assert result is None

    @pytest.mark.unit
    def test_retries_on_json_decode_error(self, tmp_path):
        """Should retry when JSON decode fails (file still syncing)."""
        test_file = tmp_path / "partial.json"
        test_file.write_text('{"incomplete": ')  # Invalid JSON

        with patch('time.sleep'):
            result = read_json_safe(test_file, max_retries=2)

        # Should return None after retries exhausted
        assert result is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_handles_oserror_with_retry(self, mock_run, tmp_path):
        """Should retry on OSError with resource deadlock."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"data": "test"}')

        call_count = 0

        def mock_ensure_downloaded(path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("Resource deadlock avoided")
            return True

        with patch('icloud_helper.ensure_downloaded', side_effect=mock_ensure_downloaded):
            with patch('time.sleep'):
                result = read_json_safe(test_file, max_retries=2)

        # Should succeed on second attempt
        assert result is not None

    @pytest.mark.unit
    def test_respects_max_retries(self, tmp_path):
        """Should respect max_retries parameter."""
        test_file = tmp_path / "bad.json"
        test_file.write_text('invalid json')

        with patch('time.sleep') as mock_sleep:
            result = read_json_safe(test_file, max_retries=3)

        # Should have slept (retries - 1) times
        assert mock_sleep.call_count >= 2
        assert result is None


class TestGetICloudStatus:
    """Tests for get_icloud_status function."""

    @pytest.mark.unit
    def test_returns_unknown_for_non_existent_file(self, tmp_path):
        """Should return 'unknown' for non-existent file."""
        non_existent = tmp_path / "missing.json"

        status = get_icloud_status(non_existent)

        assert status == 'unknown'

    @pytest.mark.unit
    def test_returns_placeholder_for_zero_byte_file(self, tmp_path):
        """Should return 'placeholder' for zero-byte file."""
        placeholder = tmp_path / "placeholder.json"
        placeholder.touch()

        status = get_icloud_status(placeholder)

        assert status == 'placeholder'

    @pytest.mark.unit
    def test_returns_downloaded_for_accessible_file(self, mock_icloud_file):
        """Should return 'downloaded' for accessible file with content."""
        status = get_icloud_status(mock_icloud_file)

        assert status == 'downloaded'

    @pytest.mark.unit
    def test_returns_downloading_for_locked_file(self, tmp_path):
        """Should return 'downloading' for locked file."""
        test_file = tmp_path / "locked.json"
        test_file.write_text('{"data": "test"}')

        # Mock file opening to raise deadlock error
        with patch('builtins.open', side_effect=OSError("Resource deadlock avoided")):
            status = get_icloud_status(test_file)

        assert status == 'downloading'

    @pytest.mark.unit
    def test_returns_unknown_for_other_errors(self, tmp_path):
        """Should return 'unknown' for unexpected errors."""
        test_file = tmp_path / "error.json"
        test_file.write_text('{"data": "test"}')

        with patch('builtins.open', side_effect=OSError("Unknown error")):
            status = get_icloud_status(test_file)

        assert status == 'unknown'


class TestIntegrationScenarios:
    """Integration-style tests for common workflows."""

    @pytest.mark.integration
    def test_full_workflow_with_valid_file(self, mock_icloud_file):
        """Test complete workflow: check status, ensure download, read file."""
        # Check status
        status = get_icloud_status(mock_icloud_file)
        assert status == 'downloaded'

        # Ensure downloaded
        ready = ensure_downloaded(mock_icloud_file)
        assert ready is True

        # Read file
        data = read_json_safe(mock_icloud_file)
        assert data is not None
        assert 'data' in data

    @pytest.mark.integration
    @patch('subprocess.run')
    def test_workflow_with_placeholder(self, mock_run, tmp_path):
        """Test workflow with iCloud placeholder file."""
        placeholder = tmp_path / "placeholder.json"
        placeholder.touch()

        # Check status
        status = get_icloud_status(placeholder)
        assert status == 'placeholder'

        # Try to ensure downloaded (will timeout in test)
        with patch('time.sleep'):
            ready = ensure_downloaded(placeholder, timeout=0.5)

        # Should have tried to download
        assert mock_run.called
