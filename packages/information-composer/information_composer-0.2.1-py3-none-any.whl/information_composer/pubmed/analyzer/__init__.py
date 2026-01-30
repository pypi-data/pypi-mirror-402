"""
PubMed 文献智能分析模块
基于 LangChain 和 LLM 的文献分析功能，提供论文总结、领域判定等智能分析能力。
支持多种 LLM 提供商：DashScope (通义千问)、Ollama (本地模型)、OpenAI (GPT 系列)。
"""

from .analyzer import PaperAnalyzer
from .langchain_adapter import (
    create_langchain_dashscope,
    create_langchain_ollama,
    create_langchain_openai,
    create_llm,
)
from .models import (
    AnalysisConfig,
    AnalysisResult,
    DomainResult,
    PaperInput,
    ProcessingMetadata,
    SummaryResult,
)


__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "DomainResult",
    "PaperAnalyzer",
    "PaperInput",
    "ProcessingMetadata",
    "SummaryResult",
    "create_langchain_dashscope",
    "create_langchain_ollama",
    "create_langchain_openai",
    # LLM 适配器
    "create_llm",
]
