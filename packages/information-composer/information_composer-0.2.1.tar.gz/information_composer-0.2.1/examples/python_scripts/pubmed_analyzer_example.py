"""
PubMed 文献智能分析示例

演示如何使用 PaperAnalyzer 进行文献分析，包括：
1. 单篇论文总结分析
2. 单篇论文领域判定
3. 批量论文分析
4. 结果导出
"""

import asyncio
import os
from pathlib import Path

from information_composer.pubmed.analyzer import (
    AnalysisConfig,
    PaperAnalyzer,
    PaperInput,
)


async def example_single_summary():
    """示例1: 单篇论文总结分析"""
    print("=" * 80)
    print("示例1: 单篇论文总结分析")
    print("=" * 80)

    # 配置分析器 - 只进行论文总结
    config = AnalysisConfig(
        analysis_types=["summary"],
        llm_model="qwen-plus-latest",
        temperature=0.1,
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备论文数据
    paper = PaperInput(
        pmid="12345678",
        title="CRISPR-Cas9 mediated genome editing in rice for drought tolerance",
        abstract=(
            "Drought is a major environmental stress affecting rice yield worldwide. "
            "We developed a CRISPR-Cas9 system to edit key drought-responsive genes in rice. "
            "Three genes (OsDREB1A, OsNAC5, and OsLEA3) were simultaneously edited using "
            "multiplex CRISPR technology. The edited rice lines showed 30% higher grain yield "
            "under drought stress compared to wild-type plants. Gene expression analysis revealed "
            "enhanced activation of stress-responsive pathways. This study demonstrates the "
            "potential of genome editing for developing climate-resilient crops."
        ),
    )

    # 执行分析
    print("\n正在分析论文...")
    result = await analyzer.analyze_paper(paper)

    # 显示结果
    print(f"\n论文标题: {result.title}")
    print(f"PMID: {result.pmid}")
    print("\n主要发现:")
    for i, finding in enumerate(result.summary.main_findings, 1):
        print(f"  {i}. {finding}")

    print("\n创新点:")
    for i, innovation in enumerate(result.summary.innovations, 1):
        print(f"  {i}. {innovation}")

    print("\n核心结论:")
    print(f"  {result.summary.conclusions}")

    print("\n处理元数据:")
    print(f"  模型: {result.processing_metadata.llm_model}")
    print(f"  耗时: {result.processing_metadata.processing_time:.2f} 秒")
    print(f"  缓存命中: {result.processing_metadata.cache_hit}")

    return result


async def example_domain_analysis():
    """示例2: 领域判定分析"""
    print("\n" + "=" * 80)
    print("示例2: 领域判定分析")
    print("=" * 80)

    # 配置分析器 - 只进行领域判定
    config = AnalysisConfig(
        analysis_types=["domain"],
        domain_list=[
            "Genome Editing",
            "Plant Breeding",
            "Climate Change",
            "Cancer Research",
        ],
        llm_model="qwen-plus-latest",
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备论文数据
    paper = PaperInput(
        pmid="23456789",
        title="Application of CRISPR technology in crop improvement",
        abstract=(
            "CRISPR-Cas9 has revolutionized plant breeding by enabling precise genome editing. "
            "This review discusses recent advances in CRISPR applications for crop improvement, "
            "including yield enhancement, disease resistance, and stress tolerance. "
            "We highlight successful examples in rice, wheat, and maize, and discuss "
            "regulatory challenges for genome-edited crops."
        ),
    )

    # 执行分析
    print("\n正在分析论文领域...")
    result = await analyzer.analyze_paper(paper)

    # 显示结果
    print(f"\n论文标题: {result.title}")
    print("\n相关领域:")
    for domain in result.domain_analysis.relevant_domains:
        score = result.domain_analysis.domain_scores[domain]
        print(f"  - {domain}: {score:.2f}")

    print(f"\n主要领域: {result.domain_analysis.primary_domain}")
    print("\n判定依据:")
    print(f"  {result.domain_analysis.reasoning}")

    return result


async def example_full_analysis():
    """示例3: 完整分析（总结 + 领域判定）"""
    print("\n" + "=" * 80)
    print("示例3: 完整分析（总结 + 领域判定）")
    print("=" * 80)

    # 配置分析器 - 包含所有分析类型
    config = AnalysisConfig(
        analysis_types=["summary", "domain"],
        domain_list=["Epigenetics", "Gene Expression", "Plant Development"],
        llm_model="qwen-plus-latest",
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备论文数据
    paper = PaperInput(
        pmid="34567890",
        title="Histone modifications regulate flowering time in Arabidopsis",
        abstract=(
            "Flowering time is controlled by complex epigenetic mechanisms. "
            "We investigated the role of histone H3 lysine 27 trimethylation (H3K27me3) "
            "in vernalization-mediated flowering. ChIP-seq analysis revealed that H3K27me3 "
            "marks are dynamically deposited on FLOWERING LOCUS C (FLC) during cold exposure. "
            "Mutations in Polycomb Repressive Complex 2 (PRC2) components abolished H3K27me3 "
            "deposition and prevented vernalization response. Our findings demonstrate that "
            "epigenetic regulation is essential for plant adaptation to seasonal changes."
        ),
    )

    # 执行分析
    print("\n正在执行完整分析...")
    result = await analyzer.analyze_paper(paper)

    # 显示总结结果
    print("\n【论文总结】")
    print("主要发现:")
    for i, finding in enumerate(result.summary.main_findings, 1):
        print(f"  {i}. {finding}")

    print("\n创新点:")
    for i, innovation in enumerate(result.summary.innovations, 1):
        print(f"  {i}. {innovation}")

    # 显示领域判定结果
    print("\n【领域判定】")
    print(f"主要领域: {result.domain_analysis.primary_domain}")
    print("相关领域评分:")
    for domain in result.domain_analysis.relevant_domains:
        score = result.domain_analysis.domain_scores[domain]
        print(f"  - {domain}: {score:.2f}")

    # 显示置信度
    print("\n【置信度评分】")
    for analysis_type, score in result.confidence_scores.items():
        print(f"  {analysis_type}: {score:.2f}")

    return result


async def example_batch_analysis():
    """示例4: 批量分析"""
    print("\n" + "=" * 80)
    print("示例4: 批量论文分析")
    print("=" * 80)

    # 配置分析器
    config = AnalysisConfig(
        analysis_types=["summary", "domain"],
        domain_list=["Genome Editing", "Plant Genetics", "Molecular Biology"],
        llm_model="qwen-plus-latest",
        batch_size=2,  # 每批处理2篇
        max_concurrent=2,  # 最大并发数
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备多篇论文
    papers = [
        PaperInput(
            pmid="11111111",
            title="CRISPR base editing in plants",
            abstract="We developed a cytosine base editor for precise point mutations in rice without double-strand breaks.",
        ),
        PaperInput(
            pmid="22222222",
            title="Prime editing technology for crop improvement",
            abstract="Prime editing enables insertions, deletions, and base conversions in plant genomes with high precision.",
        ),
        PaperInput(
            pmid="33333333",
            title="RNA interference in plant disease resistance",
            abstract="RNAi-based approach provides effective resistance against viral and fungal pathogens in crops.",
        ),
    ]

    # 定义进度回调
    def progress_callback(current, total):
        print(f"  进度: {current}/{total} ({current * 100 // total}%)")

    # 执行批量分析
    print(f"\n开始批量分析 {len(papers)} 篇论文...")
    results = await analyzer.analyze_batch(papers, progress_callback=progress_callback)

    # 显示结果摘要
    print(f"\n批量分析完成，成功分析 {len(results)} 篇论文\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   PMID: {result.pmid}")
        print(f"   主要领域: {result.domain_analysis.primary_domain}")
        print(f"   主要发现数: {len(result.summary.main_findings)}")
        print()

    # 导出结果
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "batch_analysis_results.json"

    print(f"导出结果到: {output_file}")
    analyzer.export_results(results, str(output_file))

    return results


async def example_cache_management():
    """示例5: 缓存管理"""
    print("\n" + "=" * 80)
    print("示例5: 缓存管理")
    print("=" * 80)

    # 创建分析器
    config = AnalysisConfig(
        analysis_types=["summary"],
        cache_enabled=True,
    )
    analyzer = PaperAnalyzer(config)

    # 获取缓存统计
    stats = analyzer.get_cache_stats()
    print("\n缓存统计信息:")
    print(f"  启用状态: {stats.get('enabled', False)}")
    print(f"  缓存目录: {stats.get('cache_dir', 'N/A')}")
    print(f"  缓存文件数: {stats.get('total_files', 0)}")
    print(f"  总大小: {stats.get('total_size_mb', 0)} MB")

    return stats


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 80)
    print("PubMed 文献智能分析示例")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("请设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
        return

    try:
        # 运行示例 1: 论文总结
        await example_single_summary()

        # 运行示例 2: 领域判定
        await example_domain_analysis()

        # 运行示例 3: 完整分析
        await example_full_analysis()

        # 运行示例 4: 批量分析
        await example_batch_analysis()

        # 运行示例 5: 缓存管理
        await example_cache_management()

        print("\n" + "=" * 80)
        print("所有示例运行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
"""
PubMed 文献智能分析示例

演示如何使用 PaperAnalyzer 进行文献分析，包括：
1. 单篇论文总结分析
2. 单篇论文领域判定
3. 批量论文分析
4. 结果导出
"""

import asyncio
import os
from pathlib import Path

from information_composer.pubmed.analyzer import (
    AnalysisConfig,
    PaperAnalyzer,
    PaperInput,
)


async def example_single_summary():
    """示例1: 单篇论文总结分析"""
    print("=" * 80)
    print("示例1: 单篇论文总结分析")
    print("=" * 80)

    # 配置分析器 - 只进行论文总结
    config = AnalysisConfig(
        analysis_types=["summary"],
        llm_model="qwen-plus-latest",
        temperature=0.1,
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备论文数据
    paper = PaperInput(
        pmid="12345678",
        title="CRISPR-Cas9 mediated genome editing in rice for drought tolerance",
        abstract=(
            "Drought is a major environmental stress affecting rice yield worldwide. "
            "We developed a CRISPR-Cas9 system to edit key drought-responsive genes in rice. "
            "Three genes (OsDREB1A, OsNAC5, and OsLEA3) were simultaneously edited using "
            "multiplex CRISPR technology. The edited rice lines showed 30% higher grain yield "
            "under drought stress compared to wild-type plants. Gene expression analysis revealed "
            "enhanced activation of stress-responsive pathways. This study demonstrates the "
            "potential of genome editing for developing climate-resilient crops."
        ),
    )

    # 执行分析
    print("\n正在分析论文...")
    result = await analyzer.analyze_paper(paper)

    # 显示结果
    print(f"\n论文标题: {result.title}")
    print(f"PMID: {result.pmid}")
    print("\n主要发现:")
    for i, finding in enumerate(result.summary.main_findings, 1):
        print(f"  {i}. {finding}")

    print("\n创新点:")
    for i, innovation in enumerate(result.summary.innovations, 1):
        print(f"  {i}. {innovation}")

    print("\n核心结论:")
    print(f"  {result.summary.conclusions}")

    print("\n处理元数据:")
    print(f"  模型: {result.processing_metadata.llm_model}")
    print(f"  耗时: {result.processing_metadata.processing_time:.2f} 秒")
    print(f"  缓存命中: {result.processing_metadata.cache_hit}")

    return result


async def example_domain_analysis():
    """示例2: 领域判定分析"""
    print("\n" + "=" * 80)
    print("示例2: 领域判定分析")
    print("=" * 80)

    # 配置分析器 - 只进行领域判定
    config = AnalysisConfig(
        analysis_types=["domain"],
        domain_list=[
            "Genome Editing",
            "Plant Breeding",
            "Climate Change",
            "Cancer Research",
        ],
        llm_model="qwen-plus-latest",
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备论文数据
    paper = PaperInput(
        pmid="23456789",
        title="Application of CRISPR technology in crop improvement",
        abstract=(
            "CRISPR-Cas9 has revolutionized plant breeding by enabling precise genome editing. "
            "This review discusses recent advances in CRISPR applications for crop improvement, "
            "including yield enhancement, disease resistance, and stress tolerance. "
            "We highlight successful examples in rice, wheat, and maize, and discuss "
            "regulatory challenges for genome-edited crops."
        ),
    )

    # 执行分析
    print("\n正在分析论文领域...")
    result = await analyzer.analyze_paper(paper)

    # 显示结果
    print(f"\n论文标题: {result.title}")
    print("\n相关领域:")
    for domain in result.domain_analysis.relevant_domains:
        score = result.domain_analysis.domain_scores[domain]
        print(f"  - {domain}: {score:.2f}")

    print(f"\n主要领域: {result.domain_analysis.primary_domain}")
    print("\n判定依据:")
    print(f"  {result.domain_analysis.reasoning}")

    return result


async def example_full_analysis():
    """示例3: 完整分析（总结 + 领域判定）"""
    print("\n" + "=" * 80)
    print("示例3: 完整分析（总结 + 领域判定）")
    print("=" * 80)

    # 配置分析器 - 包含所有分析类型
    config = AnalysisConfig(
        analysis_types=["summary", "domain"],
        domain_list=["Epigenetics", "Gene Expression", "Plant Development"],
        llm_model="qwen-plus-latest",
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备论文数据
    paper = PaperInput(
        pmid="34567890",
        title="Histone modifications regulate flowering time in Arabidopsis",
        abstract=(
            "Flowering time is controlled by complex epigenetic mechanisms. "
            "We investigated the role of histone H3 lysine 27 trimethylation (H3K27me3) "
            "in vernalization-mediated flowering. ChIP-seq analysis revealed that H3K27me3 "
            "marks are dynamically deposited on FLOWERING LOCUS C (FLC) during cold exposure. "
            "Mutations in Polycomb Repressive Complex 2 (PRC2) components abolished H3K27me3 "
            "deposition and prevented vernalization response. Our findings demonstrate that "
            "epigenetic regulation is essential for plant adaptation to seasonal changes."
        ),
    )

    # 执行分析
    print("\n正在执行完整分析...")
    result = await analyzer.analyze_paper(paper)

    # 显示总结结果
    print("\n【论文总结】")
    print("主要发现:")
    for i, finding in enumerate(result.summary.main_findings, 1):
        print(f"  {i}. {finding}")

    print("\n创新点:")
    for i, innovation in enumerate(result.summary.innovations, 1):
        print(f"  {i}. {innovation}")

    # 显示领域判定结果
    print("\n【领域判定】")
    print(f"主要领域: {result.domain_analysis.primary_domain}")
    print("相关领域评分:")
    for domain in result.domain_analysis.relevant_domains:
        score = result.domain_analysis.domain_scores[domain]
        print(f"  - {domain}: {score:.2f}")

    # 显示置信度
    print("\n【置信度评分】")
    for analysis_type, score in result.confidence_scores.items():
        print(f"  {analysis_type}: {score:.2f}")

    return result


async def example_batch_analysis():
    """示例4: 批量分析"""
    print("\n" + "=" * 80)
    print("示例4: 批量论文分析")
    print("=" * 80)

    # 配置分析器
    config = AnalysisConfig(
        analysis_types=["summary", "domain"],
        domain_list=["Genome Editing", "Plant Genetics", "Molecular Biology"],
        llm_model="qwen-plus-latest",
        batch_size=2,  # 每批处理2篇
        max_concurrent=2,  # 最大并发数
        cache_enabled=True,
    )

    # 创建分析器
    analyzer = PaperAnalyzer(config)

    # 准备多篇论文
    papers = [
        PaperInput(
            pmid="11111111",
            title="CRISPR base editing in plants",
            abstract="We developed a cytosine base editor for precise point mutations in rice without double-strand breaks.",
        ),
        PaperInput(
            pmid="22222222",
            title="Prime editing technology for crop improvement",
            abstract="Prime editing enables insertions, deletions, and base conversions in plant genomes with high precision.",
        ),
        PaperInput(
            pmid="33333333",
            title="RNA interference in plant disease resistance",
            abstract="RNAi-based approach provides effective resistance against viral and fungal pathogens in crops.",
        ),
    ]

    # 定义进度回调
    def progress_callback(current, total):
        print(f"  进度: {current}/{total} ({current * 100 // total}%)")

    # 执行批量分析
    print(f"\n开始批量分析 {len(papers)} 篇论文...")
    results = await analyzer.analyze_batch(papers, progress_callback=progress_callback)

    # 显示结果摘要
    print(f"\n批量分析完成，成功分析 {len(results)} 篇论文\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   PMID: {result.pmid}")
        print(f"   主要领域: {result.domain_analysis.primary_domain}")
        print(f"   主要发现数: {len(result.summary.main_findings)}")
        print()

    # 导出结果
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "batch_analysis_results.json"

    print(f"导出结果到: {output_file}")
    analyzer.export_results(results, str(output_file))

    return results


async def example_cache_management():
    """示例5: 缓存管理"""
    print("\n" + "=" * 80)
    print("示例5: 缓存管理")
    print("=" * 80)

    # 创建分析器
    config = AnalysisConfig(
        analysis_types=["summary"],
        cache_enabled=True,
    )
    analyzer = PaperAnalyzer(config)

    # 获取缓存统计
    stats = analyzer.get_cache_stats()
    print("\n缓存统计信息:")
    print(f"  启用状态: {stats.get('enabled', False)}")
    print(f"  缓存目录: {stats.get('cache_dir', 'N/A')}")
    print(f"  缓存文件数: {stats.get('total_files', 0)}")
    print(f"  总大小: {stats.get('total_size_mb', 0)} MB")

    return stats


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 80)
    print("PubMed 文献智能分析示例")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("请设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
        return

    try:
        # 运行示例 1: 论文总结
        await example_single_summary()

        # 运行示例 2: 领域判定
        await example_domain_analysis()

        # 运行示例 3: 完整分析
        await example_full_analysis()

        # 运行示例 4: 批量分析
        await example_batch_analysis()

        # 运行示例 5: 缓存管理
        await example_cache_management()

        print("\n" + "=" * 80)
        print("所有示例运行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
