# Phase 2: 新增 ReportStore 類別

> **功能**: 日報時間過濾
> **階段**: Phase 2 of 5
> **狀態**: 規劃中

---

## 1. Planning (規劃)

### 1.1 目標

建立 `ReportStore` 類別，管理日報記錄的 CRUD 操作，提供查詢上次日報時間和儲存新日報的功能。

### 1.2 需求分析

**核心需求:**
1. 查詢最近一次日報的 `period_end` (用於下次日報的起始時間)
2. 儲存新的日報記錄
3. 遵循現有 `ArticleStore` 的設計模式

### 1.3 設計規格

**類別結構:**

```python
class ReportStore:
    """日報記錄管理類別"""

    def __init__(self, database: Database)

    def get_last_daily_report(self) -> Optional[Dict[str, Any]]
        """取得最近一次日報記錄"""

    def create_daily_report(...) -> int
        """建立新的日報記錄"""

    def get_daily_report_by_date(report_date: date) -> Optional[Dict[str, Any]]
        """依日期查詢日報"""
```

**方法規格:**

| 方法 | 輸入 | 輸出 | 說明 |
|------|------|------|------|
| `get_last_daily_report()` | 無 | `Optional[dict]` | 取得最近日報，用於確定下次起始時間 |
| `create_daily_report()` | 多個參數 | `int` (ID) | 建立新日報記錄 |
| `get_daily_report_by_date()` | `date` | `Optional[dict]` | 依日期查詢 |

### 1.4 影響範圍

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `src/memory/report_store.py` | 新增 | ReportStore 類別 |
| `src/memory/__init__.py` | 修改 | 匯出 ReportStore |

---

## 2. Implementation (實作)

### 2.1 新增 report_store.py

**檔案**: `src/memory/report_store.py`

