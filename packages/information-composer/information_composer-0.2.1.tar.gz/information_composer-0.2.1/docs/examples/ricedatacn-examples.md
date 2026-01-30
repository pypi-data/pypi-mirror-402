# RiceDataCN 示例文档

本文档详细介绍了 information-composer 项目中与 RiceDataCN（水稻数据中心）相关的示例代码。该示例展示了如何解析和处理水稻基因数据。

## 示例概览

### 水稻基因数据解析示例 (`ricedatacn_gene_example.py`)

**功能**：演示如何从 RiceDataCN 网站解析水稻基因数据。

**主要特性**：
- 单个基因数据解析
- 批量基因数据处理
- 错误处理和重试
- 数据导出功能
- 详细结果统计

**使用场景**：
- 水稻基因研究
- 批量基因数据收集
- 基因信息整合
- 生物信息学研究

**代码示例**：
```python
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

# 初始化解析器
parser = RiceGeneParser()

# 设置输出目录
output_dir = "downloads/genes"

# 解析单个基因
gene_info = parser.parse_gene_page("1", output_dir)

# 解析多个基因
gene_ids = ["1", "2", "3"]
results = parser.parse_multiple_genes(gene_ids, output_dir)
```

**运行方法**：
```bash
python examples/ricedatacn_gene_example.py
```

## 配置要求

### 依赖包

```bash
# 基础依赖
pip install information-composer

# 网页解析依赖
pip install beautifulsoup4 lxml requests
```

### 网络要求

- 需要能够访问 RiceDataCN 网站
- 稳定的网络连接
- 建议使用适当的请求延迟

## 功能说明

### RiceGeneParser 类

主要的解析类，提供水稻基因数据解析功能。

```python
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

# 初始化解析器
parser = RiceGeneParser()

# 解析单个基因
gene_info = parser.parse_gene_page(
    gene_id="1",
    output_dir="downloads/genes"
)

# 解析多个基因
gene_ids = ["1", "2", "3", "4", "5"]
results = parser.parse_multiple_genes(
    gene_ids=gene_ids,
    output_dir="downloads/genes"
)
```

### 数据结构

解析器返回的基因信息包含：

```python
{
    "gene_id": "1",              # 基因ID
    "gene_name": "Os01g0100100", # 基因名称
    "chromosome": "1",            # 染色体编号
    "position": "2983-10815",     # 基因位置
    "strand": "+",                # 正负链
    "description": "...",         # 基因描述
    "function": "...",            # 功能注释
    "go_terms": [...],           # GO术语
    "pathway": [...],            # 代谢通路
    "expression": {...},         # 表达数据
    "url": "https://...",        # 数据来源URL
}
```

## 使用示例

### 1. 基本解析

```python
#!/usr/bin/env python3
"""基本基因数据解析示例"""

import os
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

def basic_parse_example():
    """基本解析示例"""
    # 初始化解析器
    parser = RiceGeneParser()
    
    # 设置输出目录
    output_dir = os.path.join(os.getcwd(), "downloads", "genes")
    
    # 解析单个基因
    print("解析单个基因...")
    gene_id = "1"
    gene_info = parser.parse_gene_page(gene_id, output_dir)
    
    if gene_info:
        print(f"成功解析基因 {gene_id}")
        print(f"基因名称: {gene_info.get('gene_name', 'N/A')}")
        print(f"染色体: {gene_info.get('chromosome', 'N/A')}")
        print(f"位置: {gene_info.get('position', 'N/A')}")
    else:
        print(f"解析基因 {gene_id} 失败")

if __name__ == "__main__":
    basic_parse_example()
```

### 2. 批量解析

