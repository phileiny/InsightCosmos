"""
Unit tests for Weekly Pipeline Orchestrator

測試 Weekly Runner 的核心功能，包括：
- 初始化
- 日期驗證
- 統計收集
- 錯誤處理

Author: Ray 張瑞涵
Created: 2025-11-25
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.orchestrator.weekly_runner import (
    WeeklyPipelineOrchestrator,
    parse_args
)
from src.utils.config import Config


class TestWeeklyPipelineOrchestrator:
    """測試 WeeklyPipelineOrchestrator 類"""

    def test_orchestrator_initialization(self, mock_config):
        """測試編排器初始化"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        assert orchestrator.config == mock_config
        assert orchestrator.logger is not None
        assert isinstance(orchestrator.stats, dict)
        assert orchestrator.stats["duration"] == 0.0
        assert orchestrator.stats["total_articles"] == 0

    def test_validate_dates_default(self, mock_config):
        """測試日期驗證 - 默認值"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        # 默認應該是過去 7 天
        week_start, week_end = orchestrator._validate_dates(None, None)

        # 驗證格式
        assert len(week_start) == 10  # YYYY-MM-DD
        assert len(week_end) == 10

        # 驗證邏輯
        start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        end_dt = datetime.strptime(week_end, "%Y-%m-%d")
        assert (end_dt - start_dt).days == 7

    def test_validate_dates_custom(self, mock_config):
        """測試日期驗證 - 自訂值"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        week_start = "2025-11-18"
        week_end = "2025-11-24"

        result_start, result_end = orchestrator._validate_dates(week_start, week_end)

        assert result_start == week_start
        assert result_end == week_end

    def test_validate_dates_invalid_format(self, mock_config):
        """測試日期驗證 - 無效格式"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        with pytest.raises(ValueError, match="Invalid date format"):
            orchestrator._validate_dates("invalid-date", "2025-11-24")

    def test_validate_dates_invalid_order(self, mock_config):
        """測試日期驗證 - 順序錯誤"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        with pytest.raises(ValueError, match="must be before"):
            orchestrator._validate_dates("2025-11-25", "2025-11-18")

    def test_validate_dates_range_warning(self, mock_config, capsys):
        """測試日期驗證 - 範圍過大警告"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        # 超過 14 天應該產生警告（但不影響執行）
        week_start = "2025-11-01"
        week_end = "2025-11-25"

        # 應該成功執行（不拋出異常）
        result_start, result_end = orchestrator._validate_dates(week_start, week_end)

        # 驗證返回值正確
        assert result_start == week_start
        assert result_end == week_end

        # 驗證日期範圍確實超過 14 天
        from datetime import datetime
        start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        end_dt = datetime.strptime(week_end, "%Y-%m-%d")
        assert (end_dt - start_dt).days > 14

    def test_collect_stats(self, mock_config):
        """測試統計收集"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        mock_result = {
            "total_articles": 52,
            "analyzed_articles": 48,
            "high_priority_articles": 25,
            "num_clusters": 4,
            "hot_trends": 3,
            "emerging_topics": 2,
            "email_sent": True,
            "recipients": ["test@example.com"]
        }

        orchestrator._collect_stats(mock_result)

        assert orchestrator.stats["total_articles"] == 52
        assert orchestrator.stats["analyzed_articles"] == 48
        assert orchestrator.stats["high_priority_articles"] == 25
        assert orchestrator.stats["num_clusters"] == 4
        assert orchestrator.stats["hot_trends"] == 3
        assert orchestrator.stats["emerging_topics"] == 2
        assert orchestrator.stats["email_sent"] is True
        assert orchestrator.stats["recipients"] == ["test@example.com"]

    def test_get_error_suggestion_insufficient_data(self, mock_config):
        """測試錯誤建議 - 資料不足"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        error = Exception("Insufficient articles for report")
        suggestion = orchestrator._get_error_suggestion(error)

        assert "adjust date range" in suggestion.lower() or "collect more" in suggestion.lower()

    def test_get_error_suggestion_date_error(self, mock_config):
        """測試錯誤建議 - 日期錯誤"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        error = ValueError("Invalid date format")
        suggestion = orchestrator._get_error_suggestion(error)

        assert "date format" in suggestion.lower()

    def test_get_error_suggestion_database_error(self, mock_config):
        """測試錯誤建議 - 資料庫錯誤"""
        orchestrator = WeeklyPipelineOrchestrator(mock_config)

        error = Exception("Database connection failed")
        suggestion = orchestrator._get_error_suggestion(error)

        assert "database" in suggestion.lower()

    @patch('src.orchestrator.weekly_runner.CuratorWeeklyRunner')
    def test_run_pipeline_success(self, mock_runner_class, mock_config):
        """測試成功流程 (Mock)"""
        # Mock Runner
        mock_runner = Mock()
        mock_runner.generate_weekly_report.return_value = {
            "status": "success",
            "total_articles": 52,
            "analyzed_articles": 48,
            "high_priority_articles": 25,
            "num_clusters": 4,
            "hot_trends": 3,
            "emerging_topics": 2,
            "email_sent": True,
            "recipients": ["test@example.com"],
            "subject": "Weekly Report"
        }
        mock_runner_class.return_value = mock_runner

        # 執行
        orchestrator = WeeklyPipelineOrchestrator(mock_config)
        result = orchestrator.run_weekly_pipeline(dry_run=True)

        # 驗證
        assert result["status"] == "success"
        assert result["stats"]["total_articles"] == 52
        assert result["stats"]["num_clusters"] == 4
        assert result["report_preview"]["subject"] == "Weekly Report"

    @patch('src.orchestrator.weekly_runner.CuratorWeeklyRunner')
    def test_run_pipeline_error(self, mock_runner_class, mock_config):
        """測試錯誤處理 (Mock)"""
        # Mock Runner 拋出異常
        mock_runner = Mock()
        mock_runner.generate_weekly_report.side_effect = Exception("Test error")
        mock_runner_class.return_value = mock_runner

        # 執行
        orchestrator = WeeklyPipelineOrchestrator(mock_config)
        result = orchestrator.run_weekly_pipeline(dry_run=True)

        # 驗證
        assert result["status"] == "error"
        assert result["error_type"] == "Exception"
        assert "Test error" in result["error_message"]
        assert "suggestion" in result


