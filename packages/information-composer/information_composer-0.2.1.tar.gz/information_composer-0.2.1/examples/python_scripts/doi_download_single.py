#!/usr/bin/env python3
"""
DOI Single Download Example

This example demonstrates how to download a single academic paper using its
Digital Object Identifier (DOI). It shows the basic workflow for DOI-based
paper retrieval and result handling.

The example covers:
- Single DOI download process
- Result validation and error handling
- CSV export for result tracking
- File organization and naming

Requirements:
    - Valid email address for Crossref API compliance
    - Internet connection for API access
    - information_composer package installed

Usage:
    python doi_download_single.py

Note:
    Crossref API requires a valid email address for identification.
    Some papers may require institutional access or payment.
"""

import csv
import os
from typing import List

from information_composer.core.doi_downloader import DOIDownloader


def save_results_to_csv(results: list, output_file: str) -> None:
    """
    Save download results to a CSV file for analysis and tracking.

    This function handles both DownloadResult objects and dictionaries,
    providing flexibility in data format while ensuring consistent CSV output.
    It includes proper error handling for file operations.

    Args:
        results (List): List of DownloadResult objects or dictionaries
            containing download results
        output_file (str): Path to the output CSV file

    Returns:
        None

    Raises:
        IOError: When unable to write to the output file
        Exception: For other file operation errors

    Example:
        >>> results = [DownloadResult(doi="10.1000/182", downloaded=True, ...)]
        >>> save_results_to_csv(results, "downloads.csv")
        Results saved to: downloads.csv
    """
    # Validate input before processing
    if not results:  # Check if results is empty
        print("No results to save")
        return

    try:
        # Define CSV column headers for consistent output format
        fieldnames = ["DOI", "file_name", "downloaded", "file_size", "error_message"]
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Process each result, handling different data types
            for result in results:
                # Handle both DownloadResult objects and dictionaries
                if hasattr(result, "doi"):
                    # DownloadResult object - extract attributes
                    writer.writerow(
                        {
                            "DOI": result.doi,
                            "file_name": result.file_name,
                            "downloaded": result.downloaded,
                            "file_size": result.file_size or "",  # Handle None values
                            "error_message": result.error_message or "",
                        }
                    )
                else:
                    # Dictionary format - write directly
                    writer.writerow(result)
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results to CSV: {str(e)}")


def main():
    """
    Demonstrate single DOI download with result tracking.

    This function shows the complete workflow for downloading a single
    academic paper using its DOI. It demonstrates proper configuration,
    error handling, and result management.

    The function:
    1. Sets up download configuration
    2. Initializes the DOI downloader
    3. Downloads a single paper
    4. Saves results to CSV for tracking

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
        Results saved to: downloads/single_download_results.csv
    """
    # Step 1: Configure download settings
    base_dir = os.path.join(os.getcwd(), "downloads")
    email = "your_email@example.com"  # Replace with your actual email

    # Step 2: Initialize the DOI downloader
    # Email is required for Crossref API compliance
    downloader = DOIDownloader(email=email)

    try:
        # Step 3: Download a single paper by DOI
        print("Starting single DOI download example...")
        print("-" * 50)

        # Example DOI for demonstration
        single_doi = "10.1093/jxb/erad499"  # Replace with actual DOI
        single_output_dir = os.path.join(base_dir, "single")

        # Perform the download
        single_result = downloader.download_single(
            doi=single_doi, output_dir=single_output_dir
        )

        # Step 4: Save results to CSV for tracking and analysis
        if single_result:  # Check if we have a result
            single_csv_path = os.path.join(base_dir, "single_download_results.csv")
            save_results_to_csv([single_result], single_csv_path)
        else:
            print("No result returned from download")

    except Exception as e:
        print(f"An error occurred during download: {str(e)}")
        print("Please check your internet connection and DOI format.")


if __name__ == "__main__":
    # Entry point for the script
    # This ensures the demo only runs when the script is executed directly,
    # not when imported as a module
    main()
