"""
PubMed 论文分析器 - OpenAI 使用示例

演示如何使用 OpenAI API 进行论文分析。
支持的模型：gpt-4o, gpt-4o-mini, gpt-3.5-turbo 等
"""

import asyncio
import logging
import os
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
    # 从环境变量获取 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量")
        logger.warning("请运行: export OPENAI_API_KEY='your-api-key'")
        return

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
        # LLM 配置 - 使用 OpenAI
        llm_provider="openai",
        llm_model="gpt-4o-mini",  # 可以替换为 gpt-4o 或 gpt-3.5-turbo
        llm_api_key=api_key,
        # 可选：使用自定义 base_url（如 Azure OpenAI 或其他兼容服务）
        # llm_base_url="https://your-endpoint.openai.azure.com/",
        # 处理配置
        batch_size=10,
        max_concurrent=5,
        temperature=0.1,
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # ==================== 准备测试数据 ====================
    paper = PaperInput(
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

    # ==================== 单篇分析示例 ====================
    logger.info("\n" + "=" * 80)
    logger.info("开始论文分析（使用 OpenAI GPT-4o-mini）")
    logger.info("=" * 80)

    result = await analyzer.analyze_paper(paper)

    logger.info(f"\n论文标题: {result.title}")
    logger.info(f"PMID: {result.pmid}")

    if result.summary:
        logger.info("\n【论文总结】")
        logger.info(f"主要发现: {result.summary.main_findings}")
        logger.info(f"创新点: {result.summary.innovations}")
        logger.info(f"核心结论: {result.summary.conclusions}")

    if result.domain_analysis:
        logger.info("\n【领域判定】")
        logger.info(f"主要领域: {result.domain_analysis.primary_domain}")
        logger.info(f"相关领域: {result.domain_analysis.relevant_domains}")
        logger.info(f"领域评分: {result.domain_analysis.domain_scores}")
        logger.info(f"判定依据: {result.domain_analysis.reasoning}")

    logger.info("\n【处理元数据】")
    logger.info(f"LLM 模型: {result.processing_metadata.llm_model}")
    logger.info(f"处理耗时: {result.processing_metadata.processing_time:.2f}秒")
    logger.info(f"缓存命中: {result.processing_metadata.cache_hit}")

    # ==================== 导出结果 ====================
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "analyzer_results_openai.json"

    analyzer.export_results([result], str(output_file))
    logger.info(f"\n分析结果已导出到: {output_file}")

    # ==================== 缓存统计 ====================
    cache_stats = analyzer.get_cache_stats()
    logger.info("\n【缓存统计信息】")
    logger.info(f"缓存启用: {cache_stats.get('enabled', False)}")
    logger.info(f"缓存条目数: {cache_stats.get('size', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
