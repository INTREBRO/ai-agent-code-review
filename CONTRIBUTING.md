# 🤝 贡献指南

感谢您考虑为 **AI Agent 代码审查工作流** 项目做出贡献！

本指南将帮助您了解如何参与项目开发。

---

## 📋 目录

1. [行为准则](#️-行为准则)
2. [如何贡献](#-如何贡献)
3. [开发流程](#-开发流程)
4. [代码规范](#-代码规范)
5. [提交规范](#-提交规范)
6. [审查流程](#-审查流程)

---

## ️ 行为准则

参与本项目即表示您同意遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。

**请阅读并遵守它** —— 我们重视开放、友好、包容的社区环境。

---

## 🎯 如何贡献

### 1️⃣ 报告 Bug

**在提交 Bug 报告之前**：
- 搜索 [现有 Issue](https://github.com/INTREBRO/ai-agent-code-review/issues)，确认没有重复
- 如果您发现了新 Bug，请使用 [Bug 报告模板](https://github.com/INTREBRO/ai-agent-code-review/issues/new?template=bug-report.yml) 创建 Issue

**Bug 报告应包含**：
- 清晰的问题描述
- 复现步骤
- 预期行为 vs 实际行为
- 环境信息（OS、Python/Node 版本等）
- 相关日志或截图

---

### 2️⃣ 建议新功能

如果您有新功能建议：
- 使用 [功能请求模板](https://github.com/INTREBRO/ai-agent-code-review/issues/new?template=feature-request.yml) 创建 Issue
- 详细描述使用场景和预期效果
- 如有，提供示例代码或设计草图

---

### 3️⃣ 提交代码

#### 步骤 1：Fork 仓库

点击 GitHub 页面右上角的 **Fork** 按钮，将仓库 fork 到您的账号。

#### 步骤 2：克隆您的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/ai-agent-code-review.git
cd ai-agent-code-review
```

#### 步骤 3：添加上游仓库

```bash
git remote add upstream https://github.com/INTREBRO/ai-agent-code-review.git
```

#### 步骤 4：创建功能分支

```bash
git checkout -b feature/your-feature-name
```

**分支命名规范**：
- 新功能：`feature/功能名称`
- Bug 修复：`fix/bug-description`
- 文档更新：`docs/description`
- 性能优化：`perf/description`

#### 步骤 5：开发和提交

```bash
# 进行您的修改...

# 添加文件到暂存区
git add .

# 提交（遵循 Conventional Commits 规范）
git commit -m "feat: 添加对 Vue 3 的支持"
```

#### 步骤 6：推送到您的 Fork

```bash
git push origin feature/your-feature-name
```

#### 步骤 7：提交 Pull Request

- 访问您的 Fork 页面
- 点击 **Compare & pull request**
- 填写 PR 模板
- 等待审查

---

## 🛠️ 开发流程

### 本地开发环境

#### Python 环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖（如果有 requirements.txt）
pip install -r requirements.txt
```

#### Node.js 环境（如果使用 JavaScript 审查脚本）

```bash
# 安装依赖
npm install

# 运行测试（如果有）
npm test
```

---

### 测试指南

**Python 代码**：

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_rules.py

# 检查测试覆盖率
pytest --cov=.ai-review
```

**JavaScript 代码**：

```bash
# 运行测试
npm test

# 检查代码规范
npm run lint
```

---

## 📏 代码规范

### Python 代码

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 `pylint` 或 `flake8` 进行静态检查
- 使用 `black` 进行代码格式化
- 使用 `isort` 排序 import 语句

**检查命令**：

```bash
pylint .ai-review/ai-agent-review.py
flake8 .ai-review/ai-agent-review.py
black .ai-review/ai-agent-review.py
```

---

### JavaScript 代码

- 遵循 [ESLint](.eslintrc.json) 配置
- 使用 [Prettier](.prettierrc) 格式化代码
- 使用 camelCase 命名变量和函数
- 使用 PascalCase 命名类名

**检查和格式化命令**：

```bash
# 检查代码规范
npx eslint .ai-review/ai-agent-review.js

# 格式化代码
npx prettier --write .ai-review/ai-agent-review.js
```

---

### 文档规范

- 使用 Markdown 格式
- 代码块指定语言（```python、```javascript）
- 保持语言一致（中文或英文，建议中文）
- 添加必要的截图或示例

---

## 📝 提交规范

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型（Type）

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具链相关 |

### 示例

```bash
# 新功能
git commit -m "feat: 添加对 Go 语言的审查规则"

# Bug 修复
git commit -m "fix: 修复规则匹配时的正则错误"

# 文档更新
git commit -m "docs: 更新 README.md 安装说明"

# 重构
git commit -m "refactor: 重构 AI 审查引擎核心逻辑"

# 性能优化
git commit -m "perf: 优化 AST 解析性能，提升 30%"
```

---

## 🔍 审查流程

### PR 审查标准

Reviewer 将检查：

1. **功能正确性**：代码是否实现了预期功能？
2. **代码质量**：是否遵循项目规范？
3. **测试覆盖**：是否添加了必要的测试？
4. **文档更新**：是否更新了相关文档？
5. **性能影响**：是否引入性能问题？
6. **安全风险**：是否存在安全漏洞？

---

### 审查响应

- 请在 3 个工作日内响应审查意见
- 如有异议，请在 PR 中友好讨论
- 修改后再次请求审查

---

## 📧 联系方式

如果您有任何问题，请通过以下方式联系我们：

- **Issue Tracker**: [https://github.com/INTREBRO/ai-agent-code-review/issues](https://github.com/INTREBRO/ai-agent-code-review/issues)
- **Discussions**: [https://github.com/INTREBRO/ai-agent-code-review/discussions](https://github.com/INTREBRO/ai-agent-code-review/discussions)

---

## 🎉 致谢

感谢所有为本项目做出贡献的开发者！❤️

您的贡献让这个项目变得更好。

---

**最后更新**：2026-05-06
