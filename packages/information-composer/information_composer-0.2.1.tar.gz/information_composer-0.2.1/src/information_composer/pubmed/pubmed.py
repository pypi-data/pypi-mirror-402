"""PubMed database querying and data processing module.
This module provides comprehensive functionality for querying PubMed database,
fetching article details, and processing Medline format data with proper
type annotations and error handling.
"""

import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import time
from typing import Any

import aiohttp
from Bio import Entrez, Medline
import pandas as pd
from tqdm import tqdm

from information_composer.core.utils import clean_doi


def query_pmid_by_date(
    query: str,
    email: str = "your_email@example.com",
    start_date: str | None = None,
    end_date: str | None = None,
    batch_months: int = 12,
) -> list[str]:
    """
    Query PubMed database with date ranges to get all unique PMIDs matching the search query.
    Args:
        query: PubMed search query string
        email: Email address for NCBI's tracking purposes
        start_date: Start date in format 'YYYY/MM/DD' (defaults to earliest possible)
        end_date: End date in format 'YYYY/MM/DD' (defaults to today)
        batch_months: Number of months per batch (default 12)
    Returns:
        List of unique PMIDs matching the query
    Raises:
        RuntimeError: If there's an error querying PubMed or too many results
    """
    Entrez.email = email  # type: ignore[assignment]
    # Set default dates if not provided
    if end_date is None:
        end_date = datetime.today().strftime("%Y/%m/%d")
    if start_date is None:
        start_date = "1800/01/01"  # PubMed's earliest date
    # Convert dates to datetime objects
    start_dt = datetime.strptime(start_date, "%Y/%m/%d")
    end_dt = datetime.strptime(end_date, "%Y/%m/%d")
    all_pmids: set[str] = set()
    # Calculate total number of batches for progress bar
    total_months = (end_dt.year - start_dt.year) * 12 + end_dt.month - start_dt.month
    total_batches = (total_months + batch_months - 1) // batch_months
    # Process in batches with progress bar
    with tqdm(total=total_batches, desc="Querying PubMed") as pbar:
        current_start = start_dt
        while current_start <= end_dt:
            # Calculate end of current batch
            current_end = min(current_start + timedelta(days=batch_months * 30), end_dt)
            # Format dates for query
            date_query = (
                f"{query} AND ({current_start.strftime('%Y/%m/%d')}[DP]:"
                f"{current_end.strftime('%Y/%m/%d')}[DP])"
            )
            try:
                with Entrez.esearch(
                    db="pubmed", term=date_query, retmax=9999
                ) as search_handle:
                    record = Entrez.read(search_handle)
                    batch_pmids = record["IdList"]  # type: ignore[index]
                    all_pmids.update(batch_pmids)
                    # If we got less than 9999 results, we don't need to worry about missing any
                    if len(batch_pmids) < 9999:
                        current_start = current_end + timedelta(days=1)
                        pbar.update(1)
                    else:
                        # If we hit the limit, use smaller time intervals
                        new_batch_months = max(1, batch_months // 2)
                        if new_batch_months == batch_months:
                            raise RuntimeError(
                                "Too many results even with minimum batch size for "
                                f"period {current_start.strftime('%Y/%m/%d')} to "
                                f"{current_end.strftime('%Y/%m/%d')}"
                            )
                        batch_months = new_batch_months
                        # Recalculate total batches with new batch_months
                        total_batches = (
                            total_months + batch_months - 1
                        ) // batch_months
                        pbar.reset(total=total_batches)
                        continue
            except Exception as e:
                raise RuntimeError(f"Error querying PubMed: {e!s}") from e
    return list(all_pmids)


def query_pmid(
    query: str, email: str = "your_email@example.com", retmax: int = 9999
) -> list[str]:
    """
    Query PubMed database and return a list of PMIDs matching the search query.
    Args:
        query: PubMed search query string
        email: Email address for NCBI's tracking purposes
        retmax: Maximum number of results to return
    Returns:
        List of PMIDs matching the query
    Raises:
        RuntimeError: If there's an error querying PubMed
    """
    Entrez.email = email  # type: ignore[assignment]
    try:
        with Entrez.esearch(db="pubmed", term=query, retmax=retmax) as search_handle:
            record = Entrez.read(search_handle)
            return record["IdList"]  # type: ignore[no-any-return]
    except Exception as e:
        raise RuntimeError(f"Error querying PubMed: {e!s}") from e


def load_pubmed_file(
    filename: str,
    *args: Any,
    **kwargs: Any,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    Load and parse PubMed Medline file.
    Args:
        filename: Path to Medline format file
        **kwargs: Optional parameters
            - output_type: Output format ('pd', 'dict', 'list')
    Returns:
        Parsed data in specified format
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If output_type is invalid
        RuntimeError: If there's an error parsing the file
    """
    output_type = kwargs.get("output_type", "list")
    if output_type not in ["list", "dict", "pd"]:
        raise ValueError('output_type must be "pd", "list" or "dict"')
    records_dict: dict[str, dict[str, Any]] = {}
    try:
        with open(filename, encoding="utf-8") as handle:
            for record in Medline.parse(handle):
                pmid = record["PMID"]
                records_dict[pmid] = {
                    "pmid": pmid,
                    "title": record.get("TI", "N/A"),
                    "abstract": record.get("AB", "No abstract available"),
                    "journal": record.get("JT", "N/A"),
                    "pubdate": record.get("DP", "N/A"),
                    "publication_types": record.get("PT", []),
                    "authors": record.get("AU", []),
                    "doi": record.get("LID", "N/A"),
                    "keywords": record.get("MH", []),
                }
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {filename} does not exist") from None
    except Exception as e:
        raise RuntimeError(f"Error parsing file {filename}: {e!s}") from e
    if output_type == "pd":
        return pd.DataFrame.from_dict(records_dict).T
    elif output_type == "dict":
        return records_dict
    return list(records_dict.values())


async def _fetch_pmids_chunk(
    pmids: list[str],
    email: str,
    session: aiohttp.ClientSession,
) -> list[dict[str, Any]]:
    """
    Helper function to fetch a chunk of PMIDs asynchronously.
    Args:
        pmids: List of PMIDs to fetch
        email: Email for NCBI tracking
        session: aiohttp session for HTTP requests
    Returns:
        List of processed records
    """
    Entrez.email = email  # type: ignore[assignment]
    try:
        with Entrez.efetch(
            db="pubmed", id=pmids, rettype="medline", retmode="text"
        ) as handle:
            records = list(Medline.parse(handle))
            return [_process_record(record) for record in records]
    except Exception as e:
        print(f"Error fetching chunk {pmids[:5]}...: {e!s}")
        return []


def _process_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Helper function to process a single record.
    Args:
        record: Raw Medline record
    Returns:
        Processed record dictionary
    """
    processed_record = {
        # Basic Information
        "pmid": record.get("PMID", "N/A"),
        "title": record.get("TI", "N/A"),
        "abstract": record.get("AB", "No abstract available"),
        # Journal Information
        "journal": record.get("JT", "N/A"),
        "journal_abbreviation": record.get("TA", "N/A"),
        "journal_iso": record.get("IS", "N/A"),
        "volume": record.get("VI", "N/A"),
        "issue": record.get("IP", "N/A"),
        "pagination": record.get("PG", "N/A"),
        # Dates
        "pubdate": record.get("DP", "N/A"),
        "create_date": record.get("DA", "N/A"),
        "complete_date": record.get("LR", "N/A"),
        "revision_date": record.get("DEP", "N/A"),
        # Publication Details
        "publication_types": record.get("PT", []),
        "publication_status": record.get("PST", "N/A"),
        "language": record.get("LA", ["N/A"])[0],
        # Authors and Affiliations
        "authors": record.get("AU", []),
        "authors_full": record.get("FAU", []),
        "affiliations": record.get("AD", []),
        # Identifiers
        "doi": clean_doi(
            record.get("LID", record.get("AID", ["N/A"])[0])
        ),  # Try LID first, then AID
        "pmcid": record.get("PMC", "N/A"),
        "article_id": record.get("AID", []),
        # Subject Terms
        "mesh_terms": record.get("MH", []),
        "mesh_qualifiers": record.get("SH", []),
        "keywords": record.get("OT", []),
        "chemicals": record.get("RN", []),
        "chemical_names": record.get("NM", []),
        # Grant Information
        "grants": record.get("GR", []),
        "grant_agencies": record.get("GS", []),
        # Additional Information
        "comments_corrections": record.get("CIN", []),
        "publication_country": record.get("PL", "N/A"),
        "article_type": record.get("PT", []),
        "citation_subset": record.get("SB", []),
    }
    return processed_record


async def fetch_pubmed_details_batch(
    pmids: list[str],
    email: str = "your_email@example.com",
    cache_dir: str | None = None,
    chunk_size: int = 100,
    delay_between_chunks: float = 1.0,
    max_retries: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch detailed information from PubMed for a large list of PMIDs with caching and retry support.
    Args:
        pmids: List of PMIDs to fetch
        email: Email for NCBI tracking
        cache_dir: Directory to cache results
        chunk_size: Number of PMIDs per chunk
        delay_between_chunks: Delay between chunks in seconds
        max_retries: Maximum number of retry attempts
    Returns:
        List of detailed PubMed records
    Raises:
        RuntimeError: If there's an error during fetching
    """
    cache_path: Path | None = None
    if cache_dir:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
    # Initialize results storage
    results: dict[str, dict[str, Any]] = {}
    pmids_to_fetch: set[str] = set()
    # Check cache for existing results with progress bar
    if cache_path:
        print("Checking cache...")
        for pmid in tqdm(pmids, desc="Reading cache"):
            cache_file = cache_path / f"{pmid}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        results[pmid] = json.load(f)
                except Exception as e:
                    print(f"\nError reading cache for {pmid}: {e}")
                    pmids_to_fetch.add(pmid)
            else:
                pmids_to_fetch.add(pmid)
    else:
        pmids_to_fetch = set(pmids)
    # Process uncached PMIDs in chunks
    if pmids_to_fetch:
        pmids_list = list(pmids_to_fetch)
        chunks = [
            pmids_list[i : i + chunk_size]
            for i in range(0, len(pmids_list), chunk_size)
        ]
        print(
            f"\nFetching {len(pmids_to_fetch)} uncached PMIDs in "
            f"{len(chunks)} chunks..."
        )
        async with aiohttp.ClientSession() as session:
            with tqdm(total=len(pmids_to_fetch), desc="Downloading") as pbar:
                for chunk in chunks:
                    retry_count = 0
                    while retry_count < max_retries:
                        try:
                            chunk_results = await _fetch_pmids_chunk(
                                chunk, email, session
                            )
                            # Store results and update cache
                            for record in chunk_results:
                                pmid = record["pmid"]
                                results[pmid] = record
                                if cache_path:
                                    cache_file = cache_path / f"{pmid}.json"
                                    with open(cache_file, "w", encoding="utf-8") as f:
                                        json.dump(
                                            record, f, ensure_ascii=False, indent=2
                                        )
                            # Update progress bar
                            pbar.update(len(chunk_results))
                            # Success - break retry loop
                            break
                        except Exception as e:
                            retry_count += 1
                            print(
                                f"\nError processing chunk (attempt {retry_count}/{max_retries}): {e}"
                            )
                            if retry_count == max_retries:
                                print(
                                    f"\nFailed to process chunk after {max_retries} attempts: {chunk}"
                                )
                                # Update progress bar even for failed chunks
                                pbar.update(len(chunk))
                            else:
                                await asyncio.sleep(delay_between_chunks * retry_count)
                    # Delay between chunks to avoid overwhelming the API
                    await asyncio.sleep(delay_between_chunks)
    # Return results in the same order as input PMIDs
    return [
        results.get(pmid, {"pmid": pmid, "error": "Failed to fetch"}) for pmid in pmids
    ]


def fetch_pubmed_details_batch_sync(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    """
    Synchronous wrapper for fetch_pubmed_details_batch.
    Args:
        *args: Positional arguments for fetch_pubmed_details_batch
        **kwargs: Keyword arguments for fetch_pubmed_details_batch
    Returns:
        List of detailed PubMed records
    """
    return asyncio.run(fetch_pubmed_details_batch(*args, **kwargs))


def fetch_pubmed_details(pmids: list[str], email: str) -> list[dict[str, Any]]:
    """
    Fetch PubMed details for a list of PMIDs (synchronous wrapper).
    Args:
        pmids: List of PubMed IDs
        email: Email address for Entrez API
    Returns:
        list[dict[str, Any]]: List of article details
    """
    return fetch_pubmed_details_batch_sync(pmids, email)


def clean_pubmed_cache(
    cache_dir: str | Path, older_than_days: int | None = None
) -> int:
    """
    Clean the PubMed cache directory.
    Args:
        cache_dir: Path to the cache directory
        older_than_days: If provided, only delete files older than this many days
    Returns:
        Number of files deleted
    Raises:
        RuntimeError: If there's an error cleaning the cache directory
    """
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return 0
    deleted_count = 0
    current_time = time.time()
    try:
        with tqdm(list(cache_dir.glob("*.json")), desc="Cleaning cache") as pbar:
            for cache_file in pbar:
                should_delete = True
                if older_than_days is not None:
                    file_age = current_time - cache_file.stat().st_mtime
                    should_delete = file_age > (older_than_days * 24 * 3600)
                if should_delete:
                    cache_file.unlink()
                    deleted_count += 1
                    pbar.set_postfix(deleted=deleted_count)
        # Remove the directory if it's empty
        if not any(cache_dir.iterdir()):
            cache_dir.rmdir()
        return deleted_count
    except Exception as e:
        raise RuntimeError(f"Error cleaning cache directory: {e!s}") from e
