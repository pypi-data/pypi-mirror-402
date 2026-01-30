# 示例文档

本目录包含了 information-composer 项目的所有示例代码的详细说明文档。每个示例都经过精心设计，展示了项目的不同功能模块的使用方法。

## 示例分类

### 📚 学术数据获取
- [PubMed 示例](./pubmed-examples.md) - PubMed 数据库查询和数据处理
- [DOI 下载示例](./doi-download-examples.md) - 基于 DOI 的学术论文下载
- [Google Scholar 示例](./google-scholar-examples.md) - Google Scholar 学术搜索

### 🔧 数据处理工具
- [Markdown 处理示例](./markdown-processing-examples.md) - Markdown 文档转换和处理
- [LLM 过滤示例](./llm-filter-examples.md) - 基于大语言模型的智能内容过滤
- [PDF 验证示例](./pdf-validator-examples.md) - PDF 文件格式验证

### 🌾 专业数据源
- [RiceDataCN 示例](./ricedatacn-examples.md) - 水稻基因数据解析

## 快速开始

1. **选择相关示例**：根据您的需求选择相应的示例文档
2. **查看代码**：每个示例都包含完整的源代码和详细注释
3. **运行示例**：按照文档中的说明运行示例代码
4. **自定义修改**：根据您的具体需求修改示例代码

## 示例代码位置

所有示例代码位于项目根目录的 `examples/` 文件夹中：

```
examples/
├── pubmed_query_pmid.py                    # PubMed PMID 查询
├── pubmed_details_example.py               # PubMed 详情获取
├── pubmed_details_batch_example.py         # PubMed 批量详情获取
├── pubmed_keywords_filter_example.py       # PubMed 关键词过滤
├── pubmed_cli_example.py                   # PubMed CLI 工具使用
├── doi_download_single.py                  # 单个 DOI 下载
├── doi_download_example.py                 # DOI 批量下载
├── doi_download_by_using_pubmed_batch_example.py  # 结合 PubMed 的 DOI 下载
├── google_scholar_basic_example.py         # Google Scholar 基础搜索
├── google_scholar_advanced_example.py      # Google Scholar 高级搜索
├── google_scholar_batch_example.py         # Google Scholar 批量处理
├── markdown_converter.py                   # Markdown 转换
├── markdown_filter_ref.py                  # Markdown 引用过滤
├── llm_filter_example.py                   # LLM 智能过滤
├── pdf_validator_example.py                # PDF 验证
└── ricedatacn_gene_example.py              # 水稻基因数据解析
```

## 运行环境

在运行示例之前，请确保：

1. **Python 环境**：Python 3.7+ （推荐 3.10+）
2. **虚拟环境**：激活项目的虚拟环境
   ```bash
   source activate.sh  # Linux/macOS
   # 或
   activate.bat        # Windows
   ```
3. **依赖安装**：安装项目依赖
   ```bash
   pip install -e .
   ```
4. **API 密钥**：某些示例需要配置 API 密钥（如 DashScope）

## 配置说明

### 环境变量

某些示例需要设置环境变量：

```bash
# DashScope API 密钥（用于 LLM 过滤）
export DASHSCOPE_API_KEY="your-api-key"

# PubMed 邮箱（用于 API 合规）
export PUBMED_EMAIL="your-email@example.com"
```

### 配置文件

部分示例支持配置文件：

- `config.json` - 通用配置文件
- `llm_config.yaml` - LLM 相关配置
- `search_config.json` - 搜索相关配置

## 最佳实践

### 1. 代码注释
- 所有示例代码都包含详细的英文注释
- 注释解释了关键步骤、参数选择和注意事项
- 遵循 Google 风格的 docstring 规范

### 2. 错误处理
- 示例包含完整的错误处理机制
- 提供清晰的错误信息和解决建议
- 演示了重试和恢复策略

### 3. 性能优化
- 使用缓存机制减少重复请求
- 实现适当的延迟和速率限制
- 提供批量处理选项

### 4. 数据管理
- 示例包含数据导出功能
- 支持多种输出格式（JSON、CSV、BibTeX）
- 提供数据清理和验证

## 贡献指南

如果您想添加新的示例：

1. **创建示例文件**：在 `examples/` 目录下创建新的 Python 文件
2. **添加详细注释**：使用英文编写详细的代码注释
3. **更新文档**：在相应的示例文档中添加说明
4. **测试验证**：确保示例可以正常运行
5. **提交代码**：通过 Pull Request 提交更改

## 常见问题

### Q: 示例运行时出现网络错误怎么办？
A: 检查网络连接，某些示例需要访问外部 API。如果使用代理，请配置相应的环境变量。

### Q: 如何获取 API 密钥？
A: 参考各个模块的配置文档，通常需要在相应的服务提供商网站注册账号。

### Q: 示例运行很慢怎么办？
A: 这是正常现象，因为需要遵守 API 速率限制。可以调整 `rate_limit` 参数，但不建议设置过低。

### Q: 如何自定义示例？
A: 修改示例代码中的配置参数，如搜索关键词、输出路径、API 密钥等。

## 技术支持

如果您在使用示例时遇到问题：

1. 查看示例文档中的常见问题部分
2. 检查项目的 GitHub Issues
3. 参考各个模块的 API 文档
4. 在项目仓库中提交新的 Issue

## 更新日志

- **v1.0.0** - 初始版本，包含所有基础示例
- **v1.1.0** - 添加了详细的代码注释和文档
- **v1.2.0** - 增加了错误处理和性能优化示例

---

*最后更新：2024年12月*
