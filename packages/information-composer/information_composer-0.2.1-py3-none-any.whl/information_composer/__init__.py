"""
Information Composer - A comprehensive toolkit for collecting, composing, and filtering
information from various web resources with AI-powered markdown processing.
This package provides tools for:
- PDF validation and processing
- Markdown conversion and manipulation
- Academic paper downloading and management
- PubMed database integration
- Web scraping from various academic sites
- LLM-based content filtering
"""

from typing import TYPE_CHECKING

# Import all modules
from . import core, llm_filter, markdown, pdf, pubmed, sites

# Import key classes for easy access
from .core.doi_downloader import DOIDownloader
from .markdown.markdown import dictify, jsonify, markdownify
from .pdf.validator import PDFValidator
from .pubmed.pubmed import load_pubmed_file, query_pmid
from .sites.base import BaseSiteCollector
from .sites.google_scholar.models import GoogleScholarPaper, SearchConfig, SearchResult
from .sites.ricedatacn_gene_parser import RiceGeneParser


if TYPE_CHECKING:
    from .llm_filter.core.filter import MarkdownFilter as LLMFilter

__version__ = "0.2.1"
__author__ = "Information Composer Team"
__email__ = "info@information-composer.dev"
__all__ = [
    # Sites utilities
    "BaseSiteCollector",
    # Core classes
    "DOIDownloader",
    "GoogleScholarPaper",
    # Type hints
    "LLMFilter",
    "PDFValidator",
    "RiceGeneParser",
    "SearchConfig",
    "SearchResult",
    "clean_doi",
    # Package modules
    "core",
    # Markdown utilities
    "dictify",
    "jsonify",
    "llm_filter",
    "load_pubmed_file",
    "markdown",
    "markdownify",
    "pdf",
    "pubmed",
    # PubMed utilities
    "query_pmid",
    "sites",
]
