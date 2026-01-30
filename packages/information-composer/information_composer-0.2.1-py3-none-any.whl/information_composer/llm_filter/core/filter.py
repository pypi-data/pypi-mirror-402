"""
过滤逻辑模块
负责使用LLM直接过滤学术论文中不需要的内容，保留核心学术内容。
"""

from datetime import datetime
import logging
import os
from typing import Any

from ..llm.llm_interface import ChatMessage, LLMFactory, MessageRole


logger = logging.getLogger(__name__)


class MarkdownFilter:
    """基于LLM的Markdown过滤器"""

    def __init__(
        self, model: str = "qwen-plus-latest", provider: str = "dashscope"
    ) -> None:
        """
        初始化过滤器
        Args:
            model: 使用的LLM模型名称
            provider: LLM提供商
        """
        self.model = model
        self.provider = provider
        self.llm = LLMFactory.create(provider, model)
        # 定义过滤提示词
        self.filter_prompt = (
            "You are an expert in analyzing academic papers in Markdown format. "
            "Your task is to extract key sections such as the Title, Abstract, "
            "Results, Methods, and Discussion from a given Markdown-formatted "
            "research paper.\n\n"
            "Please follow these guidelines:\n"
            "- Extract the content of the specified sections exactly as they "
            "appear in the original text.\n"
            "- Do not modify, paraphrase, or summarize any part of the extracted "
            "content.\n"
            "- Exclude unnecessary information such as:\n"
            "  - References/Bibliography\n"
            "  - Author affiliations\n"
            "  - Acknowledgments\n"
            "  - Appendices\n"
            "  - Footnotes\n"
            "  - Page numbers\n\n"
            "Your output should only include the raw text of the requested "
            "sections (Title, Abstract, Results, Methods, Discussion) without "
            "any additional commentary or structural changes.\n"
            "If a section is missing or cannot be located, simply omit it from "
            "the output. Do not generate placeholder text.\n\n"
            "Please process the following Markdown input:"
        )

    async def filter_paper(self, content: str) -> str:
        """
        使用LLM直接过滤论文内容
        Args:
            content: 原始Markdown文档内容
        Returns:
            过滤后的Markdown文档内容
        Raises:
            Exception: 过滤失败时抛出异常
        """
        try:
            logger.info("开始使用LLM过滤论文内容")
            # 验证输入内容
            if not content or not content.strip():
                logger.warning("输入内容为空，返回空结果")
                return ""
            # 构建完整的提示词
            full_prompt = f"{self.filter_prompt}\n\n{content}"
            # 使用LLM进行过滤
            try:
                messages = [
                    ChatMessage(
                        role=MessageRole.SYSTEM,
                        content=(
                            "You are an expert in academic paper analysis "
                            "and filtering."
                        ),
                    ),
                    ChatMessage(role=MessageRole.USER, content=full_prompt),
                ]
                response = await self.llm.chat(messages)
                filtered_content = (
                    response.content if response and response.content else None
                )
                if not filtered_content or not filtered_content.strip():
                    logger.warning("LLM返回空内容，使用回退过滤")
                    return self._simple_fallback_filter(content)
                logger.info("LLM过滤完成")
            except Exception as e:
                logger.error(f"LLM过滤失败: {e}")
                # 回退到简单过滤
                return self._simple_fallback_filter(content)
            # 不再添加过滤信息元数据
            # filtered_content = self._add_filter_info(filtered_content)
            logger.info("论文内容过滤完成")
            return filtered_content
        except Exception as e:
            logger.error(f"论文过滤失败: {e}")
            # 最终回退方案
            return self._emergency_filter(content)

    def _simple_fallback_filter(self, content: str) -> str:
        """简单的回退过滤方法"""
        logger.info("使用简单回退过滤方法")
        try:
            lines = content.split("\n")
            filtered_lines = []
            skip_section = False
            found_main_content = False
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    if not skip_section:
                        filtered_lines.append("")
                    continue
                # 检查是否是需要跳过的章节
                if line_stripped.startswith("#"):
                    skip_section = self._should_skip_section_simple(line_stripped)
                    logger.debug(f"章节: {line_stripped}, 跳过: {skip_section}")
                    # 如果找到主要章节，标记为已找到主要内容
                    if not skip_section and any(
                        keyword in line_stripped.lower()
                        for keyword in [
                            "abstract",
                            "introduction",
                            "methods",
                            "results",
                            "discussion",
                            "conclusion",
                        ]
                    ):
                        found_main_content = True
                # 如果不需要跳过，则保留内容
                if not skip_section:
                    filtered_lines.append(line)
            # 如果找到了主要内容，返回过滤结果
            if found_main_content:
                return "\n".join(filtered_lines)
            else:
                # 如果没有找到主要内容，使用紧急过滤
                logger.warning("未找到主要内容，使用紧急过滤")
                return self._emergency_filter(content)
        except Exception as e:
            logger.error(f"简单回退过滤失败: {e}")
            return self._emergency_filter(content)

    def _should_skip_section_simple(self, heading_line: str) -> bool:
        """简单判断是否应该跳过某个章节"""
        skip_keywords = [
            "references",
            "bibliography",
            "acknowledgments",
            "acknowledgements",
            "appendix",
            "appendices",
            "author",
            "affiliation",
            "footnote",
            "page",
            "figure",
            "table",
            "supplementary",
        ]
        heading_lower = heading_line.lower()
        return any(keyword in heading_lower for keyword in skip_keywords)

    def _add_filter_info(self, content: str) -> str:
        """添加过滤信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filter_info = f"""
