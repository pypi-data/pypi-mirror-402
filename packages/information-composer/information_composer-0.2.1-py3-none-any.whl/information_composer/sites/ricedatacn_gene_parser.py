"""Parser module for extracting gene information from ricedata.cn.
This module provides functionality to parse gene information from the RiceDataCN
website, including basic gene information, ontology data, and references.

Features:
- Automatic encoding detection (GBK/GB2312/UTF-8)
- Concurrent reference fetching for improved performance
- Retry mechanism with exponential backoff
- Rate limiting to avoid server overload
- Caching support for parsed genes
- Comprehensive logging
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import os
import re
import time
import traceback
from typing import Any, ClassVar

from bs4 import BeautifulSoup, Tag
import requests

from information_composer.sites.base import BaseSiteCollector


# Configure module logger
logger = logging.getLogger(__name__)


class RiceGeneParser(BaseSiteCollector):
    """Parser for extracting gene information from ricedata.cn.

    This class provides methods to parse gene information from the RiceDataCN
    website, including basic gene information, ontology data, and references.

    Attributes:
        name: The name of the parser
        config: Configuration dictionary with optional settings for timeout, retries, etc.
        headers: HTTP request headers
        base_url: Base URL for the RiceDataCN gene pages

    Example:
        >>> parser = RiceGeneParser(config={"timeout": 60, "retries": 3})
        >>> gene_info = parser.parse_gene_page("318", "downloads/genes")
        >>> print(gene_info["basic_info"].get("基因名称", ""))
    """

    # Supported Chinese encodings (in order of preference)
    ENCODING_PRIORITY: ClassVar[list[str]] = ["gbk", "gb2312", "utf-8", "gb18030"]

    # Default settings
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRIES = 3
    DEFAULT_MAX_WORKERS = 5  # Concurrent workers for reference fetching
    DEFAULT_RATE_LIMIT_DELAY = 1.0  # Seconds between requests

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the RiceGeneParser.

        Args:
            config: Optional configuration dictionary with keys:
                - timeout: Request timeout in seconds (default: 30)
                - retries: Number of retry attempts for failed requests (default: 3)
                - max_workers: Max concurrent workers for reference fetching (default: 5)
                - rate_limit_delay: Delay between requests in seconds (default: 1.0)
                - enable_cache: Enable caching of parsed genes (default: False)
                - cache_dir: Directory for cache files (default: "cache/genes")
        """
        super().__init__(config)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
        }

        # Configuration with defaults
        self.timeout = self.config.get("timeout", self.DEFAULT_TIMEOUT)
        self.retries = self.config.get("retries", self.DEFAULT_RETRIES)
        self.max_workers = self.config.get("max_workers", self.DEFAULT_MAX_WORKERS)
        self.rate_limit_delay = self.config.get(
            "rate_limit_delay", self.DEFAULT_RATE_LIMIT_DELAY
        )
        self.enable_cache = self.config.get("enable_cache", False)
        self.cache_dir = self.config.get("cache_dir", "cache/genes")

        # Request session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Cache for parsed genes (in-memory)
        self._cache: dict[str, dict[str, Any]] = {}

        # Rate limiting
        self._last_request_time = 0.0

        self.base_url = "https://www.ricedata.cn/gene/list"
        logger.info(f"RiceGeneParser initialized with config: {self.config}")

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests.

        Ensures that requests are spaced out to avoid overloading the server.
        """
        current_time = time.monotonic()
        elapsed = current_time - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    def _fetch_page(
        self, url: str, encoding: str | None = None
    ) -> tuple[BeautifulSoup | None, str]:
        """Fetch a webpage with retry logic and encoding detection.

        Args:
            url: The URL to fetch
            encoding: Optional specific encoding to use

        Returns:
            Tuple of (BeautifulSoup object or None, detected encoding or empty string)
        """
        self._rate_limit()

        last_error: Exception | None = None
        detected_encoding = encoding or ""

        for attempt in range(self.retries):
            try:
                logger.debug(
                    f"Fetching URL (attempt {attempt + 1}/{self.retries}): {url}"
                )
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                # Detect encoding if not specified
                if encoding:
                    response.encoding = encoding
                    detected_encoding = encoding
                else:
                    # Try to detect encoding from content or headers
                    response_encoding = self._detect_encoding(response)
                    response.encoding = response_encoding
                    detected_encoding = response_encoding

                soup = BeautifulSoup(response.text, "html.parser")
                return soup, detected_encoding

            except requests.exceptions.HTTPError as e:
                last_error = e
                logger.warning(f"HTTP error fetching {url}: {e}")
                if e.response is not None and e.response.status_code == 404:
                    logger.info(f"Page not found (404): {url}")
                    return None, ""

                if attempt < self.retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Request error fetching {url}: {e}")
                if attempt < self.retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        logger.error(
            f"Failed to fetch {url} after {self.retries} attempts: {last_error}"
        )
        return None, detected_encoding

    def _detect_encoding(self, response: requests.Response) -> str:
        """Detect the encoding of a response.

        Args:
            response: The HTTP response object

        Returns:
            Detected encoding string
        """
        # First check if encoding is specified in headers
        content_type = response.headers.get("content-type", "")
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].split(";")[0].strip()
            if encoding.lower() in ["gbk", "gb2312", "utf-8", "gb18030"]:
                return encoding

        # Try to detect from content
        content = response.content[:1000]
        for enc in self.ENCODING_PRIORITY:
            try:
                content.decode(enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue

        # Default fallback
        return "gbk"

    def collect(self) -> Any:
        """Collect gene information (not implemented for this parser).

        This method is not used for this parser as it requires specific gene IDs.
        Use parse_gene_page or parse_multiple_genes instead.

        Returns:
            None

        Raises:
            NotImplementedError: This method is not implemented for this parser
        """
        raise NotImplementedError("Use parse_gene_page or parse_multiple_genes instead")

    def compose(self, data: Any) -> Any:
        """Compose collected data (not implemented for this parser).

        Args:
            data: The data to compose

        Returns:
            The composed data

        Raises:
            NotImplementedError: This method is not implemented for this parser
        """
        raise NotImplementedError("Use parse_gene_page or parse_multiple_genes instead")

    def parse_gene_page(
        self, gene_id: str, output_dir: str = "downloads/genes"
    ) -> dict[str, Any] | None:
        """Parse gene information from ricedata.cn webpage.

        Args:
            gene_id: The gene ID to parse (e.g., "318", "34590")
            output_dir: Directory to save the output file

        Returns:
            Dictionary containing parsed gene information, or None if parsing failed

        Example:
            >>> parser = RiceGeneParser()
            >>> result = parser.parse_gene_page("318", "downloads/genes")
            >>> if result:
            ...     print(f"Gene: {result['basic_info'].get('基因名称', 'N/A')}")
        """
        # Check cache first
        cache_key = f"gene_{gene_id}"
        if self.enable_cache and cache_key in self._cache:
            logger.info(f"Returning cached result for gene {gene_id}")
            return self._cache[cache_key]

        url = f"{self.base_url}/{gene_id}.htm"
        logger.info(f"Parsing gene page: {url}")

        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Get webpage content with encoding detection
            result = self._fetch_page(url)
            soup, encoding = result

            if soup is None:
                logger.warning(f"Failed to fetch gene page for ID: {gene_id}")
                return None

            logger.debug(f"Detected encoding: {encoding}")

            # Get basic reference information
            references = self._parse_references(soup)

            # Optionally fetch reference details concurrently
            if references and self.max_workers > 1:
                references = self._fetch_reference_details_concurrent(references)

            gene_info: dict[str, Any] = {
                "gene_id": gene_id,
                "url": url,
                "encoding": encoding,
                "basic_info": self._parse_basic_info(soup),
                "description": self._parse_gene_description(soup),
                "ontology": self._parse_ontology(soup),
                "references": references,
            }

            # Save to JSON file
            output_file = os.path.join(output_dir, f"gene_{gene_id}.json")
            self._save_to_json(gene_info, output_file)

            # Cache if enabled
            if self.enable_cache:
                self._cache[cache_key] = gene_info

            logger.info(f"Successfully parsed gene {gene_id}")
            return gene_info

        except requests.exceptions.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                logger.info(f"Gene ID {gene_id} not found (404 error)")
                return None
            logger.error(f"HTTP error parsing gene {gene_id}: {e}")
            raise

        except Exception as e:
            logger.error(f"Error parsing gene page {gene_id}: {e!s}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

    def parse_multiple_genes(
        self,
        gene_ids: list[str],
        output_dir: str = "downloads/genes",
        fetch_details: bool = True,
    ) -> list[dict[str, Any] | None]:
        """Parse multiple genes and save their information.

        Args:
            gene_ids: List of gene IDs to parse (e.g., ["318", "34590", "420"])
            output_dir: Directory to save the JSON files
            fetch_details: Whether to fetch reference details (default: True)

        Returns:
            List of parsed gene information dictionaries

        Example:
            >>> parser = RiceGeneParser(config={"max_workers": 3})
            >>> results = parser.parse_multiple_genes(
            ...     ["318", "34590", "420", "70000"],
            ...     "downloads/genes"
            ... )
            >>> success_count = len([r for r in results if r])
            >>> print(f"Successfully parsed {success_count}/{len(results)} genes")
        """
        results: list[dict[str, Any] | None] = []
        total = len(gene_ids)

        logger.info(f"Starting to parse {total} genes")

        for index, gene_id in enumerate(gene_ids, 1):
            logger.info(f"Parsing gene {index}/{total}: {gene_id}")
            gene_info = self.parse_gene_page(gene_id, output_dir)
            results.append(gene_info)

        # Summary
        success_count = len([r for r in results if r])
        logger.info(
            f"Completed parsing {total} genes: "
            f"{success_count} successful, {total - success_count} failed"
        )

        return results

    def _fetch_reference_details_concurrent(
        self, references: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Fetch reference details concurrently for better performance.

        Args:
            references: List of reference dictionaries with reference_url key

        Returns:
            Updated list with reference details added
        """
        if not references:
            return references

        updated_references = [ref.copy() for ref in references]

        def fetch_single_reference(ref: dict[str, str]) -> tuple[int, dict[str, str]]:
            """Fetch details for a single reference.

            Args:
                ref: Reference dictionary with reference_url

            Returns:
                Tuple of (index, updated reference)
            """
            ref_url = ref.get("reference_url", "")
            if not ref_url:
                return (0, ref)

            index = ref.get("_index", 0)
            logger.debug(f"Fetching reference details: {ref_url}")

            # Add rate limiting for reference requests
            self._rate_limit()

            try:
                # Ensure absolute URL
                if not ref_url.startswith("http"):
                    ref_url = f"https://www.ricedata.cn/{ref_url.lstrip('/')}"

                response = self.session.get(ref_url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = "utf-8"

                soup = BeautifulSoup(response.text, "html.parser")
                details = self._extract_reference_details(soup)

                ref.update(details)
                return (index, ref)

            except Exception as e:
                logger.warning(f"Error fetching reference {ref_url}: {e}")
                return (index, ref)

        # Add index for ordering
        for i, ref in enumerate(updated_references):
            ref["_index"] = i

        # Fetch details concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(fetch_single_reference, ref): ref
                for ref in updated_references
            }

            for future in as_completed(futures):
                try:
                    index, updated_ref = future.result()
                    # Update the reference in the list
                    if index < len(updated_references):
                        updated_references[index] = updated_ref
                except Exception as e:
                    logger.error(f"Error in concurrent fetch: {e}")

        # Remove index key from results
        for ref in updated_references:
            ref.pop("_index", None)

        return updated_references

    def _extract_reference_details(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract detailed information from a reference page.

        Args:
            soup: BeautifulSoup object of the reference page

        Returns:
            Dictionary containing reference details (title, doi, abstract_en, abstract_cn)
        """
        details: dict[str, str] = {}

        try:
            # Get title
            title = soup.find("h1")
            if title:
                details["title"] = title.get_text(strip=True)

            # Get DOI
            h5_elements = soup.find_all("h5")
            for h5 in h5_elements:
                h5_text = h5.get_text()
                if "DOI:" in h5_text:
                    doi_match = re.search(r"DOI:\s*(10\.\d{4,}/[-._;()/:\w]+)", h5_text)
                    if doi_match:
                        details["doi"] = doi_match.group(1)
                    break

            # Get English abstract
            en_p = soup.find(
                "p", style=lambda x: x and "margin" in x and "margin-bottom:10" in x
            )
            if en_p:
                details["abstract_en"] = en_p.get_text(strip=True)

            # Get Chinese abstract
            cn_title = soup.find("h1", style=lambda x: x and "color: orangered" in x)
            if cn_title:
                cn_p = cn_title.find_next("p")
                if cn_p and isinstance(cn_p, Tag):
                    # Preserve line breaks and indentation
                    text_parts = []
                    for element in cn_p.children:
                        if not isinstance(element, Tag):
                            continue
                        if element.name == "br":
                            text_parts.append("\n")
                        elif element.name in ("em", "sup", "sub"):
                            text_parts.append(element.get_text())
                        else:
                            try:
                                text = str(element).replace("&emsp;", "    ")
                                text_parts.append(text)
                            except Exception:
                                text_parts.append(str(element))
                    details["abstract_cn"] = "".join(text_parts).strip()

        except Exception as e:
            logger.warning(f"Error extracting reference details: {e}")

        return details

    def _clean_text(self, text: str | None) -> str:
        """Clean and normalize text.

        Args:
            text: The text to clean (can be None)

        Returns:
            Cleaned text string
        """
        if text is None:
            return ""

        # Remove special characters and normalize spaces
        text = text.replace("：", "").replace(":", "")
        text = re.sub(r"\s+", " ", text)
        # Remove any potential BOM or special characters
        text = text.replace("\ufeff", "")
        return text.strip()

    def _parse_basic_info(self, soup: BeautifulSoup) -> dict[str, str]:
        """Parse basic gene information from the first table.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Dictionary containing basic gene information

        Example:
            >>> soup = BeautifulSoup(html, "html.parser")
            >>> info = parser._parse_basic_info(soup)
            >>> print(info.get("基因名称", ""))
        """
        basic_info: dict[str, str] = {}
        tables = soup.find_all("table")

        if not tables:
            logger.debug("No tables found in basic info section")
            return basic_info

        table = tables[0]

        if not isinstance(table, Tag):
            return basic_info

        rows = table.find_all("tr")
        current_key: str | None = None
        current_value: list[str] = []

        for row in rows:
            if not isinstance(row, Tag):
                continue

            cols = row.find_all("td")
            if len(cols) >= 2:
                # Get the text content
                key_text = self._clean_text(cols[0].get_text(strip=True))
                value_text = self._clean_text(cols[1].get_text(strip=True))

                # If it's a new key
                if key_text:
                    # Save previous key-value pair if exists
                    if current_key and current_value:
                        basic_info[current_key] = " ".join(current_value)
                    # Start new key-value pair
                    current_key = key_text
                    current_value = [value_text]
                else:
                    # Append to current value if it's a continuation
                    if current_key and value_text:
                        current_value.append(value_text)

        # Save the last key-value pair
        if current_key and current_value:
            basic_info[current_key] = " ".join(current_value)

        logger.debug(f"Parsed {len(basic_info)} basic info fields")
        return basic_info

    def _parse_ontology(self, soup: BeautifulSoup) -> dict[str, list[dict[str, str]]]:
        """Parse gene ontology information from the ontology table.

        This method looks for the table containing ontology terms like:
        - 表型特征 (Traits) with TO:xxxxxx IDs
        - 分子功能 (Molecular Function) with GO:xxxxxx IDs
        - 生物进程 (Biological Process) with GO:xxxxxx IDs
        - 细胞结构 (Cellular Component) with GO:xxxxxx IDs
        - 形态构造 (Morphology) with PO:xxxxxx IDs

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Dictionary containing ontology information with category names as keys
        """
        ontology: dict[str, list[dict[str, str]]] = {}
        tables = soup.find_all("table")

        if not tables:
            logger.debug("No tables found for ontology")
            return ontology

        # Ontology category names to look for
        ontology_categories = [
            "表型特征",
            "分子功能",
            "生物进程",
            "细胞结构",
            "形态构造",
        ]

        # Pattern to match ontology IDs with their full term (e.g., "粘性胚乳(TO:0000098)")
        # This pattern captures the term before the ID (excluding commas and spaces)
        ontology_pattern = re.compile(r"([^\(\),]+?)\s*\((TO|GO|PO):(\d+)\)")

        # Search through all tables to find ontology categories
        for table in tables:
            if not isinstance(table, Tag):
                continue

            rows = table.find_all("tr")

            for row in rows:
                if not isinstance(row, Tag):
                    continue

                # Check both <td> and <th> tags for category names
                # Some pages use <th> for headers, others use <td>
                first_cell = row.find("th") or row.find("td")
                second_cell = None

                # Find the second cell
                all_cells = row.find_all(["td", "th"])
                if len(all_cells) >= 2:
                    first_cell = all_cells[0]
                    second_cell = all_cells[1]

                if not first_cell or not second_cell:
                    continue

                key = self._clean_text(first_cell.get_text(strip=True))

                # Check if this is an ontology category
                if key not in ontology_categories:
                    continue

                # Get all text from the second column
                text_content = second_cell.get_text(strip=True)

                # Find all ontology IDs and their terms
                matches = ontology_pattern.findall(text_content)

                if matches:
                    terms: list[dict[str, str]] = []
                    for term_text, id_prefix, id_number in matches:
                        term_text = self._clean_text(term_text)
                        full_id = f"{id_prefix}:{id_number}"
                        if term_text and full_id:
                            terms.append(
                                {
                                    "term": term_text,
                                    "id": full_id,
                                }
                            )

                    # Remove duplicates while preserving order
                    seen_ids: set[str] = set()
                    unique_terms: list[dict[str, str]] = []
                    for term in terms:
                        if term["id"] not in seen_ids:
                            seen_ids.add(term["id"])
                            unique_terms.append(term)

                    if unique_terms:
                        ontology[key] = unique_terms
                        logger.debug(f"Found {len(unique_terms)} terms for {key}")

        logger.debug(f"Parsed {len(ontology)} ontology categories")
        return ontology

    def _parse_gene_description(self, soup: BeautifulSoup) -> str:
        """Parse gene description from the content cell.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Gene description text with section markers
        """
        try:
            # Find the content cell with colspan=2
            content_cell = soup.find(
                "td", attrs={"colspan": "2", "style": "padding: 5px; font-size: 14px"}
            )

            if not content_cell or not isinstance(content_cell, Tag):
                logger.debug("No gene description cell found")
                return ""

            # Get all description text, including titles
            description_text: list[str] = []

            # Get red text part (locus information)
            red_text = content_cell.find(
                "p", style="color: rgb(255, 0, 0); font-weight: bold"
            )
            if red_text:
                description_text.append(red_text.get_text(strip=True))

            # Get all h5 titles and corresponding paragraphs
            current_section: str | None = None
            for element in content_cell.children:
                if not isinstance(element, Tag):
                    continue

                if element.name == "h5":
                    current_section = element.get_text(strip=True)
                    description_text.append(f"\n{current_section}")
                elif element.name == "p":
                    # Remove HTML tags but preserve text format
                    text = element.get_text(strip=True)
                    if text:
                        description_text.append(text)

            # Filter out the "【相关登录号】" section
            filtered_text = [
                text for text in description_text if "【相关登录号】" not in text
            ]

            # Combine all text with newlines
            return "\n".join(filtered_text)

        except Exception as e:
            logger.warning(f"Error parsing gene description: {e}")
            return ""

    def _parse_references(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Parse reference information from the reference table.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of reference dictionaries with reference_info and reference_url keys
        """
        references: list[dict[str, str]] = []

        try:
            # Find all reference table rows
            ref_rows = soup.find_all(
                "td",
                style=lambda x: x
                and (
                    "BACKGROUND-COLOR:#eef9de" in x or "BACKGROUND-COLOR:#ffffcc" in x
                ),
            )

            for row in ref_rows:
                if not isinstance(row, Tag):
                    continue

                link = row.find("a")
                if not link or not isinstance(link, Tag):
                    continue

                # Fix URL construction
                href = link.get("href")
                if not href or not isinstance(href, str):
                    continue

                url = "https://www.ricedata.cn/" + href.replace("../../", "")

                # Extract complete reference text
                text_parts = []
                for content in row.stripped_strings:
                    if content not in (".", "(", ")", ":"):
                        text_parts.append(content)

                reference_info = " ".join(text_parts[1:]) if len(text_parts) > 1 else ""
                reference = {"reference_info": reference_info, "reference_url": url}
                references.append(reference)

            logger.debug(f"Found {len(references)} references")

        except Exception as e:
            logger.warning(f"Error parsing references: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")

        return references

    def _get_reference_details(self, ref_url: str) -> dict[str, str]:
        """Get detailed information for a reference.

        Note: This method is kept for backward compatibility.
        Use _fetch_reference_details_concurrent for better performance.

        Args:
            ref_url: URL of the reference

        Returns:
            Dictionary containing reference details
        """
        try:
            if ref_url.startswith("@"):
                ref_url = ref_url[1:]

            if not ref_url.startswith("http"):
                ref_url = f"https://www.ricedata.cn/{ref_url}"

            self._rate_limit()

            response = self.session.get(ref_url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            return self._extract_reference_details(soup)

        except Exception as e:
            logger.warning(f"Error getting reference details from {ref_url}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return {}

    def _save_to_json(self, data: dict[str, Any], output_file: str) -> None:
        """Save parsed data to JSON file.

        Args:
            data: Data to save
            output_file: Output file path
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving to JSON {output_file}: {e}")

    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_cache_size(self) -> int:
        """Get the number of cached items.

        Returns:
            Number of cached gene entries
        """
        return len(self._cache)
