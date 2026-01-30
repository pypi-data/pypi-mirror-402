"""RSS Feed fetcher module for information-composer.

This module provides functionality to fetch, parse, and process RSS/Atom feeds
with special optimization for academic journals.
"""

from information_composer.rss.cache import CacheManager
from information_composer.rss.config import ConfigManager
from information_composer.rss.fetcher import RSSFetcher
from information_composer.rss.models import (
    FeedConfig,
    FeedEntry,
    FeedFormat,
    FeedMetadata,
    FeedResult,
    FeedStatus,
)
from information_composer.rss.parser import RSSParser


__all__ = [
    "CacheManager",
    "ConfigManager",
    "FeedConfig",
    "FeedEntry",
    "FeedFormat",
    "FeedMetadata",
    "FeedResult",
    "FeedStatus",
    "RSSFetcher",
    "RSSParser",
]
