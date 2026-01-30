# 快速开始

本指南将帮助您在 5 分钟内快速上手 Information Composer。

## 🚀 5 分钟快速开始

### 步骤 1: 安装和激活

```bash
# 克隆项目
git clone https://github.com/yourusername/information-composer.git
cd information-composer

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装项目
pip install -e .
```

### 步骤 2: 验证安装

```bash
# 检查 CLI 工具
pdf-validator --help
md-llm-filter --help

# 运行代码质量检查
python scripts/check_code.py
```

### 步骤 3: 基本使用

#### PDF 验证
```bash
# 验证单个 PDF 文件
pdf-validator document.pdf

# 验证目录中的所有 PDF
pdf-validator -d /path/to/pdfs

# 递归验证
pdf-validator -d /path/to/pdfs -r
```

#### Markdown 处理
```bash
# 使用 LLM 过滤 Markdown
md-llm-filter input.md output.md

# 查看帮助
md-llm-filter --help
```

## 📖 详细使用示例

### 1. PDF 验证器

```python
from information_composer.pdf.validator import PDFValidator

# 创建验证器
validator = PDFValidator(verbose=True)

# 验证单个文件
is_valid, error = validator.validate_single_pdf("document.pdf")
if is_valid:
    print("PDF 文件有效")
else:
    print(f"PDF 文件无效: {error}")

# 验证目录
validator.validate_directory("/path/to/pdfs", recursive=True)
stats = validator.get_validation_stats()
print(f"验证了 {stats['total_files']} 个文件")
```

### 2. Markdown 处理器

```python
from information_composer.markdown import jsonify, markdownify

# 将 Markdown 转换为 JSON
with open("document.md", "r") as f:
    content = f.read()

json_data = jsonify(content)
print(json_data)

# 将 JSON 转换为 Markdown
markdown_content = markdownify(json_data)
print(markdown_content)
```

### 3. PubMed 查询

```python
from information_composer.pubmed.pubmed import query_pmid_by_date

# 查询 PubMed
pmids = query_pmid_by_date(
    query="machine learning",
    email="your-email@example.com",
    start_date="2023/01/01",
    end_date="2023/12/31"
)

print(f"找到 {len(pmids)} 篇相关文献")
```

### 4. DOI 下载器

```python
from information_composer.core.doi_downloader import DOIDownloader

# 创建下载器
downloader = DOIDownloader()

# 下载 DOI
result = downloader.download_doi("10.1038/nature12373")
if result:
    print(f"成功下载: {result['title']}")
```

## 🛠️ 常用命令

### 代码质量检查
```bash
# 运行所有检查
python scripts/check_code.py

# 自动修复问题
python scripts/check_code.py --fix

# 详细输出
python scripts/check_code.py --verbose

# 包含测试
python scripts/check_code.py --with-tests
```

### 环境管理
```bash
# 激活环境
source activate.sh  # Linux/macOS
activate.bat        # Windows

# 检查环境
python --version
pip list | grep information-composer
```

## 📁 项目结构

```
information-composer/
├── src/information_composer/    # 主源代码
│   ├── pdf/                    # PDF 处理
│   ├── markdown/               # Markdown 处理
│   ├── pubmed/                 # PubMed 集成
│   ├── core/                   # 核心功能
│   └── llm_filter/             # LLM 过滤
├── examples/                   # 使用示例
├── scripts/                    # 工具脚本
├── docs/                       # 文档
└── tests/                      # 测试文件
```

## 🔧 配置选项

### 环境变量
```bash
# 必需
export DASHSCOPE_API_KEY="your-api-key"

# 可选
export MAX_CONCURRENT_REQUESTS=5
export REQUEST_TIMEOUT=30
export ENABLE_CACHE=true
```

### 配置文件
创建 `config.yaml`:
```yaml
llm:
  api_key: "your-api-key"
  model: "qwen-plus"
  max_concurrent_requests: 5

processing:
  max_file_size_mb: 10
  supported_formats: ["pdf", "md", "txt"]
```

## 🎯 下一步

现在您已经掌握了基本用法，可以：

1. **探索功能**: 查看 [功能指南](guides/) 了解详细功能
2. **学习 API**: 阅读 [API 参考](api/) 了解编程接口
3. **查看示例**: 运行 [examples/](examples/) 目录中的示例
4. **参与开发**: 查看 [开发指南](development/) 了解如何贡献

## ❓ 常见问题

### Q: 如何获取 DashScope API 密钥？
A: 访问 [DashScope 官网](https://dashscope.aliyun.com/) 注册并获取 API 密钥。

### Q: 支持哪些文件格式？
A: 目前支持 PDF、Markdown、TXT 等格式，更多格式正在开发中。

### Q: 如何处理大文件？
A: 可以通过环境变量 `MAX_FILE_SIZE_MB` 设置最大文件大小限制。

### Q: 如何提高处理速度？
A: 调整 `MAX_CONCURRENT_REQUESTS` 参数，或启用缓存 `ENABLE_CACHE=true`。

---

**恭喜！** 您已经成功完成了 Information Composer 的快速开始。现在可以开始探索更多高级功能了！
