"""
Configuration management for Health Analytics.

This module provides a centralized configuration system that:
- Eliminates hard-coded paths throughout the codebase
- Supports environment variable overrides
- Provides sensible defaults
- Validates paths exist

Usage:
    from src.health_analytics.config import config

    # Access paths
    data_path = config.health_data_path
    output_path = config.dashboard_data_path

    # Or with environment variables:
    # HEALTH_DATA_PATH=/custom/path python script.py
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


def _get_project_root() -> Path:
    """Find the project root directory."""
    # Start from this file and go up to find the project root
    current = Path(__file__).resolve()

    # Look for markers of project root
    markers = ['README.md', 'pytest.ini', 'requirements.txt', '.git']

    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent

    # Fallback: assume we're in src/health_analytics/
    return current.parent.parent.parent


@dataclass
class Config:
    """
    Centralized configuration for Health Analytics.

    All paths are resolved as Path objects. Environment variables
    can override defaults:
    - HEALTH_DATA_PATH: Path to raw health export data
    - DASHBOARD_DATA_PATH: Path for generated dashboard JSON
    - HEALTH_ANALYTICS_CACHE_DIR: Cache directory
    """

    # Project root (auto-detected)
    project_root: Path = field(default_factory=_get_project_root)

    # Data paths (can be overridden via environment)
    _health_data_path: Optional[Path] = None
    _dashboard_data_path: Optional[Path] = None
    _cache_dir: Optional[Path] = None

    def __post_init__(self):
        """Resolve paths after initialization."""
        # Ensure project_root is a Path
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)

    @property
    def health_data_path(self) -> Path:
        """Path to raw Apple Health export JSON files."""
        if self._health_data_path:
            return self._health_data_path

        # Check environment variable
        env_path = os.environ.get('HEALTH_DATA_PATH')
        if env_path:
            return Path(env_path)

        # Default: project_root/data
        return self.project_root / 'data'

    @property
    def dashboard_data_path(self) -> Path:
        """Path for generated dashboard JSON files."""
        if self._dashboard_data_path:
            return self._dashboard_data_path

        # Check environment variable
        env_path = os.environ.get('DASHBOARD_DATA_PATH')
        if env_path:
            return Path(env_path)

        # Default: project_root/dashboard/data
        return self.project_root / 'dashboard' / 'data'

    @property
    def dashboard_path(self) -> Path:
        """Path to dashboard directory."""
        return self.project_root / 'dashboard'

    @property
    def scripts_path(self) -> Path:
        """Path to scripts directory."""
        return self.project_root / 'scripts'

    @property
    def cache_dir(self) -> Path:
        """Path to cache directory."""
        if self._cache_dir:
            return self._cache_dir

        # Check environment variable
        env_path = os.environ.get('HEALTH_ANALYTICS_CACHE_DIR')
        if env_path:
            return Path(env_path)

        # Default: project_root/.cache
        return self.project_root / '.cache'

    @property
    def hevy_api_token(self) -> Optional[str]:
        """Hevy API authentication token from HEVY_API env var."""
        return os.environ.get('HEVY_API')

    @property
    def hevy_username(self) -> Optional[str]:
        """Hevy username from HEVY_USERNAME env var."""
        return os.environ.get('HEVY_USERNAME')

    @property
    def hevy_configured(self) -> bool:
        """Check if Hevy integration is fully configured (only needs API token)."""
        return bool(self.hevy_api_token)

    @property
    def user_profile_path(self) -> Path:
        """Path to user profile JSON file."""
        return self.project_root / 'user_profile.json'

    def load_user_profile(self) -> dict:
        """Load user profile from JSON file. Returns empty dict if not found."""
        if not self.user_profile_path.exists():
            return {}
        try:
            with open(self.user_profile_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @property
    def user_age(self) -> Optional[int]:
        """User's age from profile, if configured."""
        profile = self.load_user_profile()
        age = profile.get('age')
        return int(age) if age is not None else None

    @property
    def hrmax(self) -> Optional[int]:
        """
        User's max heart rate.
        Uses hrmax_override if set, otherwise calculates from age (220 - age).
        Returns None if neither is configured.
        """
        profile = self.load_user_profile()
        override = profile.get('hrmax_override')
        if override is not None:
            return int(override)
        age = profile.get('age')
        if age is not None:
            return 220 - int(age)
        return None

    @property
    def hr_zones_configured(self) -> bool:
        """Check if HR zones can be calculated (age or hrmax_override set)."""
        return self.hrmax is not None

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.dashboard_data_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> dict:
        """
        Validate configuration and return status.

        Returns:
            Dict with validation results for each path
        """
        return {
            'project_root': {
                'path': str(self.project_root),
                'exists': self.project_root.exists()
            },
            'health_data_path': {
                'path': str(self.health_data_path),
                'exists': self.health_data_path.exists(),
                'is_symlink': self.health_data_path.is_symlink() if self.health_data_path.exists() else False
            },
            'dashboard_data_path': {
                'path': str(self.dashboard_data_path),
                'exists': self.dashboard_data_path.exists()
            },
            'dashboard_path': {
                'path': str(self.dashboard_path),
                'exists': self.dashboard_path.exists()
            },
            'scripts_path': {
                'path': str(self.scripts_path),
                'exists': self.scripts_path.exists()
            },
            'cache_dir': {
                'path': str(self.cache_dir),
                'exists': self.cache_dir.exists()
            },
            'hevy': {
                'configured': self.hevy_configured,
                'api_token_set': bool(self.hevy_api_token)
            },
            'user_profile': {
                'path': str(self.user_profile_path),
                'exists': self.user_profile_path.exists(),
                'age': self.user_age,
                'hrmax': self.hrmax,
                'hr_zones_configured': self.hr_zones_configured
            }
        }

    def __str__(self) -> str:
        """String representation showing all paths."""
        hevy_status = "configured" if self.hevy_configured else "not configured"
        hr_status = f"HRmax={self.hrmax}" if self.hr_zones_configured else "not configured"
        return (
            f"Health Analytics Configuration:\n"
            f"  Project Root:      {self.project_root}\n"
            f"  Health Data:       {self.health_data_path}\n"
            f"  Dashboard Data:    {self.dashboard_data_path}\n"
            f"  Dashboard:         {self.dashboard_path}\n"
            f"  Scripts:           {self.scripts_path}\n"
            f"  Cache:             {self.cache_dir}\n"
            f"  Hevy:              {hevy_status}\n"
            f"  HR Zones:          {hr_status}"
        )


# Singleton instance for easy import
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def create_config(
    project_root: Optional[Path] = None,
    health_data_path: Optional[Path] = None,
    dashboard_data_path: Optional[Path] = None,
    cache_dir: Optional[Path] = None
) -> Config:
    """
    Create a custom configuration instance.

    Useful for testing or running with different paths.

    Args:
        project_root: Override project root
        health_data_path: Override health data path
        dashboard_data_path: Override dashboard data path
        cache_dir: Override cache directory

    Returns:
        New Config instance with specified paths
    """
    return Config(
        project_root=project_root or _get_project_root(),
        _health_data_path=health_data_path,
        _dashboard_data_path=dashboard_data_path,
        _cache_dir=cache_dir
    )


if __name__ == '__main__':
    # Print configuration when run directly
    print(config)
    print("\nValidation:")
    for name, info in config.validate().items():
        status = "✓" if info['exists'] else "✗"
        extra = " (symlink)" if info.get('is_symlink') else ""
        print(f"  {status} {name}: {info['path']}{extra}")
