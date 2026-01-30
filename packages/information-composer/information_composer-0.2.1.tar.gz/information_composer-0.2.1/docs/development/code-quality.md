# 代码质量指南

本指南介绍 Information Composer 项目的代码质量标准和检查工具。

## 🎯 代码质量标准

### 代码风格
- 遵循 PEP 8 标准
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 Ruff 进行代码质量检查

### 类型注解
- 所有公共函数必须有类型注解
- 使用 `typing` 模块的类型提示
- 复杂类型使用 `TypedDict` 或 `dataclass`

### 文档字符串
- 所有公共函数必须有文档字符串
- 使用 Google 风格的文档字符串
- 包含参数、返回值和异常说明

## 🛠️ 代码质量工具

### Ruff 配置

项目使用 Ruff 作为主要的代码质量工具：

```toml
# pyproject.toml
[tool.ruff]
target-version = "py37"
line-length = 88

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "SIM", # flake8-simplify
    "Q",   # flake8-quotes
    "RUF", # Ruff-specific rules
]
```

### 运行代码检查

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

### 直接使用 Ruff

```bash
# 格式化代码
ruff format src/ examples/ scripts/

# 检查代码质量
ruff check src/ examples/ scripts/

# 自动修复问题
ruff check src/ examples/ scripts/ --fix

# 只检查导入排序
ruff check src/ examples/ scripts/ --select I
```

## 📋 检查项目

### 1. 代码格式化
- 行长度限制（88 字符）
- 缩进一致性（4 空格）
- 空行规范
- 引号使用（双引号）

### 2. 代码质量
- 未使用的导入
- 未使用的变量
- 死代码检测
- 复杂度检查
- 命名规范

### 3. 导入排序
- 标准库导入
- 第三方库导入
- 本地模块导入
- 导入分组和排序

### 4. 类型检查
- 类型注解完整性
- 类型兼容性
- 可选类型使用

## 🔧 配置说明

### 忽略规则

某些规则被忽略或配置为警告：

```toml
[tool.ruff.lint]
ignore = [
    "E501",  # 行长度，由 Black 处理
    "W293",  # 空白行包含空格
    "RUF001", # Unicode 字符（中文注释）
    "ARG001", # 未使用的函数参数
    # ... 更多忽略规则
]
```

### 文件特定忽略

```toml
[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401", "TID252"]
"tests/**/*" = ["ARG", "S101", "TID252", "B904"]
"examples/**/*" = ["TID252", "E402", "F401"]
"src/information_composer/markdown/vendor/**/*" = ["ALL"]
```

## 📝 代码规范

### 函数定义

```python
def process_document(
    file_path: str,
    output_dir: str = "output",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    处理文档文件。

    Args:
        file_path: 输入文件路径
        output_dir: 输出目录路径
        verbose: 是否显示详细输出

    Returns:
        处理结果字典

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式不支持
    """
    # 实现代码
    pass
```

### 类定义

```python
class DocumentProcessor:
    """文档处理器类。"""

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化文档处理器。

        Args:
            config: 配置字典
        """
        self.config = config
        self._setup_processor()

    def _setup_processor(self) -> None:
        """设置处理器。"""
        # 私有方法实现
        pass
```

### 类型注解

```python
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

def process_files(
    file_paths: List[Union[str, Path]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """处理文件列表。"""
    if options is None:
        options = {}
    
    results = {}
    for file_path in file_paths:
        # 处理逻辑
        pass
    
    return results
```

## 🧪 测试规范

### 测试文件结构

```
tests/
├── __init__.py
├── test_core/
│   ├── __init__.py
│   ├── test_doi_downloader.py
│   └── test_downloader.py
├── test_pdf/
│   ├── __init__.py
│   └── test_validator.py
├── test_markdown/
│   ├── __init__.py
│   └── test_processor.py
└── test_integration/
    ├── __init__.py
    └── test_end_to_end.py
```

