"""Result processing component for data cleaning, validation, and enhancement."""

# import asyncio  # Unused import
from collections import defaultdict
from difflib import SequenceMatcher
import logging
import re

from information_composer.core.doi_downloader import DOIDownloader
from information_composer.core.utils import clean_doi
from information_composer.pubmed.pubmed import query_pmid

from ..models import GoogleScholarPaper, SearchConfig


logger = logging.getLogger(__name__)


class ResultProcessor:
    """Process and enhance Google Scholar search results."""

    def __init__(self, config: SearchConfig):
        """Initialize result processor with configuration."""
        self.config = config
        self.doi_downloader = DOIDownloader() if config.resolve_dois else None
        # Patterns for data cleaning
        self.title_patterns = [
            (r"\[PDF\]", ""),
            (r"\[HTML\]", ""),
            (r"\[CITATION\]", ""),
            (r"\s+", " "),
        ]
        # Common publisher/venue mappings
        self.venue_mappings = {
            "arxiv preprint": "arXiv",
            "biorxiv": "bioRxiv",
            "medrxiv": "medRxiv",
        }

    async def process_papers(
        self, papers: list[GoogleScholarPaper]
    ) -> list[GoogleScholarPaper]:
        """
        Process a list of papers with cleaning, validation, and enhancement.
        Args:
            papers: List of raw GoogleScholarPaper objects
        Returns:
            List of processed and enhanced GoogleScholarPaper objects
        """
        logger.info(f"Processing {len(papers)} papers")
        # Step 1: Clean and validate
        cleaned_papers = self._clean_papers(papers)
        logger.info(f"After cleaning: {len(cleaned_papers)} papers")
        # Step 2: Remove duplicates
        deduplicated_papers = self._remove_duplicates(cleaned_papers)
        logger.info(f"After deduplication: {len(deduplicated_papers)} papers")
        # Step 3: Enhance with external data
        if self.config.resolve_dois or self.config.link_pubmed:
            enhanced_papers = await self._enhance_papers(deduplicated_papers)
            logger.info(f"After enhancement: {len(enhanced_papers)} papers")
        else:
            enhanced_papers = deduplicated_papers
        # Step 4: Final validation and scoring
        final_papers = self._final_validation(enhanced_papers)
        logger.info(f"Final result: {len(final_papers)} papers")
        return final_papers

    def _clean_papers(
        self, papers: list[GoogleScholarPaper]
    ) -> list[GoogleScholarPaper]:
        """Clean individual paper data."""
        cleaned_papers = []
        for paper in papers:
            try:
                cleaned_paper = self._clean_single_paper(paper)
                if (
                    cleaned_paper
                    and cleaned_paper.is_valid()
                    and self._passes_quality_checks(cleaned_paper)
                ):
                    cleaned_papers.append(cleaned_paper)
            except Exception as e:
                logger.warning(f"Error cleaning paper '{paper.title[:50]}...': {e}")
                continue
        return cleaned_papers

    def _clean_single_paper(self, paper: GoogleScholarPaper) -> GoogleScholarPaper:
        """Clean a single paper's data."""
        # Clean title
        title = self._clean_title(paper.title)
        # Clean authors
        authors = self._clean_authors(paper.authors)
        # Clean journal/venue
        journal = self._clean_venue(paper.journal) if paper.journal else None
        # Clean abstract
        abstract = self._clean_abstract(paper.abstract) if paper.abstract else None
        # Validate and clean year
        year = self._validate_year(paper.year)
        # Clean DOI
        doi = clean_doi(paper.doi) if paper.doi else None
        # Create cleaned paper
        cleaned_paper = GoogleScholarPaper(
            google_scholar_id=paper.google_scholar_id,
            title=title,
            authors=authors,
            journal=journal,
            conference=paper.conference,
            year=year,
            volume=paper.volume,
            issue=paper.issue,
            pages=paper.pages,
            publisher=paper.publisher,
            abstract=abstract,
            pdf_url=paper.pdf_url,
            doi=doi,
            pubmed_id=paper.pubmed_id,
            arxiv_id=self._extract_arxiv_id(paper),
            isbn=paper.isbn,
            citation_count=paper.citation_count,
            search_rank=paper.search_rank,
            confidence_score=paper.confidence_score,
            google_scholar_url=paper.google_scholar_url,
            source_url=paper.source_url,
            language=paper.language,
            search_query=paper.search_query,
            extracted_date=paper.extracted_date,
            publication_date=paper.publication_date,
            keywords=paper.keywords,
            abstract_snippet=paper.abstract_snippet,
            venue_type=paper.venue_type,
            open_access=paper.open_access,
        )
        # Update confidence score
        cleaned_paper.update_confidence_score()
        return cleaned_paper

    def _clean_title(self, title: str) -> str:
        """Clean paper title."""
        if not title:
            return ""
        # Apply cleaning patterns
        for pattern, replacement in self.title_patterns:
            title = re.sub(pattern, replacement, title)
        # Remove leading/trailing punctuation except periods
        title = re.sub(r'^[^\w"\']+|[^\w.!?"\')]+$', "", title)
        # Additional cleanup for trailing punctuation
        title = re.sub(r"[?!]+$", "", title)
        return title.strip()

    def _clean_authors(self, authors: list[str]) -> list[str]:
        """Clean author list."""
        if not authors:
            return []
        cleaned_authors = []
        for author in authors:
            # Clean individual author name
            author = re.sub(r"\s+", " ", author.strip())
            # Remove common prefixes/suffixes
            author = re.sub(r"^(Dr\.?|Prof\.?|Mr\.?|Ms\.?|Mrs\.?)\s+", "", author)
            author = re.sub(r"\s+(Jr\.?|Sr\.?|III|II|IV)$", "", author)
            # Validate author name (should have reasonable length and characters)
            if 2 <= len(author) <= 100 and re.match(r"^[a-zA-Z\s\.\-\']+$", author):
                cleaned_authors.append(author)
        return cleaned_authors[:20]  # Limit to reasonable number

    def _clean_venue(self, venue: str) -> str | None:
        """Clean venue/journal name."""
        if not venue:
            return None
        # Apply venue mappings
        venue_lower = venue.lower()
        for pattern, replacement in self.venue_mappings.items():
            if pattern in venue_lower:
                venue = replacement
                break
        # Clean common artifacts
        venue = re.sub(r"\s+", " ", venue.strip())
        venue = re.sub(r"^[^\w]+|[^\w]+$", "", venue)
        return venue if len(venue) >= 2 else None

    def _clean_abstract(self, abstract: str) -> str | None:
        """Clean abstract text."""
        if not abstract:
            return None
        # Remove common prefixes
        abstract = re.sub(
            r"^(Abstract:?|Summary:?)\s*", "", abstract, flags=re.IGNORECASE
        )
        # Normalize whitespace
        abstract = re.sub(r"\s+", " ", abstract.strip())
        # Validate length
        if 10 <= len(abstract) <= 5000:
            return abstract
        return None

    def _validate_year(self, year: int | None) -> int | None:
        """Validate publication year."""
        if not year:
            return None
        # Reasonable range for academic papers
        if 1800 <= year <= 2030:
            return year
        return None

    def _extract_arxiv_id(self, paper: GoogleScholarPaper) -> str | None:
        """Extract arXiv ID from various fields."""
        # Check PDF URL
        if paper.pdf_url and "arxiv.org" in paper.pdf_url:
            arxiv_match = re.search(r"(\d{4}\.\d{4,5})", paper.pdf_url)
            if arxiv_match:
                return arxiv_match.group(1)
        # Check journal field
        if paper.journal and "arxiv" in paper.journal.lower():
            arxiv_match = re.search(r"(\d{4}\.\d{4,5})", paper.journal)
            if arxiv_match:
                return arxiv_match.group(1)
        return None

    def _remove_duplicates(
        self, papers: list[GoogleScholarPaper]
    ) -> list[GoogleScholarPaper]:
        """Remove duplicate papers based on various criteria."""
        if not papers:
            return []
        unique_papers: list[GoogleScholarPaper] = []
        # _seen_titles: set[str] = set()  # Unused variable
        # _seen_dois: set[str] = set()  # Unused variable
        title_similarity_threshold = 0.9
        # Group by exact title matches first
        title_groups = defaultdict(list)
        for paper in papers:
            title_key = self._normalize_title_for_comparison(paper.title)
            title_groups[title_key].append(paper)
        for _title_key, group in title_groups.items():
            if len(group) == 1:
                unique_papers.append(group[0])
            else:
                # For duplicates, keep the best one
                best_paper = self._select_best_duplicate(group)
                unique_papers.append(best_paper)
        # Check for similar titles across different groups
        final_papers: list[GoogleScholarPaper] = []
        for paper in unique_papers:
            is_duplicate = False
            # Check against already selected papers
            for existing_paper in final_papers:
                if self._are_papers_similar(
                    paper, existing_paper, title_similarity_threshold
                ):
                    is_duplicate = True
                    break
            if not is_duplicate:
                final_papers.append(paper)
        return final_papers

    def _normalize_title_for_comparison(self, title: str) -> str:
        """Normalize title for duplicate detection."""
        if not title:
            return ""
        # Convert to lowercase and remove punctuation
        normalized = re.sub(r"[^\w\s]", "", title.lower())
        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _are_papers_similar(
        self, paper1: GoogleScholarPaper, paper2: GoogleScholarPaper, threshold: float
    ) -> bool:
        """Check if two papers are similar (likely duplicates)."""
        # Title similarity
        title1 = self._normalize_title_for_comparison(paper1.title)
        title2 = self._normalize_title_for_comparison(paper2.title)
        similarity = 0.0
        if title1 and title2:
            similarity = SequenceMatcher(None, title1, title2).ratio()
            if similarity >= threshold:
                return True
        # DOI match
        if paper1.doi and paper2.doi and paper1.doi == paper2.doi:
            return True
        # Author and year match with high title similarity
        if (
            paper1.authors
            and paper2.authors
            and paper1.year
            and paper2.year
            and paper1.year == paper2.year
        ):
            # Check if first authors match
            if (
                paper1.authors[0].lower() == paper2.authors[0].lower()
                and similarity >= 0.8
            ):
                return True
        return False

    def _select_best_duplicate(
        self, papers: list[GoogleScholarPaper]
    ) -> GoogleScholarPaper:
        """Select the best paper from a group of duplicates."""

        def score_paper(paper: GoogleScholarPaper) -> float:
            score = 0.0
            # Prefer papers with DOI
            if paper.doi:
                score += 2.0
            # Prefer papers with abstract
            if paper.abstract:
                score += 1.0
            # Prefer papers with more authors
            score += min(len(paper.authors) * 0.1, 1.0)
            # Prefer papers with journal info
            if paper.journal:
                score += 1.0
            # Prefer papers with higher citation count
            score += min(paper.citation_count * 0.01, 2.0)
            # Prefer papers with PDF
            if paper.pdf_url:
                score += 0.5
            # Use confidence score
            score += paper.confidence_score
            return score

        return max(papers, key=score_paper)

    async def _enhance_papers(
        self, papers: list[GoogleScholarPaper]
    ) -> list[GoogleScholarPaper]:
        """Enhance papers with external data sources."""
        enhanced_papers = []
        for paper in papers:
            try:
                enhanced_paper = await self._enhance_single_paper(paper)
                enhanced_papers.append(enhanced_paper)
            except Exception as e:
                logger.warning(f"Error enhancing paper '{paper.title[:50]}...': {e}")
                enhanced_papers.append(paper)  # Keep original if enhancement fails
        return enhanced_papers

    async def _enhance_single_paper(
        self, paper: GoogleScholarPaper
    ) -> GoogleScholarPaper:
        """Enhance a single paper with external data."""
        enhanced_paper = paper
        # Resolve DOI if not present
        if self.config.resolve_dois and not paper.doi and self.doi_downloader:
            doi = await self._resolve_doi(paper)
            if doi:
                enhanced_paper.doi = doi
        # Link to PubMed if requested
        if self.config.link_pubmed and not paper.pubmed_id:
            pubmed_id = await self._find_pubmed_id(enhanced_paper)
            if pubmed_id:
                enhanced_paper.pubmed_id = pubmed_id
        # Update confidence score after enhancement
        enhanced_paper.update_confidence_score()
        return enhanced_paper

    async def _resolve_doi(self, paper: GoogleScholarPaper) -> str | None:
        """Resolve DOI using CrossRef API."""
        try:
            # Use title and first author for search
            if not paper.title:
                return None
            # This would typically use CrossRef API
            # For now, return None as placeholder
            # TODO: Implement CrossRef integration
            return None
        except Exception as e:
            logger.debug(f"Error resolving DOI for '{paper.title[:50]}...': {e}")
            return None

    async def _find_pubmed_id(self, paper: GoogleScholarPaper) -> str | None:
        """Find PubMed ID using existing PubMed module."""
        try:
            if paper.doi:
                # Search by DOI
                query = f'"{paper.doi}"[DOI]'
                pmids = query_pmid(query, retmax=1)
                if pmids:
                    return pmids[0]
            if paper.title and paper.authors:
                # Search by title and first author
                first_author = paper.authors[0].split()[-1] if paper.authors else ""
                query = f'"{paper.title}"[Title] AND {first_author}[Author]'
                pmids = query_pmid(query, retmax=1)
                if pmids:
                    return pmids[0]
            return None
        except Exception as e:
            logger.debug(f"Error finding PubMed ID for '{paper.title[:50]}...': {e}")
            return None

    def _final_validation(
        self, papers: list[GoogleScholarPaper]
    ) -> list[GoogleScholarPaper]:
        """Perform final validation and filtering."""
        validated_papers = []
        for paper in papers:
            # Basic validation
            if not paper.is_valid():
                continue
            # Additional quality checks
            if not self._passes_quality_checks(paper):
                continue
            validated_papers.append(paper)
        return validated_papers

    def _passes_quality_checks(self, paper: GoogleScholarPaper) -> bool:
        """Check if paper passes quality thresholds."""
        # Minimum title length
        if len(paper.title) < 10:
            return False
        # Check for suspicious patterns
        title_lower = paper.title.lower()
        suspicious_patterns = ["untitled", "no title", "unknown", "[pdf]", "[citation]"]
        if any(pattern in title_lower for pattern in suspicious_patterns):
            return False
        # Check confidence score
        return not paper.confidence_score < 0.3
