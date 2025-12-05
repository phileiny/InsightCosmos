# Time Filter Feature - Phase 4 測試報告

> **功能**: 日報時間過濾
> **階段**: Phase 4 - 修改 CuratorDailyRunner
> **測試日期**: 2025-12-05
> **狀態**: 通過

---

## 1. 測試概覽

| 項目 | 結果 |
|------|------|
| 新增測試案例 | 6 |
| 原有測試案例 | 16 |
| 通過 | 22 |
| 失敗 | 0 |
| 測試時間 | 0.85s |

---

## 2. 修改檔案

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `src/agents/curator_daily.py` | 修改 | 新增時間過濾整合 |
| `tests/unit/test_curator_daily.py` | 修改 | 新增 6 個測試案例 + 更新原有測試 |

---

## 3. 新增測試案例詳情

### TC-CUR-01: First Run Uses 30 Days

**目的**: 驗證首次執行使用 30 天作為預設時間範圍

**測試方法**:
```python
# 模擬無前次報告
mock_report_store.get_last_daily_report.return_value = None

period_start, period_end = runner._determine_time_period()

# 驗證: period_start 應為 30 天前
expected_start = period_end - timedelta(days=DEFAULT_FIRST_RUN_DAYS)
assert abs((period_start - expected_start).total_seconds()) < 1
```

**結果**: PASSED

---

### TC-CUR-02: Subsequent Run Uses Last Period End

**目的**: 驗證後續執行使用前次報告的 `period_end`

**測試方法**:
```python
last_period_end = datetime(2025, 12, 4, 8, 0, 0)
mock_report_store.get_last_daily_report.return_value = {
    'period_end': last_period_end.isoformat()
}

period_start, period_end = runner._determine_time_period()

assert period_start == last_period_end
```

**結果**: PASSED

---

### TC-CUR-03: No Articles Returns Skip

**目的**: 驗證無文章時返回 'skip' 狀態

**測試方法**:
```python
mock_article_store.get_top_priority.return_value = []

result = runner.generate_and_send_digest(...)

assert result['status'] == 'skip'
assert 'No new articles' in result['message']
```

**結果**: PASSED

---

### TC-CUR-04: Saves Report On Success

**目的**: 驗證成功發送後儲存報告記錄

**測試方法**:
```python
# Mock 成功流程
result = runner.generate_and_send_digest(...)

# 驗證 ReportStore.create_daily_report 被調用
mock_report_store.create_daily_report.assert_called_once()
```

**結果**: PASSED

---

### TC-CUR-05: Does Not Save Report On Email Failure

**目的**: 驗證 Email 發送失敗時不儲存報告記錄

**測試方法**:
```python
# Mock Email 發送失敗
mock_send.return_value = {'success': False, 'error': 'SMTP error'}

result = runner.generate_and_send_digest(...)

# 驗證: ReportStore.create_daily_report 未被調用
mock_report_store.create_daily_report.assert_not_called()
```

**結果**: PASSED

---

### TC-CUR-06: Fetch Articles With Time Params

**目的**: 驗證時間參數正確傳遞給 `get_top_priority()`

**測試方法**:
```python
runner.fetch_analyzed_articles(max_articles=10, fetched_after=start, fetched_before=end)

call_kwargs = mock_article_store.get_top_priority.call_args[1]
assert call_kwargs['fetched_after'] == start
assert call_kwargs['fetched_before'] == end
```

**結果**: PASSED

---

## 4. 原有測試更新

| 測試 | 修改說明 |
|------|----------|
| `test_fetch_analyzed_articles` | 更新驗證邏輯以符合新的方法簽名（新增時間參數） |
| `test_generate_and_send_digest_no_articles` | 更新預期結果為 'skip' 狀態 |
| `test_generate_daily_digest_with_mock` | 修正 patch 路徑並新增 ReportStore mock |
| `mock_article_store` fixture | 新增 `database` 屬性以支援 ReportStore 初始化 |

---

## 5. 測試執行記錄

