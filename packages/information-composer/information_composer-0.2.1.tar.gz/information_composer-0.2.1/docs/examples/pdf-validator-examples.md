# PDF 验证示例文档

本文档详细介绍了 information-composer 项目中与 PDF 文件验证相关的示例代码。该示例展示了如何验证 PDF 文件的格式和完整性。

## 示例概览

### PDF 验证示例 (`pdf_validator_example.py`)

**功能**：演示如何使用 PDF 验证器验证 PDF 文件。

**主要特性**：
- PDF 文件格式验证
- 批量文件处理
- 目录递归搜索
- 详细错误报告
- 统计信息输出
- JSON 格式输出
- CLI 命令行工具

**使用场景**：
- 验证下载的 PDF 文件
- 批量检查 PDF 文件质量
- 文件完整性检查
- 自动化文件验证

**代码示例**：
```python
from information_composer.pdf.validator import PDFValidator

# 创建验证器实例
validator = PDFValidator(verbose=True)

# 验证单个文件
is_valid, error_msg = validator.validate_single_pdf("sample.pdf")

if is_valid:
    print("✅ 文件验证通过")
else:
    print(f"❌ 文件验证失败: {error_msg}")
```

**运行方法**：
```bash
python examples/pdf_validator_example.py
```

## 配置要求

### 依赖包

```bash
# 基础依赖
pip install information-composer

# PDF 处理依赖
pip install pypdfium2
```

## 功能说明

### PDFValidator 类

主要的验证类，提供 PDF 文件验证功能。

```python
from information_composer.pdf.validator import PDFValidator

# 创建验证器实例
validator = PDFValidator(verbose=True)

# 验证单个文件
is_valid, error_msg = validator.validate_single_pdf("file.pdf")

# 验证多个文件
validator.validate_files(["file1.pdf", "file2.pdf", "file3.pdf"])

# 验证目录
validator.validate_directory("/path/to/directory", recursive=True)

# 获取统计信息
stats = validator.get_validation_stats()
```

### 验证统计

```python
# 获取验证统计信息
stats = validator.get_validation_stats()

print(f"总文件数: {stats.total_files}")
print(f"有效PDF: {stats.valid_files}")
print(f"无效PDF: {stats.invalid_files}")
print(f"成功率: {stats.success_rate:.1f}%")
```

## 使用示例

### 1. 基本验证

```python
#!/usr/bin/env python3
"""基本 PDF 验证示例"""

from information_composer.pdf.validator import PDFValidator

def basic_validation_example():
    """基本验证示例"""
    # 创建验证器
    validator = PDFValidator(verbose=True)
    
    # 验证单个文件
    sample_pdf = "sample.pdf"
    if os.path.exists(sample_pdf):
        print(f"验证文件: {sample_pdf}")
        is_valid, error_msg = validator.validate_single_pdf(sample_pdf)
        
        if is_valid:
            print("✅ 文件验证通过")
        else:
            print(f"❌ 文件验证失败: {error_msg}")
    else:
        print(f"文件不存在: {sample_pdf}")

if __name__ == "__main__":
    basic_validation_example()
```

### 2. 目录验证

```python
#!/usr/bin/env python3
"""目录 PDF 验证示例"""

from information_composer.pdf.validator import PDFValidator

def directory_validation_example():
    """目录验证示例"""
    # 创建验证器
    validator = PDFValidator(verbose=True)
    
    # 验证目录
    current_dir = "."
    print(f"验证目录: {current_dir}")
    
    # 重置统计
    validator.reset_stats()
    
    # 验证目录中的所有 PDF
    validator.validate_directory(current_dir, recursive=False)
    
    # 显示统计
    stats = validator.get_validation_stats()
    print("\n验证统计:")
    print(f"  总文件数: {stats.total_files}")
    print(f"  有效PDF: {stats.valid_files}")
    print(f"  无效PDF: {stats.invalid_files}")
    print(f"  成功率: {stats.success_rate:.1f}%")

if __name__ == "__main__":
    directory_validation_example()
```

### 3. 批量验证

```python
#!/usr/bin/env python3
"""批量 PDF 验证示例"""

from information_composer.pdf.validator import PDFValidator

def batch_validation_example():
    """批量验证示例"""
    # 创建验证器
    validator = PDFValidator(verbose=True)
    
    # 文件列表
    test_files = ["file1.pdf", "file2.pdf", "file3.pdf"]
    
    print("批量验证文件列表:")
    for file in test_files:
        print(f"  - {file}")
    
    # 重置统计
    validator.reset_stats()
    
    # 验证文件列表
    validator.validate_files(test_files)
    
    # 显示统计
    stats = validator.get_validation_stats()
    print("\n批量验证统计:")
    print(f"  总文件数: {stats.total_files}")
    print(f"  有效PDF: {stats.valid_files}")
    print(f"  无效PDF: {stats.invalid_files}")
    print(f"  成功率: {stats.success_rate:.1f}%")

if __name__ == "__main__":
    batch_validation_example()
```

