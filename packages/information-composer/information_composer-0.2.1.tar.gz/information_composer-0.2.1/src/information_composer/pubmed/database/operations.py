"""
PubMed database operations.

This module provides the PubMedDatabase class for database operations.
"""

from datetime import datetime
import json
import os
from typing import Any

from pony.orm import db_session

from .models import ArticleStatus, PubMedArticle, db


class PubMedDatabase:
    """
    PubMed database management class.

    Encapsulates Pony ORM operations with high-level business interfaces:
    - Database initialization and connection management
    - CRUD operations
    - Batch operations
    - Data conversion and validation
    - Database maintenance
    """

    def __init__(self, db_path: str | None = None):
        """
        Initialize database connection.

        Args:
            db_path: Database file path, defaults to "data/pubmed/pubmed.db"
        """
        if db_path is None:
            db_path = "data/pubmed/pubmed.db"
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        if db.provider is None:
            db.bind(provider="sqlite", filename=db_path, create_db=True)
            db.generate_mapping(create_tables=True)
        else:
            db.disconnect()
            db.provider = None
            db.schema = None
            db.bind(provider="sqlite", filename=db_path, create_db=True)
            db.generate_mapping(create_tables=True)

    def close(self) -> None:
        """Close database connection."""
        db.disconnect()

    @db_session
    def save_article(self, article: dict[str, Any]) -> None:
        """
        Save a single article to the database.

        Args:
            article: Article info dictionary (processed_record format)
        Raises:
            ValueError: Missing required fields
            RuntimeError: Database operation failed
        """
        if "pmid" not in article or "title" not in article:
            raise ValueError("Missing required fields: pmid and title")
        pmid = article["pmid"]
        existing = PubMedArticle.get(pmid=pmid)
        entity_data = self._prepare_entity_data(article)
        if existing:
            existing.set(**entity_data)
        else:
            PubMedArticle(**entity_data)

    @db_session
    def save_articles_batch(self, articles: list[dict[str, Any]]) -> int:
        """
        Batch save articles.

        Args:
            articles: List of article info dictionaries
        Returns:
            Number of successfully saved records
        """
        count = 0
        for article in articles:
            pmid = article.get("pmid")
            if not pmid:
                continue
            existing = PubMedArticle.get(pmid=pmid)
            entity_data = self._prepare_entity_data(article)
            if existing:
                existing.set(**entity_data)
            else:
                PubMedArticle(**entity_data)
            count += 1
        return count

    @db_session
    def get_article(self, pmid: str) -> dict[str, Any] | None:
        """
        Get a single article by PMID.

        Args:
            pmid: PubMed ID
        Returns:
            Article info dictionary or None
        """
        article = PubMedArticle.get(pmid=pmid)
        if not article:
            return None
        return self._entity_to_dict(article)

    @db_session
    def get_articles_batch(self, pmids: list[str]) -> dict[str, dict[str, Any]]:
        """
        Batch get multiple articles.

        Args:
            pmids: List of PMIDs
        Returns:
            Dictionary with PMID as key and article info as value
        """
        articles = []
        for pmid in pmids:
            article = PubMedArticle.get(pmid=pmid)
            if article:
                articles.append(article)
        return {a.pmid: self._entity_to_dict(a) for a in articles}

    @db_session
    def check_exists(self, pmid: str) -> bool:
        """
        Check if a PMID exists.

        Args:
            pmid: PubMed ID
        Returns:
            True if exists, False otherwise
        """
        return PubMedArticle.exists(pmid=pmid)

    @db_session
    def get_missing_pmids(self, pmids: list[str]) -> list[str]:
        """
        Get PMIDs that don't exist in the database.

        Args:
            pmids: List of PMIDs to check
        Returns:
            List of PMIDs not in database
        """
        existing = set()
        for pmid in pmids:
            article = PubMedArticle.get(pmid=pmid)
            if article:
                existing.add(pmid)
        return [pmid for pmid in pmids if pmid not in existing]

    @db_session
    def get_articles_by_status(
        self, status: ArticleStatus, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get articles by status.

        Args:
            status: Article status
            limit: Maximum number of results
        Returns:
            List of articles
        """
        query = PubMedArticle.select().filter(status=status.value)
        if limit:
            query = query.limit(limit)
        entities = list(query)
        return [self._entity_to_dict(entity) for entity in entities]

    @db_session
    def get_filtered_articles(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Get filtered relevant articles (pending translation).

        Args:
            limit: Maximum number of results
        Returns:
            List of relevant articles
        """
        query = PubMedArticle.select().filter(
            status=ArticleStatus.FILTERED.value, is_relevant=True
        )
        if limit:
            query = query.limit(limit)
        entities = list(query)
        return [self._entity_to_dict(e) for e in entities]

    @db_session
    def get_translated_unsent_articles(
        self, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get translated but unsent relevant articles.

        Args:
            limit: Maximum number of results
        Returns:
            List of articles
        """
        query = PubMedArticle.select().filter(
            status=ArticleStatus.TRANSLATED.value,
            is_relevant=True,
            is_email_sent=False,
        )
        if limit:
            query = query.limit(limit)
        entities = list(query)
        return [self._entity_to_dict(e) for e in entities]

    @db_session
    def update_article_translation(self, pmid: str, translated_abstract: str) -> None:
        """
        Update article translation.

        Args:
            pmid: PubMed ID
            translated_abstract: Translated abstract
        """
        article = PubMedArticle.get(pmid=pmid)
        if article:
            article.abstract_zh = translated_abstract
            article.translation_timestamp = datetime.now()
            article.status = ArticleStatus.TRANSLATED.value
            article.updated_at = datetime.now()

    @db_session
    def update_article_filtering(
        self,
        pmid: str,
        relevance_score: float,
        is_relevant: bool,
        reasoning: str,
        matched_domains: list[str],
    ) -> None:
        """
        Update article filtering result.

        Args:
            pmid: PubMed ID
            relevance_score: Relevance score
            is_relevant: Whether relevant
            reasoning: Evaluation reasoning
            matched_domains: Matched domains
        """
        article = PubMedArticle.get(pmid=pmid)
        if article:
            article.is_evaluated = True
            article.relevance_score = relevance_score
            article.is_relevant = is_relevant
            article.relevance_reasoning = reasoning
            article.matched_domains = json.dumps(matched_domains, ensure_ascii=False)
            article.status = ArticleStatus.FILTERED.value
            article.updated_at = datetime.now()

    @db_session
    def mark_article_sent(self, pmid: str) -> None:
        """
        Mark article as sent.

        Args:
            pmid: PubMed ID
        """
        article = PubMedArticle.get(pmid=pmid)
        if article:
            article.email_sent_timestamp = datetime.now()
            article.is_email_sent = True
            article.status = ArticleStatus.SENT.value
            article.updated_at = datetime.now()

    @db_session
    def update_article_novelty(self, pmid: str, novelty: str, novelty_zh: str) -> None:
        """
        Update article novelty.

        Args:
            pmid: PubMed ID
            novelty: English novelty description
            novelty_zh: Chinese novelty description
        """
        article = PubMedArticle.get(pmid=pmid)
        if article:
            article.novelty = novelty
            article.novelty_zh = novelty_zh
            article.updated_at = datetime.now()

    @db_session
    def get_articles_for_novelty_extraction(
        self, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get translated articles pending novelty extraction.

        Args:
            limit: Maximum number of results
        Returns:
            List of articles
        """
        all_entities = list(PubMedArticle.select())
        entities = [
            e
            for e in all_entities
            if e.abstract_zh is not None
            and e.abstract_zh.strip() != ""
            and e.is_relevant is True
            and (
                not e.novelty
                or e.novelty.strip() == ""
                or not e.novelty_zh
                or e.novelty_zh.strip() == ""
            )
        ]
        if limit and len(entities) > limit:
            entities = entities[:limit]
        return [self._entity_to_dict(e) for e in entities]

    @db_session
    def delete_article(self, pmid: str) -> bool:
        """
        Delete an article by PMID.

        Args:
            pmid: PubMed ID
        Returns:
            True if deleted, False if not found
        """
        article = PubMedArticle.get(pmid=pmid)
        if article:
            article.delete()
            return True
        return False

    @db_session
    def get_statistics(self) -> dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with total records, earliest/latest times, size
        """
        total = PubMedArticle.select().count()
        stats = {
            "total_records": total,
            "database_size": self._get_db_file_size(),
        }
        if total > 0:
            earliest_article = (
                PubMedArticle.select().order_by(PubMedArticle.created_at).first()
            )
            latest_article = (
                PubMedArticle.select().order_by(PubMedArticle.created_at.desc()).first()
            )
            if earliest_article:
                stats["earliest_record"] = earliest_article.created_at
            if latest_article:
                stats["latest_record"] = latest_article.created_at
        return stats

    def vacuum(self) -> None:
        """Optimize database and reclaim space."""
        db.execute("VACUUM")

    @db_session
    def get_articles_batch_by_status(
        self, status: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get articles by status (CLI compatible method).

        Args:
            status: Article status (new, filtered, translated, sent, failed)
            limit: Maximum number of results
        Returns:
            List of articles
        """
        if status:
            article_status = ArticleStatus(status)
            return self.get_articles_by_status(article_status, limit)
        return self.get_all_articles(limit=limit)

    @db_session
    def search_articles(self, keyword: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Fuzzy search articles (title, abstract, journal).

        Args:
            keyword: Search keyword
            limit: Maximum number of results
        Returns:
            List of matching articles
        """
        keyword_lower = keyword.lower()
        all_entities = list(PubMedArticle.select())
        matched = [
            self._entity_to_dict(e)
            for e in all_entities
            if keyword_lower in (e.title or "").lower()
            or keyword_lower in (e.abstract or "").lower()
            or keyword_lower in (e.journal or "").lower()
        ]
        return matched[:limit]

    @db_session
    def get_all_articles(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Get all articles.

        Args:
            limit: Maximum number of results (None for all)
        Returns:
            List of all articles
        """
        all_entities = list(PubMedArticle.select())
        if limit:
            all_entities = all_entities[:limit]
        return [self._entity_to_dict(e) for e in all_entities]

    @db_session
    def delete_old_articles(self, days: int = 30) -> int:
        """
        Delete articles older than specified days.

        Args:
            days: Number of days to keep
        Returns:
            Number of deleted articles
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        all_entities = list(PubMedArticle.select())
        old_articles = [
            e for e in all_entities if e.created_at and e.created_at < cutoff_date
        ]
        count = len(old_articles)
        for article in old_articles:
            article.delete()
        return count

    def _prepare_entity_data(self, article: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare entity data for insertion/update.

        Args:
            article: processed_record format article data
        Returns:
            Data dictionary for Pony ORM entity
        """
        now = datetime.now()
        list_fields = [
            "publication_types",
            "authors",
            "authors_full",
            "affiliations",
            "article_id",
            "mesh_terms",
            "mesh_qualifiers",
            "keywords",
            "chemicals",
            "chemical_names",
            "grants",
            "grant_agencies",
            "comments_corrections",
            "article_type",
            "citation_subset",
            "matched_domains",
        ]
        entity_data = {
            "pmid": article["pmid"],
            "title": article.get("title", "N/A"),
            "updated_at": now,
        }
        if not PubMedArticle.exists(pmid=article["pmid"]):
            entity_data["created_at"] = now
        text_fields = [
            "abstract",
            "abstract_zh",
            "journal",
            "journal_abbreviation",
            "journal_iso",
            "volume",
            "issue",
            "pagination",
            "pubdate",
            "create_date",
            "complete_date",
            "revision_date",
            "publication_status",
            "language",
            "doi",
            "pmcid",
            "publication_country",
            "pdf_path",
            "pdf_local_path",
            "pubmed_query",
            "note",
            "novelty",
            "novelty_zh",
            "relevance_reasoning",
        ]
        for field in text_fields:
            if field in article and article[field] is not None:
                entity_data[field] = str(article[field])
        for field in list_fields:
            if field in article and article[field] is not None:
                if isinstance(article[field], list):
                    entity_data[field] = json.dumps(article[field], ensure_ascii=False)
                else:
                    entity_data[field] = article[field]
        if "is_evaluated" in article:
            entity_data["is_evaluated"] = bool(article["is_evaluated"])
        if "relevance_score" in article and article["relevance_score"] is not None:
            entity_data["relevance_score"] = float(article["relevance_score"])
        if "is_relevant" in article and article["is_relevant"] is not None:
            entity_data["is_relevant"] = bool(article["is_relevant"])
        if "is_email_sent" in article:
            entity_data["is_email_sent"] = bool(article["is_email_sent"])
        if "retrieval_timestamp" in article:
            ts = article["retrieval_timestamp"]
            if isinstance(ts, str):
                entity_data["retrieval_timestamp"] = datetime.fromisoformat(ts)
            elif isinstance(ts, datetime):
                entity_data["retrieval_timestamp"] = ts
        else:
            if not PubMedArticle.exists(pmid=article["pmid"]):
                entity_data["retrieval_timestamp"] = now
        if article.get("translation_timestamp"):
            ts = article["translation_timestamp"]
            if isinstance(ts, str):
                entity_data["translation_timestamp"] = datetime.fromisoformat(ts)
            elif isinstance(ts, datetime):
                entity_data["translation_timestamp"] = ts
        if article.get("email_sent_timestamp"):
            ts = article["email_sent_timestamp"]
            if isinstance(ts, str):
                entity_data["email_sent_timestamp"] = datetime.fromisoformat(ts)
            elif isinstance(ts, datetime):
                entity_data["email_sent_timestamp"] = ts
        entity_data["raw_data"] = json.dumps(article, ensure_ascii=False)
        return entity_data

    def _entity_to_dict(self, entity: PubMedArticle) -> dict[str, Any]:
        """
        Convert entity to dictionary.

        Args:
            entity: PubMedArticle entity instance
        Returns:
            Article info dictionary
        """
        result = {
            "pmid": entity.pmid,
            "title": entity.title,
            "abstract": entity.abstract,
            "abstract_zh": entity.abstract_zh,
            "journal": entity.journal,
            "journal_abbreviation": entity.journal_abbreviation,
            "journal_iso": entity.journal_iso,
            "volume": entity.volume,
            "issue": entity.issue,
            "pagination": entity.pagination,
            "pubdate": entity.pubdate,
            "create_date": entity.create_date,
            "complete_date": entity.complete_date,
            "revision_date": entity.revision_date,
            "publication_status": entity.publication_status,
            "language": entity.language,
            "doi": entity.doi,
            "pmcid": entity.pmcid,
            "publication_country": entity.publication_country,
            "pdf_path": entity.pdf_path,
            "pdf_local_path": entity.pdf_local_path,
            "pubmed_query": entity.pubmed_query,
            "note": entity.note,
            "raw_data": entity.raw_data,
            "is_evaluated": entity.is_evaluated,
            "relevance_score": entity.relevance_score,
            "is_relevant": entity.is_relevant,
            "relevance_reasoning": entity.relevance_reasoning,
            "novelty": entity.novelty,
            "novelty_zh": entity.novelty_zh,
            "is_email_sent": entity.is_email_sent,
            "status": entity.status,
            "retrieval_timestamp": entity.retrieval_timestamp,
            "translation_timestamp": entity.translation_timestamp,
            "email_sent_timestamp": entity.email_sent_timestamp,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }
        list_fields = {
            "publication_types": entity.publication_types,
            "authors": entity.authors,
            "authors_full": entity.authors_full,
            "affiliations": entity.affiliations,
            "article_id": entity.article_id,
            "mesh_terms": entity.mesh_terms,
            "mesh_qualifiers": entity.mesh_qualifiers,
            "keywords": entity.keywords,
            "chemicals": entity.chemicals,
            "chemical_names": entity.chemical_names,
            "grants": entity.grants,
            "grant_agencies": entity.grant_agencies,
            "comments_corrections": entity.comments_corrections,
            "article_type": entity.article_type,
            "citation_subset": entity.citation_subset,
            "matched_domains": entity.matched_domains,
        }
        for field, value in list_fields.items():
            if value:
                try:
                    result[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field] = []
            else:
                result[field] = []
        return result

    def _get_db_file_size(self) -> int:
        """
        Get database file size in bytes.

        Returns:
            File size or 0 if file doesn't exist
        """
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path)
        return 0


__all__ = [
    "PubMedDatabase",
]
