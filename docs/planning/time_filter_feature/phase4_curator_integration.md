# Phase 4: 修改 CuratorDailyRunner 整合時間過濾

> **功能**: 日報時間過濾
> **階段**: Phase 4 of 5
> **狀態**: 完成
> **完成日期**: 2025-12-05

---

## 1. Planning (規劃)

### 1.1 目標

修改 `CuratorDailyRunner`，整合時間過濾邏輯：
1. 查詢上次日報的結束時間
2. 使用時間範圍篩選文章
3. 儲存本次日報記錄

### 1.2 需求分析

**核心邏輯:**
```
首次執行: period_start = now - 30 days (一個月)
後續執行: period_start = 上次日報的 period_end
```

**流程變化:**

```
修改前:
  get_top_priority(limit=30, status='analyzed')
      ↓
  所有已分析文章

修改後:
  get_last_daily_report()
      ↓
  確定 period_start (首次: -30天, 後續: 上次 period_end)
      ↓
  get_top_priority(limit=30, status='analyzed',
                   fetched_after=period_start,
                   fetched_before=now)
      ↓
  時間範圍內的文章
      ↓
  生成日報
      ↓
  create_daily_report(period_start, period_end)
```

### 1.3 設計規格

**修改方法:**

| 方法 | 修改內容 |
|------|----------|
| `__init__()` | 初始化 ReportStore |
| `generate_and_send_digest()` | 加入時間範圍邏輯和日報儲存 |
| `fetch_analyzed_articles()` | 加入時間範圍參數 |

**新增常數:**

```python
DEFAULT_FIRST_RUN_DAYS = 30  # 首次執行預設取 30 天內的文章
```

### 1.4 影響範圍

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `src/agents/curator_daily.py` | 修改 | 整合時間過濾邏輯 |

---

## 2. Implementation (實作)

### 2.1 修改 curator_daily.py

**檔案**: `src/agents/curator_daily.py`

#### 2.1.1 修改 __init__()

```python
# 新增常數 (檔案開頭)
DEFAULT_FIRST_RUN_DAYS = 30  # 首次執行預設取 30 天內的文章


class CuratorDailyRunner:
    """
    Curator Daily Agent Runner

    Orchestrates the daily digest generation with time-based filtering.
    """

    def __init__(
        self,
        agent: LlmAgent,
        article_store: ArticleStore,
        config: Config
    ):
        """
        Initialize CuratorDailyRunner

        Args:
            agent: Curator Daily Agent
            article_store: Article storage instance
            config: Application configuration
        """
        self.agent = agent
        self.article_store = article_store
        self.config = config
        self.logger = Logger.get_logger(__name__)

        # Initialize formatter and email sender
        self.formatter = DigestFormatter()
        self.email_sender = self._create_email_sender()

        # Initialize ADK components
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name="InsightCosmos",
            agent=self.agent,
            session_service=self.session_service
        )

        # 新增: 初始化 ReportStore
        from src.memory.report_store import ReportStore
        self.report_store = ReportStore(self.article_store.database)
```

#### 2.1.2 修改 generate_and_send_digest()

```python
def generate_and_send_digest(
    self,
    recipient_email: str,
    max_articles: int = 10,
    digest_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Generate daily digest and send via email

    Uses time-based filtering to only include articles collected since
    the last digest was generated.

    Args:
        recipient_email: Recipient email address
        max_articles: Maximum number of articles to include (default: 10)
        digest_date: Date for the digest (default: today)

    Returns:
        dict: {
            "status": "success" | "error" | "skip",
            "digest": dict (if success),
            "email_result": dict (if success),
            "error": str (if error),
            "period_start": str,
            "period_end": str
        }
    """
    try:
        # 新增: 決定時間範圍
        period_start, period_end = self._determine_time_period()

        self.logger.info(
            f"Generating digest for period: {period_start} to {period_end}"
        )

        # Step 1: Fetch analyzed articles (修改: 加入時間範圍)
        self.logger.info(f"Fetching top {max_articles} analyzed articles...")
        articles = self.fetch_analyzed_articles(
            max_articles=max_articles,
            fetched_after=period_start,
            fetched_before=period_end
        )

        if not articles:
            self.logger.warning(
                f"No new articles found between {period_start} and {period_end}"
            )
            return {
                "status": "skip",
                "message": "No new articles in the specified time range",
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            }

        self.logger.info(f"Fetched {len(articles)} articles")

        # Step 2: Generate digest
        self.logger.info("Generating daily digest...")
        digest = self.generate_digest(articles, digest_date)

        if not digest:
            self.logger.error("Failed to generate digest")
            return {
                "status": "error",
                "error": "LLM failed to generate valid digest",
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            }

        self.logger.info("Digest generated successfully")

        # Step 3: Format digest
        self.logger.info("Formatting digest for email...")
        html_body = self.formatter.format_html(digest)
        text_body = self.formatter.format_text(digest)

        # Step 4: Send email
        self.logger.info(f"Sending digest to {recipient_email}...")
        email_result = self.email_sender.send(
            to_email=recipient_email,
            subject=f"InsightCosmos Daily Digest - {digest['date']}",
            html_body=html_body,
            text_body=text_body
        )

        if email_result['status'] == 'success':
            self.logger.info("✅ Daily digest sent successfully")

            # 新增: 儲存日報記錄
            self._save_daily_report(
                report_date=digest_date or date.today(),
                period_start=period_start,
                period_end=period_end,
                articles=articles,
                digest=digest
            )

            return {
                "status": "success",
                "digest": digest,
                "email_result": email_result,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            }
        else:
            self.logger.error(f"Failed to send email: {email_result.get('error')}")
            return {
                "status": "error",
                "error": f"Email sending failed: {email_result.get('error')}",
                "digest": digest,
                "email_result": email_result,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            }

    except Exception as e:
        self.logger.error(f"Error in generate_and_send_digest: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
```

