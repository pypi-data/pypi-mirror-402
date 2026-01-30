# 安装指南

本指南将帮助您在系统上安装和配置 Information Composer。

## 系统要求

### 操作系统
- Linux (Ubuntu 18.04+, CentOS 7+)
- macOS (10.14+)
- Windows (10+)

### Python 版本
- **Python 3.12** (最低要求版本)
- Python 3.13 (推荐版本)
- Python 3.11 及以下版本不再被支持

### 硬件要求
- 内存: 最少 4GB RAM，推荐 8GB+
- 存储: 最少 1GB 可用空间
- 网络: 稳定的互联网连接（用于下载依赖和访问 API）

## 安装方法

### 方法 1: 从源码安装（推荐）

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/information-composer.git
cd information-composer
```

2. **创建虚拟环境**
```bash
# Linux/macOS
python -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -e .
```

### 方法 2: 使用 pip 安装

```bash
pip install information-composer
```

### 方法 3: 使用 conda 安装

```bash
conda install -c conda-forge information-composer
```

## 配置

### 1. 环境变量

创建 `.env` 文件或设置环境变量：

```bash
# DashScope API 配置（用于 LLM 过滤）
export DASHSCOPE_API_KEY="your-api-key-here"

# 可选配置
export MAX_CONCURRENT_REQUESTS=5
export REQUEST_TIMEOUT=30
export ENABLE_CACHE=true
export CACHE_TTL_HOURS=24
```

### 2. 配置文件

项目支持通过配置文件进行设置：

```yaml
# config.yaml
llm:
  api_key: "your-api-key-here"
  model: "qwen-plus"
  max_concurrent_requests: 5
  request_timeout: 30

processing:
  max_file_size_mb: 10
  supported_formats: ["pdf", "md", "txt"]
```

## 验证安装

### 1. 检查安装

```bash
# 检查版本
python -c "import information_composer; print(information_composer.__version__)"

# 检查 CLI 工具
pdf-validator --help
md-llm-filter --help
```

### 2. 运行测试

```bash
# 运行代码质量检查
python scripts/check_code.py

# 运行示例
python examples/pdf_validator_example.py
```

## 开发环境设置

如果您计划参与开发，请按照以下步骤设置开发环境：

### 1. 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 2. 安装代码质量工具

```bash
pip install ruff pytest pytest-cov black isort
```

### 3. 配置 Git hooks（可选）

```bash
# 安装 pre-commit
pip install pre-commit
pre-commit install
```

## 故障排除

### 常见问题

#### 1. 导入错误
```
ModuleNotFoundError: No module named 'information_composer'
```

**解决方案**: 确保已激活虚拟环境并正确安装项目：
```bash
source .venv/bin/activate  # Linux/macOS
pip install -e .
```

#### 2. 权限错误
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**: 使用虚拟环境或添加 `--user` 标志：
```bash
pip install -e . --user
```

#### 3. 依赖冲突
```
ERROR: pip's dependency resolver does not currently have a strategy
```

**解决方案**: 使用虚拟环境隔离依赖：
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### 4. API 密钥错误
```
Error: Invalid API key
```

**解决方案**: 检查 API 密钥配置：
```bash
echo $DASHSCOPE_API_KEY
# 或检查 .env 文件
```

### 获取帮助

如果遇到其他问题：

1. 查看 [常见问题](quickstart.md#常见问题)
2. 搜索 [Issues](https://github.com/yourusername/information-composer/issues)
3. 创建新的 Issue 描述您的问题

## 下一步

安装完成后，请查看：

- [快速开始](quickstart.md) - 学习基本用法
- [配置说明](configuration.md) - 了解详细配置选项
- [功能指南](guides/) - 探索各种功能

---

**恭喜！** 您已成功安装 Information Composer。现在可以开始使用这个强大的信息处理工具了！
