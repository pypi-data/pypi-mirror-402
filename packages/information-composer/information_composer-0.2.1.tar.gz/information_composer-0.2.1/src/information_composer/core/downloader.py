"""
Base downloader implementation for Information Composer.
This module provides the base class for downloading content from various sources.
"""

from typing import Any

import requests


class BaseDownloader:
    """
    Base class for downloading content from various sources.
    This class provides a common interface for downloading content and
    manages HTTP sessions with configurable timeouts.
    """

    def __init__(self, timeout: int = 30) -> None:
        """
        Initialize the base downloader.
        Args:
            timeout: Request timeout in seconds. Defaults to 30.
        """
        self.timeout = timeout
        self.session = requests.Session()

    def download(self, url: str, headers: dict[str, str] | None = None) -> Any:
        """
        Download content from specified URL.
        This is an abstract method that should be implemented by subclasses
        to provide specific download functionality.
        Args:
            url: The URL to download content from
            headers: Optional HTTP headers to include in the request
        Returns:
            The downloaded content (type depends on implementation)
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement the download method")
