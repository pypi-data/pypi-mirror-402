# Google Scholar 示例文档

本文档详细介绍了 information-composer 项目中与 Google Scholar 学术搜索相关的所有示例代码。这些示例展示了如何使用 Google Scholar 爬虫进行学术论文搜索、数据收集和分析。

## 示例概览

### 1. Google Scholar 基础搜索示例 (`google_scholar_basic_example.py`)

**功能**：演示 Google Scholar 爬虫的基本搜索功能。

**主要特性**：
- 基础搜索配置和设置
- 简单查询执行
- 结果处理和显示
- 数据导出功能
- 错误处理和最佳实践

**使用场景**：
- 学术论文发现
- 基础文献调研
- 学习搜索功能

**代码示例**：
```python
from information_composer.sites.google_scholar import (
    GoogleScholarCrawler,
    SearchConfig
)

# 配置搜索参数
config = SearchConfig(
    max_results=20,
    year_range=(2020, 2023),
    include_citations=True,
    include_abstracts=True,
    rate_limit=2.0
)

# 执行搜索
async with GoogleScholarCrawler(config=config) as crawler:
    result = await crawler.search("machine learning natural language processing")
```

**运行方法**：
```bash
python examples/google_scholar_basic_example.py
```

### 2. Google Scholar 高级搜索示例 (`google_scholar_advanced_example.py`)

**功能**：演示 Google Scholar 爬虫的高级搜索功能。

**主要特性**：
- 高级搜索配置
- 结构化搜索
- 批量搜索处理
- 多种导出格式
- 数据分析和组合

**使用场景**：
- 复杂学术研究
- 多主题文献调研
- 高级数据分析
- 学术趋势分析

**代码示例**：
```python
# 高级结构化搜索
result = await crawler.advanced_search(
    title_keywords=["neural networks", "deep learning"],
    author_names=["Hinton", "LeCun"],
    exclude_terms=["survey", "review"]
)

# 批量搜索
queries = [
    "transformer neural networks attention mechanism",
    "BERT language model natural language processing",
    "GPT generative pre-trained transformer"
]
batch_results = await crawler.search_batch(queries, max_results_per_query=20)
```

**运行方法**：
```bash
python examples/google_scholar_advanced_example.py
```

### 3. Google Scholar 批量处理示例 (`google_scholar_batch_example.py`)

**功能**：演示大规模 Google Scholar 数据收集和处理。

**主要特性**：
- 大规模数据收集
- 批量处理能力
- 进度跟踪和性能监控
- 错误处理和恢复
- 综合分析报告

**使用场景**：
- 大规模学术研究
- 文献数据库构建
- 学术趋势分析
- 长期数据收集项目

**代码示例**：
```python
# 研究主题列表
research_topics = [
    "artificial intelligence machine learning",
    "natural language processing transformers",
    "computer vision deep learning",
    "reinforcement learning robotics"
]

# 批量处理
batch_results = await crawler.search_batch(
    research_topics,
    max_results_per_query=25,
    delay_between_queries=3.0
)
```

**运行方法**：
```bash
python examples/google_scholar_batch_example.py
```

## 配置要求

### 环境变量

```bash
# 可选：代理设置
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="https://proxy.example.com:8080"

# 可选：用户代理设置
export USER_AGENT="Mozilla/5.0 (compatible; AcademicBot/1.0)"
```

### 依赖包

```bash
# 基础依赖
pip install information-composer

# 可选依赖（用于高级功能）
pip install selenium beautifulsoup4 lxml
```

### 浏览器驱动（可选）

对于使用 Selenium 的高级功能，需要安装浏览器驱动：

```bash
# Chrome 驱动
# 下载地址：https://chromedriver.chromium.org/

# Firefox 驱动
# 下载地址：https://github.com/mozilla/geckodriver/releases
```

## 搜索配置说明

### SearchConfig 参数

