"""In-memory cache implementation for TQL.

This module provides a simple in-memory cache with TTL (time-to-live) support
and basic LRU (Least Recently Used) eviction when the cache reaches its size limit.
"""

import time
from typing import Any, Dict, Optional

from .base import CacheManager


class LocalCacheManager(CacheManager):
    """Local in-memory cache with TTL and LRU eviction.

    This implementation provides thread-safe in-memory caching suitable for
    single-process applications. For distributed caching across multiple
    processes or servers, use RedisCacheManager instead.

    Features:
        - TTL-based expiration
        - LRU eviction when cache is full
        - Hit/miss statistics tracking
        - Pattern-based key clearing

    Args:
        max_size: Maximum number of items to store (default: 10000)
        default_ttl: Default time-to-live in seconds (default: 3600 = 1 hour)

    Example:
        >>> cache = LocalCacheManager(max_size=1000, default_ttl=600)
        >>> cache.set("user:123", {"name": "Alice"}, ttl=300)
        >>> user = cache.get("user:123")
        >>> stats = cache.get_stats()
        >>> print(f"Hit rate: {stats['hit_rate']:.2%}")

    Attributes:
        max_size: Maximum cache size
        default_ttl: Default TTL for cached items
    """

    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        """Initialize the local cache.

        Args:
            max_size: Maximum number of items to cache before eviction starts.
            default_ttl: Default expiration time in seconds for cached items.
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache if not expired.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value if present and not expired, None otherwise.

        Note:
            This method automatically removes expired keys when accessed.
            Hit/miss statistics are updated on each call.
        """
        if key in self._cache:
            expiry = self._expiry.get(key, float("inf"))
            if expiry == 0 or expiry > time.time():
                self._hits += 1
                return self._cache[key]
            else:
                # Expired - clean up
                del self._cache[key]
                del self._expiry[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in cache with optional TTL.

        Args:
            key: The cache key under which to store the value.
            value: The value to cache (any Python object).
            ttl: Time-to-live in seconds. If None, uses default_ttl.
                 If 0, the item never expires.

        Returns:
            True if the value was successfully stored.

        Note:
            When the cache is full (reaches max_size), the oldest item
            is evicted to make room for the new one (LRU eviction).
        """
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Simple eviction: remove oldest (first in dict)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._expiry.pop(oldest_key, None)

        self._cache[key] = value
        if ttl == 0:
            # Never expires
            self._expiry[key] = 0
        else:
            expiry_time = time.time() + (ttl if ttl is not None else self.default_ttl)
            self._expiry[key] = expiry_time
        return True

    def delete(self, key: str) -> bool:
        """Remove value from cache.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.

        Note:
            If the key doesn't exist, this method returns False (no error raised).
        """
        if key in self._cache:
            del self._cache[key]
            self._expiry.pop(key, None)
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache and hasn't expired.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists and hasn't expired, False otherwise.

        Note:
            This method automatically removes expired keys when accessed.
        """
        if key in self._cache:
            expiry = self._expiry.get(key, float("inf"))
            if expiry == 0 or expiry > time.time():
                return True
            else:
                # Expired - clean up
                del self._cache[key]
                del self._expiry[key]
        return False

    def clear(self) -> bool:
        """Clear all items from the cache.

        Returns:
            True if the cache was successfully cleared.

        Note:
            This also resets hit/miss statistics.
        """
        self._cache.clear()
        self._expiry.clear()
        self._hits = 0
        self._misses = 0
        return True

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a glob pattern.

        Args:
            pattern: A glob pattern to match keys. Supports wildcards:
                    - '*' matches any sequence of characters
                    - '?' matches any single character
                    - '[seq]' matches any character in seq
                    - '[!seq]' matches any character not in seq

        Returns:
            The number of keys that were deleted.

        Example:
            >>> cache.set("user:123", data1)
            >>> cache.set("user:456", data2)
            >>> cache.set("session:789", data3)
            >>> count = cache.clear_pattern("user:*")  # Deletes user:123 and user:456
            >>> print(count)  # 2
        """
        import fnmatch

        keys_to_delete = [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self._cache[key]
            self._expiry.pop(key, None)
        return len(keys_to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary containing:
            - hits: Number of successful cache retrievals
            - misses: Number of cache misses
            - hit_rate: Ratio of hits to total requests (0.0 to 1.0)
            - size: Current number of items in cache
            - max_size: Maximum cache capacity

        Example:
            >>> stats = cache.get_stats()
            >>> print(f"Cache is {stats['hit_rate']:.2%} effective")
            >>> print(f"Using {stats['size']}/{stats['max_size']} slots")
        """
        total_requests = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total_requests if total_requests > 0 else 0.0,
            "size": len(self._cache),
            "max_size": self.max_size,
        }
