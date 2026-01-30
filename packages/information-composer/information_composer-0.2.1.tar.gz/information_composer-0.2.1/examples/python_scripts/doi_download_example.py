#!/usr/bin/env python3
"""
DOI Batch Download Example

This example demonstrates how to download multiple academic papers using their
Digital Object Identifiers (DOIs). It shows both single and batch download
workflows with comprehensive result tracking and error handling.

The example covers:
- Single DOI download process
- Batch DOI download with progress tracking
- Result validation and error handling
- CSV export for result analysis
- File organization and naming

Requirements:
    - Valid email address for Crossref API compliance
    - Internet connection for API access
    - information_composer package installed

Usage:
    python doi_download_example.py

Note:
    Crossref API requires a valid email address for identification.
    Batch downloads include delays to respect rate limits.
"""

import csv
import os
from typing import Dict, List

from information_composer.core.doi_downloader import DOIDownloader


def save_results_to_csv(results: list[dict], output_file: str) -> None:
    """
    Save download results to a CSV file for analysis and tracking.

    This function creates a CSV file with standardized columns for
    tracking download results, including success status and error messages.

    Args:
        results (List[Dict]): List of dictionaries containing download results
        output_file (str): Path to the output CSV file

    Returns:
        None

    Raises:
        IOError: When unable to write to the output file
        Exception: For other file operation errors

    Example:
        >>> results = [{"DOI": "10.1000/182", "downloaded": True, ...}]
        >>> save_results_to_csv(results, "downloads.csv")
        Results saved to: downloads.csv
    """
    if not results:  # Check if results is empty
        print("No results to save")
        return

    try:
        fieldnames = ["DOI", "file_name", "downloaded"]
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results to CSV: {str(e)}")


def main():
    """
    Demonstrate both single and batch DOI download workflows.

    This function shows comprehensive DOI download capabilities including:
    1. Single paper download with result tracking
    2. Batch download with multiple DOIs
    3. CSV export for result analysis
    4. Error handling and validation

    Args:
        None

    Returns:
        None

    Raises:
        Exception: When download or file operations fail

    Example:
        >>> main()
        Starting single DOI download example...
        --------------------------------------------------
        Starting batch DOI download example...
        --------------------------------------------------
        Results saved to: downloads/single_download_results.csv
        Results saved to: downloads/batch_download_results.csv
    """
    # Step 1: Configure download settings
    base_dir = os.path.join(os.getcwd(), "downloads")
    email = "your_email@example.com"  # Replace with your actual email

    # Step 2: Initialize the DOI downloader
    downloader = DOIDownloader(email=email)

    try:
        # Step 3: Single DOI download example
        print("Starting single DOI download example...")
        print("-" * 50)
        single_doi = "10.1038/s41477-024-01771-3"  # Example DOI
        single_output_dir = os.path.join(base_dir, "single")

        # Download single paper
        single_result = downloader.download_single(
            doi=single_doi, output_dir=single_output_dir
        )

        # Save single result to CSV
        if single_result:
            single_csv_path = os.path.join(base_dir, "single_download_results.csv")
            save_results_to_csv([single_result], single_csv_path)

        # Step 4: Batch DOI download example
        print("\nStarting batch DOI download example...")
        print("-" * 50)

        # List of DOIs for batch processing
        dois = [
            "10.1038/s41477-024-01771-3",  # Replace with actual DOIs
            "10.1038/s41592-024-02305-7",
            "10.1038/s41592-024-02201-0",
        ]
        batch_output_dir = os.path.join(base_dir, "batch")

        # Download multiple papers with delay between requests
        batch_results = downloader.download_batch(
            dois=dois,
            output_dir=batch_output_dir,
            delay=2,  # 2-second delay to respect rate limits
        )

        # Save batch results to CSV
        if batch_results:
            batch_csv_path = os.path.join(base_dir, "batch_download_results.csv")
            save_results_to_csv(batch_results, batch_csv_path)

    except Exception as e:
        print(f"An error occurred during download: {str(e)}")
        print("Please check your internet connection and DOI formats.")


if __name__ == "__main__":
    # Entry point for the script
    # This ensures the demo only runs when the script is executed directly,
    # not when imported as a module
    main()
