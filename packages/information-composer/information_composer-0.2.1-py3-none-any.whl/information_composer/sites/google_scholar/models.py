"""Data models for Google Scholar crawler.
This module defines the data models used by the Google Scholar crawler,
including configuration, paper information, and search results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# Check for optional dependencies
# Optional dependencies are imported when needed
class SearchStrategy(Enum):
    """Search strategy enumeration."""

    REQUESTS = "requests"
    SELENIUM = "selenium"
    SCHOLARLY = "scholarly"


@dataclass
class SearchConfig:
    """Configuration for Google Scholar search.
    This class contains all configuration parameters for Google Scholar searches,
    including search behavior, rate limiting, caching, and data enhancement options.
    """

    # Basic search parameters
    max_results: int = 100
    year_range: tuple[int, int] | None = None
    language: str = "en"
    # Search behavior
    include_citations: bool = True
    include_abstracts: bool = True
    include_patents: bool = False
    sort_by: str = "relevance"  # relevance, date
    # Rate limiting and performance
    rate_limit: float = 2.0  # seconds between requests
    max_retries: int = 3
    timeout: float = 30.0
    # Strategy selection
    search_strategy: SearchStrategy = SearchStrategy.REQUESTS
    use_selenium_fallback: bool = True
    # Caching
    cache_dir: str | None = None
    cache_ttl_days: int = 30
    # User agent and session management
    user_agent_rotation: bool = True
    session_persistence: bool = True
    # Data enhancement
    resolve_dois: bool = True
    link_pubmed: bool = True
    fetch_abstracts: bool = True

    def __post_init__(self) -> None:
        """Validate configuration parameters after initialization."""
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate configuration parameters."""
        # Validate max_results
        if self.max_results <= 0:
            raise ValueError("max_results must be positive")
        # Validate sort_by
        valid_sort_options = ["relevance", "date"]
        if self.sort_by not in valid_sort_options:
            raise ValueError(
                f"Invalid sort_by value: {self.sort_by}. Must be one of {valid_sort_options}"
            )
        # Validate year_range
        if self.year_range:
            if not isinstance(self.year_range, tuple) or len(self.year_range) != 2:
                raise ValueError("year_range must be a tuple of (start_year, end_year)")
            start_year, end_year = self.year_range
            if not isinstance(start_year, int) or not isinstance(end_year, int):
                raise ValueError("year_range values must be integers")
            if start_year > end_year:
                raise ValueError("Start year must be <= end year")
            current_year = datetime.now().year
            if start_year < 1900 or end_year > current_year + 5:
                raise ValueError(
                    f"Year range seems unrealistic: {start_year}-{end_year}"
                )
        # Validate rate_limit
        if self.rate_limit < 0.1:
            raise ValueError("Rate limit too low (minimum 0.1s), may cause blocking")
        # Validate timeout
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        # Validate cache_ttl_days
        if self.cache_ttl_days <= 0:
            raise ValueError("Cache TTL must be positive")
        # Validate search strategy with available dependencies
        if self.search_strategy == SearchStrategy.SELENIUM:
            if self.use_selenium_fallback:
                import logging

                logging.warning(
                    "Selenium not available, falling back to requests strategy"
                )
                self.search_strategy = SearchStrategy.REQUESTS
            else:
                raise ImportError(
                    "Selenium strategy requested but selenium not installed. "
                    "Install with: pip install selenium"
                )
        if self.search_strategy == SearchStrategy.SCHOLARLY:
            if self.use_selenium_fallback:  # Use as general fallback flag
                import logging

                logging.warning(
                    "Scholarly not available, falling back to requests strategy"
                )
                self.search_strategy = SearchStrategy.REQUESTS
            else:
                raise ImportError(
                    "Scholarly strategy requested but scholarly not installed. "
                    "Install with: pip install scholarly"
                )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "max_results": self.max_results,
            "year_range": self.year_range,
            "language": self.language,
            "include_citations": self.include_citations,
            "include_abstracts": self.include_abstracts,
            "include_patents": self.include_patents,
            "sort_by": self.sort_by,
            "rate_limit": self.rate_limit,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "search_strategy": self.search_strategy.value,
            "use_selenium_fallback": self.use_selenium_fallback,
            "cache_dir": self.cache_dir,
            "cache_ttl_days": self.cache_ttl_days,
            "user_agent_rotation": self.user_agent_rotation,
            "session_persistence": self.session_persistence,
            "resolve_dois": self.resolve_dois,
            "link_pubmed": self.link_pubmed,
            "fetch_abstracts": self.fetch_abstracts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchConfig":
        """Create instance from dictionary.
        Args:
            data: Dictionary containing configuration data
        Returns:
            SearchConfig instance
        """
        config = cls()
        for key, value in data.items():
            if key == "search_strategy":
                value = SearchStrategy(value)
            if hasattr(config, key):
                setattr(config, key, value)
        return config


