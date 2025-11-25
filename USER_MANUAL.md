# InsightCosmos 使用手冊

> **版本**: 1.0
> **最後更新**: 2025-11-25
> **適用階段**: Phase 1 - 個人宇宙版

---

## 📚 目錄

1. [快速開始](#快速開始)
2. [個人化配置](#個人化配置)
3. [資料管理](#資料管理)
4. [進階設定](#進階設定)
5. [部署指南](#部署指南)
6. [備份與還原](#備份與還原)
7. [常見問題](#常見問題)
8. [故障排除](#故障排除)

---

## 🚀 快速開始

### 初次安裝

```bash
# 1. Clone 專案
git clone https://github.com/your-repo/InsightCosmos.git
cd InsightCosmos

# 2. 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 配置環境變數
cp .env.example .env
# 編輯 .env 填入你的配置（見下方詳細說明）

# 5. 初始化資料庫
python -m src.memory.database

# 6. 測試運行（不發送郵件）
python -m src.orchestrator.daily_runner --dry-run
```

### 基本使用

```bash
# 執行每日情報收集與分析（生產模式）
python -m src.orchestrator.daily_runner

# 測試模式（不發送郵件，查看報告內容）
python -m src.orchestrator.daily_runner --dry-run

# 詳細日誌模式（用於調試）
python -m src.orchestrator.daily_runner --verbose

# 組合使用
python -m src.orchestrator.daily_runner --dry-run --verbose
```

---

## 🎯 個人化配置

### 1. 修改關注領域與主題

編輯 `.env` 檔案中的 `USER_INTERESTS` 變數：

```bash
# .env

# 基礎設定
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems

# 自訂你的關注領域（用逗號分隔）
# 範例 1: 更廣泛的領域
USER_INTERESTS=AI,Machine Learning,Computer Vision,NLP,Robotics,Autonomous Systems

# 範例 2: 更專注的領域
USER_INTERESTS=Large Language Models,Prompt Engineering,AI Agents,RAG

# 範例 3: 跨領域
USER_INTERESTS=AI,Healthcare,Drug Discovery,Medical Imaging

# 範例 4: 技術 + 商業
USER_INTERESTS=AI,Startups,Venture Capital,Product Management
```

### 2. 調整 RSS 資料來源

編輯 `src/agents/scout_agent.py`，修改 `DEFAULT_FEEDS` 列表：

```python
# src/agents/scout_agent.py

DEFAULT_FEEDS = [
    # 現有來源
    "https://feeds.feedburner.com/blogspot/gJZg",  # Google AI Blog
    "https://openai.com/blog/rss",                  # OpenAI Blog
    "https://www.deepmind.com/blog/rss.xml",        # DeepMind Blog

    # 新增你的自訂來源
    "https://huggingface.co/blog/feed.xml",         # Hugging Face Blog
    "https://blog.research.google/feeds/posts/default", # Google Research
    "https://arxiv-sanity-lite.com/rss",            # ArXiv ML Papers
    "https://www.reddit.com/r/MachineLearning/.rss", # Reddit ML
    "https://news.ycombinator.com/rss",             # Hacker News

    # 行業媒體
    "https://venturebeat.com/category/ai/feed/",    # VentureBeat AI
    "https://techcrunch.com/category/artificial-intelligence/feed/", # TechCrunch AI
]
```

**提示**:
- 使用 [RSS.app](https://rss.app/) 將任何網站轉換為 RSS feed
- 使用 [Feedly](https://feedly.com/) 發現更多高品質 RSS 來源
- 確保 RSS feed URL 有效（可用瀏覽器測試）

### 3. 調整搜索關鍵字

編輯 `src/agents/scout_agent.py`，修改 `DEFAULT_SEARCH_QUERIES`：

```python
# src/agents/scout_agent.py

DEFAULT_SEARCH_QUERIES = [
    # 現有關鍵字
    "AI breakthrough OR AGI OR artificial general intelligence",
    "OpenAI OR Anthropic OR Google AI latest",
    "multimodal AI OR vision language model",

    # 新增你的自訂關鍵字
    # 技術方向
    "retrieval augmented generation RAG",
    "prompt engineering best practices",
    "AI agent framework OR autonomous agents",

    # 應用場景
    "AI in healthcare OR medical AI",
    "robotics manipulation OR robot learning",
    "self-driving OR autonomous vehicles",

    # 商業與趨勢
    "AI startup funding OR AI investment",
    "AI regulation OR AI policy",
    "AGI safety OR AI alignment",

    # 研究前沿
    "transformer architecture OR attention mechanism",
    "reinforcement learning from human feedback RLHF",
    "mixture of experts MoE",
]
```

**搜索技巧**:
- 使用 `OR` 連接同義詞: `"AGI OR artificial general intelligence"`
- 使用引號精確匹配: `"large language model"`
- 使用 `-` 排除關鍵字: `"AI -cryptocurrency"`
- 限制時間範圍: 在 search queries 加上 `after:2025-01-01`

### 4. 調整內容優先度演算法

編輯 `prompts/analyst_prompt.txt`，調整評分標準：

```python
# prompts/analyst_prompt.txt

你的評分標準（0.0-1.0）：

**高優先度 (0.8-1.0)**：
- 技術突破（新模型、新架構、新理論）
- 與 {user_interests} 高度相關
- 有實際應用價值或程式碼
- 來自頂級研究機構或公司
- 有詳細技術細節或論文連結

**中優先度 (0.5-0.7)**：
- 行業趨勢分析
- 應用案例分享
- 工具或框架發布
- 相關但非核心領域

**低優先度 (0.0-0.4)**：
- 新聞報導或公關稿
- 與 {user_interests} 不相關
- 缺乏技術深度
- 過時或重複內容
```

你可以根據自己的需求調整這些標準。例如：

- **學術導向**: 提高論文權重，降低新聞報導權重
- **商業導向**: 提高產品發布、融資新聞權重
- **工程導向**: 提高開源工具、程式碼範例權重

---

## 📧 多人郵件配置

### 方法 1: 修改 Curator Agent（單次發送多人）

編輯 `src/agents/curator_daily.py`，修改收件人列表：

```python
# src/agents/curator_daily.py

def generate_daily_digest(
    config: Config,
    recipient_email: str = None,  # 單一收件人（保留向後兼容）
    recipient_emails: List[str] = None,  # 新增：多個收件人
    max_articles: int = 10
) -> Dict[str, Any]:
    """
    生成並發送每日情報摘要

    Args:
        config: 配置對象
        recipient_email: 單一收件人（已棄用）
        recipient_emails: 收件人列表（推薦）
        max_articles: 最多包含文章數
    """

    # 向後兼容：如果只提供單一收件人
    if recipient_emails is None:
        if recipient_email:
            recipient_emails = [recipient_email]
        else:
            recipient_emails = [config.email_account]

    # 生成郵件內容（同前）
    html_body = formatter.format_digest(...)
    text_body = formatter.format_digest_text(...)

    # 發送給多個收件人
    results = []
    for email in recipient_emails:
        result = sender.send(
            to_email=email,
            subject=f"InsightCosmos Daily Digest - {today_str}",
            html_body=html_body,
            text_body=text_body
        )
        results.append({
            "email": email,
            "status": result["status"]
        })

    return {
        "status": "success" if all(r["status"] == "success" for r in results) else "partial",
        "recipients": results,
        "total_sent": sum(1 for r in results if r["status"] == "success"),
        "total_failed": sum(1 for r in results if r["status"] != "success")
    }
```

### 方法 2: 使用環境變數配置多個收件人

編輯 `.env` 檔案：

```bash
# .env

# 主要收件人（你自己）
EMAIL_ACCOUNT=your_email@gmail.com

# 額外收件人列表（用逗號分隔）
ADDITIONAL_RECIPIENTS=colleague1@example.com,colleague2@example.com,team@company.com

# 或使用 CC/BCC
EMAIL_CC=colleague@example.com
EMAIL_BCC=archive@company.com
```

然後修改 `src/tools/email_sender.py` 支援 CC/BCC：

```python
# src/tools/email_sender.py

def send(
    self,
    to_email: str,
    subject: str,
    html_body: Optional[str] = None,
    text_body: Optional[str] = None,
    cc: Optional[List[str]] = None,  # 新增
    bcc: Optional[List[str]] = None,  # 新增
    retry_count: int = 3
) -> Dict[str, Any]:
    # ...
    message = self._create_message(to_email, subject, html_body, text_body, cc, bcc)
    # ...

def _create_message(
    self,
    to_email: str,
    subject: str,
    html_body: Optional[str],
    text_body: Optional[str],
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> MIMEMultipart:
    message = MIMEMultipart('alternative')
    message['From'] = self.config.sender_email
    message['To'] = to_email
    message['Subject'] = subject

    # 新增 CC/BCC 支援
    if cc:
        message['Cc'] = ', '.join(cc)
    if bcc:
        message['Bcc'] = ', '.join(bcc)

    # ... rest of the code
```

### 方法 3: 團隊共用郵件列表

使用郵件服務商的郵件列表功能：

1. **Gmail**: 創建 Google Group
   - 訪問 [groups.google.com](https://groups.google.com)
   - 創建群組（例如：`insightcosmos-team@googlegroups.com`）
   - 將團隊成員加入群組
   - 將 `.env` 中的 `EMAIL_ACCOUNT` 設為群組郵件地址

2. **自建郵件列表**:
   ```bash
   # .env
   EMAIL_ACCOUNT=team-digest@your-company.com
   ```
   讓 IT 部門設定 `team-digest@your-company.com` 轉發給所有團隊成員

---

## 🔍 擴大資料搜集範圍

### 1. 增加 RSS Feeds 數量

```python
# src/agents/scout_agent.py

DEFAULT_FEEDS = [
    # 學術來源 (10+)
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.LG",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.CV",
    "https://proceedings.mlr.press/feed.xml",

    # 公司與研究機構 (20+)
    "https://openai.com/blog/rss",
    "https://www.anthropic.com/blog/rss",
    "https://www.deepmind.com/blog/rss.xml",
    "https://ai.meta.com/blog/rss/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://azure.microsoft.com/en-us/blog/topics/ai/feed/",

    # 開源社群 (10+)
    "https://huggingface.co/blog/feed.xml",
    "https://blog.langchain.dev/feed/",
    "https://www.llamaindex.ai/blog/rss.xml",

    # 媒體與新聞 (10+)
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
]
```

**注意事項**:
- RSS feed 越多，抓取時間越長
- 建議分批測試，確保每個 feed 都有效
- 可能需要調整 timeout 設定（見下方）

### 2. 增加搜索查詢數量與頻率

```python
# src/agents/scout_agent.py

# 增加搜索查詢
DEFAULT_SEARCH_QUERIES = [
    # 原有查詢 (5-10個)
    # ...

    # 新增查詢 (10-20個)
    # 按主題分類
    "large language model benchmarks",
    "AI agent reasoning capabilities",
    "vision transformer architecture",
    # ...
]

# 調整搜索參數
def search_articles(queries: List[str], max_results_per_query: int = 5):
    """
    Args:
        max_results_per_query: 每個查詢的最大結果數（預設 5，可調整至 10-20）
    """
```

### 3. 新增其他資料來源

#### 方法 A: 新增 Twitter/X API（需申請 API Key）

```python
# src/tools/twitter_fetcher.py

import tweepy
from typing import List, Dict

def fetch_tweets(
    keywords: List[str],
    max_tweets: int = 50
) -> List[Dict]:
    """
    從 Twitter 抓取相關推文

    需要設定 .env:
        TWITTER_API_KEY=xxx
        TWITTER_API_SECRET=xxx
        TWITTER_ACCESS_TOKEN=xxx
        TWITTER_ACCESS_TOKEN_SECRET=xxx
    """
    # 實作略
    pass
```

#### 方法 B: 新增 Reddit API

```python
# src/tools/reddit_fetcher.py

import praw
from typing import List, Dict

def fetch_reddit_posts(
    subreddits: List[str] = ["MachineLearning", "artificial", "LocalLLaMA"],
    time_filter: str = "day",  # day, week, month
    limit: int = 50
) -> List[Dict]:
    """
    從 Reddit 抓取熱門貼文

    需要設定 .env:
        REDDIT_CLIENT_ID=xxx
        REDDIT_CLIENT_SECRET=xxx
        REDDIT_USER_AGENT=InsightCosmos/1.0
    """
    # 實作略
    pass
```

#### 方法 C: 新增 GitHub Trending

```python
# src/tools/github_fetcher.py

import requests
from typing import List, Dict

def fetch_trending_repos(
    language: str = "python",
    since: str = "daily"  # daily, weekly, monthly
) -> List[Dict]:
    """
    從 GitHub Trending 抓取熱門專案

    使用 GitHub Trending API (非官方):
    https://github-trending-api.now.sh/repositories?language=python&since=daily
    """
    url = f"https://github-trending-api.now.sh/repositories"
    params = {"language": language, "since": since}
    response = requests.get(url, params=params)
    return response.json()
```

然後在 `src/agents/scout_agent.py` 中整合：

```python
# src/agents/scout_agent.py

from src.tools.twitter_fetcher import fetch_tweets
from src.tools.reddit_fetcher import fetch_reddit_posts
from src.tools.github_fetcher import fetch_trending_repos

def collect_articles(
    user_prompt: str = None,
    enable_twitter: bool = False,
    enable_reddit: bool = True,
    enable_github: bool = True
) -> Dict[str, Any]:
    articles = []

    # 原有來源
    articles.extend(fetch_rss_articles(...))
    articles.extend(search_articles(...))

    # 新增來源（可選）
    if enable_twitter:
        articles.extend(fetch_tweets(...))

    if enable_reddit:
        articles.extend(fetch_reddit_posts(...))

    if enable_github:
        articles.extend(fetch_trending_repos(...))

    # 去重與返回
    return deduplicate_and_return(articles)
```

### 4. 調整收集頻率

**每日多次收集**: 修改 cron job 或系統排程

```bash
# crontab -e

# 每天執行 3 次（早上 8 點、中午 12 點、下午 6 點）
0 8 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner
0 12 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner
0 18 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner
```

**即時監控**: 實作 webhook 或持續監控

```python
# src/orchestrator/realtime_monitor.py

import time
from datetime import datetime, timedelta

def realtime_monitor(check_interval_minutes: int = 30):
    """
    每 N 分鐘檢查一次新內容
    """
    while True:
        print(f"[{datetime.now()}] Checking for new content...")

        # 執行收集
        result = run_daily_pipeline(dry_run=False)

        # 如果有新內容，發送通知
        if result["stats"]["phase1_stored"] > 0:
            print(f"Found {result['stats']['phase1_stored']} new articles!")

        # 等待下次檢查
        time.sleep(check_interval_minutes * 60)
```

---

## 🤖 更換 LLM 模型

InsightCosmos 使用 **Google ADK (Agent Development Kit)**，支援多種 LLM 模型。

### 1. 使用不同的 Gemini 模型

編輯 `src/agents/analyst_agent.py` 和 `src/agents/curator_daily.py`：

```python
# src/agents/analyst_agent.py

from google.adk.genai import Gemini

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        # 選項 1: Gemini 2.0 Flash (預設，快速，便宜)
        model=Gemini(model="gemini-2.0-flash-exp"),

        # 選項 2: Gemini 2.5 Flash (更快，最新)
        # model=Gemini(model="gemini-2.5-flash-lite"),

        # 選項 3: Gemini 2.5 Pro (更強大，但更貴更慢)
        # model=Gemini(model="gemini-2.5-pro-preview"),

        # 選項 4: Gemini 1.5 Pro (穩定版)
        # model=Gemini(model="gemini-1.5-pro"),

        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### 2. 使用 OpenAI GPT 模型（需額外配置）

ADK 也支援 OpenAI 模型。需先安裝並配置：

```bash
# .env
OPENAI_API_KEY=sk-xxx
```

```python
# src/agents/analyst_agent.py

from google.adk.openai import OpenAI  # 注意：從 ADK 導入

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        # 使用 OpenAI GPT-4o
        model=OpenAI(model="gpt-4o"),

        # 或 GPT-4o-mini (更便宜)
        # model=OpenAI(model="gpt-4o-mini"),

        # 或 GPT-4 Turbo
        # model=OpenAI(model="gpt-4-turbo"),

        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### 3. 使用 Anthropic Claude 模型

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-xxx
```

```python
# src/agents/analyst_agent.py

from google.adk.anthropic import Anthropic

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        # 使用 Claude 3.7 Sonnet
        model=Anthropic(model="claude-3-7-sonnet-20250219"),

        # 或 Claude 3.5 Opus (最強大)
        # model=Anthropic(model="claude-3-5-opus"),

        # 或 Claude 3.5 Haiku (最便宜)
        # model=Anthropic(model="claude-3-5-haiku"),

        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### 4. 混合使用多個模型

不同 Agent 使用不同模型：

```python
# src/agents/analyst_agent.py
# 使用 Claude Sonnet (推理能力強)
model=Anthropic(model="claude-3-7-sonnet-20250219")

# src/agents/curator_daily.py
# 使用 Gemini Flash (生成報告快)
model=Gemini(model="gemini-2.0-flash-exp")

# src/agents/scout_agent.py
# 不需要 LLM（純工具調用）
```

### 5. 本地 LLM（Ollama）

如果想使用本地 LLM（節省成本），可使用 Ollama：

```bash
# 安裝 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下載模型
ollama pull llama3.3:70b
# 或 ollama pull qwen2.5:72b
```

然後創建 ADK 相容的包裝器：

```python
# src/utils/ollama_wrapper.py

from google.adk.llm import LLM
import requests
from typing import Dict, Any

class OllamaLLM(LLM):
    def __init__(self, model: str = "llama3.3:70b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str, **kwargs) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]
```

使用：

```python
# src/agents/analyst_agent.py

from src.utils.ollama_wrapper import OllamaLLM

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        model=OllamaLLM(model="llama3.3:70b"),
        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### 模型選擇建議

| 場景 | 推薦模型 | 原因 |
|-----|---------|------|
| 成本優先 | Gemini 2.5 Flash Lite | 最便宜，速度快 |
| 速度優先 | Gemini 2.0 Flash | 超快響應，適合即時 |
| 品質優先 | Claude 3.7 Sonnet | 推理能力強，文字品質高 |
| 平衡選擇 | GPT-4o | 速度與品質兼顧 |
| 隱私優先 | Ollama (Local) | 本地運行，無數據外洩風險 |
| 測試開發 | Gemini Flash | 免費額度高，適合開發 |

---

## 📊 資料管理

### 1. 查看資料庫內容

#### 方法 A: 使用 SQLite 命令列工具

```bash
# 進入資料庫
sqlite3 data/insights.db

# 查看所有文章
SELECT id, title, source, status, priority_score, created_at FROM articles ORDER BY created_at DESC LIMIT 10;

# 查看高優先度文章
SELECT id, title, priority_score FROM articles WHERE priority_score >= 0.8 ORDER BY priority_score DESC;

# 查看各來源的文章數量
SELECT source_name, COUNT(*) as count FROM articles GROUP BY source_name ORDER BY count DESC;

# 查看各狀態的文章數量
SELECT status, COUNT(*) as count FROM articles GROUP BY status;

# 匯出為 CSV
.headers on
.mode csv
.output articles_export.csv
SELECT * FROM articles WHERE created_at > date('now', '-7 days');
.output stdout
```

#### 方法 B: 使用 Python 腳本

創建查詢工具：

```python
# scripts/query_database.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import Database
from src.utils.config import Config
import json

def main():
    config = Config.from_env()
    db = Database.from_config(config)

    # 查詢最近 7 天的高分文章
    query = """
    SELECT id, title, source_name, priority_score, created_at
    FROM articles
    WHERE created_at > date('now', '-7 days')
      AND priority_score >= 0.7
    ORDER BY priority_score DESC, created_at DESC
    """

    results = db.conn.execute(query).fetchall()

    print(f"Found {len(results)} high-priority articles:")
    print("=" * 80)

    for row in results:
        print(f"[{row[4]}] ({row[3]:.2f}) {row[1]}")
        print(f"  Source: {row[2]}")
        print()

if __name__ == "__main__":
    main()
```

使用：

```bash
python scripts/query_database.py
```

#### 方法 C: 使用 SQLite GUI 工具

推薦工具：
- **DB Browser for SQLite** (免費): https://sqlitebrowser.org/
- **TablePlus** (Mac/Windows): https://tableplus.com/
- **DataGrip** (JetBrains): https://www.jetbrains.com/datagrip/

步驟：
1. 下載並安裝工具
2. 開啟 `data/insights.db`
3. 使用 GUI 瀏覽、查詢、匯出資料

### 2. 清理舊資料

```python
# scripts/cleanup_old_data.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import Database
from src.utils.config import Config
from datetime import datetime, timedelta

def cleanup_old_articles(days: int = 90):
    """
    刪除 N 天前的文章

    Args:
        days: 保留最近 N 天的資料（預設 90 天）
    """
    config = Config.from_env()
    db = Database.from_config(config)

    cutoff_date = datetime.now() - timedelta(days=days)

    # 計算要刪除的數量
    count_query = "SELECT COUNT(*) FROM articles WHERE created_at < ?"
    count = db.conn.execute(count_query, (cutoff_date,)).fetchone()[0]

    print(f"Found {count} articles older than {days} days")

    if count == 0:
        print("No articles to delete")
        return

    # 確認
    confirm = input(f"Delete {count} articles? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled")
        return

    # 刪除文章
    delete_query = "DELETE FROM articles WHERE created_at < ?"
    db.conn.execute(delete_query, (cutoff_date,))
    db.conn.commit()

    print(f"Deleted {count} articles")

    # VACUUM 釋放空間
    print("Optimizing database...")
    db.conn.execute("VACUUM")
    print("Done!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clean up old articles")
    parser.add_argument("--days", type=int, default=90, help="Keep articles from last N days")
    args = parser.parse_args()

    cleanup_old_articles(args.days)
```

使用：

```bash
# 刪除 90 天前的資料
python scripts/cleanup_old_data.py

# 刪除 30 天前的資料
python scripts/cleanup_old_data.py --days 30
```

### 3. 匯出資料

```python
# scripts/export_data.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import Database
from src.utils.config import Config
import json
import csv
from datetime import datetime

def export_to_json(output_file: str = "export.json"):
    """匯出資料為 JSON"""
    config = Config.from_env()
    db = Database.from_config(config)

    query = "SELECT * FROM articles ORDER BY created_at DESC"
    results = db.conn.execute(query).fetchall()

    # 取得欄位名稱
    columns = [description[0] for description in db.conn.execute(query).description]

    # 轉換為 dict list
    data = [dict(zip(columns, row)) for row in results]

    # 寫入 JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"Exported {len(data)} articles to {output_file}")

def export_to_csv(output_file: str = "export.csv"):
    """匯出資料為 CSV"""
    config = Config.from_env()
    db = Database.from_config(config)

    query = "SELECT * FROM articles ORDER BY created_at DESC"
    results = db.conn.execute(query).fetchall()

    # 取得欄位名稱
    columns = [description[0] for description in db.conn.execute(query).description]

    # 寫入 CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(results)

    print(f"Exported {len(results)} articles to {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export database")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    parser.add_argument("--output", help="Output file name")
    args = parser.parse_args()

    if args.format == "json":
        output = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_to_json(output)
    else:
        output = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_to_csv(output)
```

使用：

```bash
# 匯出為 JSON
python scripts/export_data.py --format json

# 匯出為 CSV
python scripts/export_data.py --format csv --output my_data.csv
```

---

## 🚀 部署指南

### 1. 部署到 Heroku

#### 步驟 1: 準備 Heroku 專案

```bash
# 安裝 Heroku CLI
# Mac: brew install heroku/brew/heroku
# Windows: choco install heroku-cli
# Linux: curl https://cli-assets.heroku.com/install.sh | sh

# 登入
heroku login

# 創建應用
cd InsightCosmos
heroku create insightcosmos-yourname
```

#### 步驟 2: 配置環境變數

```bash
# 設定環境變數
heroku config:set GOOGLE_API_KEY=your_api_key
heroku config:set EMAIL_ACCOUNT=your_email@gmail.com
heroku config:set EMAIL_PASSWORD=your_app_password
heroku config:set USER_NAME=Ray
heroku config:set USER_INTERESTS="AI,Robotics,Multi-Agent Systems"
heroku config:set DATABASE_PATH=/app/data/insights.db
heroku config:set LOG_LEVEL=INFO

# 查看配置
heroku config
```

#### 步驟 3: 創建 Heroku 所需檔案

**Procfile**（告訴 Heroku 如何運行）:

```bash
# Procfile
release: python -m src.memory.database
worker: python -m src.orchestrator.daily_runner
```

**runtime.txt**（指定 Python 版本）:

```
python-3.11.0
```

**添加 PostgreSQL（可選，用於生產環境）**:

```bash
# 添加 PostgreSQL 插件（Heroku 免費版限制 10,000 行）
heroku addons:create heroku-postgresql:mini

# 查看資料庫 URL
heroku config:get DATABASE_URL
```

如果使用 PostgreSQL，需要修改 `src/memory/database.py` 支援 PostgreSQL：

```python
# src/memory/database.py

import os

class Database:
    def __init__(self, database_url: str = None):
        if database_url is None:
            # 本地使用 SQLite
            database_url = os.getenv("DATABASE_PATH", "data/insights.db")
            self.conn = sqlite3.connect(database_url)
        else:
            # Heroku 使用 PostgreSQL
            import psycopg2
            self.conn = psycopg2.connect(database_url, sslmode='require')

        # ... rest of the code
```

#### 步驟 4: 部署

```bash
# 提交程式碼
git add .
git commit -m "Prepare for Heroku deployment"

# 部署到 Heroku
git push heroku main

# 查看日誌
heroku logs --tail

# 手動執行一次 pipeline
heroku run python -m src.orchestrator.daily_runner --dry-run
```

#### 步驟 5: 設定定時任務（Heroku Scheduler）

```bash
# 安裝 Scheduler 插件
heroku addons:create scheduler:standard

# 開啟 Scheduler Dashboard
heroku addons:open scheduler
```

在 Dashboard 中添加任務：
- **Command**: `python -m src.orchestrator.daily_runner`
- **Frequency**: Daily at 8:00 AM (選擇你想要的時間)

#### 步驟 6: 監控與維護

```bash
# 查看應用狀態
heroku ps

# 查看日誌
heroku logs --tail

# 重啟應用
heroku restart

# 擴展 worker（如需要）
heroku ps:scale worker=1
```

### 2. 部署到 AWS Lambda（Serverless）

**優點**:
- 按執行次數付費（更便宜）
- 自動擴展
- 無需管理伺服器

**步驟**:

1. 安裝 Serverless Framework:
```bash
npm install -g serverless
```

2. 創建 `serverless.yml`:
```yaml
service: insightcosmos

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    GOOGLE_API_KEY: ${env:GOOGLE_API_KEY}
    EMAIL_ACCOUNT: ${env:EMAIL_ACCOUNT}
    EMAIL_PASSWORD: ${env:EMAIL_PASSWORD}
    USER_NAME: Ray
    USER_INTERESTS: "AI,Robotics,Multi-Agent Systems"

functions:
  dailyPipeline:
    handler: handler.run_daily
    timeout: 900  # 15 minutes
    events:
      # 每天早上 8 點（UTC）執行
      - schedule: cron(0 8 * * ? *)

package:
  exclude:
    - node_modules/**
    - venv/**
    - tests/**
```

3. 創建 `handler.py`:
```python
# handler.py

def run_daily(event, context):
    from src.orchestrator.daily_runner import run_daily_pipeline
    result = run_daily_pipeline(dry_run=False)
    return {
        'statusCode': 200,
        'body': result
    }
```

4. 部署:
```bash
serverless deploy
```

### 3. 部署到 Google Cloud Run

**優點**:
- 完全託管
- 自動擴展（包括縮減至 0）
- 與 Google AI 整合良好

**步驟**:

1. 創建 `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 初始化資料庫
RUN python -m src.memory.database

# 運行
CMD ["python", "-m", "src.orchestrator.daily_runner"]
```

2. 部署到 Cloud Run:
```bash
# 安裝 gcloud CLI
# https://cloud.google.com/sdk/docs/install

# 登入
gcloud auth login

# 設定專案
gcloud config set project YOUR_PROJECT_ID

# 構建並部署
gcloud run deploy insightcosmos \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=xxx,EMAIL_ACCOUNT=xxx,EMAIL_PASSWORD=xxx
```

3. 設定 Cloud Scheduler（定時執行）:
```bash
gcloud scheduler jobs create http daily-pipeline \
  --schedule="0 8 * * *" \
  --uri="https://insightcosmos-xxx.run.app" \
  --http-method=GET
```

### 4. 本地部署（自動化）

如果想在本地電腦或伺服器持續運行：

#### 方法 A: Cron Job（Linux/Mac）

```bash
# 編輯 crontab
crontab -e

# 添加定時任務（每天早上 8 點執行）
0 8 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner >> /path/to/logs/daily.log 2>&1

# 保存並退出
```

**完整範例**（帶日誌輪替）:

```bash
# 每天早上 8 點執行
0 8 * * * cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python -m src.orchestrator.daily_runner >> /Users/ray/sides/InsightCosmos/logs/daily_$(date +\%Y\%m\%d).log 2>&1

# 每週日晚上 8 點執行週報
0 20 * * 0 cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python -m src.orchestrator.weekly_runner >> /Users/ray/sides/InsightCosmos/logs/weekly_$(date +\%Y\%m\%d).log 2>&1

# 每月 1 號清理 90 天前的資料
0 0 1 * * cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python scripts/cleanup_old_data.py --days 90 >> /Users/ray/sides/InsightCosmos/logs/cleanup.log 2>&1
```

#### 方法 B: systemd Service（Linux）

創建 systemd service 文件：

```ini
# /etc/systemd/system/insightcosmos.service

[Unit]
Description=InsightCosmos Daily Pipeline
After=network.target

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/InsightCosmos
ExecStart=/path/to/venv/bin/python -m src.orchestrator.daily_runner
StandardOutput=append:/path/to/logs/daily.log
StandardError=append:/path/to/logs/error.log

[Install]
WantedBy=multi-user.target
```

創建 timer 文件：

```ini
# /etc/systemd/system/insightcosmos.timer

[Unit]
Description=Run InsightCosmos Daily at 8 AM

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

啟用 service:

```bash
# 重新載入 systemd
sudo systemctl daemon-reload

# 啟用 timer
sudo systemctl enable insightcosmos.timer

# 啟動 timer
sudo systemctl start insightcosmos.timer

# 查看狀態
sudo systemctl status insightcosmos.timer

# 查看日誌
sudo journalctl -u insightcosmos.service -f
```

#### 方法 C: Windows Task Scheduler

1. 開啟 Task Scheduler
2. 創建基本任務
3. 設定觸發器（每天早上 8 點）
4. 設定動作：
   - **Program**: `C:\path\to\InsightCosmos\venv\Scripts\python.exe`
   - **Arguments**: `-m src.orchestrator.daily_runner`
   - **Start in**: `C:\path\to\InsightCosmos`
5. 完成

---

## 💾 備份與還原

### 1. 資料庫備份

#### 自動備份腳本

```python
# scripts/backup_database.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
from datetime import datetime
from src.utils.config import Config

def backup_database(backup_dir: str = "backups"):
    """
    備份資料庫

    Args:
        backup_dir: 備份目錄
    """
    config = Config.from_env()
    db_path = Path(config.database_path)

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    # 創建備份目錄
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    # 備份檔案名稱（包含時間戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"insights_backup_{timestamp}.db"

    # 複製資料庫
    print(f"Backing up database to {backup_file}...")
    shutil.copy2(db_path, backup_file)

    # 壓縮備份（可選）
    import gzip
    with open(backup_file, 'rb') as f_in:
        with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # 刪除未壓縮的備份
    backup_file.unlink()

    print(f"Backup completed: {backup_file}.gz")
    print(f"Backup size: {(backup_path / f'{backup_file.name}.gz').stat().st_size / 1024 / 1024:.2f} MB")

    # 清理舊備份（保留最近 30 個）
    cleanup_old_backups(backup_path, keep=30)

def cleanup_old_backups(backup_dir: Path, keep: int = 30):
    """
    清理舊備份，保留最近 N 個

    Args:
        backup_dir: 備份目錄
        keep: 保留數量
    """
    backups = sorted(backup_dir.glob("insights_backup_*.db.gz"), reverse=True)

    if len(backups) <= keep:
        return

    print(f"\nCleaning up old backups (keeping {keep} most recent)...")
    for backup in backups[keep:]:
        print(f"  Deleting: {backup.name}")
        backup.unlink()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Backup InsightCosmos database")
    parser.add_argument("--dir", default="backups", help="Backup directory")
    args = parser.parse_args()

    backup_database(args.dir)
```

使用：

```bash
# 手動備份
python scripts/backup_database.py

# 指定備份目錄
python scripts/backup_database.py --dir /path/to/backups
```

#### 自動定時備份（Cron）

```bash
# crontab -e

# 每天凌晨 2 點備份
0 2 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python scripts/backup_database.py >> /path/to/logs/backup.log 2>&1

# 每週日凌晨 3 點備份到遠端（使用 rsync）
0 3 * * 0 rsync -av /path/to/InsightCosmos/backups/ user@remote-server:/backups/insightcosmos/
```

### 2. 備份到雲端

#### 備份到 Google Drive

```python
# scripts/backup_to_gdrive.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

def backup_to_gdrive(backup_file: str, folder_id: str = None):
    """
    上傳備份到 Google Drive

    Args:
        backup_file: 備份檔案路徑
        folder_id: Google Drive 資料夾 ID（可選）

    需要設定 Google Drive API:
    https://developers.google.com/drive/api/quickstart/python
    """
    # 載入憑證
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.file'])

    # 建立 Drive API client
    service = build('drive', 'v3', credentials=creds)

    # 上傳檔案
    file_metadata = {
        'name': os.path.basename(backup_file),
        'parents': [folder_id] if folder_id else []
    }
    media = MediaFileUpload(backup_file, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f"Uploaded to Google Drive: {file.get('id')}")

# 使用
# backup_to_gdrive("backups/insights_backup_20251125_080000.db.gz", "YOUR_FOLDER_ID")
```

#### 備份到 AWS S3

```python
# scripts/backup_to_s3.py

import boto3
from pathlib import Path

def backup_to_s3(backup_file: str, bucket_name: str, prefix: str = "insightcosmos"):
    """
    上傳備份到 AWS S3

    Args:
        backup_file: 備份檔案路徑
        bucket_name: S3 bucket 名稱
        prefix: S3 物件前綴（資料夾）

    需要設定 AWS 憑證:
    aws configure
    """
    s3 = boto3.client('s3')

    # 生成 S3 物件 key
    file_name = Path(backup_file).name
    s3_key = f"{prefix}/{file_name}"

    # 上傳
    print(f"Uploading {backup_file} to s3://{bucket_name}/{s3_key}...")
    s3.upload_file(backup_file, bucket_name, s3_key)
    print("Upload completed")

# 使用
# backup_to_s3("backups/insights_backup_20251125_080000.db.gz", "my-backups-bucket")
```

### 3. 還原資料庫

```python
# scripts/restore_database.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
import gzip
from datetime import datetime
from src.utils.config import Config

def list_backups(backup_dir: str = "backups"):
    """列出所有可用的備份"""
    backup_path = Path(backup_dir)
    backups = sorted(backup_path.glob("insights_backup_*.db.gz"), reverse=True)

    if not backups:
        print("No backups found")
        return []

    print("Available backups:")
    print("=" * 80)
    for i, backup in enumerate(backups, 1):
        timestamp = backup.stem.split("_")[-2:]
        date_str = f"{timestamp[0][:4]}-{timestamp[0][4:6]}-{timestamp[0][6:8]} {timestamp[1][:2]}:{timestamp[1][2:4]}:{timestamp[1][4:6]}"
        size_mb = backup.stat().st_size / 1024 / 1024
        print(f"{i}. {backup.name} ({date_str}, {size_mb:.2f} MB)")
    print("=" * 80)

    return backups

def restore_database(backup_file: str):
    """
    還原資料庫

    Args:
        backup_file: 備份檔案路徑（.db.gz）
    """
    config = Config.from_env()
    db_path = Path(config.database_path)
    backup_path = Path(backup_file)

    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}")
        return

    # 備份當前資料庫（如果存在）
    if db_path.exists():
        current_backup = db_path.parent / f"insights_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        print(f"Backing up current database to {current_backup}...")
        shutil.copy2(db_path, current_backup)

    # 解壓縮備份
    print(f"Restoring database from {backup_path}...")
    with gzip.open(backup_path, 'rb') as f_in:
        with open(db_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    print("Database restored successfully!")
    print(f"Database location: {db_path}")

def restore_interactive(backup_dir: str = "backups"):
    """互動式還原"""
    backups = list_backups(backup_dir)

    if not backups:
        return

    # 選擇備份
    while True:
        try:
            choice = input("\nSelect backup to restore (number): ")
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                break
            else:
                print("Invalid selection")
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled")
            return

    selected_backup = backups[idx]

    # 確認
    print(f"\nYou are about to restore: {selected_backup.name}")
    confirm = input("This will overwrite the current database. Continue? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Cancelled")
        return

    # 還原
    restore_database(str(selected_backup))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Restore InsightCosmos database")
    parser.add_argument("--dir", default="backups", help="Backup directory")
    parser.add_argument("--file", help="Specific backup file to restore")
    args = parser.parse_args()

    if args.file:
        restore_database(args.file)
    else:
        restore_interactive(args.dir)
```

使用：

```bash
# 互動式還原（會列出所有備份供選擇）
python scripts/restore_database.py

# 還原特定備份
python scripts/restore_database.py --file backups/insights_backup_20251125_080000.db.gz
```

### 4. 資料遷移（SQLite → PostgreSQL）

如果要從 SQLite 遷移到 PostgreSQL（用於生產環境）：

```bash
# 安裝 pgloader
# Mac: brew install pgloader
# Ubuntu: apt-get install pgloader

# 遷移
pgloader data/insights.db postgresql://user:password@localhost/insightcosmos
```

---

## ❓ 常見問題

### Q1: 如何測試郵件配置是否正確？

```bash
# 使用測試腳本
python -c "
from src.tools.email_sender import EmailSender, EmailConfig
from src.utils.config import Config

config = Config.from_env()
email_config = EmailConfig(
    sender_email=config.email_account,
    sender_password=config.email_password
)

sender = EmailSender(email_config)
result = sender.test_connection()
print(result)
"
```

### Q2: 如何查看 Pipeline 執行日誌？

```bash
# 查看最近的日誌
tail -f logs/insightcosmos.log

# 搜尋特定錯誤
grep "ERROR" logs/insightcosmos.log

# 查看特定日期的日誌
cat logs/insightcosmos.log | grep "2025-11-25"
```

### Q3: 如何限制 API 使用成本？

```python
# src/utils/config.py

class Config:
    # 添加成本控制參數
    max_articles_per_day: int = 50  # 限制每日處理文章數
    max_api_calls_per_day: int = 100  # 限制 API 呼叫次數
    use_cache: bool = True  # 啟用快取
```

然後在 `daily_runner.py` 中添加檢查：

```python
# src/orchestrator/daily_runner.py

def _run_phase2_analyst(self) -> int:
    # 檢查今日已處理數量
    today_count = self.article_store.get_analyzed_count_today()

    if today_count >= self.config.max_articles_per_day:
        self.logger.warning(f"Reached daily limit: {today_count}/{self.config.max_articles_per_day}")
        return 0

    # 限制處理數量
    pending_articles = self.article_store.get_by_status("collected")
    pending_articles = pending_articles[:self.config.max_articles_per_day - today_count]

    # ... 繼續處理
```

### Q4: 如何加快 Pipeline 執行速度？

**方法 1**: 平行處理文章分析

```python
# src/orchestrator/daily_runner.py

import asyncio
from concurrent.futures import ThreadPoolExecutor

async def _run_phase2_analyst_parallel(self) -> int:
    """平行分析文章"""
    pending_articles = self.article_store.get_by_status("collected")

    async def analyze_one(article_dict):
        # ... 分析單篇文章
        pass

    # 使用 asyncio.gather 平行執行
    results = await asyncio.gather(*[analyze_one(article) for article in pending_articles])

    return sum(1 for r in results if r["status"] == "success")
```

**方法 2**: 使用更快的 LLM 模型

```python
# 使用 Gemini 2.5 Flash (最快)
model=Gemini(model="gemini-2.5-flash-lite")
```

**方法 3**: 減少資料來源

- 減少 RSS feeds 數量
- 減少搜索查詢數量
- 調整 `max_articles` 參數

### Q5: 如何處理 Rate Limit 錯誤？

```python
# src/agents/analyst_agent.py

import time
from google.api_core import retry

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        model=Gemini(
            model="gemini-2.0-flash-exp",
            # 添加 retry 配置
            retry=retry.Retry(
                initial=1.0,
                maximum=60.0,
                multiplier=2.0,
                deadline=300.0
            )
        ),
        # ...
    )
```

或在 orchestrator 中添加延遲：

```python
# src/orchestrator/daily_runner.py

for idx, article_dict in enumerate(pending_articles, 1):
    # 每分析 5 篇文章，暫停 10 秒
    if idx % 5 == 0:
        self.logger.info("  Pausing to avoid rate limit...")
        time.sleep(10)

    # 分析文章
    result = runner.analyze_article(...)
```

---

## 🔧 故障排除

### 問題 1: 無法發送郵件（Authentication Failed）

**症狀**:
```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**解決方案**:

1. 確認使用的是 **App Password**（不是帳號密碼）
   - Gmail: https://support.google.com/accounts/answer/185833
   - 前往 Google 帳戶 → 安全性 → 兩步驟驗證 → 應用程式密碼
   - 生成新的應用程式密碼
   - 將密碼更新到 `.env` 的 `EMAIL_PASSWORD`

2. 確認 `.env` 格式正確（無多餘空格）:
   ```bash
   EMAIL_ACCOUNT=your_email@gmail.com
   EMAIL_PASSWORD=abcd efgh ijkl mnop  # 注意：App Password 包含空格是正常的
   ```

3. 測試連線:
   ```bash
   python -c "from src.tools.email_sender import *; sender = EmailSender(EmailConfig(sender_email='xxx', sender_password='xxx')); print(sender.test_connection())"
   ```

### 問題 2: Google Search Grounding 失敗

**症狀**:
```
Error: Google Search Grounding failed
```

**解決方案**:

1. 確認 API Key 有效且有 Search Grounding 權限
   - 訪問 [Google AI Studio](https://aistudio.google.com/apikey)
   - 確認 API Key 狀態為 "Active"
   - 確認有足夠的免費配額

2. 檢查網路連線（Search Grounding 需要網路）

3. 如果持續失敗，切換為純 RSS 模式：
   ```python
   # src/agents/scout_agent.py

   def collect_articles(...):
       # 暫時關閉 Google Search
       # articles.extend(search_articles(...))  # 註解掉

       # 只使用 RSS
       articles.extend(fetch_rss_articles(...))
   ```

### 問題 3: 資料庫鎖定（Database is locked）

**症狀**:
```
sqlite3.OperationalError: database is locked
```

**原因**: 多個程序同時存取 SQLite 資料庫

**解決方案**:

1. 確認沒有多個 Pipeline 同時運行:
   ```bash
   ps aux | grep daily_runner
   # 如果有多個，刪除多餘的
   kill <PID>
   ```

2. 增加 SQLite timeout:
   ```python
   # src/memory/database.py

   self.conn = sqlite3.connect(
       database_path,
       timeout=30.0  # 增加 timeout（預設 5.0）
   )
   ```

3. 考慮遷移到 PostgreSQL（生產環境推薦）

### 問題 4: 記憶體不足（Memory Error）

**症狀**:
```
MemoryError: Unable to allocate array
```

**原因**: 處理太多文章或 embedding 佔用過多記憶體

**解決方案**:

1. 減少每次處理的文章數量:
   ```python
   # src/orchestrator/daily_runner.py

   # 分批處理，每批 10 篇
   batch_size = 10
   for i in range(0, len(pending_articles), batch_size):
       batch = pending_articles[i:i+batch_size]
       # 處理 batch
   ```

2. 定期清理舊資料:
   ```bash
   python scripts/cleanup_old_data.py --days 30
   ```

3. 增加系統 swap（Linux）:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### 問題 5: RSS Feed 無法讀取

**症狀**:
```
Error fetching RSS feed: HTTP 403 Forbidden
```

**原因**: 某些網站封鎖爬蟲或 feedparser 的預設 User-Agent

**解決方案**:

修改 `src/tools/fetcher.py` 添加 User-Agent:

```python
# src/tools/fetcher.py

import feedparser
import requests

def fetch_rss_feed(feed_url: str) -> Dict[str, Any]:
    try:
        # 使用 requests 先取得內容（帶自訂 User-Agent）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()

        # 再用 feedparser 解析
        feed = feedparser.parse(response.content)

        # ... 繼續處理
    except Exception as e:
        # ...
```

---

## 📞 支援與社群

### 獲取幫助

- **GitHub Issues**: https://github.com/your-repo/InsightCosmos/issues
- **Discord 社群**: [加入連結]
- **Email**: your-email@example.com

### 貢獻

歡迎提交 Pull Request！請參考 `CONTRIBUTING.md`

### 授權

MIT License - 詳見 `LICENSE` 檔案

---

**最後更新**: 2025-11-25
**維護者**: Ray 張瑞涵
**版本**: 1.0
