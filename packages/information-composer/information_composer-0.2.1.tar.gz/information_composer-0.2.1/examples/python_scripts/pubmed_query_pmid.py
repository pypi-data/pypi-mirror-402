#!/usr/bin/env python3
"""
PubMed PMID Query Example

This example demonstrates how to query PubMed for publications using different
date ranges and search parameters. It shows how to use the query_pmid_by_date
function to search for academic papers and retrieve their PMIDs.

The example covers:
- Basic query with date range filtering
- Batch processing with different time intervals
- Search parameter customization
- Result handling and display

Requirements:
    - Valid email address for PubMed API compliance
    - Internet connection for API access
    - information_composer package installed

Usage:
    python pubmed_query_pmid.py

Note:
    PubMed API requires a valid email address for identification.
    Rate limiting may apply for large queries.
"""

from information_composer.pubmed.pubmed import query_pmid_by_date


def query_demo():
    """
    Demonstrate PubMed PMID querying with different search strategies.

    This function shows two different approaches to querying PubMed:
    1. Recent publications search with 6-month intervals
    2. Historical search with 12-month intervals and title/abstract filtering

    The function demonstrates best practices for:
    - Setting appropriate batch intervals
    - Using specific search terms
    - Handling query results
    - Displaying search statistics

    Args:
        None

    Returns:
        None

    Raises:
        ConnectionError: When unable to connect to PubMed API
        ValueError: When invalid search parameters are provided

    Example:
        >>> query_demo()
        === Recent Publications (2019-present) ===
        Number of publications found: 150
        First 5 PMIDs: ['12345678', '12345679', ...]
    """
    # Example 1: Search for recent publications with 6-month intervals
    # This approach is efficient for large date ranges as it processes
    # the query in smaller chunks to avoid API timeouts
    recent_pmids = query_pmid_by_date(
        query="cis-regulatory elements",  # General search term
        email="your_email@example.com",  # Required for API compliance
        start_date="2024/01/01",  # Start from beginning of 2024
        batch_months=6,  # Process in 6-month intervals for efficiency
    )

    # Display results for recent publications
    print("=== Recent Publications (2019-present) ===")
    print(f"Number of publications found: {len(recent_pmids)}")
    print(f"First 5 PMIDs: {recent_pmids[:5]}\n")

    # Example 2: Historical search with more specific filtering
    # Using field-specific search syntax to target title and abstract only
    # This reduces noise and improves result relevance
    historical_pmids = query_pmid_by_date(
        query="rice[Title/Abstract]",  # Search only in title and abstract fields
        email="your_email@example.com",  # Same email for consistency
        batch_months=12,  # Larger intervals for historical data
    )

    # Display results for historical search
    print("=== Historical Publications ===")
    print(f"Number of publications found: {len(historical_pmids)}")
    print(f"First 5 PMIDs: {historical_pmids[:5]}")


if __name__ == "__main__":
    # Entry point for the script
    # This ensures the demo only runs when the script is executed directly,
    # not when imported as a module
    query_demo()
