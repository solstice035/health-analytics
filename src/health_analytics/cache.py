"""
Caching layer for Health Analytics.

Provides disk-based caching for parsed health data to avoid re-parsing
large JSON files on each access. Supports:
- Automatic cache invalidation when source files change
- Configurable cache directory
- Memory-efficient storage
- Cache statistics and management

SECURITY NOTE: This module uses pickle for efficient serialization of
complex Python objects. The cache files are:
- Created only from data we parse ourselves (not untrusted sources)
- Stored in a local directory controlled by the application
- Never shared or exposed to external input

For caching user-provided or network data, use JSON serialization instead.

Usage:
    from health_analytics.cache import DataCache

    cache = DataCache()

    # Cache a parsed result
    cache.set('2026-01-25', parsed_data)

    # Get from cache (returns None if not found/stale)
    data = cache.get('2026-01-25', source_path='/path/to/source.json')

    # Or use the cached_json_read helper
    data = cached_json_read(Path('data.json'))
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, Callable, TypeVar
from dataclasses import dataclass, asdict
from functools import wraps

from health_analytics.config import config


@dataclass
class CacheEntry:
    """Metadata for a cached item."""
    key: str
    created_at: str  # ISO format for JSON serialization
    source_mtime: Optional[float] = None  # Source file modification time
    source_path: Optional[str] = None
    size_bytes: int = 0


class DataCache:
    """
    Disk-based cache for parsed health data.

    Automatically invalidates entries when source files are modified.
    Uses JSON for serialization to ensure safety and portability.
    """

    def __init__(self, cache_dir: Optional[Path] = None, max_age_hours: int = 24):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory for cache files (uses config default if not provided)
            max_age_hours: Maximum age of cache entries in hours (default 24)
        """
        self.cache_dir = cache_dir or config.cache_dir
        self.max_age = timedelta(hours=max_age_hours)
        self._ensure_cache_dir()
        self._stats = {'hits': 0, 'misses': 0, 'invalidations': 0}

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get the cache file path for a key."""
        # Use hash to create safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
        safe_key = ''.join(c if c.isalnum() or c in '-_' else '_' for c in key)[:32]
        return self.cache_dir / f"{safe_key}_{key_hash}.json"

    def _get_meta_path(self, key: str) -> Path:
        """Get the metadata file path for a key."""
        cache_path = self._get_cache_path(key)
        return cache_path.with_suffix('.meta.json')

    def _is_valid(self, key: str, source_path: Optional[Path] = None) -> bool:
        """
        Check if a cache entry is valid.

        Returns False if:
        - Entry doesn't exist
        - Entry is older than max_age
        - Source file has been modified since caching
        """
        cache_path = self._get_cache_path(key)
        meta_path = self._get_meta_path(key)

        if not cache_path.exists() or not meta_path.exists():
            return False

        try:
            with open(meta_path, 'r') as f:
                meta_dict = json.load(f)

            entry = CacheEntry(**meta_dict)
            created_at = datetime.fromisoformat(entry.created_at)

            # Check age
            if datetime.now() - created_at > self.max_age:
                self._stats['invalidations'] += 1
                return False

            # Check source file modification
            if source_path and source_path.exists():
                current_mtime = source_path.stat().st_mtime
                if entry.source_mtime and current_mtime > entry.source_mtime:
                    self._stats['invalidations'] += 1
                    return False

            return True

        except (json.JSONDecodeError, OSError, KeyError, ValueError):
            return False

    def get(self, key: str, source_path: Optional[Path] = None) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key
            source_path: Optional source file path for modification checking

        Returns:
            Cached value or None if not found/invalid
        """
        if not self._is_valid(key, source_path):
            self._stats['misses'] += 1
            return None

        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            self._stats['hits'] += 1
            return data
        except (json.JSONDecodeError, OSError):
            self._stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, source_path: Optional[Path] = None) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            source_path: Optional source file path for modification tracking

        Returns:
            True if successfully cached
        """
        cache_path = self._get_cache_path(key)
        meta_path = self._get_meta_path(key)

        try:
            # Write data
            with open(cache_path, 'w') as f:
                json.dump(value, f)

            # Write metadata
            entry = CacheEntry(
                key=key,
                created_at=datetime.now().isoformat(),
                source_mtime=source_path.stat().st_mtime if source_path and source_path.exists() else None,
                source_path=str(source_path) if source_path else None,
                size_bytes=cache_path.stat().st_size
            )

            with open(meta_path, 'w') as f:
                json.dump(asdict(entry), f)

            return True

        except (TypeError, OSError) as e:
            # Clean up partial files
            cache_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            return False

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_meta_path(key)

        deleted = False
        if cache_path.exists():
            cache_path.unlink()
            deleted = True
        if meta_path.exists():
            meta_path.unlink()
            deleted = True

        return deleted

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()
            count += 1

        return count // 2  # Divide by 2 since we have .json and .meta.json

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob('*.json'))
        # Filter out meta files for size calculation
        data_files = [f for f in cache_files if not f.name.endswith('.meta.json')]
        total_size = sum(f.stat().st_size for f in data_files if f.exists())
        entry_count = len(data_files)

        hit_rate = 0
        total_ops = self._stats['hits'] + self._stats['misses']
        if total_ops > 0:
            hit_rate = self._stats['hits'] / total_ops

        return {
            'entries': entry_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'invalidations': self._stats['invalidations'],
            'hit_rate': round(hit_rate * 100, 1),
            'cache_dir': str(self.cache_dir)
        }

    def cached(self, key_func: Optional[Callable] = None):
        """
        Decorator for caching function results.

        Args:
            key_func: Function to generate cache key from args/kwargs
                     If None, uses function name + str(args) + str(kwargs)

        Example:
            @cache.cached(lambda date: f'metrics_{date}')
            def get_metrics(date):
                return expensive_computation(date)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = f"{func.__name__}_{args}_{kwargs}"

                # Try cache first
                cached = self.get(key)
                if cached is not None:
                    return cached

                # Compute and cache
                result = func(*args, **kwargs)
                if result is not None:
                    self.set(key, result)

                return result

            return wrapper
        return decorator


# Global cache instance
_cache: Optional[DataCache] = None


def get_cache() -> DataCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache


def cached_json_read(file_path: Path) -> Optional[Dict]:
    """
    Read and parse a JSON file with caching.

    Uses the cache to avoid re-parsing unchanged files.
    Automatically invalidates when the source file changes.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data or None if file doesn't exist/is invalid
    """
    cache = get_cache()
    key = f"json_{file_path.name}"

    # Try cache first
    cached = cache.get(key, source_path=file_path)
    if cached is not None:
        return cached

    # Read and parse
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Cache the result
        cache.set(key, data, source_path=file_path)

        return data
    except (json.JSONDecodeError, OSError):
        return None


if __name__ == '__main__':
    # Demo usage
    cache = DataCache()

    print("Cache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
