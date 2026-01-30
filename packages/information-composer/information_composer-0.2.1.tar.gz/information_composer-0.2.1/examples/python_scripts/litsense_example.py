"""
LitSense API 使用示例

展示如何使用 LitSense API 进行 PubMed 语义搜索。
"""

from information_composer.pubmed.litsense import LitSenseAPI, search_litsense


def example_basic_search():
    """基础搜索示例"""
    print("=" * 60)
    print("示例 1: 基础搜索")
    print("=" * 60)

    # 使用便捷函数进行一次性搜索
    results = search_litsense("machine learning in medical diagnosis", rerank=True)

    print(f"\n找到 {len(results)} 篇文章")
    print("\n前 5 篇文章:")
    for i, article in enumerate(results[:5], 1):
        print(f"\n{i}. PMID: {article.get('pmid', 'N/A')}")
        print(f"   标题: {article.get('title', 'N/A')[:80]}...")
        print(f"   期刊: {article.get('journal', 'N/A')}")
        if "score" in article:
            print(f"   相关性得分: {article['score']}")


def example_client_usage():
    """使用客户端进行多次搜索"""
    print("\n\n" + "=" * 60)
    print("示例 2: 使用客户端对象进行多次搜索")
    print("=" * 60)

    # 使用上下文管理器
    with LitSenseAPI() as client:
        # 搜索 1
        print("\n搜索: CRISPR gene editing")
        results1 = client.search("CRISPR gene editing", rerank=True)
        print(f"找到 {len(results1)} 篇文章")

        # 搜索 2 (自动执行 1 秒速率限制)
        print("\n搜索: COVID-19 vaccine efficacy")
        results2 = client.search("COVID-19 vaccine efficacy", rerank=True)
        print(f"找到 {len(results2)} 篇文章")

        # 仅获取 PMIDs
        print("\n搜索: cancer immunotherapy (仅 PMIDs)")
        pmids = client.get_pmids("cancer immunotherapy", limit=10)
        print(f"前 10 个 PMIDs: {pmids}")


def example_batch_search():
    """批量搜索示例"""
    print("\n\n" + "=" * 60)
    print("示例 3: 批量搜索多个查询")
    print("=" * 60)

    queries = [
        "diabetes type 2 treatment",
        "Alzheimer's disease biomarkers",
        "breast cancer screening",
    ]

    with LitSenseAPI() as client:
        results = client.search_batch(queries, rerank=True, verbose=True)

        print("\n批量搜索结果汇总:")
        for query, articles in results.items():
            print(f"\n查询: {query}")
            print(f"结果数: {len(articles)}")
            if articles:
                print(f"首篇 PMID: {articles[0].get('pmid', 'N/A')}")


def example_integration_with_database():
    """与数据库集成示例"""
    print("\n\n" + "=" * 60)
    print("示例 4: 与 PubMed 数据库集成")
    print("=" * 60)

    from information_composer.pubmed.database import PubMedDatabase
    from information_composer.pubmed.pubmed import fetch_pubmed_details_batch_sync

    # 使用 LitSense 搜索
    print("\n1. 使用 LitSense 搜索相关文章")
    pmids = search_litsense("machine learning diagnosis", rerank=True)
    pmid_list = [str(article["pmid"]) for article in pmids[:10]]  # 取前 10 篇
    print(f"   获得 {len(pmid_list)} 个 PMIDs")

    # 获取详细信息
    print("\n2. 从 PubMed 获取详细信息")
    details = fetch_pubmed_details_batch_sync(
        pmid_list,
        email="your_email@example.com",
        cache_dir="pubmed_analysis_cache",
    )
    print(f"   获取了 {len(details)} 篇文章的详细信息")

    # 保存到数据库
    print("\n3. 保存到本地数据库")
    db = PubMedDatabase("data/pubmed/litsense_results.db")

    # 添加 pubmed_query 字段
    for article in details:
        article["pubmed_query"] = "LitSense: machine learning diagnosis"

    saved_count = db.save_articles_batch(details)
    print(f"   成功保存 {saved_count} 篇文章")

    db.close()
    print("\n✓ 完成：文章已保存到 data/pubmed/litsense_results.db")


def example_error_handling():
    """错误处理示例"""
    print("\n\n" + "=" * 60)
    print("示例 5: 错误处理")
    print("=" * 60)

    with LitSenseAPI() as client:
        # 空查询
        try:
            client.search("")
        except ValueError as e:
            print(f"✓ 捕获到预期错误: {e}")

        # 正常搜索
        try:
            results = client.search("valid query")
            print(f"✓ 正常搜索成功: {len(results)} 篇文章")
        except Exception as e:
            print(f"✗ 搜索失败: {e}")


if __name__ == "__main__":
    print("LitSense API 使用示例")
    print("注意：API 限制为每秒 1 次请求，请耐心等待\n")

    # 运行所有示例
    example_basic_search()
    example_client_usage()
    example_batch_search()

    # 以下示例需要数据库和网络连接，可选运行
    print("\n\n" + "=" * 60)
    print("高级示例（需要数据库和网络连接）")
    print("=" * 60)
    response = input("\n是否运行数据库集成示例？(y/N): ").strip().lower()
    if response in ["y", "yes"]:
        example_integration_with_database()

    example_error_handling()

    print("\n\n" + "=" * 60)
    print("所有示例完成！")
    print("=" * 60)
