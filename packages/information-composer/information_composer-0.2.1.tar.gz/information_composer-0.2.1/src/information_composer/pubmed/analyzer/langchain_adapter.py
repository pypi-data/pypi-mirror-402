"""
LangChain 适配器
将现有的 DashScope LLM 客户端包装为 LangChain 可用的组件。
同时支持 Ollama 和 OpenAI 等其他 LLM 提供商。
"""

import logging
from typing import Any, Literal

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, Field, model_validator

from information_composer.llm_filter.llm.dashscope_client import DashScopeClient
from information_composer.llm_filter.llm.llm_interface import ChatMessage, MessageRole


logger = logging.getLogger(__name__)


class LangChainDashScopeAdapter(BaseChatModel):
    """
    DashScope LLM 的 LangChain 适配器
    将现有的 DashScopeClient 包装为 LangChain 的 BaseChatModel 接口。
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: DashScopeClient | None = Field(default=None, exclude=True)
    model_name: str = Field(default="qwen-plus-latest")
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=4096)
    api_key: str | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def initialize_client(self) -> "LangChainDashScopeAdapter":
        """初始化 DashScope 客户端"""
        if self.client is None:
            self.client = DashScopeClient(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        return self

    @property
    def _llm_type(self) -> str:
        """返回 LLM 类型"""
        return "dashscope"

    def _convert_langchain_to_dashscope_message(
        self, message: BaseMessage
    ) -> ChatMessage:
        """
        将 LangChain 消息转换为 DashScope 消息格式
        Args:
            message: LangChain 消息
        Returns:
            DashScope 消息
        """
        if isinstance(message, SystemMessage):
            role = MessageRole.SYSTEM
        elif isinstance(message, HumanMessage):
            role = MessageRole.USER
        elif isinstance(message, AIMessage):
            role = MessageRole.ASSISTANT
        else:
            # 默认作为用户消息处理
            role = MessageRole.USER
        # 确保 content 是字符串类型
        content = message.content
        if isinstance(content, list):
            # 如果是列表，将其转换为字符串
            content = str(content)
        elif not isinstance(content, str):
            content = str(content)
        return ChatMessage(role=role, content=content)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        同步生成方法（LangChain 要求实现）
        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器
            **kwargs: 其他参数
        Returns:
            聊天结果
        """
        # 由于 DashScope 客户端是异步的，这里需要同步调用
        # 在实际使用中，建议优先使用 _agenerate
        import asyncio

        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            # 运行异步方法
            result = loop.run_until_complete(
                self._agenerate(messages, stop, None, **kwargs)
            )
            return result
        except Exception as e:
            logger.error(f"同步生成失败: {e}")
            raise

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        异步生成方法
        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器
            **kwargs: 其他参数
        Returns:
            聊天结果
        """
        try:
            # 转换消息格式
            dashscope_messages = [
                self._convert_langchain_to_dashscope_message(msg) for msg in messages
            ]
            # 确保 client 已初始化
            if self.client is None:
                raise RuntimeError("DashScope client 未初始化")
            # 调用 DashScope 客户端
            response = await self.client.chat(dashscope_messages)
            # 构建 LangChain 响应
            message = AIMessage(content=response.content)
            generation = ChatGeneration(message=message)
            # 提取 token 使用信息
            llm_output: dict[str, Any] = {}
            if response.usage:
                llm_output["token_usage"] = response.usage
            if response.model:
                llm_output["model_name"] = response.model
            return ChatResult(generations=[generation], llm_output=llm_output)
        except Exception as e:
            logger.error(f"异步生成失败: {e}")
            raise

    @property
    def _identifying_params(self) -> dict[str, Any]:
        """返回标识参数"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


def create_langchain_dashscope(
    model: str = "qwen-plus-latest",
    api_key: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    **kwargs: Any,
) -> LangChainDashScopeAdapter:
    """
    创建 LangChain DashScope 适配器
    Args:
        model: 模型名称
        api_key: API 密钥
        temperature: 温度参数
        max_tokens: 最大 token 数
        **kwargs: 其他参数
    Returns:
        LangChain DashScope 适配器实例
    """
    return LangChainDashScopeAdapter(
        model_name=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )


