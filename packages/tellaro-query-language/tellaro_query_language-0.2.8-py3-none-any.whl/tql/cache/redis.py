"""Redis-based cache implementation."""

import json
from typing import Any, Dict, Optional

from .base import CacheManager

redis: Any
try:
    import redis
except ImportError:
    redis = None


class RedisCacheManager(CacheManager):
    """Redis-based distributed cache."""

    def __init__(self, redis_client, key_prefix: str = "tql:mutator:", default_ttl: int = 3600):
        if redis is None:
            raise ImportError("redis package is required for RedisCacheManager")
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """Create full Redis key with prefix."""
        return f"{self.key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis."""
        full_key = self._make_key(key)
        value = self.redis.get(full_key)
        if value:
            return json.loads(value)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in Redis with TTL.

        Returns:
            True if the value was successfully stored.
        """
        try:
            full_key = self._make_key(key)
            ttl = ttl or self.default_ttl
            self.redis.setex(full_key, ttl, json.dumps(value))
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Remove value from Redis.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        try:
            full_key = self._make_key(key)
            result = self.redis.delete(full_key)
            return result > 0
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis.

        Returns:
            True if the key exists, False otherwise.
        """
        try:
            full_key = self._make_key(key)
            return self.redis.exists(full_key) > 0
        except Exception:
            return False

    def clear(self) -> bool:
        """Clear all keys in the Redis database.

        Returns:
            True if the cache was successfully cleared.
        """
        try:
            self.redis.flushdb()
            return True
        except Exception:
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        full_pattern = self._make_key(pattern)
        keys = list(self.redis.scan_iter(match=full_pattern))
        if keys:
            return self.redis.delete(*keys)
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics from Redis INFO."""
        info = self.redis.info()
        return {
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
                if (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) > 0
                else 0
            ),
            "used_memory": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
        }
