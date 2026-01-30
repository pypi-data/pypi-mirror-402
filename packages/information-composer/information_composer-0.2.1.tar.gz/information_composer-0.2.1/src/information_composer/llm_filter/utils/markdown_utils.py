"""
Markdown工具函数模块
提供Markdown文档处理的实用工具函数。
"""

import logging
import re
from typing import Any


logger = logging.getLogger(__name__)


def clean_markdown(content: str) -> str:
    """
    清理Markdown内容
    Args:
        content: 原始Markdown内容
    Returns:
        清理后的内容
    """
    # 移除多余的空行
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)
    # 移除行尾空格
    lines = [line.rstrip() for line in content.split("\n")]
    # 移除文档开头和结尾的空行
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def extract_headings(content: str) -> list[dict[str, Any]]:
    """
    提取Markdown文档中的所有标题
    Args:
        content: Markdown内容
    Returns:
        标题列表，每个标题包含level、text、line_number
    """
    headings = []
    lines = content.split("\n")
    for i, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({"level": level, "text": text, "line_number": i + 1})
    return headings


def extract_links(content: str) -> list[dict[str, str]]:
    """
    提取Markdown文档中的所有链接
    Args:
        content: Markdown内容
    Returns:
        链接列表，每个链接包含text、url、title
    """
    links = []
    # 内联链接 [text](url "title")
    inline_pattern = r'\[([^\]]+)\]\(([^)]+?)(?:\s+"([^"]*)")?\)'
    for match in re.finditer(inline_pattern, content):
        links.append(
            {
                "text": match.group(1),
                "url": match.group(2).strip(),
                "title": match.group(3) or "",
                "type": "inline",
            }
        )
    # 引用链接 [text][ref]
    ref_pattern = r"\[([^\]]+)\]\[([^\]]*)\]"
    for match in re.finditer(ref_pattern, content):
        links.append(
            {
                "text": match.group(1),
                "ref": match.group(2) or match.group(1),
                "type": "reference",
            }
        )
    return links


def extract_images(content: str) -> list[dict[str, str]]:
    """
    提取Markdown文档中的所有图片
    Args:
        content: Markdown内容
    Returns:
        图片列表，每个图片包含alt、src、title
    """
    images = []
    # 图片语法 ![alt](src "title")
    pattern = r'!\[([^\]]*)\]\(([^)]+?)(?:\s+"([^"]*)")?\)'
    for match in re.finditer(pattern, content):
        images.append(
            {
                "alt": match.group(1),
                "src": match.group(2).strip(),
                "title": match.group(3) or "",
            }
        )
    return images


def extract_code_blocks(content: str) -> list[dict[str, str]]:
    """
    提取Markdown文档中的所有代码块
    Args:
        content: Markdown内容
    Returns:
        代码块列表，每个代码块包含language、code
    """
    code_blocks = []
    # 围栏代码块 ```language\ncode\n```
    pattern = r"```(\w*)\n(.*?)\n```"
    for match in re.finditer(pattern, content, re.DOTALL):
        code_blocks.append(
            {"language": match.group(1) or "text", "code": match.group(2)}
        )
    return code_blocks


def extract_tables(content: str) -> list[dict[str, Any]]:
    """
    提取Markdown文档中的所有表格
    Args:
        content: Markdown内容
    Returns:
        表格列表，每个表格包含headers、rows
    """
    tables = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 检查是否是表格行
        if "|" in line and line.count("|") >= 2:
            table_lines = []
            # 收集表格行
            while i < len(lines) and "|" in lines[i] and lines[i].count("|") >= 2:
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:  # 至少要有标题行和数据行
                # 解析表格
                headers = [cell.strip() for cell in table_lines[0].split("|")[1:-1]]
                rows = []
                # 跳过分隔行（如果存在）
                data_start = 1
                if len(table_lines) > 1 and re.match(
                    r"^\|[\s\-\|:]+\|$", table_lines[1]
                ):
                    data_start = 2
                # 解析数据行
                for j in range(data_start, len(table_lines)):
                    row = [cell.strip() for cell in table_lines[j].split("|")[1:-1]]
                    if len(row) == len(headers):
                        rows.append(row)
                tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def count_words(content: str) -> int:
    """
    统计Markdown文档中的单词数
    Args:
        content: Markdown内容
    Returns:
        单词数
    """
    # 移除Markdown语法
    text = re.sub(r"#{1,6}\s+", "", content)  # 标题
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # 粗体
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # 斜体
    text = re.sub(r"`(.*?)`", r"\1", text)  # 行内代码
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # 链接
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)  # 图片
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)  # 代码块
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)  # 列表
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)  # 有序列表
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)  # 引用
    text = re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.MULTILINE)  # 表格
    # 统计单词
    words = re.findall(r"\b\w+\b", text)
    return len(words)


