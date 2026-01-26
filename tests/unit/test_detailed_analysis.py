"""
Unit tests for detailed_analysis module using TDD approach.
"""

import pytest
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from detailed_analysis import (
    extract_all_metrics,
    calculate_totals,
    get_key_readings,
    get_heart_rate_stats
)


class TestExtractAllMetrics:
    """Tests for extract_all_metrics function."""

    @pytest.mark.unit
    def test_extracts_metrics_from_valid_data(self, sample_health_data):
        """Should extract all metrics from valid health data."""
        result = extract_all_metrics(sample_health_data)

        assert result is not None
        assert isinstance(result, dict)
        assert 'step_count' in result
        assert 'active_energy' in result

    @pytest.mark.unit
    def test_metric_structure(self, sample_health_data):
        """Should return metrics with correct structure."""
        result = extract_all_metrics(sample_health_data)

        step_metric = result['step_count']
        assert 'units' in step_metric
        assert 'count' in step_metric
        assert 'data' in step_metric
        assert step_metric['units'] == 'count'
        assert step_metric['count'] == 3
        assert len(step_metric['data']) == 3

    @pytest.mark.unit
    def test_returns_none_for_invalid_data(self, invalid_health_data):
        """Should return None for data without metrics."""
        result = extract_all_metrics(invalid_health_data)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_empty_data(self):
        """Should return None for None or empty data."""
        assert extract_all_metrics(None) is None
        assert extract_all_metrics({}) is None

    @pytest.mark.unit
    def test_handles_empty_metrics_list(self, empty_health_data):
        """Should handle health data with no metrics."""
        result = extract_all_metrics(empty_health_data)

        assert result is not None
        assert result == {}

    @pytest.mark.unit
    def test_extracts_all_metric_types(self, sample_health_data):
        """Should extract all available metric types."""
        result = extract_all_metrics(sample_health_data)

        expected_metrics = [
            'step_count',
            'active_energy',
            'apple_exercise_time',
            'apple_stand_hour',
            'walking_running_distance',
            'resting_heart_rate',
            'heart_rate_variability',
            'heart_rate',
            'vo2_max',
            'flights_climbed'
        ]

        for metric in expected_metrics:
            assert metric in result, f"Missing metric: {metric}"


class TestCalculateTotals:
    """Tests for calculate_totals function."""

    @pytest.mark.unit
    def test_calculates_step_total(self, sample_health_data):
        """Should calculate total steps correctly."""
        metrics = extract_all_metrics(sample_health_data)
        totals = calculate_totals(metrics)

        assert 'steps' in totals
        assert totals['steps'] == 220  # 42 + 58 + 120

    @pytest.mark.unit
    def test_calculates_active_energy_total(self, sample_health_data):
        """Should calculate total active energy correctly."""
        metrics = extract_all_metrics(sample_health_data)
        totals = calculate_totals(metrics)

        assert 'active_energy_kcal' in totals
        assert totals['active_energy_kcal'] == 125  # 50.5 + 75.3 rounded

    @pytest.mark.unit
    def test_calculates_exercise_minutes(self, sample_health_data):
        """Should calculate total exercise minutes."""
        metrics = extract_all_metrics(sample_health_data)
        totals = calculate_totals(metrics)

        assert 'exercise_minutes' in totals
        assert totals['exercise_minutes'] == 45  # 30 + 15

    @pytest.mark.unit
    def test_calculates_stand_hours(self, sample_health_data):
        """Should calculate total stand hours."""
        metrics = extract_all_metrics(sample_health_data)
        totals = calculate_totals(metrics)

        assert 'stand_hours' in totals
        assert totals['stand_hours'] == 12

    @pytest.mark.unit
    def test_calculates_distance(self, sample_health_data):
        """Should calculate total distance in km."""
        metrics = extract_all_metrics(sample_health_data)
        totals = calculate_totals(metrics)

        assert 'distance_km' in totals
        assert totals['distance_km'] == 3.8  # 1.5 + 2.3

    @pytest.mark.unit
    def test_calculates_flights_climbed(self, sample_health_data):
        """Should calculate total flights climbed."""
        metrics = extract_all_metrics(sample_health_data)
        totals = calculate_totals(metrics)

        assert 'flights' in totals
        assert totals['flights'] == 8  # 3 + 5

    @pytest.mark.unit
    def test_handles_missing_metrics(self):
        """Should handle missing metrics gracefully."""
        metrics = {
            'step_count': {
                'units': 'count',
                'count': 1,
                'data': [{'qty': 100}]
            }
        }

        totals = calculate_totals(metrics)

        assert 'steps' in totals
        assert totals['steps'] == 100
        # Other metrics should not be present
        assert 'active_energy_kcal' not in totals

    @pytest.mark.unit
    def test_handles_empty_metrics(self):
        """Should handle empty metrics dict."""
        totals = calculate_totals({})

        assert isinstance(totals, dict)
        assert len(totals) == 0


