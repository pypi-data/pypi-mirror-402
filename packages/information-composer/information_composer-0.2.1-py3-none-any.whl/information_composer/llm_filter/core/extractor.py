"""
内容提取器模块
使用LLM智能提取学术论文的核心内容，包括标题、摘要、方法、结果、讨论等。
"""

import asyncio
import json
import logging
from typing import Any

from ..llm.dashscope_client import create_dashscope_client
from ..llm.llm_interface import ChatMessage, MessageRole
from .parser import MarkdownParser, PaperSection


logger = logging.getLogger(__name__)


class ContentExtractor:
    """内容提取器"""

    def __init__(self, model: str = "qwen-plus-latest") -> None:
        """
        初始化内容提取器
        Args:
            model: 使用的LLM模型名称
        """
        self.parser = MarkdownParser()
        self.llm_client = create_dashscope_client(model=model)
        self.model = model
        # 定义提取模式
        self.extraction_schema = {
            "title": {"description": "论文标题", "type": "string", "required": True},
            "abstract": {"description": "论文摘要", "type": "string", "required": True},
            "methods": {
                "description": "研究方法或方法论",
                "type": "string",
                "required": True,
            },
            "results": {
                "description": "实验结果或主要发现",
                "type": "string",
                "required": True,
            },
            "discussion": {
                "description": "讨论和分析",
                "type": "string",
                "required": False,
            },
            "conclusion": {"description": "结论", "type": "string", "required": False},
        }

    async def extract_paper_content(self, content: str) -> dict[str, str]:
        """
        提取论文内容
        Args:
            content: Markdown文档内容
        Returns:
            提取的内容字典
        Raises:
            Exception: 提取失败时抛出异常
        """
        try:
            # 1. 解析Markdown结构
            parsed_result = self.parser.parse(content)
            sections = parsed_result["sections"]
            # 2. 使用LLM智能提取
            extracted = await self._llm_extract(content, sections)
            # 3. 后处理和验证
            validated = self._validate_extraction(extracted)
            logger.info(f"成功提取论文内容，包含{len(validated)}个字段")
            return validated
        except Exception as e:
            logger.error(f"内容提取失败: {e}")
            raise

    async def _llm_extract(
        self, content: str, sections: dict[str, PaperSection]
    ) -> dict[str, str]:
        """使用LLM提取内容"""
        max_retries = 3
        retry_delay = 1.0
        for attempt in range(max_retries):
            try:
                # 构建提取提示
                prompt = self._build_extraction_prompt(content, sections)
                # 调用LLM
                messages = [
                    ChatMessage(
                        role=MessageRole.SYSTEM,
                        content="你是一个专业的学术论文分析助手，擅长从学术论文中提取核心内容。",
                    ),
                    ChatMessage(role=MessageRole.USER, content=prompt),
                ]
                response = await self.llm_client.chat(messages)
                # 解析响应
                extracted = self._parse_llm_response(response.content)
                # 验证提取结果
                if self._validate_extraction_result(extracted):
                    return extracted
                else:
                    logger.warning(
                        f"LLM提取结果验证失败，尝试 {attempt + 1}/{max_retries}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
            except Exception as e:
                logger.error(f"LLM提取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error("LLM提取最终失败，回退到基于规则的提取")
                    break
        # 回退到基于规则的提取
        return self._fallback_extraction(sections)

    def _build_extraction_prompt(
        self, content: str, sections: dict[str, PaperSection]
    ) -> str:
        """构建提取提示"""
        # 限制内容长度，避免超出模型限制
        max_length = 8000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[内容已截断...]"
        prompt = f"""You are an expert in analyzing academic papers in Markdown "
"format. Your task is to extract key sections such as the Title, Abstract, "
"Results, Methods, and Discussion from a given Markdown-formatted research paper."
"Please follow these guidelines:\n"
"- Extract the content of the specified sections exactly as they appear in "
"the original text.\n"
"- Do not modify, paraphrase, or summarize any part of the extracted content.\n"
"- Exclude unnecessary information such as:\n"
"  * References/Bibliography\n"
"  * Author affiliations\n"
"  * Acknowledgments\n"
"  * Appendices\n"
"  * Footnotes\n"
"  * Page numbers\n\n"
"Your output should only include the raw text of the requested sections "
"(Title, Abstract, Results, Methods, Discussion) without any additional "
"commentary or structural changes.\n"
"If a section is missing or cannot be located, simply omit it from the output. "
"Do not generate placeholder text.\n\n"
"Please return the extracted content in the following JSON format:\n\n"
"```json\n"
"{{\n"
"    \"title\": \"exact title text\",\n"
"    \"abstract\": \"exact abstract text\",\n"
"    \"methods\": \"exact methods text\",\n"
"    \"results\": \"exact results text\",\n"
"    \"discussion\": \"exact discussion text\"\n"
"}}\n"
"```\n\n"
"Please process the following Markdown input:\n\n"
"{content}"""
        return prompt

    def _parse_llm_response(self, response: str) -> dict[str, str]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON部分
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                extracted = json.loads(json_str)
                # 确保所有字段都存在
                result = {}
                for key in self.extraction_schema:
                    result[key] = extracted.get(key, "").strip()
                return result
            else:
                logger.warning("LLM响应中未找到有效的JSON格式")
                return self._extract_from_text(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}，尝试文本提取")
            return self._extract_from_text(response)
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            return dict.fromkeys(self.extraction_schema.keys(), "")

    def _extract_from_text(self, text: str) -> dict[str, str]:
        """从文本中提取内容（备用方法）"""
        result = dict.fromkeys(self.extraction_schema.keys(), "")
        # 简单的关键词匹配提取
        lines = text.split("\n")
        current_field: str | None = None
        current_content: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 检测字段标识
            if "title" in line.lower() or "标题" in line:
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content)
                current_field = "title"
                current_content = []
            elif "abstract" in line.lower() or "摘要" in line:
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content)
                current_field = "abstract"
                current_content = []
            elif "method" in line.lower() or "方法" in line:
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content)
                current_field = "methods"
                current_content = []
            elif "result" in line.lower() or "结果" in line:
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content)
                current_field = "results"
                current_content = []
            elif "discussion" in line.lower() or "讨论" in line:
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content)
                current_field = "discussion"
                current_content = []
            elif "conclusion" in line.lower() or "结论" in line:
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content)
                current_field = "conclusion"
                current_content = []
            else:
                if current_field:
                    current_content.append(line)
        # 保存最后一个字段
        if current_field and current_content:
            result[current_field] = "\n".join(current_content)
        return result

    def _fallback_extraction(self, sections: dict[str, PaperSection]) -> dict[str, str]:
        """基于规则的备用提取方法"""
        result = dict.fromkeys(self.extraction_schema.keys(), "")
        # 从解析的章节中提取内容
        section_mapping = {
            "title": ["title"],
            "abstract": ["abstract"],
            "methods": ["methods"],
            "results": ["experiments"],
            "discussion": ["discussion"],
            "conclusion": ["conclusion"],
        }
        for field, section_names in section_mapping.items():
            for section_name in section_names:
                if section_name in sections:
                    result[field] = sections[section_name].content
                    break
        return result

    def _validate_extraction(self, extracted: dict[str, str]) -> dict[str, str]:
        """验证和清理提取的内容"""
        validated = {}
        for key, value in extracted.items():
            # Ensure value is a string
            if not isinstance(value, str):
                value = str(value) if value else ""
            # 清理内容
            value = value.strip()
            # 移除可能的JSON标记
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            # 移除多余的换行
            value = "\n".join(
                line.strip() for line in value.split("\n") if line.strip()
            )
            validated[key] = value
        return validated

    def _validate_extraction_result(self, extracted: dict[str, str]) -> bool:
        """验证提取结果的质量"""
        if not extracted:
            return False
        # 检查必要字段
        required_fields = ["title", "abstract"]
        for field in required_fields:
            if field not in extracted or not extracted[field].strip():
                logger.warning(f"缺少必要字段: {field}")
                return False
        # 检查内容长度合理性
        title = extracted.get("title", "")
        abstract = extracted.get("abstract", "")
        if len(title) < 10 or len(title) > 500:
            logger.warning(f"标题长度不合理: {len(title)}")
            return False
        if len(abstract) < 50 or len(abstract) > 5000:
            logger.warning(f"摘要长度不合理: {len(abstract)}")
            return False
        return True

    async def extract_section_content(
        self, content: str, section_name: str
    ) -> str | None:
        """
        提取指定章节的内容
        Args:
            content: Markdown文档内容
            section_name: 章节名称
        Returns:
            章节内容，如果不存在则返回None
        """
        try:
            parsed_result = self.parser.parse(content)
            sections = parsed_result["sections"]
            if section_name in sections:
                return sections[section_name].content  # type: ignore[no-any-return]
            return None
        except Exception as e:
            logger.error(f"章节内容提取失败: {e}")
            return None

    def get_extraction_schema(self) -> dict[str, Any]:
        """获取提取模式"""
        return self.extraction_schema.copy()

    async def test_extraction(self, sample_content: str) -> dict[str, Any]:
        """
        测试提取功能
        Args:
            sample_content: 测试内容
        Returns:
            测试结果
        """
        try:
            start_time = asyncio.get_event_loop().time()
            extracted = await self.extract_paper_content(sample_content)
            end_time = asyncio.get_event_loop().time()
            result = {
                "success": True,
                "extracted_fields": len([v for v in extracted.values() if v]),
                "total_fields": len(extracted),
                "extraction_time": end_time - start_time,
                "content": extracted,
            }
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extraction_time": 0,
                "content": {},
            }
