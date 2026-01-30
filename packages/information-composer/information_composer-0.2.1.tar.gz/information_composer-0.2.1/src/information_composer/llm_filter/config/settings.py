"""
配置管理模块
管理项目的所有配置，包括DashScope API配置、模型参数等。
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class DashScopeConfig:
    """DashScope配置"""

    # API配置
    api_key: str = field(default="")
    model: str = field(
        default_factory=lambda: os.getenv("DASHSCOPE_MODEL", "qwen-plus-latest")
    )
    # 模型参数
    temperature: float = 0.1
    max_tokens: int = 4096
    top_p: float = 0.8
    enable_search: bool = False
    result_format: str = "message"
    # 流式配置
    stream: bool = False
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0
    # 超时配置
    timeout: int = 30

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.api_key:
            logger.error("DashScope API密钥未配置")
            return False
        if not self.model:
            logger.error("DashScope模型未配置")
            return False
        # 验证参数范围
        if not (0.0 <= self.temperature <= 2.0):
            logger.error("Temperature must be between 0.0 and 2.0")
            return False
        if self.max_tokens <= 0:
            logger.error("Max tokens must be positive")
            return False
        if not (0.0 <= self.top_p <= 1.0):
            logger.error("Top_p must be between 0.0 and 1.0")
            return False
        if self.max_retries < 0:
            logger.error("Max retries must be non-negative")
            return False
        if self.retry_delay < 0:
            logger.error("Retry delay must be non-negative")
            return False
        if self.timeout <= 0:
            logger.error("Timeout must be positive")
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "api_key": self.api_key,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "enable_search": self.enable_search,
            "result_format": self.result_format,
            "stream": self.stream,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashScopeConfig:
        """从字典创建实例"""
        return cls(**data)


@dataclass
class LLMConfig:
    """LLM通用配置"""

    # 提供商选择
    provider: str = "dashscope"
    # 模型配置
    model: str = "qwen-plus-latest"
    # 性能配置
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    # 缓存配置
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    cache_dir: str = "./cache"
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class ProcessingConfig:
    """文档处理配置"""

    # 路径配置
    input_dir: str = ""
    output_dir: str = ""
    # 文件配置
    file_pattern: str = "*.md"
    recursive: bool = False
    max_file_size_mb: int = 50
    supported_formats: list[str] = field(default_factory=lambda: ["md", "markdown"])
    output_format: str = "markdown"
    overwrite: bool = False
    backup: bool = True
    encoding: str = "utf-8"
    # 处理配置
    chunk_size: int = 1000
    chunk_overlap: int = 200
    # 内容提取配置
    extraction_targets: list[str] = field(
        default_factory=lambda: [
            "title",
            "abstract",
            "methods",
            "results",
            "discussion",
        ]
    )
    # 内容过滤配置
    filter_targets: list[str] = field(
        default_factory=lambda: [
            "references",
            "affiliations",
            "acknowledgments",
            "appendices",
            "footnotes",
            "page_numbers",
        ]
    )

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.input_dir:
            logger.error("Input directory is required")
            return False
        if not self.output_dir:
            logger.error("Output directory is required")
            return False
        if self.output_format not in ["markdown", "html", "json"]:
            logger.error("Invalid output format")
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "file_pattern": self.file_pattern,
            "recursive": self.recursive,
            "max_file_size_mb": self.max_file_size_mb,
            "supported_formats": self.supported_formats,
            "output_format": self.output_format,
            "overwrite": self.overwrite,
            "backup": self.backup,
            "encoding": self.encoding,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "extraction_targets": self.extraction_targets,
            "filter_targets": self.filter_targets,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessingConfig:
        """从字典创建实例"""
        return cls(**data)


@dataclass
class AppConfig:
    """应用主配置"""

    # 环境配置
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )
    log_level: str = field(default="INFO")
    # 路径配置
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    cache_dir: Path = field(default_factory=lambda: Path("./cache"))
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    # 子配置
    dashscope: DashScopeConfig = field(default_factory=DashScopeConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 确保目录存在
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        # 设置日志级别
        logging.basicConfig(
            level=getattr(logging, self.llm.log_level.upper()),
            format=self.llm.log_format,
        )

    def validate(self) -> bool:
        """验证所有配置"""
        validations = [
            self.dashscope.validate(),
            self.processing.validate(),
            # 可以添加其他配置验证
        ]
        return all(validations)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "app_env": self.app_env,
            "debug": self.debug,
            "log_level": self.log_level,
            "base_dir": str(self.base_dir),
            "cache_dir": str(self.cache_dir),
            "output_dir": str(self.output_dir),
            "dashscope": self.dashscope.to_dict(),
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "max_concurrent_requests": self.llm.max_concurrent_requests,
                "request_timeout": self.llm.request_timeout,
                "enable_cache": self.llm.enable_cache,
                "cache_ttl_hours": self.llm.cache_ttl_hours,
                "cache_dir": self.llm.cache_dir,
                "log_level": self.llm.log_level,
                "log_format": self.llm.log_format,
            },
            "processing": self.processing.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        """从字典创建实例"""
        # 处理子配置
        dashscope_data = data.pop("dashscope", {})
        llm_data = data.pop("llm", {})
        processing_data = data.pop("processing", {})
        # 处理路径字段
        if "base_dir" in data:
            data["base_dir"] = Path(data["base_dir"])
        if "cache_dir" in data:
            data["cache_dir"] = Path(data["cache_dir"])
        if "output_dir" in data:
            data["output_dir"] = Path(data["output_dir"])
        # 创建实例
        instance = cls(**data)
        # 设置子配置
        if dashscope_data:
            instance.dashscope = DashScopeConfig.from_dict(dashscope_data)
        if llm_data:
            instance.llm = LLMConfig(**llm_data)
        if processing_data:
            instance.processing = ProcessingConfig.from_dict(processing_data)
        return instance

    def get_llm_config(self) -> dict[str, Any]:
        """获取LLM配置字典"""
        return {
            "provider": self.llm.provider,
            "model": self.dashscope.model,
            "api_key": self.dashscope.api_key,
            "temperature": self.dashscope.temperature,
            "max_tokens": self.dashscope.max_tokens,
            "top_p": self.dashscope.top_p,
            "enable_search": self.dashscope.enable_search,
            "result_format": self.dashscope.result_format,
            "stream": self.dashscope.stream,
            "max_retries": self.dashscope.max_retries,
            "retry_delay": self.dashscope.retry_delay,
            "timeout": self.dashscope.timeout,
        }

    def get_processing_config(self) -> dict[str, Any]:
        """获取处理配置字典"""
        return {
            "max_file_size_mb": self.processing.max_file_size_mb,
            "supported_formats": self.processing.supported_formats,
            "output_format": self.processing.output_format,
            "chunk_size": self.processing.chunk_size,
            "chunk_overlap": self.processing.chunk_overlap,
            "extraction_targets": self.processing.extraction_targets,
            "filter_targets": self.processing.filter_targets,
        }


class ConfigManager:
    """配置管理器"""

    _instance: ConfigManager | None = None
    _config: AppConfig | None = None

    def __new__(cls, config: AppConfig | None = None) -> ConfigManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: AppConfig | None = None) -> None:
        if config is not None:
            self._config = config
        elif self._config is None:
            self._config = self._load_config()
        else:
            # 如果已经有配置，重新加载以确保环境变量更新
            self._config = self._load_config()

    def _load_config(self) -> AppConfig:
        """加载配置"""
        try:
            config = AppConfig()
            # 从环境变量加载配置
            self._load_from_env(config)
            # 验证配置
            if not config.validate():
                logger.warning("配置验证失败，使用默认配置")
            logger.info("配置加载成功")
            return config
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            # 返回默认配置
            return AppConfig()

    def _load_from_env(self, config: AppConfig) -> None:
        """从环境变量加载配置"""
        # DashScope配置
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if api_key:
            config.dashscope.api_key = api_key
        model = os.getenv("DASHSCOPE_MODEL")
        if model:
            config.dashscope.model = model
        # 应用配置
        app_env = os.getenv("APP_ENV")
        if app_env:
            config.app_env = app_env
        debug = os.getenv("DEBUG")
        if debug:
            config.debug = debug.lower() == "true"
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            config.log_level = log_level
        # 性能配置
        max_requests = os.getenv("MAX_CONCURRENT_REQUESTS")
        if max_requests:
            with contextlib.suppress(ValueError):
                config.llm.max_concurrent_requests = int(max_requests)
        request_timeout = os.getenv("REQUEST_TIMEOUT")
        if request_timeout:
            with contextlib.suppress(ValueError):
                config.llm.request_timeout = int(request_timeout)
        # 缓存配置
        enable_cache = os.getenv("ENABLE_CACHE")
        if enable_cache:
            config.llm.enable_cache = enable_cache.lower() == "true"
        cache_ttl = os.getenv("CACHE_TTL_HOURS")
        if cache_ttl:
            with contextlib.suppress(ValueError):
                config.llm.cache_ttl_hours = int(cache_ttl)
        cache_dir = os.getenv("CACHE_DIR")
        if cache_dir:
            config.llm.cache_dir = cache_dir
        # 文件处理配置
        max_file_size = os.getenv("MAX_FILE_SIZE_MB")
        if max_file_size:
            with contextlib.suppress(ValueError):
                config.processing.max_file_size_mb = int(max_file_size)
        supported_formats = os.getenv("SUPPORTED_FORMATS")
        if supported_formats:
            formats = supported_formats.split(",")
            config.processing.supported_formats = [f.strip() for f in formats]
        output_format = os.getenv("OUTPUT_FORMAT")
        if output_format:
            config.processing.output_format = output_format

    def get_config(self) -> AppConfig:
        """获取配置实例"""
        return self._config  # type: ignore[return-value]

    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()

    def update_config(self, **kwargs: Any) -> None:
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                logger.warning(f"未知配置项: {key}")

    def save_config(self, config_file: Path) -> None:
        """保存配置到文件"""
        import json

        try:
            config_data = self._config.to_dict()
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到: {config_file}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise

    def load_config(self, config_file: Path) -> None:
        """从文件加载配置"""
        import json

        try:
            with open(config_file, encoding="utf-8") as f:
                config_data = json.load(f)
            self._config = AppConfig.from_dict(config_data)
            logger.info(f"配置已从文件加载: {config_file}")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise


# 全局配置实例
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """获取配置实例的便捷函数"""
    return config_manager.get_config()


def get_llm_config() -> dict[str, Any]:
    """获取LLM配置的便捷函数"""
    return config_manager.get_config().get_llm_config()


def get_processing_config() -> dict[str, Any]:
    """获取处理配置的便捷函数"""
    return config_manager.get_config().get_processing_config()
