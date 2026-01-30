#!/usr/bin/env python3
"""
MD_LLM_Filter CLI 主程序
支持以下功能：
- 单文件过滤：-i 参数
- 目录批量过滤：-m 参数
- 输出指定：-o 参数
- 自动添加_filtered后缀
"""

import argparse
import asyncio
import logging
from pathlib import Path
import sys

from tqdm import tqdm

from ..core.filter import MarkdownFilter
from ..utils.text_processing import get_document_stats


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_markdown_files(directory: Path) -> list[Path]:
    """
    在目录中查找所有markdown文件
    Args:
        directory: 目录路径
    Returns:
        markdown文件路径列表
    """
    markdown_files = []
    # 支持的markdown文件扩展名
    markdown_extensions = {".md", ".markdown", ".mdown", ".mkdn", ".mkd"}
    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in markdown_extensions:
                markdown_files.append(file_path)
    except Exception as e:
        logger.error(f"扫描目录失败 {directory}: {e}")
    return sorted(markdown_files)


def create_output_path(input_path: Path, output_dir: Path | None = None) -> Path:
    """
    创建输出文件路径
    Args:
        input_path: 输入文件路径
        output_dir: 输出目录，如果为None则使用输入文件所在目录
    Returns:
        输出文件路径
    """
    if output_dir:
        # 如果指定了输出目录，保持相对路径结构
        output_file = output_dir / f"{input_path.stem}_filtered.md"
    else:
        # 在输入文件所在目录创建_filtered文件
        output_file = input_path.parent / f"{input_path.stem}_filtered.md"
    return output_file


async def process_single_file(
    input_file: Path,
    output_file: Path | None = None,
    filter_obj: MarkdownFilter | None = None,
    show_stats: bool = False,
    verbose: bool = False,
) -> bool:
    """
    处理单个文件
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径，如果为None则自动生成
        filter_obj: 过滤器对象
        show_stats: 是否显示统计信息
        verbose: 是否详细输出
    Returns:
        处理是否成功
    """
    try:
        if verbose:
            logger.info(f"开始处理文件: {input_file}")
        # 生成输出文件路径
        if output_file is None:
            output_file = create_output_path(input_file)
        # 读取输入文件
        with open(input_file, encoding="utf-8") as f:
            content = f.read()
        # 显示原始统计信息
        if show_stats:
            original_stats = get_document_stats(content)
            print(f"\n📄 文件: {input_file.name}")
            print(f"   原始行数: {original_stats['total_lines']:,}")
            print(f"   原始字符数: {original_stats['characters']:,}")
            print(f"   原始单词数: {original_stats['words']:,}")
        # 执行过滤
        if verbose:
            logger.info("正在过滤内容...")
        if filter_obj is None:
            filter_obj = MarkdownFilter()
        filtered_content = await filter_obj.filter_paper(content)
        # 保存输出文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(filtered_content)
        if verbose:
            logger.info(f"过滤完成: {output_file}")
        # 显示过滤后统计信息
        if show_stats:
            filtered_stats = get_document_stats(filtered_content)
            filter_stats = filter_obj.get_filter_statistics(content, filtered_content)
            print(f"   过滤后行数: {filtered_stats['total_lines']:,}")
            print(f"   过滤后字符数: {filtered_stats['characters']:,}")
            print(f"   过滤后单词数: {filtered_stats['words']:,}")
            print(
                "   行数减少: "
                f"{filter_stats['lines_reduction']:,} "
                f"({filter_stats['lines_reduction_percent']:.1f}%)"
            )
            print(
                "   字符数减少: "
                f"{filter_stats['chars_reduction']:,} "
                f"({filter_stats['chars_reduction_percent']:.1f}%)"
            )
            print(f"   压缩比: {filter_stats['compression_ratio']:.3f}")
        return True
    except Exception as e:
        logger.error(f"处理文件失败 {input_file}: {e}")
        if verbose:
            logger.exception("详细错误信息:")
        return False


