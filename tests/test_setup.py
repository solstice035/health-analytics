"""
Test to verify test infrastructure is working.
"""

import pytest


def test_fixtures_available(sample_health_data, expected_totals):
    """Verify fixtures load correctly."""
    assert sample_health_data is not None
    assert 'data' in sample_health_data
    assert 'metrics' in sample_health_data['data']
    assert len(sample_health_data['data']['metrics']) > 0
    assert expected_totals['steps'] == 220


def test_temp_dir_fixture(temp_health_data_dir):
    """Verify temp directory fixture creates files."""
    files = list(temp_health_data_dir.glob("*.json"))
    assert len(files) == 7
    assert files[0].exists()


@pytest.mark.unit
def test_marker_unit():
    """Test that unit marker works."""
    assert True


@pytest.mark.integration
def test_marker_integration():
    """Test that integration marker works."""
    assert True
