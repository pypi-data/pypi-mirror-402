"""Cache management utilities for Google Scholar crawler."""

# import asyncio  # Unused import
import hashlib
import json
from pathlib import Path

# import pickle  # Unused import
import time

from ..models import GoogleScholarPaper, SearchConfig, SearchResult


class CacheManager:
    """Manage caching of Google Scholar search results."""

    def __init__(self, cache_dir: str, ttl_days: int = 30):
        """
        Initialize cache manager.
        Args:
            cache_dir: Directory to store cache files
            ttl_days: Time to live for cache entries in days
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_days * 24 * 3600

    def _get_cache_key(self, query: str, config: SearchConfig) -> str:
        """Generate cache key from query and config."""
        # Create a hash from query and relevant config parameters
        cache_data = {
            "query": query.lower().strip(),
            "max_results": config.max_results,
            "year_range": config.year_range,
            "language": config.language,
            "include_citations": config.include_citations,
            "include_abstracts": config.include_abstracts,
            "include_patents": config.include_patents,
            "sort_by": config.sort_by,
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.json"

    async def get_cached_search(
        self, query: str, config: SearchConfig
    ) -> SearchResult | None:
        """
        Get cached search result.
        Args:
            query: Search query
            config: Search configuration
        Returns:
            Cached SearchResult if found and valid, None otherwise
        """
        cache_key = self._get_cache_key(query, config)
        cache_file = self._get_cache_file_path(cache_key)
        if not cache_file.exists():
            return None
        try:
            # Check if cache is still valid
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > self.ttl_seconds:
                # Cache expired, remove it
                cache_file.unlink()
                return None
            # Load cached data
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)
            # Reconstruct SearchResult
            papers = [
                GoogleScholarPaper.from_dict(paper_data)
                for paper_data in data["papers"]
            ]
            result = SearchResult(
                papers=papers,
                query=data["query"],
                total_results=data["total_results"],
                search_time=data["search_time"],
                cached=True,
                search_config=config,
            )
            result.update_statistics()
            return result
        except Exception:
            # If there's any error reading cache, remove the file
            if cache_file.exists():
                cache_file.unlink()
            return None

    async def cache_search_results(
        self, query: str, result: SearchResult, config: SearchConfig
    ) -> None:
        """
        Cache search results.
        Args:
            query: Search query
            result: SearchResult to cache
            config: Search configuration
        """
        try:
            cache_key = self._get_cache_key(query, config)
            cache_file = self._get_cache_file_path(cache_key)
            # Prepare data for caching
            cache_data = {
                "query": result.query,
                "papers": [paper.to_dict() for paper in result.papers],
                "total_results": result.total_results,
                "search_time": result.search_time,
                "cached_at": time.time(),
                "cache_key": cache_key,
            }
            # Write to cache file
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception:
            # Log error but don't fail the search
            pass

    async def invalidate_cache(
        self, query: str | None = None, config: SearchConfig | None = None
    ) -> int:
        """
        Invalidate cache entries.
        Args:
            query: Specific query to invalidate (if None, invalidate all)
            config: Search configuration (required if query is provided)
        Returns:
            Number of cache files removed
        """
        removed_count = 0
        if query and config:
            # Invalidate specific query
            cache_key = self._get_cache_key(query, config)
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                cache_file.unlink()
                removed_count = 1
        else:
            # Invalidate all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                    removed_count += 1
                except Exception:
                    continue
        return removed_count

    async def clean_expired_cache(self) -> int:
        """
        Clean expired cache entries.
        Returns:
            Number of expired cache files removed
        """
        removed_count = 0
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > self.ttl_seconds:
                    cache_file.unlink()
                    removed_count += 1
            except Exception:
                continue
        return removed_count

    def get_cache_info(self) -> dict:
        """
        Get information about the cache.
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_files = len(cache_files)
            total_size = sum(f.stat().st_size for f in cache_files)
            # Count expired files
            current_time = time.time()
            expired_files = 0
            for cache_file in cache_files:
                try:
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > self.ttl_seconds:
                        expired_files += 1
                except Exception:
                    continue
            return {
                "cache_dir": str(self.cache_dir),
                "total_files": total_files,
                "total_size_mb": total_size / (1024 * 1024),
                "expired_files": expired_files,
                "valid_files": total_files - expired_files,
                "ttl_days": self.ttl_seconds / (24 * 3600),
            }
        except Exception:
            return {
                "cache_dir": str(self.cache_dir),
                "total_files": 0,
                "total_size_mb": 0,
                "expired_files": 0,
                "valid_files": 0,
                "ttl_days": self.ttl_seconds / (24 * 3600),
            }
