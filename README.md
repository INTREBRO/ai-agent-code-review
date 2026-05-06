# AI Agent 代码审查工作流

[![GitHub](https://img.shields.io/badge/GitHub-INTREBRO-green.svg)](https://github.com/INTREBRO/ai-agent-code-review)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/INTREBRO/ai-agent-code-review.svg?style=social)](https://github.com/INTREBRO/ai-agent-code-review/stargazers)

> **AI Agent 自动化代码审查解决方案** - 为 15 人团队、每日 20+ PR 的高强度开发环境设计的智能代码审查系统。

---

## 📋 项目简介

本项目提供了一套完整的 **AI Agent 自动化代码审查工作流**设计方案，包括：

- ✅ **代码规范检查规则集**（命名、格式、复杂度、安全漏洞）
- ✅ **自动化审查流水线**（4 阶段，< 11 分钟完成审查）
- ✅ **常见问题模式库**（性能反模式、安全风险、可维护性问题）
- ✅ **优先级分类与自动标注**（P0-P3 四级分类）
- ✅ **Agent 自学习机制**（基于反馈持续优化）
- ✅ **CI/CD 集成方案**（GitHub Actions、Jenkins、GitLab CI）
- ✅ **审查效果度量指标与仪表盘**（效率、质量、满意度指标）

---

## 🎯 适用场景

| 团队规模 | 每日 PR 量 | 主要收益 |
|---------|------------|----------|
| 10-20 人 | 15-30 PR | 审查效率提升 60%，严重 Bug 漏检率 < 5% |
| 20-50 人 | 30-100 PR | 自动化覆盖率 95%，人工审查聚焦架构设计 |
| >50 人 | >100 PR | 统一审查标准，知识沉淀与复用 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent 审查系统                         │
├─────────────────────────────────────────────────────────────┤
│  ① 触发层 → ② 分析层 → ③ 决策层 → ④ 反馈层 → ⑤ 学习层   │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

| 层级 | 组件 | 功能 |
|------|------|------|
| **触发层** | Webhook 监听器 | 监听 PR 事件，触发审查流程 |
| **分析层** | 多引擎分析器 | AST 解析、模式匹配、复杂度计算 |
| **决策层** | AI 评审引擎 | 综合评分、优先级判定、意见生成 |
| **反馈层** | 报告生成器 | PR 评论、仪表盘更新、通知推送 |
| **学习层** | 反馈收集器 | 收集人工反馈，优化检测规则 |

---

## 📂 文档结构

```
.
├── README.md                          # 本文件
├── ai-agent-code-review-workflow.md  # 完整设计文档
├── LICENSE                           # 开源协议
└── examples/                         # 示例代码（待补充）
    ├── .ai-review-config.yml          # 配置文件示例
    ├── github-actions-example.yml    # GitHub Actions 示例
    └── pattern-library.json          # 模式库示例
```

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
# 安装 GitHub CLI
# Windows: https://github.com/cli/cli/releases/latest
# macOS: brew install gh
# Ubuntu: sudo apt install gh

# 安装 Git
# https://git-scm.com/downloads
```

### 2️⃣ 配置 AI Agent 审查系统

```bash
# 1. 克隆本仓库
git clone https://github.com/INTREBRO/ai-agent-code-review.git
cd ai-agent-code-review

# 2. 阅读完整设计文档
cat ai-agent-code-review-workflow.md

# 3. 根据您的团队情况调整配置
# 编辑 .ai-review-config.yml（待补充）
```

### 3️⃣ 集成到您的项目

参考设计文档中的 [CI/CD 集成方案](#7-cicd-集成方案) 章节，选择适合您的 CI/CD 系统：

- **GitHub Actions**: 参见 `examples/github-actions-example.yml`
- **Jenkins**: 参见设计文档 7.2 节
- **GitLab CI**: 参见设计文档 7.3 节

---

## 📊 核心功能详解

### 1. 代码规范检查规则集

#### 命名规范示例

```javascript
// ❌ 不符合规范
const UserName = "Alice";  // 应使用 camelCase
const data = fetchData();  // 无意义命名
function process() { ... }  // 动词缺失

// ✅ 符合规范
const userName = "Alice";
const userData = fetchUserData();
function processOrderData() { ... }
```

#### 复杂度检查

| 复杂度范围 | 评级 | 处理方式 |
|------------|------|----------|
| 1-5 | ✅ 简单 | 通过 |
| 6-10 | ⚠️ 中等 | 警告，建议重构 |
| 11-15 | 🔴 复杂 | 错误，必须重构 |
| >15 | ⛔ 极复杂 | 阻止合并，强制重构 |

### 2. 自动化审查流水线

```
阶段 1：快速检查（< 2 分钟）
  ├─ 代码格式检查
  ├─ 命名规范检查
  └─ 快速安全扫描

阶段 2：深度分析（< 5 分钟）
  ├─ 复杂度分析
  ├─ 重复代码检测
  ├─ 依赖漏洞扫描
  └─ AST 模式匹配

阶段 3：AI 审查（< 3 分钟）
  ├─ 代码逻辑审查
  ├─ 设计模式检查
  ├─ 性能反模式检测
  └─ 生成审查意见

阶段 4：结果汇总（< 1 分钟）
  ├─ 聚合所有检查结果
  ├─ 去重与优先级排序
  ├─ 生成审查报告
  └─ 发布 PR 评论
```

### 3. 常见问题模式库

#### 性能反模式示例

```javascript
// ❌ N+1 查询问题
async function getUsersWithPosts() {
  const users = await User.find();
  for (const user of users) {
    user.posts = await Post.find({ userId: user.id });  // N 次查询
  }
}

// ✅ 优化后：使用 IN 查询
async function getUsersWithPosts() {
  const users = await User.find();
  const userIds = users.map(u => u.id);
  const posts = await Post.find({ userId: { $in: userIds } });  // 1 次查询
  return users.map(user => ({
    ...user,
    posts: posts.filter(p => p.userId === user.id)
  }));
}
```

---

## 📈 预期效果

| 指标 | 当前值 | 目标值 | 改善幅度 |
|------|--------|--------|----------|
| 代码审查效率 | 人工审查 30 分钟/PR | AI 审查 10 分钟/PR | **+66%** |
| 严重 Bug 漏检率 | 15% | < 5% | **-67%** |
| 代码规范遵守率 | 70% | > 95% | **+36%** |
| 开发者满意度 | 60 分 | > 80 分 | **+33%** |

---

## 🛠️ 技术栈

| 组件 | 推荐方案 | 备选方案 |
|------|----------|----------|
| **代码解析** | Tree-sitter | ANTLR, Babel Parser |
| **静态分析** | SonarQube + ESLint | PMD, SpotBugs |
| **AI 模型** | CodeBuddy | GitHub Copilot, CodeGeeX |
| **规则引擎** | 自研规则 DSL | Drools |
| **数据存储** | PostgreSQL + Redis | MySQL + Memcached |
| **消息队列** | RabbitMQ | Kafka, Redis Streams |

---

## 📚 文档目录

1. [系统架构概览](#1-系统架构概览)
2. [代码规范检查规则集](#2-代码规范检查规则集)
3. [自动化审查流水线设计](#3-自动化审查流水线设计)
4. [常见问题模式库](#4-常见问题模式库)
5. [审查意见优先级分类与自动标注](#5-审查意见优先级分类与自动标注)
6. [Agent 自学习机制](#6-agent-自学习机制)
7. [CI/CD 集成方案](#7-cicd-集成方案)
8. [审查效果度量指标与仪表盘设计](#8-审查效果度量指标与仪表盘设计)
9. [实施路线图](#9-实施路线图)

> 📖 **完整文档**：请参阅 [ai-agent-code-review-workflow.md](ai-agent-code-review-workflow.md)

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 贡献方式

1. **提交 Issue**：报告 Bug、提出新功能建议
2. **提交 Pull Request**：修复 Bug、添加新的检测规则
3. **完善文档**：修正错误、补充示例
4. **分享案例**：分享您在团队中实施 AI 代码审查的经验

### 开发流程

```bash
# 1. Fork 本仓库
# 2. 创建功能分支
git checkout -b feature/your-feature-name

# 3. 提交更改
git commit -m "Add: your feature description"

# 4. 推送到您的 Fork
git push origin feature/your-feature-name

# 5. 提交 Pull Request
```

---

## 📄 开源协议

本项目采用 **MIT 协议** - 详见 [LICENSE](LICENSE) 文件。

---

## 📧 联系方式

- **Issue Tracker**: [https://github.com/INTREBRO/ai-agent-code-review/issues](https://github.com/INTREBRO/ai-agent-code-review/issues)
- **Discussions**: [https://github.com/INTREBRO/ai-agent-code-review/discussions](https://github.com/INTREBRO/ai-agent-code-review/discussions)

---

## ⭐ Star History

如果这个项目对您有帮助，请给我们一个 Star！

[![Star History Chart](https://api.star-history.com/svg?repos=INTREBRO/ai-agent-code-review&type=Date)](https://star-history.com/#INTREBRO/ai-agent-code-review&Date)

---

## 🎉 致谢

感谢所有为本项目做出贡献的开发者！

---

**最后更新时间**：2026-05-06
