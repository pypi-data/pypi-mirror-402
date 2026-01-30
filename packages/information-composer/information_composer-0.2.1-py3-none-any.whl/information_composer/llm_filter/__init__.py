"""
LLM Filter module for AI-powered markdown content filtering and extraction.
This module provides functionality for:
- LLM-based content filtering and extraction
- Markdown parsing and processing
- Integration with various LLM providers (DashScope, etc.)
- Configuration management for LLM services
"""

from typing import TYPE_CHECKING

from .core import ContentExtractor, MarkdownFilter, MarkdownParser
from .llm import LLMFactory, create_dashscope_client


if TYPE_CHECKING:
    from .cli.main import main as llm_filter_cli
    from .config.settings import LLMConfig
__all__ = [
    "ContentExtractor",
    # Configuration
    "LLMConfig",
    "LLMFactory",
    "MarkdownFilter",
    "MarkdownParser",
    "create_dashscope_client",
    # CLI
    "llm_filter_cli",
]
