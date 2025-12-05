# Phase 1: 擴展 daily_reports 表結構

> **功能**: 日報時間過濾
> **階段**: Phase 1 of 5
> **狀態**: 規劃中

---

## 1. Planning (規劃)

### 1.1 目標

擴展 `daily_reports` 表，新增時間範圍欄位，用於記錄每次日報涵蓋的文章收集期間。

### 1.2 需求分析

**現有 Schema (schema.sql:84-92):**
```sql
CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    article_count INTEGER NOT NULL,
    top_articles TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**缺少欄位:**
- `period_start` - 本次日報涵蓋的起始時間
- `period_end` - 本次日報涵蓋的結束時間

### 1.3 設計規格

**新增欄位:**

| 欄位名稱 | 類型 | 約束 | 說明 |
|---------|------|------|------|
| `period_start` | DATETIME | NOT NULL | 文章收集起始時間 |
| `period_end` | DATETIME | NOT NULL | 文章收集結束時間 |

**新 Schema:**
```sql
CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    period_start DATETIME NOT NULL,     -- 新增
    period_end DATETIME NOT NULL,       -- 新增
    article_count INTEGER NOT NULL,
    top_articles TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 1.4 影響範圍

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `src/memory/schema.sql` | 修改 | 新增欄位定義 |
| `src/memory/models.py` | 修改 | 更新 DailyReport ORM Model |

---

## 2. Implementation (實作)

### 2.1 修改 schema.sql

**檔案**: `src/memory/schema.sql`

**修改位置**: Lines 84-92

```sql
-- ========================================
-- Table 3: daily_reports
-- ========================================
-- Description: Stores daily digest reports with time period tracking
-- Primary Key: id (auto-increment)
-- Unique Constraint: report_date (one report per day)

CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    period_start DATETIME NOT NULL,     -- 新增: 文章收集起始時間
    period_end DATETIME NOT NULL,       -- 新增: 文章收集結束時間
    article_count INTEGER NOT NULL,
    top_articles TEXT NOT NULL,         -- JSON array of article IDs
    content TEXT NOT NULL,              -- Report content in JSON format
    sent_at DATETIME,                   -- Email sent timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for daily_reports table
CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(report_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_reports_period ON daily_reports(period_end DESC);  -- 新增
```

### 2.2 修改 models.py

**檔案**: `src/memory/models.py`

**修改位置**: DailyReport class (Lines 185-227)

```python
class DailyReport(Base):
    """
    Daily Report ORM model

    Represents a daily digest report with time period tracking.

    Attributes:
        id (int): Primary key
        report_date (datetime): Report date (unique)
        period_start (datetime): Article collection start time (新增)
        period_end (datetime): Article collection end time (新增)
        article_count (int): Number of articles included
        top_articles (str): JSON array of article IDs
        content (str): Report content in JSON format
        sent_at (datetime): Email sent timestamp
        created_at (datetime): Record creation time
    """
    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(DateTime, unique=True, nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)  # 新增
    period_end = Column(DateTime, nullable=False)    # 新增
    article_count = Column(Integer, nullable=False)
    top_articles = Column(Text, nullable=False)      # JSON array
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DailyReport to dictionary

        Returns:
            dict: Report data as dictionary
        """
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'period_start': self.period_start.isoformat() if self.period_start else None,  # 新增
            'period_end': self.period_end.isoformat() if self.period_end else None,        # 新增
            'article_count': self.article_count,
            'top_articles': json.loads(self.top_articles) if self.top_articles else [],
            'content': self.content,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"<DailyReport(id={self.id}, date='{self.report_date}', "
            f"period={self.period_start} to {self.period_end}, "
            f"articles={self.article_count})>"
        )
```

---

## 3. Validation (驗證)

### 3.1 驗證項目

| 項目 | 驗證方法 | 預期結果 |
|------|----------|----------|
| Schema 語法 | SQLite 執行 | 無錯誤 |
| ORM Model 對應 | 單元測試 | 欄位正確對應 |
| to_dict() 輸出 | 單元測試 | 包含新欄位 |
| 向後相容 | 現有程式碼測試 | 不影響現有功能 |

### 3.2 測試案例

```python
# tests/unit/test_daily_report_model.py

def test_daily_report_has_period_columns():
    """驗證 DailyReport 包含 period_start 和 period_end 欄位"""
    from src.memory.models import DailyReport

    assert hasattr(DailyReport, 'period_start')
    assert hasattr(DailyReport, 'period_end')

def test_daily_report_to_dict_includes_period():
    """驗證 to_dict() 包含 period 欄位"""
    from datetime import datetime
    from src.memory.models import DailyReport

    report = DailyReport(
        report_date=datetime(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 8, 0),
        article_count=10,
        top_articles='[1,2,3]',
        content='{}'
    )

    result = report.to_dict()

    assert 'period_start' in result
    assert 'period_end' in result
    assert result['period_start'] == '2025-12-04T08:00:00'
    assert result['period_end'] == '2025-12-05T08:00:00'
```

### 3.3 驗收標準

- [x] schema.sql 新增 period_start, period_end 欄位 ✓
- [x] models.py DailyReport 類別更新 ✓
- [x] to_dict() 方法包含新欄位 ✓
- [x] 單元測試通過 ✓
- [x] 現有功能不受影響 ✓

---

## 4. 相依性

**前置條件**: 無

**後續階段**:
- Phase 2 (ReportStore) 依賴本階段的 Model 定義
- Phase 5 (遷移) 依賴本階段的 Schema 定義

---

*文件建立: 2025-12-05*
*完成日期: 2025-12-05*
