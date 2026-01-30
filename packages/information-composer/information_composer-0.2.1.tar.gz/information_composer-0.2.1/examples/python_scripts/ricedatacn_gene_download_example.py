"""
RiceDataCN Gene Download Example

This script demonstrates how to download gene information from ricedata.cn
for multiple gene IDs using the optimized RiceGeneParser.

Features demonstrated:
- Automatic encoding detection (GBK/GB2312/UTF-8)
- Concurrent reference fetching for improved performance
- Retry mechanism with exponential backoff
- Rate limiting to avoid server overload
- Caching support for parsed genes
- Comprehensive logging and progress tracking

Gene IDs: 50420, 420, 307, 1037

Usage:
    python ricedatacn_gene_download_example.py

Output:
    - JSON files in downloads/genes/ directory
    - Console output with progress and summary
"""

import os
import sys
from datetime import datetime
from typing import Any

from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser


def print_banner() -> None:
    """Print a nice banner for the script."""
    print("=" * 60)
    print("  RiceDataCN Gene Downloader")
    print("  Downloading gene information from ricedata.cn")
    print("=" * 60)
    print()


def print_gene_summary(gene_info: dict[str, Any] | None, index: int, total: int) -> None:
    """Print a summary of a single gene.

    Args:
        gene_info: Parsed gene information or None if failed
        index: Current gene index (1-based)
        total: Total number of genes
    """
    gene_id = gene_info.get("gene_id", "Unknown") if gene_info else "N/A"

    print(f"\n[{index}/{total}] Gene ID: {gene_id}")
    print("-" * 40)

    if gene_info:
        # Basic info
        basic_info = gene_info.get("basic_info", {})
        gene_name = basic_info.get("基因名称", basic_info.get("Gene Name", "N/A"))
        print(f"  Gene Name: {gene_name}")

        # Description preview
        description = gene_info.get("description", "")
        if description:
            # Show first 200 characters
            preview = description[:200].replace("\n", " ").strip()
            print(f"  Description: {preview}...")

        # Ontology count
        ontology = gene_info.get("ontology", {})
        print(f"  Ontology Categories: {len(ontology)}")

        # References count
        references = gene_info.get("references", [])
        print(f"  References: {len(references)}")

        # Output file
        output_file = gene_info.get("url", "").replace(".htm", ".json").split("/")[-1]
        print(f"  Output: {output_file}")
    else:
        print("  Status: FAILED (gene not found)")


def print_final_summary(results: list[dict[str, Any] | None], gene_ids: list[str]) -> None:
    """Print final summary of all downloads.

    Args:
        results: List of parsed gene information (or None for failed)
        gene_ids: List of gene IDs that were attempted
    """
    print("\n" + "=" * 60)
    print("  Download Summary")
    print("=" * 60)

    success_count = len([r for r in results if r])
    fail_count = len(results) - success_count
    total = len(results)

    print(f"\n  Total genes: {total}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Success rate: {success_count/total*100:.1f}%")

    # Detailed breakdown
    print("\n  Detailed Results:")
    print("  " + "-" * 40)
    for i, (gene_id, result) in enumerate(zip(gene_ids, results, strict=False), 1):
        status = "✓" if result else "✗"
        gene_name = "N/A"
        if result:
            basic_info = result.get("basic_info", {})
            gene_name = basic_info.get("基因名称", basic_info.get("Gene Name", "N/A"))
        print(f"  {status} Gene {gene_id}: {gene_name}")

    print()


def main() -> None:
    """Main function to download gene information."""
    # Print banner
    print_banner()

    # Configuration for optimized performance
    config = {
        "timeout": 60,              # Request timeout in seconds
        "retries": 3,               # Number of retry attempts
        "max_workers": 5,           # Concurrent workers for reference fetching
        "rate_limit_delay": 1.0,    # Delay between requests (seconds)
        "enable_cache": False,      # Disable cache for fresh downloads
    }

    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()

    # Initialize parser with config
    parser = RiceGeneParser(config=config)

    # Gene IDs to download
    gene_ids = ["50420", "420", "307", "1037"]

    print(f"Target genes: {', '.join(gene_ids)}")

    # Set output directory
    output_dir = os.path.join(os.getcwd(), "downloads", "genes")
    print(f"Output directory: {output_dir}")
    print()

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Track start time
    start_time = datetime.now()

    # Parse multiple genes
    print("Starting download...")
    print("-" * 40)

    results = parser.parse_multiple_genes(gene_ids, output_dir, fetch_details=True)

    # Calculate elapsed time
    elapsed = datetime.now() - start_time

    # Print individual summaries
    print("\n" + "=" * 60)
    print("  Individual Results")
    print("=" * 60)

    for i, result in enumerate(results, 1):
        print_gene_summary(result, i, len(results))

    # Print final summary
    print_final_summary(results, gene_ids)

    # Print elapsed time
    print(f"Total time elapsed: {elapsed.total_seconds():.2f} seconds")
    print(f"Average time per gene: {elapsed.total_seconds()/len(gene_ids):.2f} seconds")

    # Exit with appropriate code
    success_count = len([r for r in results if r])
    if success_count == len(gene_ids):
        print("\n✓ All genes downloaded successfully!")
        sys.exit(0)
    elif success_count > 0:
        print(f"\n⚠ Some genes failed to download ({len(gene_ids) - success_count} failed)")
        sys.exit(1)
    else:
        print("\n✗ All genes failed to download")
        sys.exit(1)


if __name__ == "__main__":
    main()

