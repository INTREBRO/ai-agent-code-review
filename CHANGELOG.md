# 📄 变更日志

本文档记录 **AI Agent 代码审查工作流** 项目的所有 notable changes。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 🎯 计划中

- [ ] 添加对 Vue 3 的审查支持
- [ ] 添加 Go 语言审查规则
- [ ] 完善 GitHub Actions 工作流
- [ ] 添加 Docker Compose 部署配置
- [ ] 添加 MkDocs 文档网站

---

## [1.0.0] - 2026-05-06

### ✨ 新增功能

#### AI 代码审查核心
- ✅ 添加 Python 审查脚本 `.ai-review/ai-agent-review.py`
- ✅ 添加 JavaScript 审查脚本 `.ai-review/ai-agent-review.js`
- ✅ 添加审查规则库 `.ai-review/rules.json`
- ✅ 添加模式匹配库 `.ai-review/patterns.json`

#### 代码质量工具配置
- ✅ 添加 ESLint 配置文件 `.eslintrc.json`
- ✅ 添加 Prettier 配置文件 `.prettierrc`
- ✅ 添加 SonarQube 配置文件 `sonar-project.properties`

#### 安全工具配置
- ✅ 添加 GitLeaks 配置文件 `.gitleaks.toml`（密钥扫描）
- ✅ 添加 Snyk 配置文件 `.snyk`（依赖漏洞扫描）

#### GitHub 社区文件
- ✅ 添加 Bug 报告模板 `.github/ISSUE_TEMPLATE/bug-report.yml`
- ✅ 添加功能请求模板 `.github/ISSUE_TEMPLATE/feature-request.yml`
- ✅ 添加 PR 模板 `.github/PULL_REQUEST_TEMPLATE.md`
- ✅ 添加行为准则 `CODE_OF_CONDUCT.md`
- ✅ 添加贡献指南 `CONTRIBUTING.md`
- ✅ 添加安全漏洞报告流程 `SECURITY.md`
- ✅ 添加变更日志 `CHANGELOG.md`（本文件）

#### 项目配置示例
- ✅ 添加 EditorConfig `.editorconfig`
- ✅ 添加 Jest 配置示例 `jest.config.example.js`
- ✅ 添加 TypeScript 配置示例 `tsconfig.json.example`
- ✅ 添加 AI 审查配置示例 `.ai-review-config.yml`

#### 文档
- ✅ 添加完整设计文档 `ai-agent-code-review-workflow.md`（1.8 万字）
- ✅ 添加实施清单 `IMPLEMENTATION-CHECKLIST.md`
- ✅ 添加项目介绍 `README.md`
- ✅ 添加 MIT 开源协议 `LICENSE`

### 🐛 修复

- 修复 README.md 文档结构描述过时问题
- 修复 Badge 图片链接格式错误

### 📊 统计

- **文件数量**：25 个
- **代码行数**：约 3500 行
- **文档字数**：约 2.5 万字

---

## 版本说明

### 版本号格式

`主版本.次版本.修订号`

- **主版本**：不兼容的 API 修改
- **次版本**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 变更类型

| 图标 | 含义 |
|------|------|
| ✨ `新增` | 新功能 |
| 🐛 `修复` | Bug 修复 |
| 📝 `文档` | 文档更新 |
| ♻️ `重构` | 代码重构 |
| ⚡ `优化` | 性能优化 |
| 🧪 `测试` | 测试相关 |
| 🔧 `配置` | 配置变更 |
| 🗑️ `删除` | 删除代码/文件 |
| 🔒 `安全` | 安全问题修复 |
| ⚠️ `弃用` | 即将移除的功能 |

---

## 📚 历史版本

- **v1.0.0** (2026-05-06) - 首个正式版本 ⭐

---

## 🔗 链接

- [GitHub Releases](https://github.com/INTREBRO/ai-agent-code-review/releases)
- [GitHub Milestones](https://github.com/INTREBRO/ai-agent-code-review/milestones)
- [提交历史](https://github.com/INTREBRO/ai-agent-code-review/commits)

---

**最后更新**：2026-05-06