def count_characters(content: str) -> int:
    """
    统计Markdown文档中的字符数
    Args:
        content: Markdown内容
    Returns:
        字符数（不包括空格和换行）
    """
    # 移除空格和换行
    text = re.sub(r"\s", "", content)
    return len(text)


def get_document_stats(content: str) -> dict[str, int]:
    """
    获取文档统计信息
    Args:
        content: Markdown内容
    Returns:
        统计信息字典
    """
    lines = content.split("\n")
    stats = {
        "total_lines": len(lines),
        "non_empty_lines": len([line for line in lines if line.strip()]),
        "words": count_words(content),
        "characters": count_characters(content),
        "headings": len(extract_headings(content)),
        "links": len(extract_links(content)),
        "images": len(extract_images(content)),
        "code_blocks": len(extract_code_blocks(content)),
        "tables": len(extract_tables(content)),
    }
    return stats


def format_markdown(
    content: str, max_line_length: int = 80, preserve_formatting: bool = True
) -> str:
    """
    格式化Markdown文档
    Args:
        content: 原始内容
        max_line_length: 最大行长度
        preserve_formatting: 是否保持原有格式
    Returns:
        格式化后的内容
    """
    if not preserve_formatting:
        return clean_markdown(content)
    lines = content.split("\n")
    formatted_lines = []
    for line in lines:
        if len(line) <= max_line_length or line.strip().startswith("#"):
            # 标题或短行保持原样
            formatted_lines.append(line)
        elif line.strip().startswith("|"):
            # 表格行保持原样
            formatted_lines.append(line)
        elif line.strip().startswith("```"):
            # 代码块标记保持原样
            formatted_lines.append(line)
        else:
            # 长行进行换行处理
            if len(line.strip()) > max_line_length:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) <= max_line_length:
                        current_line += word + " "
                    else:
                        if current_line:
                            formatted_lines.append(current_line.rstrip())
                        current_line = word + " "
                if current_line:
                    formatted_lines.append(current_line.rstrip())
            else:
                formatted_lines.append(line)
    return "\n".join(formatted_lines)


def validate_markdown(content: str) -> dict[str, Any]:
    """
    验证Markdown文档的语法
    Args:
        content: Markdown内容
    Returns:
        验证结果字典
    """
    issues = []
    warnings = []
    # _lines = content.split("\n")  # Unused variable
    # 检查标题层级
    headings = extract_headings(content)
    for i, heading in enumerate(headings):
        if i > 0 and heading["level"] > headings[i - 1]["level"] + 1:
            warnings.append(f"标题层级跳跃: 第{heading['line_number']}行")
    # 检查链接
    links = extract_links(content)
    for link in links:
        if link["type"] == "reference" and not link.get("url"):
            issues.append(f"未定义的引用链接: {link['text']}")
    # 检查图片
    images = extract_images(content)
    for img in images:
        if not img["src"]:
            issues.append(f"图片缺少源地址: {img['alt']}")
    # 检查代码块
    code_blocks = extract_code_blocks(content)
    for block in code_blocks:
        if not block["code"].strip():
            warnings.append("发现空的代码块")
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "total_issues": len(issues),
        "total_warnings": len(warnings),
    }