---
*本文档由 MD_LLM_Filter 自动过滤生成*
*过滤时间: {timestamp}*
*使用模型: {self.model}*
*已过滤内容: 参考文献、致谢、附录、作者信息、页码等*
"""
        return content + filter_info

    async def filter_file(self, input_path: str, output_path: str | None = None) -> str:
        """
        过滤文件
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果为None则自动生成
        Returns:
            输出文件路径
        Raises:
            Exception: 文件操作失败时抛出异常
        """
        try:
            # 读取输入文件
            with open(input_path, encoding="utf-8") as f:
                content = f.read()
            # 过滤内容
            filtered_content = await self.filter_paper(content)
            # 生成输出路径
            if output_path is None:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_filtered.md"
            # 写入输出文件
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(filtered_content)
            logger.info(f"文件过滤完成: {input_path} -> {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"文件过滤失败: {e}")
            raise

    async def batch_filter(
        self, input_files: list[str], output_dir: str | None = None
    ) -> list[str]:
        """
        批量过滤文件
        Args:
            input_files: 输入文件列表
            output_dir: 输出目录，如果为None则使用输入文件
            所在目录
        Returns:
            输出文件路径列表
        """
        output_files = []
        for input_file in input_files:
            try:
                if output_dir:
                    base_name = os.path.splitext(os.path.basename(input_file))[0]
                    output_file = os.path.join(output_dir, f"{base_name}_filtered.md")
                else:
                    output_file = None
                result = await self.filter_file(input_file, output_file)
                output_files.append(result)
            except Exception as e:
                logger.error(f"批量过滤文件失败 {input_file}: {e}")
                continue
        return output_files

    def get_filter_statistics(
        self, original_content: str, filtered_content: str
    ) -> dict[str, Any]:
        """
        获取过滤统计信息
        Args:
            original_content: 原始内容
            filtered_content: 过滤后内容
        Returns:
            统计信息字典
        """
        try:
            original_lines = len(original_content.split("\n"))
            filtered_lines = len(filtered_content.split("\n"))
            original_chars = len(original_content)
            filtered_chars = len(filtered_content)
            stats = {
                "original_lines": original_lines,
                "filtered_lines": filtered_lines,
                "lines_reduction": original_lines - filtered_lines,
                "lines_reduction_percent": round(
                    (original_lines - filtered_lines) / original_lines * 100, 2
                ),
                "original_chars": original_chars,
                "filtered_chars": filtered_chars,
                "chars_reduction": original_chars - filtered_chars,
                "chars_reduction_percent": round(
                    (original_chars - filtered_chars) / original_chars * 100, 2
                ),
                "compression_ratio": round(filtered_chars / original_chars, 3),
            }
            return stats
        except Exception as e:
            logger.error(f"统计信息计算失败: {e}")
            return {}

    def _emergency_filter(self, content: str) -> str:
        """紧急过滤方法"""
        logger.warning("使用紧急过滤方法")
        try:
            # 最简单的过滤：只保留标题和第一段
            lines = content.split("\n")
            filtered_lines = []
            # 保留第一个标题
            for line in lines:
                if line.strip().startswith("#"):
                    filtered_lines.append(line)
                    break
            # 保留第一段非空内容
            in_first_paragraph = False
            for line in lines:
                if line.strip() and not line.strip().startswith("#"):
                    if not in_first_paragraph:
                        filtered_lines.append("")
                        in_first_paragraph = True
                    filtered_lines.append(line)
                elif in_first_paragraph and not line.strip():
                    break
            result = "\n".join(filtered_lines)
            return result
        except Exception as e:
            logger.error(f"紧急过滤也失败: {e}")
            return "# 过滤失败\n\n原始内容处理出现问题，请检查输入文件。"
