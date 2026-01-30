"""Cache manager for RSS feeds with incremental update support.
This module provides file-system based caching for RSS feeds,
supporting conditional requests (ETag/Last-Modified) and entry tracking.
"""

# import os
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any


class CacheManager:
    """Manager for RSS feed caching."""

    def __init__(
        self, cache_dir: str | Path | None = None, expire_days: int = 7
    ) -> None:
        """Initialize cache manager.
        Args:
            cache_dir: Directory for cache storage. If None, uses .cache/rss
            expire_days: Number of days before cache expires
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "information-composer" / "rss"
        self.cache_dir = Path(cache_dir)
        self.expire_days = expire_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cached(self, feed_url: str) -> dict[str, Any] | None:
        """Get cached feed data.
        Args:
            feed_url: URL of the feed
        Returns:
            Cached data dictionary or None if not found/expired
        """
        cache_file = self._get_cache_file(feed_url)
        if not cache_file.exists():
            return None
        try:
            with open(cache_file) as f:
                data = json.load(f)
            # Check expiration
            cached_time = datetime.fromisoformat(data.get("cached_at", ""))
            if datetime.now() - cached_time > timedelta(days=self.expire_days):
                return None
            return data
        except Exception:
            # If cache is corrupted, return None
            return None

    def save_cache(
        self,
        feed_url: str,
        feed_data: dict[str, Any],
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        """Save feed data to cache.
        Args:
            feed_url: URL of the feed
            feed_data: Feed data to cache
            etag: HTTP ETag for conditional requests
            last_modified: Last-Modified header
        """
        cache_file = self._get_cache_file(feed_url)
        cache_data = {
            "feed_url": feed_url,
            "cached_at": datetime.now().isoformat(),
            "etag": etag,
            "last_modified": last_modified,
            "data": feed_data,
            "entry_ids": self._extract_entry_ids(feed_data),
        }
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to save cache for {feed_url}: {e}")

    def get_new_entries(self, feed_url: str, current_entry_ids: list[str]) -> list[str]:
        """Get list of new entry IDs compared to cached version.
        Args:
            feed_url: URL of the feed
            current_entry_ids: List of current entry IDs
        Returns:
            List of new entry IDs not in cache
        """
        cached = self.get_cached(feed_url)
        if not cached:
            # No cache, all entries are new
            return current_entry_ids
        cached_ids = set(cached.get("entry_ids", []))
        return [eid for eid in current_entry_ids if eid not in cached_ids]

    def get_conditional_headers(self, feed_url: str) -> dict[str, str]:
        """Get conditional request headers for incremental updates.
        Args:
            feed_url: URL of the feed
        Returns:
            Dictionary with If-None-Match and/or If-Modified-Since headers
        """
        cached = self.get_cached(feed_url)
        if not cached:
            return {}
        headers = {}
        if cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]
        if cached.get("last_modified"):
            headers["If-Modified-Since"] = cached["last_modified"]
        return headers

    def clean_cache(
        self,
        feed_url: str | None = None,
        older_than_days: int | None = None,
    ) -> int:
        """Clean cache files.
        Args:
            feed_url: If specified, only clean this feed's cache
            older_than_days: If specified, clean files older than this
        Returns:
            Number of files removed
        """
        if feed_url:
            # Clean specific feed
            cache_file = self._get_cache_file(feed_url)
            if cache_file.exists():
                cache_file.unlink()
                return 1
            return 0
        # Clean all cache
        removed = 0
        cutoff_time = None
        if older_than_days:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
        for cache_file in self.cache_dir.rglob("*.json"):
            should_remove = False
            if cutoff_time:
                # Check file modification time
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff_time:
                    should_remove = True
            else:
                # Remove all
                should_remove = True
            if should_remove:
                try:
                    cache_file.unlink()
                    removed += 1
                except Exception:
                    pass
        return removed

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.
        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.rglob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        return {
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }

    def _get_cache_file(self, feed_url: str) -> Path:
        """Get cache file path for a feed URL.
        Args:
            feed_url: URL of the feed
        Returns:
            Path to cache file
        """
        # Create hash of URL for filename
        url_hash = hashlib.sha256(feed_url.encode()).hexdigest()[:16]
        return self.cache_dir / f"{url_hash}.json"

    def _extract_entry_ids(self, feed_data: dict[str, Any]) -> list[str]:
        """Extract entry IDs from feed data.
        Args:
            feed_data: Feed data dictionary
        Returns:
            List of entry IDs
        """
        entries = feed_data.get("entries", [])
        return [entry.get("id", "") for entry in entries if entry.get("id")]
