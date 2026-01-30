"""
PubMed Analyzer 快速测试脚本

用于验证 Ollama 和 OpenAI 集成是否正常工作。
"""

import asyncio
import logging

from information_composer.pubmed.analyzer import (
    AnalysisConfig,
    PaperAnalyzer,
    PaperInput,
    create_llm,
)


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_llm_creation():
    """测试 LLM 创建功能"""
    logger.info("=" * 80)
    logger.info("测试 LLM 创建功能")
    logger.info("=" * 80)

    # 测试 DashScope
    try:
        llm_dashscope = create_llm(provider="dashscope", model="qwen-plus-latest")
        logger.info("✓ DashScope LLM 创建成功")
    except Exception as e:
        logger.warning(f"✗ DashScope LLM 创建失败: {e}")

    # 测试 Ollama
    try:
        llm_ollama = create_llm(
            provider="ollama", model="qwen2.5:latest", base_url="http://localhost:11434"
        )
        logger.info("✓ Ollama LLM 创建成功")
    except Exception as e:
        logger.warning(f"✗ Ollama LLM 创建失败: {e}")

    # 测试 OpenAI
    try:
        llm_openai = create_llm(provider="openai", model="gpt-4o-mini")
        logger.info("✓ OpenAI LLM 创建成功")
    except Exception as e:
        logger.warning(f"✗ OpenAI LLM 创建失败: {e}")


async def test_analyzer_config():
    """测试分析器配置"""
    logger.info("\n" + "=" * 80)
    logger.info("测试分析器配置")
    logger.info("=" * 80)

    # 测试 Ollama 配置
    try:
        config_ollama = AnalysisConfig(
            analysis_types=["summary"],
            llm_provider="ollama",
            llm_model="qwen2.5:latest",
            llm_base_url="http://localhost:11434",
        )
        logger.info(f"✓ Ollama 配置创建成功: {config_ollama.llm_provider}")
    except Exception as e:
        logger.error(f"✗ Ollama 配置创建失败: {e}")

    # 测试 OpenAI 配置
    try:
        config_openai = AnalysisConfig(
            analysis_types=["summary"],
            llm_provider="openai",
            llm_model="gpt-4o-mini",
        )
        logger.info(f"✓ OpenAI 配置创建成功: {config_openai.llm_provider}")
    except Exception as e:
        logger.error(f"✗ OpenAI 配置创建失败: {e}")

    # 测试无效配置
    try:
        config_invalid = AnalysisConfig(
            analysis_types=["summary"],
            llm_provider="invalid_provider",  # type: ignore
        )
        logger.error("✗ 应该拒绝无效的提供商")
    except ValueError as e:
        logger.info(f"✓ 正确拒绝无效提供商: {e}")


async def test_simple_analysis():
    """测试简单的论文分析（需要 Ollama 服务运行）"""
    logger.info("\n" + "=" * 80)
    logger.info("测试简单论文分析（Ollama）")
    logger.info("=" * 80)

    try:
        # 创建配置
        config = AnalysisConfig(
            analysis_types=["summary"],
            llm_provider="ollama",
            llm_model="qwen2.5:latest",
            llm_base_url="http://localhost:11434",
            cache_enabled=False,  # 禁用缓存以便测试
        )

        # 创建分析器
        analyzer = PaperAnalyzer(config)
        logger.info("✓ 分析器创建成功")

        # 准备测试数据
        paper = PaperInput(
            pmid="test001",
            title="A Simple Test Paper",
            abstract="This is a simple test abstract for testing purposes. It contains minimal information.",
        )

        # 执行分析
        logger.info("开始执行分析...")
        result = await analyzer.analyze_paper(paper)

        logger.info("✓ 分析完成")
        logger.info(f"  标题: {result.title}")
        logger.info(f"  PMID: {result.pmid}")
        if result.summary:
            logger.info(f"  主要发现数量: {len(result.summary.main_findings)}")
            logger.info(f"  创新点数量: {len(result.summary.innovations)}")
        logger.info(f"  处理时间: {result.processing_metadata.processing_time:.2f}秒")

    except Exception as e:
        logger.warning(f"✗ 分析失败（可能 Ollama 服务未运行）: {e}")
        logger.warning("  提示: 请确保 Ollama 服务已启动并且已下载 qwen2.5:latest 模型")
        logger.warning("  启动服务: ollama serve")
        logger.warning("  下载模型: ollama pull qwen2.5:latest")


async def main():
    """主函数"""
    logger.info("\n" + "=" * 80)
    logger.info("PubMed Analyzer - LLM 集成测试")
    logger.info("=" * 80 + "\n")

    # 运行测试
    await test_llm_creation()
    await test_analyzer_config()
    await test_simple_analysis()

    logger.info("\n" + "=" * 80)
    logger.info("测试完成！")
    logger.info("=" * 80)
    logger.info("\n下一步：")
    logger.info("1. 如需使用 Ollama，请确保服务运行：ollama serve")
    logger.info("2. 如需使用 OpenAI，请设置 API Key：export OPENAI_API_KEY='...'")
    logger.info("3. 运行完整示例：")
    logger.info("   - python examples/python_scripts/pubmed_analyzer_ollama_example.py")
    logger.info("   - python examples/python_scripts/pubmed_analyzer_openai_example.py")


if __name__ == "__main__":
    asyncio.run(main())
