#!/usr/bin/env python3
"""
Google Scholar Basic Search Example

This example demonstrates how to perform basic searches using the Google Scholar
crawler. It shows the fundamental workflow for academic paper discovery and
result processing.

The example covers:
- Basic search configuration and setup
- Simple query execution
- Result processing and display
- Data export capabilities
- Error handling and best practices

Requirements:
    - Internet connection for web scraping
    - information_composer package installed
    - Optional: Selenium for advanced features

Usage:
    python google_scholar_basic_example.py

Note:
    This example uses web scraping techniques. Be respectful of rate limits
    and terms of service. Consider using delays between requests.
"""

import asyncio
from pathlib import Path

from information_composer.sites.google_scholar import (
    GoogleScholarCrawler,
    SearchConfig,
)


async def basic_search_example():
    """
    Demonstrate basic Google Scholar search functionality.

    This function shows how to perform a simple academic search using
    Google Scholar crawler. It demonstrates configuration, execution,
    and result processing.

    Args:
        None

    Returns:
        SearchResult: The search results object containing papers and metadata

    Raises:
        ConnectionError: When unable to connect to Google Scholar
        Exception: When search execution fails

    Example:
        >>> result = await basic_search_example()
        🔍 Google Scholar Basic Search Example
        ==================================================
        Searching for: machine learning natural language processing
        ...
    """
    print("🔍 Google Scholar Basic Search Example")
    print("=" * 50)

    # Step 1: Configure search parameters
    # These settings balance result quality with performance
    config = SearchConfig(
        max_results=20,  # Limit results for demonstration
        year_range=(2020, 2023),  # Focus on recent publications
        include_citations=True,  # Include citation counts
        include_abstracts=True,  # Include paper abstracts
        rate_limit=2.0,  # 2-second delay between requests
        cache_dir="./cache/google_scholar",  # Cache directory for performance
        cache_ttl_days=7,  # Cache results for 7 days
    )

    # Initialize crawler
    async with GoogleScholarCrawler(config=config) as crawler:
        try:
            # Perform search
            query = "machine learning natural language processing"
            print(f"Searching for: {query}")
            print(f"Year range: {config.year_range[0]}-{config.year_range[1]}")
            print(f"Max results: {config.max_results}")
            print()

            result = await crawler.search(query)

            # Display results summary
            print("📊 Search Results Summary:")
            print(f"   Query: {result.query}")
            print(f"   Papers found: {len(result.papers)}")
            print(f"   Search time: {result.search_time:.2f} seconds")
            print(f"   Strategy used: {result.strategy_used.value}")
            print(f"   Valid papers: {result.valid_papers}")
            print(f"   Papers with DOI: {result.papers_with_doi}")
            print(f"   Papers with abstracts: {result.papers_with_abstract}")
            print()

            # Display top papers
            print("📄 Top 5 Papers:")
            print("-" * 50)

            for i, paper in enumerate(result.papers[:5], 1):
                print(f"{i}. {paper.title}")

                if paper.authors:
                    authors_str = ", ".join(paper.authors[:3])
                    if len(paper.authors) > 3:
                        authors_str += " et al."
                    print(f"   👥 Authors: {authors_str}")

                if paper.journal:
                    print(f"   📚 Published in: {paper.journal}")

                if paper.year:
                    print(f"   📅 Year: {paper.year}")

                if paper.citation_count > 0:
                    print(f"   📊 Citations: {paper.citation_count}")

                if paper.doi:
                    print(f"   🔗 DOI: {paper.doi}")

                if paper.abstract:
                    abstract_preview = (
                        paper.abstract[:200] + "..."
                        if len(paper.abstract) > 200
                        else paper.abstract
                    )
                    print(f"   📝 Abstract: {abstract_preview}")

                print(f"   ⭐ Confidence: {paper.confidence_score:.2f}")
                print()

            # Export results to JSON
            output_file = "search_results_basic.json"
            await crawler.export_results(result, output_file, "json")
            print(f"📁 Results exported to: {output_file}")

            return result

        except Exception as e:
            print(f"❌ Error during search: {e}")
            return None


if __name__ == "__main__":
    asyncio.run(basic_search_example())
