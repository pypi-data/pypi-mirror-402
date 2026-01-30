"""
PubMed 模块集成示例

演示如何将 PaperAnalyzer 与现有的 PubMed 搜索功能集成使用。
"""

import asyncio
import os

from information_composer.pubmed.analyzer import (
    AnalysisConfig,
    PaperAnalyzer,
    PaperInput,
)
from information_composer.pubmed.pubmed import (
    fetch_pubmed_details_batch_sync,
    query_pmid,
)


def convert_pubmed_to_paper_input(pubmed_article: dict) -> PaperInput:
    """
    将 PubMed 文章数据转换为 PaperInput 格式

    Args:
        pubmed_article: PubMed 文章数据

    Returns:
        PaperInput 对象
    """
    return PaperInput(
        pmid=pubmed_article.get("pmid", ""),
        title=pubmed_article.get("title", ""),
        abstract=pubmed_article.get("abstract", ""),
        authors=pubmed_article.get("authors", []),
        journal=pubmed_article.get("journal", ""),
        pubdate=pubmed_article.get("pubdate", ""),
        keywords=pubmed_article.get("keywords", []),
        mesh_terms=pubmed_article.get("mesh_terms", []),
    )


async def example_search_and_analyze():
    """示例: 搜索 PubMed 文献并进行智能分析"""
    print("=" * 80)
    print("PubMed 搜索与智能分析集成示例")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        return

    # 1. 搜索 PubMed 文献
    search_query = "CRISPR rice[Title/Abstract]"
    max_results = 5

    print("\n步骤 1: 搜索 PubMed 文献")
    print(f"  查询: {search_query}")
    print(f"  最大结果数: {max_results}")

    try:
        # 使用 PubMed 模块搜索
        pmid_list = query_pmid(
            query=search_query,
            retmax=max_results,
            email="example@example.com",  # 请替换为您的邮箱
        )

        print(f"  找到 {len(pmid_list)} 篇文献")

        if not pmid_list:
            print("  没有找到相关文献，退出")
            return

        # 2. 获取文献详情
        print("\n步骤 2: 获取文献详情")

        # 批量获取文献详情
        articles = fetch_pubmed_details_batch_sync(
            pmid_list=pmid_list,
            email="example@example.com",  # 请替换为您的邮箱
        )

        print(f"  成功获取 {len(articles)} 篇文献详情")

        # 3. 转换为 PaperInput 格式
        print("\n步骤 3: 转换数据格式")
        papers: list[PaperInput] = []

        for article in articles:
            try:
                paper = convert_pubmed_to_paper_input(article)
                papers.append(paper)
                print(f"  - {paper.pmid}: {paper.title[:60]}...")
            except Exception as e:
                print(f"  转换失败: {e}")

        if not papers:
            print("  没有可分析的文献")
            return

        # 4. 配置分析器并执行分析
        print("\n步骤 4: 执行智能分析")

        config = AnalysisConfig(
            analysis_types=["summary", "domain"],
            domain_list=[
                "Genome Editing",
                "Plant Genetics",
                "Molecular Biology",
                "Agricultural Biotechnology",
            ],
            llm_model="qwen-plus-latest",
            batch_size=3,
            max_concurrent=2,
            cache_enabled=True,
        )

        analyzer = PaperAnalyzer(config)

        # 定义进度回调
        def progress_callback(current, total):
            print(f"  分析进度: {current}/{total} ({current * 100 // total}%)")

        # 批量分析
        results = await analyzer.analyze_batch(
            papers, progress_callback=progress_callback
        )

        # 5. 显示分析结果
        print("\n步骤 5: 分析结果汇总")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n【论文 {i}】")
            print(f"PMID: {result.pmid}")
            print(f"标题: {result.title}")
            print(f"\n主要领域: {result.domain_analysis.primary_domain}")

            print("\n相关领域评分:")
            for domain in result.domain_analysis.relevant_domains:
                score = result.domain_analysis.domain_scores[domain]
                print(f"  - {domain}: {score:.2f}")

            print("\n主要发现:")
            for j, finding in enumerate(result.summary.main_findings, 1):
                print(f"  {j}. {finding}")

            print("\n创新点:")
            for j, innovation in enumerate(result.summary.innovations, 1):
                print(f"  {j}. {innovation}")

            print("\n核心结论:")
            print(f"  {result.summary.conclusions}")

            print(f"\n处理时间: {result.processing_metadata.processing_time:.2f} 秒")
            print("-" * 80)

        # 6. 导出结果
        print("\n步骤 6: 导出分析结果")
        output_file = "./output/pubmed_search_analysis.json"
        os.makedirs("./output", exist_ok=True)

        analyzer.export_results(results, output_file)
        print(f"  结果已导出到: {output_file}")

        # 7. 显示缓存统计
        print("\n步骤 7: 缓存统计")
        stats = analyzer.get_cache_stats()
        print(f"  缓存文件数: {stats.get('total_files', 0)}")
        print(f"  缓存大小: {stats.get('total_size_mb', 0)} MB")

        print("\n" + "=" * 80)
        print("集成示例运行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


async def example_analyze_specific_pmids():
    """示例: 分析指定的 PMID 列表"""
    print("\n" + "=" * 80)
    print("分析指定 PMID 列表示例")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        return

    # 指定要分析的 PMID
    pmid_list = ["38704099", "38623486", "38357163"]  # 示例 PMID

    print(f"\n待分析的 PMID: {', '.join(pmid_list)}")

    try:
        # 1. 获取文献详情
        print("\n获取文献详情...")
        articles = fetch_pubmed_details_batch_sync(
            pmid_list=pmid_list,
            email="example@example.com",  # 请替换为您的邮箱
        )

        # 2. 转换格式
        papers = [convert_pubmed_to_paper_input(article) for article in articles]

        # 3. 配置并执行分析
        config = AnalysisConfig(
            analysis_types=["summary"],
            llm_model="qwen-plus-latest",
            cache_enabled=True,
        )

        analyzer = PaperAnalyzer(config)

        print(f"\n开始分析 {len(papers)} 篇文献...")
        results = await analyzer.analyze_batch(papers)

        # 4. 显示结果
        print("\n分析完成！\n")
        for result in results:
            print(f"PMID: {result.pmid}")
            print(f"标题: {result.title}")
            print(f"主要发现: {len(result.summary.main_findings)} 项")
            print("-" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """主函数"""
    # 运行搜索和分析集成示例
    await example_search_and_analyze()

    # 可选: 运行指定 PMID 分析示例
    # await example_analyze_specific_pmids()


if __name__ == "__main__":
    asyncio.run(main())
"""
PubMed 模块集成示例

演示如何将 PaperAnalyzer 与现有的 PubMed 搜索功能集成使用。
"""

import asyncio
import os

from information_composer.pubmed.analyzer import (
    AnalysisConfig,
    PaperAnalyzer,
    PaperInput,
)
from information_composer.pubmed.pubmed import (
    fetch_pubmed_details_batch_sync,
    query_pmid,
)


def convert_pubmed_to_paper_input(pubmed_article: dict) -> PaperInput:
    """
    将 PubMed 文章数据转换为 PaperInput 格式

    Args:
        pubmed_article: PubMed 文章数据

    Returns:
        PaperInput 对象
    """
    return PaperInput(
        pmid=pubmed_article.get("pmid", ""),
        title=pubmed_article.get("title", ""),
        abstract=pubmed_article.get("abstract", ""),
        authors=pubmed_article.get("authors", []),
        journal=pubmed_article.get("journal", ""),
        pubdate=pubmed_article.get("pubdate", ""),
        keywords=pubmed_article.get("keywords", []),
        mesh_terms=pubmed_article.get("mesh_terms", []),
    )


async def example_search_and_analyze():
    """示例: 搜索 PubMed 文献并进行智能分析"""
    print("=" * 80)
    print("PubMed 搜索与智能分析集成示例")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        return

    # 1. 搜索 PubMed 文献
    search_query = "CRISPR rice[Title/Abstract]"
    max_results = 5

    print("\n步骤 1: 搜索 PubMed 文献")
    print(f"  查询: {search_query}")
    print(f"  最大结果数: {max_results}")

    try:
        # 使用 PubMed 模块搜索
        pmid_list = query_pmid(
            query=search_query,
            retmax=max_results,
            email="example@example.com",  # 请替换为您的邮箱
        )

        print(f"  找到 {len(pmid_list)} 篇文献")

        if not pmid_list:
            print("  没有找到相关文献，退出")
            return

        # 2. 获取文献详情
        print("\n步骤 2: 获取文献详情")

        # 批量获取文献详情
        articles = fetch_pubmed_details_batch_sync(
            pmid_list=pmid_list,
            email="example@example.com",  # 请替换为您的邮箱
        )

        print(f"  成功获取 {len(articles)} 篇文献详情")

        # 3. 转换为 PaperInput 格式
        print("\n步骤 3: 转换数据格式")
        papers: list[PaperInput] = []

        for article in articles:
            try:
                paper = convert_pubmed_to_paper_input(article)
                papers.append(paper)
                print(f"  - {paper.pmid}: {paper.title[:60]}...")
            except Exception as e:
                print(f"  转换失败: {e}")

        if not papers:
            print("  没有可分析的文献")
            return

        # 4. 配置分析器并执行分析
        print("\n步骤 4: 执行智能分析")

        config = AnalysisConfig(
            analysis_types=["summary", "domain"],
            domain_list=[
                "Genome Editing",
                "Plant Genetics",
                "Molecular Biology",
                "Agricultural Biotechnology",
            ],
            llm_model="qwen-plus-latest",
            batch_size=3,
            max_concurrent=2,
            cache_enabled=True,
        )

        analyzer = PaperAnalyzer(config)

        # 定义进度回调
        def progress_callback(current, total):
            print(f"  分析进度: {current}/{total} ({current * 100 // total}%)")

        # 批量分析
        results = await analyzer.analyze_batch(
            papers, progress_callback=progress_callback
        )

        # 5. 显示分析结果
        print("\n步骤 5: 分析结果汇总")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n【论文 {i}】")
            print(f"PMID: {result.pmid}")
            print(f"标题: {result.title}")
            print(f"\n主要领域: {result.domain_analysis.primary_domain}")

            print("\n相关领域评分:")
            for domain in result.domain_analysis.relevant_domains:
                score = result.domain_analysis.domain_scores[domain]
                print(f"  - {domain}: {score:.2f}")

            print("\n主要发现:")
            for j, finding in enumerate(result.summary.main_findings, 1):
                print(f"  {j}. {finding}")

            print("\n创新点:")
            for j, innovation in enumerate(result.summary.innovations, 1):
                print(f"  {j}. {innovation}")

            print("\n核心结论:")
            print(f"  {result.summary.conclusions}")

            print(f"\n处理时间: {result.processing_metadata.processing_time:.2f} 秒")
            print("-" * 80)

        # 6. 导出结果
        print("\n步骤 6: 导出分析结果")
        output_file = "./output/pubmed_search_analysis.json"
        os.makedirs("./output", exist_ok=True)

        analyzer.export_results(results, output_file)
        print(f"  结果已导出到: {output_file}")

        # 7. 显示缓存统计
        print("\n步骤 7: 缓存统计")
        stats = analyzer.get_cache_stats()
        print(f"  缓存文件数: {stats.get('total_files', 0)}")
        print(f"  缓存大小: {stats.get('total_size_mb', 0)} MB")

        print("\n" + "=" * 80)
        print("集成示例运行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


async def example_analyze_specific_pmids():
    """示例: 分析指定的 PMID 列表"""
    print("\n" + "=" * 80)
    print("分析指定 PMID 列表示例")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        return

    # 指定要分析的 PMID
    pmid_list = ["38704099", "38623486", "38357163"]  # 示例 PMID

    print(f"\n待分析的 PMID: {', '.join(pmid_list)}")

    try:
        # 1. 获取文献详情
        print("\n获取文献详情...")
        articles = fetch_pubmed_details_batch_sync(
            pmid_list=pmid_list,
            email="example@example.com",  # 请替换为您的邮箱
        )

        # 2. 转换格式
        papers = [convert_pubmed_to_paper_input(article) for article in articles]

        # 3. 配置并执行分析
        config = AnalysisConfig(
            analysis_types=["summary"],
            llm_model="qwen-plus-latest",
            cache_enabled=True,
        )

        analyzer = PaperAnalyzer(config)

        print(f"\n开始分析 {len(papers)} 篇文献...")
        results = await analyzer.analyze_batch(papers)

        # 4. 显示结果
        print("\n分析完成！\n")
        for result in results:
            print(f"PMID: {result.pmid}")
            print(f"标题: {result.title}")
            print(f"主要发现: {len(result.summary.main_findings)} 项")
            print("-" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """主函数"""
    # 运行搜索和分析集成示例
    await example_search_and_analyze()

    # 可选: 运行指定 PMID 分析示例
    # await example_analyze_specific_pmids()


if __name__ == "__main__":
    asyncio.run(main())
