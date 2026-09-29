# AI Agent Code Review

一个用于展示真实 PR 自动审查流程的面试项目。GitHub Actions 读取 PR 的代码变更，调用 OpenAI 模型生成审查意见，并把结果发布到 PR 评论。仓库上下文检索（RAG）可选，默认关闭。

## 当前实现

- `.github/workflows/ai-code-review.yml` 是唯一由 PR 触发的审查工作流，也支持手动输入 PR 编号重跑。
- `.ai-review/ai-agent-review.py` 获取 PR 文件和 diff，审查最多 10 个有文本 patch 的文件，生成 `review-report.json`，并创建或更新同一条机器人评论。
- `.ai-review/rag/` 可检索默认分支中的相关代码片段。索引或检索失败时，审查继续使用纯 diff。
- `tests/` 提供不调用外部 API 的流程和检索测试。

`code-quality.yml` 是单独的代码质量实验工作流，不参与 PR 审查。Node.js 审查脚本和 `.ai-review-config.yml` 保留为早期原型，真实 PR 流程使用 Python 脚本，也不会读取该 YAML 配置。

## 配置与演示

1. 将本项目推送到 GitHub 仓库的默认分支，并在仓库 Actions secrets 中设置 `OPENAI_API_KEY`。
2. 从该仓库创建一个分支，按 [演示步骤](examples/demo/README.md) 修改示例文件，提交并发起 PR。GitHub Actions 会运行离线测试，再执行真实审查。
3. 在 PR 页面查看机器人评论；在 Actions 运行记录中下载 `review-report.json`。再次推送或手动重跑时，审查器会更新已有的机器人评论。

仓库 Actions variables 可选设置：

| 名称 | 默认值 | 作用 |
| --- | --- | --- |
| `RAG_ENABLED` | `false` | 设为 `true` 时加入默认分支的相关代码片段 |
| `OPENAI_MODEL` | `gpt-4.1-mini` | 选择有权限使用的 Chat Completions 模型 |

来自 fork 的 PR 不会自动获取仓库密钥，也不会运行审查 job。维护者可以在 Actions 中手动运行工作流，输入该 PR 编号；工作流始终检出默认分支的审查器代码，只通过 GitHub API 读取 PR diff，不执行 PR 分支代码。

## 本地验证

需要 Python 3.11。离线测试不需要 API 密钥：

```bash
python -m unittest discover -s tests -v
```

本地连接真实 API 需要安装 `requests`，并设置 `OPENAI_API_KEY`、`GITHUB_TOKEN`、`REPO_NAME`（例如 `owner/repo`）和 `PR_NUMBER`，随后运行：

```bash
python .ai-review/ai-agent-review.py
```

## 边界与后续

模型意见需要人工核对。目前只审查前 10 个 PR 文件中的文本 patch；报告会列出其余跳过的文件。评论是 PR 总结评论，没有行内定位。RAG 使用本地 JSON 缓存，启用时会将选中的仓库代码发送到 OpenAI Embeddings API。自动修复、多 Agent 和量化评测尚未实现。

仓库原有的 [方案文档](ai-agent-code-review-workflow.md) 与 [实施清单](IMPLEMENTATION-CHECKLIST.md) 包含未来设想，不代表现有功能。下一阶段适合建立真实 PR 评测集，再衡量 RAG 是否提升检出率及误报率。
