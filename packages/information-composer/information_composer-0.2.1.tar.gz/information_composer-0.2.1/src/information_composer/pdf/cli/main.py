#!/usr/bin/env python3
"""
PDF file format validation CLI tool.
This module provides a command-line interface for validating PDF files
using the PDFValidator class.
"""

import argparse
import json
from pathlib import Path
import sys

from information_composer.pdf.validator import PDFValidator, ValidationStats


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="PDF file format validation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  pdf-validator file1.pdf file2.pdf          # Validate specified files
  pdf-validator -d /path/to/directory        # Validate all PDFs in directory
  pdf-validator -d /path/to/directory -r     # Recursively validate directory
  pdf-validator -d /path/to/directory -v     # Verbose output
  pdf-validator -d /path/to/directory --json # JSON format output
        """,
    )
    parser.add_argument("files", nargs="*", help="PDF file paths to validate")
    parser.add_argument("-d", "--directory", help="Directory path to validate")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively search subdirectories for PDF files",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output information"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Show only statistics, not detailed errors",
    )
    return parser


def validate_files_or_directory(
    validator: PDFValidator,
    files: list[str | Path],
    directory: str | None,
    recursive: bool,
) -> None:
    """
    Validate files or directory based on provided arguments.
    Args:
        validator: PDFValidator instance to use for validation.
        files: List of file paths to validate.
        directory: Directory path to validate.
        recursive: Whether to recursively search subdirectories.
    """
    if directory:
        # Validate directory
        validator.validate_directory(directory, recursive)
    elif files:
        # Validate specified files
        validator.validate_files(files)
    else:
        # If no arguments provided, show help
        raise ValueError("No files or directory specified")


def print_results(validator: PDFValidator, json_output: bool, stats_only: bool) -> None:
    """
    Print validation results in the requested format.
    Args:
        validator: PDFValidator instance with validation results.
        json_output: Whether to output results in JSON format.
        stats_only: Whether to show only statistics.
    """
    if json_output:
        validation_stats: ValidationStats = validator.get_validation_stats()
        # Convert to dict for JSON serialization
        stats_dict = {
            "total_files": validation_stats.total_files,
            "valid_files": validation_stats.valid_files,
            "invalid_files": validation_stats.invalid_files,
            "success_rate": validation_stats.success_rate,
            "error_details": validation_stats.error_details,
        }
        print(json.dumps(stats_dict, indent=2, ensure_ascii=False))
    elif stats_only:
        stats_summary: ValidationStats = validator.get_validation_stats()
        print(f"Total files: {stats_summary.total_files}")
        print(f"Valid PDFs: {stats_summary.valid_files}")
        print(f"Invalid PDFs: {stats_summary.invalid_files}")
        print(f"Success rate: {stats_summary.success_rate:.1f}%")
    else:
        # Print detailed summary
        validator.print_summary()


def main() -> int:
    """
    Main function for PDF validation CLI.
    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = create_argument_parser()
    args = parser.parse_args()
    # Create validator
    validator = PDFValidator(verbose=args.verbose)
    try:
        validate_files_or_directory(
            validator=validator,
            files=args.files,
            directory=args.directory,
            recursive=args.recursive,
        )
        # Output results
        print_results(
            validator=validator, json_output=args.json, stats_only=args.stats_only
        )
        return 0
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        return 1
    except ValueError as e:
        print(f"Argument error: {e}")
        parser.print_help()
        return 1
    except Exception as e:
        print(f"Error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