```python
config = SearchConfig(
    max_results=50,                    # 最大结果数量
    year_range=(2020, 2023),          # 年份范围
    language="en",                     # 语言设置
    include_citations=True,            # 包含引用信息
    include_abstracts=True,            # 包含摘要
    include_patents=False,             # 包含专利
    sort_by="relevance",               # 排序方式
    rate_limit=2.5,                    # 请求间隔（秒）
    search_strategy=SearchStrategy.REQUESTS,  # 搜索策略
    use_selenium_fallback=True,        # 使用 Selenium 备用
    cache_dir="./cache/google_scholar", # 缓存目录
    resolve_dois=True,                 # 解析 DOIs
    link_pubmed=True                   # 链接 PubMed
)
```

### 搜索策略

1. **REQUESTS**：使用 requests 库（默认，快速）
2. **SELENIUM**：使用 Selenium 浏览器（更稳定，但较慢）
3. **AUTO**：自动选择最佳策略

### 排序选项

- `relevance`：相关性（默认）
- `date`：按日期排序
- `citations`：按引用数排序

## 结果处理

### SearchResult 对象

```python
class SearchResult:
    query: str                    # 搜索查询
    papers: List[Paper]          # 论文列表
    search_time: float           # 搜索耗时
    strategy_used: SearchStrategy # 使用的策略
    valid_papers: int            # 有效论文数
    papers_with_doi: int         # 有 DOI 的论文数
    papers_with_abstract: int    # 有摘要的论文数
```

### Paper 对象

```python
class Paper:
    title: str                   # 论文标题
    authors: List[str]           # 作者列表
    journal: str                 # 期刊名称
    year: int                    # 发表年份
    citation_count: int          # 引用次数
    doi: str                     # DOI 标识符
    abstract: str                # 摘要
    confidence_score: float      # 置信度分数
    pubmed_id: str               # PubMed ID
```

## 数据导出

### 支持的导出格式

1. **JSON**：结构化数据格式
```python
await crawler.export_results(result, "results.json", "json")
```

2. **CSV**：表格数据格式
```python
await crawler.export_results(result, "results.csv", "csv")
```

3. **BibTeX**：参考文献格式
```python
await crawler.export_results(result, "results.bib", "bibtex")
```

### 批量导出示例

```python
# 导出所有论文
await crawler.export_results(all_papers, "all_papers.json", "json")

# 导出高影响因子论文
high_impact_papers = [p for p in all_papers if p.citation_count >= 50]
await crawler.export_results(high_impact_papers, "high_impact.bib", "bibtex")
```

## 性能优化

### 1. 缓存机制

```python
# 启用缓存以提高性能
config = SearchConfig(
    cache_dir="./cache/google_scholar",
    cache_ttl_days=7  # 缓存7天
)
```

### 2. 速率限制

```python
# 设置适当的请求间隔
config = SearchConfig(
    rate_limit=2.0  # 2秒间隔
)
```

### 3. 批量处理

```python
# 使用批量搜索提高效率
batch_results = await crawler.search_batch(
    queries,
    max_results_per_query=20,
    delay_between_queries=3.0
)
```

### 4. 内存管理

```python
# 处理大量数据时分批处理
def process_large_dataset(papers, batch_size=100):
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        # 处理批次
        process_batch(batch)
```

## 错误处理

### 常见错误类型

1. **网络错误**：连接超时、DNS 解析失败
2. **反爬虫检测**：IP 被封、验证码要求
3. **数据解析错误**：HTML 结构变化
4. **API 限制**：请求频率过高

### 错误处理示例

```python
async def robust_search(query: str, max_retries: int = 3):
    """带重试机制的搜索函数"""
    for attempt in range(max_retries):
        try:
            result = await crawler.search(query)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"搜索失败，重试 {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

### 反爬虫对策

```python
# 使用随机用户代理
config = SearchConfig(
    user_agent="Mozilla/5.0 (compatible; AcademicBot/1.0)",
    rate_limit=3.0,  # 增加延迟
    use_selenium_fallback=True  # 使用浏览器备用
)
```

## 最佳实践

### 1. 搜索策略

```python
# 使用具体的搜索术语
query = "machine learning natural language processing"

