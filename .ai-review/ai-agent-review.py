#!/usr/bin/env python3
"""
AI Agent 代码审查脚本
从 GitHub PR 获取代码变更，调用 AI 模型进行审查，发布评论
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any

# ========== 配置 ==========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PR_NUMBER = os.getenv("PR_NUMBER")
REPO_NAME = os.getenv("REPO_NAME")

# ========== AI 审查引擎 ==========
class AICodeReviewer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_review(self, code_diff: str, file_path: str) -> Dict[str, Any]:
        """
        使用 AI 模型生成代码审查意见
        """
        prompt = self._build_prompt(code_diff, file_path)
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "你是一个专业的代码审查助手，擅长发现代码中的逻辑错误、性能问题、安全风险和可维护性问题。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            review_text = result["choices"][0]["message"]["content"]
            return self._parse_review(review_text)
        except Exception as e:
            print(f"AI 审查失败: {e}")
            return {"issues": [], "error": str(e)}
    
    def _build_prompt(self, code_diff: str, file_path: str) -> str:
        """构建审查提示词"""
        return f"""
请审查以下代码变更（文件：{file_path}）：

```
{code_diff}
```

请从以下方面进行审查，并以 JSON 格式返回结果：
1. 代码逻辑正确性
2. 潜在的性能问题
3. 安全风险（SQL 注入、XSS、敏感信息泄露等）
4. 可维护性问题（复杂度、重复代码等）
5. 代码规范（命名、格式等）

返回格式：
```json
{{
  "issues": [
    {{
      "severity": "critical|error|warning|info",
      "line": 123,
      "message": "问题描述",
      "suggestion": "修复建议",
      "code_example": "代码示例（可选）"
    }}
  ],
  "summary": "审查总结"
}}
```
"""
    
    def _parse_review(self, review_text: str) -> Dict[str, Any]:
        """解析 AI 返回的审查结果"""
        try:
            # 提取 JSON（可能在代码块中）
            if "```json" in review_text:
                start = review_text.find("```json") + 7
                end = review_text.find("```", start)
                json_str = review_text[start:end].strip()
            else:
                json_str = review_text
            
            return json.loads(json_str)
        except Exception as e:
            print(f"解析审查结果失败: {e}")
            return {"issues": [], "error": "解析失败", "raw": review_text}

# ========== GitHub API 交互 ==========
class GitHubClient:
    def __init__(self, token: str, repo: str, pr_number: str):
        self.token = token
        self.repo = repo
        self.pr_number = pr_number
        self.api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_pr_diff(self) -> List[Dict[str, Any]]:
        """获取 PR 的代码变更"""
        url = f"{self.api_url}/repos/{self.repo}/pulls/{self.pr_number}/files"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取 PR diff 失败: {e}")
            return []
    
    def post_review_comment(self, issues: List[Dict], summary: str) -> bool:
        """发布审查评论到 PR"""
        # 构建评论内容
        comment_body = self._build_comment_body(issues, summary)
        
        url = f"{self.api_url}/repos/{self.repo}/issues/{self.pr_number}/comments"
        payload = {"body": comment_body}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            print("✓ 审查评论已发布")
            return True
        except Exception as e:
            print(f"发布评论失败: {e}")
            return False
    
    def _build_comment_body(self, issues: List[Dict], summary: str) -> str:
        """构建评论内容（Markdown 格式）"""
        body = "## 🤖 AI Agent 代码审查报告\n\n"
        body += f"**审查时间**: {self._get_current_time()}\n\n"
        
        # 统计
        stats = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        for issue in issues:
            severity = issue.get("severity", "info")
            if severity in stats:
                stats[severity] += 1
        
        body += "### 📊 问题统计\n\n"
        body += f"- 🔴 严重: {stats['critical']}\n"
        body += f"- ⛔ 错误: {stats['error']}\n"
        body += f"- ⚠️ 警告: {stats['warning']}\n"
        body += f"- 💡 建议: {stats['info']}\n\n"
        
        # 详细问题
        if issues:
            body += "### 🔍 详细问题\n\n"
            for i, issue in enumerate(issues, 1):
                severity_icon = {
                    "critical": "🔴",
                    "error": "⛔",
                    "warning": "⚠️",
                    "info": "💡"
                }.get(issue.get("severity", "info"), "❓")
                
                body += f"#### {severity_icon} 问题 {i}: {issue.get('message', '未知问题')}\n\n"
                body += f"- **文件**: `{issue.get('file', '未知')}`\n"
                body += f"- **行号**: {issue.get('line', '未知')}\n"
                body += f"- **修复建议**: {issue.get('suggestion', '无')}\n\n"
                
                if issue.get("code_example"):
                    body += f"```javascript\n{issue['code_example']}\n```\n\n"
        else:
            body += "### ✅ 未发现明显问题\n\n"
        
        # 总结
        if summary:
            body += f"### 📝 审查总结\n\n{summary}\n\n"
        
        body += "---\n*本审查由 AI Agent 自动生成*"
        
        return body
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ========== 主流程 ==========
def main():
    # 验证环境变量
    if not all([OPENAI_API_KEY, GITHUB_TOKEN, PR_NUMBER, REPO_NAME]):
        print("❌ 缺少必要的环境变量")
        sys.exit(1)
    
    print(f"开始审查 PR #{PR_NUMBER}...")
    
    # 1. 获取 PR 变更
    github_client = GitHubClient(GITHUB_TOKEN, REPO_NAME, PR_NUMBER)
    files = github_client.get_pr_diff()
    
    if not files:
        print("未找到代码变更")
        return
    
    print(f"找到 {len(files)} 个文件变更")
    
    # 2. AI 审查
    reviewer = AICodeReviewer(OPENAI_API_KEY)
    all_issues = []
    
    for file in files[:10]:  # 限制审查文件数，避免超时
        file_path = file["filename"]
        patch = file.get("patch", "")
        
        if not patch:
            continue
        
        print(f"审查文件: {file_path}")
        result = reviewer.generate_review(patch, file_path)
        
        if "issues" in result:
            for issue in result["issues"]:
                issue["file"] = file_path
                all_issues.append(issue)
    
    # 3. 发布审查结果
    summary = result.get("summary", "")
    github_client.post_review_comment(all_issues, summary)
    
    # 4. 保存结果到文件（用于后续步骤）
    output = {
        "pr_number": PR_NUMBER,
        "issues": all_issues,
        "summary": summary,
        "issue_count": len(all_issues)
    }
    
    with open("review-report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 审查完成，发现 {len(all_issues)} 个问题")

if __name__ == "__main__":
    main()
