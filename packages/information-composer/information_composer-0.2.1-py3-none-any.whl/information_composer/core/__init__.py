"""
Core module for Information Composer.
This module provides base functionality for downloading and processing
academic papers and other content.
"""

from typing import TYPE_CHECKING

from . import utils
from .doi_downloader import DOIDownloader
from .downloader import BaseDownloader
from .utils import clean_doi, extract_doi_from_text, validate_doi


if TYPE_CHECKING:
    from .doi_downloader import BatchDownloadStats, DownloadResult
__all__ = [
    "BaseDownloader",
    "BatchDownloadStats",
    "DOIDownloader",
    # Type hints
    "DownloadResult",
    # Utils
    "clean_doi",
    "extract_doi_from_text",
    "utils",
    "validate_doi",
]
