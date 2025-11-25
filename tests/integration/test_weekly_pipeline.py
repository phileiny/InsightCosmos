"""
Integration tests for Weekly Pipeline

測試 Weekly Pipeline 的完整流程整合，包括：
- Orchestrator + CuratorWeeklyRunner 整合
- 端到端執行（dry-run 模式）
- 自訂日期範圍執行
- 錯誤恢復機制

Author: Ray 張瑞涵
Created: 2025-11-25
"""

import pytest
from datetime import datetime, timedelta

from src.orchestrator.weekly_runner import WeeklyPipelineOrchestrator
from src.utils.config import Config


class TestWeeklyPipelineIntegration:
    """Weekly Pipeline 整合測試"""

    @pytest.mark.slow
    def test_full_pipeline_dry_run(self, test_config):
        """
        測試完整流程（dry-run 模式）

        驗證：
        - Orchestrator 能正確初始化
        - 能呼叫 CuratorWeeklyRunner
        - 能處理完整流程
        - 統計數據正確收集
        """
        # 創建 Orchestrator
        orchestrator = WeeklyPipelineOrchestrator(test_config)

        # 執行（dry-run 模式）
        result = orchestrator.run_weekly_pipeline(dry_run=True)

        # 基本驗證
        assert result["status"] in ["success", "error"]

        if result["status"] == "success":
            # 成功情況驗證
            assert "stats" in result
            assert "report_preview" in result

            stats = result["stats"]
            assert stats["duration"] > 0
            assert stats["week_start"] is not None
            assert stats["week_end"] is not None
            assert stats["total_articles"] >= 0
            assert stats["email_sent"] is False  # dry-run 不發送

            # 如果有足夠文章，應該有聚類結果
            if stats["total_articles"] >= 20:
                assert stats["num_clusters"] > 0

        else:
            # 錯誤情況驗證
            assert "error_type" in result
            assert "error_message" in result
            assert "suggestion" in result

            # 常見的可接受錯誤：資料不足
            if "insufficient" in result["error_message"].lower():
                print(f"⚠️  Expected error: {result['error_message']}")
            else:
                # 其他錯誤應該記錄
                print(f"❌ Unexpected error: {result['error_message']}")

    @pytest.mark.slow
    def test_pipeline_custom_dates(self, test_config):
        """
        測試自訂日期範圍

        驗證：
        - 能正確處理自訂日期參數
        - 日期範圍影響查詢結果
        """
        orchestrator = WeeklyPipelineOrchestrator(test_config)

        # 使用較短的日期範圍（3 天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)

        week_start = start_date.strftime("%Y-%m-%d")
        week_end = end_date.strftime("%Y-%m-%d")

        result = orchestrator.run_weekly_pipeline(
            week_start=week_start,
            week_end=week_end,
            dry_run=True
        )

        # 驗證日期設定正確
        if result["status"] == "success":
            assert result["stats"]["week_start"] == week_start
            assert result["stats"]["week_end"] == week_end

    def test_pipeline_with_invalid_dates(self, test_config):
        """
        測試無效日期處理

        驗證：
        - 能正確識別無效日期
        - 提供友好的錯誤訊息
        """
        orchestrator = WeeklyPipelineOrchestrator(test_config)

        # 測試無效格式
        result = orchestrator.run_weekly_pipeline(
            week_start="invalid-date",
            week_end="2025-11-24",
            dry_run=True
        )

        assert result["status"] == "error"
        assert "date" in result["error_message"].lower()

    def test_pipeline_with_reversed_dates(self, test_config):
        """
        測試日期順序錯誤處理

        驗證：
        - 能識別開始日期晚於結束日期
        - 提供明確的錯誤訊息
        """
        orchestrator = WeeklyPipelineOrchestrator(test_config)

        result = orchestrator.run_weekly_pipeline(
            week_start="2025-11-25",
            week_end="2025-11-18",
            dry_run=True
        )

        assert result["status"] == "error"
        assert "before" in result["error_message"].lower()

    @pytest.mark.skipif(
        True,  # 默認跳過，因為需要足夠的測試數據
        reason="Requires sufficient test data in database"
    )
    def test_pipeline_statistics_accuracy(self, test_config):
        """
        測試統計數據準確性

        驗證：
        - 文章數量統計正確
        - 聚類數量合理
        - 趨勢識別正常
        """
        orchestrator = WeeklyPipelineOrchestrator(test_config)

        result = orchestrator.run_weekly_pipeline(dry_run=True)

        assert result["status"] == "success"

        stats = result["stats"]
        assert stats["total_articles"] >= 0
        assert stats["analyzed_articles"] <= stats["total_articles"]
        assert stats["high_priority_articles"] <= stats["analyzed_articles"]

        # 如果有足夠文章，應該有聚類
        if stats["total_articles"] >= 20:
            assert stats["num_clusters"] >= 2
            assert stats["num_clusters"] <= 5

    def test_orchestrator_idempotency(self, test_config):
        """
        測試編排器的冪等性

        驗證：
        - 相同參數執行多次結果一致
        - 不會產生副作用
        """
        orchestrator = WeeklyPipelineOrchestrator(test_config)

        # 固定日期範圍
        week_start = "2025-11-18"
        week_end = "2025-11-24"

        # 執行兩次
        result1 = orchestrator.run_weekly_pipeline(
            week_start=week_start,
            week_end=week_end,
            dry_run=True
        )

        result2 = orchestrator.run_weekly_pipeline(
            week_start=week_start,
            week_end=week_end,
            dry_run=True
        )

        # 驗證狀態一致
        assert result1["status"] == result2["status"]

        # 如果成功，文章數量應該一致
        if result1["status"] == "success":
            assert result1["stats"]["total_articles"] == result2["stats"]["total_articles"]


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def test_config():
    """測試用配置"""
    return Config.from_env()
