# LLM 过滤示例文档

本文档详细介绍了 information-composer 项目中与 LLM（大语言模型）智能过滤相关的示例代码。这些示例展示了如何使用 LLM 进行智能内容过滤和处理。

## 示例概览

### LLM 智能过滤示例 (`llm_filter_example.py`)

**功能**：演示如何使用 LLM 进行智能内容过滤。

**主要特性**：
- 基于 LLM 的智能过滤
- 支持 DashScope 模型
- 保留核心学术内容
- 过滤冗余信息
- 支持批量处理
- 提供统计信息
- 支持多种输出格式

**使用场景**：
- 学术论文内容过滤
- 文档摘要和精简
- 内容质量提升
- 自动化文档处理

**代码示例**：
```python
from information_composer.llm_filter.core.filter import MarkdownFilter

# 创建过滤器实例
filter_obj = MarkdownFilter(model="qwen-plus-latest")

# 过滤内容
filtered_content = await filter_obj.filter_paper(sample_content)

# 获取过滤统计
filter_stats = filter_obj.get_filter_statistics(
    sample_content, filtered_content
)
```

**运行方法**：
```bash
python examples/llm_filter_example.py
```

## 配置要求

### 环境变量

```bash
# DashScope API 密钥（必需）
export DASHSCOPE_API_KEY="your-dashscope-api-key"

# 可选配置
export DASHSCOPE_MODEL="qwen-plus-latest"
export LOG_LEVEL="INFO"
```

### 依赖包

```bash
# 基础依赖
pip install information-composer

# LLM 相关依赖
pip install llama-index-llms-dashscope

# 可选依赖
pip install nltk spacy  # 用于文本处理
```

## 功能说明

### MarkdownFilter 类

主要的过滤类，提供智能内容过滤功能。

```python
from information_composer.llm_filter.core.filter import MarkdownFilter

# 创建过滤器实例
filter_obj = MarkdownFilter(model="qwen-plus-latest")

# 过滤单个文档
filtered_content = await filter_obj.filter_paper(content)

# 批量过滤文件
output_files = filter_obj.filter_files(
    input_dir="input_docs",
    output_dir="filtered_docs",
    file_pattern="*.md"
)
```

### 配置选项

```python
from information_composer.llm_filter.config.settings import AppConfig

# 创建配置
config = AppConfig()

# 设置 DashScope API 密钥
config.dashscope.api_key = "your-api-key"
config.dashscope.model = "qwen-plus"
config.dashscope.temperature = 0.1
config.dashscope.max_tokens = 4096

# 设置处理选项
config.processing.input_dir = "/path/to/input"
config.processing.output_dir = "/path/to/output"
config.processing.file_pattern = "*.md"
config.processing.recursive = True
config.processing.output_format = "markdown"
config.processing.overwrite = False
config.processing.backup = True
```

## 使用示例

### 1. 基本使用

```python
#!/usr/bin/env python3
"""LLM 过滤基本使用示例"""

import asyncio
from information_composer.llm_filter.core.filter import MarkdownFilter

async def basic_filter_example():
    """基本过滤示例"""
    # 创建过滤器
    filter_obj = MarkdownFilter(model="qwen-plus-latest")
    
    # 示例内容
    sample_content = """# 基于深度学习的图像识别研究
    
    ## 摘要
    
    本文提出了一种基于深度学习的图像识别方法...
    
    ## 引言
    
    图像识别是计算机视觉领域的重要研究方向...
    
    ## 方法
    
    我们提出的方法包括以下步骤：
    1. 数据预处理
    2. 模型设计
    3. 训练策略
    4. 评估指标
    
    ## 结果
    
    在CIFAR-10数据集上，我们的方法达到了95.2%的准确率...
    
    ## 讨论
    
    实验结果表明，我们提出的方法在多个方面都有显著改进...
    
    ## 结论
    
    本文提出的基于深度学习的图像识别方法在多个数据集上都取得了优异的性能...
    
    ## 参考文献
    
    [1] LeCun, Y., et al. (2015). Deep learning. Nature, 521(7553), 436-444.
    [2] Krizhevsky, A., et al. (2012). ImageNet classification with deep convolutional neural networks...
    
    ## 致谢
    
    感谢所有参与实验的同事和提供数据支持的研究机构...
    
    ## 附录
    
    详细的实验参数设置如下...
    """
    
    # 过滤内容
    filtered_content = await filter_obj.filter_paper(sample_content)
    
    # 显示结果
    print("过滤后的内容:")
    print(filtered_content)
    
    # 获取统计信息
    stats = filter_obj.get_filter_statistics(sample_content, filtered_content)
    print(f"\n过滤统计:")
    print(f"行数减少: {stats['lines_reduction']} ({stats['lines_reduction_percent']:.1f}%)")
    print(f"字符数减少: {stats['chars_reduction']} ({stats['chars_reduction_percent']:.1f}%)")
    print(f"压缩比: {stats['compression_ratio']:.3f}")

# 运行示例
if __name__ == "__main__":
    asyncio.run(basic_filter_example())
```

