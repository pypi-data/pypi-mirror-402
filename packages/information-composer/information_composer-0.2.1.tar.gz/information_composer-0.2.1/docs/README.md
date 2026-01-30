# Information Composer 文档

欢迎使用 Information Composer！这是一个综合性的信息收集、处理和过滤工具包。

## 📚 文档导航

### 快速开始
- [安装指南](installation.md) - 如何安装和配置项目
- [快速开始](quickstart.md) - 5分钟快速上手
- [配置说明](configuration.md) - 详细配置选项

### 功能指南
- [PDF 验证器](guides/pdf-validator.md) - PDF 文件格式验证
- [Markdown 处理器](guides/markdown-processor.md) - Markdown 文档处理
- [PubMed 集成](guides/pubmed-integration.md) - 学术文献查询和处理
- [DOI 管理器](guides/doi-manager.md) - DOI 引用管理
- [LLM 过滤器](guides/llm-filter.md) - AI 驱动的文档过滤

### API 参考
- [核心 API](api/core.md) - 核心功能 API
- [PDF API](api/pdf.md) - PDF 处理 API
- [Markdown API](api/markdown.md) - Markdown 处理 API
- [PubMed API](api/pubmed.md) - PubMed 查询 API
- [LLM Filter API](api/llm-filter.md) - LLM 过滤 API

### 示例和教程
- [基础示例](examples/basic-usage.md) - 基础使用示例
- [高级示例](examples/advanced-usage.md) - 高级功能示例
- [集成示例](examples/integration-examples.md) - 与其他工具集成

### 开发指南
- [开发环境设置](development/setup.md) - 开发环境配置
- [代码质量检查](development/code-quality.md) - 代码质量工具
- [测试指南](development/testing.md) - 测试和调试
- [贡献指南](development/contributing.md) - 如何贡献代码

### 部署和运维
- [部署指南](deployment/deployment.md) - 生产环境部署
- [CI/CD 配置](deployment/ci-cd.md) - 持续集成配置
- [监控和日志](deployment/monitoring.md) - 系统监控

## 🚀 主要特性

- **PDF 验证**: 验证 PDF 文件格式和完整性
- **Markdown 处理**: 高级 Markdown 文档处理
- **PubMed 集成**: 学术文献查询和处理
- **DOI 管理**: DOI 引用下载和管理
- **LLM 过滤**: AI 驱动的智能文档过滤
- **代码质量**: 自动化代码质量检查
- **多格式支持**: 支持多种数据格式和来源

## 📖 快速开始

```bash
# 安装项目
pip install -e .

# 激活环境
source activate.sh  # Linux/macOS
activate.bat        # Windows

# 验证 PDF 文件
pdf-validator file.pdf

# 过滤 Markdown 文档
md-llm-filter input.md output.md

# 运行代码质量检查
python scripts/check_code.py --fix
```

## 🤝 贡献

我们欢迎各种形式的贡献！请查看 [贡献指南](development/contributing.md) 了解如何参与项目开发。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有任何疑问，请：

1. 查看相关文档
2. 搜索现有的 [Issues](https://github.com/yourusername/information-composer/issues)
3. 创建新的 Issue 描述您的问题

---

**Information Composer** - 让信息处理更简单、更智能！
