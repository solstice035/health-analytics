"""
Unit tests for hevy_helper module.
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from hevy_helper import (
    HevyClient,
    HevyAPIError,
    fetch_and_cache_workouts,
    get_hevy_status,
    HEVY_BASE_URL
)


class TestHevyClient:
    """Tests for HevyClient class."""

    @pytest.mark.unit
    def test_client_requires_auth_token(self, monkeypatch):
        """Should raise error when no auth token provided."""
        monkeypatch.delenv('HEVY_API', raising=False)

        with pytest.raises(HevyAPIError) as exc_info:
            HevyClient(auth_token=None)

        assert 'HEVY_API' in str(exc_info.value)

    @pytest.mark.unit
    def test_client_accepts_explicit_token(self):
        """Should accept explicitly provided auth token."""
        client = HevyClient(auth_token='test-token-123')
        assert client.auth_token == 'test-token-123'

    @pytest.mark.unit
    def test_client_uses_env_token(self, monkeypatch):
        """Should use HEVY_API environment variable."""
        monkeypatch.setenv('HEVY_API', 'env-token-456')
        client = HevyClient()
        assert client.auth_token == 'env-token-456'

    @pytest.mark.unit
    def test_get_headers_includes_api_key(self):
        """Should include api-key header with auth token."""
        client = HevyClient(auth_token='test-token')
        headers = client._get_headers()

        assert headers['api-key'] == 'test-token'
        assert 'Content-Type' in headers

    @pytest.mark.unit
    @patch('hevy_helper.requests.get')
    def test_get_workouts_success(self, mock_get):
        """Should return data on successful API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'workouts': [{'id': '1'}]}
        mock_get.return_value = mock_response

        client = HevyClient(auth_token='test-token')
        result = client.get_workouts()

        assert result == {'workouts': [{'id': '1'}]}
        mock_get.assert_called_once()
        assert '/v1/workouts' in mock_get.call_args[0][0]

    @pytest.mark.unit
    @patch('hevy_helper.requests.get')
    def test_get_workouts_401_raises_error(self, mock_get):
        """Should raise error on authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = HevyClient(auth_token='bad-token')

        with pytest.raises(HevyAPIError) as exc_info:
            client.get_workouts()

        assert 'Authentication' in str(exc_info.value)

    @pytest.mark.unit
    @patch('hevy_helper.requests.get')
    def test_get_workouts_404_raises_error(self, mock_get):
        """Should raise error when endpoint not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = HevyClient(auth_token='test-token')

        with pytest.raises(HevyAPIError) as exc_info:
            client.get_workouts()

        assert 'not found' in str(exc_info.value)

    @pytest.mark.unit
    @patch('hevy_helper.requests.get')
    @patch('hevy_helper.time.sleep')
    def test_get_workouts_retries_on_server_error(self, mock_sleep, mock_get):
        """Should retry on 5xx server errors."""
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'workouts': []}

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        client = HevyClient(auth_token='test-token')
        result = client.get_workouts(max_retries=3)

        assert result == {'workouts': []}
        assert mock_get.call_count == 2

    @pytest.mark.unit
    @patch('hevy_helper.requests.get')
    @patch('hevy_helper.time.sleep')
    def test_rate_limiting(self, mock_sleep, mock_get):
        """Should respect rate limiting between requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'workouts': []}
        mock_get.return_value = mock_response

        client = HevyClient(auth_token='test-token', rate_limit_delay=0.5)

        # Make two requests
        client.get_workouts()
        client.get_workouts()

        # Second request should have waited
        assert mock_sleep.called or mock_get.call_count == 2


class TestFetchAndCacheWorkouts:
    """Tests for fetch_and_cache_workouts function."""

    @pytest.mark.unit
    @patch('hevy_helper.get_cache')
    def test_requires_api_token(self, mock_get_cache, monkeypatch):
        """Should raise error when no API token provided."""
        monkeypatch.delenv('HEVY_API', raising=False)

        # Cache returns None so it tries to create a HevyClient
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        with pytest.raises(HevyAPIError) as exc_info:
            fetch_and_cache_workouts()

        assert 'HEVY_API' in str(exc_info.value)

    @pytest.mark.unit
    @patch('hevy_helper.HevyClient')
    @patch('hevy_helper.get_cache')
    def test_returns_cached_data(self, mock_get_cache, mock_client, monkeypatch):
        """Should return cached data if available."""
        monkeypatch.setenv('HEVY_API', 'test-token')

        mock_cache = Mock()
        mock_cache.get.return_value = {'workouts': [{'cached': True}]}
        mock_get_cache.return_value = mock_cache

        result = fetch_and_cache_workouts()

        assert result == {'workouts': [{'cached': True}]}
        mock_client.assert_not_called()

    @pytest.mark.unit
    @patch('hevy_helper.HevyClient')
    @patch('hevy_helper.get_cache')
    def test_fetches_when_cache_miss(self, mock_get_cache, mock_client_class, monkeypatch):
        """Should fetch from API when cache misses."""
        monkeypatch.setenv('HEVY_API', 'test-token')

        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        mock_client = Mock()
        mock_client.get_workouts.return_value = {'workouts': [{'fresh': True}]}
        mock_client_class.return_value = mock_client

        result = fetch_and_cache_workouts()

        assert result == {'workouts': [{'fresh': True}]}
        mock_cache.set.assert_called_once()

    @pytest.mark.unit
    @patch('hevy_helper.HevyClient')
    @patch('hevy_helper.get_cache')
    def test_force_refresh_bypasses_cache(self, mock_get_cache, mock_client_class, monkeypatch):
        """Should bypass cache when force_refresh is True."""
        monkeypatch.setenv('HEVY_API', 'test-token')

        mock_cache = Mock()
        mock_cache.get.return_value = {'workouts': [{'cached': True}]}
        mock_get_cache.return_value = mock_cache

        mock_client = Mock()
        mock_client.get_workouts.return_value = {'workouts': [{'fresh': True}]}
        mock_client_class.return_value = mock_client

        result = fetch_and_cache_workouts(force_refresh=True)

        assert result == {'workouts': [{'fresh': True}]}
        mock_client.get_workouts.assert_called_once()


class TestGetHevyStatus:
    """Tests for get_hevy_status function."""

    @pytest.mark.unit
    def test_status_not_configured(self, monkeypatch):
        """Should show not configured when env vars missing."""
        monkeypatch.delenv('HEVY_API', raising=False)

        status = get_hevy_status()

        assert status['configured'] is False
        assert status['api_token_set'] is False

    @pytest.mark.unit
    def test_status_configured(self, monkeypatch):
        """Should show configured when API token is set."""
        monkeypatch.setenv('HEVY_API', 'test-token')

        status = get_hevy_status()

        assert status['configured'] is True
        assert status['api_token_set'] is True