class TestGetKeyReadings:
    """Tests for get_key_readings function."""

    @pytest.mark.unit
    def test_extracts_resting_heart_rate(self, sample_health_data):
        """Should extract resting heart rate."""
        metrics = extract_all_metrics(sample_health_data)
        readings = get_key_readings(metrics)

        assert 'resting_hr' in readings
        assert readings['resting_hr'] == 58

    @pytest.mark.unit
    def test_extracts_hrv_average(self, sample_health_data):
        """Should calculate average HRV."""
        metrics = extract_all_metrics(sample_health_data)
        readings = get_key_readings(metrics)

        assert 'hrv_avg' in readings
        assert readings['hrv_avg'] == 45  # (45 + 42 + 48) / 3

    @pytest.mark.unit
    def test_extracts_vo2_max(self, sample_health_data):
        """Should extract VO2 max."""
        metrics = extract_all_metrics(sample_health_data)
        readings = get_key_readings(metrics)

        assert 'vo2_max' in readings
        assert readings['vo2_max'] == 42.5

    @pytest.mark.unit
    def test_handles_missing_readings(self):
        """Should handle missing readings gracefully."""
        metrics = {
            'step_count': {
                'units': 'count',
                'count': 1,
                'data': [{'qty': 100}]
            }
        }

        readings = get_key_readings(metrics)

        assert isinstance(readings, dict)
        # No readings should be present for non-reading metrics
        assert 'resting_hr' not in readings

    @pytest.mark.unit
    def test_handles_empty_data_arrays(self):
        """Should handle metrics with empty data arrays."""
        metrics = {
            'resting_heart_rate': {
                'units': 'bpm',
                'count': 0,
                'data': []
            }
        }

        readings = get_key_readings(metrics)

        assert 'resting_hr' not in readings


class TestGetHeartRateStats:
    """Tests for get_heart_rate_stats function."""

    @pytest.mark.unit
    def test_calculates_hr_stats(self, sample_health_data):
        """Should calculate heart rate statistics."""
        metrics = extract_all_metrics(sample_health_data)
        hr_stats = get_heart_rate_stats(metrics)

        assert hr_stats is not None
        assert 'count' in hr_stats
        assert 'min' in hr_stats
        assert 'max' in hr_stats
        assert 'avg' in hr_stats

    @pytest.mark.unit
    def test_hr_stats_values(self, sample_health_data):
        """Should calculate correct HR statistics."""
        metrics = extract_all_metrics(sample_health_data)
        hr_stats = get_heart_rate_stats(metrics)

        assert hr_stats['count'] == 5
        assert hr_stats['min'] == 65
        assert hr_stats['max'] == 140
        assert hr_stats['avg'] == 96  # (65 + 72 + 130 + 140 + 75) / 5

    @pytest.mark.unit
    def test_returns_none_for_missing_heart_rate(self):
        """Should return None when heart rate data is missing."""
        metrics = {
            'step_count': {
                'units': 'count',
                'count': 1,
                'data': [{'qty': 100}]
            }
        }

        hr_stats = get_heart_rate_stats(metrics)

        assert hr_stats is None

    @pytest.mark.unit
    def test_returns_none_for_empty_heart_rate(self):
        """Should return None when heart rate data is empty."""
        metrics = {
            'heart_rate': {
                'units': 'bpm',
                'count': 0,
                'data': []
            }
        }

        hr_stats = get_heart_rate_stats(metrics)

        assert hr_stats is None

    @pytest.mark.unit
    def test_handles_missing_qty_fields(self):
        """Should handle heart rate entries without qty field."""
        metrics = {
            'heart_rate': {
                'units': 'bpm',
                'count': 3,
                'data': [
                    {'qty': 70},
                    {},  # Missing qty
                    {'qty': 80}
                ]
            }
        }

        hr_stats = get_heart_rate_stats(metrics)

        assert hr_stats is not None
        assert hr_stats['count'] == 2  # Only counts entries with qty
        assert hr_stats['avg'] == 75  # (70 + 80) / 2


