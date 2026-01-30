#!/usr/bin/env python3
"""
MD_LLM_Filter 使用示例

展示如何在 information-composer 项目中使用 MD_LLM_Filter 功能。
"""

import asyncio
from pathlib import Path

from information_composer.llm_filter.core.filter import MarkdownFilter
from information_composer.llm_filter.utils.text_processing import (
    get_document_stats,
)


async def basic_usage_example():
    """基本使用示例"""
    print("=== MD_LLM_Filter 基本使用示例 ===\n")

    # 创建过滤器实例
    filter_obj = MarkdownFilter(model="qwen-plus-latest")

    # 示例 Markdown 内容
    sample_content = """# 基于深度学习的图像识别研究

## 摘要

本文提出了一种基于深度学习的图像识别方法，该方法在多个数据集上取得了优异的性能。我们使用了卷积神经网络架构，并结合了数据增强技术来提高模型的泛化能力。

## 引言

图像识别是计算机视觉领域的重要研究方向...

## 方法

我们提出的方法包括以下步骤：
1. 数据预处理
2. 模型设计
3. 训练策略
4. 评估指标

## 结果

在CIFAR-10数据集上，我们的方法达到了95.2%的准确率...

## 讨论

实验结果表明，我们提出的方法在多个方面都有显著改进...

## 结论

本文提出的基于深度学习的图像识别方法在多个数据集上都取得了优异的性能...

## 参考文献

[1] LeCun, Y., et al. (2015). Deep learning. Nature, 521(7553),
436-444.
[2] Krizhevsky, A., et al. (2012). ImageNet classification with deep
convolutional neural networks...

## 致谢

感谢所有参与实验的同事和提供数据支持的研究机构...

## 附录

详细的实验参数设置如下...
"""

    print("原始内容统计:")
    original_stats = get_document_stats(sample_content)
    print(f"  行数: {original_stats['total_lines']}")
    print(f"  字符数: {original_stats['characters']}")
    print(f"  单词数: {original_stats['words']}")
    print()

    print("正在使用 LLM 过滤内容...")
    try:
        # 过滤内容
        filtered_content = await filter_obj.filter_paper(sample_content)

        print("过滤后内容统计:")
        filtered_stats = get_document_stats(filtered_content)
        print(f"  行数: {filtered_stats['total_lines']}")
        print(f"  字符数: {filtered_stats['characters']}")
        print(f"  单词数: {filtered_stats['words']}")
        print()

        # 显示过滤统计
        filter_stats = filter_obj.get_filter_statistics(
            sample_content, filtered_content
        )
        print("过滤效果:")
        print(
            "  行数减少: "
            f"{filter_stats['lines_reduction']} "
            f"({filter_stats['lines_reduction_percent']:.1f}%)"
        )
        print(
            "  字符数减少: "
            f"{filter_stats['chars_reduction']} "
            f"({filter_stats['chars_reduction_percent']:.1f}%)"
        )
        print(f"  压缩比: {filter_stats['compression_ratio']:.3f}")
        print()

        print("过滤后的内容预览:")
        print("-" * 50)
        print(
            filtered_content[:500] + "..."
            if len(filtered_content) > 500
            else filtered_content
        )
        print("-" * 50)

    except Exception as e:
        print(f"过滤过程中出现错误: {e}")
        print("这通常是因为没有配置 DashScope API 密钥")
        print("请设置环境变量 DASHSCOPE_API_KEY")


def cli_usage_example():
    """CLI 使用示例"""
    print("\n=== CLI 使用示例 ===\n")

    print("1. 过滤单个文件:")
    print("   md-llm-filter -i paper.md")
    print()

    print("2. 过滤单个文件并指定输出:")
    print("   md-llm-filter -i paper.md -o filtered_paper.md")
    print()

    print("3. 批量过滤目录:")
    print("   md-llm-filter -m papers/ -o filtered_papers/")
    print()

    print("4. 显示统计信息:")
    print("   md-llm-filter -i paper.md --stats")
    print()

    print("5. 详细输出模式:")
    print("   md-llm-filter -m papers/ --verbose")
    print()

    print("6. 指定模型:")
    print("   md-llm-filter -i paper.md --model qwen-plus-latest")
    print()


def integration_example():
    """集成示例"""
    print("\n=== 与其他模块集成示例 ===\n")

    print("MD_LLM_Filter 已成功集成到 information-composer 项目中！")
    print()
    print("主要特性:")
    print("✅ 基于 LLM 的智能过滤")
    print("✅ 支持 DashScope 模型")
    print("✅ 保留核心学术内容")
    print("✅ 过滤冗余信息")
    print("✅ 支持批量处理")
    print("✅ 提供统计信息")
    print("✅ 支持多种输出格式")
    print()

    print("项目结构:")
    print("information_composer/")
    print("├── llm_filter/           # MD_LLM_Filter 集成模块")
    print("│   ├── core/            # 核心功能")
    print("│   ├── llm/             # LLM 接口")
    print("│   ├── utils/           # 工具函数")
    print("│   └── cli/             # 命令行工具")
    print("├── core/                # 原有核心模块")
    print("├── pubmed/              # PubMed 集成")
    print("└── markdown/            # Markdown 处理")
    print()


async def main():
    """主函数"""
    print("MD_LLM_Filter 集成示例")
    print("=" * 50)

    # 基本使用示例
    await basic_usage_example()

    # CLI 使用示例
    cli_usage_example()

    # 集成示例
    integration_example()

    print("\n🎉 MD_LLM_Filter 已成功集成到 information-composer 项目中！")
    print("现在您可以使用 md-llm-filter 命令来过滤 Markdown 学术论文了。")


if __name__ == "__main__":
    asyncio.run(main())
