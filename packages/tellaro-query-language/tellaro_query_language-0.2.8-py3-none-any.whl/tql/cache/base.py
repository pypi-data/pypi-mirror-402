"""Base cache infrastructure for TQL.

This module provides the base CacheManager class that defines the caching
interface used throughout TQL. Concrete implementations include LocalCacheManager
for in-memory caching and RedisCacheManager for distributed caching.
"""

from typing import Any, Dict, Optional


class CacheManager:
    """Base class for cache management.

    This class defines the interface for all cache implementations in TQL.
    Subclasses should override these methods to provide actual caching functionality.

    The base implementation provides no-op defaults that can be safely used when
    caching is disabled or not needed.

    Example:
        >>> cache = LocalCacheManager()
        >>> cache.set("user:123", {"name": "Alice", "age": 30}, ttl=3600)
        >>> user = cache.get("user:123")
        >>> cache.delete("user:123")
    """

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up. Should be a string identifier.

        Returns:
            The cached value if it exists and hasn't expired, None otherwise.

        Example:
            >>> value = cache.get("my_key")
            >>> if value is not None:
            ...     print(f"Found: {value}")
        """
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in the cache.

        Args:
            key: The cache key under which to store the value.
            value: The value to cache. Can be any Python object.
            ttl: Time-to-live in seconds. If None or 0, the value never expires.

        Returns:
            True if the value was successfully stored.

        Example:
            >>> cache.set("config", {"debug": True}, ttl=300)  # Cache for 5 minutes
            >>> cache.set("permanent", {"version": "1.0"})  # Never expires
        """
        return True

    def delete(self, key: str) -> bool:
        """Remove a value from the cache.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.

        Example:
            >>> cache.delete("expired_key")
        """
        return False

    def exists(self, key: str) -> bool:  # pylint: disable=unused-argument
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists and hasn't expired, False otherwise.

        Example:
            >>> if cache.exists("my_key"):
            ...     value = cache.get("my_key")
        """
        return False

    def clear(self) -> bool:
        """Clear all items from the cache.

        Returns:
            True if the cache was successfully cleared.

        Example:
            >>> cache.clear()
        """
        return True

    def clear_pattern(self, pattern: str) -> int:  # pylint: disable=unused-argument
        """Clear all keys matching a pattern.

        Args:
            pattern: A pattern string to match keys. Format depends on implementation.
                    For Redis: supports wildcards like "user:*" or "session:?123"
                    For Local: basic string matching

        Returns:
            The number of keys that were deleted.

        Example:
            >>> count = cache.clear_pattern("temp:*")
            >>> print(f"Cleared {count} temporary keys")
        """
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and metrics.

        Returns:
            Dictionary containing cache statistics such as:
            - hit_rate: Cache hit rate percentage
            - miss_rate: Cache miss rate percentage
            - size: Number of items in cache
            - memory_usage: Memory used by cache (if available)

        Example:
            >>> stats = cache.get_stats()
            >>> print(f"Hit rate: {stats.get('hit_rate', 0)}%")
        """
        return {}
