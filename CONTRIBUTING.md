# 贡献指南

感谢关注 AI Agent Code Review。本仓库目前为私有的面试展示项目；只有获得访问权限的协作者才能查看代码、提交 Issue 或创建 PR。参与讨论时请遵守[行为准则](CODE_OF_CONDUCT.md)。

## 提问题或建议

- 普通 Bug：先搜索现有 Issue，再使用 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug-report.yml)。写明复现步骤、预期与实际结果，以及必要的环境信息。
- 功能建议：使用 [功能建议模板](.github/ISSUE_TEMPLATE/feature-request.yml)，说明使用场景和预期效果。
- 安全漏洞：请先阅读[安全说明](SECURITY.md)，不要把漏洞细节、令牌或个人信息放进 Issue。

## 提交代码

1. 从默认分支 `main` 创建工作分支，聚焦一个问题。
2. 修改代码时补充或更新对应测试；修改行为时同步更新 README 或演示说明。
3. 在提交 PR 前运行离线测试：

   ```bash
   python -m unittest discover -s tests -v
   ```

4. 在 PR 中写清变更目的、验证方式和限制，并使用仓库现有的 [PR 模板](.github/PULL_REQUEST_TEMPLATE.md)。

项目主要审查流程使用 Python 3.11；GitHub Actions 会安装 `requests>=2.31,<3`。本地运行真实审查还需要 `OPENAI_API_KEY`、`GITHUB_TOKEN`、`REPO_NAME` 和 `PR_NUMBER`，详见 [README](README.md)。离线测试不需要这些密钥。

## 审查约定

请针对具体代码和证据讨论，友好回应反馈。AI 生成的评论只是辅助信息，不能代替人工判断。不要在提交、日志、测试夹具、Issue 或 PR 中加入真实密钥或敏感数据。

仓库保留了早期 Node.js 原型和独立的代码质量实验工作流；除非 PR 明确针对这些原型，否则以 [Python PR 审查工作流](.github/workflows/ai-code-review.yml)为准。本指南不要求运行不存在的 `requirements.txt` 或额外的 JavaScript 检查。
