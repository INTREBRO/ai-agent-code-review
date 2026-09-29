# AI Agent Code Review

一个用于面试展示的 GitHub PR 自动审查项目：工作流读取 PR 的代码差异，调用 OpenAI 生成审查意见，并将结果写回 PR。可选的仓库上下文检索（RAG）让模型参考默认分支中的相关代码；默认关闭。

> 这是可演示的原型，不是生产级安全扫描器。AI 意见需要人工核对。

## 一次审查如何运行

```text
PR 创建或更新 → GitHub Actions 离线测试 → 读取 PR diff
                                        ↓
                             可选：检索仓库代码片段
                                        ↓
                           OpenAI 审查 → PR 总结评论
                                        └→ review-report.json
```

- [审查工作流](.github/workflows/ai-code-review.yml) 在同仓库 PR 创建或更新时运行，也支持输入 PR 编号手动重跑。
- [Python 审查器](.ai-review/ai-agent-review.py) 最多处理 PR 前 10 个文件中具有文本 patch 的文件；跳过的文件会记录在报告中。
- 审查结果写入 `review-report.json`，并创建或更新同一条 PR 总结评论，避免每次运行都新增评论。
- [RAG 模块](.ai-review/rag/) 从默认分支构建本地 JSON 索引；索引或检索失败时继续使用纯 diff 审查。
- [离线测试](tests/) 不调用 GitHub 或 OpenAI API。

## 在 GitHub 上演示

1. 在仓库的 **Settings → Secrets and variables → Actions** 中添加仓库密钥 `OPENAI_API_KEY`。不要把密钥写入代码、Issue 或 PR。
2. 从本仓库创建分支，按[演示步骤](examples/demo/README.md)修改示例文件并发起 PR。
3. 查看 **AI Code Review** 工作流、PR 评论和 Actions 产物 `review-report.json`。模型输出会变化，请以真实运行结果为准。

可选的 Actions variables：

| 名称 | 默认值 | 用途 |
| --- | --- | --- |
| `RAG_ENABLED` | `false` | 设为 `true` 时检索默认分支的相关代码 |
| `OPENAI_MODEL` | `gpt-4.1-mini` | 指定可用的 Chat Completions 模型 |

来自 fork 的 PR 不会自动运行带密钥的审查 job。维护者可在 Actions 中手动输入 PR 编号；工作流使用默认分支的审查器，通过 GitHub API 读取 PR diff，不执行 PR 分支代码。启用 RAG 时，相关仓库代码片段会发送给 OpenAI Embeddings API。

## 本地运行与验证

使用 Python 3.11。离线测试不需要 API 密钥：

```bash
python -m unittest discover -s tests -v
```

如需在本地审查真实 PR，先安装 `requests>=2.31,<3`，再设置 `OPENAI_API_KEY`、`GITHUB_TOKEN`、`REPO_NAME`（如 `owner/repo`）和 `PR_NUMBER`，运行：

```bash
python .ai-review/ai-agent-review.py
```

## 范围与后续

当前只分析前 10 个 PR 文件中的文本 patch，评论没有行内定位；大文件、二进制文件或缺少 patch 的文件可能被跳过。RAG 默认关闭，且没有经过量化评测。多 Agent 审查、自动修复 PR 和评测基准仍是后续方向，**尚未实现**。

仓库还保留了早期 Node.js 原型和独立的代码质量实验工作流；真实 PR 审查使用上文所述的 Python 流程。原有的[方案文档](ai-agent-code-review-workflow.md)与[实施清单](IMPLEMENTATION-CHECKLIST.md)包含未来设想，不代表现有功能。

参与项目请看[贡献指南](CONTRIBUTING.md)；安全问题请看[安全说明](SECURITY.md)。本项目采用 [MIT 许可证](LICENSE)。
