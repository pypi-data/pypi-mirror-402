# 更新日志

本文档记录了 Information Composer 项目的所有重要变更。

## [未发布]

### 新增功能
- 待定

### 修复
- 待定

### 改进
- 待定

## [0.1.3] - 2024-01-15

### 新增功能
- 添加 MCP (Model Context Protocol) 服务器支持
- 新增 RiceDataCN 基因数据解析器
- 实现 Google Scholar 高级搜索功能
- 添加批量 DOI 下载功能
- 支持 PDF 文件递归验证

### 修复
- 修复 PDF 验证器中的内存泄漏问题
- 解决 PubMed 查询中的编码问题
- 修复 Markdown 处理器中的表格解析错误
- 解决 LLM 过滤器中的并发问题

### 改进
- 优化 PDF 验证性能，提升 40% 处理速度
- 改进错误处理和日志记录
- 增强类型注解覆盖度至 95%
- 更新依赖库到最新稳定版本

### 文档
- 完善 API 文档
- 添加更多使用示例
- 更新安装和配置指南

## [0.1.2] - 2024-01-01

### 新增功能
- 实现 LLM 过滤器模块
- 添加 DashScope API 集成
- 支持 Markdown 文档智能过滤
- 新增批量处理功能

### 修复
- 修复 DOI 下载器中的超时问题
- 解决 PubMed 查询中的分页问题
- 修复 PDF 验证器中的文件路径处理

### 改进
- 重构代码结构，提高可维护性
- 添加全面的单元测试
- 改进错误消息的可读性

## [0.1.1] - 2023-12-15

### 新增功能
- 添加 PubMed 数据库集成
- 实现 DOI 下载功能
- 支持 PDF 文件验证
- 添加 Markdown 处理工具

### 修复
- 修复初始版本中的关键 bug
- 解决依赖库兼容性问题

### 改进
- 优化代码性能
- 改进用户界面

## [0.1.0] - 2023-12-01

### 新增功能
- 项目初始版本发布
- 基础 PDF 验证功能
- 简单的 Markdown 处理
- 基本的命令行界面

---

## 版本说明

### 版本号格式

我们使用 [语义化版本控制](https://semver.org/lang/zh-CN/)：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 变更类型

- **新增功能**：新功能、新模块、新 API
- **修复**：Bug 修复、问题解决
- **改进**：性能优化、代码重构、用户体验改进
- **文档**：文档更新、示例添加
- **依赖**：依赖库更新、版本升级
- **废弃**：标记即将移除的功能
- **移除**：移除已废弃的功能

### 发布周期

- **主版本**：重大更新，可能包含破坏性变更
- **次版本**：功能更新，向下兼容
- **修订版本**：Bug 修复，向下兼容

### 支持策略

- **当前版本**：完全支持，包括新功能和 bug 修复
- **前一个主版本**：仅提供 bug 修复
- **更早版本**：不提供支持

## 贡献更新日志

如果您想为更新日志做出贡献，请遵循以下格式：

```markdown
## [版本号] - YYYY-MM-DD

### 新增功能
- 描述新功能

### 修复
- 描述修复的问题

### 改进
- 描述改进内容

### 文档
- 描述文档更新
```

### 提交信息

使用以下格式的提交信息：

```bash
changelog: add entry for v0.1.4
changelog: update changelog for bug fixes
```

## 相关链接

- [GitHub Releases](https://github.com/yourusername/information-composer/releases)
- [项目主页](https://github.com/yourusername/information-composer)
- [文档](https://information-composer.readthedocs.io/)
- [问题追踪](https://github.com/yourusername/information-composer/issues)

---

**注意**：此更新日志遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式。
