"""
Markdown解析器模块
负责解析和结构化Markdown文档，识别学术论文的各个章节。
"""

from dataclasses import dataclass
from enum import Enum
import logging
import re
from typing import Any


logger = logging.getLogger(__name__)


class ElementType(Enum):
    """Markdown元素类型"""

    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    QUOTE = "quote"
    SEPARATOR = "separator"
    METADATA = "metadata"


@dataclass
class MarkdownElement:
    """Markdown元素数据结构"""

    type: ElementType
    level: int = 0  # 标题级别
    content: str = ""
    metadata: dict[str, Any] | None = None
    line_number: int = 0

    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PaperSection:
    """论文章节数据结构"""

    name: str
    content: str
    elements: list[MarkdownElement]
    start_line: int
    end_line: int


class MarkdownParser:
    """Markdown解析器"""

    def __init__(self) -> None:
        """初始化解析器"""
        # 定义章节识别模式
        self.section_patterns = {
            "title": [
                r"^#\s+(.+)$",  # 一级标题作为标题
            ],
            "abstract": [
                r"^#\s*摘要\s*$",
                r"^#\s*Abstract\s*$",
                r"^#\s*SUMMARY\s*$",
                r"^##\s*摘要\s*$",
                r"^##\s*Abstract\s*$",
                r"^##\s*Summary\s*$",
            ],
            "introduction": [
                r"^#\s*引言\s*$",
                r"^#\s*Introduction\s*$",
                r"^#\s*INTRODUCTION\s*$",
                r"^#\s*背景\s*$",
                r"^#\s*Background\s*$",
                r"^##\s*引言\s*$",
                r"^##\s*Introduction\s*$",
                r"^##\s*背景\s*$",
                r"^##\s*Background\s*$",
            ],
            "related_work": [
                r"^#\s*相关工作\s*$",
                r"^#\s*Related\s+Work\s*$",
                r"^#\s*RELATED\s+WORK\s*$",
                r"^#\s*文献综述\s*$",
                r"^#\s*Literature\s+Review\s*$",
                r"^##\s*相关工作\s*$",
                r"^##\s*Related\s+Work\s*$",
                r"^##\s*文献综述\s*$",
                r"^##\s*Literature\s+Review\s*$",
            ],
            "methods": [
                r"^#\s*方法\s*$",
                r"^#\s*Methods\s*$",
                r"^#\s*METHODS\s*$",
                r"^#\s*方法论\s*$",
                r"^#\s*Methodology\s*$",
                r"^#\s*算法\s*$",
                r"^#\s*Algorithm\s*$",
                r"^##\s*方法\s*$",
                r"^##\s*Methods\s*$",
                r"^##\s*方法论\s*$",
                r"^##\s*Methodology\s*$",
                r"^##\s*算法\s*$",
                r"^##\s*Algorithm\s*$",
                r"^#\s*Methods\s+summary\s*$",  # 支持一级标题
                r"^##\s*Methods\s+summary\s*$",
            ],
            "experiments": [
                r"^#\s*实验\s*$",
                r"^#\s*Experiments\s*$",
                r"^#\s*EXPERIMENTS\s*$",
                r"^#\s*实验设计\s*$",
                r"^#\s*Experimental\s+Design\s*$",
                r"^#\s*实验结果\s*$",
                r"^#\s*Results\s*$",
                r"^##\s*实验\s*$",
                r"^##\s*Experiments\s*$",
                r"^##\s*实验设计\s*$",
                r"^##\s*Experimental\s+Design\s*$",
                r"^##\s*实验结果\s*$",
                r"^##\s*Results\s*$",
            ],
            "results": [
                r"^#\s*结果\s*$",
                r"^#\s*Results\s*$",
                r"^#\s*RESULTS\s*$",
                r"^#\s*实验结果\s*$",
                r"^#\s*Experimental\s+Results\s*$",
                r"^##\s*结果\s*$",
                r"^##\s*Results\s*$",
                r"^##\s*实验结果\s*$",
                r"^##\s*Experimental\s+Results\s*$",
            ],
            "discussion": [
                r"^#\s*讨论\s*$",
                r"^#\s*Discussion\s*$",
                r"^#\s*DISCUSSION\s*$",
                r"^#\s*分析\s*$",
                r"^#\s*Analysis\s*$",
                r"^##\s*讨论\s*$",
                r"^##\s*Discussion\s*$",
                r"^##\s*分析\s*$",
                r"^##\s*Analysis\s*$",
            ],
            "conclusion": [
                r"^#\s*结论\s*$",
                r"^#\s*Conclusion\s*$",
                r"^#\s*CONCLUSION\s*$",
                r"^#\s*总结\s*$",
                r"^#\s*Summary\s*$",
                r"^##\s*结论\s*$",
                r"^##\s*Conclusion\s*$",
                r"^##\s*总结\s*$",
                r"^##\s*Summary\s*$",
            ],
            "references": [
                r"^#\s*参考文献\s*$",
                r"^#\s*References\s*$",
                r"^#\s*REFERENCES\s*$",
                r"^#\s*Bibliography\s*$",
                r"^#\s*文献\s*$",
                r"^##\s*参考文献\s*$",
                r"^##\s*References\s*$",
                r"^##\s*Bibliography\s*$",
                r"^##\s*文献\s*$",
            ],
            "acknowledgments": [
                r"^#\s*致谢\s*$",
                r"^#\s*Acknowledgments\s*$",
                r"^#\s*ACKNOWLEDGMENTS\s*$",
                r"^#\s*Acknowledgements\s*$",
                r"^#\s*感谢\s*$",
                r"^##\s*致谢\s*$",
                r"^##\s*Acknowledgments\s*$",
                r"^##\s*Acknowledgements\s*$",
                r"^##\s*感谢\s*$",
            ],
            "appendix": [
                r"^#\s*附录\s*$",
                r"^#\s*Appendix\s*$",
                r"^#\s*APPENDIX\s*$",
                r"^#\s*Appendices\s*$",
                r"^##\s*附录\s*$",
                r"^##\s*Appendix\s*$",
                r"^##\s*Appendices\s*$",
            ],
        }
        # 需要过滤的内容模式
        self.filter_patterns = {
            "author_info": [
                r"^\*\*作者\*\*:",
                r"^\*\*Author\*\*:",
                r"^\*\*Authors\*\*:",
            ],
            "affiliation": [
                r"^\*\*单位\*\*:",
                r"^\*\*Affiliation\*\*:",
                r"^\*\*Institution\*\*:",
            ],
            "email": [
                r"^\*\*邮箱\*\*:",
                r"^\*\*Email\*\*:",
                r"^\*\*E-mail\*\*:",
            ],
            "keywords": [
                r"^\*\*关键词\*\*:",
                r"^\*\*Keywords\*\*:",
                r"^\*\*Key\s+Words\*\*:",
            ],
            "page_numbers": [
                r"^\*页码:\s*\d+-\d+\*$",
                r"^\*Page:\s*\d+-\d+\*$",
                r"^\*第\s*\d+\s*页\*$",
            ],
            "publication_info": [
                r"^\*本文发表于.*\*$",
                r"^\*Published\s+in.*\*$",
            ],
        }
        # 编译正则表达式
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """编译正则表达式模式"""
        self.compiled_section_patterns: dict[str, list[re.Pattern[str]]] = {}
        for section_name, patterns in self.section_patterns.items():
            self.compiled_section_patterns[section_name] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in patterns
            ]
        self.compiled_filter_patterns: dict[str, list[re.Pattern[str]]] = {}
        for filter_name, patterns in self.filter_patterns.items():
            self.compiled_filter_patterns[filter_name] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in patterns
            ]

    def parse(self, content: str) -> dict[str, Any]:
        """
        解析Markdown内容
        Args:
            content: Markdown文档内容
        Returns:
            解析结果字典，包含章节信息和元素列表
        Raises:
            Exception: 解析失败时抛出异常
        """
        try:
            lines = content.split("\n")
            elements = self._parse_elements(lines)
            sections = self._identify_sections(elements)
            result = {
                "sections": sections,
                "elements": elements,
                "metadata": self._extract_metadata(elements),
                "statistics": self._calculate_statistics(elements, sections),
            }
            logger.info(f"成功解析Markdown文档，识别到{len(sections)}个章节")
            return result
        except Exception as e:
            logger.error(f"Markdown解析失败: {e}")
            raise

    def _parse_elements(self, lines: list[str]) -> list[MarkdownElement]:
        """解析Markdown元素"""
        elements = []
        for i, line in enumerate(lines):
            element = self._parse_line(line, i + 1)
            if element:
                elements.append(element)
        return elements

    def _parse_line(self, line: str, line_number: int) -> MarkdownElement | None:
        """解析单行内容"""
        line = line.strip()
        if not line:
            return None
        # 标题
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            content = line.lstrip("#").strip()
            return MarkdownElement(
                type=ElementType.HEADING,
                level=level,
                content=content,
                line_number=line_number,
            )
        # 分隔符
        if re.match(r"^[-*_]{3,}$", line):
            return MarkdownElement(
                type=ElementType.SEPARATOR, content=line, line_number=line_number
            )
        # 代码块标记
        if line.startswith("```"):
            return MarkdownElement(
                type=ElementType.CODE_BLOCK, content=line, line_number=line_number
            )
        # 引用
        if line.startswith(">"):
            return MarkdownElement(
                type=ElementType.QUOTE, content=line, line_number=line_number
            )
        # 列表项
        if re.match(r"^\s*[-*+]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
            return MarkdownElement(
                type=ElementType.LIST, content=line, line_number=line_number
            )
        # 表格行
        if "|" in line and line.count("|") >= 2:
            return MarkdownElement(
                type=ElementType.TABLE, content=line, line_number=line_number
            )
        # 元数据（作者信息等）
        if self._is_metadata_line(line):
            return MarkdownElement(
                type=ElementType.METADATA, content=line, line_number=line_number
            )
        # 普通段落
        return MarkdownElement(
            type=ElementType.PARAGRAPH, content=line, line_number=line_number
        )

    def _is_metadata_line(self, line: str) -> bool:
        """判断是否为元数据行"""
        for patterns in self.compiled_filter_patterns.values():
            for pattern in patterns:
                if pattern.match(line):
                    return True
        return False

    def _identify_sections(
        self, elements: list[MarkdownElement]
    ) -> dict[str, PaperSection]:
        """识别论文章节"""
        sections: dict[str, PaperSection] = {}
        current_section: str | None = None
        current_elements: list[MarkdownElement] = []
        start_line = 0
        for element in elements:
            # 支持一级和二级标题
            if element.type == ElementType.HEADING and element.level in [1, 2]:
                # 保存当前章节
                if current_section:
                    sections[current_section] = PaperSection(
                        name=current_section,
                        content="\n".join([e.content for e in current_elements]),
                        elements=current_elements.copy(),
                        start_line=start_line,
                        end_line=element.line_number - 1,
                    )
                # 开始新章节
                section_name = self._match_section_name(element.content, element.level)
                if section_name:
                    current_section = section_name
                    current_elements = [element]
                    start_line = element.line_number
                else:
                    current_section = None
                    current_elements = []
            elif current_section:
                current_elements.append(element)
        # 保存最后一个章节
        if current_section and current_elements:
            sections[current_section] = PaperSection(
                name=current_section,
                content="\n".join([e.content for e in current_elements]),
                elements=current_elements.copy(),
                start_line=start_line,
                end_line=current_elements[-1].line_number,
            )
        return sections

    def _match_section_name(self, heading: str, level: int = 2) -> str | None:
        """匹配章节名称"""
        # 构建匹配字符串
        prefix = "#" * level
        match_string = f"{prefix} {heading}"
        for section_name, patterns in self.compiled_section_patterns.items():
            for pattern in patterns:
                if pattern.match(match_string):
                    return section_name
        return None

    def _extract_metadata(self, elements: list[MarkdownElement]) -> dict[str, Any]:
        """提取文档元数据"""
        metadata: dict[str, Any] = {}
        # 提取标题
        for element in elements:
            if element.type == ElementType.HEADING and element.level == 1:
                metadata["title"] = element.content
                break
        # 提取其他元数据
        for element in elements:
            if element.type == ElementType.METADATA:
                for filter_name, patterns in self.compiled_filter_patterns.items():
                    for pattern in patterns:
                        if pattern.match(element.content):
                            metadata[filter_name] = element.content
                            break
        return metadata

    def _calculate_statistics(
        self, elements: list[MarkdownElement], sections: dict[str, PaperSection]
    ) -> dict[str, Any]:
        """计算文档统计信息"""
        stats: dict[str, Any] = {
            "total_elements": len(elements),
            "total_sections": len(sections),
            "element_types": {},
            "section_names": list(sections.keys()),
            "total_lines": max([e.line_number for e in elements], default=0),
        }
        # 统计元素类型
        for element in elements:
            element_type = element.type.value
            stats["element_types"][element_type] = (
                stats["element_types"].get(element_type, 0) + 1
            )
        return stats

    def get_section_content(
        self, sections: dict[str, PaperSection], section_name: str
    ) -> str | None:
        """获取指定章节的内容"""
        if section_name in sections:
            return sections[section_name].content
        return None

    def filter_metadata(self, elements: list[MarkdownElement]) -> list[MarkdownElement]:
        """过滤元数据元素"""
        filtered = []
        for element in elements:
            if element.type != ElementType.METADATA:
                filtered.append(element)
        return filtered

    def get_keep_sections(self) -> list[str]:
        """获取需要保留的章节名称"""
        return [
            "title",
            "abstract",
            "introduction",
            "related_work",
            "methods",
            "experiments",
            "discussion",
            "conclusion",
        ]

    def get_filter_sections(self) -> list[str]:
        """获取需要过滤的章节名称"""
        return ["references", "acknowledgments", "appendix"]
