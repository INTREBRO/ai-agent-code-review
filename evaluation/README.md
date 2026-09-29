# 离线评测基础

## 真实 PR 清单（尚未有模型成绩）

`real_pr_manifest.json` 目前固定了 18 个公开 PR、20 条待评测的问题标注：13 个 PR/15 条问题来自 [CloudAEye C/C++ benchmark](https://github.com/CloudAEye/c_cpp_benchmark)，5 个 PR/5 条问题来自 [AACR-Bench](https://github.com/alibaba/aacr-bench)。每条记录都保存原 PR、固定 base/head 提交、diff 的 SHA-256、问题所在文件和行号，以及原始讨论链接。两个上游数据版本分别固定为 `60733901a3deef2c7128b883cde420fea86d2186` 和 `68a569759289a83654a59d06db2a72910edf0a4a`。来源与许可见 `THIRD_PARTY_NOTICES.md`。

CloudAEye 原有 16 个 PR 中，3 个固定 head 提交在核对时无法从原仓库和复现仓库读取，所以未纳入；Valkey 一条标注位于未改动的上下文行，也明确排除于当前“变更行命中”评分。AACR 补充样例只选择了能在原 PR 找到人类讨论、并落在固定 diff 新增行上的意见。**这些是基准答案，不是本项目模型已检出的结果；当前没有检出率或误报率成绩。**本清单没有经完整人工证明“无缺陷”的负样例，未来精确率尤其需要逐条人工复核模型的新增意见，不能把未匹配标注的意见自动断定为误报。

清单与旧的四个合成样例分开；现有 `score.py` 命令仍只用于合成样例。真实 PR 的准备、双条件运行和人工判定逻辑在 `prepare.py`、`run.py`、`real_pr_score.py`；它们不会在导入时访问上游或调用模型。

`prepare.py` 可按固定提交读取 GitHub compare diff，并只从 base 提交读取变更文件的旧版本，缓存到调用者指定的本地目录。它校验清单中的 diff 哈希与每条问题的新增行位置；超过 64,000 字节、非 UTF-8 或新增而无旧版本的文件会记录在 `skipped_sources`，不会偷偷改用 head 版本。首次核对时，18 个 PR 的固定 diff 均与清单哈希一致；有 2 个样例没有可用的旧版源文件，后续比较必须标注这一覆盖限制。缓存不应提交到仓库。

`lexical_context.py` 对已获取的 base 文件按固定行窗口做关键词重合排序，最多返回调用者指定的字符数。它不调用向量模型，不索引整个仓库；报告中应称为“限定文件的词法检索”，不能把结果解释为现有 OpenAI 向量 RAG 的效果。

## 运行真实 PR 预演

从仓库根目录运行，指定仓库外的缓存和结果目录。首次准备样例会从 GitHub 获取固定提交，可能受匿名访问限额影响；如需提高限额，可在本机临时设置 `GITHUB_TOKEN`，不要把令牌写入仓库。

```bash
python -m evaluation.run --cache-root ../real-pr-cache --out ../real-pr-results --mode diff --limit-cases 3
python -m evaluation.run --cache-root ../real-pr-cache --out ../real-pr-results --mode lexical --limit-cases 3
```

以上默认是零模型调用的预演。付费试跑须由操作者在本机自行设置 `DEEPSEEK_API_KEY`，并显式添加 `--live --max-calls 1`；`--max-calls` 约束单次命令调用量，重复运行同一命令会继续处理尚未完成的文件。一个 PR 可能涉及多个文件，因此 18 个 PR 不等于 18 次模型调用。每次模型输出、token 用量、耗时和错误类型按文件存入结果目录，成功结果按输入哈希复用。单文件差异超过 12,000 字符会跳过，不会截断后伪称完整审查；单 PR 至多处理前 10 个文件，评分前应核对跳过与覆盖范围。

两种条件复用同一生产审查提示词与解析器；唯一实验变量是词法检索给出的旧版本代码片段。由于某些样例没有可读取的旧源文件，不能把这项对比称为“完整仓库向量 RAG”效果。所有 PR 内容都是不可信输入；试跑工具不会执行 PR 代码，也不会向其原仓库发评论。

`real_pr_score.py` 只接收人工完成的判定：每个模型意见必须写 `verdict: "matched"` 且给出对应 `matched_expected_id`，或写 `verdict: "false_positive"` 且匹配 ID 为 `null`。必须覆盖清单的全部 18 个样例；未判定意见、位置不符或重复匹配都会拒绝计分。在全部判定完成之前，不能报告检出率或误报率。当前清单没有独立核验的无缺陷 PR，因此最终精确率只描述这批带问题样例中的模型意见，不代表真实 PR 总体误报率。

`benchmark.json` 包含手写的示例 PR diff、问题标签和无问题样例。它不是实际项目 PR 的随机样本，也没有附带真实模型输出；不能据此宣称模型检出率。

## 校验样例

```bash
python evaluation/score.py validate evaluation/benchmark.json
```

这一步不调用模型，输出中的 `quality_score` 为 `null`。

## 评分真实输出

对每个样例分别运行审查后，人工核对模型意见是否对应预期问题，把结果整理成以下 JSON。`matched_expected_id` 必须由人确认；错误、重复或不对应任何预期问题的意见填 `null`。文件和行号必须与被匹配的预期问题一致。

```json
{
  "cases": [
    {
      "id": "sql-injection",
      "issues": [
        {"file": "db.py", "line": 1, "message": "使用参数化查询", "matched_expected_id": "sql-1"}
      ]
    }
  ]
}
```

实际结果文件必须覆盖 `benchmark.json` 中的**所有**样例，包括没有问题的样例（其 `issues` 为 `[]`）。

```bash
python evaluation/score.py score evaluation/benchmark.json path/to/results.json
python evaluation/score.py compare evaluation/benchmark.json path/to/diff-results.json path/to/rag-results.json
```

程序分别报告真阳性、误报、漏报、精确率、召回率和类别计数。比较功能只计算两组已标注结果的差值，不作统计显著性声明。四个示例样本只能验证流程；若要在面试中展示可靠的效果结论，应补充更多真实、分层标注的 PR 样本，并记录模型、提示词、RAG 设置和运行成本。
