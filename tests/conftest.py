"""
Pytest configuration and shared fixtures for Health Analytics tests.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_health_data(fixtures_dir) -> Dict[str, Any]:
    """Load sample health data from fixture file."""
    with open(fixtures_dir / "sample_health_data.json") as f:
        return json.load(f)


@pytest.fixture
def empty_health_data() -> Dict[str, Any]:
    """Return health data structure with no metrics."""
    return {
        "exportDate": "2026-01-25 23:59:59 +0000",
        "data": {
            "metrics": []
        }
    }


@pytest.fixture
def invalid_health_data() -> Dict[str, Any]:
    """Return invalid health data structure."""
    return {
        "exportDate": "2026-01-25 23:59:59 +0000",
        "invalid_key": "missing data key"
    }


@pytest.fixture
def temp_health_data_dir(tmp_path) -> Path:
    """Create temporary directory with sample health data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create sample files for last 7 days
    today = datetime.now()
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        file_path = data_dir / f"HealthAutoExport-{date_str}.json"

        # Create sample data with varying metrics
        data = {
            "exportDate": f"{date_str} 23:59:59 +0000",
            "data": {
                "metrics": [
                    {
                        "name": "step_count",
                        "units": "count",
                        "data": [
                            {"qty": 1000 + (i * 100), "startDate": f"{date_str} 08:00:00 +0000", "endDate": f"{date_str} 09:00:00 +0000"}
                        ]
                    },
                    {
                        "name": "active_energy",
                        "units": "kcal",
                        "data": [
                            {"qty": 500 + (i * 50), "startDate": f"{date_str} 08:00:00 +0000", "endDate": f"{date_str} 09:00:00 +0000"}
                        ]
                    },
                    {
                        "name": "apple_exercise_time",
                        "units": "min",
                        "data": [
                            {"qty": 30 + (i * 5), "startDate": f"{date_str} 08:00:00 +0000", "endDate": f"{date_str} 09:00:00 +0000"}
                        ]
                    },
                    {
                        "name": "resting_heart_rate",
                        "units": "bpm",
                        "data": [
                            {"qty": 60 - i, "startDate": f"{date_str} 06:00:00 +0000", "endDate": f"{date_str} 06:00:00 +0000"}
                        ]
                    }
                ]
            }
        }

        with open(file_path, 'w') as f:
            json.dump(data, f)

    return data_dir


@pytest.fixture
def mock_icloud_file(tmp_path):
    """Create a mock iCloud file for testing."""
    file_path = tmp_path / "HealthAutoExport-2026-01-25.json"
    data = {
        "exportDate": "2026-01-25 23:59:59 +0000",
        "data": {
            "metrics": [
                {
                    "name": "step_count",
                    "units": "count",
                    "data": [{"qty": 10000, "startDate": "2026-01-25 08:00:00 +0000", "endDate": "2026-01-25 09:00:00 +0000"}]
                }
            ]
        }
    }
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path


@pytest.fixture
def expected_metrics():
    """Expected metrics structure from sample health data."""
    return {
        'step_count': {
            'units': 'count',
            'count': 3,
            'data': [
                {'qty': 42, 'startDate': '2026-01-25 08:00:00 +0000', 'endDate': '2026-01-25 08:15:00 +0000'},
                {'qty': 58, 'startDate': '2026-01-25 08:15:00 +0000', 'endDate': '2026-01-25 08:30:00 +0000'},
                {'qty': 120, 'startDate': '2026-01-25 09:00:00 +0000', 'endDate': '2026-01-25 09:15:00 +0000'}
            ]
        },
        'active_energy': {
            'units': 'kcal',
            'count': 2,
            'data': [
                {'qty': 50.5, 'startDate': '2026-01-25 08:00:00 +0000', 'endDate': '2026-01-25 09:00:00 +0000'},
                {'qty': 75.3, 'startDate': '2026-01-25 09:00:00 +0000', 'endDate': '2026-01-25 10:00:00 +0000'}
            ]
        }
    }


@pytest.fixture
def expected_totals():
    """Expected daily totals from sample health data."""
    return {
        'steps': 220,  # 42 + 58 + 120
        'active_energy_kcal': 125,  # 50.5 + 75.3 (rounded)
        'exercise_minutes': 45,  # 30 + 15
        'stand_hours': 12,
        'distance_km': 3.8,  # 1.5 + 2.3
        'flights': 8  # 3 + 5
    }


@pytest.fixture
def expected_readings():
    """Expected key readings from sample health data."""
    return {
        'resting_hr': 58,
        'hrv_avg': 45,  # (45 + 42 + 48) / 3
        'vo2_max': 42.5
    }


@pytest.fixture
def expected_hr_stats():
    """Expected heart rate statistics from sample health data."""
    return {
        'count': 5,
        'min': 65,
        'max': 140,
        'avg': 96  # (65 + 72 + 130 + 140 + 75) / 5
    }


# Hevy workout fixtures
@pytest.fixture
def sample_hevy_data(fixtures_dir) -> Dict[str, Any]:
    """Load sample Hevy workout data from fixture file."""
    with open(fixtures_dir / "sample_hevy_data.json") as f:
        return json.load(f)


@pytest.fixture
def empty_hevy_data() -> Dict[str, Any]:
    """Return Hevy data structure with no workouts."""
    return {"workouts": []}


# Auto-use fixtures
@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test."""
    # Remove any health analytics env vars
    for key in list(monkeypatch._setitem):
        if key.startswith('HEALTH_') or key.startswith('HEVY_'):
            monkeypatch.delenv(key, raising=False)