# 结合布尔运算符
query = "transformer AND attention AND (BERT OR GPT)"

# 使用引号进行精确匹配
query = '"deep learning" "neural networks"'
```

### 2. 数据验证

```python
def validate_paper(paper: Paper) -> bool:
    """验证论文数据的完整性"""
    return (
        paper.title and
        paper.authors and
        paper.year and
        paper.year > 1900 and
        paper.year <= 2024
    )
```

### 3. 结果过滤

```python
# 过滤高质量论文
high_quality_papers = [
    p for p in papers 
    if p.citation_count >= 10 and p.confidence_score >= 0.8
]

# 按年份过滤
recent_papers = [
    p for p in papers 
    if p.year >= 2020
]
```

### 4. 数据清理

```python
def clean_paper_data(paper: Paper) -> Paper:
    """清理论文数据"""
    # 清理标题
    paper.title = paper.title.strip()
    
    # 清理作者列表
    paper.authors = [author.strip() for author in paper.authors if author.strip()]
    
    # 清理摘要
    if paper.abstract:
        paper.abstract = paper.abstract.strip()
    
    return paper
```

## 常见问题

### Q: 搜索结果为空怎么办？
A: 检查搜索查询是否正确，尝试使用更通用的术语，或者调整搜索参数。

### Q: 如何避免被反爬虫检测？
A: 使用适当的延迟、随机用户代理、代理服务器，或者使用 Selenium 模式。

### Q: 如何处理大量数据？
A: 使用批量处理、分页加载、缓存机制，并考虑使用数据库存储。

### Q: 搜索结果不准确怎么办？
A: 优化搜索查询、使用高级搜索功能、调整搜索参数，或者使用多个搜索策略。

### Q: 如何提高搜索速度？
A: 使用缓存、减少结果数量、使用 requests 模式、优化网络连接。

## 集成示例

### 与 DOI 下载集成

```python
# 搜索论文并下载 PDF
async def search_and_download(query: str):
    # 搜索论文
    result = await crawler.search(query)
    
    # 提取有 DOI 的论文
    papers_with_doi = [p for p in result.papers if p.doi]
    
    # 下载 PDF
    from information_composer.core.doi_downloader import DOIDownloader
    downloader = DOIDownloader()
    
    for paper in papers_with_doi:
        download_result = downloader.download_single(paper.doi, "downloads")
        if download_result.downloaded:
            print(f"下载成功: {paper.title}")
```

### 与 PubMed 集成

```python
# 搜索并链接 PubMed
async def search_with_pubmed(query: str):
    config = SearchConfig(link_pubmed=True)
    
    async with GoogleScholarCrawler(config=config) as crawler:
        result = await crawler.search(query)
        
        # 处理有 PubMed ID 的论文
        pubmed_papers = [p for p in result.papers if p.pubmed_id]
        
        for paper in pubmed_papers:
            print(f"论文: {paper.title}")
            print(f"PubMed ID: {paper.pubmed_id}")
            print(f"DOI: {paper.doi}")
```

## 相关资源

- [Google Scholar 搜索技巧](https://scholar.google.com/intl/en/scholar/help.html)
- [information-composer Google Scholar 模块文档](../api/sites/google_scholar.md)
- [学术搜索最佳实践](https://libguides.usc.edu/c.php?g=234208&p=1556824)
- [反爬虫对策指南](https://docs.python-requests.org/en/latest/user/advanced.html#proxies)

## 更新日志

- **v1.0.0** - 初始版本，包含基础搜索功能
- **v1.1.0** - 添加高级搜索和批量处理
- **v1.2.0** - 增加数据导出和分析功能
- **v1.3.0** - 完善错误处理和性能优化

---

*最后更新：2024年12月*
