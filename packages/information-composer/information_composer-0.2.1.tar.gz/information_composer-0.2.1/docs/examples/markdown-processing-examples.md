# Markdown 处理示例文档

本文档详细介绍了 information-composer 项目中与 Markdown 处理相关的所有示例代码。这些示例展示了如何转换、过滤和处理 Markdown 文档。

## 示例概览

### 1. Markdown 转换示例 (`markdown_converter.py`)

**功能**：演示如何将 Markdown 文件转换为 JSON 格式。

**主要特性**：
- Markdown 到 JSON 的转换
- 文件路径处理
- 错误处理
- 格式化输出

**使用场景**：
- 文档格式转换
- 数据提取和分析
- 文档处理自动化

**代码示例**：
```python
from information_composer.markdown import jsonify

def convert_markdown_to_json(markdown_file_path: str, json_output_path: str = None):
    """将 Markdown 文件转换为 JSON 格式"""
    # 读取 Markdown 文件
    with open(markdown_file_path, encoding="utf-8") as f:
        markdown_content = f.read()
    
    # 转换为 JSON
    json_content = jsonify(markdown_content)
    
    # 保存 JSON 文件
    if json_output_path:
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(json.loads(json_content), f, indent=2, ensure_ascii=False)
    
    return json_content
```

**运行方法**：
```bash
python examples/markdown_converter.py
```

### 2. Markdown 引用过滤示例 (`markdown_filter_ref.py`)

**功能**：演示如何过滤 Markdown 文档中的引用和致谢部分。

**主要特性**：
- 批量文件处理
- 关键词过滤
- 文本清理
- 统计信息导出

**使用场景**：
- 学术论文处理
- 文档清理
- 内容过滤

**代码示例**：
```python
from information_composer.markdown import dictify, markdownify

def filter_markdown_files(markdown_files, output_dir, filters):
    """过滤 Markdown 文件中的指定内容"""
    for markdown_file in markdown_files:
        with open(markdown_file, encoding="utf-8") as f:
            markdown_content = f.read()
        
        # 转换为字典格式
        dict_content = dictify(markdown_content)
        
        # 过滤指定关键词
        keys_to_delete = [
            key for key in dict_content 
            if any(f in key.lower() for f in filters)
        ]
        
        # 删除过滤的键
        for key in keys_to_delete:
            del dict_content[key]
        
        # 转换回 Markdown
        json_content = json.dumps(dict_content)
        markdown_content = markdownify(json_content)
        
        # 保存过滤后的文件
        output_file = os.path.join(output_dir, 
            os.path.basename(markdown_file).replace(".md", "_filtered.md"))
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
```

**运行方法**：
```bash
python examples/markdown_filter_ref.py
```

## 配置要求

### 依赖包

```bash
# 基础依赖
pip install information-composer

# 可选依赖
pip install pandas  # 用于数据分析
```

## 功能说明

### Markdown 转换功能

#### jsonify 函数
将 Markdown 内容转换为 JSON 格式，保留文档结构。

```python
from information_composer.markdown import jsonify

# 转换 Markdown 为 JSON
markdown_text = "# 标题\n\n这是内容"
json_result = jsonify(markdown_text)
```

#### dictify 函数
将 Markdown 内容转换为字典格式，便于程序处理。

```python
from information_composer.markdown import dictify

# 转换 Markdown 为字典
markdown_text = "# 标题\n\n这是内容"
dict_result = dictify(markdown_text)
```

#### markdownify 函数
将 JSON 或字典内容转换回 Markdown 格式。

```python
from information_composer.markdown import markdownify

# 转换字典为 Markdown
dict_content = {"title": "标题", "content": "内容"}
markdown_result = markdownify(json.dumps(dict_content))
```

### 过滤功能

#### 关键词过滤
根据指定的关键词列表过滤文档内容。

```python
# 定义过滤关键词
filters = [
    "reference",
    "acknowledgments", 
    "funding",
    "license",
    "author contributions"
]

# 过滤文档
filtered_content = filter_by_keywords(content, filters)
```

#### 文本清理
清理和标准化文本内容。

```python
def clean_text(text):
    """清理文本，移除多余的换行和空格"""
    if pd.isna(text):
        return ""
    return " ".join(str(text).split())
```

## 使用示例

### 1. 基本转换

```python
#!/usr/bin/env python3
"""基本 Markdown 转换示例"""

from information_composer.markdown import jsonify

# 读取 Markdown 文件
with open("document.md", "r", encoding="utf-8") as f:
    markdown_content = f.read()

# 转换为 JSON
json_content = jsonify(markdown_content)

# 保存结果
with open("document.json", "w", encoding="utf-8") as f:
    json.dump(json.loads(json_content), f, indent=2, ensure_ascii=False)

print("转换完成！")
```

### 2. 批量处理

