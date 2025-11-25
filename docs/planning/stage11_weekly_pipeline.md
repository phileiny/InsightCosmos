# Stage 11: Weekly Pipeline 集成 - 規劃文件

> **階段**: Phase 1 - Stage 11/12
> **目標**: 實現完整的週報自動化流程編排
> **預計時間**: 0.5 天
> **創建日期**: 2025-11-25
> **負責人**: Ray 張瑞涵

---

## 📋 目錄

1. [目標說明](#目標說明)
2. [輸入/輸出定義](#輸入輸出定義)
3. [技術設計](#技術設計)
4. [Weekly Pipeline Orchestrator 設計](#weekly-pipeline-orchestrator-設計)
5. [與 Daily Pipeline 的對比](#與-daily-pipeline-的對比)
6. [實作計劃](#實作計劃)
7. [測試策略](#測試策略)
8. [驗收標準](#驗收標準)
9. [風險與對策](#風險與對策)

---

## 🎯 目標說明

### 核心目標

實現 **Weekly Pipeline Orchestrator**，完成週報生成的完整自動化流程，並整合 CuratorWeeklyRunner 的所有功能。

### 與 Stage 10 的關係

- **Stage 10**: 實作了 `CuratorWeeklyRunner` 類，包含週報生成的所有邏輯
- **Stage 11**: 實作 `WeeklyPipelineOrchestrator`，提供：
  - 命令行介面 (CLI)
  - 參數解析與驗證
  - 錯誤處理與日誌
  - 統計數據收集
  - 便捷的執行入口

### 具體功能

1. **命令行介面**
   - 支援 `--dry-run` 測試模式
   - 支援自訂週期 `--week-start` / `--week-end`
   - 支援指定收件人 `--recipients`
   - 支援詳細日誌 `--verbose`

2. **執行流程編排**
   - 呼叫 `CuratorWeeklyRunner.generate_weekly_report()`
   - 收集執行統計數據
   - 記錄完整執行日誌
   - 處理異常並提供友好錯誤訊息

3. **統計與報告**
   - 執行時間追蹤
   - 文章數量統計
   - 聚類結果統計
   - Email 發送狀態

4. **定時任務整合**
   - 提供 cron 配置範例
   - 支援腳本化執行

### 與其他模組的關係

```
┌────────────────────────────────────────────────────┐
│         Weekly Pipeline Orchestrator               │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │ 1. 解析命令行參數                         │    │
│  │    → argparse                            │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 2. 初始化配置與日誌                       │    │
│  │    → Config.from_env()                   │    │
│  │    → setup_logger()                      │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 3. 執行 Weekly Runner                    │    │
│  │    → CuratorWeeklyRunner(config)         │    │
│  │    → generate_weekly_report()            │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 4. 收集統計與報告                         │    │
│  │    → 執行時間                             │    │
│  │    → 文章數量                             │    │
│  │    → Email 狀態                           │    │
│  └──────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

---

## 📥 輸入/輸出定義

### 命令行參數

```bash
python -m src.orchestrator.weekly_runner [OPTIONS]
```

**選項**:

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--dry-run` | Flag | False | 測試模式，不發送郵件 |
| `--week-start` | String | 7天前 | 週期開始日期 (YYYY-MM-DD) |
| `--week-end` | String | 今天 | 週期結束日期 (YYYY-MM-DD) |
| `--recipients` | String | Config | 收件人列表（逗號分隔） |
| `--verbose` / `-v` | Flag | False | 詳細日誌模式 |

**範例**:

```bash
# 測試模式（不發送郵件）
python -m src.orchestrator.weekly_runner --dry-run

# 生產模式（發送郵件）
python -m src.orchestrator.weekly_runner

# 自訂週期
python -m src.orchestrator.weekly_runner \
  --week-start 2025-11-18 \
  --week-end 2025-11-24

# 自訂收件人
python -m src.orchestrator.weekly_runner \
  --recipients "user1@example.com,user2@example.com"

# 詳細日誌
python -m src.orchestrator.weekly_runner --verbose
```

### 輸出

**1. 控制台輸出**:

```
============================================================
InsightCosmos Weekly Pipeline
============================================================

Week Period: 2025-11-18 to 2025-11-24
Mode: Production (Email will be sent)

[2025-11-25 10:00:00] INFO: Starting Weekly Pipeline...
[2025-11-25 10:00:01] INFO: Querying weekly articles...
[2025-11-25 10:00:02] INFO: Found 52 articles (48 analyzed, 25 high-priority)
[2025-11-25 10:00:03] INFO: Performing vector clustering...
[2025-11-25 10:00:05] INFO: Found 4 topic clusters
[2025-11-25 10:00:06] INFO: Analyzing trends...
[2025-11-25 10:00:08] INFO: Identified 3 hot trends, 2 emerging topics
[2025-11-25 10:00:09] INFO: Generating report with LLM...
[2025-11-25 10:00:35] INFO: Formatting HTML and text emails...
[2025-11-25 10:00:36] INFO: Sending email to sourcecor103@gmail.com...
[2025-11-25 10:00:38] INFO: Email sent successfully!

============================================================
✓ Weekly Pipeline Completed Successfully

Stats:
  Duration: 38.2s
  Articles: 52 total, 48 analyzed
  Clusters: 4 topics
  Hot Trends: 3
  Emerging Topics: 2
  Email Sent: True
============================================================
```

**2. 返回值** (Python API):

```python
{
    "status": "success",
    "stats": {
        "duration": 38.2,
        "week_start": "2025-11-18",
        "week_end": "2025-11-24",
        "total_articles": 52,
        "analyzed_articles": 48,
        "high_priority_articles": 25,
        "num_clusters": 4,
        "hot_trends": 3,
        "emerging_topics": 2,
        "email_sent": True,
        "recipients": ["sourcecor103@gmail.com"]
    },
    "report_preview": {
        "subject": "...",
        "week_summary": "...",
        "top_cluster": "..."
    }
}
```

**錯誤時**:

```python
{
    "status": "error",
    "error_type": "InsufficientDataError",
    "error_message": "Insufficient articles for weekly report (found: 5, required: 20)",
    "suggestion": "Collect more articles or adjust date range",
    "stats": {
        "duration": 2.1,
        "total_articles": 5,
        "error_stage": "data_collection"
    }
}
```

---

## 🏗️ 技術設計

### 整體架構

```
┌──────────────────────────────────────────────────────┐
│           weekly_runner.py (CLI Entry)               │
│                                                      │
│  main()                                              │
│    ↓                                                 │
│  parse_args()  →  argparse                          │
│    ↓                                                 │
│  WeeklyPipelineOrchestrator                         │
│    ↓                                                 │
│  run_weekly_pipeline()                              │
│    │                                                 │
│    ├─→ CuratorWeeklyRunner.generate_weekly_report() │
│    │                                                 │
│    └─→ collect_stats() + log_results()              │
└──────────────────────────────────────────────────────┘
```

### 與 Daily Pipeline 的對比

| 特性 | Daily Pipeline | Weekly Pipeline |
|------|----------------|-----------------|
| **執行頻率** | 每天 | 每週 |
| **核心 Agent** | Scout → Analyst → Curator | Curator (數據已存在) |
| **處理階段** | 3 個 (收集、分析、生成) | 1 個 (生成報告) |
| **資料來源** | RSS + Search (即時) | Memory (過去7天) |
| **複雜度** | 高（多 Agent 協作） | 中（單一 Runner） |
| **執行時間** | 4-5 分鐘 | < 1 分鐘 |
| **失敗風險** | 高（外部 API 依賴） | 低（僅 Memory + LLM） |

### 依賴關係

**現有模組（無需新增）**:

```python
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.agents.curator_weekly import CuratorWeeklyRunner
```

**標準庫**:

```python
import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
```

---

## 🎨 Weekly Pipeline Orchestrator 設計

### 類設計

**文件**: `src/orchestrator/weekly_runner.py`

**類**: `WeeklyPipelineOrchestrator`

```python
class WeeklyPipelineOrchestrator:
    """
    週報流程編排器

    負責 Weekly Pipeline 的執行編排，提供命令行介面、
    錯誤處理、統計收集等功能。

    Attributes:
        config (Config): 配置對象
        logger (Logger): 日誌記錄器
        stats (dict): 執行統計
    """

    def __init__(self, config: Optional[Config] = None):
        """
        初始化編排器

        Args:
            config: 配置對象（可選，默認從環境載入）
        """
        self.config = config or Config.from_env()
        self.logger = setup_logger("WeeklyPipeline")
        self.stats = {
            "duration": 0.0,
            "week_start": None,
            "week_end": None,
            "total_articles": 0,
            "analyzed_articles": 0,
            "high_priority_articles": 0,
            "num_clusters": 0,
            "hot_trends": 0,
            "emerging_topics": 0,
            "email_sent": False,
            "recipients": []
        }

    def run_weekly_pipeline(
        self,
        week_start: Optional[str] = None,
        week_end: Optional[str] = None,
        dry_run: bool = False,
        recipients: Optional[List[str]] = None
    ) -> dict:
        """
        執行完整週報流程

        Args:
            week_start: 週期開始日期 (YYYY-MM-DD)
            week_end: 週期結束日期 (YYYY-MM-DD)
            dry_run: 是否為測試模式（不發送郵件）
            recipients: 收件人列表（覆蓋配置）

        Returns:
            dict: 執行結果與統計數據
        """
        start_time = time.time()

        try:
            # 1. 參數驗證與處理
            week_start, week_end = self._validate_dates(week_start, week_end)
            self.stats["week_start"] = week_start
            self.stats["week_end"] = week_end

            # 2. 顯示執行資訊
            self._print_header(week_start, week_end, dry_run)

            # 3. 執行 Weekly Runner
            self.logger.info("Starting Weekly Pipeline...")
            runner = CuratorWeeklyRunner(self.config)
            result = runner.generate_weekly_report(
                week_start=week_start,
                week_end=week_end,
                dry_run=dry_run
            )

            # 4. 檢查執行結果
            if result["status"] != "success":
                raise Exception(result.get("error_message", "Unknown error"))

            # 5. 收集統計數據
            self._collect_stats(result)

            # 6. 顯示成功結果
            self.stats["duration"] = time.time() - start_time
            self._print_success()

            return {
                "status": "success",
                "stats": self.stats,
                "report_preview": {
                    "subject": result.get("subject", ""),
                    "recipients": result.get("recipients", [])
                }
            }

        except Exception as e:
            # 錯誤處理
            self.stats["duration"] = time.time() - start_time
            self.logger.error(f"Weekly Pipeline failed: {e}")
            self._print_error(e)

            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stats": self.stats
            }

    def _validate_dates(
        self,
        week_start: Optional[str],
        week_end: Optional[str]
    ) -> tuple:
        """
        驗證與處理日期參數

        Args:
            week_start: 週期開始日期
            week_end: 週期結束日期

        Returns:
            tuple: (week_start, week_end) 字串
        """
        # 默認值：過去 7 天
        if week_end is None:
            week_end = datetime.now().strftime("%Y-%m-%d")
        if week_start is None:
            end_date = datetime.strptime(week_end, "%Y-%m-%d")
            start_date = end_date - timedelta(days=7)
            week_start = start_date.strftime("%Y-%m-%d")

        # 驗證日期格式
        try:
            datetime.strptime(week_start, "%Y-%m-%d")
            datetime.strptime(week_end, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}. Use YYYY-MM-DD")

        # 驗證邏輯順序
        if week_start >= week_end:
            raise ValueError(f"week_start ({week_start}) must be before week_end ({week_end})")

        return week_start, week_end

    def _collect_stats(self, result: dict):
        """
        從 Runner 結果收集統計數據

        Args:
            result: CuratorWeeklyRunner 的返回結果
        """
        # 從 result 中提取統計數據
        # (具體欄位取決於 CuratorWeeklyRunner 的實作)
        self.stats["total_articles"] = result.get("total_articles", 0)
        self.stats["analyzed_articles"] = result.get("analyzed_articles", 0)
        self.stats["high_priority_articles"] = result.get("high_priority_articles", 0)
        self.stats["num_clusters"] = result.get("num_clusters", 0)
        self.stats["hot_trends"] = result.get("hot_trends", 0)
        self.stats["emerging_topics"] = result.get("emerging_topics", 0)
        self.stats["email_sent"] = result.get("email_sent", False)
        self.stats["recipients"] = result.get("recipients", [])

    def _print_header(self, week_start: str, week_end: str, dry_run: bool):
        """顯示執行資訊標題"""
        print("=" * 60)
        print("InsightCosmos Weekly Pipeline")
        print("=" * 60)
        print()
        print(f"Week Period: {week_start} to {week_end}")
        print(f"Mode: {'Dry Run (No Email)' if dry_run else 'Production (Email will be sent)'}")
        print()

    def _print_success(self):
        """顯示成功結果"""
        print()
        print("=" * 60)
        print("✓ Weekly Pipeline Completed Successfully")
        print()
        print("Stats:")
        print(f"  Duration: {self.stats['duration']:.1f}s")
        print(f"  Articles: {self.stats['total_articles']} total, {self.stats['analyzed_articles']} analyzed")
        print(f"  Clusters: {self.stats['num_clusters']} topics")
        print(f"  Hot Trends: {self.stats['hot_trends']}")
        print(f"  Emerging Topics: {self.stats['emerging_topics']}")
        print(f"  Email Sent: {self.stats['email_sent']}")
        print("=" * 60)

    def _print_error(self, error: Exception):
        """顯示錯誤訊息"""
        print()
        print("=" * 60)
        print("✗ Weekly Pipeline Failed")
        print()
        print(f"Error: {type(error).__name__}")
        print(f"Message: {str(error)}")
        print(f"Duration: {self.stats['duration']:.1f}s")
        print("=" * 60)
```

### 命令行介面

```python
def parse_args():
    """
    解析命令行參數

    Returns:
        argparse.Namespace: 解析後的參數
    """
    parser = argparse.ArgumentParser(
        description="InsightCosmos Weekly Pipeline - 週報自動化生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 測試模式（不發送郵件）
  python -m src.orchestrator.weekly_runner --dry-run

  # 生產模式（發送郵件）
  python -m src.orchestrator.weekly_runner

  # 自訂週期
  python -m src.orchestrator.weekly_runner --week-start 2025-11-18 --week-end 2025-11-24

  # 詳細日誌
  python -m src.orchestrator.weekly_runner --verbose
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="測試模式，不發送郵件"
    )

    parser.add_argument(
        "--week-start",
        type=str,
        default=None,
        help="週期開始日期 (YYYY-MM-DD)，默認為 7 天前"
    )

    parser.add_argument(
        "--week-end",
        type=str,
        default=None,
        help="週期結束日期 (YYYY-MM-DD)，默認為今天"
    )

    parser.add_argument(
        "--recipients",
        type=str,
        default=None,
        help="收件人列表（逗號分隔），覆蓋配置文件"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細日誌模式"
    )

    return parser.parse_args()


def main():
    """
    主函數入口

    使用方式：
        python -m src.orchestrator.weekly_runner [OPTIONS]
    """
    # 解析參數
    args = parse_args()

    # 設置日誌級別
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    # 創建編排器
    orchestrator = WeeklyPipelineOrchestrator()

    # 處理收件人參數
    recipients = None
    if args.recipients:
        recipients = [r.strip() for r in args.recipients.split(",")]

    # 執行流程
    result = orchestrator.run_weekly_pipeline(
        week_start=args.week_start,
        week_end=args.week_end,
        dry_run=args.dry_run,
        recipients=recipients
    )

    # 返回適當的退出碼
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
```

---

## 🔄 與 Daily Pipeline 的對比

### 相似之處

1. **命令行介面**: 都支援 `--dry-run`, `--verbose` 等參數
2. **統計收集**: 都收集執行時間、文章數量等統計數據
3. **錯誤處理**: 都提供友好的錯誤訊息與退出碼
4. **日誌記錄**: 都使用統一的 Logger

### 差異之處

| 特性 | Daily Pipeline | Weekly Pipeline |
|------|----------------|-----------------|
| **複雜度** | 高（3 個階段） | 低（1 個階段） |
| **參數** | 無自訂參數 | 支援自訂週期 |
| **執行時間** | 4-5 分鐘 | < 1 分鐘 |
| **資料來源** | 外部 API | Memory |
| **失敗風險** | 高 | 低 |
| **重試機制** | 需要 | 不需要 |

---

## 🛠️ 實作計劃

### 文件結構

```
src/orchestrator/
├─ __init__.py                 # 已存在
├─ daily_runner.py             # 已存在（Stage 9）
├─ weekly_runner.py            # 新增（Stage 11）
└─ utils.py                    # 已存在（共用工具）
```

### 開發步驟

#### Step 1: 創建 weekly_runner.py 骨架 (30 分鐘)

1. 創建文件結構
2. 實作 `WeeklyPipelineOrchestrator` 類骨架
3. 實作 `parse_args()` 函數
4. 實作 `main()` 入口函數

#### Step 2: 實作核心方法 (1 小時)

1. 實作 `run_weekly_pipeline()` 主流程
2. 實作 `_validate_dates()` 日期驗證
3. 實作 `_collect_stats()` 統計收集
4. 整合 `CuratorWeeklyRunner`

#### Step 3: 實作顯示方法 (30 分鐘)

1. 實作 `_print_header()` 標題顯示
2. 實作 `_print_success()` 成功顯示
3. 實作 `_print_error()` 錯誤顯示

#### Step 4: 測試與驗證 (1 小時)

1. 編寫單元測試
2. 執行端到端測試
3. 測試錯誤處理
4. 測試不同參數組合

#### Step 5: 文檔與總結 (30 分鐘)

1. 更新 `src/orchestrator/__init__.py`
2. 編寫實作筆記
3. 編寫測試報告
4. 更新 README.md

---

## 🧪 測試策略

### 單元測試

**文件**: `tests/unit/test_weekly_runner.py`

**測試案例**:

1. `test_orchestrator_initialization()` - 初始化測試
2. `test_validate_dates_default()` - 日期驗證（默認值）
3. `test_validate_dates_custom()` - 日期驗證（自訂值）
4. `test_validate_dates_invalid()` - 日期驗證（無效值）
5. `test_collect_stats()` - 統計收集
6. `test_run_pipeline_success()` - 成功流程（Mock）
7. `test_run_pipeline_error()` - 錯誤處理（Mock）

### 整合測試

**文件**: `tests/integration/test_weekly_pipeline.py`

**測試案例**:

1. `test_full_pipeline_dry_run()` - 完整流程（測試模式）
2. `test_full_pipeline_custom_dates()` - 自訂日期範圍
3. `test_pipeline_with_insufficient_data()` - 資料不足處理
4. `test_pipeline_with_verbose_logging()` - 詳細日誌模式

### 端到端測試（手動）

**測試案例**:

1. **測試模式執行**
   ```bash
   python -m src.orchestrator.weekly_runner --dry-run --verbose
   ```
   預期：完整流程執行，不發送郵件，顯示詳細日誌

2. **生產模式執行**
   ```bash
   python -m src.orchestrator.weekly_runner
   ```
   預期：完整流程執行，發送郵件到指定信箱

3. **自訂週期執行**
   ```bash
   python -m src.orchestrator.weekly_runner \
     --week-start 2025-11-18 \
     --week-end 2025-11-24 \
     --dry-run
   ```
   預期：查詢指定週期的文章並生成報告

4. **錯誤處理驗證**
   ```bash
   # 無效日期格式
   python -m src.orchestrator.weekly_runner --week-start invalid-date

   # 日期邏輯錯誤
   python -m src.orchestrator.weekly_runner \
     --week-start 2025-11-25 \
     --week-end 2025-11-18
   ```
   預期：顯示友好的錯誤訊息

---

## ✅ 驗收標準

### 功能驗收

- [ ] **命令行介面** - 所有參數正確解析
- [ ] **日期驗證** - 能正確驗證與處理日期參數
- [ ] **流程執行** - 能成功呼叫 CuratorWeeklyRunner
- [ ] **統計收集** - 能收集完整的執行統計
- [ ] **錯誤處理** - 能友好處理各種錯誤情況
- [ ] **日誌記錄** - 能記錄完整執行過程
- [ ] **顯示格式** - 控制台輸出清晰美觀

### 測試驗收

- [ ] **單元測試通過率** - 100%
- [ ] **整合測試通過率** - >= 90%
- [ ] **端到端測試** - 所有場景通過
- [ ] **錯誤測試** - 覆蓋主要錯誤情況

### 使用性驗收

- [ ] **命令行友好** - 參數清晰，幫助文件完整
- [ ] **執行快速** - 總執行時間 < 1 分鐘
- [ ] **訊息清晰** - 執行過程與結果易於理解
- [ ] **錯誤友好** - 錯誤訊息提供修正建議

---

## ⚠️ 風險與對策

### 風險 1: CuratorWeeklyRunner 介面變更

**風險描述**: Stage 10 的 Runner 介面可能與預期不符

**影響**: Orchestrator 無法正確呼叫 Runner

**對策**:
1. 先檢查 CuratorWeeklyRunner 的實際介面
2. 根據實際介面調整 Orchestrator 實作
3. 如有不合理處，反饋改進 Runner

**優先級**: 高

---

### 風險 2: 統計數據不完整

**風險描述**: Runner 返回的統計數據不夠詳細

**影響**: Orchestrator 無法顯示完整統計

**對策**:
1. 明確定義需要的統計欄位
2. 如 Runner 未提供，補充計算邏輯
3. 或簡化 Orchestrator 的統計顯示

**優先級**: 中

---

### 風險 3: 日期範圍過大

**風險描述**: 使用者設定過長的日期範圍（如 30 天）

**影響**: 文章數量過多，影響性能與報告品質

**對策**:
1. 設定最大日期範圍限制（如 14 天）
2. 超過限制時顯示警告並使用默認值
3. 在文檔中說明建議的日期範圍

**優先級**: 低

---

## 📚 參考資料

### 專案內部文件

- `src/orchestrator/daily_runner.py` - Daily Pipeline 實作參考
- `src/agents/curator_weekly.py` - CuratorWeeklyRunner 實作
- `docs/planning/stage9_daily_pipeline.md` - Daily Pipeline 設計
- `docs/planning/stage10_curator_weekly.md` - Weekly Curator 設計

### Python 官方文件

- [argparse](https://docs.python.org/3/library/argparse.html) - 命令行參數解析
- [datetime](https://docs.python.org/3/library/datetime.html) - 日期時間處理

---

## 🎯 下一步

完成 Stage 11 後，接續：

**Stage 12**: 質量保證與優化（QA & Optimization）
- 完善測試覆蓋
- 性能優化
- 文檔完善
- Phase 1 最終驗收

---

## 📋 Checklist

### 規劃階段
- [x] 創建規劃文件
- [x] 定義輸入/輸出介面
- [x] 設計 Orchestrator 架構
- [x] 設計命令行介面
- [x] 準備測試案例

### 實作階段
- [ ] 創建 weekly_runner.py 骨架
- [ ] 實作 WeeklyPipelineOrchestrator 類
- [ ] 實作命令行介面
- [ ] 實作顯示方法
- [ ] 整合 CuratorWeeklyRunner

### 驗證階段
- [ ] 編寫單元測試
- [ ] 編寫整合測試
- [ ] 執行端到端測試
- [ ] 驗證錯誤處理
- [ ] 更新文檔

---

**創建者**: Ray 張瑞涵
**創建日期**: 2025-11-25
**最後更新**: 2025-11-25
**狀態**: 規劃完成，待實作
