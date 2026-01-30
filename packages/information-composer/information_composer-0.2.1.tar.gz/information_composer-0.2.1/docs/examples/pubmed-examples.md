# PubMed 示例文档

本文档详细介绍了 information-composer 项目中与 PubMed 相关的所有示例代码。PubMed 是生物医学文献数据库，这些示例展示了如何查询、获取和处理 PubMed 数据。

## 示例概览

### 1. PubMed PMID 查询示例 (`pubmed_query_pmid.py`)

**功能**：演示如何使用不同日期范围和搜索参数查询 PubMed 获取 PMIDs。

**主要特性**：
- 支持日期范围过滤
- 批量处理不同时间间隔
- 搜索参数自定义
- 结果统计和显示

**使用场景**：
- 学术研究中的文献发现
- 特定主题的文献调研
- 时间序列分析

**代码示例**：
```python
from information_composer.pubmed.pubmed import query_pmid_by_date

# 查询最近5年的相关论文
recent_pmids = query_pmid_by_date(
    query="cis-regulatory elements",
    email="your_email@example.com",
    start_date="2024/01/01",
    batch_months=6,  # 使用6个月间隔
)
```

**运行方法**：
```bash
python examples/pubmed_query_pmid.py
```

### 2. PubMed 详情获取示例 (`pubmed_details_example.py`)

**功能**：演示如何根据 PMIDs 获取详细的文章信息。

**主要特性**：
- 多 PMID 批量处理
- 结构化信息显示
- 不同数据字段处理
- JSON 格式结果保存

**使用场景**：
- 获取论文的完整元数据
- 学术文献分析
- 数据挖掘和统计

**代码示例**：
```python
from information_composer.pubmed.pubmed import fetch_pubmed_details

# 获取多个 PMID 的详细信息
pmids = ["39659015", "24191062", "26400163"]
results = fetch_pubmed_details(pmids, email="your_email@example.com")
```

**运行方法**：
```bash
python examples/pubmed_details_example.py
```

### 3. PubMed 批量详情获取示例 (`pubmed_details_batch_example.py`)

**功能**：演示大规模 PubMed 数据收集和处理的完整工作流程。

**主要特性**：
- 大规模数据查询
- 缓存机制提高性能
- 进度跟踪和性能监控
- 错误处理和缓存管理

**使用场景**：
- 大规模学术研究
- 文献数据库构建
- 长期数据收集项目

**代码示例**：
```python
from information_composer.pubmed.pubmed import (
    query_pmid_by_date,
    fetch_pubmed_details_batch_sync,
    clean_pubmed_cache
)

# 完整的工作流程
pmids = query_pmid_by_date(query="cis-regulatory elements", ...)
results = fetch_pubmed_details_batch_sync(pmids=pmids, ...)
clean_pubmed_cache(cache_dir)
```

**运行方法**：
```bash
python examples/pubmed_details_batch_example.py
```

### 4. PubMed 关键词过滤示例 (`pubmed_keywords_filter_example.py`)

**功能**：演示如何使用关键词过滤 PubMed 基线数据。

**主要特性**：
- 大型 XML 文件处理
- 关键词过滤和统计
- 文本清理和预处理
- 结果导出和分析

**使用场景**：
- 特定主题的文献筛选
- 关键词频率分析
- 大规模数据处理

**代码示例**：
```python
from information_composer.pubmed.baseline import load_baseline

# 加载并过滤 PubMed 基线数据
df = load_baseline(
    xml_file_path,
    output_type="pd",
    keywords=["promoter", "cis-regulatory", "enhancer"],
    kw_filter="both",
    log=True
)
```

**运行方法**：
```bash
python examples/pubmed_keywords_filter_example.py
```

### 5. PubMed CLI 工具使用示例 (`pubmed_cli_example.py`)

**功能**：演示如何使用 PubMed CLI 工具进行命令行操作。

**主要特性**：
- 命令行工具使用
- 帮助信息显示
- 错误处理演示
- 最佳实践展示

**使用场景**：
- 命令行环境下的 PubMed 操作
- 脚本自动化
- 批处理任务

**代码示例**：
```bash
# 搜索命令帮助
pubmed-cli search --help

# 详情命令帮助
pubmed-cli details --help

# 批量命令帮助
pubmed-cli batch --help
```

**运行方法**：
```bash
python examples/pubmed_cli_example.py
```

## 配置要求

### 环境变量

```bash
# PubMed API 邮箱（必需）
export PUBMED_EMAIL="your-email@example.com"
```

### 依赖包

```bash
# 基础依赖
pip install information-composer

# 可选依赖（用于高级功能）
pip install tqdm pandas
```

### 数据文件

某些示例需要额外的数据文件：

- **PubMed 基线数据**：`pubmed24n1219.xml.gz`
  - 下载地址：https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/
  - 文件大小：约 1-2 GB
  - 用于关键词过滤示例

## 常见问题

### Q: 为什么需要提供邮箱地址？
A: PubMed API 要求提供有效的邮箱地址用于身份识别和合规性。这有助于 API 服务提供商进行使用统计和联系。

### Q: 查询结果为空怎么办？
A: 检查搜索关键词是否正确，尝试使用更通用的术语，或者调整日期范围。某些专业术语可能没有匹配的文献。

### Q: 如何处理大量数据的查询？
A: 使用批量处理示例，设置适当的 `batch_months` 参数，并启用缓存机制。避免一次性查询过大的时间范围。

### Q: 缓存文件占用太多空间怎么办？
A: 定期运行 `clean_pubmed_cache()` 函数清理缓存，或者设置较短的缓存过期时间。

### Q: 如何自定义搜索参数？
A: 修改示例代码中的配置参数，如 `batch_months`、`start_date`、`query` 等。参考 API 文档了解所有可用参数。

## 性能优化建议

### 1. 使用缓存
```python
# 启用缓存以提高性能
cache_dir = Path("pubmed_cache")
results = fetch_pubmed_details_batch_sync(
    pmids=pmids,
    cache_dir=cache_dir,
    chunk_size=100
)
```

### 2. 批量处理
```python
# 使用适当的批次大小
batch_months = 12  # 根据数据量调整
chunk_size = 100   # 根据内存情况调整
```

### 3. 错误处理
```python
# 实现重试机制
try:
    results = query_pmid_by_date(query, email)
except Exception as e:
    print(f"查询失败: {e}")
    # 实现重试逻辑
```

## 最佳实践

### 1. 搜索策略
- 使用具体的搜索术语
- 结合 MeSH 术语和关键词
- 利用布尔运算符（AND, OR, NOT）
- 使用字段限定符（[Title/Abstract]）

### 2. 数据处理
- 验证 PMID 的有效性
- 处理缺失的数据字段
- 使用适当的数据类型
- 实现数据清理和标准化

### 3. 错误处理
- 检查网络连接
- 处理 API 限制
- 实现重试机制
- 记录错误日志

### 4. 性能考虑
- 使用缓存减少重复请求
- 实现适当的延迟
- 监控内存使用
- 优化查询参数

## 相关资源

- [PubMed API 文档](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [MeSH 术语数据库](https://www.ncbi.nlm.nih.gov/mesh/)
- [information-composer PubMed 模块文档](../api/pubmed/)
- [PubMed 搜索语法指南](https://pubmed.ncbi.nlm.nih.gov/help/)

## 更新日志

- **v1.0.0** - 初始版本，包含基础查询功能
- **v1.1.0** - 添加批量处理和缓存支持
- **v1.2.0** - 增加关键词过滤和 CLI 工具
- **v1.3.0** - 完善错误处理和性能优化

---

*最后更新：2024年12月*
