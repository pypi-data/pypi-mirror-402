"""RSS Feed fetcher with async support and retry logic.
This module provides the main RSS fetcher class that inherits from BaseSiteCollector
and implements feed fetching with caching, retries, and rate limiting.
"""

import asyncio
from datetime import datetime
import time
from typing import Any

import aiohttp
import requests

from information_composer.rss.cache import CacheManager
from information_composer.rss.models import FeedResult, FeedStatus
from information_composer.rss.parser import RSSParser
from information_composer.sites.base import BaseSiteCollector


class RSSFetcher(BaseSiteCollector):
    """RSS Feed fetcher with caching and retry support."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize RSS fetcher.
        Args:
            config: Configuration dictionary with optional keys:
                - cache_enabled: Enable caching (default: True)
                - cache_dir: Cache directory path
                - cache_expire_days: Cache expiration in days (default: 7)
                - timeout: Request timeout in seconds (default: 30)
                - max_retries: Maximum retry attempts (default: 3)
                - retry_delay: Delay between retries in seconds (default: 2)
                - user_agent: Custom User-Agent string
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        self.cache_enabled = self.get_config_value("cache_enabled", True)
        self.timeout = self.get_config_value("timeout", 30)
        self.max_retries = self.get_config_value("max_retries", 3)
        self.retry_delay = self.get_config_value("retry_delay", 2)
        self.max_concurrent = self.get_config_value("max_concurrent", 5)
        # Initialize cache manager
        cache_dir = self.get_config_value("cache_dir")
        cache_expire_days = self.get_config_value("cache_expire_days", 7)
        self.cache = (
            CacheManager(cache_dir, cache_expire_days) if self.cache_enabled else None
        )
        # Initialize parser
        self.parser = RSSParser()
        # Setup headers
        user_agent = self.get_config_value(
            "user_agent", "information-composer/0.1.3 (RSS Fetcher)"
        )
        self.headers = {"User-Agent": user_agent}

    def collect(self) -> Any:
        """Collect RSS feed data (not used in this implementation).
        This method is required by BaseSiteCollector but not used directly.
        Use fetch_single or fetch_batch instead.
        Returns:
            None
        """
        # This is a placeholder as we use fetch_single/fetch_batch instead
        return None

    def compose(self, data: Any) -> Any:
        """Compose collected data (not used in this implementation).
        This method is required by BaseSiteCollector but not used directly.
        The parser handles composition.
        Args:
            data: Raw data
        Returns:
            data as-is
        """
        return data

    def fetch_single(
        self,
        feed_url: str,
        use_cache: bool = True,
        max_entries: int | None = None,
    ) -> FeedResult:
        """Fetch a single RSS feed.
        Args:
            feed_url: URL of the RSS feed
            use_cache: Whether to use cache
            max_entries: Maximum number of entries to return
        Returns:
            FeedResult object with feed data
        """
        fetch_time = datetime.now()
        # Check cache if enabled
        if use_cache and self.cache:
            cached = self.cache.get_cached(feed_url)
            if cached:
                # Return cached data
                try:
                    metadata, entries = self.parser.parse(
                        str(cached.get("data", "")), feed_url
                    )
                    if max_entries:
                        entries = entries[:max_entries]
                    return FeedResult(
                        feed_url=feed_url,
                        metadata=metadata,
                        entries=entries,
                        fetch_time=fetch_time,
                        status=FeedStatus.SUCCESS,
                    )
                except Exception:
                    # Cache corrupted, continue to fetch
                    pass
        # Prepare headers for conditional request
        request_headers = self.headers.copy()
        if use_cache and self.cache:
            conditional_headers = self.cache.get_conditional_headers(feed_url)
            request_headers.update(conditional_headers)
        # Fetch feed with retries
        xml_content = None
        error_message = None
        etag = None
        last_modified = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    feed_url, headers=request_headers, timeout=self.timeout
                )
                # Check for 304 Not Modified
                if response.status_code == 304:
                    # Use cached data
                    if use_cache and self.cache:
                        cached = self.cache.get_cached(feed_url)
                        if cached:
                            metadata, entries = self.parser.parse(
                                str(cached.get("data", "")), feed_url
                            )
                            if max_entries:
                                entries = entries[:max_entries]
                            return FeedResult(
                                feed_url=feed_url,
                                metadata=metadata,
                                entries=entries,
                                fetch_time=fetch_time,
                                status=FeedStatus.SUCCESS,
                            )
                response.raise_for_status()
                xml_content = response.text
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")
                break
            except requests.exceptions.Timeout:
                error_message = (
                    f"Timeout fetching feed (attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff
                continue
            except requests.exceptions.RequestException as e:
                error_message = f"Error fetching feed: {e}"
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))
                continue
        # Check if fetch was successful
        if xml_content is None:
            return FeedResult(
                feed_url=feed_url,
                metadata=None,
                entries=[],
                fetch_time=fetch_time,
                status=FeedStatus.FAILURE,
                error=error_message or "Failed to fetch feed",
            )
        # Parse feed
        try:
            metadata, entries = self.parser.parse(xml_content, feed_url)
            # Update metadata with conditional request headers
            if metadata:
                metadata.etag = etag
                metadata.last_modified = last_modified
            # Save to cache
            if use_cache and self.cache:
                # Create cache data
                cache_data = {
                    "xml": xml_content,
                    "metadata": metadata.to_dict() if metadata else {},
                    "entries": [e.to_dict() for e in entries],
                }
                self.cache.save_cache(feed_url, cache_data, etag, last_modified)
            # Limit entries if requested
            if max_entries:
                entries = entries[:max_entries]
            return FeedResult(
                feed_url=feed_url,
                metadata=metadata,
                entries=entries,
                fetch_time=fetch_time,
                status=FeedStatus.SUCCESS,
            )
        except Exception as e:
            return FeedResult(
                feed_url=feed_url,
                metadata=None,
                entries=[],
                fetch_time=fetch_time,
                status=FeedStatus.FAILURE,
                error=f"Error parsing feed: {e}",
            )

    def fetch_batch(
        self,
        feed_urls: list[str],
        use_cache: bool = True,
        delay: float = 1.0,
        continue_on_error: bool = True,
    ) -> list[FeedResult]:
        """Fetch multiple RSS feeds with rate limiting.
        Args:
            feed_urls: List of feed URLs
            use_cache: Whether to use cache
            delay: Delay between requests in seconds
            continue_on_error: Continue on individual feed errors
        Returns:
            List of FeedResult objects
        """
        results = []
        for url in feed_urls:
            result = self.fetch_single(url, use_cache=use_cache)
            results.append(result)
            if not continue_on_error and result.status == FeedStatus.FAILURE:
                break
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
        return results

    async def fetch_single_async(
        self, session: aiohttp.ClientSession, feed_url: str, use_cache: bool = True
    ) -> FeedResult:
        """Fetch a single feed asynchronously.
        Args:
            session: aiohttp ClientSession
            feed_url: URL of the feed
            use_cache: Whether to use cache
        Returns:
            FeedResult object
        """
        fetch_time = datetime.now()
        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get_cached(feed_url)
            if cached:
                try:
                    metadata, entries = self.parser.parse(
                        str(cached.get("data", "")), feed_url
                    )
                    return FeedResult(
                        feed_url=feed_url,
                        metadata=metadata,
                        entries=entries,
                        fetch_time=fetch_time,
                        status=FeedStatus.SUCCESS,
                    )
                except Exception:
                    pass
        # Fetch feed
        request_headers = self.headers.copy()
        if use_cache and self.cache:
            conditional_headers = self.cache.get_conditional_headers(feed_url)
            request_headers.update(conditional_headers)
        try:
            async with session.get(
                feed_url, headers=request_headers, timeout=self.timeout
            ) as response:
                # Handle 304
                if response.status == 304 and use_cache and self.cache:
                    cached = self.cache.get_cached(feed_url)
                    if cached:
                        metadata, entries = self.parser.parse(
                            str(cached.get("data", "")), feed_url
                        )
                        return FeedResult(
                            feed_url=feed_url,
                            metadata=metadata,
                            entries=entries,
                            fetch_time=fetch_time,
                            status=FeedStatus.SUCCESS,
                        )
                response.raise_for_status()
                xml_content = await response.text()
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")
                # Parse
                metadata, entries = self.parser.parse(xml_content, feed_url)
                if metadata:
                    metadata.etag = etag
                    metadata.last_modified = last_modified
                # Cache
                if use_cache and self.cache:
                    cache_data = {
                        "xml": xml_content,
                        "metadata": metadata.to_dict() if metadata else {},
                        "entries": [e.to_dict() for e in entries],
                    }
                    self.cache.save_cache(feed_url, cache_data, etag, last_modified)
                return FeedResult(
                    feed_url=feed_url,
                    metadata=metadata,
                    entries=entries,
                    fetch_time=fetch_time,
                    status=FeedStatus.SUCCESS,
                )
        except Exception as e:
            return FeedResult(
                feed_url=feed_url,
                metadata=None,
                entries=[],
                fetch_time=fetch_time,
                status=FeedStatus.FAILURE,
                error=str(e),
            )

    async def fetch_batch_async(
        self, feed_urls: list[str], use_cache: bool = True
    ) -> list[FeedResult]:
        """Fetch multiple feeds concurrently with async.
        Args:
            feed_urls: List of feed URLs
            use_cache: Whether to use cache
        Returns:
            List of FeedResult objects
        """
        async with aiohttp.ClientSession() as session:
            # Create semaphore for rate limiting
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def fetch_with_semaphore(url: str) -> FeedResult:
                async with semaphore:
                    return await self.fetch_single_async(session, url, use_cache)

            tasks = [fetch_with_semaphore(url) for url in feed_urls]
            return await asyncio.gather(*tasks)

    def fetch_batch_sync(
        self, feed_urls: list[str], use_cache: bool = True
    ) -> list[FeedResult]:
        """Synchronous wrapper for async batch fetch.
        Args:
            feed_urls: List of feed URLs
            use_cache: Whether to use cache
        Returns:
            List of FeedResult objects
        """
        return asyncio.run(self.fetch_batch_async(feed_urls, use_cache))
