# DOI 下载示例文档

本文档详细介绍了 information-composer 项目中与 DOI（数字对象标识符）下载相关的所有示例代码。这些示例展示了如何通过 DOI 下载学术论文的完整工作流程。

## 示例概览

### 1. 单个 DOI 下载示例 (`doi_download_single.py`)

**功能**：演示如何使用 DOI 下载单个学术论文。

**主要特性**：
- 单个论文下载流程
- 结果验证和错误处理
- CSV 导出用于结果跟踪
- 文件组织和命名

**使用场景**：
- 下载特定论文
- 测试 DOI 下载功能
- 学习基本下载流程

**代码示例**：
```python
from information_composer.core.doi_downloader import DOIDownloader

# 初始化下载器
downloader = DOIDownloader(email="your_email@example.com")

# 下载单个论文
result = downloader.download_single(
    doi="10.1093/jxb/erad499",
    output_dir="downloads"
)
```

**运行方法**：
```bash
python examples/doi_download_single.py
```

### 2. DOI 批量下载示例 (`doi_download_example.py`)

**功能**：演示如何批量下载多个学术论文。

**主要特性**：
- 单个和批量下载工作流程
- 进度跟踪和错误处理
- CSV 导出用于结果分析
- 文件组织和命名

**使用场景**：
- 批量下载论文集合
- 学术研究项目
- 文献数据库构建

**代码示例**：
```python
# 批量下载多个论文
dois = [
    "10.1038/s41477-024-01771-3",
    "10.1038/s41592-024-02305-7",
    "10.1038/s41592-024-02201-0",
]

results = downloader.download_batch(
    dois=dois,
    output_dir="papers",
    delay=2  # 2秒延迟以遵守速率限制
)
```

**运行方法**：
```bash
python examples/doi_download_example.py
```

### 3. 结合 PubMed 的 DOI 下载示例 (`doi_download_by_using_pubmed_batch_example.py`)

**功能**：演示如何从 PubMed 批量结果中提取 DOIs 并下载对应论文。

**主要特性**：
- 从 PubMed 结果加载 DOIs
- 过滤有效 DOIs
- 批量 DOI 下载
- 结果验证和错误处理

**使用场景**：
- 基于 PubMed 查询结果的论文下载
- 学术研究项目的数据收集
- 文献数据库的自动化构建

**代码示例**：
```python
import json
from information_composer.core.doi_downloader import DOIDownloader

# 从 PubMed 结果加载 DOIs
with open("pubmed_results.json") as f:
    pubmed_data = json.load(f)

# 提取有效 DOIs
dois = [item["doi"] for item in pubmed_data if item["doi"] != "N/A"]

# 下载论文
downloader = DOIDownloader(email="your_email@example.com")
results = downloader.download_batch(dois=dois, output_dir="papers")
```

**运行方法**：
```bash
python examples/doi_download_by_using_pubmed_batch_example.py
```

## 配置要求

### 环境变量

```bash
# Crossref API 邮箱（推荐）
export CROSSREF_EMAIL="your-email@example.com"
```

### 依赖包

```bash
# 基础依赖
pip install information-composer

# 可选依赖
pip install tqdm  # 用于进度条显示
```

## 下载结果说明

### DownloadResult 对象

每个下载操作返回一个 `DownloadResult` 对象，包含以下信息：

```python
class DownloadResult:
    doi: str                    # DOI 标识符
    downloaded: bool           # 是否成功下载
    file_name: str             # 下载的文件名
    file_size: int             # 文件大小（字节）
    error_message: str         # 错误信息（如果有）
```

### 常见错误类型

1. **访问被拒绝**：论文需要订阅或付费
2. **DOI 未找到**：无效或不存在的 DOI
3. **访问受限**：重定向到登录或付费页面
4. **网络错误**：SSL、连接或超时问题

### 错误处理示例

```python
def download_with_error_handling(doi: str, output_dir: str):
    """带错误处理的下载函数"""
    result = downloader.download_single(doi, output_dir)
    
    if result.downloaded:
        print(f"✓ 成功下载: {result.file_name}")
        return True
    else:
        error_msg = result.error_message or "未知错误"
        if "subscription" in error_msg.lower():
            print(f"✗ {doi}: 需要订阅")
        elif "not found" in error_msg.lower():
            print(f"✗ {doi}: DOI 未找到")
        elif "access" in error_msg.lower():
            print(f"✗ {doi}: 访问受限")
        else:
            print(f"✗ {doi}: {error_msg}")
        return False
```

## 性能优化

### 1. 速率限制

Crossref API 有速率限制，下载器包含内置延迟：

```python
# 保守延迟（推荐用于大批量）
results = downloader.download_batch(dois, "papers", delay=3)

# 较快延迟（谨慎使用）
results = downloader.download_batch(dois, "papers", delay=1)
```

### 2. 批量处理

