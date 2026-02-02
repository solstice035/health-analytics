#!/usr/bin/env python3
"""
Hevy API Helper - Fetch workout data from Hevy.

Provides functions for:
- Authenticating with Hevy API
- Fetching workouts for a user
- Caching API responses
- Rate limiting and error handling

Usage:
    from hevy_helper import HevyClient, fetch_and_cache_workouts

    # Direct API access
    client = HevyClient()
    data = client.get_workouts('username')

    # With caching (recommended)
    data = fetch_and_cache_workouts('username')
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import requests
except ImportError:
    print("Error: 'requests' package not installed. Run: pip install requests")
    sys.exit(1)

from health_analytics.config import config
from health_analytics.cache import get_cache

# Hevy API Configuration
HEVY_BASE_URL = "https://api.hevyapp.com"
DEFAULT_RATE_LIMIT_DELAY = 1.0  # seconds between requests


class HevyAPIError(Exception):
    """Custom exception for Hevy API errors."""
    pass


class HevyClient:
    """
    Client for interacting with the Hevy API.

    Handles authentication, rate limiting, and retry logic.
    """

    def __init__(
        self,
        auth_token: Optional[str] = None,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
        base_url: str = HEVY_BASE_URL
    ):
        """
        Initialize the Hevy API client.

        Args:
            auth_token: Hevy auth token (defaults to HEVY_API env var)
            rate_limit_delay: Seconds to wait between requests
            base_url: API base URL
        """
        self.auth_token = auth_token or os.environ.get('HEVY_API')
        self.rate_limit_delay = rate_limit_delay
        self.base_url = base_url
        self._last_request_time = 0.0

        if not self.auth_token:
            raise HevyAPIError(
                "HEVY_API token not found. Add it to .env file:\n"
                "  HEVY_API=your-auth-token"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get headers required for API requests."""
        return {
            "api-key": self.auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def get_workouts(
        self,
        max_retries: int = 3,
        timeout: int = 30,
        page: int = 1,
        page_size: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch workouts for the authenticated user.

        Args:
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            page: Page number for pagination
            page_size: Number of workouts per page

        Returns:
            API response data or None if failed

        Raises:
            HevyAPIError: For non-retryable errors
        """
        url = f"{self.base_url}/v1/workouts"
        params = {"page": page, "pageSize": page_size}

        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=timeout
                )

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 401:
                    raise HevyAPIError(
                        "Authentication failed. Check your HEVY_API token."
                    )

                elif response.status_code == 404:
                    raise HevyAPIError(
                        "Workouts endpoint not found."
                    )

                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = int(response.headers.get('Retry-After', 60))
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                elif response.status_code >= 500:
                    # Server error - exponential backoff
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        print(f"  Server error, retrying in {wait}s...")
                        time.sleep(wait)
                        continue
                    raise HevyAPIError(
                        f"Server error: {response.status_code}"
                    )

                else:
                    raise HevyAPIError(
                        f"API error: {response.status_code} - {response.text}"
                    )

            except requests.Timeout:
                if attempt < max_retries - 1:
                    print(f"  Request timeout, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                raise HevyAPIError("Request timeout after all retries")

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise HevyAPIError(f"Request failed: {e}")

        return None

    def get_exercise_templates(
        self,
        max_retries: int = 3,
        timeout: int = 30,
        page: int = 1,
        page_size: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch exercise templates from Hevy API.

        Args:
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            page: Page number for pagination
            page_size: Number of templates per page

        Returns:
            API response data or None if failed
        """
        url = f"{self.base_url}/v1/exercise_templates"
        params = {"page": page, "pageSize": page_size}

        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=timeout
                )

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 401:
                    raise HevyAPIError(
                        "Authentication failed. Check your HEVY_API token."
                    )

                elif response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', 60))
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                elif response.status_code >= 500:
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        time.sleep(wait)
                        continue
                    raise HevyAPIError(f"Server error: {response.status_code}")

                else:
                    raise HevyAPIError(
                        f"API error: {response.status_code} - {response.text}"
                    )

            except requests.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise HevyAPIError("Request timeout after all retries")

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise HevyAPIError(f"Request failed: {e}")

        return None


def fetch_and_cache_exercise_templates(
    force_refresh: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch exercise templates and build a lookup map.

    Returns a dict mapping exercise_template_id to template data including
    primary_muscle_group and secondary_muscle_groups.

    Args:
        force_refresh: If True, bypass cache

    Returns:
        Dict mapping template_id to template data
    """
    cache = get_cache()
    cache_key = "hevy_exercise_templates"

    # Try cache first
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached:
            return cached

    # Fetch from API (paginated)
    client = HevyClient()
    template_map = {}
    page = 1

    print("  Fetching exercise templates...")
    while True:
        data = client.get_exercise_templates(page=page)
        if not data:
            break

        templates = data.get('exercise_templates', [])
        for t in templates:
            template_id = t.get('id')
            if template_id:
                template_map[template_id] = {
                    'title': t.get('title', ''),
                    'type': t.get('type', ''),
                    'primary_muscle_group': t.get('primary_muscle_group', 'other'),
                    'secondary_muscle_groups': t.get('secondary_muscle_groups', []),
                    'is_custom': t.get('is_custom', False)
                }

        page_count = data.get('page_count', 1)
        if page >= page_count:
            break
        page += 1

    if template_map:
        cache.set(cache_key, template_map)
        print(f"  Cached {len(template_map)} exercise templates")

    return template_map


def fetch_and_cache_workouts(
    force_refresh: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Fetch workouts with caching.

    Uses the DataCache to avoid repeated API calls. Cache is invalidated
    after 24 hours or when force_refresh is True.

    Args:
        force_refresh: If True, bypass cache

    Returns:
        Workout data or None if failed
    """
    cache = get_cache()
    cache_key = "hevy_workouts"

    # Try cache first (unless forcing refresh)
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached:
            return cached

    # Fetch from API (may fetch multiple pages)
    client = HevyClient()
    all_workouts = []
    page = 1

    while True:
        data = client.get_workouts(page=page)
        if not data:
            break

        workouts = data.get('workouts', [])
        all_workouts.extend(workouts)

        # Check if there are more pages
        page_count = data.get('page_count', 1)
        if page >= page_count:
            break
        page += 1

    result = {'workouts': all_workouts}

    if all_workouts:
        # Store in cache
        cache.set(cache_key, result)

    return result


def get_hevy_status() -> Dict[str, Any]:
    """
    Get the status of Hevy integration.

    Returns:
        Dict with configuration and connection status
    """
    status = {
        'configured': False,
        'api_token_set': bool(os.environ.get('HEVY_API')),
        'connection': 'unknown',
        'last_sync': None,
        'workout_count': 0
    }

    status['configured'] = status['api_token_set']

    # Check cache for last sync info
    if status['configured']:
        cache = get_cache()
        cache_key = "hevy_workouts"
        cached = cache.get(cache_key)

        if cached:
            status['connection'] = 'cached'
            workouts = cached.get('workouts', [])
            if isinstance(workouts, list):
                status['workout_count'] = len(workouts)

    return status


if __name__ == "__main__":
    # Test the helper when run directly
    import argparse

    parser = argparse.ArgumentParser(description="Hevy API Helper")
    parser.add_argument('--status', action='store_true', help="Show status")
    parser.add_argument('--sync', action='store_true', help="Sync workouts")
    parser.add_argument('--force', action='store_true', help="Force refresh")
    args = parser.parse_args()

    if args.status:
        print("Hevy Integration Status:")
        status = get_hevy_status()
        for key, value in status.items():
            icon = "✓" if value else "✗" if isinstance(value, bool) else " "
            print(f"  {icon} {key}: {value}")

    elif args.sync:
        print("Syncing workouts from Hevy...")
        try:
            data = fetch_and_cache_workouts(force_refresh=args.force)
            if data:
                workouts = data.get('workouts', [])
                print(f"✓ Synced {len(workouts)} workouts")
                if workouts:
                    print(f"  Latest: {workouts[0].get('title', 'Unknown')}")
            else:
                print("✗ No data returned")
        except HevyAPIError as e:
            print(f"✗ Error: {e}")

    else:
        parser.print_help()
