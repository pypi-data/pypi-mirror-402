"""DOI cleaning utilities.

This module provides functions for cleaning and standardizing DOI formats.
"""

import re
from typing import Any


def clean_doi(doi: str) -> str:
    """
    Clean and standardize DOI format by extracting the actual DOI from various formats.

    Args:
        doi: Raw DOI string

    Returns:
        Cleaned DOI string

    Examples:
        >>> clean_doi("10.26508/lsa.202302380 [doi] e202302380")
        "10.26508/lsa.202302380"
        >>> clean_doi("S1534-5807(24)00603-8 [pii] 10.1016/j.devcel.2024.10.004 [doi]")
        "10.1016/j.devcel.2024.10.004"
    """
    if not doi or doi == "N/A":
        return "N/A"
    doi_pattern = r"(10\.\d{4,}(?:\.[1-9][0-9]*)*(?:\/|%2F)(?:(?![\"&\'])\S)+)"
    matches = re.findall(doi_pattern, doi)
    if matches:
        return matches[0].strip()  # type: ignore[no-any-return]
    return "N/A"


def validate_doi(doi: str) -> bool:
    """
    Validate if a string is a valid DOI.

    Args:
        doi: String to validate

    Returns:
        True if the string is a valid DOI format, False otherwise
    """
    if not doi:
        return False
    doi_pattern = r"^10\.\d{4,}(?:\.[1-9][0-9]*)*\/[^\s]+$"
    return bool(re.match(doi_pattern, doi))


def extract_doi_from_text(text: str) -> list[str]:
    """
    Extract all DOIs from a text string.

    Args:
        text: Text to search for DOIs

    Returns:
        List of found DOIs
    """
    if not text:
        return []
    doi_pattern = r"(10\.\d{4,}(?:\.[1-9][0-9]*)*(?:\/|%2F)(?:(?![\"&\'\s,])[^\s])+)"
    return re.findall(doi_pattern, text)


__all__ = [
    "clean_doi",
    "extract_doi_from_text",
    "validate_doi",
]