```
============================= test session starts ==============================
platform darwin -- Python 3.13.1, pytest-9.0.1, pluggy-1.6.0
rootdir: /Users/ray/sides/InsightCosmos
plugins: anyio-4.11.0, asyncio-1.3.0, cov-7.0.0

tests/unit/test_curator_daily.py::TestCuratorDailyAgent::test_create_curator_agent PASSED [  4%]
tests/unit/test_curator_daily.py::TestCuratorDailyAgent::test_load_prompt_with_variables PASSED [  9%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_runner_initialization PASSED [ 13%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_fetch_analyzed_articles PASSED [ 18%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_fetch_analyzed_articles_empty PASSED [ 22%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_parse_digest_json_plain PASSED [ 27%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_parse_digest_json_in_markdown PASSED [ 31%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_parse_digest_invalid_json PASSED [ 36%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_generate_digest_with_mock_llm PASSED [ 40%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_generate_digest_empty_articles PASSED [ 45%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_generate_and_send_digest_success PASSED [ 50%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_generate_and_send_digest_no_articles PASSED [ 54%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_generate_and_send_digest_llm_failure PASSED [ 59%]
tests/unit/test_curator_daily.py::TestCuratorDailyRunner::test_generate_and_send_digest_email_failure PASSED [ 63%]
tests/unit/test_curator_daily.py::TestConvenienceFunction::test_generate_daily_digest_with_mock PASSED [ 68%]
tests/unit/test_curator_daily.py::test_module_imports PASSED             [ 72%]
tests/unit/test_curator_daily.py::TestCuratorTimeFilter::test_first_run_uses_30_days PASSED [ 77%]
tests/unit/test_curator_daily.py::TestCuratorTimeFilter::test_subsequent_run_uses_last_period_end PASSED [ 81%]
tests/unit/test_curator_daily.py::TestCuratorTimeFilter::test_no_articles_returns_skip PASSED [ 86%]
tests/unit/test_curator_daily.py::TestCuratorTimeFilter::test_saves_report_on_success PASSED [ 90%]
tests/unit/test_curator_daily.py::TestCuratorTimeFilter::test_does_not_save_report_on_email_failure PASSED [ 95%]
tests/unit/test_curator_daily.py::TestCuratorTimeFilter::test_fetch_articles_with_time_params PASSED [100%]

======================= 22 passed, 12 warnings in 0.85s ========================
```

---

## 6. 程式碼變更摘要

### 6.1 新增常數

```python
# src/agents/curator_daily.py
DEFAULT_FIRST_RUN_DAYS = 30  # 首次執行預設取 30 天內的文章
```

### 6.2 新增 Import

```python
from src.memory.report_store import ReportStore
```

### 6.3 新增方法: `_determine_time_period()`

```python
def _determine_time_period(self) -> tuple:
    """
    Determine the time period for article filtering

    Returns:
        tuple: (period_start, period_end) as datetime objects

    Logic:
        - First run: period_start = 30 days ago
        - Subsequent runs: period_start = last report's period_end
    """
    period_end = datetime.utcnow()
    last_report = self.report_store.get_last_daily_report()

    if last_report and last_report.get('period_end'):
        period_start = datetime.fromisoformat(last_report['period_end'])
    else:
        period_start = period_end - timedelta(days=DEFAULT_FIRST_RUN_DAYS)

    return period_start, period_end
```

### 6.4 新增方法: `_save_daily_report()`

```python
def _save_daily_report(
    self,
    digest_date: date,
    period_start: datetime,
    period_end: datetime,
    articles: List[Dict],
    digest: Dict[str, Any],
    formatted_content: Dict[str, str]
) -> int:
    """Save daily report record after successful email"""
```

### 6.5 修改方法: `generate_and_send_digest()`

**主要變更**:
1. 開始時調用 `_determine_time_period()` 取得時間範圍
2. 將時間參數傳遞給 `fetch_analyzed_articles()`
3. 無文章時返回 `status: 'skip'` 而非 `status: 'error'`
4. 成功發送後調用 `_save_daily_report()` 儲存記錄

### 6.6 修改方法: `fetch_analyzed_articles()`

**新增參數**:
```python
def fetch_analyzed_articles(
    self,
    max_articles: int = 10,
    fetched_after: Optional[datetime] = None,   # 新增
    fetched_before: Optional[datetime] = None   # 新增
) -> List[Dict[str, Any]]:
```

---

## 7. 驗收標準

| 項目 | 狀態 |
|------|------|
| 首次執行使用 30 天作為預設時間範圍 | ✓ 通過 |
| 後續執行使用前次報告的 `period_end` | ✓ 通過 |
| 無新文章時返回 'skip' 狀態 | ✓ 通過 |
| 成功發送後儲存報告記錄 | ✓ 通過 |
| Email 失敗時不儲存報告記錄 | ✓ 通過 |
| 時間參數正確傳遞 | ✓ 通過 |
| 原有測試全部通過（向後相容） | ✓ 通過 |

---

## 8. 備註

- 有 deprecation warning: `datetime.utcnow()` 建議改用 `datetime.now(datetime.UTC)`
- 此為 Python 3.12+ 的建議，暫不影響功能

---

*測試執行: 2025-12-05*
*測試人員: Claude Code*