```python
#!/usr/bin/env python3
"""批量基因数据解析示例"""

import os
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

def batch_parse_example():
    """批量解析示例"""
    # 初始化解析器
    parser = RiceGeneParser()
    
    # 设置输出目录
    output_dir = os.path.join(os.getcwd(), "downloads", "genes")
    
    # 批量解析多个基因
    print("\n解析多个基因...")
    gene_ids = ["1", "2", "3", "4", "5"]
    results = parser.parse_multiple_genes(gene_ids, output_dir)
    
    # 打印详细摘要
    print("\n摘要:")
    success_count = len([r for r in results if r])
    print(f"成功解析 {success_count} / {len(gene_ids)} 个基因")
    print(f"失败 {len(gene_ids) - success_count} 个基因")
    
    # 打印详细结果
    print("\n详细结果:")
    for gene_id, result in zip(gene_ids, results):
        status = "成功" if result else "失败 (404 未找到)"
        print(f"基因 {gene_id}: {status}")

if __name__ == "__main__":
    batch_parse_example()
```

### 3. 错误处理

```python
#!/usr/bin/env python3
"""带错误处理的基因数据解析示例"""

import os
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

def parse_with_error_handling():
    """带错误处理的解析示例"""
    parser = RiceGeneParser()
    output_dir = os.path.join(os.getcwd(), "downloads", "genes")
    
    # 包含一些无效的基因ID
    gene_ids = ["1", "2", "3", "100000", "invalid"]
    
    results = {
        "success": [],
        "failed": [],
        "errors": {}
    }
    
    for gene_id in gene_ids:
        try:
            gene_info = parser.parse_gene_page(gene_id, output_dir)
            
            if gene_info:
                results["success"].append(gene_id)
                print(f"✓ 基因 {gene_id}: 解析成功")
            else:
                results["failed"].append(gene_id)
                results["errors"][gene_id] = "未找到或无法解析"
                print(f"✗ 基因 {gene_id}: 未找到")
                
        except Exception as e:
            results["failed"].append(gene_id)
            results["errors"][gene_id] = str(e)
            print(f"✗ 基因 {gene_id}: 错误 - {e}")
    
    # 打印摘要
    print(f"\n解析完成:")
    print(f"  成功: {len(results['success'])}")
    print(f"  失败: {len(results['failed'])}")
    
    if results["errors"]:
        print(f"\n错误详情:")
        for gene_id, error in results["errors"].items():
            print(f"  {gene_id}: {error}")
    
    return results

if __name__ == "__main__":
    parse_with_error_handling()
```

## 高级功能

### 1. 数据导出

```python
import json

def export_gene_data(gene_ids, output_dir):
    """导出基因数据"""
    parser = RiceGeneParser()
    results = parser.parse_multiple_genes(gene_ids, output_dir)
    
    # 过滤成功的结果
    valid_results = [r for r in results if r]
    
    # 导出为JSON
    output_file = os.path.join(output_dir, "gene_data.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(valid_results, f, indent=2, ensure_ascii=False)
    
    print(f"数据已导出到: {output_file}")
    return output_file
```

### 2. 数据分析

```python
def analyze_gene_data(gene_data_list):
    """分析基因数据"""
    analysis = {
        "total_genes": len(gene_data_list),
        "chromosomes": set(),
        "average_length": 0,
        "strands": {"forward": 0, "reverse": 0}
    }
    
    total_length = 0
    
    for gene in gene_data_list:
        if gene:
            # 收集染色体信息
            if "chromosome" in gene:
                analysis["chromosomes"].add(gene["chromosome"])
            
            # 计算基因长度
            if "position" in gene:
                try:
                    start, end = map(int, gene["position"].split("-"))
                    total_length += (end - start)
                except:
                    pass
            
            # 统计链方向
            if "strand" in gene:
                if gene["strand"] == "+":
                    analysis["strands"]["forward"] += 1
                else:
                    analysis["strands"]["reverse"] += 1
    
    # 计算平均长度
    if analysis["total_genes"] > 0:
        analysis["average_length"] = total_length / analysis["total_genes"]
    
    analysis["chromosomes"] = sorted(list(analysis["chromosomes"]))
    
    return analysis
```

### 3. 批量下载优化

