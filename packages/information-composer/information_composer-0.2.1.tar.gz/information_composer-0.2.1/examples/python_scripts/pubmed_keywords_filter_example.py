#!/usr/bin/env python3
"""
PubMed Keywords Filter Example

This example demonstrates how to filter PubMed baseline data using specific
keywords. It shows how to use the load_baseline function to process large
XML files and filter publications based on keyword presence in titles and abstracts.

The example covers:
- Loading PubMed baseline XML data
- Filtering publications by keywords
- Text cleaning and preprocessing
- Statistical analysis of keyword distribution
- Exporting filtered results to CSV

Requirements:
    - PubMed baseline XML file (pubmed24n1219.xml.gz)
    - information_composer package installed
    - pandas package for data manipulation

Usage:
    python pubmed_keywords_filter_example.py

Note:
    This example requires a PubMed baseline XML file which is large (~GB).
    Download from: https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/
"""

from pathlib import Path
from typing import cast

import pandas as pd

from information_composer.pubmed.baseline import load_baseline


def clean_text(text):
    """
    Clean text by removing extra whitespace and newlines.

    This function normalizes text data by removing excessive whitespace
    and newline characters that may be present in the raw XML data.
    It handles NaN values gracefully by returning empty strings.

    Args:
        text: Input text string, may contain NaN values

    Returns:
        str: Cleaned text with normalized whitespace

    Example:
        >>> clean_text("  hello   world  \n\n  ")
        "hello world"
        >>> clean_text(pd.NA)
        ""
    """
    if pd.isna(text):
        return ""
    return " ".join(str(text).split())


def main():
    """
    Demonstrate PubMed baseline data filtering with keyword analysis.

    This function shows how to process large PubMed baseline datasets
    to find publications containing specific keywords. It demonstrates
    the complete workflow from data loading to statistical analysis.

    The function:
    1. Loads PubMed baseline XML data
    2. Filters publications by keyword presence
    3. Cleans and normalizes text data
    4. Performs statistical analysis
    5. Exports results to CSV format

    Args:
        None

    Returns:
        None

    Raises:
        FileNotFoundError: When PubMed data file is not found
        ValueError: When invalid parameters are provided
        Exception: When data processing fails

    Example:
        >>> main()
        Looking for PubMed data file at: /path/to/pubmed24n1219.xml.gz
        Keywords: promoter, cis-regulatory, cis-element, enhancer, silencer, operator
        Results Summary:
        Total matching papers found: 1250
    """
    # Step 1: Set up file paths using Path objects for cross-platform compatibility
    current_dir = Path(__file__).parent
    data_dir = (current_dir / ".." / "data" / "pubmedbaseline").resolve()
    xml_file = data_dir / "pubmed24n1219.xml.gz"

    # Step 2: Define keywords for filtering publications
    # These keywords target regulatory elements and related concepts
    keywords = [
        "promoter",  # DNA sequences that initiate transcription
        "cis-regulatory",  # Regulatory elements on the same DNA molecule
        "cis-element",  # Specific regulatory DNA sequences
        "enhancer",  # DNA sequences that increase transcription
        "silencer",  # DNA sequences that decrease transcription
        "operator",  # DNA sequences that control gene expression
    ]

    # Display configuration information
    print(f"Looking for PubMed data file at: {xml_file}")
    print(f"Keywords: {', '.join(keywords)}")

    # Step 3: Validate that the PubMed data file exists
    if not xml_file.exists():
        print(f"\nError: PubMed data file not found at {xml_file}")
        print("\nPlease ensure the file 'pubmed24n1219.xml.gz' exists in:")
        print(f"   {data_dir}")
        print("\nDownload from: https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/")
        return

    try:
        # Step 4: Load and filter the PubMed baseline data
        print("\nLoading and filtering PubMed data...")
        result = load_baseline(
            str(xml_file),  # Path to the XML file
            output_type="pd",  # Return as pandas DataFrame
            keywords=keywords,  # Keywords to search for
            kw_filter="both",  # Search in both title and abstract
            log=True,  # Enable logging for progress tracking
        )
        # Type assertion to help type checker understand the return type
        df = cast(pd.DataFrame, result)

        # Step 5: Clean and normalize text data
        print("Cleaning text data...")
        text_columns = ["title", "abstract", "journal"]
        for col in text_columns:
            if col in df.columns:
                # Apply text cleaning to remove extra whitespace
                df[col] = df[col].apply(clean_text)

        # Step 6: Display summary statistics
        print("\nResults Summary:")
        print(f"Total matching papers found: {len(df)}")

        # Step 7: Perform keyword frequency analysis
        print("\nAnalyzing keyword distribution...")
        keyword_counts = {}
        for keyword in keywords:
            # Count occurrences in title and abstract separately
            title_count = df["title"].str.contains(keyword, case=False).sum()
            abstract_count = df["abstract"].str.contains(keyword, case=False).sum()
            keyword_counts[keyword] = {
                "title": title_count,
                "abstract": abstract_count,
                "total": title_count + abstract_count,
            }

        # Step 8: Display keyword statistics in formatted table
        print("\nKeyword Statistics:")
        print("-" * 60)
        print(f"{'Keyword':<15} {'Title':<10} {'Abstract':<10} {'Total':<10}")
        print("-" * 60)
        for keyword, counts in keyword_counts.items():
            print(
                f"{keyword:<15} "
                f"{counts['title']:<10} "
                f"{counts['abstract']:<10} "
                f"{counts['total']:<10}"
            )

        # Step 9: Export filtered results to CSV file
        output_file = data_dir / "pubmed_filtered_results.csv"
        print(f"\nSaving results to {output_file}...")
        df.to_csv(
            output_file,
            index=True,  # Include row indices
            quoting=1,  # Quote all fields to handle special characters
        )
        print(f"Results saved to {output_file}")

    except Exception as e:
        print(f"An error occurred during processing: {str(e)}")
        print("Please check the file path and ensure the XML file is valid.")


if __name__ == "__main__":
    # Entry point for the script
    # This ensures the demo only runs when the script is executed directly,
    # not when imported as a module
    main()
