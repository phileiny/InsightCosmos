# InsightCosmos API Reference

> **版本**: 1.0.0
> **更新日期**: 2025-11-25
> **階段**: Phase 1 完成

---

## 目錄

1. [Agents](#agents)
   - [ScoutAgent](#scoutagent)
   - [AnalystAgent](#analystagent)
   - [CuratorDailyAgent](#curatordailyagent)
   - [CuratorWeeklyAgent](#curatorweeklyagent)
2. [Tools](#tools)
   - [RSSFetcher](#rssfetcher)
   - [GoogleSearchGroundingTool](#googlesearchgroundingtool)
   - [ContentExtractor](#contentextractor)
   - [DigestFormatter](#digestformatter)
   - [EmailSender](#emailsender)
   - [VectorClusteringTool](#vectorclusteringtool)
   - [TrendAnalysisTool](#trendanalysistool)
3. [Memory](#memory)
   - [Database](#database)
   - [ArticleStore](#articlestore)
   - [EmbeddingStore](#embeddingstore)
4. [Orchestrator](#orchestrator)
   - [DailyPipelineOrchestrator](#dailypipelineorchestrator)
   - [WeeklyPipelineOrchestrator](#weeklypipelineorchestrator)
5. [Utils](#utils)
   - [Config](#config)
   - [Logger](#logger)

---

## Agents

### ScoutAgent

**模組**: `src.agents.scout_agent`

Scout Agent 負責從 RSS 來源和 Google Search 收集文章。

#### create_scout_agent()

```python
def create_scout_agent(
    model: str = "gemini-2.5-flash",
    user_interests: str = "AI, Robotics, Multi-Agent Systems",
    prompt_path: Optional[Path] = None
) -> LlmAgent
```

創建 Scout Agent 實例。

**參數**:
- `model`: Gemini 模型名稱（預設: "gemini-2.5-flash"）
- `user_interests`: 用戶興趣列表（用於搜尋關鍵字）
- `prompt_path`: Prompt 模板路徑（可選）

**返回**: `LlmAgent` 實例

**範例**:
```python
agent = create_scout_agent(
    user_interests="AI, Robotics, LLM"
)
```

#### ScoutAgentRunner

```python
class ScoutAgentRunner:
    def __init__(
        self,
        agent: LlmAgent,
        rss_fetcher: Optional[RSSFetcher] = None,
        search_tool: Optional[GoogleSearchGroundingTool] = None,
        logger: Optional[Logger] = None
    )
```

Scout Agent 運行器，協調 RSS 抓取和搜尋。

**方法**:

##### collect_articles()

```python
def collect_articles(
    rss_feeds: Optional[List[str]] = None,
    search_queries: Optional[List[str]] = None,
    max_articles: int = 50
) -> Dict[str, Any]
```

收集文章。

**返回**:
```python
{
    "status": "success" | "error",
    "articles": List[Dict],
    "sources": {
        "rss_count": int,
        "search_count": int
    },
    "errors": List[Dict]
}
```

---

### AnalystAgent

**模組**: `src.agents.analyst_agent`

Analyst Agent 負責分析文章內容、提取洞察、評估優先度。

#### create_analyst_agent()

```python
def create_analyst_agent(
    model: str = "gemini-2.5-flash",
    user_name: str = "Ray",
    user_interests: str = "AI, Robotics, Multi-Agent Systems",
    prompt_path: Optional[Path] = None
) -> LlmAgent
```

創建 Analyst Agent 實例。

#### AnalystAgentRunner

```python
class AnalystAgentRunner:
    def __init__(
        self,
        agent: LlmAgent,
        article_store: ArticleStore,
        embedding_store: EmbeddingStore,
        logger: Optional[Logger] = None,
        config: Optional[Config] = None
    )
```

**方法**:

##### analyze_article()

```python
async def analyze_article(
    self,
    article_id: int,
    skip_if_analyzed: bool = True
) -> Dict[str, Any]
```

分析單篇文章。

**返回**:
```python
{
    "status": "success" | "error" | "skipped",
    "article_id": int,
    "analysis": {
        "summary": str,
        "key_insights": List[str],
        "tech_stack": List[str],
        "category": str,
        "trends": List[str],
        "relevance_score": float,  # 0-1
        "priority_score": float,   # 0-1
        "reasoning": str
    },
    "embedding_id": int
}
```

##### analyze_batch()

```python
async def analyze_batch(
    self,
    article_ids: List[int],
    concurrency: int = 3
) -> Dict[str, Any]
```

批量分析文章。

---

### CuratorDailyAgent

**模組**: `src.agents.curator_daily`

Daily Curator Agent 負責生成每日摘要報告。

#### generate_daily_digest()

```python
def generate_daily_digest(
    config: Config,
    recipient_email: str,
    max_articles: int = 10,
    dry_run: bool = False
) -> Dict[str, Any]
```

生成並發送每日摘要。

**返回**:
```python
{
    "status": "success" | "error",
    "subject": str,
    "recipients": List[str],
    "article_count": int,
    "html_body": str,  # if dry_run
    "text_body": str   # if dry_run
}
```

---

### CuratorWeeklyAgent

**模組**: `src.agents.curator_weekly`

Weekly Curator Agent 負責生成週報，包含趨勢分析。

#### generate_weekly_report()

```python
def generate_weekly_report(
    config: Config,
    week_start: date,
    week_end: date,
    recipient_email: str,
    dry_run: bool = False
) -> Dict[str, Any]
```

生成並發送週報。

**返回**:
```python
{
    "status": "success" | "error",
    "subject": str,
    "recipients": List[str],
    "statistics": {
        "total_articles": int,
        "clusters": int,
        "hot_trends": int,
        "emerging_topics": int
    }
}
```

---

## Tools

### RSSFetcher

**模組**: `src.tools.fetcher`

```python
class RSSFetcher:
    def __init__(
        self,
        timeout: int = 30,
        user_agent: str = "InsightCosmos/1.0",
        logger: Optional[Logger] = None
    )
```

**方法**:

##### fetch_single_feed()

```python
def fetch_single_feed(
    self,
    feed_url: str,
    max_articles: Optional[int] = None
) -> Dict[str, Any]
```

**返回**:
```python
{
    "status": "success" | "error",
    "feed_url": str,
    "feed_title": str,
    "articles": List[Dict],
    "fetched_at": datetime
}
```

##### fetch_rss_feeds()

```python
def fetch_rss_feeds(
    self,
    feed_urls: List[str],
    max_articles_per_feed: Optional[int] = None
) -> Dict[str, Any]
```

批量抓取多個 RSS feed。

---

### GoogleSearchGroundingTool

**模組**: `src.tools.google_search_grounding_v2`

使用 Gemini Search Grounding 進行網路搜尋。

```python
class GoogleSearchGroundingTool:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        logger: Optional[Logger] = None
    )
```

**方法**:

##### search_articles()

```python
def search_articles(
    self,
    query: str,
    num_results: int = 10
) -> Dict[str, Any]
```

使用 Gemini Search Grounding 搜尋文章。

**返回**:
```python
{
    "status": "success" | "error",
    "query": str,
    "articles": List[Dict],
    "grounding_metadata": Dict
}
```

---

### ContentExtractor

**模組**: `src.tools.content_extractor`

```python
def extract_content(
    url: str,
    timeout: int = 10
) -> Dict[str, Any]
```

從 URL 提取文章內容。

**返回**:
```python
{
    "status": "success" | "error",
    "url": str,
    "content": str,
    "title": str,
    "author": str,
    "published_date": str
}
```

---

### DigestFormatter

**模組**: `src.tools.digest_formatter`

```python
class DigestFormatter:
    def format_daily_digest(
        self,
        articles: List[Dict],
        user_name: str,
        date: date
    ) -> Tuple[str, str]
```

格式化每日摘要為 HTML 和純文字。

**返回**: `(html_body, text_body)`

```python
    def format_weekly_report(
        self,
        report_data: Dict,
        user_name: str,
        week_start: date,
        week_end: date
    ) -> Tuple[str, str]
```

格式化週報為 HTML 和純文字。

---

### EmailSender

**模組**: `src.tools.email_sender`

```python
class EmailSender:
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        use_tls: bool = True
    )

    def send_email(
        self,
        sender: str,
        password: str,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: str
    ) -> Dict[str, Any]
```

發送電子郵件。

---

### VectorClusteringTool

**模組**: `src.tools.vector_clustering`

```python
class VectorClusteringTool:
    def cluster_articles(
        self,
        articles: List[Dict],
        embeddings: List[List[float]],
        method: str = "kmeans",
        n_clusters: int = 5
    ) -> Dict[str, Any]
```

對文章進行向量聚類。

**支援方法**: `kmeans`, `dbscan`

---

### TrendAnalysisTool

**模組**: `src.tools.trend_analysis`

```python
class TrendAnalysisTool:
    def analyze_trends(
        self,
        clusters: List[Dict],
        articles: List[Dict]
    ) -> Dict[str, Any]
```

分析趨勢，識別熱門話題和新興主題。

**返回**:
```python
{
    "hot_trends": List[Dict],
    "emerging_topics": List[Dict],
    "trend_summary": str
}
```

---

## Memory

### Database

**模組**: `src.memory.database`

```python
class Database:
    @classmethod
    def from_config(cls, config: Config) -> "Database"

    def init_db(self) -> None
    def close(self) -> None
    def get_session(self) -> Session
```

SQLite 資料庫管理器。

---

### ArticleStore

**模組**: `src.memory.article_store`

```python
class ArticleStore:
    def __init__(self, database: Database)

    # CRUD 操作
    def store_article(self, article: Dict) -> int
    def get_by_id(self, article_id: int) -> Optional[Dict]
    def get_by_url(self, url: str) -> Optional[Dict]
    def get_by_status(self, status: str) -> List[Dict]

    # 更新操作
    def update_status(self, article_id: int, status: str) -> bool
    def update_analysis(self, article_id: int, analysis: Dict) -> bool

    # 查詢操作
    def get_top_priority(self, limit: int = 10, days: int = 1) -> List[Dict]
    def get_by_date_range(self, start: date, end: date) -> List[Dict]
    def count_by_status(self) -> Dict[str, int]
```

文章存儲管理。

---

### EmbeddingStore

**模組**: `src.memory.embedding_store`

```python
class EmbeddingStore:
    def __init__(self, database: Database)

    def store(self, article_id: int, embedding: List[float]) -> int
    def get(self, article_id: int) -> Optional[List[float]]
    def delete(self, article_id: int) -> bool
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Dict]
```

向量嵌入存儲管理。

---

## Orchestrator

### DailyPipelineOrchestrator

**模組**: `src.orchestrator.daily_runner`

```python
class DailyPipelineOrchestrator:
    def __init__(self, config: Config)

    def run(self, dry_run: bool = False) -> Dict[str, Any]
    def get_summary(self) -> Dict[str, Any]
```

每日流程編排器。

**執行階段**:
1. Phase 1: Scout（收集文章）
2. Phase 2: Analyst（分析文章）
3. Phase 3: Curator（生成報告）

**CLI 使用**:
```bash
python -m src.orchestrator.daily_runner --dry-run --verbose
```

---

### WeeklyPipelineOrchestrator

**模組**: `src.orchestrator.weekly_runner`

```python
class WeeklyPipelineOrchestrator:
    def __init__(self, config: Config)

    def run(
        self,
        week_start: Optional[date] = None,
        week_end: Optional[date] = None,
        recipients: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]
```

每週流程編排器。

**CLI 使用**:
```bash
python -m src.orchestrator.weekly_runner \
    --week-start 2025-11-18 \
    --week-end 2025-11-24 \
    --dry-run
```

---

## Utils

### Config

**模組**: `src.utils.config`

```python
@dataclass
class Config:
    google_api_key: str
    email_account: str
    email_password: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    database_path: str = "data/insights.db"
    user_name: str = "Ray"
    user_interests: str = "AI,Robotics,Multi-Agent Systems"
    log_level: str = "INFO"

    @classmethod
    def load(cls, env_path: str = ".env") -> "Config"

    @classmethod
    def from_env(cls, env_path: str = ".env") -> "Config"

    def validate(self) -> bool
    def get_interests_list(self) -> List[str]
```

配置管理器。

---

### Logger

**模組**: `src.utils.logger`

```python
class Logger:
    @staticmethod
    def get_logger(
        name: str,
        log_level: str = "INFO",
        log_dir: Optional[str] = None
    ) -> logging.Logger

    @staticmethod
    def set_level(logger: logging.Logger, level: str) -> None

    @staticmethod
    def clear_cache() -> None
```

日誌管理器。

---

## 錯誤處理

所有 API 方法返回標準化的錯誤格式：

```python
{
    "status": "error",
    "error_type": str,      # 錯誤類型
    "error_message": str,   # 錯誤描述
    "suggestion": str       # 修復建議（可選）
}
```

---

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0.0 | 2025-11-25 | Phase 1 初始版本 |

---

**維護者**: Ray 張瑞涵
