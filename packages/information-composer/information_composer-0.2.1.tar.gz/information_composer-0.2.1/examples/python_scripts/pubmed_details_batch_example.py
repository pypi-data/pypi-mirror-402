#!/usr/bin/env python3
"""
PubMed Batch Details Processing Example

This example demonstrates how to perform large-scale PubMed data collection
and processing. It shows how to query PubMed for publications, save PMIDs,
and then fetch detailed information for all publications in batches.

The example covers:
- Querying PubMed with date range filtering
- Saving PMIDs to file for persistence
- Batch processing with caching for efficiency
- Progress tracking and performance monitoring
- Error handling and cache management

Requirements:
    - Valid email address for PubMed API compliance
    - Internet connection for API access
    - information_composer package installed
    - tqdm package for progress bars

Usage:
    python pubmed_details_batch_example.py

Note:
    This example processes large amounts of data and may take significant time.
    Caching is used to avoid re-fetching data on subsequent runs.
"""

import json
from pathlib import Path
import time

from tqdm import tqdm

from information_composer.pubmed.pubmed import (
    clean_pubmed_cache,
    fetch_pubmed_details_batch_sync,
    query_pmid_by_date,
)


def main(query: str, output_file: str, pmid_file: str):
    """
    Process a large-scale PubMed query and fetch detailed information.

    This function demonstrates a complete workflow for academic research:
    1. Query PubMed for publications matching a search term
    2. Save the PMIDs to a file for persistence
    3. Fetch detailed information for all publications in batches
    4. Save complete results to JSON format
    5. Clean up temporary cache files

    The function uses caching to improve performance and handles large
    datasets efficiently by processing them in chunks.

    Args:
        query (str): Search query string for PubMed
        output_file (str): Path to save detailed results JSON file
        pmid_file (str): Path to save PMIDs list file

    Returns:
        None

    Raises:
        ConnectionError: When unable to connect to PubMed API
        ValueError: When invalid parameters are provided
        FileNotFoundError: When unable to create output files

    Example:
        >>> main("cis-regulatory elements", "results.json", "pmids.txt")
        Querying PubMed for publications about cis-regulatory elements ...
        Found 150 publications in 2.34 seconds
        Fetching detailed information for each publication...
        Fetched details for 150 articles in 45.67 seconds
    """
    # Create cache directory for storing temporary data
    # This improves performance by avoiding re-fetching data
    cache_dir = Path("pubmed_cache")

    try:
        # Step 1: Query PubMed for publications matching the search term
        print(f"Querying PubMed for publications about {query} ...")
        start_time = time.time()

        # Query with 36-month intervals for efficient processing
        # This balances API rate limits with processing speed
        pmids = query_pmid_by_date(
            query=query,
            email="your_email@example.com",  # Required for API compliance
            # start_date="2024/01/01",  # Uncomment to limit date range
            batch_months=36,  # Process in 36-month chunks for efficiency
        )

        # Calculate and display query performance
        query_time = time.time() - start_time
        print(f"Found {len(pmids)} publications in {query_time:.2f} seconds\n")

        # Step 2: Save PMIDs to file for persistence and debugging
        print(f"Saving PMIDs to {pmid_file}...")
        with open(pmid_file, "w") as f:
            f.write("\n".join(map(str, pmids)))
        print(f"Saved {len(pmids)} PMIDs to file")

        # Step 3: Fetch detailed information in batches with caching
        print("Fetching detailed information for each publication...")
        start_time = time.time()

        # Use batch processing with caching for efficiency
        # Chunk size of 100 balances memory usage with API efficiency
        results = fetch_pubmed_details_batch_sync(
            pmids=pmids,
            email="your_email@example.com",  # Same email for consistency
            cache_dir=cache_dir,  # Enable caching for performance
            chunk_size=100,  # Process 100 PMIDs at a time
            delay_between_chunks=1.0,  # 1-second delay to respect rate limits
        )

        # Calculate and display fetch performance
        fetch_time = time.time() - start_time
        print(
            f"\nFetched details for {len(results)} articles in {fetch_time:.2f} seconds"
        )

        # Step 4: Save complete results to JSON file
        print("\nSaving results to file...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Full results have been saved to {output_file}")

        # Step 5: Display summary of results with progress bar
        print("\nGenerating summary...")
        for article in tqdm(results, desc="Processing results"):
            # Skip articles with errors (e.g., PMID not found)
            if "error" in article:
                continue

            # Display formatted article information
            print("=" * 80)
            print(f"PMID: {article['pmid']}")
            print(f"Title: {article['title']}")
            print(f"Journal: {article['journal']} ({article.get('pubdate', 'N/A')})")
            print(f"Authors: {', '.join(article.get('authors', []))}")
            print("\n")

    finally:
        # Step 6: Clean up cache files to free disk space
        print("\nCleaning up cache...")
        deleted_count = clean_pubmed_cache(cache_dir)
        print(f"Cleaned up {deleted_count} cache files")


if __name__ == "__main__":
    # Entry point for the script
    # This demonstrates the complete workflow with example parameters
    # Uncomment the first line to use default parameters, or modify as needed

    # main(query="cis-regulatory elements", output_file="pubmed_batch_results.json")
    main(
        query="cis-regulatory elements",  # Search term for cis-regulatory elements
        output_file="./data/CRM_pubmed_batch_results.json",  # Output file for results
        pmid_file="./data/CRM_pmids.txt",  # File to save PMIDs list
    )
