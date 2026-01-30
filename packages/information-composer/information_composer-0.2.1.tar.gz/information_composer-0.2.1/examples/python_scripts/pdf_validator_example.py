#!/usr/bin/env python3
"""
PDF 验证器使用示例

展示如何在 information-composer 项目中使用 PDF 验证功能。
"""

import os
from pathlib import Path

from information_composer.pdf.validator import PDFValidator


def basic_usage_example():
    """基本使用示例"""
    print("=== PDF 验证器基本使用示例 ===\n")

    # 创建验证器实例
    validator = PDFValidator(verbose=True)

    # 示例：验证单个文件（如果存在）
    sample_pdf = "sample.pdf"
    if os.path.exists(sample_pdf):
        print(f"验证文件: {sample_pdf}")
        is_valid, error_msg = validator.validate_single_pdf(sample_pdf)

        if is_valid:
            print("✅ 文件验证通过")
        else:
            print(f"❌ 文件验证失败: {error_msg}")
    else:
        print(f"示例文件 {sample_pdf} 不存在，跳过单文件验证")

    print()


def directory_validation_example():
    """目录验证示例"""
    print("=== 目录验证示例 ===\n")

    # 创建验证器实例
    validator = PDFValidator(verbose=True)

    # 示例：验证当前目录中的PDF文件
    current_dir = "."
    print(f"验证目录: {current_dir}")

    # 重置统计信息
    validator.reset_stats()

    # 验证目录
    validator.validate_directory(current_dir, recursive=False)

    # 显示统计信息
    stats = validator.get_validation_stats()
    print("\n验证统计:")
    print(f"  总文件数: {stats.total_files}")
    print(f"  有效PDF: {stats.valid_files}")
    print(f"  无效PDF: {stats.invalid_files}")
    print(f"  成功率: {stats.success_rate:.1f}%")

    print()


def batch_validation_example():
    """批量验证示例"""
    print("=== 批量验证示例 ===\n")

    # 创建验证器实例
    validator = PDFValidator(verbose=True)

    # 示例文件列表（这些文件可能不存在，仅作演示）
    test_files = ["file1.pdf", "file2.pdf", "file3.pdf"]

    print("批量验证文件列表:")
    for file in test_files:
        print(f"  - {file}")

    # 重置统计信息
    validator.reset_stats()

    # 验证文件列表
    validator.validate_files(test_files)

    # 显示统计信息
    stats = validator.get_validation_stats()
    print("\n批量验证统计:")
    print(f"  总文件数: {stats.total_files}")
    print(f"  有效PDF: {stats.valid_files}")
    print(f"  无效PDF: {stats.invalid_files}")
    print(f"  成功率: {stats.success_rate:.1f}%")

    print()


def cli_usage_example():
    """CLI 使用示例"""
    print("=== CLI 使用示例 ===\n")

    print("1. 验证单个文件:")
    print("   pdf-validator file.pdf")
    print()

    print("2. 验证多个文件:")
    print("   pdf-validator file1.pdf file2.pdf file3.pdf")
    print()

    print("3. 验证目录中的所有PDF:")
    print("   pdf-validator -d /path/to/directory")
    print()

    print("4. 递归验证目录:")
    print("   pdf-validator -d /path/to/directory -r")
    print()

    print("5. 详细输出:")
    print("   pdf-validator -d /path/to/directory -v")
    print()

    print("6. JSON格式输出:")
    print("   pdf-validator -d /path/to/directory --json")
    print()

    print("7. 只显示统计信息:")
    print("   pdf-validator -d /path/to/directory --stats-only")
    print()


def integration_example():
    """集成示例"""
    print("=== 与其他模块集成示例 ===\n")

    print("PDF 验证器已成功集成到 information-composer 项目中！")
    print()
    print("主要特性:")
    print("✅ PDF 文件格式验证")
    print("✅ 批量文件处理")
    print("✅ 目录递归搜索")
    print("✅ 详细错误报告")
    print("✅ 统计信息输出")
    print("✅ JSON 格式输出")
    print("✅ CLI 命令行工具")
    print()

    print("项目结构:")
    print("information_composer/")
    print("├── pdf/                    # PDF 处理模块")
    print("│   ├── validator.py       # PDF 验证器")
    print("│   └── cli/               # CLI 工具")
    print("│       └── main.py        # 命令行入口")
    print("├── llm_filter/            # MD_LLM_Filter 集成")
    print("├── core/                  # 核心功能")
    print("├── pubmed/                # PubMed 集成")
    print("└── markdown/              # Markdown 处理")
    print()


def create_sample_pdf():
    """创建示例PDF文件（用于测试）"""
    print("=== 创建示例PDF文件 ===\n")

    try:
        # 尝试创建一个简单的PDF文件用于测试
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        sample_pdf = "sample.pdf"
        c = canvas.Canvas(sample_pdf, pagesize=letter)
        c.drawString(100, 750, "这是一个示例PDF文件")
        c.drawString(100, 700, "用于测试PDF验证器功能")
        c.save()

        print(f"✅ 创建示例PDF文件: {sample_pdf}")
        return True

    except ImportError:
        print("❌ 缺少 reportlab 库，无法创建示例PDF文件")
        print("   可以手动创建一个PDF文件进行测试")
        return False
    except Exception as e:
        print(f"❌ 创建PDF文件失败: {e}")
        return False


def main():
    """主函数"""
    print("PDF 验证器集成示例")
    print("=" * 50)

    # 基本使用示例
    basic_usage_example()

    # 目录验证示例
    directory_validation_example()

    # 批量验证示例
    batch_validation_example()

    # CLI 使用示例
    cli_usage_example()

    # 集成示例
    integration_example()

    # 尝试创建示例PDF
    if create_sample_pdf():
        print("\n现在可以测试PDF验证功能了！")
        print("运行: pdf-validator sample.pdf")

    print("\n🎉 PDF 验证器已成功集成到 information-composer 项目中！")
    print("现在您可以使用 pdf-validator 命令来验证PDF文件了。")


if __name__ == "__main__":
    main()
