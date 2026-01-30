"""Data extraction component for Google Scholar HTML parsing."""

from datetime import datetime
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from ..models import GoogleScholarPaper


logger = logging.getLogger(__name__)


class DataExtractor:
    """Extract paper metadata from Google Scholar HTML."""

    def __init__(self) -> None:
        """Initialize data extractor."""
        self.base_url = "https://scholar.google.com"
        # Regex patterns for parsing
        self.year_pattern = re.compile(r"\b(19\d{2}|20\d{2})\b")
        self.volume_pattern = re.compile(r"\bvol\.?\s*(\d+)", re.IGNORECASE)
        self.issue_pattern = re.compile(r"\bno\.?\s*(\d+)", re.IGNORECASE)
        self.pages_pattern = re.compile(r"\bpp\.?\s*([\d-]+)", re.IGNORECASE)
        self.doi_pattern = re.compile(r"10\.\d{4,}/[^\s,]+")

    def extract_papers(
        self, elements: list[Tag | BeautifulSoup | dict], query: str = ""
    ) -> list[GoogleScholarPaper]:
        """
        Extract papers from a list of HTML elements.
        Args:
            elements: List of BeautifulSoup elements or paper dictionaries
            query: Original search query
        Returns:
            List of GoogleScholarPaper objects
        """
        papers = []
        for i, element in enumerate(elements):
            try:
                if isinstance(element, dict):
                    # Handle scholarly API results
                    paper = self._extract_from_scholarly_dict(element, query, i)
                else:
                    # Handle HTML elements
                    paper = self._extract_from_html_element(element, query, i)
                if paper and paper.is_valid():
                    papers.append(paper)
                    logger.debug(f"Extracted paper: {paper.title[:50]}...")
                else:
                    logger.debug(f"Skipped invalid paper at index {i}")
            except Exception as e:
                logger.warning(f"Error extracting paper at index {i}: {e}")
                continue
        logger.info(
            f"Successfully extracted {len(papers)} papers from {len(elements)} elements"
        )
        return papers

    def _extract_from_html_element(
        self, element: Tag, query: str, rank: int
    ) -> GoogleScholarPaper | None:
        """Extract paper data from HTML element."""
        try:
            # Find the main title element
            title_element = element.find("h3", class_="gs_rt") or element.find(
                "a", class_="gs_rt"
            )
            if not title_element:
                return None
            # Extract title and URL
            title_link = (
                title_element.find("a")
                if hasattr(title_element, "find")
                and hasattr(title_element, "name")
                and title_element.name != "a"
                else title_element
            )
            if title_link and hasattr(title_link, "get_text"):
                title_text = title_link.get_text()
            else:
                title_text = title_element.get_text()
            title = self._clean_text(title_text)
            if not title:
                return None
            # Extract Google Scholar URL and ID
            scholar_url = None
            scholar_id = None
            if title_link and hasattr(title_link, "get") and title_link.get("href"):
                href = title_link.get("href")
                if isinstance(href, str):
                    scholar_url = urljoin(self.base_url, href)
                    scholar_id = self._extract_scholar_id(scholar_url)
            if not scholar_id:
                scholar_id = f"gs_{hash(title + query)}_{rank}"
            # Extract authors and publication info
            authors_element = element.find("div", class_="gs_a")
            if authors_element is not None and hasattr(authors_element, "get_text"):
                # Type check to ensure it's a Tag
                from bs4 import Tag

                if isinstance(authors_element, Tag):
                    authors, journal, year, venue_info = self._parse_authors_and_venue(
                        authors_element
                    )
                else:
                    authors, journal, year, venue_info = [], None, None, {}
            else:
                authors, journal, year, venue_info = [], None, None, {}
            # Extract abstract/snippet
            abstract_element = element.find("div", class_="gs_rs")
            abstract = (
                self._clean_text(abstract_element.get_text())
                if abstract_element
                else None
            )
            # Extract citation count
            citation_count = self._extract_citation_count(element)
            # Extract PDF link
            pdf_url = self._extract_pdf_url(element)
            # Extract additional metadata
            doi = self._extract_doi(element, title, venue_info)
            # Create paper object
            paper = GoogleScholarPaper(
                google_scholar_id=scholar_id,
                title=title,
                authors=authors,
                journal=journal.get("name") if journal else None,
                year=year,
                abstract=abstract,
                pdf_url=pdf_url,
                doi=doi,
                citation_count=citation_count,
                search_rank=rank + 1,
                google_scholar_url=scholar_url,
                search_query=query,
                volume=journal.get("volume") if journal else None,
                issue=journal.get("issue") if journal else None,
                pages=journal.get("pages") if journal else None,
                publisher=journal.get("publisher") if journal else None,
                venue_type=venue_info.get("type") if venue_info else None,
            )
            # Update confidence score
            paper.update_confidence_score()
            return paper
        except Exception as e:
            logger.error(f"Error extracting from HTML element: {e}")
            return None

    def _extract_from_scholarly_dict(
        self, data: dict, query: str, rank: int
    ) -> GoogleScholarPaper | None:
        """Extract paper data from scholarly API dictionary."""
        try:
            title = data.get("title", "")
            if not title:
                return None
            # Extract basic information
            authors = [author.get("name", "") for author in data.get("author", [])]
            year = self._extract_year_from_text(data.get("pub_year", ""))
            abstract = data.get("abstract", "")
            # Extract venue information
            venue = data.get("venue", "")
            journal_info = self._parse_venue_string(venue)
            # Extract URLs
            scholar_url = data.get("pub_url", "")
            pdf_url = data.get("eprint_url", "")
            # Extract identifiers
            scholar_id = data.get("gsrank", f"gs_{hash(title + query)}_{rank}")
            citation_count = data.get("num_citations", 0)
            # Create paper object
            paper = GoogleScholarPaper(
                google_scholar_id=str(scholar_id),
                title=title,
                authors=authors,
                journal=journal_info.get("name"),
                year=year,
                abstract=abstract,
                pdf_url=pdf_url,
                citation_count=citation_count,
                search_rank=rank + 1,
                google_scholar_url=scholar_url,
                search_query=query,
                volume=journal_info.get("volume"),
                issue=journal_info.get("issue"),
                pages=journal_info.get("pages"),
                publisher=journal_info.get("publisher"),
            )
            paper.update_confidence_score()
            return paper
        except Exception as e:
            logger.error(f"Error extracting from scholarly dict: {e}")
            return None

    def _parse_authors_and_venue(
        self, element: Tag
    ) -> tuple[list[str], dict | None, int | None, dict]:
        """Parse authors and venue information from the gs_a element."""
        if not element:
            return [], None, None, {}
        text = self._clean_text(element.get_text())
        authors = []
        journal_info = None
        year = None
        venue_info = {}
        # Split by common delimiters
        parts = re.split(r" - | \u2013 |\u2014", text)  # em dash, en dash, hyphen
        if len(parts) >= 1:
            # First part usually contains authors
            author_part = parts[0].strip()
            authors = self._parse_authors(author_part)
        if len(parts) >= 2:
            # Second part usually contains venue and year
            venue_part = parts[1].strip()
            journal_info = self._parse_venue_string(venue_part)
            year = self._extract_year_from_text(venue_part)
            venue_info = self._classify_venue_type(venue_part)
        return authors, journal_info, year, venue_info

    def _parse_authors(self, author_text: str) -> list[str]:
        """Parse author names from text."""
        if not author_text:
            return []
        # Remove common prefixes and clean
        author_text = re.sub(r"^(by\s+)?", "", author_text, flags=re.IGNORECASE)
        # Split by common separators
        separators = [", ", " and ", " & ", ";"]
        authors = [author_text]
        for sep in separators:
            new_authors = []
            for author in authors:
                new_authors.extend(author.split(sep))
            authors = new_authors
        # Clean and filter authors
        cleaned_authors = []
        for author in authors:
            author = author.strip()
            if author and len(author) > 1 and not self._is_venue_text(author):
                cleaned_authors.append(author)
        return cleaned_authors[:10]  # Limit to reasonable number

    def _parse_venue_string(self, venue_text: str) -> dict[str, str | None]:
        """Parse venue string to extract journal, volume, issue, pages, etc."""
        if not venue_text:
            return {}
        info: dict[str, str | None] = {
            "name": None,
            "volume": None,
            "issue": None,
            "pages": None,
            "publisher": None,
        }
        # Extract volume
        volume_match = self.volume_pattern.search(venue_text)
        if volume_match:
            info["volume"] = volume_match.group(1)
        # Extract issue
        issue_match = self.issue_pattern.search(venue_text)
        if issue_match:
            info["issue"] = issue_match.group(1)
        # Extract pages
        pages_match = self.pages_pattern.search(venue_text)
        if pages_match:
            info["pages"] = pages_match.group(1)
        # Extract journal name (everything before volume/year or the whole string)
        name_text = venue_text
        for pattern in [self.volume_pattern, self.year_pattern]:
            match = pattern.search(name_text)
            if match:
                name_text = name_text[: match.start()].strip()
                break
        # Clean up the name
        name_text = re.sub(r"[,\-\u2013\u2014]\s*$", "", name_text).strip()
        if name_text and not self._is_year_only(name_text):
            info["name"] = name_text
        return info

    def _classify_venue_type(self, venue_text: str) -> dict[str, str]:
        """Classify the type of venue (journal, conference, etc.)."""
        venue_lower = venue_text.lower()
        # Conference indicators
        conf_indicators = [
            "proceedings",
            "conference",
            "workshop",
            "symposium",
            "meeting",
            "congress",
            "summit",
            "ieee",
            "acm",
        ]
        # Journal indicators
        journal_indicators = [
            "journal",
            "review",
            "magazine",
            "bulletin",
            "quarterly",
            "monthly",
            "annual",
            "international",
            "nature",
            "science",
        ]
        # Book indicators
        book_indicators = ["book", "handbook", "manual", "guide"]
        if any(indicator in venue_lower for indicator in conf_indicators):
            return {"type": "conference"}
        elif any(indicator in venue_lower for indicator in journal_indicators):
            return {"type": "journal"}
        elif any(indicator in venue_lower for indicator in book_indicators):
            return {"type": "book"}
        else:
            return {"type": "unknown"}

    def _extract_citation_count(self, element: Tag) -> int:
        """Extract citation count from element."""
        try:
            # Look for "Cited by X" link
            cited_link = element.find("a", string=re.compile(r"Cited by \d+"))
            if cited_link:
                match = re.search(r"Cited by (\d+)", cited_link.get_text())
                if match:
                    return int(match.group(1))
            # Alternative patterns
            for link in element.find_all("a"):
                text = link.get_text()
                if "cited by" in text.lower():
                    numbers = re.findall(r"\d+", text)
                    if numbers:
                        return int(numbers[0])
            return 0
        except Exception:
            return 0

    def _extract_pdf_url(self, element: Tag) -> str | None:
        """Extract PDF URL from element."""
        try:
            # Look for PDF links in various places
            selectors = [
                'a[href*=".pdf"]',
                'a[href*="pdf"]',
                ".gs_or_ggsm a",
                ".gs_ggsd a",
            ]
            for selector in selectors:
                pdf_link = element.select_one(selector)
                if pdf_link and pdf_link.get("href"):
                    url = pdf_link["href"]
                    if isinstance(url, str) and url.startswith("/"):
                        url = urljoin(self.base_url, url)
                    elif isinstance(url, str):
                        return url
            return None
        except Exception:
            return None

    def _extract_doi(self, element: Tag, title: str, venue_info: dict) -> str | None:
        """Extract DOI from element or text."""
        try:
            # Look for DOI in links
            for link in element.find_all("a"):
                href = link.get("href", "") if hasattr(link, "get") else ""
                if isinstance(href, str) and "doi.org" in href:
                    doi_match = self.doi_pattern.search(href)
                    if doi_match:
                        return doi_match.group(0)
            # Look for DOI in text
            text = element.get_text()
            doi_match = self.doi_pattern.search(text)
            if doi_match:
                return doi_match.group(0)
            return None
        except Exception:
            return None

    def _extract_scholar_id(self, url: str) -> str | None:
        """Extract Google Scholar ID from URL."""
        try:
            if "cluster=" in url:
                return url.split("cluster=")[1].split("&")[0]
            elif "cites=" in url:
                return url.split("cites=")[1].split("&")[0]
            return None
        except Exception:
            return None

    def _extract_year_from_text(self, text: str) -> int | None:
        """Extract year from text."""
        if not text:
            return None
        matches = self.year_pattern.findall(text)
        if matches:
            # Get the most recent year that's not in the future
            current_year = datetime.now().year
            valid_years = [
                int(year) for year in matches if int(year) <= current_year + 1
            ]
            if valid_years:
                return max(valid_years)
        return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r"\s+", " ", text.strip())
        # Remove special characters that might cause issues
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)  # Zero-width characters
        return text

    def _is_venue_text(self, text: str) -> bool:
        """Check if text looks like venue information rather than author."""
        venue_indicators = [
            "proceedings",
            "journal",
            "conference",
            "workshop",
            "ieee",
            "acm",
            "springer",
            "elsevier",
            "vol",
            "pp",
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in venue_indicators)

    def _is_year_only(self, text: str) -> bool:
        """Check if text is just a year."""
        return bool(re.match(r"^\d{4}$", text.strip()))
