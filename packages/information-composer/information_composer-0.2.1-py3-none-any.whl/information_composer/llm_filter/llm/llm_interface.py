"""
LLM接口抽象模块
定义了统一的LLM接口，支持不同的LLM供应商。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar


class MessageRole(Enum):
    """消息角色枚举"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """聊天消息数据结构"""

    role: MessageRole
    content: str
    metadata: dict[str, Any] | None = None


@dataclass
class LLMResponse:
    """LLM响应数据结构"""

    content: str
    metadata: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    model: str | None = None


class LLMInterface(ABC):
    """LLM接口抽象类"""

    def __init__(self, model: str, **kwargs: Any) -> None:
        """
        初始化LLM接口
        Args:
            model: 模型名称
            **kwargs: 其他配置参数
        """
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def chat(self, messages: list[ChatMessage]) -> LLMResponse:
        """
        聊天对话接口
        Args:
            messages: 消息列表
        Returns:
            LLM响应
        """
        pass

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        文本补全接口
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
        Returns:
            LLM响应
        """
        pass

    @abstractmethod
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
        """
        pass

    def get_model_info(self) -> dict[str, Any]:
        """
        获取模型信息
        Returns:
            模型信息字典
        """
        return {
            "model": self.model,
            "provider": self.__class__.__name__,
            "config": self.config,
        }

    def validate_config(self) -> bool:
        """
        验证配置有效性
        Returns:
            配置是否有效
        """
        return True

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        Args:
            key: 配置键
            default: 默认值
        Returns:
            配置值
        """
        return self.config.get(key, default)


class LLMFactory:
    """LLM工厂类"""

    _providers: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type) -> None:
        """注册LLM提供商"""
        cls._providers[name] = provider_class

    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """注册LLM提供商（别名）"""
        cls.register(name, provider_class)

    @classmethod
    def create(cls, provider: str, model: str, **kwargs: Any) -> LLMInterface:
        """
        创建LLM实例
        Args:
            provider: 提供商名称
            model: 模型名称
            **kwargs: 配置参数
        Returns:
            LLM实例
        Raises:
            ValueError: 不支持的提供商
        """
        if provider not in cls._providers:
            raise ValueError(f"不支持的LLM提供商: {provider}")
        provider_class = cls._providers[provider]
        return provider_class(model=model, **kwargs)  # type: ignore[no-any-return]

    @classmethod
    def list_providers(cls) -> list[str]:
        """列出所有支持的提供商"""
        return list(cls._providers.keys())

    @classmethod
    def create_dashscope(cls, model: str, **kwargs: Any) -> LLMInterface:
        """
        创建DashScope LLM实例
        Args:
            model: 模型名称
            **kwargs: 配置参数
        Returns:
            LLM实例
        """
        return cls.create("dashscope", model, **kwargs)


class ConcreteLLMInterface(LLMInterface):
    """具体的LLM接口实现（用于测试）"""

    async def chat(self, messages: list[ChatMessage]) -> LLMResponse:
        """聊天对话接口实现"""
        # 简单的测试实现
        content = f"Response to {len(messages)} messages"
        return LLMResponse(content=content, model=self.model)

    async def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """文本补全接口实现"""
        # 简单的测试实现
        content = f"Completion for: {prompt[:50]}..."
        return LLMResponse(content=content, model=self.model)

    async def extract_structured(
        self, content: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """结构化数据提取接口实现"""
        # 简单的测试实现
        return {"extracted": "data", "content_length": len(content)}


# 注册默认提供商
LLMFactory.register("dashscope", ConcreteLLMInterface)
LLMFactory.register("test", ConcreteLLMInterface)
