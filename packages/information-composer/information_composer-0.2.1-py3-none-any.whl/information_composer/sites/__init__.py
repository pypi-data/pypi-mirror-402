"""Sites module for web scraping and data collection.
This module provides functionality for collecting information from various
academic and research websites, including Google Scholar and RiceDataCN.
"""

from typing import TYPE_CHECKING

from .base import BaseSiteCollector
from .ricedatacn_gene_parser import RiceGeneParser


# Import Google Scholar components
try:
    from .google_scholar.crawler import GoogleScholarCrawler
    from .google_scholar.models import GoogleScholarPaper, SearchConfig, SearchResult
except ImportError:
    # Handle case where Google Scholar dependencies are not available
    GoogleScholarCrawler = None  # type: ignore
    GoogleScholarPaper = None  # type: ignore
    SearchConfig = None  # type: ignore
    SearchResult = None  # type: ignore
if TYPE_CHECKING:
    pass  # TYPE_CHECKING imports are for type hints only
__all__ = [
    "BaseSiteCollector",
    "GoogleScholarCrawler",
    "GoogleScholarPaper",
    "RiceGeneParser",
    # Google Scholar models
    "SearchConfig",
    "SearchResult",
]
