"""
LLM模块
提供统一的LLM接口和DashScope集成。
"""

from .dashscope_client import (
    DashScopeClient,
    DashScopeStreamClient,
    create_dashscope_client,
    create_dashscope_stream_client,
)
from .llm_interface import (
    ChatMessage,
    LLMFactory,
    LLMInterface,
    LLMResponse,
    MessageRole,
)


__all__ = [
    "ChatMessage",
    "DashScopeClient",
    "DashScopeStreamClient",
    "LLMFactory",
    "LLMInterface",
    "LLMResponse",
    "MessageRole",
    "create_dashscope_client",
    "create_dashscope_stream_client",
]
