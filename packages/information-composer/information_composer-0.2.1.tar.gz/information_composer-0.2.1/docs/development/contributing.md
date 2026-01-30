# 贡献指南

感谢您对 Information Composer 项目的关注！我们欢迎各种形式的贡献，包括代码、文档、测试、反馈等。

## 🤝 如何贡献

### 贡献方式

1. **报告问题** - 在 GitHub Issues 中报告 bug 或提出功能请求
2. **提交代码** - 通过 Pull Request 提交代码改进
3. **完善文档** - 改进文档、添加示例或翻译
4. **编写测试** - 添加测试用例提高代码覆盖率
5. **分享反馈** - 提供使用反馈和改进建议

### 开发流程

#### 1. Fork 项目

```bash
# 在 GitHub 上 Fork 项目
# 然后克隆您的 Fork
git clone https://github.com/yourusername/information-composer.git
cd information-composer
```

#### 2. 设置开发环境

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装代码质量工具
pip install ruff pytest pytest-cov black isort mypy
```

#### 3. 创建功能分支

```bash
# 创建新分支
git checkout -b feature/your-feature-name

# 或修复 bug
git checkout -b fix/issue-number
```

#### 4. 开发代码

- 遵循项目的代码规范
- 添加适当的类型注解
- 编写文档字符串
- 添加测试用例

#### 5. 运行测试

```bash
# 运行代码质量检查
python scripts/check_code.py --fix

# 运行测试
python scripts/check_code.py --with-tests

# 或直接运行 pytest
pytest tests/ -v --cov=src/information_composer
```

#### 6. 提交代码

```bash
# 添加修改的文件
git add .

# 提交代码（使用规范的提交信息）
git commit -m "feat: add new feature description"

# 推送到您的 Fork
git push origin feature/your-feature-name
```

#### 7. 创建 Pull Request

- 在 GitHub 上创建 Pull Request
- 填写详细的描述
- 关联相关的 Issue
- 等待代码审查

## 📋 代码规范

### Python 代码风格

- 遵循 PEP 8 标准
- 使用 Ruff 进行代码检查和格式化
- 行长度限制为 88 字符
- 使用 4 个空格缩进
- 使用双引号

### 类型注解

```python
def process_data(
    input_data: List[Dict[str, Any]], 
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    处理数据的函数。

    Args:
        input_data: 输入数据列表
        options: 可选的配置选项

    Returns:
        处理结果字典

    Raises:
        ValueError: 当输入数据无效时
    """
    pass
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def example_function(param1: str, param2: int = 10) -> bool:
    """
    示例函数的简短描述。

    更详细的描述可以在这里添加，解释函数的作用、
    使用方法和注意事项。

    Args:
        param1: 第一个参数的描述
        param2: 第二个参数的描述，默认为10

    Returns:
        返回值的描述

    Raises:
        ValueError: 参数无效时抛出的异常
        RuntimeError: 运行时错误

    Example:
        >>> result = example_function("test", 20)
        >>> print(result)
        True
    """
    pass
```

### 测试规范

#### 测试文件命名

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头

#### 测试示例

```python
import pytest
from information_composer.pdf.validator import PDFValidator

class TestPDFValidator:
    """PDF验证器测试类。"""

    def setup_method(self):
        """测试前准备。"""
        self.validator = PDFValidator(verbose=False)

    def test_validate_single_pdf_success(self):
        """测试成功验证PDF文件。"""
        # 准备测试数据
        test_file = "tests/data/valid.pdf"
        
        # 执行测试
        result = self.validator.validate_single_pdf(test_file)
        
        # 验证结果
        assert result.is_valid is True
        assert result.error_message is None

    @pytest.mark.parametrize("file_path,expected", [
        ("valid.pdf", True),
        ("invalid.pdf", False),
    ])
    def test_validate_multiple_files(self, file_path, expected):
        """测试验证多个文件。"""
        result = self.validator.validate_single_pdf(file_path)
        assert result.is_valid == expected
```

## 🚀 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 格式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
feat: add PDF validation CLI tool
fix: resolve memory leak in batch processing
docs: update installation guide
test: add unit tests for DOI downloader
```

## 🔍 代码审查

### 审查要点

1. **功能正确性** - 代码是否实现了预期功能
2. **代码质量** - 是否遵循项目规范
3. **测试覆盖** - 是否有足够的测试
4. **文档完整** - 是否有适当的文档
5. **性能考虑** - 是否有性能问题
6. **安全性** - 是否有安全漏洞

### 审查流程

1. 自动检查通过（CI/CD）
2. 至少一位维护者审查
3. 所有讨论的问题得到解决
4. 代码合并到主分支

## 🐛 报告问题

### Bug 报告

在创建 Issue 时，请包含：

1. **问题描述** - 清晰描述遇到的问题
2. **重现步骤** - 详细的重现步骤
3. **预期行为** - 期望的正确行为
4. **实际行为** - 实际发生的行为
5. **环境信息** - Python 版本、操作系统等
6. **错误日志** - 相关的错误信息

### 功能请求

1. **功能描述** - 详细描述想要的功能
2. **使用场景** - 说明为什么需要这个功能
3. **实现建议** - 如果有的话，提供实现建议
4. **替代方案** - 说明是否考虑过其他方案

## 📚 文档贡献

### 文档类型

1. **API 文档** - 自动生成，但可以改进示例
2. **用户指南** - 使用说明和教程
3. **开发文档** - 开发环境设置和架构说明
4. **示例代码** - 实际可运行的示例

### 文档规范

- 使用 Markdown 格式
- 包含目录结构
- 提供代码示例
- 使用中文或英文，保持一致性
- 定期更新过时信息

## 🎯 开发优先级

### 高优先级

1. Bug 修复
2. 性能优化
3. 安全性改进
4. 测试覆盖率提升

### 中优先级

1. 新功能开发
2. 文档完善
3. 代码重构
4. 工具链改进

### 低优先级

1. 代码风格调整
2. 注释完善
3. 示例代码添加

## 🤔 常见问题

### Q: 如何开始贡献？

A: 建议从以下方式开始：
1. 查看 [Issues](https://github.com/yourusername/information-composer/issues) 中的 "good first issue" 标签
2. 阅读现有代码，了解项目结构
3. 运行测试，确保环境正常
4. 从小的改进开始，如修复文档错误

### Q: 代码审查需要多长时间？

A: 通常在 1-3 个工作日内完成，复杂的功能可能需要更长时间。

### Q: 如何联系维护者？

A: 可以通过以下方式：
1. GitHub Issues 和 Pull Requests
2. 项目讨论区
3. 邮件联系（如果提供）

### Q: 贡献代码有奖励吗？

A: 虽然没有物质奖励，但您的贡献会被记录在项目历史中，有助于个人技术成长和社区声誉。

## 📄 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

## 🙏 致谢

感谢所有为 Information Composer 项目做出贡献的开发者！

---

**开始贡献吧！** 我们期待您的参与，一起让 Information Composer 变得更好！