@dataclass
class GoogleScholarPaper:
    """Data model for a Google Scholar paper.
    This class represents a single paper from Google Scholar with all its
    associated metadata and information.
    """

    # Core identifiers
    google_scholar_id: str
    title: str
    # Author information
    authors: list[str] = field(default_factory=list)
    author_affiliations: list[str] = field(default_factory=list)
    # Publication details
    journal: str | None = None
    conference: str | None = None
    year: int | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publisher: str | None = None
    # Content
    abstract: str | None = None
    pdf_url: str | None = None
    # External identifiers
    doi: str | None = None
    pubmed_id: str | None = None
    arxiv_id: str | None = None
    isbn: str | None = None
    # Metrics and metadata
    citation_count: int = 0
    search_rank: int = 0
    confidence_score: float = 0.0
    # Source and context
    google_scholar_url: str | None = None
    source_url: str | None = None
    language: str = "en"
    search_query: str = ""
    # Timestamps
    extracted_date: datetime = field(default_factory=datetime.now)
    publication_date: datetime | None = None
    # Additional metadata
    keywords: list[str] = field(default_factory=list)
    abstract_snippet: str | None = None
    venue_type: str | None = None  # journal, conference, book, etc.
    open_access: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        Returns:
            Dictionary representation of the paper
        """
        return {
            "google_scholar_id": self.google_scholar_id,
            "title": self.title,
            "authors": self.authors,
            "author_affiliations": self.author_affiliations,
            "journal": self.journal,
            "conference": self.conference,
            "year": self.year,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "publisher": self.publisher,
            "abstract": self.abstract,
            "pdf_url": self.pdf_url,
            "doi": self.doi,
            "pubmed_id": self.pubmed_id,
            "arxiv_id": self.arxiv_id,
            "isbn": self.isbn,
            "citation_count": self.citation_count,
            "search_rank": self.search_rank,
            "confidence_score": self.confidence_score,
            "google_scholar_url": self.google_scholar_url,
            "source_url": self.source_url,
            "language": self.language,
            "search_query": self.search_query,
            "extracted_date": self.extracted_date.isoformat()
            if self.extracted_date
            else None,
            "publication_date": self.publication_date.isoformat()
            if self.publication_date
            else None,
            "keywords": self.keywords,
            "abstract_snippet": self.abstract_snippet,
            "venue_type": self.venue_type,
            "open_access": self.open_access,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoogleScholarPaper":
        """Create instance from dictionary.
        Args:
            data: Dictionary containing paper data
        Returns:
            GoogleScholarPaper instance
        """
        # Handle datetime conversion
        if data.get("extracted_date"):
            data["extracted_date"] = datetime.fromisoformat(data["extracted_date"])
        if data.get("publication_date"):
            data["publication_date"] = datetime.fromisoformat(data["publication_date"])
        return cls(**data)

    def is_valid(self) -> bool:
        """Check if the paper has minimum required information.
        Returns:
            True if paper has required information, False otherwise
        """
        return bool(self.title and self.google_scholar_id)

    def get_primary_author(self) -> str | None:
        """Get the first author if available.
        Returns:
            First author name or None
        """
        return self.authors[0] if self.authors else None

    def get_citation_display(self) -> str:
        """Get formatted citation for display.
        Returns:
            Formatted citation string
        """
        parts = []
        # Authors
        if self.authors:
            if len(self.authors) == 1:
                parts.append(self.authors[0])
            elif len(self.authors) <= 3:
                parts.append(", ".join(self.authors[:-1]) + " and " + self.authors[-1])
            else:
                parts.append(f"{self.authors[0]} et al.")
        # Title
        if self.title:
            parts.append(f'"{self.title}"')
        # Venue
        venue = self.journal or self.conference
        if venue:
            parts.append(venue)
        # Year
        if self.year:
            parts.append(f"({self.year})")
        return ". ".join(parts) + "."

    def update_confidence_score(self) -> None:
        """Calculate and update confidence score based on available data."""
        score = 0.0
        # Basic requirements
        if self.title:
            score += 0.2
        if self.authors:
            score += 0.15
        if self.google_scholar_id:
            score += 0.1
        # Publication information
        if self.journal or self.conference:
            score += 0.15
        if self.year:
            score += 0.1
        # External identifiers
        if self.doi:
            score += 0.15
        if self.pubmed_id:
            score += 0.1
        # Content
        if self.abstract:
            score += 0.05
        self.confidence_score = min(1.0, score)


@dataclass
class SearchResult:
    """Container for search results with metadata.
    This class contains the results of a Google Scholar search along with
    metadata about the search process and statistics.
    """

    papers: list[GoogleScholarPaper] = field(default_factory=list)
    query: str = ""
    total_results: int = 0
    search_time: float = 0.0
    strategy_used: SearchStrategy = SearchStrategy.REQUESTS
    cached: bool = False
    search_config: SearchConfig | None = None
    # Statistics
    valid_papers: int = 0
    papers_with_doi: int = 0
    papers_with_abstract: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.
        Returns:
            Dictionary representation of the search results
        """
        return {
            "papers": [paper.to_dict() for paper in self.papers],
            "query": self.query,
            "total_results": self.total_results,
            "search_time": self.search_time,
            "strategy_used": self.strategy_used.value,
            "cached": self.cached,
            "search_config": self.search_config.to_dict()
            if self.search_config
            else None,
            "valid_papers": self.valid_papers,
            "papers_with_doi": self.papers_with_doi,
            "papers_with_abstract": self.papers_with_abstract,
        }

    def update_statistics(self) -> None:
        """Update result statistics."""
        self.valid_papers = sum(1 for paper in self.papers if paper.is_valid())
        self.papers_with_doi = sum(1 for paper in self.papers if paper.doi)
        self.papers_with_abstract = sum(1 for paper in self.papers if paper.abstract)

    def get_top_papers(self, n: int = 10) -> list[GoogleScholarPaper]:
        """Get top N papers by search rank.
        Args:
            n: Number of top papers to return
        Returns:
            List of top N papers
        """
        return sorted(self.papers, key=lambda p: p.search_rank)[:n]

    def filter_by_year(self, start_year: int, end_year: int) -> "SearchResult":
        """Filter papers by year range.
        Args:
            start_year: Start year for filtering
            end_year: End year for filtering
        Returns:
            New SearchResult with filtered papers
        """
        filtered_papers = [
            paper
            for paper in self.papers
            if paper.year and start_year <= paper.year <= end_year
        ]
        result = SearchResult(
            papers=filtered_papers, query=self.query, search_config=self.search_config
        )
        result.update_statistics()
        return result
