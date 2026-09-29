#!/usr/bin/env node
/**
 * AI Agent 代码审查脚本（Node.js 版本）
 * 从 GitHub PR 获取代码变更，调用 AI 模型进行审查，发布评论
 */

const https = require('https');
const { execSync } = require('child_process');

// ========== 配置 ==========
const CONFIG = {
  openai: {
    apiKey: process.env.OPENAI_API_KEY,
    model: 'gpt-4',
    temperature: 0.3,
    maxTokens: 2000
  },
  github: {
    token: process.env.GITHUB_TOKEN,
    repo: process.env.REPO_NAME,
    prNumber: process.env.PR_NUMBER
  }
};

// ========== AI 审查引擎 ==========
class AICodeReviewer {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.apiUrl = 'https://api.openai.com/v1/chat/completions';
  }

  async generateReview(codeDiff, filePath) {
    const prompt = this.buildPrompt(codeDiff, filePath);
    
    const payload = JSON.stringify({
      model: CONFIG.openai.model,
      messages: [
        { role: 'system', content: '你是一个专业的代码审查助手，擅长发现代码中的逻辑错误、性能问题、安全风险和可维护性问题。' },
        { role: 'user', content: prompt }
      ],
      temperature: CONFIG.openai.temperature,
      max_tokens: CONFIG.openai.maxTokens
    });

    try {
      const response = await this.makeRequest(this.apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }, payload);

      const reviewText = response.choices[0].message.content;
      return this.parseReview(reviewText);
    } catch (error) {
      console.error(`AI 审查失败: ${error.message}`);
      return { issues: [], error: error.message };
    }
  }

  buildPrompt(codeDiff, filePath) {
    return `
请审查以下代码变更（文件：${filePath}）：

\`\`\`diff
${codeDiff}
\`\`\`

请从以下方面进行审查，并以 JSON 格式返回结果：
1. 代码逻辑正确性
2. 潜在的性能问题
3. 安全风险（SQL 注入、XSS、敏感信息泄露等）
4. 可维护性问题（复杂度、重复代码等）
5. 代码规范（命名、格式等）

返回格式：
\`\`\`json
{
  "issues": [
    {
      "severity": "critical|error|warning|info",
      "line": 123,
      "message": "问题描述",
      "suggestion": "修复建议",
      "code_example": "代码示例（可选）"
    }
  ],
  "summary": "审查总结"
}
\`\`\`
`;
  }

  parseReview(reviewText) {
    try {
      let jsonStr = reviewText;
      
      // 提取 JSON（可能在代码块中）
      if (reviewText.includes('```json')) {
        const start = reviewText.indexOf('```json') + 7;
        const end = reviewText.indexOf('```', start);
        jsonStr = reviewText.substring(start, end).trim();
      }
      
      return JSON.parse(jsonStr);
    } catch (error) {
      console.error(`解析审查结果失败: ${error.message}`);
      return { issues: [], error: '解析失败', raw: reviewText };
    }
  }

  makeRequest(url, options, payload) {
    return new Promise((resolve, reject) => {
      const req = https.request(url, options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          if (res.statusCode === 200) {
            resolve(JSON.parse(data));
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });
      
      req.on('error', (error) => {
        reject(error);
      });
      
      if (payload) {
        req.write(payload);
      }
      
      req.end();
    });
  }
}

// ========== GitHub API 交互 ==========
class GitHubClient {
  constructor(token, repo, prNumber) {
    this.token = token;
    this.repo = repo;
    this.prNumber = prNumber;
    this.apiUrl = 'https://api.github.com';
  }

  async getPRDiff() {
    const url = `${this.apiUrl}/repos/${this.repo}/pulls/${this.prNumber}/files`;
    
    try {
      const data = await this.githubRequest(url);
      return data;
    } catch (error) {
      console.error(`获取 PR diff 失败: ${error.message}`);
      return [];
    }
  }

  async postReviewComment(issues, summary) {
    const commentBody = this.buildCommentBody(issues, summary);
    const url = `${this.apiUrl}/repos/${this.repo}/issues/${this.prNumber}/comments`;
    const payload = { body: commentBody };
    
    try {
      await this.githubRequest(url, 'POST', payload);
      console.log('✓ 审查评论已发布');
      return true;
    } catch (error) {
      console.error(`发布评论失败: ${error.message}`);
      return false;
    }
  }