```python
"""
InsightCosmos Report Store

Provides CRUD operations for daily/weekly reports.

Classes:
    ReportStore: Report data management

Usage:
    from src.memory.database import Database
    from src.memory.report_store import ReportStore

    db = Database.from_config(config)
    store = ReportStore(db)

    # Get last report
    last_report = store.get_last_daily_report()

    # Create new report
    report_id = store.create_daily_report(
        report_date=date.today(),
        period_start=last_period_end,
        period_end=datetime.utcnow(),
        article_count=10,
        top_articles=[1, 2, 3],
        content='{"digest": ...}'
    )
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy import desc
import json
import logging

from src.memory.models import DailyReport
from src.memory.database import Database
from src.utils.logger import Logger


class ReportStore:
    """
    Report storage management

    Provides CRUD operations for daily reports with support for:
    - Querying last report (for time-based filtering)
    - Creating new reports with period tracking
    - Querying by date

    Attributes:
        database (Database): Database instance
        logger (Logger): Logger instance

    Example:
        >>> store = ReportStore(db)
        >>> last = store.get_last_daily_report()
        >>> if last:
        ...     period_start = last['period_end']
        ... else:
        ...     period_start = datetime.utcnow() - timedelta(days=30)
    """

    def __init__(self, database: Database, logger: Optional[logging.Logger] = None):
        """
        Initialize ReportStore

        Args:
            database: Database instance
            logger: Logger instance (optional)
        """
        self.database = database
        self.logger = logger or Logger.get_logger("ReportStore")

    def get_last_daily_report(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent daily report

        Returns the last daily report record, which can be used to determine
        the starting time for the next report's article collection.

        Returns:
            Optional[dict]: Last report data with period_end, or None if no reports exist

        Example:
            >>> last = store.get_last_daily_report()
            >>> if last:
            ...     print(f"Last report ended at: {last['period_end']}")
            ... else:
            ...     print("No previous reports found")
        """
        try:
            with self.database.get_session() as session:
                report = session.query(DailyReport)\
                    .order_by(desc(DailyReport.created_at))\
                    .first()

                if report:
                    self.logger.info(
                        f"Found last daily report: {report.report_date}, "
                        f"period_end={report.period_end}"
                    )
                    return report.to_dict()

                self.logger.info("No previous daily reports found")
                return None

        except Exception as e:
            self.logger.error(f"Failed to get last daily report: {e}")
            return None

    def create_daily_report(
        self,
        report_date: date,
        period_start: datetime,
        period_end: datetime,
        article_count: int,
        top_articles: List[int],
        content: str,
        sent_at: Optional[datetime] = None
    ) -> int:
        """
        Create a new daily report record

        Args:
            report_date: Report date (unique per day)
            period_start: Article collection start time
            period_end: Article collection end time
            article_count: Number of articles included
            top_articles: List of article IDs
            content: Report content (JSON string)
            sent_at: Email sent timestamp (optional)

        Returns:
            int: New report ID

        Raises:
            ValueError: If report for this date already exists
            Exception: If database operation fails

        Example:
            >>> report_id = store.create_daily_report(
            ...     report_date=date.today(),
            ...     period_start=datetime(2025, 12, 4, 8, 0),
            ...     period_end=datetime(2025, 12, 5, 8, 0),
            ...     article_count=10,
            ...     top_articles=[101, 102, 103],
            ...     content='{"top_articles": [...], "daily_insight": "..."}'
            ... )
        """
        try:
            with self.database.get_session() as session:
                # Check if report for this date already exists
                existing = session.query(DailyReport)\
                    .filter(DailyReport.report_date == report_date)\
                    .first()

                if existing:
                    self.logger.warning(
                        f"Daily report for {report_date} already exists (id={existing.id}), "
                        "updating instead"
                    )
                    # Update existing report
                    existing.period_start = period_start
                    existing.period_end = period_end
                    existing.article_count = article_count
                    existing.top_articles = json.dumps(top_articles)
                    existing.content = content
                    existing.sent_at = sent_at
                    session.flush()
                    return existing.id

                # Create new report
                report = DailyReport(
                    report_date=report_date,
                    period_start=period_start,
                    period_end=period_end,
                    article_count=article_count,
                    top_articles=json.dumps(top_articles),
                    content=content,
                    sent_at=sent_at
                )

                session.add(report)
                session.flush()

                report_id = report.id

                self.logger.info(
                    f"Created daily report: id={report_id}, date={report_date}, "
                    f"period={period_start} to {period_end}, articles={article_count}"
                )

                return report_id

        except Exception as e:
            self.logger.error(f"Failed to create daily report: {e}")
            raise

    def get_daily_report_by_date(self, report_date: date) -> Optional[Dict[str, Any]]:
        """
        Get daily report by date

        Args:
            report_date: Report date to query

        Returns:
            Optional[dict]: Report data or None if not found

        Example:
            >>> report = store.get_daily_report_by_date(date(2025, 12, 5))
        """
        try:
            with self.database.get_session() as session:
                report = session.query(DailyReport)\
                    .filter(DailyReport.report_date == report_date)\
                    .first()

                if report:
                    return report.to_dict()
                return None

        except Exception as e:
            self.logger.error(f"Failed to get daily report by date: {e}")
            return None
```

### 2.2 修改 __init__.py

**檔案**: `src/memory/__init__.py`

```python
# 新增匯出
from src.memory.report_store import ReportStore

__all__ = [
    'Database',
    'ArticleStore',
    'EmbeddingStore',
    'ReportStore',  # 新增
]
```

---

## 3. Validation (驗證)

### 3.1 驗證項目

| 項目 | 驗證方法 | 預期結果 |
|------|----------|----------|
| 類別建立 | 單元測試 | 正常初始化 |
| get_last_daily_report() | 單元測試 | 回傳正確資料或 None |
| create_daily_report() | 單元測試 | 成功建立並回傳 ID |
| 重複日期處理 | 單元測試 | 更新而非報錯 |

### 3.2 測試案例