## CLI 使用

### 基本命令

```bash
# 验证单个文件
pdf-validator file.pdf

# 验证多个文件
pdf-validator file1.pdf file2.pdf file3.pdf

# 验证目录中的所有PDF
pdf-validator -d /path/to/directory

# 递归验证目录
pdf-validator -d /path/to/directory -r
```

### 高级选项

```bash
# 详细输出
pdf-validator -d /path/to/directory -v

# JSON格式输出
pdf-validator -d /path/to/directory --json

# 只显示统计信息
pdf-validator -d /path/to/directory --stats-only

# 保存结果到文件
pdf-validator -d /path/to/directory --output results.json
```

## 验证规则

### PDF 格式检查

1. **文件头验证**：检查 PDF 文件头是否正确
2. **文件结构**：验证 PDF 内部结构完整性
3. **页面信息**：检查是否包含有效页面
4. **元数据**：验证基本元数据存在性

### 错误类型

1. **格式错误**：文件不是有效的 PDF 格式
2. **损坏文件**：文件结构损坏
3. **空文件**：文件大小为 0
4. **无法读取**：文件权限或其他读取错误

## 最佳实践

### 1. 验证策略

```python
def robust_pdf_validation(pdf_files):
    """健壮的 PDF 验证策略"""
    validator = PDFValidator(verbose=False)
    
    results = {
        "valid": [],
        "invalid": [],
        "errors": {}
    }
    
    for pdf_file in pdf_files:
        is_valid, error_msg = validator.validate_single_pdf(pdf_file)
        
        if is_valid:
            results["valid"].append(pdf_file)
        else:
            results["invalid"].append(pdf_file)
            results["errors"][pdf_file] = error_msg
    
    return results
```

### 2. 错误处理

```python
def safe_validation(pdf_file):
    """安全的验证函数"""
    validator = PDFValidator(verbose=False)
    
    try:
        is_valid, error_msg = validator.validate_single_pdf(pdf_file)
        return is_valid, error_msg
    except FileNotFoundError:
        return False, "文件不存在"
    except PermissionError:
        return False, "无权限访问文件"
    except Exception as e:
        return False, f"未知错误: {str(e)}"
```

### 3. 性能优化

```python
# 批量验证时使用多线程
from concurrent.futures import ThreadPoolExecutor

def parallel_validation(pdf_files, max_workers=4):
    """并行验证 PDF 文件"""
    validator = PDFValidator(verbose=False)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            validator.validate_single_pdf, 
            pdf_files
        ))
    
    return results
```

## 常见问题

### Q: 验证失败的常见原因是什么？
A: 常见原因包括：文件损坏、格式错误、加密保护、不完整下载等。

### Q: 如何处理加密的 PDF 文件？
A: 当前版本的验证器会将加密的 PDF 标记为无效。如需验证加密文件，需要先解密。

### Q: 验证大量文件时如何提高性能？
A: 使用批量验证功能、减少详细输出、考虑使用多线程处理。

### Q: 如何自定义验证规则？
A: 可以继承 PDFValidator 类并重写验证方法来实现自定义验证规则。

## 集成示例

### 与 DOI 下载集成

```python
from information_composer.core.doi_downloader import DOIDownloader
from information_composer.pdf.validator import PDFValidator

def download_and_validate(dois, output_dir):
    """下载并验证 PDF 文件"""
    # 下载文件
    downloader = DOIDownloader()
    results = downloader.download_batch(dois, output_dir)
    
    # 验证下载的文件
    validator = PDFValidator()
    pdf_files = [r.file_name for r in results if r.downloaded]
    
    for pdf_file in pdf_files:
        is_valid, error = validator.validate_single_pdf(pdf_file)
        if not is_valid:
            print(f"警告: {pdf_file} 验证失败: {error}")
```

### 自动化工作流

```python
def automated_pdf_workflow(download_dir):
    """自动化 PDF 工作流"""
    validator = PDFValidator(verbose=True)
    
    # 验证目录
    validator.validate_directory(download_dir, recursive=True)
    
    # 获取统计
    stats = validator.get_validation_stats()
    
    # 生成报告
    report = {
        "directory": download_dir,
        "total_files": stats.total_files,
        "valid_files": stats.valid_files,
        "invalid_files": stats.invalid_files,
        "success_rate": stats.success_rate
    }
    
    # 保存报告
    with open("validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report
```

## 相关资源

- [pypdfium2 文档](https://pypdfium2.readthedocs.io/)
- [PDF 规范](https://www.adobe.com/devnet/pdf/pdf_reference.html)
- [information-composer PDF 模块文档](../api/pdf/)
- [PDF 文件格式指南](https://en.wikipedia.org/wiki/PDF)

## 更新日志

- **v1.0.0** - 初始版本，包含基础验证功能
- **v1.1.0** - 添加批量验证和目录扫描
- **v1.2.0** - 增加统计信息和 JSON 输出
- **v1.3.0** - 完善错误处理和 CLI 工具

---

*最后更新：2024年12月*
