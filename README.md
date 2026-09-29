# AI Agent Code Review

GitHub PR 自动审查项目：工作流读取 PR 的代码差异，调用 OpenAI 或 DeepSeek 生成审查意见，并将结果写回 PR。可选的仓库上下文检索（RAG）让模型参考默认分支中的相关代码；默认关闭。

> 这是可演示的原型，不是生产级安全扫描器。AI 意见需要人工核对。

## 一次审查如何运行

```text
PR 创建或更新 → GitHub Actions 离线测试 → 读取 PR diff
                                        ↓
                             可选：检索仓库代码片段
                                        ↓
                       OpenAI / DeepSeek 审查 → PR 总结 + 可定位的行内评论
                                        └→ review-report.json
```

- [审查工作流](.github/workflows/ai-code-review.yml) 在同仓库 PR 创建或更新时运行，也支持输入 PR 编号手动重跑。
- [Python 审查器](.ai-review/ai-agent-review.py) 最多处理 PR 前 10 个文件中具有文本 patch 的文件；跳过的文件会记录在报告中。
- 审查结果写入 `review-report.json`，并创建或更新同一条 PR 总结评论；能匹配变更行的意见也会发布为行内评论。同一提交重复运行不会重复发送相同的行内意见，无法定位或发布失败的意见仍留在总结中。
- [RAG 模块](.ai-review/rag/) 从默认分支构建本地 JSON 索引；索引或检索失败时继续使用纯 diff 审查。
- [离线测试](tests/) 不调用 GitHub 或 OpenAI API。
- [离线评测基础](evaluation/README.md) 提供标注样例、格式校验和人工匹配后的评分；目前没有真实模型成绩。

## 在 GitHub 上演示

1. 在仓库的 **Settings → Secrets and variables → Actions** 中添加所选提供方的仓库密钥：OpenAI 使用 `OPENAI_API_KEY`，DeepSeek 使用 `DEEPSEEK_API_KEY`。不要把密钥写入代码、Issue、PR 或聊天记录。
2. 从本仓库创建分支，按[演示步骤](examples/demo/README.md)修改示例文件并发起 PR。
3. 查看 **AI Code Review** 工作流、PR 评论和 Actions 产物 `review-report.json`。模型输出会变化，请以真实运行结果为准。

可选的 Actions variables：

| 名称 | 默认值 | 用途 |
| --- | --- | --- |
| `AI_PROVIDER` | `openai` | 设为 `deepseek` 时改用 DeepSeek 审查 |
| `RAG_ENABLED` | `false` | 设为 `true` 时检索默认分支的相关代码 |
| `OPENAI_MODEL` | `gpt-4.1-mini` | 指定可用的 Chat Completions 模型 |
| `DEEPSEEK_MODEL` | `deepseek-flash` | 指定 DeepSeek 审查模型 |

来自 fork 的 PR 不会自动运行带密钥的审查 job。维护者可在 Actions 中手动输入 PR 编号；工作流使用默认分支的审查器，通过 GitHub API 读取 PR diff，不执行 PR 分支代码。启用 RAG 时仍需 `OPENAI_API_KEY`，相关仓库代码片段会发送给 OpenAI Embeddings API；只有 DeepSeek 密钥时，RAG 会回退为纯 diff 审查。

## 本地运行与验证

使用 Python 3.11。离线测试不需要 API 密钥：

```bash
python -m unittest discover -s tests -v
python evaluation/score.py validate evaluation/benchmark.json
```

如需在本地审查真实 PR，先安装 `requests>=2.31,<3`，再设置 `GITHUB_TOKEN`、`REPO_NAME`（如 `owner/repo`）、`PR_NUMBER` 和所选提供方的密钥。默认使用 `OPENAI_API_KEY`；使用 DeepSeek 时设置 `AI_PROVIDER=deepseek` 与 `DEEPSEEK_API_KEY`。随后运行：

```bash
python .ai-review/ai-agent-review.py
```

## 范围与后续

当前只分析前 10 个 PR 文件中的文本 patch；大文件、二进制文件或缺少 patch 的文件可能被跳过。每次审查最多发布 5 条行内评论，其余意见保留在总结中。RAG 默认关闭，尚无真实模型的量化评测数据。多 Agent 审查与自动修复 PR 仍是后续方向，**尚未实现**。

仓库还保留了早期 Node.js 原型和独立的代码质量实验工作流；真实 PR 审查使用上文所述的 Python 流程。原有的[方案文档](ai-agent-code-review-workflow.md)与[实施清单](IMPLEMENTATION-CHECKLIST.md)包含未来设想，不代表现有功能。

参与项目请看[贡献指南](CONTRIBUTING.md)；安全问题请看[安全说明](SECURITY.md)。本项目采用 [MIT 许可证](LICENSE)。
