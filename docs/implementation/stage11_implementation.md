# Stage 11: Weekly Pipeline 集成 - 實作筆記

> **階段**: Phase 1 - Stage 11/12
> **實作日期**: 2025-11-25
> **實作者**: Ray 張瑞涵
> **狀態**: ✅ 完成（所有問題已修正）

---

## 📋 目錄

1. [實作總結](#實作總結)
2. [文件結構](#文件結構)
3. [主要實作](#主要實作)
4. [測試結果](#測試結果)
5. [發現的問題](#發現的問題)
6. [後續改進建議](#後續改進建議)

---

## 🎯 實作總結

### 完成內容

1. **Weekly Pipeline Orchestrator**
   - 創建 `src/orchestrator/weekly_runner.py`
   - 實作完整的命令行介面
   - 實作參數解析與驗證
   - 實作統計收集與顯示
   - 實作錯誤處理與建議

2. **單元測試**
   - 創建 `tests/unit/test_weekly_runner.py`
   - 18 個測試案例，全部通過
   - 覆蓋初始化、日期驗證、統計收集、錯誤處理、CLI 解析

3. **整合測試**
   - 創建 `tests/integration/test_weekly_pipeline.py`
   - 測試完整流程、自訂日期、錯誤處理

4. **文檔更新**
   - 更新 `src/orchestrator/__init__.py`
   - 添加 Weekly Orchestrator 到模組導出

### 實作時間

- **規劃**: 30 分鐘
- **實作**: 1 小時
- **測試**: 30 分鐘
- **總計**: 2 小時

---

## 📁 文件結構

### 新增文件

```
docs/
└─ planning/
    └─ stage11_weekly_pipeline.md       # 規劃文件

src/orchestrator/
└─ weekly_runner.py                     # 新增（420 行）

tests/unit/
└─ test_weekly_runner.py                # 新增（18 測試）

tests/integration/
└─ test_weekly_pipeline.py              # 新增（7 測試）

docs/implementation/
└─ stage11_implementation.md            # 本文件
```

### 修改文件

```
src/orchestrator/__init__.py            # 添加 Weekly Orchestrator 導出
```

---

## 🏗️ 主要實作

### 1. WeeklyPipelineOrchestrator 類

**文件**: `src/orchestrator/weekly_runner.py`

**關鍵方法**:

#### `run_weekly_pipeline()`

主要執行流程：

```python
def run_weekly_pipeline(
    self,
    week_start: Optional[str] = None,
    week_end: Optional[str] = None,
    dry_run: bool = False,
    recipients: Optional[List[str]] = None
) -> Dict[str, Any]:
    """執行完整週報流程"""
    start_time = time.time()

    try:
        # 1. 參數驗證與處理
        week_start, week_end = self._validate_dates(week_start, week_end)

        # 2. 顯示執行資訊
        self._print_header(week_start, week_end, dry_run)

        # 3. 執行 Weekly Runner
        runner = CuratorWeeklyRunner(self.config)
        result = runner.generate_weekly_report(
            week_start=week_start,
            week_end=week_end,
            dry_run=dry_run
        )

        # 4. 收集統計數據
        self._collect_stats(result)

        # 5. 顯示成功結果
        self.stats["duration"] = time.time() - start_time
        self._print_success()

        return {"status": "success", "stats": self.stats, ...}

    except Exception as e:
        # 錯誤處理
        self._print_error(e)
        return {"status": "error", ...}
```

#### `_validate_dates()`

日期驗證邏輯：

```python
def _validate_dates(
    self,
    week_start: Optional[str],
    week_end: Optional[str]
) -> tuple:
    """驗證與處理日期參數"""
    # 1. 設定默認值（過去 7 天）
    if week_end is None:
        week_end = datetime.now().strftime("%Y-%m-%d")
    if week_start is None:
        end_date = datetime.strptime(week_end, "%Y-%m-%d")
        start_date = end_date - timedelta(days=7)
        week_start = start_date.strftime("%Y-%m-%d")

    # 2. 驗證日期格式
    try:
        start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        end_dt = datetime.strptime(week_end, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}. Use YYYY-MM-DD")

    # 3. 驗證邏輯順序
    if start_dt >= end_dt:
        raise ValueError(
            f"week_start ({week_start}) must be before week_end ({week_end})"
        )

    # 4. 驗證日期範圍（建議 <= 14 天）
    days_diff = (end_dt - start_dt).days
    if days_diff > 14:
        self.logger.warning(
            f"Date range is {days_diff} days (recommended: <= 14 days). "
            f"Large ranges may affect report quality."
        )

    return week_start, week_end
```

### 2. 命令行介面

**解析器設計**:

```python
def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(
        description="InsightCosmos Weekly Pipeline - 週報自動化生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.orchestrator.weekly_runner --dry-run
  python -m src.orchestrator.weekly_runner --week-start 2025-11-18 --week-end 2025-11-24
  python -m src.orchestrator.weekly_runner --verbose
        """
    )

    parser.add_argument("--dry-run", action="store_true", help="測試模式，不發送郵件")
    parser.add_argument("--week-start", type=str, help="週期開始日期 (YYYY-MM-DD)")
    parser.add_argument("--week-end", type=str, help="週期結束日期 (YYYY-MM-DD)")
    parser.add_argument("--recipients", type=str, help="收件人列表（逗號分隔）")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細日誌模式")

    return parser.parse_args()
```

**主函數**:

```python
def main():
    """主函數入口"""
    args = parse_args()

    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        orchestrator = WeeklyPipelineOrchestrator()
        recipients = None
        if args.recipients:
            recipients = [r.strip() for r in args.recipients.split(",")]

        result = orchestrator.run_weekly_pipeline(
            week_start=args.week_start,
            week_end=args.week_end,
            dry_run=args.dry_run,
            recipients=recipients
        )

        sys.exit(0 if result["status"] == "success" else 1)

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
```

### 3. 顯示方法

**成功顯示**:

```
============================================================
✓ Weekly Pipeline Completed Successfully

Stats:
  Duration: 38.2s
  Articles: 52 total, 48 analyzed
  Clusters: 4 topics
  Hot Trends: 3
  Emerging Topics: 2
  Email Sent: True
  Recipients: sourcecor103@gmail.com
============================================================
```

**錯誤顯示**:

```
============================================================
✗ Weekly Pipeline Failed

Error: AttributeError
Message: 'ArticleStore' object has no attribute 'get_by_date_range'
Duration: 0.0s

Suggestion: Check database connection and ensure tables are initialized
============================================================
```

---

## 🧪 測試結果

### 單元測試

**命令**: `python -m pytest tests/unit/test_weekly_runner.py -v`

**結果**: ✅ **18/18 通過**

```
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_orchestrator_initialization PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_validate_dates_default PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_validate_dates_custom PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_validate_dates_invalid_format PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_validate_dates_invalid_order PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_validate_dates_range_warning PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_collect_stats PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_get_error_suggestion_insufficient_data PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_get_error_suggestion_date_error PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_get_error_suggestion_database_error PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_run_pipeline_success PASSED
tests/unit/test_weekly_runner.py::TestWeeklyPipelineOrchestrator::test_run_pipeline_error PASSED
tests/unit/test_weekly_runner.py::TestParseArgs::test_parse_args_default PASSED
tests/unit/test_weekly_runner.py::TestParseArgs::test_parse_args_dry_run PASSED
tests/unit/test_weekly_runner.py::TestParseArgs::test_parse_args_custom_dates PASSED
tests/unit/test_weekly_runner.py::TestParseArgs::test_parse_args_recipients PASSED
tests/unit/test_weekly_runner.py::TestParseArgs::test_parse_args_verbose PASSED
tests/unit/test_weekly_runner.py::TestParseArgs::test_parse_args_verbose_short PASSED

======================== 18 passed, 1 warning in 0.89s =========================
```

### 端到端測試

**命令**: `python -m src.orchestrator.weekly_runner --dry-run`

**結果**: ✅ **成功**

**執行結果**:

```
============================================================
InsightCosmos Weekly Pipeline
============================================================

Week Period: 2025-11-18 to 2025-11-25
Mode: Dry Run (No Email)


============================================================
✓ Weekly Pipeline Completed Successfully

Stats:
  Duration: 17.3s
  Articles: 71 total, 71 analyzed
  Clusters: 5 topics
  Hot Trends: 4
  Emerging Topics: 15
  Email Sent: False
  Recipients: sourcecor103@gmail.com
============================================================
```

---

## ⚠️ 發現並修正的問題

### 問題 1: ArticleStore 缺少 `get_by_date_range` 方法 ✅ 已修正

**發現位置**: Stage 11 端到端測試

**解決方案**: 在 `src/memory/article_store.py` 添加 `get_by_date_range()` 方法

### 問題 2: EmbeddingStore 缺少 `get_embeddings` 方法 ✅ 已修正

**發現位置**: Stage 11 端到端測試

**解決方案**: 在 `src/memory/embedding_store.py` 添加 `get_embeddings()` 方法

### 問題 3: Embedding.vector 應為 Embedding.embedding ✅ 已修正

**發現位置**: 聚類步驟

**解決方案**: 修正 `get_embeddings()` 中的欄位名稱

### 問題 4: 文章數與 Embedding 數不匹配 ✅ 已修正

**發現位置**: 聚類步驟

**解決方案**: 在聚類前過濾出有 embedding 的文章

### 問題 5: tags 欄位類型不一致 ✅ 已修正

**發現位置**: 趨勢分析步驟

**解決方案**: 修正 `trend_analysis.py` 以處理 list 和 string 類型

### 問題 6: LLM Runner 調用方式錯誤 ✅ 已修正

**發現位置**: LLM 報告生成步驟

**解決方案**: 改用 async 模式調用，參考 Daily Curator 實作

### 問題 7: 統計數據未正確收集 ✅ 已修正

**發現位置**: 端到端測試

**解決方案**: 修改 `generate_weekly_report()` 返回值包含統計數據

---

## 🔧 後續改進建議

### 中期優化

1. **ArticleStore 增強查詢能力**
   - 添加更多過濾條件支援
   - 支援複合查詢條件
   - 支援分頁

2. **Weekly Pipeline 性能優化**
   - 減少資料庫查詢次數
   - 優化聚類演算法
   - 添加快取機制

### 長期規劃

1. **完整的日期範圍查詢 API**
2. **更靈活的過濾與排序**
3. **查詢結果快取**

---

## 📊 Stage 11 完成度

### 已完成 ✅

- [x] 規劃文件
- [x] WeeklyPipelineOrchestrator 實作
- [x] 命令行介面實作
- [x] 日期驗證與處理
- [x] 統計收集與顯示
- [x] 錯誤處理與建議
- [x] 單元測試（18/18 通過）
- [x] 整合測試（已編寫）
- [x] 文檔更新
- [x] Stage 10 API 問題修正
- [x] 端到端測試驗證通過

### 驗收標準

| 標準 | 狀態 | 備註 |
|------|------|------|
| 命令行介面 | ✅ | 所有參數正確解析 |
| 日期驗證 | ✅ | 能正確驗證與處理 |
| 流程執行 | ✅ | 完整 5 步流程順利執行 |
| 統計收集 | ✅ | 71 文章、5 集群、4 熱門趨勢、15 新興話題 |
| 錯誤處理 | ✅ | 能友好處理各種錯誤 |
| 日誌記錄 | ✅ | 能記錄完整過程 |
| 顯示格式 | ✅ | 控制台輸出清晰 |
| 單元測試 | ✅ | 18/18 通過 |
| 整合測試 | ✅ | 端到端驗證通過 |

---

## 🎯 下一步行動

### 已完成 ✅

1. **修正 Stage 10 問題** ✅
   - 添加 `ArticleStore.get_by_date_range()` 方法
   - 添加 `EmbeddingStore.get_embeddings()` 方法
   - 修正 LLM Runner 調用方式
   - 修正統計數據收集

2. **完成 Stage 11 端到端驗證** ✅
   - 執行完整 Weekly Pipeline 測試
   - 確認統計數據準確性

### 待進行

3. **進入 Stage 12**
   - 質量保證與優化
   - 完善測試覆蓋
   - 性能優化
   - Phase 1 最終驗收

4. **生產模式測試**（可選）
   - 驗證郵件發送（移除 --dry-run）

---

## 📝 經驗教訓

### 1. 跨 Stage 依賴驗證的重要性

**問題**: Stage 10 實作時假設了不存在的 API，直到 Stage 11 整合測試才發現。

**教訓**: 每個 Stage 完成後應該進行基本的端到端測試，而不僅是單元測試。

**改進**: 在 Stage 完成 Checklist 中添加「基本功能驗證」項目。

### 2. API 設計一致性

**問題**: ArticleStore 的查詢方法不一致（get_recent 用天數，其他用具體條件）。

**教訓**: 應該在設計階段明確定義完整的查詢 API。

**改進**: 在 Memory Layer 設計文件中明確列出所有需要的查詢方法。

### 3. 測試驅動的重要性

**優點**: 單元測試幫助我們快速驗證 Orchestrator 的邏輯正確性。

**教訓**: 但單元測試（使用 Mock）無法發現跨模組的介面不匹配問題。

**改進**: 整合測試與端到端測試同樣重要，不能只依賴單元測試。

---

## 🔗 相關文件

- [Stage 11 規劃文件](../planning/stage11_weekly_pipeline.md)
- [Stage 10 規劃文件](../planning/stage10_curator_weekly.md)
- [ArticleStore 實作](../../src/memory/article_store.py)
- [CuratorWeeklyRunner 實作](../../src/agents/curator_weekly.py)
- [WeeklyPipelineOrchestrator 實作](../../src/orchestrator/weekly_runner.py)

---

**實作完成時間**: 2025-11-25
**文件版本**: 1.1
**維護者**: Ray 張瑞涵
**狀態**: ✅ Stage 11 完成，所有問題已修正，端到端驗證通過
