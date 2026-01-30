"""
论文分析器核心模块
基于 LangChain 和 LLM 的文献分析核心功能。
"""

import asyncio
from collections.abc import Callable, Sequence
import json
import logging
import time
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError

from .cache import AnalysisCache
from .langchain_adapter import create_llm
from .models import (
    AnalysisConfig,
    AnalysisResult,
    DomainResult,
    PaperInput,
    ProcessingMetadata,
    SummaryResult,
)
from .prompts import PromptManager


logger = logging.getLogger(__name__)


class PaperAnalyzer:
    """论文分析器"""

    def __init__(self, config: AnalysisConfig):
        """
        初始化论文分析器
        Args:
            config: 分析配置
        """
        self.config = config
        self.prompt_manager = PromptManager()
        # 初始化 LLM
        llm_kwargs: dict[str, Any] = {
            "temperature": config.temperature,
        }
        # 根据不同的 provider 添加相应参数
        if config.llm_provider == "dashscope":
            if config.llm_api_key:
                llm_kwargs["api_key"] = config.llm_api_key
            llm_kwargs["max_tokens"] = 4096
        elif config.llm_provider == "ollama":
            if config.llm_base_url:
                llm_kwargs["base_url"] = config.llm_base_url
        elif config.llm_provider == "openai":
            if config.llm_api_key:
                llm_kwargs["api_key"] = config.llm_api_key
            if config.llm_base_url:
                llm_kwargs["base_url"] = config.llm_base_url
        self.llm = create_llm(
            provider=config.llm_provider,  # type: ignore
            model=config.llm_model,
            **llm_kwargs,
        )
        # 初始化缓存
        self.cache = AnalysisCache(enabled=config.cache_enabled)
        # 初始化并发控制
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        logger.info(
            f"PaperAnalyzer 初始化完成，提供商: {config.llm_provider}, "
            f"模型: {config.llm_model}, 分析类型: {config.analysis_types}"
        )

    async def analyze_paper(self, paper: PaperInput | dict[str, Any]) -> AnalysisResult:
        """
        分析单篇文献
        Args:
            paper: 文献输入数据
        Returns:
            分析结果
        Raises:
            ValueError: 输入数据不完整
            Exception: 分析失败
        """
        # 转换输入数据
        if isinstance(paper, dict):
            paper_input = PaperInput(**paper)
        else:
            paper_input = paper
        logger.info(f"开始分析论文: PMID={paper_input.pmid}, Title={paper_input.title}")
        # 检查缓存
        cache_config = {
            "analysis_types": self.config.analysis_types,
            "domain_list": self.config.domain_list,
            "llm_model": self.config.llm_model,
        }
        cached_result = self.cache.get(paper_input.pmid, cache_config)
        if cached_result:
            logger.info(f"使用缓存结果: PMID={paper_input.pmid}")
            return AnalysisResult(**cached_result)
        # 开始计时
        start_time = time.time()
        # 执行分析任务
        summary_result = None
        domain_result = None
        confidence_scores: dict[str, float] = {}
        total_tokens = 0
        try:
            # 并行执行分析任务
            tasks = []
            if "summary" in self.config.analysis_types:
                tasks.append(self._analyze_summary(paper_input))
            if "domain" in self.config.analysis_types:
                tasks.append(self._analyze_domain(paper_input))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 处理结果
            task_idx = 0
            if "summary" in self.config.analysis_types:
                if isinstance(results[task_idx], Exception):
                    logger.error(f"论文总结分析失败: {results[task_idx]}")
                else:
                    result_tuple = results[task_idx]
                    if isinstance(result_tuple, tuple):
                        summary_result, tokens = result_tuple
                        total_tokens += tokens
                        confidence_scores["summary"] = 0.8  # 简化版本使用固定置信度
                task_idx += 1
            if "domain" in self.config.analysis_types:
                if isinstance(results[task_idx], Exception):
                    logger.error(f"领域判定分析失败: {results[task_idx]}")
                else:
                    result_tuple = results[task_idx]
                    if isinstance(result_tuple, tuple):
                        domain_result, tokens = result_tuple
                        total_tokens += tokens
                        confidence_scores["domain"] = 0.85  # 简化版本使用固定置信度
                task_idx += 1
            # 计算处理时间
            processing_time = time.time() - start_time
            # 构建元数据
            metadata = ProcessingMetadata(
                llm_model=self.config.llm_model,
                processing_time=processing_time,
                tokens_used=total_tokens if total_tokens > 0 else None,
                cache_hit=False,
            )
            # 构建分析结果
            result = AnalysisResult(
                pmid=paper_input.pmid,
                title=paper_input.title,
                summary=summary_result,
                domain_analysis=domain_result,
                confidence_scores=confidence_scores,
                processing_metadata=metadata,
            )
            # 保存到缓存
            self.cache.set(paper_input.pmid, cache_config, result.model_dump())
            logger.info(
                f"分析完成: PMID={paper_input.pmid}, "
                f"耗时={processing_time:.2f}s, tokens={total_tokens}"
            )
            return result
        except Exception as e:
            logger.error(f"分析失败: PMID={paper_input.pmid}, 错误: {e}")
            raise

    async def _analyze_summary(self, paper: PaperInput) -> tuple[SummaryResult, int]:
        """
        执行论文总结分析
        Args:
            paper: 文献输入
        Returns:
            总结结果和消耗的 token 数
        """
        async with self.semaphore:
            try:
                # 构建提示词
                prompt_template = self.prompt_manager.get_summary_prompt()
                prompt_vars = self.prompt_manager.format_summary_prompt(
                    paper.title, paper.abstract
                )
                # 创建输出解析器
                parser = JsonOutputParser()
                # 构建处理链
                chain = prompt_template | self.llm | parser
                # 执行分析
                logger.debug(f"执行论文总结分析: PMID={paper.pmid}")
                result = await chain.ainvoke(prompt_vars)
                # 验证并构建结果
                summary = SummaryResult(**result)
                # 提取 token 使用信息（简化版本）
                tokens = 0  # TODO: 从 LLM 响应中提取实际 token 数
                return summary, tokens
            except ValidationError as e:
                logger.error(f"论文总结结果验证失败: {e}")
                raise
            except Exception as e:
                logger.error(f"论文总结分析失败: {e}")
                raise

    async def _analyze_domain(self, paper: PaperInput) -> tuple[DomainResult, int]:
        """
        执行领域判定分析
        Args:
            paper: 文献输入
        Returns:
            领域判定结果和消耗的 token 数
        """
        if not self.config.domain_list:
            raise ValueError("domain_list 不能为空")
        async with self.semaphore:
            try:
                # 构建提示词
                prompt_template = self.prompt_manager.get_domain_prompt()
                prompt_vars = self.prompt_manager.format_domain_prompt(
                    paper.title, paper.abstract, self.config.domain_list
                )
                # 创建输出解析器
                parser = JsonOutputParser()
                # 构建处理链
                chain = prompt_template | self.llm | parser
                # 执行分析
                logger.debug(f"执行领域判定分析: PMID={paper.pmid}")
                result = await chain.ainvoke(prompt_vars)
                # 验证并构建结果
                domain = DomainResult(**result)
                # 提取 token 使用信息（简化版本）
                tokens = 0  # TODO: 从 LLM 响应中提取实际 token 数
                return domain, tokens
            except ValidationError as e:
                logger.error(f"领域判定结果验证失败: {e}")
                raise
            except Exception as e:
                logger.error(f"领域判定分析失败: {e}")
                raise

    async def analyze_batch(
        self,
        papers: Sequence[PaperInput | dict[str, Any]],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[AnalysisResult]:
        """
        批量分析文献
        Args:
            papers: 文献列表
            progress_callback: 进度回调函数，接收 (当前进度, 总数) 参数
        Returns:
            分析结果列表
        """
        logger.info(f"开始批量分析: 总数={len(papers)}")
        results: list[AnalysisResult] = []
        errors: list[tuple[int, Exception]] = []
        # 分批处理
        batch_size = self.config.batch_size
        total_batches = (len(papers) + batch_size - 1) // batch_size
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(papers))
            batch = papers[start_idx:end_idx]
            logger.info(
                f"处理批次 {batch_idx + 1}/{total_batches}, "
                f"论文 {start_idx + 1}-{end_idx}/{len(papers)}"
            )
            # 并行处理当前批次
            tasks = [self.analyze_paper(paper) for paper in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            # 收集结果和错误
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    paper_idx = start_idx + i
                    errors.append((paper_idx, result))
                    logger.error(f"论文 {paper_idx + 1} 分析失败: {result}")
                elif isinstance(result, AnalysisResult):
                    results.append(result)
                # 调用进度回调
                if progress_callback:
                    progress_callback(len(results) + len(errors), len(papers))
        # 输出统计信息
        logger.info(
            f"批量分析完成: 成功={len(results)}, 失败={len(errors)}, 总数={len(papers)}"
        )
        if errors:
            logger.warning("以下论文分析失败:")
            for idx, error in errors:
                logger.warning(f"  索引 {idx}: {error}")
        return results

    def export_results(
        self,
        results: list[AnalysisResult],
        output_file: str,
        format: str = "json",
    ) -> str:
        """
        导出分析结果
        Args:
            results: 分析结果列表
            output_file: 输出文件路径
            format: 输出格式 (json)
        Returns:
            导出文件路径
        """
        logger.info(f"导出分析结果: {len(results)} 条记录到 {output_file}")
        if format == "json":
            # 转换为字典列表
            results_dict = [result.model_dump() for result in results]
            # 写入 JSON 文件
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"结果已导出到: {output_file}")
            return output_file
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息
        Returns:
            缓存统计信息
        """
        return self.cache.get_cache_stats()
