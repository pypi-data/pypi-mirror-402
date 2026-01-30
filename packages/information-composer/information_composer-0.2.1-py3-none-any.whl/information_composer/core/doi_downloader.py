"""
DOI Downloader module for downloading academic papers using DOI.
This module provides functionality to download academic papers using their
Digital Object Identifier (DOI) through the Crossref API.
"""

from dataclasses import dataclass
from pathlib import Path
import time

from habanero import Crossref
import requests
from tqdm import tqdm


@dataclass
class DownloadResult:
    """Result of a single download operation."""

    doi: str
    file_name: str
    downloaded: bool
    file_size: int | None = None
    error_message: str | None = None


@dataclass
class BatchDownloadStats:
    """Statistics for batch download operations."""

    total_papers: int
    successfully_downloaded: int
    subscription_required: int
    doi_not_found: int
    access_restricted: int
    other_errors: int


class DOIDownloader:
    """
    A class to download academic papers using their DOI.
    This class uses the Crossref API to resolve DOIs to PDF URLs and
    then downloads the PDFs with proper error handling and status reporting.
    """

    def __init__(self, email: str | None = None) -> None:
        """
        Initialize DOIDownloader.
        Args:
            email: Email for Crossref API. Providing an email improves service
                and helps with rate limiting. If None, uses anonymous@example.com.
        """
        self.cr = Crossref(mailto=email if email else "anonymous@example.com")
        self.headers = {
            "User-Agent": (
                "information-composer/1.0 "
                "(https://github.com/yourusername/information-composer)"
            )
        }

    def get_pdf_url(self, doi: str) -> str | None:
        """
        Get PDF URL from DOI using Crossref.
        Args:
            doi: The DOI of the paper
        Returns:
            The URL of the PDF if found, None otherwise
        """
        try:
            work = self.cr.works(ids=doi)
            if "message" in work:
                # Check for direct PDF links
                if "link" in work["message"]:
                    for link in work["message"]["link"]:
                        if (
                            "content-type" in link
                            and "pdf" in link["content-type"].lower()
                        ):
                            return str(link["URL"])
                # Fallback to general URL
                if "URL" in work["message"]:
                    return str(work["message"]["URL"])
            return None
        except Exception as e:
            print(f"Error getting PDF URL for DOI {doi}: {e}")
            return None

    def download_pdf(self, url: str, output_path: str | Path) -> bool:
        """
        Download PDF from URL.
        Args:
            url: The URL of the PDF
            output_path: Path where the PDF should be saved
        Returns:
            True if download was successful, False otherwise
        """
        try:
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            # Check for various status codes
            if response.status_code == 401 or response.status_code == 403:
                print("Access denied: This paper requires subscription or payment")
                return False
            elif response.status_code == 404:
                print("PDF not found: The URL is no longer valid")
                return False
            elif response.status_code != 200:
                print(f"Failed to download: HTTP status code {response.status_code}")
                return False
            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if "application/pdf" in content_type:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            elif "text/html" in content_type:
                print("Access restricted: Redirected to login or payment page")
                return False
            else:
                print(f"Unexpected content type: {content_type}")
                return False
        except requests.exceptions.SSLError:
            print("SSL Error: Could not establish secure connection")
            return False
        except requests.exceptions.ConnectionError:
            print("Connection Error: Could not connect to the server")
            return False
        except requests.exceptions.Timeout:
            print("Timeout Error: Request timed out")
            return False
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return False

    def download_by_doi(
        self, doi: str, output_dir: str | Path = "downloads"
    ) -> str | None:
        """
        Download PDF by DOI.
        Args:
            doi: The DOI of the paper
            output_dir: Directory where PDFs should be saved. Defaults to "downloads"
        Returns:
            Path to the downloaded PDF if successful, None otherwise
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        doi = doi.strip()
        output_path = output_dir / f"{doi.replace('/', '_')}.pdf"
        print(f"Processing DOI: {doi}")
        pdf_url = self.get_pdf_url(doi)
        if pdf_url:
            print(f"Found PDF URL: {pdf_url}")
            if self.download_pdf(pdf_url, output_path):
                print(f"Successfully downloaded PDF to: {output_path}")
                return str(output_path)
            else:
                print("Failed to download PDF")
                return None
        else:
            print("Could not find PDF URL")
            return None

    def download_single(
        self, doi: str, output_dir: str | Path, file_name: str | None = None
    ) -> DownloadResult:
        """
        Download a single paper by DOI with detailed output.
        Args:
            doi: The DOI of the paper to download
            output_dir: Directory to save the downloaded paper
            file_name: Custom filename for the PDF. If None, uses DOI as filename
        Returns:
            DownloadResult containing DOI, file_name, and download status
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        # If custom filename is provided, use it; otherwise use DOI
        if file_name:
            # Ensure filename ends with .pdf
            if not file_name.lower().endswith(".pdf"):
                file_name += ".pdf"
            output_path = output_dir / file_name
        else:
            doi_clean = doi.strip().replace("/", "_")
            output_path = output_dir / f"{doi_clean}.pdf"
        print(f"Processing DOI: {doi}")
        pdf_url = self.get_pdf_url(doi)
        if pdf_url:
            print(f"Found PDF URL: {pdf_url}")
            if self.download_pdf(pdf_url, output_path):
                file_size = output_path.stat().st_size
                print(f"Successfully downloaded to: {output_path}")
                print(f"File size: {file_size / 1024:.2f} KB")
                return DownloadResult(
                    doi=doi,
                    file_name=str(output_path),
                    downloaded=True,
                    file_size=file_size,
                )
            else:
                print("Failed to download PDF")
                return DownloadResult(
                    doi=doi,
                    file_name="",
                    downloaded=False,
                    error_message="Failed to download PDF",
                )
        else:
            print("Could not find PDF URL")
            return DownloadResult(
                doi=doi,
                file_name="",
                downloaded=False,
                error_message="Could not find PDF URL",
            )

    def download_batch(
        self, dois: list[str], output_dir: str | Path, delay: int = 2
    ) -> list[DownloadResult]:
        """
        Download multiple papers by their DOIs with detailed output.
        Args:
            dois: List of DOIs to download
            output_dir: Directory to save the downloaded papers
            delay: Delay between downloads in seconds. Defaults to 2
        Returns:
            List of DownloadResult objects containing DOI, file_name, and download status
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        download_results: list[DownloadResult] = []
        status_messages: list[tuple[str, str]] = []
        for doi in tqdm(dois, desc="Downloading papers", unit="paper"):
            result = self.download_single(doi, output_dir)
            download_results.append(result)
            # Store status information for display
            if not result.downloaded:
                try:
                    response = requests.get(
                        f"https://doi.org/{doi}",
                        headers=self.headers,
                        allow_redirects=True,
                        timeout=10,
                    )
                    if response.status_code in (401, 403):
                        status_messages.append((doi, "Subscription required"))
                    elif response.status_code == 404:
                        status_messages.append((doi, "DOI not found"))
                    else:
                        status_messages.append((doi, "Access restricted"))
                except Exception:
                    status_messages.append((doi, "Network error"))
            else:
                status_messages.append((doi, "Success"))
            time.sleep(delay)
        # Print results with improved status information
        print("\nDownload Results:")
        print("-" * 50)
        for result, (_doi, status_msg) in zip(
            download_results, status_messages, strict=False
        ):
            if result.downloaded and result.file_name:
                file_size = result.file_size or 0
                print(f"✓ {result.doi}")
                print(f"  └─ Saved to: {result.file_name}")
                print(f"  └─ Size: {file_size / 1024:.2f} KB")
            else:
                print(f"✗ {result.doi}")
                print(f"  └─ Status: {status_msg}")
            print("-" * 50)
        # Print summary
        self._print_batch_summary(download_results, status_messages)
        return download_results

    def _print_batch_summary(
        self, results: list[DownloadResult], status_messages: list[tuple[str, str]]
    ) -> None:
        """Print a summary of batch download results."""
        stats = BatchDownloadStats(
            total_papers=len(results),
            successfully_downloaded=sum(1 for r in results if r.downloaded),
            subscription_required=sum(
                1 for _doi, msg in status_messages if msg == "Subscription required"
            ),
            doi_not_found=sum(
                1 for _doi, msg in status_messages if msg == "DOI not found"
            ),
            access_restricted=sum(
                1 for _doi, msg in status_messages if msg == "Access restricted"
            ),
            other_errors=sum(
                1
                for _doi, msg in status_messages
                if msg
                not in [
                    "Success",
                    "Subscription required",
                    "DOI not found",
                    "Access restricted",
                ]
            ),
        )
        print("\nDownload Summary:")
        print(f"Total papers: {stats.total_papers}")
        print(f"Successfully downloaded: {stats.successfully_downloaded}")
        if stats.subscription_required > 0:
            print(f"Subscription required: {stats.subscription_required}")
        if stats.doi_not_found > 0:
            print(f"DOI not found: {stats.doi_not_found}")
        if stats.access_restricted > 0:
            print(f"Access restricted: {stats.access_restricted}")
        if stats.other_errors > 0:
            print(f"Other errors: {stats.other_errors}")