```python
def robust_batch_download(dois: list, output_dir: str, delay: int = 2):
    """健壮的批量下载函数"""
    print(f"开始批量下载 {len(dois)} 篇论文...")
    
    # 验证 DOIs
    valid_dois = [doi for doi in dois if doi and doi.strip()]
    
    if not valid_dois:
        print("没有有效的 DOIs")
        return []
    
    # 下载并跟踪进度
    results = downloader.download_batch(valid_dois, output_dir, delay)
    
    # 显示摘要
    successful = [r for r in results if r.downloaded]
    print(f"批量下载完成:")
    print(f"  总计: {len(results)}")
    print(f"  成功: {len(successful)}")
    print(f"  失败: {len(results) - len(successful)}")
    
    return results
```

### 3. 结果分析

```python
import pandas as pd

def analyze_download_results(results):
    """分析下载结果"""
    data = []
    for result in results:
        data.append({
            "doi": result.doi,
            "downloaded": result.downloaded,
            "file_name": result.file_name,
            "file_size": result.file_size,
            "error_message": result.error_message
        })
    
    df = pd.DataFrame(data)
    
    # 分析
    print("下载分析:")
    print(f"成功率: {df['downloaded'].mean():.2%}")
    print(f"平均文件大小: {df[df['downloaded']]['file_size'].mean():.0f} 字节")
    
    # 保存报告
    df.to_csv("download_report.csv", index=False)
    
    return df
```

## 最佳实践

### 1. 使用邮箱
```python
# 始终提供邮箱地址以获得更好的服务
downloader = DOIDownloader(email="your-email@example.com")
```

### 2. 尊重速率限制
```python
# 使用适当的延迟
results = downloader.download_batch(dois, "papers", delay=2)
```

### 3. 处理错误
```python
# 始终检查下载结果
for result in results:
    if result.downloaded:
        print(f"成功: {result.file_name}")
    else:
        print(f"失败: {result.doi} - {result.error_message}")
```

### 4. 验证 DOIs
```python
# 确保 DOIs 格式正确
def validate_doi(doi: str) -> bool:
    """验证 DOI 格式"""
    return doi and doi.strip() and doi.startswith("10.")
```

### 5. 监控进度
```python
# 使用进度条显示下载进度
from tqdm import tqdm

for doi in tqdm(dois, desc="下载论文"):
    result = downloader.download_single(doi, output_dir)
    # 处理结果
```

## 常见问题

### Q: 为什么某些论文下载失败？
A: 可能的原因包括：需要订阅访问、DOI 无效、网络问题、服务器错误等。检查错误信息以确定具体原因。

### Q: 如何提高下载成功率？
A: 使用有效的邮箱地址、遵守速率限制、检查 DOI 格式、确保网络连接稳定。

### Q: 下载的文件保存在哪里？
A: 文件保存在指定的输出目录中，文件名通常基于 DOI 或论文标题生成。

### Q: 如何处理大量 DOIs？
A: 使用批量下载功能，设置适当的延迟，考虑分批处理以避免内存问题。

### Q: 如何恢复中断的下载？
A: 检查已下载的文件，只处理未下载的 DOIs，或者使用缓存机制。

## 集成示例

### 与文件管理集成

```python
import os
from pathlib import Path

def download_and_organize(dois: list, base_dir: str):
    """下载论文并按年份组织"""
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    for doi in dois:
        # 创建基于年份的子目录
        year_dir = base_path / "2024"  # 可以从 DOI 提取年份
        year_dir.mkdir(exist_ok=True)
        
        result = downloader.download_single(doi, year_dir)
        if result.downloaded:
            print(f"下载到: {result.file_name}")
        else:
            print(f"下载失败 {doi}: {result.error_message}")
```

### 与数据分析集成

```python
import pandas as pd

def download_and_analyze(dois: list, output_dir: str):
    """下载论文并创建分析报告"""
    results = downloader.download_batch(dois, output_dir)
    
    # 转换为 DataFrame 进行分析
    data = []
    for result in results:
        data.append({
            "doi": result.doi,
            "downloaded": result.downloaded,
            "file_name": result.file_name,
            "file_size": result.file_size,
            "error_message": result.error_message
        })
    
    df = pd.DataFrame(data)
    
    # 分析
    print("下载分析:")
    print(f"成功率: {df['downloaded'].mean():.2%}")
    print(f"平均文件大小: {df[df['downloaded']]['file_size'].mean():.0f} 字节")
    
    # 保存报告
    df.to_csv(f"{output_dir}/download_report.csv", index=False)
    
    return df
```

## 相关资源

- [Crossref API 文档](https://www.crossref.org/documentation/retrieve-metadata/)
- [DOI 系统介绍](https://www.doi.org/)
- [information-composer DOI 模块文档](../api/core/doi_downloader.md)
- [学术论文下载最佳实践](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)

## 更新日志

- **v1.0.0** - 初始版本，包含基础下载功能
- **v1.1.0** - 添加批量下载和错误处理
- **v1.2.0** - 增加与 PubMed 的集成
- **v1.3.0** - 完善性能优化和结果分析

---

*最后更新：2024年12月*
