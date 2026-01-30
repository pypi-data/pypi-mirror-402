# 配置说明

本指南详细介绍 Information Composer 的配置选项和设置方法。

## 📋 配置概览

Information Composer 支持多种配置方式：

- 环境变量
- 配置文件
- 命令行参数
- 代码配置

## 🔧 环境变量配置

### 必需配置

#### DASHSCOPE_API_KEY
DashScope API 密钥，用于 LLM 过滤功能。

```bash
export DASHSCOPE_API_KEY="sk-your-api-key-here"
```

**获取方法**:
1. 访问 [DashScope 官网](https://dashscope.aliyun.com/)
2. 注册账号并登录
3. 在控制台创建 API 密钥

### 可选配置

#### LLM 配置

```bash
# 并发请求数（默认: 5）
export MAX_CONCURRENT_REQUESTS=5

# 请求超时时间（秒，默认: 30）
export REQUEST_TIMEOUT=30

# 缓存配置
export ENABLE_CACHE=true
export CACHE_TTL_HOURS=24
export CACHE_DIR="/path/to/cache"
```

#### 文件处理配置

```bash
# 最大文件大小（MB，默认: 10）
export MAX_FILE_SIZE_MB=10

# 支持的文件格式
export SUPPORTED_FORMATS="pdf,md,txt"

# 输出目录
export OUTPUT_DIR="/path/to/output"
```

#### 应用配置

```bash
# 应用环境
export APP_ENV="production"  # development, staging, production

# 调试模式
export DEBUG=false

# 日志级别
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

## 📄 配置文件

### YAML 配置文件

创建 `config.yaml` 文件：

```yaml
# LLM 配置
llm:
  api_key: "sk-your-api-key-here"
  model: "qwen-plus"  # qwen-plus, qwen-max, qwen-turbo
  max_concurrent_requests: 5
  request_timeout: 30
  enable_cache: true
  cache_ttl_hours: 24
  cache_dir: "./cache"

# 文件处理配置
processing:
  max_file_size_mb: 10
  supported_formats:
    - "pdf"
    - "md"
    - "txt"
  output_dir: "./output"

# 应用配置
app:
  env: "production"
  debug: false
  log_level: "INFO"

# PDF 验证配置
pdf:
  strict_mode: true
  check_encryption: true
  max_pages: 1000

# Markdown 处理配置
markdown:
  preserve_formatting: true
  extract_metadata: true
  clean_html: true

# PubMed 配置
pubmed:
  email: "your-email@example.com"
  batch_size: 100
  delay_between_requests: 1.0
```

### JSON 配置文件

创建 `config.json` 文件：

```json
{
  "llm": {
    "api_key": "sk-your-api-key-here",
    "model": "qwen-plus",
    "max_concurrent_requests": 5,
    "request_timeout": 30,
    "enable_cache": true,
    "cache_ttl_hours": 24,
    "cache_dir": "./cache"
  },
  "processing": {
    "max_file_size_mb": 10,
    "supported_formats": ["pdf", "md", "txt"],
    "output_dir": "./output"
  },
  "app": {
    "env": "production",
    "debug": false,
    "log_level": "INFO"
  }
}
```

## 🐍 代码配置

### 使用配置管理器

```python
from information_composer.llm_filter.config.settings import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 获取配置
config = config_manager.get_config()

# 更新配置
config.llm.api_key = "new-api-key"
config.llm.max_concurrent_requests = 10

# 保存配置
config_manager.save_config(config)
```

### 直接配置

```python
from information_composer.llm_filter.config.settings import LLMConfig, ProcessingConfig

# 创建 LLM 配置
llm_config = LLMConfig(
    api_key="sk-your-api-key-here",
    model="qwen-plus",
    max_concurrent_requests=5,
    request_timeout=30
)

# 创建处理配置
processing_config = ProcessingConfig(
    max_file_size_mb=10,
    supported_formats=["pdf", "md", "txt"]
)
```

## 🎯 特定功能配置

### PDF 验证器配置

```python
from information_composer.pdf.validator import PDFValidator

# 创建验证器时配置
validator = PDFValidator(
    verbose=True,  # 详细输出
    strict_mode=True,  # 严格模式
    check_encryption=True,  # 检查加密
    max_pages=1000  # 最大页数
)
```

### Markdown 处理器配置

```python
from information_composer.markdown import jsonify, markdownify

# 配置选项
options = {
    "preserve_formatting": True,
    "extract_metadata": True,
    "clean_html": True,
    "remove_links": False
}

# 使用配置
json_data = jsonify(content, **options)
markdown_content = markdownify(json_data, **options)
```

### PubMed 查询配置

```python
from information_composer.pubmed.pubmed import query_pmid_by_date

# 查询配置
pmids = query_pmid_by_date(
    query="machine learning",
    email="your-email@example.com",
    start_date="2023/01/01",
    end_date="2023/12/31",
    batch_months=6  # 批处理月数
)
```

## 🔄 配置优先级

配置的优先级从高到低：

1. **命令行参数** - 最高优先级
2. **环境变量** - 次高优先级
3. **配置文件** - 中等优先级
4. **默认值** - 最低优先级

## 📝 配置示例

### 开发环境配置

```bash
# .env.development
DASHSCOPE_API_KEY=sk-dev-key
DEBUG=true
LOG_LEVEL=DEBUG
MAX_CONCURRENT_REQUESTS=2
ENABLE_CACHE=false
```

### 生产环境配置

```bash
# .env.production
DASHSCOPE_API_KEY=sk-prod-key
DEBUG=false
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
ENABLE_CACHE=true
CACHE_TTL_HOURS=24
```

### 测试环境配置

```bash
# .env.testing
DASHSCOPE_API_KEY=sk-test-key
DEBUG=true
LOG_LEVEL=DEBUG
MAX_CONCURRENT_REQUESTS=1
ENABLE_CACHE=false
```

## 🔍 配置验证

### 验证配置

```python
from information_composer.llm_filter.config.settings import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 验证配置
is_valid, errors = config_manager.validate_config()
if not is_valid:
    print("配置验证失败:")
    for error in errors:
        print(f"  - {error}")
else:
    print("配置验证通过")
```

### 检查配置

```python
# 检查特定配置
config = config_manager.get_config()

# 检查 API 密钥
if not config.llm.api_key:
    print("警告: 未设置 DashScope API 密钥")

# 检查缓存配置
if config.llm.enable_cache and not config.llm.cache_dir:
    print("警告: 启用了缓存但未设置缓存目录")
```

## 🛠️ 故障排除

### 常见配置问题

#### 1. API 密钥无效
```
Error: Invalid API key
```

**解决方案**:
- 检查 API 密钥是否正确
- 确认 API 密钥是否有效
- 检查环境变量是否正确设置

#### 2. 配置文件格式错误
```
Error: Invalid YAML format
```

**解决方案**:
- 检查 YAML 语法
- 使用在线 YAML 验证器
- 参考配置示例

#### 3. 权限问题
```
Error: Permission denied
```

**解决方案**:
- 检查文件权限
- 使用正确的用户权限
- 检查目录是否存在

### 调试配置

```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看当前配置
from information_composer.llm_filter.config.settings import ConfigManager
config_manager = ConfigManager()
config = config_manager.get_config()
print(config)
```

## 📚 相关文档

- [安装指南](installation.md) - 安装和基本配置
- [快速开始](quickstart.md) - 快速上手
- [功能指南](guides/) - 各功能详细说明
- [API 参考](api/) - 编程接口文档

---

**配置完成！** 现在您可以根据需要调整 Information Composer 的各种配置选项了。
