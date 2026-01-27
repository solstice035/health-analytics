"""Tests for sync_data.py"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from sync_data import sync_health_data, SOURCE_PATH, DEST_PATH


class TestSyncHealthData:
    """Tests for sync_health_data function."""

    @pytest.mark.unit
    def test_sync_returns_error_when_source_not_found(self, tmp_path):
        """Should return 1 when source path doesn't exist."""
        with patch('sync_data.SOURCE_PATH', tmp_path / "nonexistent"):
            result = sync_health_data()
            assert result == 1

    @pytest.mark.unit
    def test_sync_returns_error_when_no_files(self, tmp_path):
        """Should return 1 when no health files found."""
        source = tmp_path / "source"
        source.mkdir()

        with patch('sync_data.SOURCE_PATH', source):
            with patch('sync_data.DEST_PATH', tmp_path / "dest"):
                result = sync_health_data()
                assert result == 1

    @pytest.mark.unit
    def test_sync_copies_files(self, tmp_path):
        """Should copy health data files to destination."""
        source = tmp_path / "source"
        source.mkdir()
        dest = tmp_path / "dest"

        # Create test files
        (source / "HealthAutoExport-2026-01-01.json").write_text('{"test": 1}')
        (source / "HealthAutoExport-2026-01-02.json").write_text('{"test": 2}')

        with patch('sync_data.SOURCE_PATH', source):
            with patch('sync_data.DEST_PATH', dest):
                result = sync_health_data()

        assert result == 0
        assert (dest / "HealthAutoExport-2026-01-01.json").exists()
        assert (dest / "HealthAutoExport-2026-01-02.json").exists()

    @pytest.mark.unit
    def test_sync_skips_existing_files(self, tmp_path):
        """Should skip files that already exist."""
        source = tmp_path / "source"
        source.mkdir()
        dest = tmp_path / "dest"
        dest.mkdir()

        # Create source file
        (source / "HealthAutoExport-2026-01-01.json").write_text('{"new": 1}')
        # Create existing dest file with different content
        (dest / "HealthAutoExport-2026-01-01.json").write_text('{"old": 1}')

        with patch('sync_data.SOURCE_PATH', source):
            with patch('sync_data.DEST_PATH', dest):
                result = sync_health_data(force=False)

        assert result == 0
        # Original content should be preserved
        assert '{"old": 1}' in (dest / "HealthAutoExport-2026-01-01.json").read_text()

    @pytest.mark.unit
    def test_sync_force_overwrites(self, tmp_path):
        """Should overwrite existing files when force=True."""
        source = tmp_path / "source"
        source.mkdir()
        dest = tmp_path / "dest"
        dest.mkdir()

        # Create source file
        (source / "HealthAutoExport-2026-01-01.json").write_text('{"new": 1}')
        # Create existing dest file with different content
        (dest / "HealthAutoExport-2026-01-01.json").write_text('{"old": 1}')

        with patch('sync_data.SOURCE_PATH', source):
            with patch('sync_data.DEST_PATH', dest):
                result = sync_health_data(force=True)

        assert result == 0
        # New content should replace old
        assert '{"new": 1}' in (dest / "HealthAutoExport-2026-01-01.json").read_text()

    @pytest.mark.unit
    def test_sync_creates_dest_directory(self, tmp_path):
        """Should create destination directory if it doesn't exist."""
        source = tmp_path / "source"
        source.mkdir()
        dest = tmp_path / "dest" / "nested"

        (source / "HealthAutoExport-2026-01-01.json").write_text('{"test": 1}')

        with patch('sync_data.SOURCE_PATH', source):
            with patch('sync_data.DEST_PATH', dest):
                result = sync_health_data()

        assert result == 0
        assert dest.exists()

    @pytest.mark.unit
    def test_sync_handles_copy_error(self, tmp_path):
        """Should handle errors when copying files."""
        source = tmp_path / "source"
        source.mkdir()
        dest = tmp_path / "dest"

        (source / "HealthAutoExport-2026-01-01.json").write_text('{"test": 1}')

        with patch('sync_data.SOURCE_PATH', source):
            with patch('sync_data.DEST_PATH', dest):
                with patch('shutil.copy2', side_effect=PermissionError("denied")):
                    result = sync_health_data()

        # Should still complete but with failed count
        assert result == 0


class TestSyncDataModule:
    """Tests for module-level behavior."""

    @pytest.mark.unit
    def test_source_path_is_icloud(self):
        """SOURCE_PATH should point to iCloud directory."""
        assert "iCloud" in str(SOURCE_PATH) or "Mobile Documents" in str(SOURCE_PATH)

    @pytest.mark.unit
    def test_dest_path_is_data_directory(self):
        """DEST_PATH should point to data directory."""
        assert "data" in str(DEST_PATH)
