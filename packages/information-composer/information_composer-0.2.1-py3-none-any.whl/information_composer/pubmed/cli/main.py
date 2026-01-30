#!/usr/bin/env python3
"""
PubMed CLI tool for searching and retrieving article information from PubMed database.
This module provides a comprehensive command-line interface for PubMed operations
including searching, fetching details, batch processing, and cache management.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any


# Add the project root to the path so we can import from information_composer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from information_composer.pubmed.pubmed import (
    clean_pubmed_cache,
    fetch_pubmed_details_batch_sync,
    query_pmid,
    query_pmid_by_date,
)


def save_results(
    results: list[dict[str, Any]], output_file: str, output_format: str
) -> None:
    """
    Save results to file in specified format.
    Args:
        results: List of result dictionaries
        output_file: Path to output file
        output_format: Output format ('json' or 'csv')
    Raises:
        ValueError: If output format is not supported
    """
    if output_format == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    elif output_format == "csv":
        import pandas as pd

        # Flatten the results for CSV export
        flattened_results = []
        for record in results:
            flat_record = {}
            for key, value in record.items():
                if isinstance(value, list):
                    flat_record[key] = "; ".join(str(item) for item in value)
                else:
                    flat_record[key] = value
            flattened_results.append(flat_record)
        df = pd.DataFrame(flattened_results)
        df.to_csv(output_file, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def search_command(args: argparse.Namespace) -> None:
    """
    Handle the search command.
    Args:
        args: Parsed command line arguments
    """
    print(f"Searching PubMed for: {args.query}")
    # Use date-range search if dates are provided
    if args.start_date or args.end_date:
        pmids = query_pmid_by_date(
            query=args.query,
            email=args.email,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_months=args.batch_months,
        )
    else:
        pmids = query_pmid(query=args.query, email=args.email, retmax=args.max_results)
    print(f"Found {len(pmids)} PMIDs")
    # Fetch details if requested
    if args.fetch_details and pmids:
        print("Fetching detailed information...")
        results = fetch_pubmed_details_batch_sync(
            pmids=pmids,
            email=args.email,
            cache_dir=args.cache_dir if not args.no_cache else None,
            chunk_size=args.chunk_size,
            delay_between_chunks=args.delay,
            max_retries=args.retries,
        )
        # Save results if output file is specified
        if args.output:
            save_results(results, args.output, args.format)
            print(f"Results saved to {args.output}")
        else:
            # Print to stdout
            if args.format == "json":
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                print("Use --output with --format to save results in desired format")
    elif args.output:
        # Save PMIDs only
        if args.format == "json":
            with open(args.output, "w") as f:
                json.dump(pmids, f, indent=2)
        elif args.format == "csv":
            import pandas as pd

            df = pd.DataFrame({"pmid": pmids})
            df.to_csv(args.output, index=False)
        print(f"PMIDs saved to {args.output}")
    else:
        # Print PMIDs to stdout
        for pmid in pmids:
            print(pmid)


def details_command(args: argparse.Namespace) -> None:
    """
    Handle the details command.
    Args:
        args: Parsed command line arguments
    """
    print(f"Fetching details for {len(args.pmids)} PMIDs")
    results = fetch_pubmed_details_batch_sync(
        pmids=args.pmids,
        email=args.email,
        cache_dir=args.cache_dir if not args.no_cache else None,
        chunk_size=args.chunk_size,
        delay_between_chunks=args.delay,
        max_retries=args.retries,
    )
    # Save results if output file is specified
    if args.output:
        save_results(results, args.output, args.format)
        print(f"Results saved to {args.output}")
    else:
        # Print to stdout
        if args.format == "json":
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print("Use --output with --format to save results in desired format")


def batch_command(args: argparse.Namespace) -> None:
    """
    Handle the batch command.
    Args:
        args: Parsed command line arguments
    """
    print(f"Processing batch file: {args.input_file}")
    # Read PMIDs from input file
    with open(args.input_file, encoding="utf-8") as f:
        content = f.read().strip()
        # Try to parse as JSON first
        try:
            pmids = json.loads(content)
        except json.JSONDecodeError:
            # Treat as plain text with one PMID per line
            pmids = [line.strip() for line in content.split("\n") if line.strip()]
    print(f"Found {len(pmids)} PMIDs in input file")
    results = fetch_pubmed_details_batch_sync(
        pmids=pmids,
        email=args.email,
        cache_dir=args.cache_dir if not args.no_cache else None,
        chunk_size=args.chunk_size,
        delay_between_chunks=args.delay,
        max_retries=args.retries,
    )
    # Save results if output file is specified
    if args.output:
        save_results(results, args.output, args.format)
        print(f"Results saved to {args.output}")
    else:
        # Print to stdout
        if args.format == "json":
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print("Use --output with --format to save results in desired format")


def cache_clean_command(args: argparse.Namespace) -> None:
    """
    Handle the cache clean command.
    Args:
        args: Parsed command line arguments
    """
    if not args.cache_dir:
        print("Error: --cache-dir is required for cache clean command")
        return
    deleted_count = clean_pubmed_cache(
        cache_dir=args.cache_dir, older_than_days=args.older_than
    )
    print(f"Deleted {deleted_count} cache files")


def main() -> None:
    """Main entry point for the PubMed CLI tool."""
    parser = argparse.ArgumentParser(
        description="PubMed CLI tool for searching and retrieving article information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple search
  pubmed-cli search "cancer research" -e user@example.com
  # Search with date range
  pubmed-cli search "cancer research" -e user@example.com -s 2020/01/01 -d 2023/12/31
  # Search with results saved to CSV
  pubmed-cli search "machine learning" -e user@example.com -o results.csv -f csv
  # Get details for specific PMIDs
  pubmed-cli details 12345678 23456789 -e user@example.com
  # Process PMIDs from file
  pubmed-cli batch pmids.txt -e user@example.com -o results.json
  # Clean cache files older than 30 days
  pubmed-cli cache clean --cache-dir ./pubmed_cache --older-than 30
        """,
    )
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    # Search command
    search_parser = subparsers.add_parser(
        "search", help="Search PubMed with a query term"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-e", "--email", required=True, help="Email for NCBI tracking"
    )
    search_parser.add_argument(
        "-m", "--max-results", type=int, default=9999, help="Maximum number of results"
    )
    search_parser.add_argument(
        "-s", "--start-date", help="Start date in format YYYY/MM/DD"
    )
    search_parser.add_argument("-d", "--end-date", help="End date in format YYYY/MM/DD")
    search_parser.add_argument(
        "-b",
        "--batch-months",
        type=int,
        default=12,
        help="Months per batch for date-range searches",
    )
    search_parser.add_argument(
        "--fetch-details",
        action="store_true",
        help="Fetch detailed information for found PMIDs",
    )
    search_parser.add_argument("-o", "--output", help="Output file path")
    search_parser.add_argument(
        "-f", "--format", choices=["json", "csv"], default="json", help="Output format"
    )
    search_parser.add_argument(
        "--cache-dir", default="./pubmed_cache", help="Cache directory path"
    )
    search_parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching"
    )
    search_parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="PMIDs per chunk for details fetching",
    )
    search_parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between chunks in seconds"
    )
    search_parser.add_argument(
        "--retries", type=int, default=3, help="Max retry attempts"
    )
    # Details command
    details_parser = subparsers.add_parser(
        "details", help="Fetch detailed information for a list of PMIDs"
    )
    details_parser.add_argument("pmids", nargs="+", help="PMIDs to fetch details for")
    details_parser.add_argument(
        "-e", "--email", required=True, help="Email for NCBI tracking"
    )
    details_parser.add_argument(
        "-c", "--chunk-size", type=int, default=100, help="PMIDs per chunk"
    )
    details_parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between chunks in seconds"
    )
    details_parser.add_argument(
        "-r", "--retries", type=int, default=3, help="Max retry attempts"
    )
    details_parser.add_argument("-o", "--output", help="Output file path")
    details_parser.add_argument(
        "-f", "--format", choices=["json", "csv"], default="json", help="Output format"
    )
    details_parser.add_argument(
        "--cache-dir", default="./pubmed_cache", help="Cache directory path"
    )
    details_parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching"
    )
    # Batch command
    batch_parser = subparsers.add_parser(
        "batch", help="Process multiple queries or PMIDs from a file"
    )
    batch_parser.add_argument("input_file", help="Input file containing PMIDs")
    batch_parser.add_argument(
        "-e", "--email", required=True, help="Email for NCBI tracking"
    )
    batch_parser.add_argument("-o", "--output", help="Output file path")
    batch_parser.add_argument(
        "-f", "--format", choices=["json", "csv"], default="json", help="Output format"
    )
    batch_parser.add_argument(
        "--cache-dir", default="./pubmed_cache", help="Cache directory path"
    )
    batch_parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    batch_parser.add_argument(
        "--chunk-size", type=int, default=100, help="PMIDs per chunk"
    )
    batch_parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between chunks in seconds"
    )
    batch_parser.add_argument(
        "--retries", type=int, default=3, help="Max retry attempts"
    )
    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Manage cached results")
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_command", help="Cache commands"
    )
    # Cache clean command
    cache_clean_parser = cache_subparsers.add_parser(
        "clean", help="Clean cache directory"
    )
    cache_clean_parser.add_argument("--cache-dir", help="Cache directory path")
    cache_clean_parser.add_argument(
        "--older-than", type=int, help="Only delete files older than specified days"
    )
    # Parse arguments
    args = parser.parse_args()
    # Execute the appropriate command
    if args.command == "search":
        search_command(args)
    elif args.command == "details":
        details_command(args)
    elif args.command == "batch":
        batch_command(args)
    elif args.command == "cache":
        if args.cache_command == "clean":
            cache_clean_command(args)
        else:
            cache_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
