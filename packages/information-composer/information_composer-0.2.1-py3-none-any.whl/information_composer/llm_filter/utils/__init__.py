"""
工具模块
提供Markdown处理和文本分析的实用工具函数。
"""

from .markdown_utils import (
    clean_markdown,
    count_characters,
    count_words,
    extract_code_blocks,
    extract_headings,
    extract_images,
    extract_links,
    extract_tables,
    format_markdown,
    validate_markdown,
)
from .markdown_utils import (
    get_document_stats as get_markdown_stats,
)
from .text_processing import (
    calculate_readability_score,
    calculate_text_similarity,
    clean_text,
    count_syllables,
    extract_entities,
    extract_keywords,
    extract_ngrams,
    extract_paragraphs,
    extract_sentences,
    get_document_stats,
    remove_stopwords,
    summarize_text,
)


__all__ = [
    "calculate_readability_score",
    "calculate_text_similarity",
    "clean_markdown",
    "clean_text",
    "count_characters",
    "count_syllables",
    "count_words",
    "extract_code_blocks",
    "extract_entities",
    "extract_headings",
    "extract_images",
    "extract_keywords",
    "extract_links",
    "extract_ngrams",
    "extract_paragraphs",
    "extract_sentences",
    "extract_tables",
    "format_markdown",
    "get_document_stats",
    "get_markdown_stats",
    "remove_stopwords",
    "summarize_text",
    "validate_markdown",
]