### 测试函数命名

```python
def test_validate_single_pdf_success():
    """测试成功验证单个PDF文件。"""
    pass

def test_validate_single_pdf_file_not_found():
    """测试文件不存在的情况。"""
    pass

def test_validate_directory_with_recursive():
    """测试递归验证目录。"""
    pass
```

### 测试用例示例

```python
import pytest
from pathlib import Path
from information_composer.pdf.validator import PDFValidator

class TestPDFValidator:
    """PDF验证器测试类。"""

    def setup_method(self):
        """测试前准备。"""
        self.validator = PDFValidator(verbose=False)
        self.test_dir = Path("tests/data")

    def test_validate_single_pdf_success(self):
        """测试成功验证PDF文件。"""
        # 准备测试数据
        test_file = self.test_dir / "valid.pdf"
        
        # 执行测试
        is_valid, error = self.validator.validate_single_pdf(str(test_file))
        
        # 验证结果
        assert is_valid is True
        assert error is None

    def test_validate_single_pdf_file_not_found(self):
        """测试文件不存在的情况。"""
        # 执行测试
        is_valid, error = self.validator.validate_single_pdf("nonexistent.pdf")
        
        # 验证结果
        assert is_valid is False
        assert "文件不存在" in error

    @pytest.mark.parametrize("file_path,expected", [
        ("valid.pdf", True),
        ("invalid.pdf", False),
        ("empty.pdf", False),
    ])
    def test_validate_multiple_files(self, file_path, expected):
        """测试验证多个文件。"""
        # 执行测试
        is_valid, error = self.validator.validate_single_pdf(file_path)
        
        # 验证结果
        assert is_valid == expected
```

## 🔄 CI/CD 集成

### GitHub Actions 配置

代码质量检查已集成到 GitHub Actions：

```yaml
# .github/workflows/code-quality.yaml
name: Code Quality

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  ruff-check:
    name: Ruff Code Quality Check
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]  # Tests against minimum (3.12) and latest (3.13) Python versions

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install ruff
    - name: Run Ruff formatting check
      run: ruff format --check src/ examples/ scripts/
    - name: Run Ruff code quality check
      run: ruff check src/ examples/ scripts/ --statistics
    - name: Run Ruff import sorting check
      run: ruff check src/ examples/ scripts/ --select I
```

### 本地开发流程

1. **开发前检查**
```bash
# 确保环境正确
source activate.sh
python --version
pip list | grep information-composer
```

2. **开发过程中**
```bash
# 定期运行检查
python scripts/check_code.py --fix
```

3. **提交前检查**
```bash
# 运行完整检查
python scripts/check_code.py --with-tests
```

4. **提交代码**
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature-branch
```

## 🚨 常见问题

### 1. 代码格式化问题

```bash
# 自动修复格式问题
ruff format src/ examples/ scripts/

# 或使用 Black
black src/ examples/ scripts/
```

### 2. 导入排序问题

```bash
# 自动修复导入排序
ruff check src/ examples/ scripts/ --select I --fix

# 或使用 isort
isort src/ examples/ scripts/
```

### 3. 类型注解问题

```python
# 添加类型注解
from typing import List, Dict, Optional

def process_data(data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """处理数据。"""
    pass
```

### 4. 文档字符串问题

```python
def example_function(param1: str, param2: int = 10) -> bool:
    """
    示例函数。

    Args:
        param1: 第一个参数
        param2: 第二个参数，默认为10

    Returns:
        处理结果

    Raises:
        ValueError: 参数无效时抛出
    """
    pass
```

## 📚 相关文档

- [安装指南](../installation.md) - 开发环境设置
- [快速开始](../quickstart.md) - 快速上手
- [贡献指南](contributing.md) - 如何贡献代码
- [测试指南](contributing.md#测试规范) - 测试和调试

---

**保持代码质量** 是项目成功的关键！遵循这些标准，让代码更清晰、更可维护。