  buildCommentBody(issues, summary) {
    let body = '## 🤖 AI Agent 代码审查报告\n\n';
    body += `**审查时间**: ${this.getCurrentTime()}\n\n`;

    // 统计
    const stats = { critical: 0, error: 0, warning: 0, info: 0 };
    for (const issue of issues) {
      const severity = issue.severity || 'info';
      if (stats.hasOwnProperty(severity)) {
        stats[severity]++;
      }
    }

    body += '### 📊 问题统计\n\n';
    body += `- 🔴 严重: ${stats.critical}\n`;
    body += `- ⛔ 错误: ${stats.error}\n`;
    body += `- ⚠️ 警告: ${stats.warning}\n`;
    body += `- 💡 建议: ${stats.info}\n\n`;

    // 详细问题
    if (issues.length > 0) {
      body += '### 🔍 详细问题\n\n';
      issues.forEach((issue, index) => {
        const severityIcon = {
          critical: '🔴',
          error: '⛔',
          warning: '⚠️',
          info: '💡'
        }[issue.severity] || '📌';

        body += `#### ${severityIcon} 问题 ${index + 1}: ${issue.message || '未知问题'}\n\n`;
        body += `- **文件**: \`${issue.file || '未知'}\`\n`;
        body += `- **行号**: ${issue.line || '未知'}\n`;
        body += `- **修复建议**: ${issue.suggestion || '无'}\n\n`;

        if (issue.code_example) {
          body += `\`\`\`javascript\n${issue.code_example}\n\`\`\`\n\n`;
        }
      });
    } else {
      body += '### ✅ 未发现明显问题\n\n';
    }

    // 总结
    if (summary) {
      body += '### 📝 审查总结\n\n';
      body += `${summary}\n\n`;
    }

    body += '---\n*本审查由 AI Agent 自动生成*';

    return body;
  }

  getCurrentTime() {
    return new Date().toISOString().replace('T', ' ').substring(0, 19);
  }

  githubRequest(url, method = 'GET', payload = null) {
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const options = {
        hostname: urlObj.hostname,
        path: urlObj.pathname + urlObj.search,
        method: method,
        headers: {
          'Authorization': `token ${this.token}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'AI-Code-Review'
        }
      };

      if (payload) {
        const body = JSON.stringify(payload);
        options.headers['Content-Type'] = 'application/json';
        options.headers['Content-Length'] = Buffer.byteLength(body);
      }

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(JSON.parse(data));
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      if (payload) {
        req.write(JSON.stringify(payload));
      }

      req.end();
    });
  }
}

// ========== 主流程 ==========
async function main() {
  // 验证环境变量
  const { OPENAI_API_KEY, GITHUB_TOKEN, PR_NUMBER, REPO_NAME } = process.env;

  if (!OPENAI_API_KEY || !GITHUB_TOKEN || !PR_NUMBER || !REPO_NAME) {
    console.error('❌ 缺少必要的环境变量');
    process.exit(1);
  }

  console.log(`开始审查 PR #${PR_NUMBER}...`);

  // 1. 获取 PR 变更
  const githubClient = new GitHubClient(GITHUB_TOKEN, REPO_NAME, PR_NUMBER);
  const files = await githubClient.getPRDiff();

  if (!files || files.length === 0) {
    console.log('未找到代码变更');
    return;
  }

  console.log(`找到 ${files.length} 个文件变更`);

  // 2. AI 审查
  const reviewer = new AICodeReviewer(OPENAI_API_KEY);
  const allIssues = [];

  for (const file of files.slice(0, 10)) {
    const filePath = file.filename;
    const patch = file.patch || '';

    if (!patch) continue;

    console.log(`审查文件: ${filePath}`);
    const result = await reviewer.generateReview(patch, filePath);

    if (result.issues) {
      for (const issue of result.issues) {
        issue.file = filePath;
        allIssues.push(issue);
      }
    }
  }

  // 3. 发布审查结果
  const summary = result ? result.summary : '';
  await githubClient.postReviewComment(allIssues, summary);

  // 4. 保存结果到文件（用于后续步骤）
  const output = {
    pr_number: parseInt(PR_NUMBER),
    issues: allIssues,
    summary: summary,
    issue_count: allIssues.length
  };

  require('fs').writeFileSync('review-report.json', JSON.stringify(output, null, 2));
  console.log(`✓ 审查完成，发现 ${allIssues.length} 个问题`);
}

main().catch(error => {
  console.error(`执行失败: ${error.message}`);
  process.exit(1);
});