```python
# tests/unit/test_report_store.py

import pytest
from datetime import datetime, date, timedelta
from src.memory.report_store import ReportStore
from src.memory.database import Database


@pytest.fixture
def report_store(tmp_path):
    """建立測試用 ReportStore"""
    db_path = tmp_path / "test.db"
    db = Database(f"sqlite:///{db_path}")
    db.create_tables()
    return ReportStore(db)


class TestReportStore:

    def test_get_last_daily_report_empty(self, report_store):
        """測試無日報時回傳 None"""
        result = report_store.get_last_daily_report()
        assert result is None

    def test_create_daily_report(self, report_store):
        """測試建立日報"""
        report_id = report_store.create_daily_report(
            report_date=date(2025, 12, 5),
            period_start=datetime(2025, 12, 4, 8, 0),
            period_end=datetime(2025, 12, 5, 8, 0),
            article_count=10,
            top_articles=[1, 2, 3],
            content='{"test": true}'
        )

        assert report_id > 0

    def test_get_last_daily_report_after_create(self, report_store):
        """測試建立後可查詢"""
        # 建立日報
        report_store.create_daily_report(
            report_date=date(2025, 12, 5),
            period_start=datetime(2025, 12, 4, 8, 0),
            period_end=datetime(2025, 12, 5, 8, 0),
            article_count=10,
            top_articles=[1, 2, 3],
            content='{}'
        )

        # 查詢
        result = report_store.get_last_daily_report()

        assert result is not None
        assert result['article_count'] == 10
        assert result['period_end'] == '2025-12-05T08:00:00'

    def test_create_duplicate_date_updates(self, report_store):
        """測試重複日期會更新而非報錯"""
        # 第一次建立
        id1 = report_store.create_daily_report(
            report_date=date(2025, 12, 5),
            period_start=datetime(2025, 12, 4, 8, 0),
            period_end=datetime(2025, 12, 5, 8, 0),
            article_count=10,
            top_articles=[1, 2, 3],
            content='{}'
        )

        # 第二次建立（同日期）
        id2 = report_store.create_daily_report(
            report_date=date(2025, 12, 5),
            period_start=datetime(2025, 12, 4, 8, 0),
            period_end=datetime(2025, 12, 5, 10, 0),  # 不同時間
            article_count=15,  # 不同數量
            top_articles=[1, 2, 3, 4, 5],
            content='{}'
        )

        assert id1 == id2  # 應該是同一筆記錄

        # 確認已更新
        result = report_store.get_daily_report_by_date(date(2025, 12, 5))
        assert result['article_count'] == 15

    def test_get_last_report_returns_most_recent(self, report_store):
        """測試回傳最新的日報"""
        # 建立多筆日報
        report_store.create_daily_report(
            report_date=date(2025, 12, 3),
            period_start=datetime(2025, 12, 2),
            period_end=datetime(2025, 12, 3),
            article_count=5,
            top_articles=[1],
            content='{}'
        )

        report_store.create_daily_report(
            report_date=date(2025, 12, 5),
            period_start=datetime(2025, 12, 4),
            period_end=datetime(2025, 12, 5),
            article_count=10,
            top_articles=[2],
            content='{}'
        )

        # 查詢最新
        result = report_store.get_last_daily_report()

        assert result['report_date'] == '2025-12-05T00:00:00'
```

### 3.3 驗收標準

- [x] ReportStore 類別建立完成 ✓
- [x] get_last_daily_report() 正確回傳最新日報或 None ✓
- [x] create_daily_report() 正確建立日報記錄 ✓
- [x] 重複日期自動更新而非報錯 ✓
- [x] 單元測試全部通過 ✓
- [x] 已匯出至 `src/memory/__init__.py` ✓

---

## 4. 相依性

**前置條件**:
- Phase 1 完成 (DailyReport Model 已更新)

**後續階段**:
- Phase 4 (CuratorDailyRunner) 依賴本階段的 ReportStore

---

*文件建立: 2025-12-05*
*完成日期: 2025-12-05*