### 2. 批量处理

```python
#!/usr/bin/env python3
"""LLM 过滤批量处理示例"""

import asyncio
from pathlib import Path
from information_composer.llm_filter.core.filter import MarkdownFilter

async def batch_filter_example():
    """批量过滤示例"""
    # 创建过滤器
    filter_obj = MarkdownFilter(model="qwen-plus-latest")
    
    # 批量处理文件
    output_files = await filter_obj.filter_files(
        input_dir="input_documents",
        output_dir="filtered_documents",
        file_pattern="*.md",
        recursive=True
    )
    
    print(f"处理完成，共处理 {len(output_files)} 个文件")
    
    # 显示处理结果
    for output_file in output_files:
        print(f"输出文件: {output_file}")

# 运行示例
if __name__ == "__main__":
    asyncio.run(batch_filter_example())
```

### 3. 自定义过滤规则

```python
#!/usr/bin/env python3
"""自定义 LLM 过滤规则示例"""

import asyncio
from information_composer.llm_filter.core.filter import MarkdownFilter

async def custom_filter_example():
    """自定义过滤规则示例"""
    # 创建过滤器
    filter_obj = MarkdownFilter(model="qwen-plus-latest")
    
    # 自定义过滤提示
    custom_prompt = """
    请过滤这篇学术论文，只保留以下内容：
    
    保留：
    1. 摘要和引言
    2. 方法论部分
    3. 关键发现和结果
    4. 结论
    
    移除：
    - 参考文献和引用
    - 致谢
    - 附录
    - 非必要细节
    """
    
    # 读取文档
    with open("paper.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 应用自定义过滤
    filtered_content = await filter_obj.filter_paper(
        content, 
        custom_prompt=custom_prompt
    )
    
    # 保存结果
    with open("filtered_paper.md", "w", encoding="utf-8") as f:
        f.write(filtered_content)
    
    print("自定义过滤完成！")

# 运行示例
if __name__ == "__main__":
    asyncio.run(custom_filter_example())
```

## CLI 使用

### 基本命令

```bash
# 过滤单个文件
md-llm-filter input.md -o output.md

# 过滤多个文件
md-llm-filter input_dir/ -o output_dir/

# 使用特定模型
md-llm-filter input.md -o output.md --model qwen-plus

# 设置自定义温度
md-llm-filter input.md -o output.md --temperature 0.1
```

### 高级选项

```bash
# 递归处理
md-llm-filter input_dir/ -o output_dir/ --recursive

# 特定文件模式
md-llm-filter input_dir/ -o output_dir/ --pattern "*.txt"

# 覆盖现有文件
md-llm-filter input_dir/ -o output_dir/ --overwrite

# 启用备份
md-llm-filter input_dir/ -o output_dir/ --backup

# 调试模式
md-llm-filter input_dir/ -o output_dir/ --debug

# 详细输出
md-llm-filter input_dir/ -o output_dir/ --verbose
```

### 配置文件

```bash
# 使用配置文件
md-llm-filter input_dir/ -o output_dir/ --config config.json

# 保存当前配置
md-llm-filter --save-config config.json
```