```python
#!/usr/bin/env python3
"""批量 Markdown 处理示例"""

import os
from glob import glob
from information_composer.markdown import dictify, markdownify

def process_markdown_files(input_dir, output_dir):
    """批量处理 Markdown 文件"""
    # 获取所有 Markdown 文件
    markdown_files = glob(os.path.join(input_dir, "*.md"))
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    for markdown_file in markdown_files:
        # 处理每个文件
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 转换为字典
        dict_content = dictify(content)
        
        # 处理内容（例如：过滤特定部分）
        # ... 处理逻辑 ...
        
        # 转换回 Markdown
        processed_content = markdownify(json.dumps(dict_content))
        
        # 保存处理后的文件
        output_file = os.path.join(output_dir, 
            os.path.basename(markdown_file))
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(processed_content)
        
        print(f"处理完成: {markdown_file}")

# 使用示例
process_markdown_files("input_docs", "output_docs")
```

### 3. 内容过滤

```python
#!/usr/bin/env python3
"""Markdown 内容过滤示例"""

from information_composer.markdown import dictify, markdownify

def filter_academic_content(markdown_content, filters):
    """过滤学术内容"""
    # 转换为字典
    dict_content = dictify(markdown_content)
    
    # 定义要过滤的键
    keys_to_remove = [
        "references",
        "acknowledgments",
        "funding",
        "author contributions",
        "conflicts of interest"
    ]
    
    # 过滤内容
    filtered_content = {}
    for key, value in dict_content.items():
        if not any(filter_key in key.lower() for filter_key in keys_to_remove):
            filtered_content[key] = value
    
    # 转换回 Markdown
    return markdownify(json.dumps(filtered_content))

# 使用示例
with open("paper.md", "r", encoding="utf-8") as f:
    content = f.read()

filtered_content = filter_academic_content(content, [])
print(filtered_content)
```

## 高级功能

### 1. 文档结构分析

```python
def analyze_document_structure(markdown_content):
    """分析文档结构"""
    dict_content = dictify(markdown_content)
    
    structure = {
        "total_sections": len(dict_content),
        "sections": list(dict_content.keys()),
        "has_references": any("reference" in key.lower() for key in dict_content),
        "has_abstract": any("abstract" in key.lower() for key in dict_content),
        "has_conclusion": any("conclusion" in key.lower() for key in dict_content)
    }
    
    return structure
```

### 2. 内容统计

```python
def get_content_statistics(markdown_content):
    """获取内容统计信息"""
    dict_content = dictify(markdown_content)
    
    stats = {
        "total_sections": len(dict_content),
        "total_words": sum(len(str(value).split()) for value in dict_content.values()),
        "average_section_length": sum(len(str(value)) for value in dict_content.values()) / len(dict_content),
        "longest_section": max(dict_content.keys(), key=lambda k: len(str(dict_content[k])))
    }
    
    return stats
```

### 3. 内容验证

```python
def validate_document_content(markdown_content):
    """验证文档内容"""
    dict_content = dictify(markdown_content)
    
    issues = []
    
    # 检查必需部分
    required_sections = ["title", "abstract", "introduction", "conclusion"]
    for section in required_sections:
        if not any(section in key.lower() for key in dict_content):
            issues.append(f"缺少必需部分: {section}")
    
    # 检查内容长度
    for key, value in dict_content.items():
        if len(str(value)) < 10:
            issues.append(f"部分内容过短: {key}")
    
    return issues
```

## 最佳实践

### 1. 文件处理

```python
# 使用适当的编码
with open("document.md", "r", encoding="utf-8") as f:
    content = f.read()

# 处理文件路径
from pathlib import Path
input_path = Path("input.md")
output_path = Path("output.json")
```

### 2. 错误处理

```python
def safe_convert_markdown(markdown_content):
    """安全的 Markdown 转换"""
    try:
        return jsonify(markdown_content)
    except Exception as e:
        print(f"转换失败: {e}")
        return None
```

### 3. 性能优化

```python
# 批量处理时使用生成器
def process_large_dataset(files):
    for file_path in files:
        yield process_file(file_path)
```

## 常见问题

### Q: 转换后的 JSON 格式是什么？
A: 转换后的 JSON 是一个对象，键为文档的标题或章节名，值为对应的内容。

### Q: 如何处理特殊字符？
A: 使用 `ensure_ascii=False` 参数保持 Unicode 字符，确保中文等特殊字符正确显示。

### Q: 如何自定义过滤规则？
A: 修改 `filters` 列表，添加或删除需要过滤的关键词。

### Q: 转换失败怎么办？
A: 检查 Markdown 格式是否正确，确保文件编码为 UTF-8，查看错误信息进行调试。

## 相关资源

- [Markdown 语法指南](https://www.markdownguide.org/)
- [information-composer Markdown 模块文档](../api/markdown/)
- [JSON 格式规范](https://www.json.org/)
- [Python 文件处理最佳实践](https://docs.python.org/3/tutorial/inputoutput.html)

## 更新日志

- **v1.0.0** - 初始版本，包含基础转换功能
- **v1.1.0** - 添加过滤和清理功能
- **v1.2.0** - 增加批量处理和统计功能
- **v1.3.0** - 完善错误处理和性能优化

---

*最后更新：2024年12月*
