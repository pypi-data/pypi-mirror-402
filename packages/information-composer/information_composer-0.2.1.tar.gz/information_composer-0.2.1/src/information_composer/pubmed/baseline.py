"""PubMed baseline data processing module.
This module provides functionality for loading and processing PubMed baseline data
from XML files with filtering capabilities based on keywords and impact factors.
"""

import logging
import os
from os.path import isfile
import pickle
from typing import Any

import pandas as pd
import pubmed_parser as pp


def load_baseline(
    xmlfile: str,
    *args: Any,
    **kwargs: Any,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    Load and parse PubMed baseline data from XML file with filtering options.
    Args:
        xmlfile: Path to the XML file
        **kwargs: Optional parameters:
            - output_type: Output format ('pd', 'dict', 'list')
            - keywords: List of keywords for filtering
            - kw_filter: Filter type ('abstract', 'title', 'both')
            - impact_factor: Minimum impact factor threshold
            - log: Enable logging
    Returns:
        Parsed data in specified format
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        ValueError: If output_type or kw_filter is invalid
        RuntimeError: If there's an error parsing the XML file
    """
    # Configure logging
    log = kwargs.get("log", False)
    if log:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
    if not isfile(xmlfile):
        raise FileNotFoundError(f"The specified file {xmlfile} does not exist.")
    # Parameter validation and initialization
    output_type = kwargs.get("output_type", "list")
    if output_type not in ["list", "dict", "pd"]:
        raise ValueError('output_type must be "pd", "list" or "dict"')
    keywords = kwargs.get("keywords", [])
    kw_filter = kwargs.get("kw_filter", "abstract")
    if kw_filter not in ["abstract", "title", "both"]:
        raise ValueError('kw_filter must be "abstract", "title", or "both"')
    impact_factor = float(kwargs.get("impact_factor", 0))
    # Load impact factor data (using cache)
    impact_factor_dict: dict[str, float] = {}
    if impact_factor > 0:
        try:
            impact_factor_dict = load_dict_from_pickle("./if2024.pickle")
        except Exception as e:
            logging.warning(f"Failed to load impact factor data: {e}")
            impact_factor = 0
    # XML parsing
    try:
        path_xml = pp.parse_medline_xml(xmlfile)
        baselineversion = os.path.basename(xmlfile).split(".")[0]
    except Exception as e:
        raise RuntimeError(f"Error parsing XML file {xmlfile}") from e
    # Data processing
    data_dict: dict[str, dict[str, Any]] = {}
    for entry in path_xml:
        if not _should_keep_entry(
            entry, keywords, kw_filter, impact_factor, impact_factor_dict
        ):
            continue
        data_dict[str(entry["pmid"])] = _create_entry_dict(entry, baselineversion)
    # Return results
    if output_type == "pd":
        return pd.DataFrame.from_dict(data_dict).T
    elif output_type == "dict":
        return data_dict
    return list(data_dict.values())


def _should_keep_entry(
    entry: dict[str, Any],
    keywords: list[str],
    kw_filter: str,
    impact_factor: float,
    impact_factor_dict: dict[str, float],
) -> bool:
    """
    Determine if an entry should be kept based on filtering criteria.
    Args:
        entry: PubMed entry dictionary
        keywords: List of keywords for filtering
        kw_filter: Filter type ('abstract', 'title', 'both')
        impact_factor: Minimum impact factor threshold
        impact_factor_dict: Dictionary mapping journal names to impact factors
    Returns:
        True if entry should be kept, False otherwise
    """
    # Keyword filtering
    if keywords:
        if kw_filter == "both":
            if not (
                keywords_filter(entry["abstract"], keywords)
                or keywords_filter(entry["title"], keywords)
            ):
                return False
        elif not keywords_filter(entry[kw_filter], keywords):
            return False
    # Impact factor filtering
    if impact_factor > 0:
        journal_name = entry["journal"].rstrip().lower()
        if (
            journal_name not in impact_factor_dict
            or impact_factor_dict[journal_name] < impact_factor
        ):
            return False
    return True


def _create_entry_dict(entry: dict[str, Any], version: str) -> dict[str, Any]:
    """
    Create a standardized entry dictionary.
    Args:
        entry: Raw PubMed entry
        version: Baseline version string
    Returns:
        Standardized entry dictionary
    """
    return {
        "pmid": str(entry["pmid"]),
        "title": entry.get("title", ""),
        "abstract": entry.get("abstract", ""),
        "journal": entry.get("journal", ""),
        "pubdate": entry.get("pubdate", ""),
        "publication_types": entry.get("publication_types", []),
        "authors": entry.get("authors", []),
        "doi": entry.get("doi", ""),
        "version": version,
    }


def keywords_filter(text: str, keywords: list[str]) -> bool:
    """
    Check if text contains any of the specified keywords.
    Args:
        text: Text to check
        keywords: List of keywords to search for
    Returns:
        True if any keyword is found, False otherwise
    """
    if not text or not keywords:
        return False
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def load_dict_from_pickle(filename: str) -> dict[str, Any]:
    """
    Load a dictionary from a pickle file.
    Args:
        filename: Path to the pickle file
    Returns:
        Dictionary loaded from pickle file
    Raises:
        FileNotFoundError: If the file doesn't exist
        pickle.PickleError: If there's an error unpickling the file
    """
    try:
        with open(filename, "rb") as f:
            data = pickle.load(f)
            if isinstance(data, dict):
                return data
            else:
                raise ValueError(f"Expected dict, got {type(data)}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Pickle file {filename} not found") from None
    except Exception as e:
        raise pickle.PickleError(f"Error loading pickle file {filename}: {e}") from e