#### 2.1.3 新增 _determine_time_period()

```python
def _determine_time_period(self) -> tuple:
    """
    Determine the time period for article collection

    Returns:
        tuple: (period_start, period_end) as datetime objects

    Logic:
        - If previous report exists: start from its period_end
        - If no previous report: start from 30 days ago (first run)
    """
    period_end = datetime.utcnow()

    # 查詢上次日報
    last_report = self.report_store.get_last_daily_report()

    if last_report and last_report.get('period_end'):
        # 有上次日報 → 從上次結束時間開始
        period_end_str = last_report['period_end']
        period_start = datetime.fromisoformat(period_end_str)
        self.logger.info(f"Found last report, starting from: {period_start}")
    else:
        # 首次執行 → 預設取過去 30 天
        period_start = period_end - timedelta(days=DEFAULT_FIRST_RUN_DAYS)
        self.logger.info(
            f"No previous report found, using last {DEFAULT_FIRST_RUN_DAYS} days: "
            f"{period_start}"
        )

    return period_start, period_end
```

#### 2.1.4 新增 _save_daily_report()

```python
def _save_daily_report(
    self,
    report_date: date,
    period_start: datetime,
    period_end: datetime,
    articles: List[Dict[str, Any]],
    digest: Dict[str, Any]
) -> None:
    """
    Save daily report record to database

    Args:
        report_date: Report date
        period_start: Article collection start time
        period_end: Article collection end time
        articles: List of articles included
        digest: Generated digest content
    """
    try:
        article_ids = [a.get('id') for a in articles if a.get('id')]

        self.report_store.create_daily_report(
            report_date=report_date,
            period_start=period_start,
            period_end=period_end,
            article_count=len(articles),
            top_articles=article_ids,
            content=json.dumps(digest, ensure_ascii=False),
            sent_at=datetime.utcnow()
        )

        self.logger.info(
            f"Saved daily report: date={report_date}, "
            f"period={period_start} to {period_end}, "
            f"articles={len(articles)}"
        )

    except Exception as e:
        self.logger.error(f"Failed to save daily report: {e}")
        # 不拋出例外，避免影響已成功發送的郵件
```

#### 2.1.5 修改 fetch_analyzed_articles()

```python
def fetch_analyzed_articles(
    self,
    max_articles: int = 10,
    fetched_after: Optional[datetime] = None,
    fetched_before: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Fetch top priority analyzed articles from ArticleStore

    Args:
        max_articles: Maximum number of articles to fetch
        fetched_after: Only include articles fetched after this time (新增)
        fetched_before: Only include articles fetched before this time (新增)

    Returns:
        List[dict]: List of article dictionaries
    """
    try:
        # Fetch more articles than needed to allow for deduplication
        # 修改: 加入時間範圍參數
        articles = self.article_store.get_top_priority(
            limit=max_articles * 3,  # Fetch 3x to have buffer for dedup
            status='analyzed',
            fetched_after=fetched_after,
            fetched_before=fetched_before
        )

        # ... 現有的處理邏輯保持不變 ...
```

---

## 3. Validation (驗證)

### 3.1 驗證項目

| 項目 | 驗證方法 | 預期結果 |
|------|----------|----------|
| 首次執行 | 整合測試 | 取過去 30 天文章 |
| 後續執行 | 整合測試 | 從上次 period_end 開始 |
| 無新文章 | 單元測試 | 回傳 skip 狀態 |
| 日報儲存 | 單元測試 | 正確儲存到 daily_reports |
| 郵件發送失敗 | 單元測試 | 不儲存日報記錄 |

### 3.2 測試案例

