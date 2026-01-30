"""PubMed search functionality for the MCP service.
This module provides a clean interface for PubMed search operations
with proper type annotations and error handling.
"""

from typing import Any

from information_composer.pubmed.pubmed import (
    fetch_pubmed_details_batch_sync,
    query_pmid,
)


class PubMedSearcher:
    """A simple wrapper for PubMed search functionality."""

    def __init__(self) -> None:
        """Initialize the PubMed searcher."""
        pass

    def search(
        self,
        query: str,
        email: str = "mcp@information-composer.org",
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search PubMed database and return detailed results.
        Args:
            query: PubMed search query string
            email: Email address for NCBI's tracking purposes
            max_results: Maximum number of results to return
        Returns:
            List of dictionaries containing detailed PubMed records
        Raises:
            RuntimeError: If there's an error searching PubMed
        """
        try:
            # First get the PMIDs matching the query
            pmids = query_pmid(query, email, max_results)
            if not pmids:
                return []
            # Fetch detailed information for the PMIDs
            results = fetch_pubmed_details_batch_sync(pmids, email)
            return results
        except Exception as e:
            raise RuntimeError(f"Error searching PubMed: {e!s}") from e
