"""
配置模块
管理项目的所有配置，包括DashScope API配置、模型参数等。
"""

from .settings import (
    AppConfig,
    ConfigManager,
    DashScopeConfig,
    LLMConfig,
    ProcessingConfig,
    config_manager,
    get_config,
    get_llm_config,
    get_processing_config,
)


__all__ = [
    "AppConfig",
    "ConfigManager",
    "DashScopeConfig",
    "LLMConfig",
    "ProcessingConfig",
    "config_manager",
    "get_config",
    "get_llm_config",
    "get_processing_config",
]
