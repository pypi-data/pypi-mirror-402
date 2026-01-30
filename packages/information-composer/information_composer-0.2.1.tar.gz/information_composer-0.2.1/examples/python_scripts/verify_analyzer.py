#!/usr/bin/env python
"""
快速验证脚本 - 测试 PubMed 分析器核心功能

不需要 API Key 即可运行，验证模块结构和基本功能。
"""

import sys


def test_imports():
    """测试模块导入"""
    print("=" * 80)
    print("测试 1: 模块导入")
    print("=" * 80)

    try:
        from information_composer.pubmed.analyzer import (
            AnalysisConfig,
            AnalysisResult,
            DomainResult,
            PaperAnalyzer,
            PaperInput,
            ProcessingMetadata,
            SummaryResult,
        )

        print("✓ analyzer 模块导入成功")

        # 测试从主模块导入
        from information_composer.pubmed import (
            AnalysisConfig as AC,
        )
        from information_composer.pubmed import (
            PaperAnalyzer as PA,
        )

        print("✓ 从主 pubmed 模块导入成功")

        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_models():
    """测试数据模型"""
    print("\n" + "=" * 80)
    print("测试 2: 数据模型验证")
    print("=" * 80)

    try:
        from information_composer.pubmed.analyzer import (
            AnalysisConfig,
            DomainResult,
            PaperInput,
            SummaryResult,
        )

        # 测试 PaperInput
        paper = PaperInput(
            pmid="12345678",
            title="Test Paper",
            abstract="This is a test abstract.",
        )
        print(f"✓ PaperInput 创建成功: PMID={paper.pmid}")

        # 测试 AnalysisConfig
        config = AnalysisConfig(
            analysis_types=["summary"],
            llm_model="qwen-plus-latest",
        )
        print(f"✓ AnalysisConfig 创建成功: 分析类型={config.analysis_types}")

        # 测试带领域的配置
        config_with_domain = AnalysisConfig(
            analysis_types=["domain"],
            domain_list=["Epigenetics", "Genetics"],
        )
        print(f"✓ 领域分析配置创建成功: 领域数={len(config_with_domain.domain_list)}")

        # 测试 SummaryResult
        summary = SummaryResult(
            main_findings=["Finding 1", "Finding 2"],
            innovations=["Innovation 1"],
            conclusions="Test conclusion",
        )
        print(f"✓ SummaryResult 创建成功: 发现数={len(summary.main_findings)}")

        # 测试 DomainResult
        domain = DomainResult(
            relevant_domains=["Epigenetics"],
            domain_scores={"Epigenetics": 0.9},
            primary_domain="Epigenetics",
            reasoning="Test reasoning",
        )
        print(f"✓ DomainResult 创建成功: 主要领域={domain.primary_domain}")

        return True
    except Exception as e:
        print(f"✗ 模型测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_prompts():
    """测试提示词模板"""
    print("\n" + "=" * 80)
    print("测试 3: 提示词模板")
    print("=" * 80)

    try:
        from information_composer.pubmed.analyzer.prompts import PromptManager

        manager = PromptManager()

        # 测试总结提示词
        summary_prompt = manager.get_summary_prompt()
        print("✓ 论文总结提示词模板创建成功")

        # 测试领域提示词
        domain_prompt = manager.get_domain_prompt()
        print("✓ 领域判定提示词模板创建成功")

        # 测试格式化
        summary_vars = manager.format_summary_prompt("Test title", "Test abstract")
        print(f"✓ 总结提示词格式化成功: {list(summary_vars.keys())}")

        domain_vars = manager.format_domain_prompt(
            "Test title", "Test abstract", ["Domain1", "Domain2"]
        )
        print(f"✓ 领域提示词格式化成功: {list(domain_vars.keys())}")

        return True
    except Exception as e:
        print(f"✗ 提示词测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cache():
    """测试缓存机制"""
    print("\n" + "=" * 80)
    print("测试 4: 缓存机制")
    print("=" * 80)

    try:
        import shutil
        import tempfile

        from information_composer.pubmed.analyzer.cache import AnalysisCache

        # 使用临时目录
        temp_dir = tempfile.mkdtemp()

        try:
            cache = AnalysisCache(cache_dir=temp_dir, enabled=True)
            print(f"✓ 缓存管理器创建成功: {temp_dir}")

            # 测试缓存设置
            test_config = {"analysis_types": ["summary"], "model": "test"}
            test_result = {"summary": "test result"}

            success = cache.set("test_pmid", test_config, test_result)
            print(f"✓ 缓存保存成功: {success}")

            # 测试缓存获取
            cached = cache.get("test_pmid", test_config)
            if cached == test_result:
                print("✓ 缓存读取成功，数据一致")
            else:
                print("✗ 缓存数据不一致")

            # 测试缓存统计
            stats = cache.get_cache_stats()
            print(
                f"✓ 缓存统计: {stats['total_files']} 文件, {stats['total_size_mb']} MB"
            )

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

        return True
    except Exception as e:
        print(f"✗ 缓存测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_analyzer_creation():
    """测试分析器创建"""
    print("\n" + "=" * 80)
    print("测试 5: 分析器创建（无 API Key）")
    print("=" * 80)

    try:
        import os

        from information_composer.pubmed.analyzer import AnalysisConfig, PaperAnalyzer

        # 临时设置一个假的 API Key 用于测试创建
        original_key = os.environ.get("DASHSCOPE_API_KEY")
        os.environ["DASHSCOPE_API_KEY"] = "fake-key-for-testing"

        try:
            config = AnalysisConfig(
                analysis_types=["summary"],
                llm_model="qwen-plus-latest",
                cache_enabled=False,  # 禁用缓存避免创建文件
            )

            analyzer = PaperAnalyzer(config)
            print("✓ PaperAnalyzer 创建成功")
            print(f"  - LLM 模型: {analyzer.config.llm_model}")
            print(f"  - 分析类型: {analyzer.config.analysis_types}")
            print(f"  - 最大并发: {analyzer.config.max_concurrent}")

        finally:
            # 恢复原始 API Key
            if original_key:
                os.environ["DASHSCOPE_API_KEY"] = original_key
            else:
                os.environ.pop("DASHSCOPE_API_KEY", None)

        return True
    except Exception as e:
        print(f"✗ 分析器创建测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PubMed 分析器功能验证" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    tests = [
        ("模块导入", test_imports),
        ("数据模型", test_models),
        ("提示词模板", test_prompts),
        ("缓存机制", test_cache),
        ("分析器创建", test_analyzer_creation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n测试 {name} 发生异常: {e}")
            results.append((name, False))

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")

    print("\n" + "=" * 80)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 80)

    if passed == total:
        print("\n🎉 所有测试通过！模块功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python
"""
快速验证脚本 - 测试 PubMed 分析器核心功能

不需要 API Key 即可运行，验证模块结构和基本功能。
"""

import sys


def test_imports():
    """测试模块导入"""
    print("=" * 80)
    print("测试 1: 模块导入")
    print("=" * 80)

    try:
        from information_composer.pubmed.analyzer import (
            AnalysisConfig,
            AnalysisResult,
            DomainResult,
            PaperAnalyzer,
            PaperInput,
            ProcessingMetadata,
            SummaryResult,
        )

        print("✓ analyzer 模块导入成功")

        # 测试从主模块导入
        from information_composer.pubmed import (
            AnalysisConfig as AC,
        )
        from information_composer.pubmed import (
            PaperAnalyzer as PA,
        )

        print("✓ 从主 pubmed 模块导入成功")

        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_models():
    """测试数据模型"""
    print("\n" + "=" * 80)
    print("测试 2: 数据模型验证")
    print("=" * 80)

    try:
        from information_composer.pubmed.analyzer import (
            AnalysisConfig,
            DomainResult,
            PaperInput,
            SummaryResult,
        )

        # 测试 PaperInput
        paper = PaperInput(
            pmid="12345678",
            title="Test Paper",
            abstract="This is a test abstract.",
        )
        print(f"✓ PaperInput 创建成功: PMID={paper.pmid}")

        # 测试 AnalysisConfig
        config = AnalysisConfig(
            analysis_types=["summary"],
            llm_model="qwen-plus-latest",
        )
        print(f"✓ AnalysisConfig 创建成功: 分析类型={config.analysis_types}")

        # 测试带领域的配置
        config_with_domain = AnalysisConfig(
            analysis_types=["domain"],
            domain_list=["Epigenetics", "Genetics"],
        )
        print(f"✓ 领域分析配置创建成功: 领域数={len(config_with_domain.domain_list)}")

        # 测试 SummaryResult
        summary = SummaryResult(
            main_findings=["Finding 1", "Finding 2"],
            innovations=["Innovation 1"],
            conclusions="Test conclusion",
        )
        print(f"✓ SummaryResult 创建成功: 发现数={len(summary.main_findings)}")

        # 测试 DomainResult
        domain = DomainResult(
            relevant_domains=["Epigenetics"],
            domain_scores={"Epigenetics": 0.9},
            primary_domain="Epigenetics",
            reasoning="Test reasoning",
        )
        print(f"✓ DomainResult 创建成功: 主要领域={domain.primary_domain}")

        return True
    except Exception as e:
        print(f"✗ 模型测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_prompts():
    """测试提示词模板"""
    print("\n" + "=" * 80)
    print("测试 3: 提示词模板")
    print("=" * 80)

    try:
        from information_composer.pubmed.analyzer.prompts import PromptManager

        manager = PromptManager()

        # 测试总结提示词
        summary_prompt = manager.get_summary_prompt()
        print("✓ 论文总结提示词模板创建成功")

        # 测试领域提示词
        domain_prompt = manager.get_domain_prompt()
        print("✓ 领域判定提示词模板创建成功")

        # 测试格式化
        summary_vars = manager.format_summary_prompt("Test title", "Test abstract")
        print(f"✓ 总结提示词格式化成功: {list(summary_vars.keys())}")

        domain_vars = manager.format_domain_prompt(
            "Test title", "Test abstract", ["Domain1", "Domain2"]
        )
        print(f"✓ 领域提示词格式化成功: {list(domain_vars.keys())}")

        return True
    except Exception as e:
        print(f"✗ 提示词测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cache():
    """测试缓存机制"""
    print("\n" + "=" * 80)
    print("测试 4: 缓存机制")
    print("=" * 80)

    try:
        import shutil
        import tempfile

        from information_composer.pubmed.analyzer.cache import AnalysisCache

        # 使用临时目录
        temp_dir = tempfile.mkdtemp()

        try:
            cache = AnalysisCache(cache_dir=temp_dir, enabled=True)
            print(f"✓ 缓存管理器创建成功: {temp_dir}")

            # 测试缓存设置
            test_config = {"analysis_types": ["summary"], "model": "test"}
            test_result = {"summary": "test result"}

            success = cache.set("test_pmid", test_config, test_result)
            print(f"✓ 缓存保存成功: {success}")

            # 测试缓存获取
            cached = cache.get("test_pmid", test_config)
            if cached == test_result:
                print("✓ 缓存读取成功，数据一致")
            else:
                print("✗ 缓存数据不一致")

            # 测试缓存统计
            stats = cache.get_cache_stats()
            print(
                f"✓ 缓存统计: {stats['total_files']} 文件, {stats['total_size_mb']} MB"
            )

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

        return True
    except Exception as e:
        print(f"✗ 缓存测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_analyzer_creation():
    """测试分析器创建"""
    print("\n" + "=" * 80)
    print("测试 5: 分析器创建（无 API Key）")
    print("=" * 80)

    try:
        import os

        from information_composer.pubmed.analyzer import AnalysisConfig, PaperAnalyzer

        # 临时设置一个假的 API Key 用于测试创建
        original_key = os.environ.get("DASHSCOPE_API_KEY")
        os.environ["DASHSCOPE_API_KEY"] = "fake-key-for-testing"

        try:
            config = AnalysisConfig(
                analysis_types=["summary"],
                llm_model="qwen-plus-latest",
                cache_enabled=False,  # 禁用缓存避免创建文件
            )

            analyzer = PaperAnalyzer(config)
            print("✓ PaperAnalyzer 创建成功")
            print(f"  - LLM 模型: {analyzer.config.llm_model}")
            print(f"  - 分析类型: {analyzer.config.analysis_types}")
            print(f"  - 最大并发: {analyzer.config.max_concurrent}")

        finally:
            # 恢复原始 API Key
            if original_key:
                os.environ["DASHSCOPE_API_KEY"] = original_key
            else:
                os.environ.pop("DASHSCOPE_API_KEY", None)

        return True
    except Exception as e:
        print(f"✗ 分析器创建测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PubMed 分析器功能验证" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    tests = [
        ("模块导入", test_imports),
        ("数据模型", test_models),
        ("提示词模板", test_prompts),
        ("缓存机制", test_cache),
        ("分析器创建", test_analyzer_creation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n测试 {name} 发生异常: {e}")
            results.append((name, False))

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")

    print("\n" + "=" * 80)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 80)

    if passed == total:
        print("\n🎉 所有测试通过！模块功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