async def process_directory(
    input_dir: Path,
    output_dir: Path | None = None,
    filter_obj: MarkdownFilter | None = None,
    show_stats: bool = False,
    verbose: bool = False,
) -> int:
    """
    处理目录中的所有markdown文件
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径，如果为None则使用输入目录
        filter_obj: 过滤器对象
        show_stats: 是否显示统计信息
        verbose: 是否详细输出
    Returns:
        成功处理的文件数量
    """
    try:
        # 查找所有markdown文件
        markdown_files = find_markdown_files(input_dir)
        if not markdown_files:
            logger.warning(f"在目录 {input_dir} 中未找到markdown文件")
            return 0
        logger.info(f"找到 {len(markdown_files)} 个markdown文件")
        # 创建输出目录
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        # 处理每个文件
        success_count = 0
        # 创建进度条
        progress_bar = tqdm(
            markdown_files,
            desc="处理文件",
            unit="文件",
            disable=verbose,  # 如果verbose模式开启，禁用进度条
        )
        for input_file in progress_bar:
            # 更新进度条描述
            progress_bar.set_description(f"处理 {input_file.name}")
            if verbose:
                logger.info(f"处理文件: {input_file.name}")
            # 计算输出文件路径
            if output_dir:
                # 保持相对路径结构
                relative_path = input_file.relative_to(input_dir)
                output_file = output_dir / f"{relative_path.stem}_filtered.md"
                # 确保输出目录存在
                output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_file = None
            # 处理文件
            success = await process_single_file(
                input_file, output_file, filter_obj, show_stats, verbose
            )
            if success:
                success_count += 1
                if not verbose:
                    progress_bar.set_postfix(
                        {
                            "成功": success_count,
                            "失败": len(markdown_files) - success_count,
                        }
                    )
            else:
                if not verbose:
                    progress_bar.set_postfix(
                        {
                            "成功": success_count,
                            "失败": len(markdown_files) - success_count,
                        }
                    )
        # 关闭进度条
        progress_bar.close()
        return success_count
    except Exception as e:
        logger.error(f"处理目录失败 {input_dir}: {e}")
        if verbose:
            logger.exception("详细错误信息:")
        return 0


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="MD_LLM_Filter - 基于LLM的Markdown学术论文过滤器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 过滤单个文件 (自动添加_filtered后缀)
  md-llm-filter -i paper.md
  # 过滤单个文件并指定输出文件
  md-llm-filter -i paper.md -o filtered_paper.md
  # 批量过滤目录中的所有markdown文件 (显示进度条)
  md-llm-filter -m papers/ -o filtered_papers/
  # 显示统计信息
  md-llm-filter -i paper.md --stats
  # 详细输出 (禁用进度条)
  md-llm-filter -m papers/ --verbose
  # 批量处理并显示统计信息
  md-llm-filter -m papers/ -o filtered_papers/ --stats
        """,
    )
    # 输入参数组
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-i", "--input-file", type=Path, help="输入Markdown文件路径"
    )
    input_group.add_argument(
        "-m", "--input-dir", type=Path, help="输入目录路径 (批量处理所有markdown文件)"
    )
    # 输出参数
    parser.add_argument("-o", "--output", type=Path, help="输出文件路径或目录路径")
    # 其他参数
    parser.add_argument("--stats", action="store_true", help="显示过滤统计信息")
    parser.add_argument(
        "--model",
        default="qwen-plus-latest",
        help="使用的LLM模型 (默认: qwen-plus-latest)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出模式")
    args = parser.parse_args()
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    # 验证输入参数
    if args.input_file:
        if not args.input_file.exists():
            logger.error(f"输入文件不存在: {args.input_file}")
            sys.exit(1)
        if not args.input_file.is_file():
            logger.error(f"输入路径不是文件: {args.input_file}")
            sys.exit(1)
    elif args.input_dir:
        if not args.input_dir.exists():
            logger.error(f"输入目录不存在: {args.input_dir}")
            sys.exit(1)
        if not args.input_dir.is_dir():
            logger.error(f"输入路径不是目录: {args.input_dir}")
            sys.exit(1)
    # 验证输出参数
    if args.output:
        if args.input_file and args.output.is_dir():
            logger.error("当输入是文件时，输出不能是目录")
            sys.exit(1)
        if args.input_dir and args.output.is_file():
            logger.error("当输入是目录时，输出不能是文件")
            sys.exit(1)
    try:
        # 创建过滤器
        filter_obj = MarkdownFilter(model=args.model)
        # 执行处理
        if args.input_file:
            # 单文件处理
            success = asyncio.run(
                process_single_file(
                    args.input_file, args.output, filter_obj, args.stats, args.verbose
                )
            )
            if success:
                output_path = args.output or create_output_path(args.input_file)
                print("\n✅ 处理完成！")
                print(f"📁 输入文件: {args.input_file}")
                print(f"📁 输出文件: {output_path}")
            else:
                logger.error("文件处理失败")
                sys.exit(1)
        elif args.input_dir:
            # 目录批量处理
            success_count = asyncio.run(
                process_directory(
                    args.input_dir, args.output, filter_obj, args.stats, args.verbose
                )
            )
            print("\n✅ 批量处理完成！")
            print(f"📁 输入目录: {args.input_dir}")
            if args.output:
                print(f"📁 输出目录: {args.output}")
            print(f"📊 成功处理: {success_count} 个文件")
            if success_count == 0:
                logger.error("没有文件被成功处理")
                sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"处理失败: {e}")
        if args.verbose:
            logger.exception("详细错误信息:")
        sys.exit(1)


if __name__ == "__main__":
    main()
