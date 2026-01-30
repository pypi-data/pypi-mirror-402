#!/usr/bin/env python3
"""
PubMed Multiple Journals Recent Publications Example

This example demonstrates how to query PubMed for recent publications from
multiple journals from the last week and display detailed information
including title, abstract, DOI, authors, and publication date.

Requirements:
    - Valid email address for PubMed API compliance
    - Internet connection for API access
    - information_composer package installed

Usage:
    python pubmed_mul_journals_recent.py

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
    Query PubMed for recent publications from multiple journals from the last week.

    This function demonstrates:
    - Date-based searching for recent publications
    - Multi-journal queries
    - Fetching detailed article information
    - Displaying formatted results grouped by journal

    The search targets papers published in specified journals within
    the last 7 days and retrieves full details including abstract, authors,
    DOI, and publication date.
    """
    # Configure search parameters
    email = "your_email@example.com"  # Replace with your email

    # Define journals to query
    journals = ["Molecular Plant", "Nature", "Nature Plants"]

    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Format dates for PubMed query (YYYY/MM/DD)
    start_date_str = start_date.strftime("%Y/%m/%d")
    end_date_str = end_date.strftime("%Y/%m/%d")

    print("=" * 80)
    print("Multi-Journal Recent Publications (Last 7 Days)")
    print("=" * 80)
    print(f"Search Period: {start_date_str} to {end_date_str}")
    print(f"Journals: {', '.join(journals)}")
    print("=" * 80)
    print()

    # Step 1: Query PMIDs for all journals
    print("Step 1: Searching for PMIDs...")
    all_pmids = []
    pmids_by_journal = {}

    for journal in journals:
        print(f"  Querying {journal}...")
        query = f"{journal}[Journal]"
        pmids = query_pmid_by_date(
            query=query,
            email=email,
            start_date=start_date_str,
            end_date=end_date_str,
            batch_months=1,  # Use small batch for recent papers
        )
        pmids_by_journal[journal] = pmids
        all_pmids.extend(pmids)
        print(f"    Found {len(pmids)} publications")

    print(f"\nTotal found: {len(all_pmids)} publications across all journals\n")

    if not all_pmids:
        print("No publications found in the specified date range.")
        return

    # Step 2: Fetch detailed information for all PMIDs
    print("Step 2: Fetching detailed information...")
    details = await fetch_pubmed_details_batch(
        pmids=all_pmids,
        email=email,
        chunk_size=50,  # Fetch in chunks of 50
        delay_between_chunks=0.5,  # Short delay between chunks
    )

    print(f"\nRetrieved details for {len(details)} publications\n")
    print("=" * 80)

    # Create a mapping of PMID to details for easy lookup
    details_map = {paper["pmid"]: paper for paper in details}

    # Step 3: Display results grouped by journal
    overall_idx = 1
    for journal in journals:
        journal_pmids = pmids_by_journal[journal]
        if not journal_pmids:
            continue

        print(f"\n{'=' * 80}")
        print(f"Journal: {journal} ({len(journal_pmids)} publications)")
        print(f"{'=' * 80}")

        for pmid in journal_pmids:
            paper = details_map.get(pmid)
            if not paper:
                continue

            print(f"\n[{overall_idx}]")
            overall_idx += 1
            print(f"Title: {paper.get('title', 'N/A')}")
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

    # Summary statistics
    print("\n\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Date range: {start_date_str} to {end_date_str}")
    print("\nPublications by journal:")
    for journal in journals:
        count = len(pmids_by_journal[journal])
        print(f"  {journal}: {count}")
    print(f"\nTotal publications: {len(details)}")

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
