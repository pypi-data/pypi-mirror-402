"""Data models for RSS Feed processing.
This module defines the data structures used throughout the RSS fetcher module,
optimized for academic journal feeds and LLM integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FeedFormat(Enum):
    """Feed format type."""

    RSS = "rss"
    ATOM = "atom"
    UNKNOWN = "unknown"


class FeedStatus(Enum):
    """Feed fetch status."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class FeedMetadata:
    """Feed-level metadata.
    Attributes:
        url: Feed source URL
        title: Feed title
        description: Feed description
        link: Feed website link
        language: Language code (e.g., 'en', 'zh')
        updated: Last update time
        format: Feed format (RSS or Atom)
        etag: HTTP ETag for conditional requests
        last_modified: Last-Modified header for conditional requests
    """

    url: str
    title: str
    description: str = ""
    link: str = ""
    language: str = ""
    updated: datetime | None = None
    format: FeedFormat = FeedFormat.UNKNOWN
    etag: str | None = None
    last_modified: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_url": self.url,
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "language": self.language,
            "updated_at": self.updated.isoformat() if self.updated else None,
            "format": self.format.value,
            "etag": self.etag,
            "last_modified": self.last_modified,
        }


@dataclass
class FeedEntry:
    """Individual feed entry/article.
    Attributes:
        id: Unique identifier
        title: Entry title
        link: Entry URL
        description: Summary/abstract (plain text, HTML cleaned)
        content: Full content (optional, plain text)
        published: Publication time
        updated: Update time (optional)
        author: Single author name (optional)
        authors: List of authors (for academic papers)
        categories: Category/tag list
        enclosures: Attachments (audio, video links, etc.)
        doi: DOI identifier (academic papers)
        journal_name: Journal name (academic papers)
        volume: Volume number (academic papers)
        issue: Issue number (academic papers)
        article_type: Article type (academic papers)
        truncated: Whether content was truncated
    """

    id: str
    title: str
    link: str
    description: str = ""
    content: str = ""
    published: datetime | None = None
    updated: datetime | None = None
    author: str = ""
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    enclosures: list[dict[str, str]] = field(default_factory=list)
    # Academic metadata
    doi: str = ""
    journal_name: str = ""
    volume: str = ""
    issue: str = ""
    article_type: str = ""
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "published": self.published.isoformat() if self.published else None,
            "summary": self.description,
            "content": self.content if self.content else None,
            "authors": self.authors
            if self.authors
            else ([self.author] if self.author else []),
            "categories": self.categories,
            "metadata": {
                "doi": self.doi if self.doi else None,
                "journal": self.journal_name if self.journal_name else None,
                "volume": self.volume if self.volume else None,
                "issue": self.issue if self.issue else None,
                "article_type": self.article_type if self.article_type else None,
                "has_pdf": any(
                    "pdf" in enc.get("type", "").lower() for enc in self.enclosures
                ),
                "truncated": self.truncated,
            },
        }

    def to_llm_optimized_dict(
        self,
        max_summary_length: int = 500,
        max_content_length: int = 2000,
    ) -> dict[str, Any]:
        """Convert to LLM-optimized dictionary format.
        Args:
            max_summary_length: Maximum summary length in characters
            max_content_length: Maximum content length in characters
        Returns:
            Dictionary optimized for LLM processing with truncated text
        """
        result = self.to_dict()
        # Truncate summary if needed
        if result.get("summary") and len(result["summary"]) > max_summary_length:
            result["summary"] = result["summary"][:max_summary_length] + "..."
            result["metadata"]["truncated"] = True
        # Truncate content if needed
        if result.get("content") and len(result["content"]) > max_content_length:
            result["content"] = (
                result["content"][:max_content_length]
                + f"... [内容已截断，查看完整版本请访问: {self.link}]"
            )
            result["metadata"]["truncated"] = True
        return result