```python
# tests/unit/test_curator_time_filter.py

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock


class TestCuratorDailyRunnerTimeFilter:

    def test_first_run_uses_30_days(self):
        """測試首次執行使用 30 天"""
        from src.agents.curator_daily import CuratorDailyRunner, DEFAULT_FIRST_RUN_DAYS

        # Mock dependencies
        mock_agent = Mock()
        mock_article_store = Mock()
        mock_config = Mock()

        # Mock ReportStore - 無歷史日報
        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(mock_agent, mock_article_store, mock_config)
            period_start, period_end = runner._determine_time_period()

            # 驗證: period_start 應為 30 天前
            expected_start = period_end - timedelta(days=DEFAULT_FIRST_RUN_DAYS)
            assert abs((period_start - expected_start).total_seconds()) < 1

    def test_subsequent_run_uses_last_period_end(self):
        """測試後續執行使用上次 period_end"""
        from src.agents.curator_daily import CuratorDailyRunner

        mock_agent = Mock()
        mock_article_store = Mock()
        mock_config = Mock()

        last_period_end = datetime(2025, 12, 4, 8, 0, 0)

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = {
                'period_end': last_period_end.isoformat()
            }
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(mock_agent, mock_article_store, mock_config)
            period_start, period_end = runner._determine_time_period()

            # 驗證: period_start 應為上次的 period_end
            assert period_start == last_period_end

    def test_no_articles_returns_skip(self):
        """測試無新文章時回傳 skip"""
        from src.agents.curator_daily import CuratorDailyRunner

        mock_agent = Mock()
        mock_article_store = Mock()
        mock_article_store.get_top_priority.return_value = []  # 無文章
        mock_config = Mock()

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(mock_agent, mock_article_store, mock_config)
            result = runner.generate_and_send_digest("test@example.com")

            assert result['status'] == 'skip'
            assert 'No new articles' in result['message']

    def test_saves_report_on_success(self):
        """測試成功發送後儲存日報記錄"""
        from src.agents.curator_daily import CuratorDailyRunner

        mock_agent = Mock()
        mock_article_store = Mock()
        mock_article_store.get_top_priority.return_value = [
            {'id': 1, 'title': 'Test', 'url': 'http://test.com', 'summary': 'Test'}
        ]
        mock_config = Mock()
        mock_config.smtp_host = 'smtp.gmail.com'
        mock_config.smtp_port = 587
        mock_config.email_account = 'test@gmail.com'
        mock_config.email_password = 'password'
        mock_config.smtp_use_tls = True

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            with patch.object(CuratorDailyRunner, 'generate_digest') as mock_digest:
                mock_digest.return_value = {
                    'date': '2025-12-05',
                    'top_articles': [],
                    'daily_insight': 'Test'
                }

                with patch.object(CuratorDailyRunner, '_create_email_sender') as mock_email:
                    mock_sender = Mock()
                    mock_sender.send.return_value = {'status': 'success'}
                    mock_email.return_value = mock_sender

                    runner = CuratorDailyRunner(mock_agent, mock_article_store, mock_config)
                    result = runner.generate_and_send_digest("test@example.com")

                    # 驗證: 應該呼叫 create_daily_report
                    assert mock_report_store.create_daily_report.called
```

### 3.3 整合測試

```bash
# 1. 首次執行 (應取 30 天內文章)
python -m src.orchestrator.daily_runner

# 2. 檢查 daily_reports 表
sqlite3 data/insights.db "SELECT * FROM daily_reports ORDER BY id DESC LIMIT 1"

# 3. 再次執行 (應只取新文章)
python -m src.orchestrator.daily_runner

# 4. 檢查是否從上次 period_end 開始
sqlite3 data/insights.db "SELECT id, report_date, period_start, period_end FROM daily_reports"
```

### 3.4 驗收標準

- [x] `_determine_time_period()` 正確實作 ✓
  - 首次執行: 30 天前
  - 後續執行: 上次 period_end
- [x] `fetch_analyzed_articles()` 正確傳遞時間參數 ✓
- [x] `_save_daily_report()` 正確儲存日報記錄 ✓
- [x] 無新文章時回傳 skip 狀態 ✓
- [x] 郵件發送失敗時不儲存記錄 ✓
- [x] 單元測試全部通過 ✓
- [x] 整合測試通過 ✓

---

## 4. 相依性

**前置條件**:
- Phase 1 完成 (DailyReport Model 已更新) ✓
- Phase 2 完成 (ReportStore 已建立) ✓
- Phase 3 完成 (ArticleStore 已支援時間過濾) ✓

**後續階段**:
- Phase 5 (資料庫遷移) - 現有資料庫需要遷移

---

*文件建立: 2025-12-05*
*完成日期: 2025-12-05*
