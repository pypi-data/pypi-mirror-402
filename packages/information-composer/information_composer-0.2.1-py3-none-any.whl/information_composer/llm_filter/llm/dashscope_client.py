"""
DashScope LLM客户端模块
基于LlamaIndex的DashScope集成，提供统一的LLM接口。
"""

from collections.abc import AsyncGenerator
import logging
import os
from typing import Any


try:
    from llama_index.core.llms import ChatMessage as LlamaIndexChatMessage
    from llama_index.core.llms import ChatResponse, CompletionResponse
    from llama_index.core.llms import MessageRole as LlamaIndexMessageRole
    from llama_index.llms.dashscope import DashScope
except ImportError:
    raise ImportError(
        "请安装 llama-index-llms-dashscope: pip install llama-index-llms-dashscope"
    )
from .llm_interface import (
    ChatMessage,
    LLMFactory,
    LLMInterface,
    LLMResponse,
    MessageRole,
)


logger = logging.getLogger(__name__)


class DashScopeClient(LLMInterface):
    """DashScope LLM客户端实现"""

    def __init__(
        self,
        model: str = "qwen-plus-latest",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化DashScope客户端
        Args:
            model: 模型名称，默认使用qwen-plus-latest
            api_key: API密钥，如果未提供则从环境变量获取
            **kwargs: 其他配置参数
        Raises:
            ValueError: API密钥未提供时抛出
        """
        super().__init__(model=model, **kwargs)
        # 获取API密钥
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DashScope API密钥未提供，请设置DASHSCOPE_API_KEY环境变量")
        # 设置默认配置
        default_config = {
            "temperature": 0.1,
            "max_tokens": 4096,
            "top_p": 0.8,
            "enable_search": False,
            "result_format": "message",
        }
        default_config.update(kwargs)
        # 创建LlamaIndex DashScope实例
        try:
            self.llm = DashScope(model=model, api_key=self.api_key, **default_config)
            logger.info(f"DashScope客户端初始化成功，模型: {model}")
        except Exception as e:
            logger.error(f"DashScope客户端初始化失败: {e}")
            raise

    def _convert_message_role(self, role: MessageRole) -> LlamaIndexMessageRole:
        """转换消息角色"""
        role_mapping = {
            MessageRole.SYSTEM: LlamaIndexMessageRole.SYSTEM,
            MessageRole.USER: LlamaIndexMessageRole.USER,
            MessageRole.ASSISTANT: LlamaIndexMessageRole.ASSISTANT,
        }
        return role_mapping.get(role, LlamaIndexMessageRole.USER)

    def _convert_to_llama_index_messages(
        self, messages: list[ChatMessage]
    ) -> list[LlamaIndexChatMessage]:
        """转换为LlamaIndex消息格式"""
        return [
            LlamaIndexChatMessage(
                role=self._convert_message_role(msg.role), content=msg.content
            )
            for msg in messages
        ]

    async def chat(self, messages: list[ChatMessage]) -> LLMResponse:
        """
        聊天对话接口
        Args:
            messages: 消息列表
        Returns:
            LLM响应
        Raises:
            Exception: API调用失败时抛出
        """
        try:
            # 转换消息格式
            llama_messages = self._convert_to_llama_index_messages(messages)
            # 调用DashScope API
            response: ChatResponse = await self.llm.achat(messages=llama_messages)
            # 构建响应
            return LLMResponse(
                content=response.message.content or "",
                metadata={
                    "model": self.model,
                    "usage": getattr(response, "usage", None),
                    "raw_response": response,
                },
                usage=getattr(response, "usage", None),
                model=self.model,
            )
        except Exception as e:
            logger.error(f"DashScope聊天接口调用失败: {e}")
            raise

    async def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        文本补全接口
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
        Returns:
            LLM响应
        Raises:
            Exception: API调用失败时抛出
        """
        try:
            # 调用DashScope API
            response: CompletionResponse = await self.llm.acomplete(
                prompt=prompt, **kwargs
            )
            # 构建响应
            return LLMResponse(
                content=response.text,
                metadata={
                    "model": self.model,
                    "usage": getattr(response, "usage", None),
                    "raw_response": response,
                },
                usage=getattr(response, "usage", None),
                model=self.model,
            )
        except Exception as e:
            logger.error(f"DashScope补全接口调用失败: {e}")
            raise

    async def extract_structured(
        self, content: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """
        结构化数据提取接口
        Args:
            content: 输入内容
            schema: 输出模式定义
            **kwargs: 其他参数
        Returns:
            提取的结构化数据
        Raises:
            Exception: 提取失败时抛出
        """
        try:
            # 构建提取提示
            prompt = self._build_extraction_prompt(content, schema)
            # 调用补全接口
            response = await self.complete(prompt, **kwargs)
            # 解析响应（这里可以添加JSON解析逻辑）
            # 简单实现，实际项目中可能需要更复杂的解析
            return {
                "extracted_data": response.content,
                "schema": schema,
                "model": self.model,
            }
        except Exception as e:
            logger.error(f"DashScope结构化提取失败: {e}")
            raise

    def _build_extraction_prompt(self, content: str, schema: dict[str, Any]) -> str:
        """构建提取提示"""
        prompt = f"""请从以下内容中提取结构化信息，按照指定的模式返回：
内容：
{content}
提取模式：
{schema}
请严格按照模式要求提取信息，返回JSON格式数据。"""
        return prompt

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        info = super().get_model_info()
        info.update(
            {
                "provider": "DashScope",
                "api_key_configured": bool(self.api_key),
                "llama_index_integration": True,
            }
        )
        return info

    async def test_connection(self) -> bool:
        """
        测试API连接
        Returns:
            连接是否成功
        """
        try:
            test_message = ChatMessage(
                role=MessageRole.USER, content="Hello, this is a connection test."
            )
            response = await self.chat([test_message])
            return bool(response.content)
        except Exception as e:
            logger.error(f"DashScope连接测试失败: {e}")
            return False


class DashScopeStreamClient(DashScopeClient):
    """DashScope流式客户端"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # 启用流式输出
        self.config["stream"] = True

    async def chat_stream(
        self, messages: list[ChatMessage]
    ) -> AsyncGenerator[LLMResponse, None]:
        """
        流式聊天接口
        Args:
            messages: 消息列表
        Yields:
            流式响应片段
        Raises:
            Exception: 流式调用失败时抛出
        """
        try:
            llama_messages = self._convert_to_llama_index_messages(messages)
            async for chunk in self.llm.astream_chat(messages=llama_messages):
                yield LLMResponse(
                    content=chunk.delta,
                    metadata={
                        "model": self.model,
                        "chunk_type": "delta",
                        "raw_chunk": chunk,
                    },
                    model=self.model,
                )
        except Exception as e:
            logger.error(f"DashScope流式聊天失败: {e}")
            raise


# 注册DashScope提供商
LLMFactory.register("dashscope", DashScopeClient)
LLMFactory.register("dashscope_stream", DashScopeStreamClient)


# 便捷函数
def create_dashscope_client(
    model: str = "qwen-plus-latest", **kwargs: Any
) -> DashScopeClient:
    """
    创建DashScope客户端
    Args:
        model: 模型名称
        **kwargs: 配置参数
    Returns:
        DashScope客户端实例
    """
    return DashScopeClient(model=model, **kwargs)


def create_dashscope_stream_client(
    model: str = "qwen-plus-latest", **kwargs: Any
) -> DashScopeStreamClient:
    """
    创建DashScope流式客户端
    Args:
        model: 模型名称
        **kwargs: 配置参数
    Returns:
        DashScope流式客户端实例
    """
    return DashScopeStreamClient(model=model, **kwargs)
