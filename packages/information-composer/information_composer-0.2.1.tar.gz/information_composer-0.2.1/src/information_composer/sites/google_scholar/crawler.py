"""Main Google Scholar crawler interface."""

import asyncio
import json
import logging
from pathlib import Path
import re
import time
from typing import Any

from information_composer.sites.base import BaseSiteCollector

from .core.data_extractor import DataExtractor
from .core.result_processor import ResultProcessor
from .core.search_engine import SearchEngine
from .models import GoogleScholarPaper, SearchConfig, SearchResult, SearchStrategy
from .utils.cache_manager import CacheManager


logger = logging.getLogger(__name__)


class GoogleScholarCrawler(BaseSiteCollector):
    """Main interface for Google Scholar paper crawling."""

    search_config: SearchConfig
    use_cache: bool
    search_engine: SearchEngine
    data_extractor: DataExtractor
    result_processor: ResultProcessor
    cache_manager: CacheManager | None

    def __init__(
        self,
        config: SearchConfig | None = None,
        cache_dir: str | None = None,
        use_cache: bool = True,
    ):
        """
        Initialize Google Scholar crawler.
        Args:
            config: Search configuration
            cache_dir: Directory for caching results
            use_cache: Whether to use caching
        """
        super().__init__()
        self.search_config = config or SearchConfig()
        self.use_cache = use_cache
        # Initialize components
        self.search_engine = SearchEngine(self.search_config)
        self.data_extractor = DataExtractor()
        self.result_processor = ResultProcessor(self.search_config)
        # Initialize cache manager
        if use_cache:
            cache_path = (
                cache_dir or self.search_config.cache_dir or "google_scholar_cache"
            )
            self.cache_manager = CacheManager(
                cache_path, self.search_config.cache_ttl_days
            )
        else:
            self.cache_manager = None
        logger.info(
            f"GoogleScholarCrawler initialized with strategy: "
            f"{self.search_config.search_strategy}"
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        year_range: tuple | None = None,
        **kwargs: Any,
    ) -> SearchResult:
        """
        Search Google Scholar for papers.
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            year_range: Tuple of (start_year, end_year) for filtering
            **kwargs: Additional search parameters
        Returns:
            SearchResult object containing papers and metadata
        """
        start_time = time.time()
        # Update config with parameters
        if max_results:
            self.search_config.max_results = max_results
        if year_range:
            self.search_config.year_range = year_range
        # Check cache first
        if self.cache_manager:
            cached_result = await self._get_cached_result(query, self.search_config)
            if cached_result:
                logger.info(
                    f"Retrieved {len(cached_result.papers)} cached results "
                    f"for query: {query}"
                )
                return cached_result
        logger.info(f"Starting search for query: {query}")
        try:
            # Execute search
            raw_elements, search_metadata = await self.search_engine.search(query)
            if not raw_elements:
                logger.warning(f"No results found for query: {query}")
                return SearchResult(
                    query=query,
                    search_time=time.time() - start_time,
                    strategy_used=SearchStrategy(
                        search_metadata.get("strategy", "requests")
                    ),
                    search_config=self.search_config,
                )
            # Extract paper data
            papers = self.data_extractor.extract_papers(raw_elements, query)
            logger.info(
                f"Extracted {len(papers)} papers from {len(raw_elements)} elements"
            )
            # Process and enhance papers
            processed_papers = await self.result_processor.process_papers(papers)
            logger.info(f"Processed to {len(processed_papers)} final papers")
            # Create result
            result = SearchResult(
                papers=processed_papers,
                query=query,
                total_results=len(processed_papers),
                search_time=time.time() - start_time,
                strategy_used=SearchStrategy(
                    search_metadata.get("strategy", "requests")
                ),
                search_config=self.search_config,
            )
            # Update statistics
            result.update_statistics()
            # Cache result
            if self.cache_manager:
                await self._cache_result(query, result, self.search_config)
            logger.info(
                f"Search completed in {result.search_time:.2f}s with {len(result.papers)} papers"
            )
            return result
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    async def search_batch(
        self,
        queries: list[str],
        max_results_per_query: int = 50,
        delay_between_queries: float | None = None,
        **kwargs: Any,
    ) -> dict[str, SearchResult]:
        """
        Search multiple queries in batch.
        Args:
            queries: List of search query strings
            max_results_per_query: Maximum results per query
            delay_between_queries: Delay between queries (uses config default if None)
            **kwargs: Additional search parameters
        Returns:
            Dictionary mapping queries to SearchResult objects
        """
        logger.info(f"Starting batch search for {len(queries)} queries")
        results: dict[str, SearchResult] = {}
        delay = delay_between_queries or self.search_config.rate_limit
        for i, query in enumerate(queries):
            try:
                logger.info(f"Processing query {i + 1}/{len(queries)}: {query}")
                result = await self.search(
                    query=query, max_results=max_results_per_query, **kwargs
                )
                results[query] = result
                # Add delay between queries (except for the last one)
                if i < len(queries) - 1:
                    await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                # Create empty result for failed queries
                results[query] = SearchResult(
                    query=query, search_config=self.search_config
                )
        logger.info(f"Batch search completed. Processed {len(results)} queries")
        return results

    async def advanced_search(
        self,
        title_keywords: list[str] | None = None,
        author_names: list[str] | None = None,
        journal_names: list[str] | None = None,
        exact_phrase: str | None = None,
        exclude_terms: list[str] | None = None,
        **kwargs: Any,
    ) -> SearchResult:
        """
        Perform advanced search with structured parameters.
        Args:
            title_keywords: Keywords that must appear in title
            author_names: Author names to search for
            journal_names: Journal names to search for
            exact_phrase: Exact phrase that must appear
            exclude_terms: Terms to exclude from results
            **kwargs: Additional search parameters
        Returns:
            SearchResult object
        """
        # Build advanced query
        query_parts = []
        if exact_phrase:
            query_parts.append(f'"{exact_phrase}"')
        if title_keywords:
            for keyword in title_keywords:
                query_parts.append(f'intitle:"{keyword}"')
        if author_names:
            for author in author_names:
                query_parts.append(f'author:"{author}"')
        if journal_names:
            # Google Scholar doesn't have a direct journal search, so include in general search
            for journal in journal_names:
                query_parts.append(f'"{journal}"')
        if exclude_terms:
            for term in exclude_terms:
                query_parts.append(f'-"{term}"')
        if not query_parts:
            raise ValueError("At least one search parameter must be provided")
        query = " ".join(query_parts)
        logger.info(f"Advanced search query: {query}")
        return await self.search(query, **kwargs)

    def get_paper_by_id(self, google_scholar_id: str) -> GoogleScholarPaper | None:
        """
        Get a specific paper by Google Scholar ID from cache.
        Args:
            google_scholar_id: Google Scholar paper ID
        Returns:
            GoogleScholarPaper object if found, None otherwise
        """
        if not self.cache_manager:
            return None
        # This would search through cached results
        # TODO: Implement ID-based lookup in cache
        return None

    async def export_results(
        self,
        results: SearchResult | list[GoogleScholarPaper],
        output_file: str,
        format: str = "json",
    ) -> None:
        """
        Export search results to file.
        Args:
            results: SearchResult or list of papers to export
            output_file: Output file path
            format: Export format (json, csv, bibtex)
        """
        if isinstance(results, SearchResult):
            papers = results.papers
        else:
            papers = results
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Validate and auto-detect format
        format = self._validate_export_format(output_file, format)
        if format.lower() == "json":
            await self._export_json(papers, output_path)
        elif format.lower() == "csv":
            await self._export_csv(papers, output_path)
        elif format.lower() == "bibtex":
            await self._export_bibtex(papers, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        logger.info(f"Exported {len(papers)} papers to {output_file}")

    def _validate_export_format(self, output_file: str, format: str | None) -> str:
        """
        Validate and auto-detect export format.
        Args:
            output_file: Output file path
            format: Requested format (or None for auto-detection)
        Returns:
            Validated format string
        """
        # Auto-detect from file extension if format not specified
        if format is None:
            ext = Path(output_file).suffix.lower()
            format_map = {".json": "json", ".csv": "csv", ".bib": "bibtex"}
            format = format_map.get(ext, "json")
        # Validate format
        valid_formats = ["json", "csv", "bibtex"]
        if format.lower() not in valid_formats:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Supported formats: {', '.join(valid_formats)}"
            )
        return format.lower()

    async def _export_json(
        self, papers: list[GoogleScholarPaper], output_path: Path
    ) -> None:
        """Export papers to JSON format."""
        data = {
            "papers": [paper.to_dict() for paper in papers],
            "export_date": time.time(),
            "total_papers": len(papers),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def _export_csv(
        self, papers: list[GoogleScholarPaper], output_path: Path
    ) -> None:
        """Export papers to CSV format."""
        import csv

        fieldnames = [
            "title",
            "authors",
            "journal",
            "year",
            "doi",
            "pubmed_id",
            "citation_count",
            "abstract",
            "pdf_url",
            "google_scholar_url",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for paper in papers:
                row = {
                    "title": paper.title,
                    "authors": "; ".join(paper.authors),
                    "journal": paper.journal,
                    "year": paper.year,
                    "doi": paper.doi,
                    "pubmed_id": paper.pubmed_id,
                    "citation_count": paper.citation_count,
                    "abstract": paper.abstract,
                    "pdf_url": paper.pdf_url,
                    "google_scholar_url": paper.google_scholar_url,
                }
                writer.writerow(row)

    async def _export_bibtex(
        self, papers: list[GoogleScholarPaper], output_path: Path
    ) -> None:
        """Export papers to BibTeX format."""
        with open(output_path, "w", encoding="utf-8") as f:
            for paper in papers:
                bibtex_entry = self._paper_to_bibtex(paper)
                f.write(bibtex_entry + "\n\n")

    def _paper_to_bibtex(self, paper: GoogleScholarPaper) -> str:
        """Convert paper to BibTeX format."""
        # Generate citation key
        first_author = paper.authors[0].split()[-1] if paper.authors else "unknown"
        year = paper.year or "unknown"
        title_words = paper.title.split()[:3] if paper.title else ["unknown"]
        key = f"{first_author}{year}{''.join(title_words)}"
        key = re.sub(r"[^a-zA-Z0-9]", "", key)
        # Determine entry type
        entry_type = "article" if paper.journal else "inproceedings"
        bibtex = f"@{entry_type}{{{key},\n"
        bibtex += f"  title = {{{paper.title}}},\n"
        if paper.authors:
            authors_str = " and ".join(paper.authors)
            bibtex += f"  author = {{{authors_str}}},\n"
        if paper.journal:
            bibtex += f"  journal = {{{paper.journal}}},\n"
        if paper.year:
            bibtex += f"  year = {{{paper.year}}},\n"
        if paper.volume:
            bibtex += f"  volume = {{{paper.volume}}},\n"
        if paper.issue:
            bibtex += f"  number = {{{paper.issue}}},\n"
        if paper.pages:
            bibtex += f"  pages = {{{paper.pages}}},\n"
        if paper.doi:
            bibtex += f"  doi = {{{paper.doi}}},\n"
        if paper.google_scholar_url:
            bibtex += f"  url = {{{paper.google_scholar_url}}},\n"
        bibtex += "}"
        return bibtex

    async def _get_cached_result(
        self, query: str, config: SearchConfig
    ) -> SearchResult | None:
        """Get cached search result."""
        if not self.cache_manager:
            return None
        try:
            return await self.cache_manager.get_cached_search(query, config)
        except Exception as e:
            logger.warning(f"Error retrieving cache: {e}")
            return None

    async def _cache_result(
        self, query: str, result: SearchResult, config: SearchConfig
    ) -> None:
        """Cache search result."""
        if not self.cache_manager:
            return
        try:
            await self.cache_manager.cache_search_results(query, result, config)
        except Exception as e:
            logger.warning(f"Error caching result: {e}")

    def collect(self, query: str = "", **kwargs: Any) -> SearchResult:
        """
        Synchronous interface for compatibility with BaseSiteCollector.
        Args:
            query: Search query
            **kwargs: Additional search parameters
        Returns:
            SearchResult object
        """
        return asyncio.run(self.search(query, **kwargs))

    def compose(self, data: SearchResult) -> dict:
        """
        Compose search results into a structured format.
        Args:
            data: SearchResult object
        Returns:
            Composed data dictionary
        """
        return {
            "summary": {
                "query": data.query,
                "total_papers": len(data.papers),
                "search_time": data.search_time,
                "strategy_used": data.strategy_used.value,
                "valid_papers": data.valid_papers,
                "papers_with_doi": data.papers_with_doi,
                "papers_with_abstract": data.papers_with_abstract,
            },
            "papers": [paper.to_dict() for paper in data.papers],
            "statistics": {
                "avg_citation_count": sum(p.citation_count for p in data.papers)
                / len(data.papers)
                if data.papers
                else 0,
                "year_distribution": self._get_year_distribution(data.papers),
                "top_journals": self._get_top_journals(data.papers),
            },
        }

    def _get_year_distribution(
        self, papers: list[GoogleScholarPaper]
    ) -> dict[int, int]:
        """Get distribution of papers by year."""
        year_counts: dict[int, int] = {}
        for paper in papers:
            if paper.year:
                year_counts[paper.year] = year_counts.get(paper.year, 0) + 1
        return dict(sorted(year_counts.items()))

    def _get_top_journals(
        self, papers: list[GoogleScholarPaper], top_n: int = 10
    ) -> list[dict]:
        """Get top journals by paper count."""
        journal_counts: dict[str, int] = {}
        for paper in papers:
            if paper.journal:
                journal_counts[paper.journal] = journal_counts.get(paper.journal, 0) + 1
        sorted_journals = sorted(
            journal_counts.items(), key=lambda x: x[1], reverse=True
        )
        return [{"journal": j, "count": c} for j, c in sorted_journals[:top_n]]

    def close(self) -> None:
        """Close the crawler and cleanup resources."""
        if self.search_engine:
            self.search_engine.close()
        logger.info("GoogleScholarCrawler closed")

    def __enter__(self) -> "GoogleScholarCrawler":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    async def __aenter__(self) -> "GoogleScholarCrawler":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        self.close()
