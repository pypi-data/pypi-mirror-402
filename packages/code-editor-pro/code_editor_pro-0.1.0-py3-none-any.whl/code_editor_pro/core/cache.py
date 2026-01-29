"""Intelligent caching for token optimization."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class AnalysisCache:
    """In-memory cache for analysis results with TTL."""

    def __init__(self, ttl_seconds: int = 900):  # 15 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def get(self, file_path: Path, operation: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result if valid.

        Args:
            file_path: Path to file
            operation: Operation type (inspect, analyze, dependencies)

        Returns:
            Cached result or None if expired/missing
        """
        try:
            # Generate cache key
            key = self._cache_key(file_path, operation)

            if key not in self.cache:
                return None

            entry = self.cache[key]

            # Check TTL
            age = time.time() - entry["timestamp"]
            if age > self.ttl:
                logger.debug(f"Cache expired for {file_path}:{operation}")
                del self.cache[key]
                return None

            # Validate file hasn't changed
            if not self._is_file_unchanged(file_path, entry["file_hash"]):
                logger.debug(f"File changed, invalidating cache for {file_path}")
                del self.cache[key]
                return None

            logger.debug(f"Cache hit for {file_path}:{operation}")
            return entry["result"]

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self, file_path: Path, operation: str, result: Dict[str, Any]
    ) -> None:
        """
        Store result in cache.

        Args:
            file_path: Path to file
            operation: Operation type
            result: Result to cache
        """
        try:
            key = self._cache_key(file_path, operation)

            self.cache[key] = {
                "result": result,
                "timestamp": time.time(),
                "file_hash": self._file_hash(file_path),
            }

            # Cleanup old entries if cache is too large
            if len(self.cache) > 1000:
                self._cleanup_old_entries()

            logger.debug(f"Cached result for {file_path}:{operation}")

        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def invalidate(self, file_path: Path) -> None:
        """
        Invalidate all cache entries for a file.

        Args:
            file_path: Path to file
        """
        try:
            keys_to_delete = [
                key for key in self.cache.keys() if str(file_path) in key
            ]

            for key in keys_to_delete:
                del self.cache[key]

            logger.debug(f"Invalidated cache for {file_path}")

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
        logger.debug("Cache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        total_size = sum(
            len(json.dumps(entry["result"])) for entry in self.cache.values()
        )

        return {
            "entries": total_entries,
            "size_bytes": total_size,
            "size_mb": round(total_size / 1024 / 1024, 2),
            "ttl_seconds": self.ttl,
        }

    def _cache_key(self, file_path: Path, operation: str) -> str:
        """Generate cache key."""
        return f"{file_path}:{operation}"

    def _file_hash(self, file_path: Path) -> str:
        """Calculate file hash for change detection."""
        try:
            # Use file size + mtime for fast check
            stat = file_path.stat()
            return f"{stat.st_size}:{stat.st_mtime}"
        except Exception:
            return ""

    def _is_file_unchanged(self, file_path: Path, old_hash: str) -> bool:
        """Check if file has changed."""
        return self._file_hash(file_path) == old_hash

    def _cleanup_old_entries(self) -> None:
        """Remove oldest entries when cache is full."""
        # Sort by timestamp
        sorted_keys = sorted(
            self.cache.keys(), key=lambda k: self.cache[k]["timestamp"]
        )

        # Remove oldest 20%
        to_remove = int(len(sorted_keys) * 0.2)
        for key in sorted_keys[:to_remove]:
            del self.cache[key]

        logger.debug(f"Cleaned up {to_remove} old cache entries")


# Global cache instance
_global_cache = AnalysisCache()


def get_cache() -> AnalysisCache:
    """Get global cache instance."""
    return _global_cache
