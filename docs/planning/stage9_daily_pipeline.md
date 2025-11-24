# Stage 9: Daily Pipeline 集成 - 規劃文件

> **階段**: Phase 1 - Stage 9/12
> **目標**: 串聯 Scout → Analyst → Curator Daily 完整日報流程
> **預計時間**: 1 天
> **創建日期**: 2025-11-24
> **負責人**: Ray 張瑞涵

---

## 📋 目錄

1. [目標說明](#目標說明)
2. [系統架構](#系統架構)
3. [Daily Orchestrator 設計](#daily-orchestrator-設計)
4. [錯誤處理與重試機制](#錯誤處理與重試機制)
5. [日誌與監控](#日誌與監控)
6. [實作計劃](#實作計劃)
7. [測試策略](#測試策略)
8. [驗收標準](#驗收標準)
9. [風險與對策](#風險與對策)

---

## 🎯 目標說明

### 核心目標

實現 **Daily Pipeline Orchestrator**，將前面階段實現的三個核心模組串聯成完整的自動化日報流程：

```
Scout Agent → Analyst Agent → Curator Agent → Email Delivery
```

### 具體功能

1. **流程編排**
   - 順序執行三個 Agent
   - 數據在各階段間正確傳遞
   - 支援手動觸發與定時執行

2. **錯誤處理**
   - 各階段錯誤捕獲與記錄
   - 關鍵步驟重試機制
   - 優雅降級策略

3. **日誌與監控**
   - 完整的執行日誌
   - 性能指標追蹤
   - 執行結果摘要

4. **配置管理**
   - 支援環境變數配置
   - 支援命令列參數
   - 靈活的執行選項

### 預期效果

- ✅ **一鍵執行** - 運行 `python orchestrator/daily_runner.py` 即可完成整個流程
- ✅ **穩定可靠** - 能處理常見錯誤，提供重試機制
- ✅ **可觀測** - 完整日誌追蹤每個步驟
- ✅ **質量保證** - 最終產出高品質日報 Email

---

## 🏗️ 系統架構

### 完整流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│                     Daily Pipeline Orchestrator                 │
│                     (daily_runner.py)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1: Information Collection               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Scout Agent                                                │  │
│  │  - fetch_rss() → 20 篇文章                                 │  │
│  │  - search_articles() → 10 篇文章                          │  │
│  │  - 去重 → 約 25-30 篇原始文章                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  存儲到 ArticleStore (status='collected')                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 2: Content Analysis                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Analyst Agent                                              │  │
│  │  for each article:                                         │  │
│  │    - extract_content() → 完整內容                          │  │
│  │    - analyze_article() → LLM 分析                          │  │
│  │    - generate_embedding() → 向量                           │  │
│  │    - 存儲分析結果與 Embedding                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  更新 ArticleStore (status='analyzed', priority_score, ...)      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 3: Report Generation                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Curator Daily Agent                                        │  │
│  │  - get_top_priority() → Top 5-10 篇文章                    │  │
│  │  - generate_digest() → LLM 生成報告                        │  │
│  │  - format_html() + format_text() → 格式化                  │  │
│  │  - send_email() → SMTP 發送                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  Email 成功發送 ✅                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 數據流

```python
# Phase 1: Scout Output
[
    {"title": "...", "url": "...", "source": "RSS", ...},
    # ... 25-30 篇
]
    ↓ 存儲到 DB (status='collected')

# Phase 2: Analyst Output
# ArticleStore 更新：
{
    "status": "analyzed",
    "summary": "...",
    "key_insights": [...],
    "priority_score": 0.85,
    "priority_reasoning": "...",
    ...
}
    ↓ EmbeddingStore 存儲向量

# Phase 3: Curator Output
{
    "subject": "InsightCosmos Daily Digest - 2025-11-24",
    "html_body": "<!DOCTYPE html>...",
    "text_body": "Today's Top Insights...",
    "recipients": ["ray@example.com"]
}
    ↓ SMTP 發送 Email
```

---

## 🎨 Daily Orchestrator 設計

### 類設計

```python
class DailyPipelineOrchestrator:
    """
    日報流程編排器

    負責串聯 Scout → Analyst → Curator 完整流程，
    提供錯誤處理、重試、日誌等功能。

    Attributes:
        config (Config): 配置對象
        db (Database): 資料庫連接
        article_store (ArticleStore): 文章存儲
        embedding_store (EmbeddingStore): 向量存儲
        logger (Logger): 日誌記錄器
        stats (dict): 執行統計
    """

    def __init__(self, config: Config):
        """初始化編排器"""
        self.config = config
        self.db = Database.from_config(config)
        self.db.init_db()

        self.article_store = ArticleStore(self.db)
        self.embedding_store = EmbeddingStore(self.db)

        self.logger = setup_logger("DailyPipeline")

        # 執行統計
        self.stats = {
            "start_time": None,
            "end_time": None,
            "phase1_collected": 0,
            "phase2_analyzed": 0,
            "phase3_sent": False,
            "errors": []
        }

    def run(self, dry_run: bool = False) -> dict:
        """
        執行完整的日報流程

        Args:
            dry_run: 是否為測試模式（不發送郵件）

        Returns:
            dict: 執行結果摘要
            {
                "success": bool,
                "stats": dict,
                "errors": list
            }
        """
        pass

    def _run_phase1_scout(self) -> List[dict]:
        """Phase 1: 收集文章"""
        pass

    def _run_phase2_analyst(self, articles: List[dict]) -> int:
        """Phase 2: 分析文章"""
        pass

    def _run_phase3_curator(self, dry_run: bool) -> bool:
        """Phase 3: 生成與發送報告"""
        pass

    def _handle_error(self, phase: str, error: Exception):
        """錯誤處理"""
        pass

    def get_summary(self) -> dict:
        """獲取執行摘要"""
        pass
```

### 方法詳細設計

#### 1. `run()` - 主流程

```python
def run(self, dry_run: bool = False) -> dict:
    """
    執行完整的日報流程

    流程：
    1. Phase 1: Scout Agent 收集文章
    2. Phase 2: Analyst Agent 分析文章
    3. Phase 3: Curator Agent 生成報告並發送

    Args:
        dry_run: 是否為測試模式（不發送郵件）

    Returns:
        dict: {
            "success": bool,
            "stats": {
                "start_time": str,
                "end_time": str,
                "duration_seconds": float,
                "phase1_collected": int,
                "phase2_analyzed": int,
                "phase3_sent": bool
            },
            "errors": list
        }
    """
    self.stats["start_time"] = datetime.now()
    self.logger.info("=" * 60)
    self.logger.info("Daily Pipeline Started")
    self.logger.info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    self.logger.info("=" * 60)

    try:
        # Phase 1: Scout
        self.logger.info("\n[Phase 1/3] Starting Scout Agent...")
        articles = self._run_phase1_scout()
        self.stats["phase1_collected"] = len(articles)
        self.logger.info(f"✓ Phase 1 Complete: Collected {len(articles)} articles")

        if len(articles) == 0:
            self.logger.warning("No articles collected. Aborting pipeline.")
            return self.get_summary()

        # Phase 2: Analyst
        self.logger.info("\n[Phase 2/3] Starting Analyst Agent...")
        analyzed_count = self._run_phase2_analyst(articles)
        self.stats["phase2_analyzed"] = analyzed_count
        self.logger.info(f"✓ Phase 2 Complete: Analyzed {analyzed_count} articles")

        if analyzed_count == 0:
            self.logger.warning("No articles analyzed. Aborting pipeline.")
            return self.get_summary()

        # Phase 3: Curator
        self.logger.info("\n[Phase 3/3] Starting Curator Agent...")
        sent = self._run_phase3_curator(dry_run)
        self.stats["phase3_sent"] = sent

        if sent:
            self.logger.info("✓ Phase 3 Complete: Email sent successfully")
        else:
            self.logger.warning("✗ Phase 3 Failed: Email not sent")

        self.stats["end_time"] = datetime.now()
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Daily Pipeline Completed")
        self.logger.info("=" * 60)

        return self.get_summary()

    except Exception as e:
        self.logger.error(f"Pipeline failed with unexpected error: {e}")
        self._handle_error("pipeline", e)
        self.stats["end_time"] = datetime.now()
        return self.get_summary()
```

#### 2. `_run_phase1_scout()` - Scout 階段

```python
def _run_phase1_scout(self) -> List[dict]:
    """
    Phase 1: 使用 Scout Agent 收集文章

    Returns:
        List[dict]: 收集到的文章列表

    Raises:
        Exception: 如果收集過程失敗
    """
    from src.agents.scout_agent import collect_articles

    try:
        # RSS 源列表（從配置或硬編碼）
        rss_feeds = [
            "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "https://www.artificialintelligence-news.com/feed/",
            "https://www.robotics.org/blog-rss.cfm"
        ]

        # Google Search 關鍵字
        search_queries = [
            "AI breakthroughs",
            "robotics latest news",
            "multi-agent systems"
        ]

        # 調用 Scout Agent
        result = collect_articles(
            rss_feeds=rss_feeds,
            search_queries=search_queries,
            max_articles=30
        )

        if result["status"] != "success":
            raise Exception(f"Scout failed: {result.get('error_message')}")

        articles = result["articles"]

        # 存儲到 ArticleStore
        for article in articles:
            self.article_store.create_article(
                url=article["url"],
                title=article["title"],
                source_type=article.get("source_type", "rss"),
                source_name=article.get("source_name", "Unknown"),
                published_at=article.get("published_at"),
                raw_content=article.get("content", "")
            )

        return articles

    except Exception as e:
        self.logger.error(f"Phase 1 (Scout) failed: {e}")
        self._handle_error("phase1_scout", e)
        raise
```

#### 3. `_run_phase2_analyst()` - Analyst 階段

```python
def _run_phase2_analyst(self, articles: List[dict]) -> int:
    """
    Phase 2: 使用 Analyst Agent 分析文章

    Args:
        articles: Scout 收集的文章列表

    Returns:
        int: 成功分析的文章數量
    """
    from src.agents.analyst_agent import AnalystAgentRunner
    from src.tools.content_extractor import extract_content

    runner = AnalystAgentRunner(self.config)
    analyzed_count = 0

    # 獲取 'collected' 狀態的文章
    pending_articles = self.article_store.get_by_status("collected")

    for article_dict in pending_articles:
        article_id = article_dict["id"]
        url = article_dict["url"]

        try:
            # 1. 提取完整內容
            self.logger.info(f"  Extracting content: {article_dict['title'][:50]}...")
            content_result = extract_content(url)

            if content_result["status"] != "success":
                self.logger.warning(f"    Content extraction failed: {url}")
                continue

            full_content = content_result["content"]

            # 2. 分析文章
            self.logger.info(f"  Analyzing article...")
            analysis_result = runner.analyze_article(
                article_id=article_id,
                url=url,
                title=article_dict["title"],
                content=full_content
            )

            if analysis_result["status"] == "success":
                analyzed_count += 1
                self.logger.info(f"    ✓ Analysis complete (priority: {analysis_result['priority_score']:.2f})")
            else:
                self.logger.warning(f"    ✗ Analysis failed: {analysis_result.get('error_message')}")

        except Exception as e:
            self.logger.error(f"  Error analyzing article {article_id}: {e}")
            self._handle_error(f"phase2_analyst_article_{article_id}", e)
            continue

    return analyzed_count
```

#### 4. `_run_phase3_curator()` - Curator 階段

```python
def _run_phase3_curator(self, dry_run: bool) -> bool:
    """
    Phase 3: 使用 Curator Agent 生成報告並發送

    Args:
        dry_run: 是否為測試模式（不發送郵件）

    Returns:
        bool: 是否成功發送
    """
    from src.agents.curator_daily import generate_daily_digest

    try:
        # 調用 Curator Agent
        result = generate_daily_digest(
            config=self.config,
            dry_run=dry_run
        )

        if result["status"] == "success":
            if dry_run:
                self.logger.info("  DRY RUN: Email not sent (dry_run=True)")
                self.logger.info(f"  Subject: {result['subject']}")
                self.logger.info(f"  Recipients: {result['recipients']}")
            else:
                self.logger.info(f"  Email sent to: {result['recipients']}")

            return True
        else:
            self.logger.error(f"  Curator failed: {result.get('error_message')}")
            return False

    except Exception as e:
        self.logger.error(f"Phase 3 (Curator) failed: {e}")
        self._handle_error("phase3_curator", e)
        return False
```

#### 5. `_handle_error()` - 錯誤處理

```python
def _handle_error(self, phase: str, error: Exception):
    """
    記錄錯誤信息

    Args:
        phase: 發生錯誤的階段名稱
        error: 異常對象
    """
    error_info = {
        "phase": phase,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }
    self.stats["errors"].append(error_info)
    self.logger.error(f"Error in {phase}: {error}")
```

#### 6. `get_summary()` - 執行摘要

```python
def get_summary(self) -> dict:
    """
    獲取執行摘要

    Returns:
        dict: 執行結果摘要
    """
    success = (
        self.stats["phase1_collected"] > 0 and
        self.stats["phase2_analyzed"] > 0 and
        self.stats["phase3_sent"] and
        len(self.stats["errors"]) == 0
    )

    duration = None
    if self.stats["start_time"] and self.stats["end_time"]:
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

    return {
        "success": success,
        "stats": {
            "start_time": self.stats["start_time"].isoformat() if self.stats["start_time"] else None,
            "end_time": self.stats["end_time"].isoformat() if self.stats["end_time"] else None,
            "duration_seconds": duration,
            "phase1_collected": self.stats["phase1_collected"],
            "phase2_analyzed": self.stats["phase2_analyzed"],
            "phase3_sent": self.stats["phase3_sent"]
        },
        "errors": self.stats["errors"]
    }
```

---

## 🔧 錯誤處理與重試機制

### 錯誤分類

1. **可重試錯誤** (Retriable Errors)
   - 網絡超時
   - API 臨時不可用 (503)
   - Rate Limit 錯誤 (429)

2. **不可重試錯誤** (Non-Retriable Errors)
   - API Key 無效 (401)
   - 資源不存在 (404)
   - 參數錯誤 (400)

3. **警告級錯誤** (Warnings)
   - 單篇文章提取失敗（繼續處理其他文章）
   - 單篇文章分析失敗（繼續處理其他文章）

### 重試策略

```python
def retry_with_backoff(func, max_retries=3, backoff_factor=2):
    """
    指數退避重試

    Args:
        func: 要執行的函數
        max_retries: 最大重試次數
        backoff_factor: 退避因子（每次重試延遲倍數）

    Returns:
        函數執行結果
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            # 判斷是否可重試
            if not is_retriable_error(e):
                raise

            wait_time = backoff_factor ** attempt
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
```

### 降級策略

1. **Phase 1 失敗**
   - 如果 RSS 全部失敗，但 Google Search 成功 → 繼續
   - 如果兩者都失敗 → 中止流程，發送錯誤通知郵件

2. **Phase 2 失敗**
   - 如果部分文章分析失敗 → 繼續處理其他文章
   - 如果所有文章都失敗 → 中止流程，發送錯誤通知郵件

3. **Phase 3 失敗**
   - 如果 Email 發送失敗 → 重試 3 次
   - 如果仍然失敗 → 將報告存儲到本地文件

---

## 📊 日誌與監控

### 日誌級別

```python
# INFO - 正常流程信息
logger.info("Phase 1: Starting Scout Agent...")
logger.info("✓ Phase 1 Complete: Collected 28 articles")

# WARNING - 警告信息（不影響整體流程）
logger.warning("Article extraction failed for URL: https://...")
logger.warning("No high-priority articles found, using all analyzed articles")

# ERROR - 錯誤信息（可能影響流程）
logger.error("Phase 2 failed: API key invalid")
logger.error("Email sending failed after 3 retries")

# DEBUG - 詳細調試信息（開發階段使用）
logger.debug(f"Article analysis result: {analysis_result}")
logger.debug(f"Embedding vector shape: {embedding.shape}")
```

### 日誌格式

```
2025-11-24 09:00:00 [INFO] DailyPipeline - ============================================================
2025-11-24 09:00:00 [INFO] DailyPipeline - Daily Pipeline Started
2025-11-24 09:00:00 [INFO] DailyPipeline - Mode: PRODUCTION
2025-11-24 09:00:00 [INFO] DailyPipeline - ============================================================
2025-11-24 09:00:01 [INFO] DailyPipeline -
[Phase 1/3] Starting Scout Agent...
2025-11-24 09:00:15 [INFO] DailyPipeline - ✓ Phase 1 Complete: Collected 28 articles
2025-11-24 09:00:15 [INFO] DailyPipeline -
[Phase 2/3] Starting Analyst Agent...
2025-11-24 09:00:16 [INFO] DailyPipeline -   Extracting content: Latest AI breakthrough in natural language...
2025-11-24 09:00:18 [INFO] DailyPipeline -   Analyzing article...
2025-11-24 09:00:22 [INFO] DailyPipeline -     ✓ Analysis complete (priority: 0.87)
2025-11-24 09:02:30 [INFO] DailyPipeline - ✓ Phase 2 Complete: Analyzed 25 articles
2025-11-24 09:02:30 [INFO] DailyPipeline -
[Phase 3/3] Starting Curator Agent...
2025-11-24 09:02:45 [INFO] DailyPipeline -   Email sent to: ['ray@example.com']
2025-11-24 09:02:45 [INFO] DailyPipeline - ✓ Phase 3 Complete: Email sent successfully
2025-11-24 09:02:45 [INFO] DailyPipeline -
============================================================
2025-11-24 09:02:45 [INFO] DailyPipeline - Daily Pipeline Completed
2025-11-24 09:02:45 [INFO] DailyPipeline - Pipeline Duration: 165.3 seconds
2025-11-24 09:02:45 [INFO] DailyPipeline - Articles Collected: 28
2025-11-24 09:02:45 [INFO] DailyPipeline - Articles Analyzed: 25
2025-11-24 09:02:45 [INFO] DailyPipeline - Email Sent: True
2025-11-24 09:02:45 [INFO] DailyPipeline - Errors: 0
2025-11-24 09:02:45 [INFO] DailyPipeline - ============================================================
```

### 性能指標

追蹤以下指標：

1. **總執行時間** - 從開始到結束的總時長
2. **各階段耗時**
   - Phase 1 (Scout): 約 10-20 秒
   - Phase 2 (Analyst): 約 60-120 秒（取決於文章數量）
   - Phase 3 (Curator): 約 10-20 秒
3. **文章數量統計**
   - 收集數量
   - 成功分析數量
   - 高優先度數量
4. **錯誤率** - 各階段失敗率

---

## 🛠️ 實作計劃

### 文件結構

```
src/
└─ orchestrator/
    ├─ __init__.py
    ├─ daily_runner.py          # DailyPipelineOrchestrator 類
    └─ utils.py                 # 工具函數（重試、錯誤處理）
```

### 開發步驟

#### Step 1: 創建基礎結構 (30 分鐘)

1. 創建 `src/orchestrator/` 目錄
2. 創建 `DailyPipelineOrchestrator` 類骨架
3. 實現 `__init__()` 方法
4. 實現 `get_summary()` 方法

#### Step 2: 實現三個階段 (90 分鐘)

1. 實現 `_run_phase1_scout()` - 調用 Scout Agent
2. 實現 `_run_phase2_analyst()` - 調用 Analyst Agent
3. 實現 `_run_phase3_curator()` - 調用 Curator Agent
4. 實現錯誤處理 `_handle_error()`

#### Step 3: 實現主流程 (45 分鐘)

1. 實現 `run()` 方法
2. 添加完整的日誌輸出
3. 添加性能統計
4. 實現 dry_run 模式

#### Step 4: 添加重試機制 (30 分鐘)

1. 創建 `orchestrator/utils.py`
2. 實現 `retry_with_backoff()` 函數
3. 實現 `is_retriable_error()` 函數
4. 在關鍵操作中應用重試

#### Step 5: 創建命令列入口 (30 分鐘)

1. 添加 `main()` 函數
2. 添加命令列參數解析（argparse）
3. 支援 `--dry-run`, `--verbose` 等選項
4. 添加使用說明

---

## 🧪 測試策略

### 單元測試

**文件**: `tests/unit/test_daily_orchestrator.py`

**測試案例**:

1. `test_orchestrator_initialization()` - 初始化測試
2. `test_get_summary_empty()` - 空摘要測試
3. `test_get_summary_with_data()` - 有數據的摘要測試
4. `test_handle_error()` - 錯誤處理測試
5. `test_phase1_scout_success()` - Phase 1 成功測試（Mock）
6. `test_phase1_scout_failure()` - Phase 1 失敗測試
7. `test_phase2_analyst_partial_failure()` - Phase 2 部分失敗測試
8. `test_phase3_curator_retry()` - Phase 3 重試測試

### 整合測試

**文件**: `tests/integration/test_daily_pipeline.py`

**測試案例**:

1. `test_full_pipeline_dry_run()` - 完整流程測試（dry_run=True）
2. `test_pipeline_phase1_failure()` - Phase 1 失敗場景
3. `test_pipeline_phase2_all_fail()` - Phase 2 全部失敗場景
4. `test_pipeline_resume_from_phase2()` - 從 Phase 2 恢復測試

### 端到端測試（手動）

**測試案例**:

1. **正常流程**
   ```bash
   python -m src.orchestrator.daily_runner --dry-run
   ```
   預期：完整流程執行，不發送郵件

2. **生產模式**
   ```bash
   python -m src.orchestrator.daily_runner
   ```
   預期：完整流程執行，發送郵件到指定信箱

3. **錯誤場景**
   - 斷網測試
   - API Key 無效測試
   - 資料庫不可用測試

---

## ✅ 驗收標準

### 功能驗收

- [ ] **完整流程執行** - 能順利執行 Scout → Analyst → Curator 完整流程
- [ ] **數據正確傳遞** - 各階段數據正確存儲並傳遞到下一階段
- [ ] **錯誤處理** - 能捕獲並記錄各階段錯誤
- [ ] **重試機制** - 關鍵操作失敗後能自動重試
- [ ] **日誌完整** - 日誌能追蹤完整流程，便於調試
- [ ] **命令列介面** - 支援 `--dry-run`, `--verbose` 等選項

### 性能驗收

- [ ] **執行時間** - 完整流程在 5 分鐘內完成（30 篇文章）
- [ ] **成功率** - 正常情況下成功率 >= 95%
- [ ] **錯誤恢復** - 單篇文章失敗不影響整體流程

### 品質驗收

- [ ] **單元測試** - 通過率 100%
- [ ] **整合測試** - 通過率 >= 90%
- [ ] **代碼覆蓋率** - 核心邏輯覆蓋率 >= 85%
- [ ] **文檔完整** - 所有公開方法有 docstring

### 用戶體驗驗收

- [ ] **日誌可讀** - 日誌格式清晰，便於理解流程進度
- [ ] **錯誤友好** - 錯誤訊息提供明確的修正建議
- [ ] **執行摘要** - 執行結束後提供清晰的摘要報告

---

## ⚠️ 風險與對策

### 風險 1: API 配額超限

**風險描述**: Google Search API 或 Gemini API 配額不足

**影響**: Phase 1 或 Phase 2 無法完成

**對策**:
1. 在 Phase 1 限制 Google Search 調用次數（最多 3 次）
2. 實現配額檢查，提前預警
3. 提供降級方案（僅使用 RSS 或使用舊數據）

**優先級**: 高

---

### 風險 2: 網絡不穩定

**風險描述**: 網絡超時或斷線導致流程中斷

**影響**: 任何階段都可能失敗

**對策**:
1. 所有網絡請求實現重試機制
2. 使用指數退避策略
3. 設置合理的超時時間（30 秒）

**優先級**: 高

---

### 風險 3: 內容提取失敗率高

**風險描述**: 部分網站反爬蟲導致內容提取失敗

**影響**: Phase 2 可分析的文章數量減少

**對策**:
1. 實現 User-Agent 輪換
2. 添加隨機延遲
3. 接受部分失敗（>= 80% 成功率即可）

**優先級**: 中

---

### 風險 4: LLM 輸出格式錯誤

**風險描述**: Gemini 偶爾返回非 JSON 格式

**影響**: Phase 2 或 Phase 3 解析失敗

**對策**:
1. 已實現 Markdown 包裝的 JSON 解析
2. 實現降級解析策略
3. 記錄原始輸出便於調試

**優先級**: 中

---

### 風險 5: Email 發送失敗

**風險描述**: SMTP 連接失敗或認證失敗

**影響**: Phase 3 無法完成

**對策**:
1. 已實現重試機制（3 次）
2. 失敗時將報告存儲到本地 HTML 文件
3. 提供詳細的錯誤訊息與修正建議

**優先級**: 中

---

## 📚 參考資料

### ADK 官方文件

- [Sequential Agent](https://google.github.io/adk-docs/agents/sequential/)
- [Error Handling](https://google.github.io/adk-docs/tools/#error-handling)
- [Logging Best Practices](https://google.github.io/adk-docs/plugins/logging/)

### 專案內部文件

- `docs/planning/stage5_scout_agent.md` - Scout Agent 設計
- `docs/planning/stage7_analyst_agent.md` - Analyst Agent 設計
- `docs/planning/stage8_curator_daily.md` - Curator Agent 設計
- `CLAUDE.md` - 專案一致性指南

---

## 🎯 下一步

完成 Stage 9 後，接續：

1. **Stage 10**: Curator Weekly Agent（週報生成）
2. **Stage 11**: Weekly Pipeline 集成（週報流程）
3. **Stage 12**: 質量保證與優化（QA & Optimization）

---

**創建者**: Ray 張瑞涵
**創建日期**: 2025-11-24
**最後更新**: 2025-11-24
**狀態**: 規劃完成，待實作