```python
from time import sleep

def optimized_batch_download(gene_ids, output_dir, delay=1.0):
    """优化的批量下载"""
    parser = RiceGeneParser()
    results = []
    
    print(f"开始批量下载 {len(gene_ids)} 个基因数据...")
    
    for i, gene_id in enumerate(gene_ids, 1):
        print(f"进度: {i}/{len(gene_ids)} - 基因 {gene_id}")
        
        try:
            gene_info = parser.parse_gene_page(gene_id, output_dir)
            results.append(gene_info)
            
            # 添加延迟以避免过于频繁的请求
            if i < len(gene_ids):
                sleep(delay)
                
        except Exception as e:
            print(f"  错误: {e}")
            results.append(None)
    
    return results
```

## 性能优化

### 1. 请求延迟

```python
# 设置适当的请求延迟
parser = RiceGeneParser()

# 批量处理时使用延迟
for gene_id in gene_ids:
    gene_info = parser.parse_gene_page(gene_id, output_dir)
    time.sleep(1)  # 1秒延迟
```

### 2. 缓存机制

```python
import json
from pathlib import Path

def cached_parse_gene(gene_id, output_dir, parser, cache_dir="cache"):
    """带缓存的基因解析"""
    cache_file = Path(cache_dir) / f"gene_{gene_id}.json"
    
    # 检查缓存
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # 解析基因
    gene_info = parser.parse_gene_page(gene_id, output_dir)
    
    # 保存到缓存
    if gene_info:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(gene_info, f, indent=2, ensure_ascii=False)
    
    return gene_info
```

### 3. 并行处理

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_parse_genes(gene_ids, output_dir, max_workers=3):
    """并行解析基因数据"""
    parser = RiceGeneParser()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda gid: parser.parse_gene_page(gid, output_dir),
            gene_ids
        ))
    
    return results
```

## 最佳实践

### 1. 网络请求

```python
# 使用适当的延迟
time.sleep(1)  # 每次请求间隔1秒

# 实现重试机制
def parse_with_retry(gene_id, output_dir, max_retries=3):
    """带重试的解析函数"""
    parser = RiceGeneParser()
    
    for attempt in range(max_retries):
        try:
            return parser.parse_gene_page(gene_id, output_dir)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"重试 {attempt + 1}/{max_retries}: {e}")
            time.sleep(2 ** attempt)  # 指数退避
```

### 2. 数据验证

```python
def validate_gene_data(gene_info):
    """验证基因数据完整性"""
    required_fields = ["gene_id", "gene_name", "chromosome"]
    
    if not gene_info:
        return False, "数据为空"
    
    for field in required_fields:
        if field not in gene_info or not gene_info[field]:
            return False, f"缺少必需字段: {field}"
    
    return True, "数据有效"
```

### 3. 错误日志

```python
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='gene_parsing.log'
)

logger = logging.getLogger(__name__)

def parse_with_logging(gene_id, output_dir):
    """带日志记录的解析"""
    logger.info(f"开始解析基因 {gene_id}")
    
    try:
        gene_info = parser.parse_gene_page(gene_id, output_dir)
        logger.info(f"成功解析基因 {gene_id}")
        return gene_info
    except Exception as e:
        logger.error(f"解析基因 {gene_id} 失败: {e}")
        return None
```

## 常见问题

### Q: 如何处理404错误？
A: 404错误通常表示基因ID不存在。解析器会返回 None，并在日志中记录。

### Q: 解析速度慢怎么办？
A: 使用并行处理、减少请求延迟（但要注意不要过于频繁）、或使用缓存机制。

### Q: 如何验证数据完整性？
A: 检查返回的数据是否包含必需字段，使用验证函数确保数据质量。

### Q: 网络错误如何处理？
A: 实现重试机制、使用异常捕获、记录错误日志，必要时使用代理。

## 相关资源

- [RiceDataCN 官网](http://www.ricedatacn.cn/)
- [水稻基因组数据库](https://rapdb.dna.affrc.go.jp/)
- [information-composer RiceDataCN 模块文档](../api/sites/ricedatacn.md)
- [生物信息学数据解析指南](https://bioinformatics.org/)

## 更新日志

- **v1.0.0** - 初始版本，包含基础解析功能
- **v1.1.0** - 添加批量处理和错误处理
- **v1.2.0** - 增加数据导出和分析功能
- **v1.3.0** - 完善性能优化和缓存机制

---

*最后更新：2024年12月*
