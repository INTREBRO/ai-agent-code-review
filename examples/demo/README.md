# 可重复的 PR 演示

先把审查工作流和本目录合入默认分支，并配置 `OPENAI_API_KEY`。从同一个仓库创建演示分支，将 `user_lookup.py` 的 `find_user` 改成下面这种字符串拼接，然后发起 PR：

```python
def find_user(connection, user_id: str):
    query = f"SELECT id, email FROM users WHERE id = '{user_id}'"
    return connection.execute(query).fetchone()
```

这个改动使输入能改变 SQL 语句结构。审查器应围绕参数化查询给出意见，但模型输出并不保证每次相同；演示时展示实际运行的 PR 评论和 `review-report.json`，不要把预期意见当作已测得结果。

要展示 RAG，可以在仓库 Actions variables 中设 `RAG_ENABLED=true`，然后在 Actions 中手动运行 **AI Code Review**，输入同一个 PR 编号。对比两次真实报告中的证据、问题和耗时。演示结束后可将该变量设回 `false`。
