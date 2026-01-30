"""RSS/Atom Feed parser with academic journal support.
This module provides functionality to parse RSS 2.0 and Atom feeds,
with special handling for academic journal metadata (DOI, authors, etc.).
"""

from datetime import datetime
from html import unescape
import re
from typing import Any

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import feedparser

from information_composer.rss.models import (
    FeedEntry,
    FeedFormat,
    FeedMetadata,
)


class RSSParser:
    """Parser for RSS 2.0 and Atom feeds."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.doi_pattern = re.compile(r"10\.\d{4,}/[^\s]+")

    def parse(
        self, xml_content: str, feed_url: str
    ) -> tuple[FeedMetadata | None, list[FeedEntry]]:
        """Parse RSS/Atom feed XML content.
        Args:
            xml_content: Raw XML content of the feed
            feed_url: URL of the feed (for metadata)
        Returns:
            Tuple of (FeedMetadata, list of FeedEntry)
        Raises:
            RuntimeError: If the feed cannot be parsed
        """
        try:
            feed = feedparser.parse(xml_content)
            # Check if feed parsing failed
            if feed.bozo:
                # If there's a bozo exception, raise it
                if hasattr(feed, "bozo_exception") and feed.bozo_exception:
                    error_msg = str(feed.bozo_exception)
                    raise RuntimeError(f"Error parsing feed: {error_msg}")
                # If no entries and bozo flag is set, it's likely invalid
                if not feed.entries:
                    raise RuntimeError("Error parsing feed: Invalid feed format")
            # Extract metadata
            metadata = self._extract_metadata(feed, feed_url)
            # Extract entries
            entries = []
            for entry in feed.entries:
                parsed_entry = self._extract_entry(entry, feed)
                if parsed_entry:
                    entries.append(parsed_entry)
            return metadata, entries
        except RuntimeError:
            # Re-raise RuntimeError as is
            raise
        except Exception as e:
            raise RuntimeError(f"Error parsing feed: {e}") from e

    def detect_format(self, xml_content: str) -> FeedFormat:
        """Detect feed format (RSS or Atom).
        Args:
            xml_content: Raw XML content
        Returns:
            FeedFormat enum value
        """
        feed = feedparser.parse(xml_content)
        if hasattr(feed, "version") and isinstance(feed.version, str):
            if "rss" in feed.version.lower():
                return FeedFormat.RSS
            elif "atom" in feed.version.lower():
                return FeedFormat.ATOM
        return FeedFormat.UNKNOWN

    def _extract_metadata(self, feed: Any, feed_url: str) -> FeedMetadata:
        """Extract feed-level metadata.
        Args:
            feed: Parsed feed object from feedparser
            feed_url: URL of the feed
        Returns:
            FeedMetadata object
        """
        feed_data = feed.feed
        # Detect format
        format_type = FeedFormat.UNKNOWN
        if hasattr(feed, "version") and isinstance(feed.version, str):
            if "rss" in feed.version.lower():
                format_type = FeedFormat.RSS
            elif "atom" in feed.version.lower():
                format_type = FeedFormat.ATOM
        # Extract update time
        updated = None
        if hasattr(feed_data, "updated_parsed") and feed_data.updated_parsed:
            updated = datetime(*feed_data.updated_parsed[:6])
        elif hasattr(feed_data, "published_parsed") and feed_data.published_parsed:
            updated = datetime(*feed_data.published_parsed[:6])
        return FeedMetadata(
            url=feed_url,
            title=self._clean_text(feed_data.get("title", "")),
            description=self._clean_text(feed_data.get("description", "")),
            link=feed_data.get("link", ""),
            language=feed_data.get("language", ""),
            updated=updated,
            format=format_type,
            etag=feed_data.get("etag"),
            last_modified=feed_data.get("modified"),
        )

    def _extract_entry(self, entry: Any, feed: Any) -> FeedEntry | None:
        """Extract single entry/article from feed.
        Args:
            entry: Single entry object from feedparser
            feed: Parent feed object
        Returns:
            FeedEntry object or None if entry is invalid
        """
        # Skip if no title (essential field)
        if not entry.get("title"):
            return None
        # Extract unique ID
        entry_id = (
            entry.get("id", "") or entry.get("link", "") or entry.get("title", "")
        )
        # Extract and clean description/summary
        description = ""
        if hasattr(entry, "summary"):
            description = self._clean_html(entry.summary)
        elif hasattr(entry, "description"):
            description = self._clean_html(entry.description)
        # Extract content
        content = ""
        if hasattr(entry, "content") and entry.content:
            # Get the first content entry
            content = self._clean_html(entry.content[0].get("value", ""))
        # Extract published date
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])
        # Extract updated date
        updated = None
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            updated = datetime(*entry.updated_parsed[:6])
        # Extract author(s)
        author = ""
        authors = []
        if hasattr(entry, "author"):
            author = self._clean_text(entry.author)
        if hasattr(entry, "authors"):
            authors = [
                self._clean_text(a.get("name", ""))
                for a in entry.authors
                if a.get("name")
            ]
        # If no authors list but have single author, create list
        if not authors and author:
            authors = [author]
        # Extract categories
        categories = []
        if hasattr(entry, "tags"):
            categories = [
                self._clean_text(tag.get("term", ""))
                for tag in entry.tags
                if tag.get("term")
            ]
        # Extract enclosures (attachments)
        enclosures = []
        if hasattr(entry, "enclosures"):
            for enc in entry.enclosures:
                enclosures.append(
                    {
                        "url": enc.get("href", ""),
                        "type": enc.get("type", ""),
                        "length": enc.get("length", ""),
                    }
                )
        # Create base entry
        feed_entry = FeedEntry(
            id=entry_id,
            title=self._clean_text(entry.get("title", "")),
            link=entry.get("link", ""),
            description=description,
            content=content,
            published=published,
            updated=updated,
            author=author,
            authors=authors,
            categories=categories,
            enclosures=enclosures,
        )
        # Extract academic metadata
        self._extract_academic_metadata(entry, feed_entry)
        return feed_entry

    def _extract_academic_metadata(self, entry: Any, feed_entry: FeedEntry) -> None:
        """Extract academic journal specific metadata.
        Modifies feed_entry in place to add DOI, journal info, etc.
        Args:
            entry: Raw entry object from feedparser
            feed_entry: FeedEntry to populate
        """
        # Extract DOI
        doi = self._extract_doi(entry)
        if doi:
            feed_entry.doi = doi
        # Try to extract journal info from entry metadata
        # This varies by publisher, but we check common fields
        # Check for Dublin Core metadata (common in academic feeds)
        if hasattr(entry, "dc_source"):
            feed_entry.journal_name = self._clean_text(entry.dc_source)
        # Check for PRISM metadata (Publishing Requirements for Industry Standard Metadata)
        if hasattr(entry, "prism_publicationname"):
            feed_entry.journal_name = self._clean_text(entry.prism_publicationname)
        if hasattr(entry, "prism_volume"):
            feed_entry.volume = self._clean_text(entry.prism_volume)
        if hasattr(entry, "prism_number"):
            feed_entry.issue = self._clean_text(entry.prism_number)
        # Try to extract from categories/tags
        for category in feed_entry.categories:
            if "research article" in category.lower():
                feed_entry.article_type = "Research Article"
            elif "review" in category.lower():
                feed_entry.article_type = "Review"
            elif "brief communication" in category.lower():
                feed_entry.article_type = "Brief Communication"

    def _extract_doi(self, entry: Any) -> str:
        """Extract DOI from entry.
        Args:
            entry: Raw entry object
        Returns:
            DOI string or empty string if not found
        """
        # Check in ID field
        if hasattr(entry, "id"):
            doi_match = self.doi_pattern.search(entry.id)
            if doi_match:
                return doi_match.group(0)
        # Check in links
        if hasattr(entry, "links"):
            for link in entry.links:
                if "doi.org" in link.get("href", ""):
                    doi_match = self.doi_pattern.search(link["href"])
                    if doi_match:
                        return doi_match.group(0)
        # Check in summary/description
        if hasattr(entry, "summary"):
            doi_match = self.doi_pattern.search(entry.summary)
            if doi_match:
                return doi_match.group(0)
        return ""

    def _clean_html(self, html_text: str) -> str:
        """Clean HTML tags and convert to plain text.
        Args:
            html_text: HTML text to clean
        Returns:
            Plain text with HTML removed
        """
        if not html_text:
            return ""
        # Use BeautifulSoup to parse and extract text
        soup = BeautifulSoup(html_text, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)
        # Unescape HTML entities
        text = unescape(text)
        return text

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.
        Args:
            text: Text to clean
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        # Remove excessive whitespace
        text = " ".join(text.split())
        # Unescape HTML entities
        text = unescape(text)
        # Remove zero-width characters
        text = (
            text.replace("\u200b", "")
            .replace("\u200c", "")
            .replace("\u200d", "")
            .replace("\ufeff", "")
        )
        return text.strip()

    def normalize_date(self, date_string: str) -> datetime | None:
        """Normalize various date formats to datetime.
        Args:
            date_string: Date string in various formats
        Returns:
            datetime object or None if parsing fails
        """
        if not date_string:
            return None
        try:
            return date_parser.parse(date_string)
        except Exception:
            return None
