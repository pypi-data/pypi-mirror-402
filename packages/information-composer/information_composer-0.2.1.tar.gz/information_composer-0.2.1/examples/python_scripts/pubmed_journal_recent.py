#!/usr/bin/env python3
"""
PubMed Molecular Plant Recent Publications Example

This example demonstrates how to query PubMed for recent publications in
Molecular Plant journal from the last week and display detailed information
including title, abstract, DOI, authors, and publication date.

Requirements:
    - Valid email address for PubMed API compliance
    - Internet connection for API access
    - information_composer package installed

Usage:
    python pubmed_molecular_plant_recent.py

Note:
    PubMed API requires a valid email address for identification.
    Please replace 'your_email@example.com' with your actual email.
"""

import asyncio
from datetime import datetime, timedelta

from information_composer.pubmed.pubmed import (
    fetch_pubmed_details_batch,
    query_pmid_by_date,
)


def format_authors(authors):
    """Format authors list for display."""
    if not authors or authors == ["N/A"]:
        return "N/A"
    if len(authors) > 5:
        return ", ".join(authors[:5]) + f" et al. ({len(authors)} total)"
    return ", ".join(authors)


def format_abstract(abstract, max_length=500):
    """Format abstract with length limit."""
    if abstract == "No abstract available":
        return abstract
    if len(abstract) > max_length:
        return abstract[:max_length] + "..."
    return abstract


async def query_molecular_plant_recent():
    """
    Query PubMed for recent Molecular Plant publications from the last week.

    This function demonstrates:
    - Date-based searching for recent publications
    - Journal-specific queries
    - Fetching detailed article information
    - Displaying formatted results

    The search targets papers published in Molecular Plant journal within
    the last 7 days and retrieves full details including abstract, authors,
    DOI, and publication date.
    """
    # Configure search parameters
    email = "your_email@example.com"  # Replace with your email

    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Format dates for PubMed query (YYYY/MM/DD)
    start_date_str = start_date.strftime("%Y/%m/%d")
    end_date_str = end_date.strftime("%Y/%m/%d")

    print("=" * 80)
    print("Molecular Plant - Recent Publications (Last 7 Days)")
    print("=" * 80)
    print(f"Search Period: {start_date_str} to {end_date_str}")
    print("Journal: Molecular Plant")
    print("=" * 80)
    print()

    # Step 1: Query PMIDs
    print("Step 1: Searching for PMIDs...")
    query = "Molecular Plant[Journal]"
    # query = "Nature[Journal]"
    pmids = query_pmid_by_date(
        query=query,
        email=email,
        start_date=start_date_str,
        end_date=end_date_str,
        batch_months=1,  # Use small batch for recent papers
    )

    print(f"Found {len(pmids)} publications\n")

    if not pmids:
        print("No publications found in the specified date range.")
        return

    # Step 2: Fetch detailed information
    print("Step 2: Fetching detailed information...")
    details = await fetch_pubmed_details_batch(
        pmids=pmids,
        email=email,
        chunk_size=50,  # Fetch in chunks of 50
        delay_between_chunks=0.5,  # Short delay between chunks
    )

    print(f"\nRetrieved details for {len(details)} publications\n")
    print("=" * 80)

    # Step 3: Display results
    for idx, paper in enumerate(details, 1):
        print(f"\n[{idx}] {paper.get('title', 'N/A')}")
        print("-" * 80)

        # Publication information
        print(f"PMID:         {paper.get('pmid', 'N/A')}")
        print(f"DOI:          {paper.get('doi', 'N/A')}")
        print(f"Journal:      {paper.get('journal', 'N/A')}")
        print(f"Pub Date:     {paper.get('pubdate', 'N/A')}")

        # Authors
        authors = format_authors(paper.get("authors", []))
        print(f"Authors:      {authors}")

        # Publication types
        pub_types = paper.get("publication_types", [])
        if pub_types and pub_types != ["N/A"]:
            print(f"Pub Types:    {', '.join(pub_types)}")

        # Keywords/MeSH terms
        keywords = paper.get("keywords", [])
        mesh_terms = paper.get("mesh_terms", [])
        if keywords and keywords != ["N/A"]:
            print(f"Keywords:     {', '.join(keywords[:5])}")
        elif mesh_terms and mesh_terms != ["N/A"]:
            print(f"MeSH Terms:   {', '.join(mesh_terms[:5])}")

        # Abstract
        abstract = format_abstract(paper.get("abstract", "No abstract available"))
        print("\nAbstract:")
        print(abstract)

        print("=" * 80)

    # Summary statistics
    print("\n\nSummary:")
    print(f"Total publications found: {len(details)}")
    print(f"Date range: {start_date_str} to {end_date_str}")
    print("Journal: Molecular Plant")

    # Count papers with DOI
    with_doi = sum(1 for p in details if p.get("doi") != "N/A")
    print(f"Papers with DOI: {with_doi}/{len(details)}")

    # Count papers with abstract
    with_abstract = sum(
        1 for p in details if p.get("abstract") != "No abstract available"
    )
    print(f"Papers with abstract: {with_abstract}/{len(details)}")


def main():
    """Main entry point."""
    try:
        asyncio.run(query_molecular_plant_recent())
    except KeyboardInterrupt:
        print("\n\nSearch interrupted by user.")
    except Exception as e:
        print(f"\nError occurred: {e}")
        raise


if __name__ == "__main__":
    main()
