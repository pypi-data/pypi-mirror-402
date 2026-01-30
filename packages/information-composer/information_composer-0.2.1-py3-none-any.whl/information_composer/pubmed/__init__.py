"""PubMed module for querying and processing PubMed database data.
This module provides comprehensive functionality for:
- Querying PubMed database with various search options
- Fetching detailed article information
- Processing Medline format data
- Baseline data processing with filtering
- Caching and batch processing
- Semantic search via LitSense API
- AI-powered literature analysis (summary, domain classification)
"""

from typing import TYPE_CHECKING

from .baseline import load_baseline
from .litsense import LitSenseAPI, LitSenseResult, search_litsense
from .pubmed import (
    clean_pubmed_cache,
    fetch_pubmed_details,
    fetch_pubmed_details_batch,
    fetch_pubmed_details_batch_sync,
    load_pubmed_file,
    query_pmid,
    query_pmid_by_date,
)


# Import analyzer components
try:
    from .analyzer import (
        AnalysisConfig,
        AnalysisResult,
        DomainResult,
        PaperAnalyzer,
        PaperInput,
        ProcessingMetadata,
        SummaryResult,
    )

    _ANALYZER_AVAILABLE = True
except ImportError:
    _ANALYZER_AVAILABLE = False
    AnalysisConfig = None
    AnalysisResult = None
    DomainResult = None
    PaperAnalyzer = None
    PaperInput = None
    ProcessingMetadata = None
    SummaryResult = None
if TYPE_CHECKING:
    from .cli.main import main as pubmed_cli
    from .core.search import PubMedSearcher
__all__ = [
    # Analyzer components (if available)
    "AnalysisConfig",
    "AnalysisResult",
    # Classes
    "DomainResult",
    "LitSenseAPI",
    "LitSenseResult",
    "PaperAnalyzer",
    "PaperInput",
    "ProcessingMetadata",
    "PubMedSearcher",
    "SummaryResult",
    # Core functions
    "clean_pubmed_cache",
    "fetch_pubmed_details",
    "fetch_pubmed_details_batch",
    "fetch_pubmed_details_batch_sync",
    "load_baseline",
    "load_pubmed_file",
    # CLI
    "pubmed_cli",
    "query_pmid",
    "query_pmid_by_date",
    "search_litsense",
]
