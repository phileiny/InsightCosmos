"""
Weekly Pipeline Orchestrator

負責完整週報自動化流程的執行編排，提供命令行介面、
錯誤處理、統計收集等功能。

使用方式:
    # 測試模式（不發送郵件）
    python -m src.orchestrator.weekly_runner --dry-run

    # 生產模式（發送郵件）
    python -m src.orchestrator.weekly_runner

    # 自訂週期
    python -m src.orchestrator.weekly_runner --week-start 2025-11-18 --week-end 2025-11-24

Author: Ray 張瑞涵
Created: 2025-11-25
Version: 1.0.0
"""

import sys
import argparse
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# 確保可以導入專案模組
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.agents.curator_weekly import CuratorWeeklyRunner


class WeeklyPipelineOrchestrator:
    """
    週報流程編排器

    負責 Weekly Pipeline 的執行編排，提供命令行介面、
    錯誤處理、統計收集等功能。

    Attributes:
        config (Config): 配置對象
        logger (Logger): 日誌記錄器
        stats (dict): 執行統計

    Example:
        >>> orchestrator = WeeklyPipelineOrchestrator()
        >>> result = orchestrator.run_weekly_pipeline(dry_run=True)
        >>> print(result["status"])
        success
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
    ) -> Dict[str, Any]:
        """
        執行完整週報流程

        Args:
            week_start: 週期開始日期 (YYYY-MM-DD)，默認為 7 天前
            week_end: 週期結束日期 (YYYY-MM-DD)，默認為今天
            dry_run: 是否為測試模式（不發送郵件）
            recipients: 收件人列表（覆蓋配置）

        Returns:
            dict: {
                "status": "success" | "error",
                "stats": {...},
                "report_preview": {...},  # 僅成功時
                "error_type": str,        # 僅錯誤時
                "error_message": str,     # 僅錯誤時
                "suggestion": str         # 僅錯誤時
            }

        Example:
            >>> orchestrator = WeeklyPipelineOrchestrator()
            >>> result = orchestrator.run_weekly_pipeline(dry_run=True)
            >>> print(f"Status: {result['status']}")
            Status: success
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
                "suggestion": self._get_error_suggestion(e),
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

        Raises:
            ValueError: 日期格式錯誤或邏輯錯誤
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
            start_dt = datetime.strptime(week_start, "%Y-%m-%d")
            end_dt = datetime.strptime(week_end, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}. Use YYYY-MM-DD")

        # 驗證邏輯順序
        if start_dt >= end_dt:
            raise ValueError(
                f"week_start ({week_start}) must be before week_end ({week_end})"
            )

        # 驗證日期範圍（建議不超過 14 天）
        days_diff = (end_dt - start_dt).days
        if days_diff > 14:
            self.logger.warning(
                f"Date range is {days_diff} days (recommended: <= 14 days). "
                f"Large ranges may affect report quality."
            )

        return week_start, week_end

    def _collect_stats(self, result: Dict[str, Any]):
        """
        從 Runner 結果收集統計數據

        Args:
            result: CuratorWeeklyRunner 的返回結果
        """
        # 從 result 中提取統計數據
        self.stats["total_articles"] = result.get("total_articles", 0)
        self.stats["analyzed_articles"] = result.get("analyzed_articles", 0)
        self.stats["high_priority_articles"] = result.get("high_priority_articles", 0)
        self.stats["num_clusters"] = result.get("num_clusters", 0)
        self.stats["hot_trends"] = result.get("hot_trends", 0)
        self.stats["emerging_topics"] = result.get("emerging_topics", 0)
        self.stats["email_sent"] = result.get("email_sent", False)
        self.stats["recipients"] = result.get("recipients", [])

    def _get_error_suggestion(self, error: Exception) -> str:
        """
        根據錯誤類型提供修正建議

        Args:
            error: 異常對象

        Returns:
            str: 修正建議
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        if "insufficient" in error_msg or "not enough" in error_msg:
            return "Try adjusting date range or collect more articles first"
        elif "date" in error_msg:
            return "Check date format (YYYY-MM-DD) and ensure start < end"
        elif "database" in error_msg or "sqlite" in error_msg:
            return "Check database connection and ensure tables are initialized"
        elif "email" in error_msg or "smtp" in error_msg:
            return "Check email configuration in .env file"
        else:
            return "Check logs for details and ensure all dependencies are installed"

    def _print_header(self, week_start: str, week_end: str, dry_run: bool):
        """
        顯示執行資訊標題

        Args:
            week_start: 週期開始日期
            week_end: 週期結束日期
            dry_run: 是否為測試模式
        """
        print()
        print("=" * 60)
        print("InsightCosmos Weekly Pipeline")
        print("=" * 60)
        print()
        print(f"Week Period: {week_start} to {week_end}")
        mode = "Dry Run (No Email)" if dry_run else "Production (Email will be sent)"
        print(f"Mode: {mode}")
        print()

    def _print_success(self):
        """顯示成功結果"""
        print()
        print("=" * 60)
        print("✓ Weekly Pipeline Completed Successfully")
        print()
        print("Stats:")
        print(f"  Duration: {self.stats['duration']:.1f}s")
        print(f"  Articles: {self.stats['total_articles']} total, "
              f"{self.stats['analyzed_articles']} analyzed")
        print(f"  Clusters: {self.stats['num_clusters']} topics")
        print(f"  Hot Trends: {self.stats['hot_trends']}")
        print(f"  Emerging Topics: {self.stats['emerging_topics']}")
        print(f"  Email Sent: {self.stats['email_sent']}")
        if self.stats['recipients']:
            print(f"  Recipients: {', '.join(self.stats['recipients'])}")
        print("=" * 60)
        print()

    def _print_error(self, error: Exception):
        """
        顯示錯誤訊息

        Args:
            error: 異常對象
        """
        print()
        print("=" * 60)
        print("✗ Weekly Pipeline Failed")
        print()
        print(f"Error: {type(error).__name__}")
        print(f"Message: {str(error)}")
        print(f"Duration: {self.stats['duration']:.1f}s")
        print()
        suggestion = self._get_error_suggestion(error)
        print(f"Suggestion: {suggestion}")
        print("=" * 60)
        print()


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

    使用方式:
        python -m src.orchestrator.weekly_runner [OPTIONS]

    Example:
        $ python -m src.orchestrator.weekly_runner --dry-run
        ============================================================
        InsightCosmos Weekly Pipeline
        ============================================================

        Week Period: 2025-11-18 to 2025-11-25
        Mode: Dry Run (No Email)

        [執行過程日誌...]

        ============================================================
        ✓ Weekly Pipeline Completed Successfully
        ...
        ============================================================
    """
    # 解析參數
    args = parse_args()

    # 設置日誌級別
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    try:
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

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