class TestDataProcessingPipeline:
    """Integration tests for full data processing pipeline."""

    @pytest.mark.integration
    def test_full_processing_pipeline(self, sample_health_data):
        """Test complete pipeline from extraction to statistics."""
        # Extract
        metrics = extract_all_metrics(sample_health_data)
        assert metrics is not None

        # Calculate totals
        totals = calculate_totals(metrics)
        assert totals['steps'] == 220

        # Get readings
        readings = get_key_readings(metrics)
        assert readings['resting_hr'] == 58

        # Get HR stats
        hr_stats = get_heart_rate_stats(metrics)
        assert hr_stats['avg'] == 96

    @pytest.mark.integration
    def test_pipeline_with_partial_data(self):
        """Test pipeline with incomplete health data."""
        partial_data = {
            'exportDate': '2026-01-25 23:59:59 +0000',
            'data': {
                'metrics': [
                    {
                        'name': 'step_count',
                        'units': 'count',
                        'data': [{'qty': 5000}]
                    }
                ]
            }
        }

        metrics = extract_all_metrics(partial_data)
        totals = calculate_totals(metrics)
        readings = get_key_readings(metrics)
        hr_stats = get_heart_rate_stats(metrics)

        # Should handle partial data
        assert metrics is not None
        assert totals['steps'] == 5000
        assert isinstance(readings, dict)
        assert hr_stats is None  # No HR data


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.unit
    def test_handles_zero_quantities(self):
        """Should handle zero quantities correctly."""
        metrics = {
            'step_count': {
                'units': 'count',
                'count': 2,
                'data': [
                    {'qty': 0},
                    {'qty': 0}
                ]
            }
        }

        totals = calculate_totals(metrics)

        assert totals['steps'] == 0

    @pytest.mark.unit
    def test_handles_negative_quantities(self):
        """Should handle negative quantities (shouldn't happen but test anyway)."""
        metrics = {
            'step_count': {
                'units': 'count',
                'count': 2,
                'data': [
                    {'qty': 100},
                    {'qty': -50}  # Anomaly
                ]
            }
        }

        totals = calculate_totals(metrics)

        assert totals['steps'] == 50

    @pytest.mark.unit
    def test_handles_very_large_quantities(self):
        """Should handle very large quantities."""
        metrics = {
            'step_count': {
                'units': 'count',
                'count': 1,
                'data': [{'qty': 1000000}]
            }
        }

        totals = calculate_totals(metrics)

        assert totals['steps'] == 1000000

    @pytest.mark.unit
    def test_handles_float_vs_int_quantities(self):
        """Should handle both float and int quantities."""
        metrics = {
            'step_count': {
                'units': 'count',
                'count': 3,
                'data': [
                    {'qty': 100},    # int
                    {'qty': 50.5},   # float
                    {'qty': '30'}    # string
                ]
            }
        }

        totals = calculate_totals(metrics)

        # Should convert all to numbers
        assert totals['steps'] == 180  # 100 + 50 + 30 (rounded)
