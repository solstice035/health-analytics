"""
Tests for the configuration system.

These tests verify:
- Default path resolution
- Environment variable overrides
- Custom configuration creation
- Validation and error handling
"""

import pytest
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from health_analytics.config import Config, config, create_config, _get_project_root


class TestConfigDefaults:
    """Tests for default configuration behavior."""

    @pytest.mark.unit
    def test_project_root_detection(self):
        """Should correctly detect project root."""
        root = _get_project_root()

        # Project root should contain known files
        assert (root / 'README.md').exists() or (root / 'pytest.ini').exists()

    @pytest.mark.unit
    def test_default_health_data_path(self):
        """Should have default health data path."""
        assert config.health_data_path is not None
        assert isinstance(config.health_data_path, Path)
        assert config.health_data_path.name == 'data'

    @pytest.mark.unit
    def test_default_dashboard_data_path(self):
        """Should have default dashboard data path."""
        assert config.dashboard_data_path is not None
        assert isinstance(config.dashboard_data_path, Path)
        assert 'dashboard' in str(config.dashboard_data_path)

    @pytest.mark.unit
    def test_default_cache_dir(self):
        """Should have default cache directory."""
        assert config.cache_dir is not None
        assert isinstance(config.cache_dir, Path)
        assert '.cache' in str(config.cache_dir)

    @pytest.mark.unit
    def test_scripts_path(self):
        """Should have scripts path."""
        assert config.scripts_path is not None
        assert config.scripts_path.name == 'scripts'

    @pytest.mark.unit
    def test_dashboard_path(self):
        """Should have dashboard path."""
        assert config.dashboard_path is not None
        assert config.dashboard_path.name == 'dashboard'


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""

    @pytest.mark.unit
    def test_health_data_path_env_override(self, tmp_path, monkeypatch):
        """Should use HEALTH_DATA_PATH environment variable."""
        custom_path = tmp_path / 'custom_health_data'
        custom_path.mkdir()

        monkeypatch.setenv('HEALTH_DATA_PATH', str(custom_path))

        # Create new config to pick up env var
        new_config = Config()

        assert new_config.health_data_path == custom_path

    @pytest.mark.unit
    def test_dashboard_data_path_env_override(self, tmp_path, monkeypatch):
        """Should use DASHBOARD_DATA_PATH environment variable."""
        custom_path = tmp_path / 'custom_dashboard_data'
        custom_path.mkdir()

        monkeypatch.setenv('DASHBOARD_DATA_PATH', str(custom_path))

        # Create new config to pick up env var
        new_config = Config()

        assert new_config.dashboard_data_path == custom_path

    @pytest.mark.unit
    def test_cache_dir_env_override(self, tmp_path, monkeypatch):
        """Should use HEALTH_ANALYTICS_CACHE_DIR environment variable."""
        custom_path = tmp_path / 'custom_cache'
        custom_path.mkdir()

        monkeypatch.setenv('HEALTH_ANALYTICS_CACHE_DIR', str(custom_path))

        # Create new config to pick up env var
        new_config = Config()

        assert new_config.cache_dir == custom_path


class TestCustomConfig:
    """Tests for custom configuration creation."""

    @pytest.mark.unit
    def test_create_config_with_custom_paths(self, tmp_path):
        """Should create config with custom paths."""
        health_path = tmp_path / 'health'
        dashboard_path = tmp_path / 'dashboard'
        cache_path = tmp_path / 'cache'

        health_path.mkdir()
        dashboard_path.mkdir()
        cache_path.mkdir()

        custom = create_config(
            health_data_path=health_path,
            dashboard_data_path=dashboard_path,
            cache_dir=cache_path
        )

        assert custom.health_data_path == health_path
        assert custom.dashboard_data_path == dashboard_path
        assert custom.cache_dir == cache_path

    @pytest.mark.unit
    def test_create_config_partial_override(self, tmp_path):
        """Should allow partial path overrides."""
        health_path = tmp_path / 'health'
        health_path.mkdir()

        custom = create_config(health_data_path=health_path)

        assert custom.health_data_path == health_path
        # Other paths should be defaults
        assert custom.dashboard_data_path == custom.project_root / 'dashboard' / 'data'


class TestValidation:
    """Tests for configuration validation."""

    @pytest.mark.unit
    def test_validate_returns_dict(self):
        """Should return validation dictionary."""
        result = config.validate()

        assert isinstance(result, dict)
        assert 'project_root' in result
        assert 'health_data_path' in result
        assert 'dashboard_data_path' in result

    @pytest.mark.unit
    def test_validate_includes_exists_flag(self):
        """Should include exists flag for each path."""
        result = config.validate()

        for name, info in result.items():
            assert 'path' in info
            assert 'exists' in info
            assert isinstance(info['exists'], bool)

    @pytest.mark.unit
    def test_validate_detects_symlinks(self):
        """Should detect if health_data_path is a symlink."""
        result = config.validate()

        assert 'is_symlink' in result['health_data_path']


class TestEnsureDirectories:
    """Tests for directory creation."""

    @pytest.mark.unit
    def test_ensure_directories_creates_missing(self, tmp_path):
        """Should create missing directories."""
        dashboard_path = tmp_path / 'dashboard' / 'data'
        cache_path = tmp_path / 'cache'

        # Directories shouldn't exist yet
        assert not dashboard_path.exists()
        assert not cache_path.exists()

        custom = create_config(
            dashboard_data_path=dashboard_path,
            cache_dir=cache_path
        )

        custom.ensure_directories()

        assert dashboard_path.exists()
        assert cache_path.exists()

    @pytest.mark.unit
    def test_ensure_directories_idempotent(self, tmp_path):
        """Should not fail if directories already exist."""
        dashboard_path = tmp_path / 'dashboard' / 'data'
        dashboard_path.mkdir(parents=True)

        custom = create_config(dashboard_data_path=dashboard_path)

        # Should not raise
        custom.ensure_directories()
        custom.ensure_directories()

        assert dashboard_path.exists()


class TestStringRepresentation:
    """Tests for string representation."""

    @pytest.mark.unit
    def test_str_contains_all_paths(self):
        """Should include all paths in string representation."""
        result = str(config)

        assert 'Project Root' in result
        assert 'Health Data' in result
        assert 'Dashboard Data' in result
        assert 'Dashboard' in result
        assert 'Scripts' in result
        assert 'Cache' in result

    @pytest.mark.unit
    def test_str_is_readable(self):
        """Should produce readable output."""
        result = str(config)

        assert '\n' in result  # Multi-line
        assert ':' in result   # Key-value format


class TestSingletonBehavior:
    """Tests for singleton configuration instance."""

    @pytest.mark.unit
    def test_config_is_singleton(self):
        """Should provide single config instance."""
        from health_analytics.config import config as config1
        from health_analytics.config import config as config2

        assert config1 is config2

    @pytest.mark.unit
    def test_get_config_returns_singleton(self):
        """get_config() should return the singleton."""
        from health_analytics.config import get_config

        assert get_config() is config