class TestParseArgs:
    """測試命令行參數解析"""

    def test_parse_args_default(self, monkeypatch):
        """測試默認參數"""
        monkeypatch.setattr("sys.argv", ["weekly_runner.py"])
        args = parse_args()

        assert args.dry_run is False
        assert args.week_start is None
        assert args.week_end is None
        assert args.recipients is None
        assert args.verbose is False

    def test_parse_args_dry_run(self, monkeypatch):
        """測試 dry-run 參數"""
        monkeypatch.setattr("sys.argv", ["weekly_runner.py", "--dry-run"])
        args = parse_args()

        assert args.dry_run is True

    def test_parse_args_custom_dates(self, monkeypatch):
        """測試自訂日期"""
        monkeypatch.setattr("sys.argv", [
            "weekly_runner.py",
            "--week-start", "2025-11-18",
            "--week-end", "2025-11-24"
        ])
        args = parse_args()

        assert args.week_start == "2025-11-18"
        assert args.week_end == "2025-11-24"

    def test_parse_args_recipients(self, monkeypatch):
        """測試收件人參數"""
        monkeypatch.setattr("sys.argv", [
            "weekly_runner.py",
            "--recipients", "user1@example.com,user2@example.com"
        ])
        args = parse_args()

        assert args.recipients == "user1@example.com,user2@example.com"

    def test_parse_args_verbose(self, monkeypatch):
        """測試詳細日誌參數"""
        monkeypatch.setattr("sys.argv", ["weekly_runner.py", "--verbose"])
        args = parse_args()

        assert args.verbose is True

    def test_parse_args_verbose_short(self, monkeypatch):
        """測試詳細日誌參數 (短形式)"""
        monkeypatch.setattr("sys.argv", ["weekly_runner.py", "-v"])
        args = parse_args()

        assert args.verbose is True


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def mock_config():
    """Mock Config 對象"""
    config = Mock(spec=Config)
    config.user_name = "TestUser"
    config.user_email = "test@example.com"
    config.user_interests = ["AI", "Robotics"]
    config.database_path = ":memory:"
    config.google_api_key = "test_key"
    config.email_account = "test@example.com"
    config.email_password = "test_password"
    return config
