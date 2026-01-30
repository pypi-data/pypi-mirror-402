"""
PubMed database models.

This module defines the Pony ORM entities and database models for PubMed articles.
"""

from datetime import datetime
from enum import Enum

from pony.orm import Database, PrimaryKey, Required
from pony.orm import Optional as PonyOptional


class ArticleStatus(Enum):
    """Article processing status enum.

    Defines the various states of articles in the processing workflow.
    State transitions:
        NEW → FILTERED → TRANSLATED → SENT
                    ↓
                  FAILED
    Attributes:
        NEW: Newly retrieved articles, not yet filtered for relevance
        FILTERED: Filtered articles, pending translation
        TRANSLATED: Translated articles, pending email
        SENT: Articles that have been emailed
        FAILED: Articles that failed processing
    """

    NEW = "new"
    FILTERED = "filtered"
    TRANSLATED = "translated"
    SENT = "sent"
    FAILED = "failed"


db = Database()


class PubMedArticle(db.Entity):
    """
    PubMed article entity model.

    Uses Pony ORM declarative definition with 56 fields:
    - 35 processed_record standard fields (PubMed basic info)
    - 17 extended fields (abstract_zh, pdf_path, etc.)
    - 4 database management fields (retrieval_timestamp, raw_data, created_at, updated_at)
    """

    pmid = PrimaryKey(str)
    title = Required(str)
    abstract = PonyOptional(str)
    abstract_zh = PonyOptional(str)
    journal = PonyOptional(str, index=True)
    journal_abbreviation = PonyOptional(str)
    journal_iso = PonyOptional(str)
    volume = PonyOptional(str)
    issue = PonyOptional(str)
    pagination = PonyOptional(str)
    pubdate = PonyOptional(str, index=True)
    create_date = PonyOptional(str)
    complete_date = PonyOptional(str)
    revision_date = PonyOptional(str)
    publication_types = PonyOptional(str)
    publication_status = PonyOptional(str)
    language = PonyOptional(str)
    authors = PonyOptional(str)
    authors_full = PonyOptional(str)
    affiliations = PonyOptional(str)
    doi = PonyOptional(str, index=True)
    pmcid = PonyOptional(str)
    article_id = PonyOptional(str)
    mesh_terms = PonyOptional(str)
    mesh_qualifiers = PonyOptional(str)
    keywords = PonyOptional(str)
    chemicals = PonyOptional(str)
    chemical_names = PonyOptional(str)
    grants = PonyOptional(str)
    grant_agencies = PonyOptional(str)
    comments_corrections = PonyOptional(str)
    publication_country = PonyOptional(str)
    article_type = PonyOptional(str)
    citation_subset = PonyOptional(str)
    pdf_path = PonyOptional(str)
    pdf_local_path = PonyOptional(str)
    pubmed_query = PonyOptional(str)
    note = PonyOptional(str)
    is_evaluated = PonyOptional(bool, default=False)
    relevance_score = PonyOptional(float)
    is_relevant = PonyOptional(bool)
    relevance_reasoning = PonyOptional(str)
    matched_domains = PonyOptional(str)
    translation_timestamp = PonyOptional(datetime)
    novelty = PonyOptional(str)
    novelty_zh = PonyOptional(str)
    email_sent_timestamp = PonyOptional(datetime)
    is_email_sent = PonyOptional(bool, default=False)
    status = PonyOptional(str, default="new")
    retrieval_timestamp = Required(datetime, default=datetime.now)
    raw_data = PonyOptional(str)
    created_at = Required(datetime, index=True)
    updated_at = Required(datetime)


__all__ = [
    "ArticleStatus",
    "PubMedArticle",
    "db",
]
