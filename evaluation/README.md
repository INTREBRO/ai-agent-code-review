# 离线评测基础

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