@dataclass
class FeedResult:
    """Result of a feed fetch operation.
    Attributes:
        feed_url: Feed URL
        metadata: Feed metadata
        entries: List of entries
        fetch_time: Time when feed was fetched
        status: Fetch status
        error: Error message (if any)
    """

    feed_url: str
    metadata: FeedMetadata | None
    entries: list[FeedEntry]
    fetch_time: datetime
    status: FeedStatus
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.
        Returns dictionary optimized for LLM processing with:
        - feed_metadata: Feed-level information
        - entries: List of entries with cleaned text
        - statistics: Summary statistics
        """
        entries_data = [entry.to_dict() for entry in self.entries]
        # Calculate statistics
        stats = {
            "total_entries": len(self.entries),
            "date_range": {},
        }
        if self.entries:
            published_dates = [e.published for e in self.entries if e.published]
            if published_dates:
                stats["date_range"] = {
                    "earliest": min(published_dates).isoformat(),
                    "latest": max(published_dates).isoformat(),
                }
        result = {
            "feed_metadata": self.metadata.to_dict() if self.metadata else {},
            "entries": entries_data,
            "statistics": stats,
        }
        # Add error information if present
        if self.error:
            result["error"] = self.error
            result["status"] = self.status.value
        return result

    def to_llm_optimized_dict(
        self,
        max_summary_length: int = 500,
        max_content_length: int = 2000,
        include_context: bool = True,
    ) -> dict[str, Any]:
        """Convert to LLM-optimized dictionary format.
        Args:
            max_summary_length: Maximum summary length in characters
            max_content_length: Maximum content length in characters
            include_context: Whether to include LLM context hints
        Returns:
            Dictionary optimized for MCP and LLM processing
        """
        base_data = self.to_dict()
        # Truncate summaries and content
        for entry in base_data["entries"]:
            if entry.get("summary") and len(entry["summary"]) > max_summary_length:
                entry["summary"] = entry["summary"][:max_summary_length] + "..."
                entry["metadata"]["truncated"] = True
            if entry.get("content") and len(entry["content"]) > max_content_length:
                entry["content"] = (
                    entry["content"][:max_content_length]
                    + f"... [内容已截断，查看完整版本请访问: {entry['link']}]"
                )
                entry["metadata"]["truncated"] = True
        result = {
            "tool_name": "rss_fetcher",
            "operation": "fetch_feed",
            "timestamp": self.fetch_time.isoformat(),
            "result": {
                "status": self.status.value,
                "data": base_data,
            },
        }
        # Add summary for quick overview
        if include_context and self.metadata:
            result["result"]["summary"] = {
                "feed_title": self.metadata.title,
                "total_entries": len(self.entries),
                "date_range": base_data["statistics"].get("date_range", {}),
            }
            # Add LLM context hints
            result["result"]["llm_context"] = {
                "description": f"从 {self.metadata.title} 获取了 {len(self.entries)} 篇文章",
                "suggested_actions": [
                    "分析最新的研究进展",
                    "提取关键发现",
                    "生成内容摘要",
                ],
            }
        return result


@dataclass
class FeedConfig:
    """Configuration for a single feed.
    Attributes:
        name: Feed name/identifier
        url: Feed URL
        category: Feed category
        enabled: Whether the feed is enabled
        tags: List of tags
        update_interval: Update interval in seconds
        filter: Filter rules (keywords, exclude_keywords, etc.)
        metadata: Additional metadata
    """

    name: str
    url: str
    category: str = ""
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    update_interval: int = 3600  # Default: 1 hour
    filter: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "category": self.category,
            "enabled": self.enabled,
            "tags": self.tags,
            "update_interval": self.update_interval,
            "filter": self.filter,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeedConfig":
        """Create FeedConfig from dictionary.
        Args:
            data: Dictionary with feed configuration
        Returns:
            FeedConfig instance
        """
        return cls(
            name=data["name"],
            url=data["url"],
            category=data.get("category", ""),
            enabled=data.get("enabled", True),
            tags=data.get("tags", []),
            update_interval=data.get("update_interval", 3600),
            filter=data.get("filter", {}),
            metadata=data.get("metadata", {}),
        )
