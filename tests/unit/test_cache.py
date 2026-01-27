"""
Tests for the caching layer.

These tests verify:
- Cache storage and retrieval
- Automatic invalidation
- Source file change detection
- Cache statistics
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from health_analytics.cache import DataCache, CacheEntry, get_cache, cached_json_read


class TestCacheBasics:
    """Tests for basic cache operations."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a cache with a temp directory."""
        return DataCache(cache_dir=tmp_path / ".cache", max_age_hours=24)

    @pytest.mark.unit
    def test_cache_dir_created(self, tmp_path):
        """Cache should create its directory."""
        cache_dir = tmp_path / "test_cache"
        cache = DataCache(cache_dir=cache_dir)

        assert cache_dir.exists()

    @pytest.mark.unit
    def test_set_and_get(self, cache):
        """Should store and retrieve values."""
        data = {'key': 'value', 'number': 42}
        cache.set('test_key', data)

        retrieved = cache.get('test_key')
        assert retrieved == data

    @pytest.mark.unit
    def test_get_missing_returns_none(self, cache):
        """Should return None for missing keys."""
        result = cache.get('nonexistent_key')
        assert result is None

    @pytest.mark.unit
    def test_set_returns_true(self, cache):
        """Should return True on successful set."""
        result = cache.set('key', {'data': 'value'})
        assert result is True

    @pytest.mark.unit
    def test_delete(self, cache):
        """Should delete cache entries."""
        cache.set('to_delete', {'data': 'value'})
        assert cache.get('to_delete') is not None

        deleted = cache.delete('to_delete')
        assert deleted is True
        assert cache.get('to_delete') is None

    @pytest.mark.unit
    def test_delete_nonexistent(self, cache):
        """Should return False when deleting nonexistent key."""
        result = cache.delete('nonexistent')
        assert result is False

    @pytest.mark.unit
    def test_clear(self, cache):
        """Should clear all entries."""
        cache.set('key1', {'data': 1})
        cache.set('key2', {'data': 2})
        cache.set('key3', {'data': 3})

        count = cache.clear()
        assert count == 3

        assert cache.get('key1') is None
        assert cache.get('key2') is None
        assert cache.get('key3') is None


class TestCacheInvalidation:
    """Tests for cache invalidation."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a cache with a short max age."""
        return DataCache(cache_dir=tmp_path / ".cache", max_age_hours=1)

    @pytest.mark.unit
    def test_source_file_change_invalidates(self, cache, tmp_path):
        """Should invalidate when source file changes."""
        source_file = tmp_path / "source.json"
        source_file.write_text('{"original": true}')

        # Cache with source file tracking
        cache.set('tracked', {'cached': True}, source_path=source_file)

        # Should retrieve from cache
        assert cache.get('tracked', source_path=source_file) == {'cached': True}

        # Modify source file
        time.sleep(0.1)  # Ensure different mtime
        source_file.write_text('{"modified": true}')

        # Should be invalidated
        assert cache.get('tracked', source_path=source_file) is None

    @pytest.mark.unit
    def test_max_age_invalidation(self, tmp_path):
        """Should invalidate entries older than max_age."""
        # Create cache with very short max age
        cache = DataCache(cache_dir=tmp_path / ".cache", max_age_hours=0)

        cache.set('old_data', {'data': 'value'})

        # Should be immediately invalid due to 0 hour max age
        time.sleep(0.01)
        result = cache.get('old_data')
        assert result is None


class TestCacheStatistics:
    """Tests for cache statistics."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a cache for testing stats."""
        return DataCache(cache_dir=tmp_path / ".cache")

    @pytest.mark.unit
    def test_stats_structure(self, cache):
        """Should return properly structured stats."""
        stats = cache.get_stats()

        assert 'entries' in stats
        assert 'total_size_mb' in stats
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'invalidations' in stats
        assert 'hit_rate' in stats
        assert 'cache_dir' in stats

    @pytest.mark.unit
    def test_hit_miss_tracking(self, cache):
        """Should track hits and misses."""
        # Initial miss
        cache.get('missing')
        stats = cache.get_stats()
        assert stats['misses'] == 1

        # Set and hit
        cache.set('existing', {'data': 'value'})
        cache.get('existing')
        stats = cache.get_stats()
        assert stats['hits'] == 1

    @pytest.mark.unit
    def test_entry_count(self, cache):
        """Should count entries correctly."""
        cache.set('entry1', {'data': 1})
        cache.set('entry2', {'data': 2})

        stats = cache.get_stats()
        assert stats['entries'] == 2


class TestCacheDecorator:
    """Tests for the @cached decorator."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a cache for testing decorator."""
        return DataCache(cache_dir=tmp_path / ".cache")

    @pytest.mark.unit
    def test_decorator_caches_result(self, cache):
        """Decorator should cache function results."""
        call_count = [0]

        @cache.cached(lambda x: f'compute_{x}')
        def expensive_compute(x):
            call_count[0] += 1
            return {'result': x * 2}

        # First call computes
        result1 = expensive_compute(5)
        assert result1 == {'result': 10}
        assert call_count[0] == 1

        # Second call uses cache
        result2 = expensive_compute(5)
        assert result2 == {'result': 10}
        assert call_count[0] == 1  # Not called again

    @pytest.mark.unit
    def test_decorator_different_args(self, cache):
        """Decorator should cache different args separately."""
        @cache.cached(lambda x: f'compute_{x}')
        def compute(x):
            return {'result': x * 2}

        result1 = compute(5)
        result2 = compute(10)

        assert result1 == {'result': 10}
        assert result2 == {'result': 20}


class TestCachedJsonRead:
    """Tests for cached_json_read helper."""

    @pytest.fixture
    def json_file(self, tmp_path):
        """Create a test JSON file."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{"key": "value", "number": 42}')
        return file_path

    @pytest.mark.unit
    def test_reads_json_file(self, json_file, tmp_path, monkeypatch):
        """Should read and cache JSON file."""
        # Use a temp cache directory
        monkeypatch.setattr('health_analytics.cache._cache', None)

        result = cached_json_read(json_file)

        assert result == {'key': 'value', 'number': 42}

    @pytest.mark.unit
    def test_returns_none_for_missing_file(self, tmp_path, monkeypatch):
        """Should return None for missing files."""
        monkeypatch.setattr('health_analytics.cache._cache', None)

        missing_file = tmp_path / "nonexistent.json"
        result = cached_json_read(missing_file)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_invalid_json(self, tmp_path, monkeypatch):
        """Should return None for invalid JSON."""
        monkeypatch.setattr('health_analytics.cache._cache', None)

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ not valid json }")

        result = cached_json_read(invalid_file)

        assert result is None


class TestGlobalCache:
    """Tests for global cache instance."""

    @pytest.mark.unit
    def test_get_cache_returns_instance(self):
        """Should return a DataCache instance."""
        cache = get_cache()
        assert isinstance(cache, DataCache)

    @pytest.mark.unit
    def test_get_cache_singleton(self, monkeypatch):
        """Should return same instance on repeated calls."""
        # Reset global cache
        monkeypatch.setattr('health_analytics.cache._cache', None)

        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2
