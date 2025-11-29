# InsightCosmos 使用手冊

> **版本**: 1.1.0
> **最後更新**: 2025-11-26
> **適用階段**: Phase 1 - 個人宇宙版（完整版）

[English](USER_MANUAL.md) | **繁體中文**

---

## 📚 目錄

1. [快速開始](#快速開始)
2. [日報與週報](#日報與週報)
3. [個人化配置](#個人化配置)
4. [資料管理](#資料管理)
5. [進階設定](#進階設定)
6. [部署指南](#部署指南)
7. [備份與還原](#備份與還原)
8. [常見問題](#常見問題)
9. [故障排除](#故障排除)

---

## 🚀 快速開始

### 系統需求

- Python 3.10+（建議 3.11 或 3.13）
- 至少 4GB RAM
- 穩定的網路連線
- Google Gemini API Key

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

### 環境變數配置（.env）

```bash
# Google Gemini API (必需)
# 從 https://aistudio.google.com/apikey 取得
GOOGLE_API_KEY=your_gemini_api_key

# Email 配置 (必需)
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # 使用 Gmail App Password

# SMTP 設定（可選，預設 Gmail）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true

# 資料庫（可選，預設 data/insights.db）
DATABASE_PATH=data/insights.db

# 個人配置
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems

# 日誌級別（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL=INFO
```

### Gmail App Password 設定

1. 前往 [Google 帳戶安全性設定](https://myaccount.google.com/security)
2. 啟用「兩步驟驗證」
3. 在「兩步驟驗證」頁面底部，點擊「應用程式密碼」
4. 選擇「郵件」和你的裝置
5. 生成密碼並複製到 `.env` 的 `EMAIL_PASSWORD`

---

## 📬 日報與週報

### Daily Pipeline（每日情報）

每日 Pipeline 執行三個階段：
1. **Scout Agent**: 從 RSS 和 Google Search 收集文章
2. **Analyst Agent**: 使用 LLM 分析文章、評分、提取洞察
3. **Curator Agent**: 生成並發送每日摘要郵件

#### 執行命令

```bash
# 啟用虛擬環境
source venv/bin/activate

# 生產模式（收集 + 分析 + 發送郵件）
python -m src.orchestrator.daily_runner

# 測試模式（不發送郵件，查看報告內容）
python -m src.orchestrator.daily_runner --dry-run

# 詳細日誌模式（用於調試）
python -m src.orchestrator.daily_runner --verbose

# 組合使用
python -m src.orchestrator.daily_runner --dry-run --verbose
```

#### 執行時間

| 階段 | 預估時間 |
|------|----------|
| Scout (收集) | 30-60 秒 |
| Analyst (分析) | 1-3 分鐘 |
| Curator (報告) | 10-30 秒 |
| **總計** | **2-5 分鐘** |

### Weekly Pipeline（週報趨勢）

週報 Pipeline 分析一週的文章，進行主題聚類和趨勢識別：
1. 查詢一週內已分析的高優先度文章
2. 使用向量聚類識別主題群
3. 分析熱門趨勢和新興話題
4. 使用 LLM 生成週報
5. 發送週報郵件

#### 執行命令

```bash
# 啟用虛擬環境
source venv/bin/activate

# 生產模式（分析 + 發送郵件）
python -m src.orchestrator.weekly_runner

# 測試模式（不發送郵件）
python -m src.orchestrator.weekly_runner --dry-run

# 詳細日誌模式
python -m src.orchestrator.weekly_runner --verbose

# 指定日期範圍
python -m src.orchestrator.weekly_runner --week-start 2025-11-18 --week-end 2025-11-24

# 組合使用
python -m src.orchestrator.weekly_runner --dry-run --verbose
```

#### 週報輸出內容

| 項目 | 說明 |
|------|------|
| 主題群集 | 將文章按相似度分成 3-7 個主題群 |
| 熱門趨勢 | 出現頻率高、優先度高的關鍵字 |
| 新興話題 | 低頻但高優先度的新興關鍵字 |
| 週報摘要 | LLM 生成的週度總結報告 |

#### 執行時間

| 階段 | 預估時間 |
|------|----------|
| 資料查詢 | < 1 秒 |
| 向量聚類 | 1-2 秒 |
| 趨勢分析 | < 1 秒 |
| LLM 報告 | 10-15 秒 |
| 郵件發送 | 2-3 秒 |
| **總計** | **15-20 秒** |

### 自動化排程

#### Linux/Mac (Cron)

```bash
# 編輯 crontab
crontab -e

# 每天早上 8 點執行日報
0 8 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner >> /path/to/logs/daily_$(date +\%Y\%m\%d).log 2>&1

# 每週日晚上 8 點執行週報
0 20 * * 0 cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.weekly_runner >> /path/to/logs/weekly_$(date +\%Y\%m\%d).log 2>&1
```

#### 完整範例（含日誌輪替）

```bash
# 每天早上 8 點執行日報
0 8 * * * cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python -m src.orchestrator.daily_runner >> /Users/ray/sides/InsightCosmos/logs/daily_$(date +\%Y\%m\%d).log 2>&1

# 每週日晚上 8 點執行週報
0 20 * * 0 cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python -m src.orchestrator.weekly_runner >> /Users/ray/sides/InsightCosmos/logs/weekly_$(date +\%Y\%m\%d).log 2>&1

# 每月 1 號清理 90 天前的資料
0 0 1 * * cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python scripts/cleanup_old_data.py --days 90 >> /Users/ray/sides/InsightCosmos/logs/cleanup.log 2>&1
```

#### Windows Task Scheduler

1. 開啟 Task Scheduler
2. 創建基本任務
3. 設定觸發器（每天早上 8 點）
4. 設定動作：
   - **Program**: `C:\path\to\InsightCosmos\venv\Scripts\python.exe`
   - **Arguments**: `-m src.orchestrator.daily_runner`
   - **Start in**: `C:\path\to\InsightCosmos`
5. 完成

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

```
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
        # 選項 1: Gemini 2.5 Flash (預設，快速，便宜)
        model=Gemini(model="gemini-2.5-flash"),

        # 選項 2: Gemini 2.0 Flash (穩定版)
        # model=Gemini(model="gemini-2.0-flash-exp"),

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

        # 或 Claude 3.5 Haiku (最便宜)
        # model=Anthropic(model="claude-3-5-haiku"),

        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### 模型選擇建議

| 場景 | 推薦模型 | 原因 |
|-----|---------|------|
| 成本優先 | Gemini 2.5 Flash | 最便宜，速度快 |
| 速度優先 | Gemini 2.0 Flash | 超快響應，適合即時 |
| 品質優先 | Claude 3.7 Sonnet | 推理能力強，文字品質高 |
| 平衡選擇 | GPT-4o | 速度與品質兼顧 |
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

### 1. 本地部署（自動化）

#### 方法 A: Cron Job（Linux/Mac）

```bash
# 編輯 crontab
crontab -e

# 添加定時任務（每天早上 8 點執行）
0 8 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner >> /path/to/logs/daily.log 2>&1

# 保存並退出
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
```

### 2. 部署到 Google Cloud Run

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

### 2. 還原資料庫

```bash
# 解壓縮備份
gunzip backups/insights_backup_20251126_080000.db.gz

# 覆蓋現有資料庫
cp backups/insights_backup_20251126_080000.db data/insights.db
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
result = sender.send(
    to_email=config.email_account,
    subject='InsightCosmos Test Email',
    text_body='This is a test email from InsightCosmos.'
)
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
cat logs/insightcosmos.log | grep "2025-11-26"
```

### Q3: 如何限制 API 使用成本？

1. 減少每日處理文章數量
2. 使用更便宜的模型（Gemini Flash）
3. 減少 RSS feeds 和搜索查詢數量

### Q4: 如何加快 Pipeline 執行速度？

1. 使用更快的 LLM 模型（Gemini 2.5 Flash）
2. 減少資料來源數量
3. 調整 `max_articles` 參數

### Q5: 如何處理 Rate Limit 錯誤？

在 orchestrator 中添加延遲：

```python
# src/orchestrator/daily_runner.py

import time

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

### 問題 4: RSS Feed 無法讀取

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

## 📈 效能指標

Phase 1 完整版的效能指標：

| 指標 | 目標 | 實際 | 狀態 |
|------|------|------|------|
| Daily Pipeline 執行時間 | < 5 分鐘 | 2-3 分鐘 | ✅ |
| Weekly Pipeline 執行時間 | < 2 分鐘 | ~17 秒 | ✅ |
| 單文章分析時間 | < 15 秒 | 3-5 秒 | ✅ |
| RSS 批量抓取 (10 feeds) | < 30 秒 | 10-15 秒 | ✅ |
| 測試覆蓋率 | >= 95% | 97.4% | ✅ |

---

## 📞 支援與社群

### 獲取幫助

- **GitHub Issues**: https://github.com/your-repo/InsightCosmos/issues
- **文件目錄**: `docs/` 資料夾包含完整技術文件
- **API 參考**: `docs/implementation/api_reference.md`

### 相關文件

- [README.md](README.md) - Project description and quick start (English)
- [README_zh_TW.md](README_zh_TW.md) - 專案說明與快速開始（繁體中文）
- [USER_MANUAL.md](USER_MANUAL.md) - Complete User Manual (English)
- [CLAUDE.md](CLAUDE.md) - Claude Code 專案指南
- [PROGRESS.md](PROGRESS.md) - 開發進度追蹤
- `docs/planning/` - 規劃文件
- `docs/implementation/` - 實作文件
- `docs/validation/` - 測試與驗證報告
- `docs/optimization/` - 效能優化紀錄

### 授權

MIT License - 詳見 `LICENSE` 檔案

---

**最後更新**: 2025-11-26
**維護者**: Ray 張瑞涵
**版本**: 1.1.0 (Phase 1 完整版)
