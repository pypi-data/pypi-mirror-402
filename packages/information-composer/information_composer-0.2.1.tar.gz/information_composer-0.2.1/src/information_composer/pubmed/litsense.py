"""LitSense API Python Interface
LitSense is NCBI's semantic search API for PubMed literature.
API documentation: https://www.ncbi.nlm.nih.gov/research/litsense-api/
Important limitations:
- Maximum 100 results per query
- Rate limit: 1 request per second per user
- Resource-intensive search, please be mindful of usage
"""

from dataclasses import dataclass, field
import time
from typing import Any
from urllib.parse import urlencode

import requests


@dataclass
class LitSenseResult:
    """
    LitSense API search result item.
    Represents a single text segment from a PubMed article that matches the query.
    Each result contains the text snippet, its location in the article, and relevance score.
    Attributes:
        pmid: PubMed ID (integer)
        pmcid: PubMed Central ID (e.g., "PMC12354742")
        section: Article section where text was found (e.g., "INTRO", "METHODS", "RESULTS")
        text: The matching text snippet
        score: Relevance score (0.0 to 1.0, higher is more relevant)
        annotations: List of entity annotations (e.g., ["100|5|species|9606"])
    Example:
        >>> result = LitSenseResult(
        ...     pmid=40813612,
        ...     pmcid="PMC12354742",
        ...     section="INTRO",
        ...     text="Deep learning algorithms...",
        ...     score=0.85,
        ...     annotations=["100|5|species|9606"]
        ... )
        >>> print(f"PMID {result.pmid}: {result.text[:50]}... (score: {result.score:.2f})")
    """

    pmid: int
    text: str
    score: float
    pmcid: str | None = None
    section: str | None = None
    annotations: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LitSenseResult":
        """
        Create LitSenseResult from API response dictionary.
        Args:
            data: Dictionary from LitSense API response
        Returns:
            LitSenseResult instance
        """
        return cls(
            pmid=int(data.get("pmid", 0)),
            pmcid=data.get("pmcid"),
            section=data.get("section"),
            text=data.get("text", ""),
            score=float(data.get("score", 0.0)),
            annotations=data.get("annotations", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary.
        Returns:
            Dictionary representation
        """
        return {
            "pmid": self.pmid,
            "pmcid": self.pmcid,
            "section": self.section,
            "text": self.text,
            "score": self.score,
            "annotations": self.annotations,
        }

    def get_pmid_str(self) -> str:
        """Get PMID as string."""
        return str(self.pmid)

    def has_annotation(self, annotation_type: str) -> bool:
        """
        Check if result has specific annotation type.
        Args:
            annotation_type: Type to check (e.g., "species", "gene")
        Returns:
            True if annotation type exists
        """
        return any(annotation_type in ann for ann in self.annotations)


class LitSenseAPI:
    """
    LitSense API client for semantic search of PubMed literature.
    This client automatically enforces rate limiting (1 request per second)
    and provides convenient methods for querying the LitSense API.
    Example:
        >>> client = LitSenseAPI()
        >>> results = client.search("machine learning in medicine", rerank=True)
        >>> print(f"Found {len(results)} articles")
        >>> print(results[0]['title'])
    """

    BASE_URL = "https://www.ncbi.nlm.nih.gov/research/litsense-api/api/"

    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Initialize LitSense API client.
        Args:
            rate_limit_delay: Minimum seconds between requests (default: 1.0)
                             Must be >= 1.0 to comply with API limits
        """
        if rate_limit_delay < 1.0:
            raise ValueError("Rate limit delay must be at least 1.0 second")
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "information-composer/0.2.0 (Python LitSense Client)"}
        )

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by waiting if necessary."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            time.sleep(wait_time)
        self._last_request_time = time.time()

    def search(
        self,
        query: str,
        rerank: bool = True,
        timeout: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Search PubMed literature using LitSense semantic search.
        Args:
            query: Search query string
            rerank: Whether to rerank results by relevance (default: True)
            timeout: Request timeout in seconds (default: 30)
        Returns:
            List of article dictionaries (maximum 100 results)
            Each article contains fields like:
            - pmid: PubMed ID
            - title: Article title
            - abstract: Article abstract
            - authors: List of authors
            - journal: Journal name
            - pubdate: Publication date
            - score: Relevance score (if rerank=True)
        Raises:
            ValueError: If query is empty
            requests.RequestException: If API request fails
            RuntimeError: If API returns an error
        Example:
            >>> client = LitSenseAPI()
            >>> results = client.search("CRISPR gene editing", rerank=True)
            >>> for article in results[:5]:
            ...     print(f"{article['pmid']}: {article['title']}")
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        # Enforce rate limiting
        self._enforce_rate_limit()
        # Build request URL
        params = {
            "query": query.strip(),
            "rerank": "true" if rerank else "false",
        }
        url = f"{self.BASE_URL}?{urlencode(params)}"
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            # Check for API errors
            if isinstance(data, dict) and "error" in data:
                raise RuntimeError(f"LitSense API error: {data['error']}")
            # Return results (should be a list)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "results" in data:
                return data["results"]
            else:
                raise RuntimeError(f"Unexpected API response format: {type(data)}")
        except requests.Timeout:
            raise RuntimeError(
                f"LitSense API request timed out after {timeout} seconds"
            )
        except requests.RequestException as e:
            raise RuntimeError(f"LitSense API request failed: {e}")

    def search_batch(
        self,
        queries: list[str],
        rerank: bool = True,
        timeout: int = 30,
        verbose: bool = False,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Search multiple queries in batch (with automatic rate limiting).
        Args:
            queries: List of search query strings
            rerank: Whether to rerank results (default: True)
            timeout: Request timeout per query (default: 30)
            verbose: Print progress information (default: False)
        Returns:
            Dictionary mapping each query to its results
        Example:
            >>> client = LitSenseAPI()
            >>> queries = ["diabetes treatment", "cancer immunotherapy"]
            >>> results = client.search_batch(queries, verbose=True)
            >>> print(f"Found {len(results['diabetes treatment'])} articles")
        """
        results = {}
        for i, query in enumerate(queries, 1):
            if verbose:
                print(f"Processing query {i}/{len(queries)}: {query[:50]}...")
            try:
                query_results = self.search(query, rerank=rerank, timeout=timeout)
                results[query] = query_results
                if verbose:
                    print(f"  Found {len(query_results)} results")
            except Exception as e:
                if verbose:
                    print(f"  Error: {e}")
                results[query] = []
        return results

    def get_pmids(
        self,
        query: str,
        rerank: bool = True,
        limit: int | None = None,
    ) -> list[str]:
        """
        Get only PMIDs from search results.
        Args:
            query: Search query string
            rerank: Whether to rerank results (default: True)
            limit: Maximum number of PMIDs to return (default: None, returns all)
        Returns:
            List of PMIDs as strings
        Example:
            >>> client = LitSenseAPI()
            >>> pmids = client.get_pmids("COVID-19 vaccine", limit=10)
            >>> print(pmids)
        """
        results = self.search(query, rerank=rerank)
        pmids = [
            str(article.get("pmid", "")) for article in results if article.get("pmid")
        ]
        if limit:
            pmids = pmids[:limit]
        return pmids

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def search_litsense(
    query: str,
    rerank: bool = True,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """
    Convenience function for one-time LitSense search.
    Args:
        query: Search query string
        rerank: Whether to rerank results (default: True)
        timeout: Request timeout in seconds (default: 30)
    Returns:
        List of article dictionaries
    Example:
        >>> from information_composer.pubmed.litsense import search_litsense
        >>> results = search_litsense("machine learning diagnosis")
        >>> print(f"Found {len(results)} articles")
    """
    with LitSenseAPI() as client:
        return client.search(query, rerank=rerank, timeout=timeout)