def create_langchain_ollama(
    model: str = "qwen2.5:latest",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.1,
    **kwargs: Any,
) -> BaseChatModel:
    """
    创建 LangChain Ollama 适配器
    Args:
        model: 模型名称（如 qwen2.5:latest, llama3.2:latest）
        base_url: Ollama 服务地址
        temperature: 温度参数
        **kwargs: 其他参数
    Returns:
        LangChain Ollama 聊天模型实例
    Example:
        >>> llm = create_langchain_ollama(model="qwen2.5:latest")
        >>> # 或者使用自定义地址
        >>> llm = create_langchain_ollama(
        ...     model="llama3.2:latest",
        ...     base_url="http://192.168.1.100:11434"
        ... )
    """
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError("请安装 langchain-ollama: pip install langchain-ollama")
    # ChatOllama 使用 'model' 参数而不是 'model_name'
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        **kwargs,
    )


def create_langchain_openai(
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.1,
    **kwargs: Any,
) -> BaseChatModel:
    """
    创建 LangChain OpenAI 适配器
    Args:
        model: 模型名称（如 gpt-4o, gpt-4o-mini, gpt-3.5-turbo）
        api_key: OpenAI API 密钥（如未提供则使用环境变量 OPENAI_API_KEY）
        base_url: 自定义 API 基础 URL（可选，用于代理或兼容 API）
        temperature: 温度参数
        **kwargs: 其他参数
    Returns:
        LangChain OpenAI 聊天模型实例
    Example:
        >>> # 使用环境变量中的 API key
        >>> llm = create_langchain_openai(model="gpt-4o-mini")
        >>>
        >>> # 显式指定 API key
        >>> llm = create_langchain_openai(
        ...     model="gpt-4o",
        ...     api_key="sk-..."
        ... )
        >>>
        >>> # 使用自定义 base_url（如 Azure OpenAI 或其他兼容服务）
        >>> llm = create_langchain_openai(
        ...     model="gpt-4",
        ...     base_url="https://your-endpoint.openai.azure.com/",
        ...     api_key="your-key"
        ... )
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError("请安装 langchain-openai: pip install langchain-openai")
    params: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        **kwargs,
    }
    if api_key:
        params["api_key"] = api_key
    if base_url:
        params["base_url"] = base_url
    return ChatOpenAI(**params)


def create_llm(
    provider: Literal["dashscope", "ollama", "openai"] = "dashscope",
    model: str | None = None,
    temperature: float = 0.1,
    **kwargs: Any,
) -> BaseChatModel:
    """
    统一的 LLM 创建接口
    Args:
        provider: LLM 提供商（dashscope, ollama, openai）
        model: 模型名称（如未指定则使用默认值）
        temperature: 温度参数
        **kwargs: 其他参数，根据不同提供商传递不同参数
            - dashscope: api_key, max_tokens
            - ollama: base_url
            - openai: api_key, base_url
    Returns:
        LangChain 聊天模型实例
    Example:
        >>> # DashScope (默认)
        >>> llm = create_llm(provider="dashscope", model="qwen-plus-latest")
        >>>
        >>> # Ollama
        >>> llm = create_llm(
        ...     provider="ollama",
        ...     model="qwen2.5:latest",
        ...     base_url="http://localhost:11434"
        ... )
        >>>
        >>> # OpenAI
        >>> llm = create_llm(
        ...     provider="openai",
        ...     model="gpt-4o-mini",
        ...     api_key="sk-..."
        ... )
    """
    if provider == "dashscope":
        default_model = "qwen-plus-latest"
        return create_langchain_dashscope(
            model=model or default_model,
            temperature=temperature,
            **kwargs,
        )
    elif provider == "ollama":
        default_model = "qwen2.5:latest"
        return create_langchain_ollama(
            model=model or default_model,
            temperature=temperature,
            **kwargs,
        )
    elif provider == "openai":
        default_model = "gpt-4o-mini"
        return create_langchain_openai(
            model=model or default_model,
            temperature=temperature,
            **kwargs,
        )
    else:
        raise ValueError(
            f"不支持的 LLM 提供商: {provider}，支持的提供商: dashscope, ollama, openai"
        )
