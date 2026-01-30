"""PDF validation and processing module."""

from typing import TYPE_CHECKING

from .validator import PDFValidator, ValidationResult, ValidationStats


if TYPE_CHECKING:
    from .cli.main import main as pdf_validator_cli
__all__ = [
    "PDFValidator",
    "ValidationResult",
    "ValidationStats",
    # CLI
    "pdf_validator_cli",
]
