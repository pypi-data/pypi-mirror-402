"""Google Scholar module for academic paper search and data collection.
This module provides functionality for searching and collecting academic papers
from Google Scholar, including various search strategies and data models.
"""

from .crawler import GoogleScholarCrawler
from .models import (
    GoogleScholarPaper,
    SearchConfig,
    SearchResult,
    SearchStrategy,
)


__all__ = [
    "GoogleScholarCrawler",
    "GoogleScholarPaper",
    "SearchConfig",
    "SearchResult",
    "SearchStrategy",
]
