#!/usr/bin/env python3
"""
DOI Download with PubMed Integration Example

This example demonstrates how to download academic papers using DOIs obtained
from PubMed batch queries. It shows the integration between PubMed data
collection and DOI-based paper retrieval.

The example covers:
- Loading DOIs from PubMed batch results
- Filtering valid DOIs from JSON data
- Batch DOI download with progress tracking
- Result validation and error handling
- CSV export for download tracking

Requirements:
    - PubMed batch results JSON file
    - Valid email address for Crossref API compliance
    - Internet connection for API access
    - information_composer package installed

Usage:
    python doi_download_by_using_pubmed_batch_example.py

Note:
    This example requires a PubMed batch results file containing DOI information.
    Crossref API requires a valid email address for identification.
"""

import csv
import json
import os
from typing import Dict, List

# from tqdm import tqdm  # Unused import
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
    Demonstrate DOI download using DOIs from PubMed batch results.

    This function shows how to integrate PubMed data collection with DOI-based
    paper downloads. It loads DOIs from a PubMed batch results file and
    downloads the corresponding papers.

    The function:
    1. Loads PubMed batch results from JSON file
    2. Extracts and filters valid DOIs
    3. Downloads papers using the DOIs
    4. Saves results to CSV for tracking

    Args:
        None

    Returns:
        None

    Raises:
        FileNotFoundError: When PubMed results file is not found
        Exception: When download or file operations fail

    Example:
        >>> main()
        ['10.1000/182', '10.1000/183', ...]
        Starting batch DOI download example...
        --------------------------------------------------
        Results saved to: data/PDFs/duckweeds/batch/batch_download_results.csv
    """
    # Step 1: Configure paths and settings
    base_dir = os.path.join(os.getcwd(), "data/PDFs/duckweeds")
    email = "your_email@example.com"  # Replace with your actual email
    jsonfile = "duckweeds_pubmed_batch_results.json"  # PubMed results file

    # Step 2: Initialize the DOI downloader
    downloader = DOIDownloader(email=email)

    # Step 3: Load PubMed batch results and extract DOIs
    json_path = os.path.join(os.getcwd(), "data", jsonfile)
    try:
        with open(json_path) as f:
            pubmed_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: PubMed results file not found at {json_path}")
        print("Please ensure the file exists and contains DOI information.")
        return

    # Extract DOIs from PubMed data, filtering out "N/A" values
    dois = [item["doi"] for item in pubmed_data if item["doi"] != "N/A"]

    # Limit to first 10 DOIs for demonstration
    # Remove this line to process all DOIs
    dois = dois[:10]

    # Display the DOIs that will be processed
    print("DOIs to download:")
    print(dois)

    try:
        # Step 4: Download papers using the extracted DOIs
        print("\nStarting batch DOI download example...")
        print("-" * 50)

        # Alternative DOI list (commented out for demonstration)
        # dois = [
        #     "10.1038/s41477-024-01771-3",
        #     "10.1038/s41592-024-02305-7",
        #     "10.1038/s41592-024-02201-0",
        # ]

        batch_output_dir = os.path.join(base_dir, "batch")

        # Download papers with delay between requests
        batch_results = downloader.download_batch(
            dois=dois,
            output_dir=batch_output_dir,
            delay=2,  # 2-second delay to respect rate limits
        )

        # Step 5: Save results to CSV for tracking and analysis
        if batch_results:
            batch_csv_path = os.path.join(base_dir, "batch_download_results.csv")
            save_results_to_csv(batch_results, batch_csv_path)
        else:
            print("No results to save")

    except Exception as e:
        print(f"An error occurred during download: {str(e)}")
        print("Please check your internet connection and DOI formats.")


if __name__ == "__main__":
    # Entry point for the script
    # This ensures the demo only runs when the script is executed directly,
    # not when imported as a module
    main()
