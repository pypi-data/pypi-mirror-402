"""
数据模型定义
定义了文献分析的输入输出数据结构。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SummaryResult(BaseModel):
    """论文总结结果"""

    main_findings: list[str] = Field(
        description="主要研究发现（1-5项）", min_length=1, max_length=5
    )
    innovations: list[str] = Field(description="创新点（1-3项）", max_length=3)
    conclusions: str = Field(description="核心结论")
    limitations: list[str] | None = Field(
        default=None, description="研究局限性（可选）"
    )

    @field_validator("main_findings", "innovations")
    @classmethod
    def validate_not_empty_strings(cls, v: list[str]) -> list[str]:
        """验证列表项不为空字符串"""
        if not v:
            raise ValueError("列表不能为空")
        for item in v:
            if not item.strip():
                raise ValueError("列表项不能为空字符串")
        return v

    @field_validator("conclusions")
    @classmethod
    def validate_conclusion(cls, v: str) -> str:
        """验证结论不为空"""
        if not v.strip():
            raise ValueError("结论不能为空")
        return v


class DomainResult(BaseModel):
    """领域判定结果"""

    relevant_domains: list[str] = Field(description="相关领域列表")
    domain_scores: dict[str, float] = Field(description="各领域相关性评分（0-1）")
    primary_domain: str = Field(description="主要研究领域")
    reasoning: str = Field(description="判定依据说明")

    @field_validator("domain_scores")
    @classmethod
    def validate_scores(cls, v: dict[str, float]) -> dict[str, float]:
        """验证评分在0-1范围内"""
        for domain, score in v.items():
            if not 0 <= score <= 1:
                raise ValueError(f"领域 {domain} 的评分 {score} 必须在 0-1 范围内")
        return v

    @field_validator("primary_domain")
    @classmethod
    def validate_primary_domain(cls, v: str, info: Any) -> str:
        """验证主要领域在相关领域列表中"""
        # 在 Pydantic v2 中，使用 info.data 访问其他字段的值
        if hasattr(info, "data") and "relevant_domains" in info.data:
            relevant_domains = info.data["relevant_domains"]
            if v not in relevant_domains:
                raise ValueError(f"主要领域 {v} 必须在相关领域列表中")
        return v


class ProcessingMetadata(BaseModel):
    """处理元数据"""

    llm_model: str = Field(description="使用的 LLM 模型")
    processing_time: float = Field(description="处理耗时（秒）")
    tokens_used: int | None = Field(default=None, description="消耗的 token 数量")
    cache_hit: bool = Field(default=False, description="是否命中缓存")


class AnalysisResult(BaseModel):
    """分析结果输出"""

    pmid: str = Field(description="PubMed 文献标识")
    title: str = Field(description="文献标题")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="分析时间戳"
    )
    summary: SummaryResult | None = Field(default=None, description="论文总结结果")
    domain_analysis: DomainResult | None = Field(
        default=None, description="领域判定结果"
    )
    confidence_scores: dict[str, float] = Field(
        default_factory=dict, description="各分析项的置信度评分"
    )
    processing_metadata: ProcessingMetadata = Field(description="处理元数据")


class AnalysisConfig(BaseModel):
    """分析配置"""

    analysis_types: list[str] = Field(
        description="分析类型列表（summary, domain）", min_length=1
    )
    domain_list: list[str] | None = Field(
        default=None, description="目标领域列表，当包含 domain 分析时必填"
    )
    llm_provider: str = Field(
        default="dashscope", description="LLM 提供商（dashscope, ollama, openai）"
    )
    llm_model: str = Field(default="qwen-plus-latest", description="LLM 模型名称")
    llm_api_key: str | None = Field(
        default=None, description="LLM API 密钥（dashscope 和 openai 需要）"
    )
    llm_base_url: str | None = Field(
        default=None,
        description="LLM 服务地址（ollama 需要，默认 http://localhost:11434）",
    )
    batch_size: int = Field(default=10, description="批处理大小")
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    max_concurrent: int = Field(default=3, description="最大并发请求数")
    temperature: float = Field(default=0.1, description="LLM 温度参数")

    @field_validator("analysis_types")
    @classmethod
    def validate_analysis_types(cls, v: list[str]) -> list[str]:
        """验证分析类型"""
        valid_types = {"summary", "domain"}
        for analysis_type in v:
            if analysis_type not in valid_types:
                raise ValueError(
                    f"不支持的分析类型: {analysis_type}，支持的类型: {valid_types}"
                )
        return v

    @field_validator("domain_list")
    @classmethod
    def validate_domain_list(cls, v: list[str] | None, info: Any) -> list[str] | None:
        """验证领域列表配置"""
        if hasattr(info, "data") and "analysis_types" in info.data:
            analysis_types = info.data["analysis_types"]
            if "domain" in analysis_types and not v:
                raise ValueError("包含 domain 分析时必须提供 domain_list")
        return v

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """验证 LLM 提供商"""
        valid_providers = {"dashscope", "ollama", "openai"}
        if v not in valid_providers:
            raise ValueError(
                f"不支持的 LLM 提供商: {v}，支持的提供商: {valid_providers}"
            )
        return v


class PaperInput(BaseModel):
    """文献分析输入"""

    pmid: str = Field(description="PubMed 文献唯一标识")
    title: str = Field(description="文献标题")
    abstract: str = Field(description="文献摘要")
    authors: list[str] | None = Field(default=None, description="作者列表")
    journal: str | None = Field(default=None, description="期刊名称")
    pubdate: str | None = Field(default=None, description="发表日期")
    keywords: list[str] | None = Field(default=None, description="关键词列表")
    mesh_terms: list[str] | None = Field(default=None, description="MeSH 主题词")
