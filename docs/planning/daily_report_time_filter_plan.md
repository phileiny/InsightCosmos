# 日報時間過濾功能修改計畫

> **文件版本**: 1.0
> **建立日期**: 2025-12-05
> **狀態**: 待實作

---

## 目標

修改日報生成邏輯，使每次日報只包含「上次日報產生時間」到「本次日報產生時間」之間的新文章，避免舊文章重複出現。

**首次執行**: 預設取過去 **30 天（一個月）** 內的文章。

---

## 現狀分析

### 目前問題

```
目前流程:
articles 表 (所有已分析文章)
    ↓
get_top_priority(limit=30, status='analyzed')
    ↓
按 priority_score DESC 排序 (無時間限制)
    ↓
可能包含多天前的舊文章，導致日報內容重複
```

### 現有資源

1. **`daily_reports` 表已存在** - 可用於記錄日報時間
2. **`articles.fetched_at` 欄位** - 可用於時間過濾
3. **`DailyReport` ORM Model 已存在**

---

## 修改計畫

### Phase 1: 擴展 daily_reports 表結構

**修改檔案**: `src/memory/schema.sql`, `src/memory/models.py`

新增欄位：
- `period_start` - 本次日報涵蓋的起始時間
- `period_end` - 本次日報涵蓋的結束時間

### Phase 2: 新增 ReportStore 類別

**新增檔案**: `src/memory/report_store.py`

主要方法：
- `get_last_daily_report()` - 取得最近一次日報記錄
- `create_daily_report()` - 建立新的日報記錄

### Phase 3: 修改 ArticleStore.get_top_priority()

**修改檔案**: `src/memory/article_store.py`

新增參數：
- `fetched_after: Optional[datetime]` - 只取此時間之後的文章
- `fetched_before: Optional[datetime]` - 只取此時間之前的文章

### Phase 4: 修改 CuratorDailyRunner

**修改檔案**: `src/agents/curator_daily.py`

整合時間過濾邏輯：
1. 查詢上次日報的 `period_end`
2. 若無歷史日報，使用 `now - 30 days` 作為起始時間
3. 儲存本次日報記錄

### Phase 5: 資料庫遷移

**新增檔案**: `src/memory/migrations/001_add_period_columns.py`

---

## 核心邏輯

```python
# 時間範圍決定邏輯
last_report = report_store.get_last_daily_report()

if last_report and last_report.get('period_end'):
    # 有上次日報 → 從上次結束時間開始
    period_start = last_report['period_end']
else:
    # 首次執行 → 預設取過去 30 天（一個月）
    period_start = datetime.utcnow() - timedelta(days=30)

period_end = datetime.utcnow()

# 取得時間範圍內的文章
articles = article_store.get_top_priority(
    limit=30,
    status='analyzed',
    fetched_after=period_start,
    fetched_before=period_end
)
```

---

## 流程變更圖

```
┌─────────────────────────────────────────────────────────────┐
│                      修改後流程                              │
└─────────────────────────────────────────────────────────────┘

daily_reports 表
    │
    ▼
get_last_daily_report()
    │
    ├── 有記錄 → period_start = 上次 period_end
    │
    └── 無記錄 → period_start = now - 30 days  ← 首次取一個月
    │
    ▼
articles 表
    │
    ▼
get_top_priority(
    limit=30,
    status='analyzed',
    fetched_after=period_start,
    fetched_before=now()
)
    │
    ▼
時間範圍內的已分析文章
    │
    ▼
去重 → 10 篇
    │
    ▼
生成日報 → 發送 Email
    │
    ▼
create_daily_report(
    period_start=period_start,
    period_end=now()
)
```

---

## 邊界情況處理

| 情況 | 處理方式 |
|------|----------|
| **首次執行** | `period_start = now - 30 days` (取一個月內文章) |
| **時間範圍內無新文章** | 回傳 skip 狀態，不發送空日報 |
| **同一天多次執行** | 正常處理，每次都從上次 period_end 開始 |
| **補發日報** | 可選：允許手動指定 period_start/period_end |

---

## 實作順序

| 階段 | 任務 | 預估時間 |
|------|------|----------|
| Phase 1 | 更新 schema.sql 和 models.py | 15 分鐘 |
| Phase 2 | 新增 ReportStore 類別 | 30 分鐘 |
| Phase 3 | 修改 ArticleStore.get_top_priority() | 20 分鐘 |
| Phase 4 | 修改 CuratorDailyRunner | 45 分鐘 |
| Phase 5 | 建立並執行資料庫遷移 | 15 分鐘 |
| 測試 | 單元測試 + 整合測試 | 30 分鐘 |

**總預估時間**: 約 2.5 小時

---

## 相關檔案

| 檔案 | 修改類型 |
|------|----------|
| `src/memory/schema.sql` | 修改 |
| `src/memory/models.py` | 修改 |
| `src/memory/report_store.py` | 新增 |
| `src/memory/article_store.py` | 修改 |
| `src/agents/curator_daily.py` | 修改 |
| `src/memory/migrations/001_add_period_columns.py` | 新增 |

---

*建立日期: 2025-12-05*
