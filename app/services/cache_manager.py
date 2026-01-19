import time
from typing import Dict, Optional, Tuple
from threading import Lock
from collections import OrderedDict
import imagehash
from app.config import settings


class CacheEntry:
    """Represents a cached diagnosis."""

    def __init__(self, data: Dict, ttl: int):
        self.data = data
        self.created_at = time.time()
        self.ttl = ttl
        self.hit_count = 0

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.created_at) > self.ttl

    def get(self) -> Dict:
        """Get cached data and increment hit count."""
        self.hit_count += 1
        return self.data


class LRUCache:
    """Thread-safe LRU cache with TTL."""

    def __init__(self, max_size: int, default_ttl: int):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> Optional[Dict]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            return entry.get()

    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Optional TTL override
        """
        with self._lock:
            # Remove if exists
            if key in self._cache:
                del self._cache[key]

            # Create new entry
            entry = CacheEntry(value, ttl or self.default_ttl)
            self._cache[key] = entry

            # Move to end
            self._cache.move_to_end(key)

            # Evict oldest if over size
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        removed = 0

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]
                removed += 1

        return removed


class CacheManager:
    """Manages two-level caching: exact match and perceptual hash."""

    def __init__(self):
        # Exact match cache (SHA256)
        self.exact_cache = LRUCache(
            max_size=settings.max_cache_entries,
            default_ttl=settings.cache_ttl_seconds
        )

        # Perceptual hash cache (similar images)
        self.perceptual_cache = LRUCache(
            max_size=settings.max_cache_entries,
            default_ttl=settings.perceptual_cache_ttl_seconds
        )

        self._stats = {
            'exact_hits': 0,
            'perceptual_hits': 0,
            'misses': 0
        }
        self._stats_lock = Lock()

    def get_exact(self, sha256_hash: str, question: str = "") -> Optional[Dict]:
        """
        Get cached diagnosis by exact hash match.

        Args:
            sha256_hash: SHA256 hash of image
            question: Optional question for cache key

        Returns:
            Cached diagnosis or None
        """
        cache_key = self._make_exact_key(sha256_hash, question)
        result = self.exact_cache.get(cache_key)

        if result is not None:
            with self._stats_lock:
                self._stats['exact_hits'] += 1

        return result

    def get_perceptual(self, phash: str, threshold: int = 5) -> Optional[Dict]:
        """
        Get cached diagnosis by perceptual hash (similar images).

        Args:
            phash: Perceptual hash string
            threshold: Maximum Hamming distance for match

        Returns:
            Cached diagnosis or None
        """
        # Try exact perceptual match first
        result = self.perceptual_cache.get(phash)

        if result is not None:
            with self._stats_lock:
                self._stats['perceptual_hits'] += 1
            return result

        # Try similar matches (within threshold)
        # Note: In production, this would need a more efficient similarity search
        # For now, we'll just check exact matches to keep it simple

        return None

    def set(self, sha256_hash: str, phash: str, diagnosis: Dict, question: str = "") -> None:
        """
        Cache a diagnosis in both exact and perceptual caches.

        Args:
            sha256_hash: SHA256 hash of image
            phash: Perceptual hash
            diagnosis: Diagnosis data
            question: Optional question for cache key
        """
        # Store in exact cache
        exact_key = self._make_exact_key(sha256_hash, question)
        self.exact_cache.set(exact_key, diagnosis)

        # Store in perceptual cache (only for initial diagnoses, not follow-up questions)
        if not question:
            self.perceptual_cache.set(phash, diagnosis)

    def record_miss(self) -> None:
        """Record a cache miss."""
        with self._stats_lock:
            self._stats['misses'] += 1

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self._stats_lock:
            total_requests = sum(self._stats.values())
            hit_rate = 0.0

            if total_requests > 0:
                total_hits = self._stats['exact_hits'] + self._stats['perceptual_hits']
                hit_rate = (total_hits / total_requests) * 100

            return {
                **self._stats,
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 2),
                'exact_cache_size': self.exact_cache.size(),
                'perceptual_cache_size': self.perceptual_cache.size()
            }

    def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired entries from both caches."""
        return {
            'exact_removed': self.exact_cache.cleanup_expired(),
            'perceptual_removed': self.perceptual_cache.cleanup_expired()
        }

    def clear_all(self) -> None:
        """Clear both caches."""
        self.exact_cache.clear()
        self.perceptual_cache.clear()

        with self._stats_lock:
            self._stats = {
                'exact_hits': 0,
                'perceptual_hits': 0,
                'misses': 0
            }

    @staticmethod
    def _make_exact_key(sha256_hash: str, question: str = "") -> str:
        """Create cache key from hash and optional question."""
        if question:
            return f"{sha256_hash}:{question}"
        return sha256_hash


# Global cache manager instance
cache_manager = CacheManager()