## 高级功能

### 1. 内容提取

```python
from information_composer.llm_filter.core.extractor import ContentExtractor

# 初始化提取器
extractor = ContentExtractor(config)

# 提取特定部分
abstract = extractor.extract_section(content, "abstract")
methodology = extractor.extract_section(content, "methodology")
results = extractor.extract_section(content, "results")
```

### 2. 结构化数据提取

```python
# 定义提取模式
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "abstract": {"type": "string"},
        "publication_date": {"type": "string"}
    }
}

# 提取结构化数据
structured_data = extractor.extract_structured_data(content, schema)
```

### 3. 文本分析

```python
from information_composer.llm_filter.utils.text_processing import (
    extract_keywords,
    calculate_readability_score,
    summarize_text
)

# 提取关键词
keywords = extract_keywords(content, top_k=10)

# 计算可读性分数
readability = calculate_readability_score(content)

# 总结文本
summary = summarize_text(content, max_length=200)
```

## 性能优化

### 1. 批量处理

```python
# 分批处理文件
batch_size = 10
files = list(input_dir.glob("*.md"))

for i in range(0, len(files), batch_size):
    batch = files[i:i + batch_size]
    
    for file_path in batch:
        try:
            result = await filter_obj.filter_file(file_path)
            print(f"处理完成: {file_path}")
        except Exception as e:
            print(f"处理失败 {file_path}: {e}")
    
    # 批次间延迟
    await asyncio.sleep(1)
```

### 2. 缓存机制

```python
# 启用缓存
config.cache_enabled = True
config.cache_dir = "./cache"
config.cache_ttl_hours = 24
```

### 3. 内存管理

```python
# 处理大文件时使用分块
def process_large_file(file_path, chunk_size=1000):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    
    results = []
    for chunk in chunks:
        result = await filter_obj.filter_paper(chunk)
        results.append(result)
    
    return '\n'.join(results)
```

## 错误处理

### 1. API 错误

```python
def safe_filter_content(text, max_retries=3):
    """安全的过滤函数"""
    for attempt in range(max_retries):
        try:
            return await filter_obj.filter_paper(text)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"过滤失败，重试 {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

### 2. 输入验证

```python
def validate_input(text):
    """验证输入文本"""
    if not text or len(text.strip()) == 0:
        raise ValueError("输入文本不能为空")
    
    if len(text) > 100000:  # 限制文本长度
        raise ValueError("输入文本过长，请分段处理")
    
    return True
```

## 最佳实践

### 1. 配置管理

```python
# 使用环境变量
import os

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")

config.dashscope.api_key = api_key
```

### 2. 日志记录

```python
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 记录处理进度
logger.info(f"开始处理文件: {file_path}")
result = await filter_obj.filter_paper(content)
logger.info(f"处理完成: {file_path}")
```

### 3. 资源管理

```python
# 使用上下文管理器
async with filter_obj as fp:
    result = await fp.filter_paper(content)
```

## 常见问题

### Q: 如何获取 DashScope API 密钥？
A: 访问阿里云 DashScope 官网注册账号并申请 API 密钥。

### Q: 过滤效果不理想怎么办？
A: 尝试调整模型参数、使用自定义提示词、或者选择不同的模型。

### Q: 处理大文件时内存不足怎么办？
A: 使用分块处理、减少批处理大小、或者使用流式处理。

### Q: 如何提高处理速度？
A: 使用缓存、批量处理、选择合适的模型、优化网络连接。

## 相关资源

- [DashScope 官方文档](https://help.aliyun.com/zh/dashscope/)
- [information-composer LLM 模块文档](../api/llm_filter/)
- [大语言模型使用指南](https://docs.llamaindex.ai/en/stable/)
- [文本处理最佳实践](https://spacy.io/usage/processing-pipelines)

## 更新日志

- **v1.0.0** - 初始版本，包含基础过滤功能
- **v1.1.0** - 添加批量处理和自定义规则
- **v1.2.0** - 增加内容提取和分析功能
- **v1.3.0** - 完善错误处理和性能优化

---

*最后更新：2024年12月*
