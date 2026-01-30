"""
PubMed 论文分析器 - Ollama 使用示例

演示如何使用 Ollama 本地模型进行论文分析。
支持的模型：qwen2.5, llama3.2, mistral 等
"""

import asyncio
from collections.abc import Sequence
import logging
from pathlib import Path

from information_composer.pubmed.analyzer import (
    AnalysisConfig,
    PaperAnalyzer,
    PaperInput,
)


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    # ==================== 配置分析器 ====================
    config = AnalysisConfig(
        # 分析类型
        analysis_types=["summary", "domain"],
        # 目标领域列表（用于领域判定）
        domain_list=[
            "植物基因组学",
            "作物分子育种",
            "植物抗逆性",
            "水稻功能基因组",
            "植物表观遗传学",
        ],
        # LLM 配置 - 使用 Ollama
        llm_provider="ollama",
        llm_model="qwen3:latest",  # 可以替换为其他模型，如 llama3.2:latest
        llm_base_url="http://localhost:11434",  # Ollama 默认地址
        # 处理配置
        batch_size=5,
        max_concurrent=2,  # Ollama 本地运行，降低并发
        temperature=0.1,
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # ==================== 准备测试数据 ====================
    # 示例文献 1
    paper1 = PaperInput(
        pmid="38123456",
        title="Genome-wide association study reveals novel loci for rice grain quality",
        abstract=(
            "Rice grain quality is a complex trait influenced by multiple genetic factors. "
            "In this study, we conducted a genome-wide association study (GWAS) using a diverse "
            "panel of 500 rice accessions to identify genetic loci associated with grain quality traits. "
            "We identified 15 novel quantitative trait loci (QTLs) significantly associated with "
            "amylose content, protein content, and grain appearance. Candidate gene analysis revealed "
            "several genes involved in starch biosynthesis and protein metabolism. These findings provide "
            "valuable insights for rice quality improvement through marker-assisted selection."
        ),
        authors=["Zhang Wei", "Li Ming", "Wang Jun"],
        journal="Nature Genetics",
        pubdate="2024-01-15",
    )

    # 示例文献 2
    paper2 = PaperInput(
        pmid="38123457",
        title="CRISPR/Cas9-mediated editing of OsSWEET14 enhances rice resistance to bacterial blight",
        abstract=(
            "Bacterial blight caused by Xanthomonas oryzae pv. oryzae (Xoo) is one of the most "
            "devastating diseases in rice production worldwide. The SWEET14 gene family has been "
            "identified as susceptibility genes exploited by Xoo. In this study, we used CRISPR/Cas9 "
            "technology to edit the promoter region of OsSWEET14 to create resistant rice lines. "
            "The edited lines showed significantly enhanced resistance to multiple Xoo strains without "
            "compromising agronomic performance. Our results demonstrate that precise genome editing "
            "of susceptibility genes represents a promising strategy for developing disease-resistant crops."
        ),
        authors=["Chen Lin", "Liu Yang", "Zhou Xin"],
        journal="Plant Biotechnology Journal",
        pubdate="2024-02-20",
    )

    papers: Sequence[PaperInput] = [paper1, paper2]

    # ==================== 单篇分析示例 ====================
    logger.info("\n" + "=" * 80)
    logger.info("开始单篇论文分析（使用 Ollama）")
    logger.info("=" * 80)

    result1 = await analyzer.analyze_paper(paper1)

    logger.info(f"\n论文标题: {result1.title}")
    logger.info(f"PMID: {result1.pmid}")

    if result1.summary:
        logger.info("\n【论文总结】")
        logger.info(f"主要发现: {result1.summary.main_findings}")
        logger.info(f"创新点: {result1.summary.innovations}")
        logger.info(f"核心结论: {result1.summary.conclusions}")

    if result1.domain_analysis:
        logger.info("\n【领域判定】")
        logger.info(f"主要领域: {result1.domain_analysis.primary_domain}")
        logger.info(f"相关领域: {result1.domain_analysis.relevant_domains}")
        logger.info(f"领域评分: {result1.domain_analysis.domain_scores}")
        logger.info(f"判定依据: {result1.domain_analysis.reasoning}")

    logger.info("\n【处理元数据】")
    logger.info(f"LLM 模型: {result1.processing_metadata.llm_model}")
    logger.info(f"处理耗时: {result1.processing_metadata.processing_time:.2f}秒")
    logger.info(f"缓存命中: {result1.processing_metadata.cache_hit}")

    # ==================== 批量分析示例 ====================
    logger.info("\n" + "=" * 80)
    logger.info("开始批量论文分析")
    logger.info("=" * 80)

    # 定义进度回调函数
    def progress_callback(current: int, total: int) -> None:
        logger.info(f"进度: {current}/{total} ({current / total * 100:.1f}%)")

    # 批量分析
    results = await analyzer.analyze_batch(papers, progress_callback=progress_callback)

    logger.info(f"\n批量分析完成，共处理 {len(results)} 篇论文")

    # ==================== 导出结果 ====================
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "analyzer_results_ollama.json"

    analyzer.export_results(results, str(output_file))
    logger.info(f"\n分析结果已导出到: {output_file}")

    # ==================== 缓存统计 ====================
    cache_stats = analyzer.get_cache_stats()
    logger.info("\n【缓存统计信息】")
    logger.info(f"缓存启用: {cache_stats.get('enabled', False)}")
    logger.info(f"缓存条目数: {cache_stats.get('size', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
