#!/usr/bin/env python3
"""
PubMed Details Fetching Example

This example demonstrates how to retrieve detailed information about specific
publications from PubMed using their PMIDs. It shows how to use the
fetch_pubmed_details function to get comprehensive metadata including authors,
abstracts, journal information, and MeSH terms.

The example covers:
- Fetching details for multiple PMIDs
- Displaying structured publication information
- Handling different data fields and formats
- Saving results to JSON format

Requirements:
    - Valid email address for PubMed API compliance
    - Internet connection for API access
    - information_composer package installed

Usage:
    python pubmed_details_example.py

Note:
    PubMed API requires a valid email address for identification.
    Large batches may be subject to rate limiting.
"""

import json

# from pprint import pprint  # Unused import
from information_composer.pubmed.pubmed import fetch_pubmed_details


def main():
    """
    Demonstrate fetching detailed publication information from PubMed.

    This function shows how to retrieve comprehensive metadata for specific
    publications using their PMIDs. It demonstrates proper handling of
    publication data including authors, abstracts, journal information,
    publication types, and MeSH terms.

    The function processes a predefined list of PMIDs and displays
    formatted information for each publication, then saves the complete
    results to a JSON file for further analysis.

    Args:
        None

    Returns:
        None

    Raises:
        ConnectionError: When unable to connect to PubMed API
        ValueError: When invalid PMIDs are provided
        FileNotFoundError: When unable to create output file

    Example:
        >>> main()
        Retrieved details for 3 articles:

        ================================================================================
        PMID: 39659015
        Title: Example Publication Title
        Journal: Nature (2024)
        Authors: Smith, J., Doe, A., Johnson, B.
        DOI: 10.1038/example
    """
    # Define example PMIDs for demonstration
    # These are real PMIDs that should return valid results
    pmids = ["39659015", "24191062", "26400163"]

    # Fetch detailed information for the specified PMIDs
    # The email parameter is required for PubMed API compliance
    # Replace with your actual email address for production use
    results = fetch_pubmed_details(pmids, email="your_email@example.com")

    # Display summary of retrieved articles
    print(f"Retrieved details for {len(results)} articles:\n")

    # Iterate through each article and display formatted information
    # This demonstrates how to access and display different data fields
    for article in results:
        print("=" * 80)
        print(f"PMID: {article['pmid']}")
        print(f"Title: {article['title']}")
        print(f"Journal: {article['journal']} ({article['pubdate']})")
        print(f"Authors: {', '.join(article['authors'])}")
        print(f"DOI: {article['doi']}")

        # Display publication types (e.g., Journal Article, Review, etc.)
        print("\nPublication Types:")
        for pub_type in article["publication_types"]:
            print(f"- {pub_type}")

        # Display MeSH terms (Medical Subject Headings)
        # These are standardized terms used for indexing
        print("\nMeSH Terms:")
        for term in article["mesh_terms"]:
            print(f"- {term}")

        # Display abstract with length limit for readability
        print("\nAbstract:")
        abstract = article["abstract"]
        if len(abstract) > 300:
            # Truncate long abstracts and add ellipsis
            print(abstract[:300] + "...")
        else:
            print(abstract)
        print("\n")

    # Save complete results to JSON file for further analysis
    # This preserves all data fields including those not displayed
    output_file = "pubmed_details_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Full results have been saved to '{output_file}'")


if __name__ == "__main__":
    # Entry point for the script
    # This ensures the demo only runs when the script is executed directly,
    # not when imported as a module
    main()
