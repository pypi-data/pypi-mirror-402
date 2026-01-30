"""
PDF file format validation tool.
This module provides functionality to validate PDF files using the pypdfium2 library
to detect if PDF files are properly formatted.
"""

from dataclasses import dataclass
import os
from pathlib import Path

import pypdfium2 as pdfium
from pypdfium2._helpers.misc import PdfiumError


@dataclass(frozen=True)
class ValidationResult:
    """Result of PDF validation."""

    is_valid: bool
    error_message: str | None
    page_count: int | None = None
    file_size: int | None = None


@dataclass(frozen=True)
class ValidationStats:
    """Statistics from PDF validation."""

    total_files: int
    valid_files: int
    invalid_files: int
    success_rate: float
    error_details: list[tuple[str, str | None]]


class PDFValidator:
    """PDF file validator with comprehensive error handling and statistics."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize PDF validator.
        Args:
            verbose: Whether to print detailed output during validation.
        """
        self.verbose = verbose
        self.valid_count = 0
        self.invalid_count = 0
        self.error_details: list[tuple[str, str | None]] = []

    def validate_single_pdf(self, pdf_path: str | Path) -> ValidationResult:
        """
        Validate a single PDF file.
        Args:
            pdf_path: Path to the PDF file to validate.
        Returns:
            ValidationResult containing validation status, error message, and metadata.
        """
        pdf_path_str = str(pdf_path)
        try:
            # Check if file exists
            if not os.path.exists(pdf_path_str):
                error_msg = f"File not found: {pdf_path_str}"
                if self.verbose:
                    print(f"✗ {pdf_path_str}: {error_msg}")
                return ValidationResult(
                    is_valid=False,
                    error_message=error_msg,
                    file_size=None,
                    page_count=None,
                )
            # Check file size
            file_size = os.path.getsize(pdf_path_str)
            if file_size == 0:
                error_msg = "File is empty"
                if self.verbose:
                    print(f"✗ {pdf_path_str}: {error_msg}")
                return ValidationResult(
                    is_valid=False,
                    error_message=error_msg,
                    file_size=file_size,
                    page_count=None,
                )
            # Try to open PDF file
            with open(pdf_path_str, "rb") as file:
                pdf_doc = pdfium.PdfDocument(file)
                # Get page count
                page_count = len(pdf_doc)
                if self.verbose:
                    print(f"✓ {pdf_path_str}: Valid PDF file with {page_count} pages")
                return ValidationResult(
                    is_valid=True,
                    error_message=None,
                    file_size=file_size,
                    page_count=page_count,
                )
        except PdfiumError as e:
            error_msg = f"PDF format error: {e!s}"
            if self.verbose:
                print(f"✗ {pdf_path_str}: {error_msg}")
            return ValidationResult(
                is_valid=False,
                error_message=error_msg,
                file_size=file_size if "file_size" in locals() else None,
                page_count=None,
            )
        except Exception as e:
            error_msg = f"Unknown error: {e!s}"
            if self.verbose:
                print(f"✗ {pdf_path_str}: {error_msg}")
            return ValidationResult(
                is_valid=False,
                error_message=error_msg,
                file_size=file_size if "file_size" in locals() else None,
                page_count=None,
            )

    def validate_directory(
        self, directory_path: str | Path, recursive: bool = False
    ) -> None:
        """
        Validate all PDF files in a directory.
        Args:
            directory_path: Path to the directory to search for PDF files.
            recursive: Whether to recursively search subdirectories.
        """
        directory = Path(directory_path)
        if not directory.exists():
            print(f"Error: Directory does not exist - {directory_path}")
            return
        if not directory.is_dir():
            print(f"Error: Not a valid directory - {directory_path}")
            return
        # Search for PDF files
        if recursive:
            pdf_files = list(directory.rglob("*.pdf"))
        else:
            pdf_files = list(directory.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in directory {directory_path}")
            return
        print(f"Found {len(pdf_files)} PDF files, starting validation...")
        print("-" * 60)
        for pdf_file in pdf_files:
            result = self.validate_single_pdf(pdf_file)
            self._process_validation_result(str(pdf_file), result)

    def validate_files(self, file_paths: list[str | Path]) -> None:
        """
        Validate a list of specified PDF files.
        Args:
            file_paths: List of PDF file paths to validate.
        """
        print(f"Starting validation of {len(file_paths)} PDF files...")
        print("-" * 60)
        for file_path in file_paths:
            result = self.validate_single_pdf(file_path)
            self._process_validation_result(str(file_path), result)

    def _process_validation_result(
        self, file_path: str, result: ValidationResult
    ) -> None:
        """
        Process a validation result and update statistics.
        Args:
            file_path: Path to the file that was validated.
            result: Validation result to process.
        """
        if result.is_valid:
            self.valid_count += 1
        else:
            self.invalid_count += 1
            self.error_details.append((file_path, result.error_message))

    def get_validation_stats(self) -> ValidationStats:
        """
        Get validation statistics.
        Returns:
            ValidationStats containing comprehensive validation statistics.
        """
        total = self.valid_count + self.invalid_count
        success_rate = (self.valid_count / total * 100) if total > 0 else 0.0
        return ValidationStats(
            total_files=total,
            valid_files=self.valid_count,
            invalid_files=self.invalid_count,
            success_rate=success_rate,
            error_details=self.error_details.copy(),
        )

    def print_summary(self) -> None:
        """Print validation results summary."""
        stats = self.get_validation_stats()
        print("\n" + "=" * 60)
        print("Validation Results Summary")
        print("=" * 60)
        print(f"Total files: {stats.total_files}")
        print(f"Valid PDFs: {stats.valid_files}")
        print(f"Invalid PDFs: {stats.invalid_files}")
        print(f"Success rate: {stats.success_rate:.1f}%")
        if stats.invalid_files > 0:
            print("\nInvalid files details:")
            print("-" * 40)
            for file_path, error_msg in stats.error_details:
                print(f"File: {file_path}")
                print(f"Error: {error_msg}")
                print()

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.valid_count = 0
        self.invalid_count = 0
        self.error_details.clear()
