"""
單元測試: Daily Pipeline Orchestrator

測試 DailyPipelineOrchestrator 類的核心邏輯。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.daily_runner import DailyPipelineOrchestrator
from src.utils.config import Config
from src.memory.database import Database


@pytest.fixture
def mock_config():
    """創建 Mock 配置對象"""
    config = Mock(spec=Config)
    config.database_path = ":memory:"
    config.google_api_key = "test_api_key"
    config.email_account = "test@example.com"
    config.email_password = "test_password"
    config.user_name = "Test User"
    config.user_interests = "AI, Robotics"
    return config


@pytest.fixture
def orchestrator(mock_config):
    """創建 Orchestrator 實例"""
    with patch("src.orchestrator.daily_runner.Database") as mock_db_class:
        # Mock Database
        mock_db = Mock(spec=Database)
        mock_db_class.from_config.return_value = mock_db

        # Mock ArticleStore
        with patch("src.orchestrator.daily_runner.ArticleStore") as mock_article_store_class:
            mock_article_store = Mock()
            mock_article_store_class.return_value = mock_article_store

            # Mock EmbeddingStore
            with patch("src.orchestrator.daily_runner.EmbeddingStore") as mock_embedding_store_class:
                mock_embedding_store = Mock()
                mock_embedding_store_class.return_value = mock_embedding_store

                orchestrator = DailyPipelineOrchestrator(mock_config)
                orchestrator.db = mock_db
                orchestrator.article_store = mock_article_store
                orchestrator.embedding_store = mock_embedding_store

                return orchestrator


class TestDailyPipelineOrchestrator:
    """測試 DailyPipelineOrchestrator 類"""

    def test_initialization(self, mock_config):
        """測試初始化"""
        with patch("src.orchestrator.daily_runner.Database") as mock_db_class:
            mock_db = Mock()
            mock_db_class.from_config.return_value = mock_db

            with patch("src.orchestrator.daily_runner.ArticleStore"):
                with patch("src.orchestrator.daily_runner.EmbeddingStore"):
                    orchestrator = DailyPipelineOrchestrator(mock_config)

                    assert orchestrator.config == mock_config
                    assert orchestrator.stats["start_time"] is None
                    assert orchestrator.stats["end_time"] is None
                    assert orchestrator.stats["phase1_collected"] == 0
                    assert orchestrator.stats["phase2_analyzed"] == 0
                    assert orchestrator.stats["phase3_sent"] is False
                    assert orchestrator.stats["errors"] == []

    def test_get_summary_empty(self, orchestrator):
        """測試空摘要"""
        summary = orchestrator.get_summary()

        assert summary["success"] is False
        assert summary["stats"]["start_time"] is None
        assert summary["stats"]["end_time"] is None
        assert summary["stats"]["duration_seconds"] is None
        assert summary["stats"]["phase1_collected"] == 0
        assert summary["stats"]["phase2_analyzed"] == 0
        assert summary["stats"]["phase3_sent"] is False
        assert summary["errors"] == []

    def test_get_summary_with_data(self, orchestrator):
        """測試有數據的摘要"""
        # 設置統計數據
        orchestrator.stats["start_time"] = datetime(2025, 11, 24, 9, 0, 0)
        orchestrator.stats["end_time"] = datetime(2025, 11, 24, 9, 5, 0)
        orchestrator.stats["phase1_collected"] = 30
        orchestrator.stats["phase1_stored"] = 25
        orchestrator.stats["phase2_analyzed"] = 20
        orchestrator.stats["phase3_sent"] = True

        summary = orchestrator.get_summary()

        assert summary["success"] is True
        assert summary["stats"]["duration_seconds"] == 300.0  # 5 分鐘
        assert summary["stats"]["phase1_collected"] == 30
        assert summary["stats"]["phase1_stored"] == 25
        assert summary["stats"]["phase2_analyzed"] == 20
        assert summary["stats"]["phase3_sent"] is True

    def test_get_summary_with_errors(self, orchestrator):
        """測試有錯誤的摘要"""
        orchestrator.stats["phase1_stored"] = 25
        orchestrator.stats["phase2_analyzed"] = 20
        orchestrator.stats["phase3_sent"] = True
        orchestrator.stats["errors"] = [
            {"phase": "test", "error_type": "TestError", "error_message": "Test error"}
        ]

        summary = orchestrator.get_summary()

        assert summary["success"] is False  # 有錯誤，不算成功
        assert len(summary["errors"]) == 1

    def test_handle_error(self, orchestrator):
        """測試錯誤處理"""
        error = ValueError("Test error")
        orchestrator._handle_error("test_phase", error)

        assert len(orchestrator.stats["errors"]) == 1
        error_info = orchestrator.stats["errors"][0]
        assert error_info["phase"] == "test_phase"
        assert error_info["error_type"] == "ValueError"
        assert error_info["error_message"] == "Test error"
        assert "timestamp" in error_info

    def test_run_phase1_scout_success(self, orchestrator):
        """測試 Phase 1: Scout 成功"""
        # Mock collect_articles 結果
        mock_articles = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "source_type": "rss",
                "source_name": "Test Source",
                "published_at": "2025-11-24T10:00:00Z",
                "content": "Test content"
            },
            {
                "url": "https://example.com/article2",
                "title": "Test Article 2",
                "source_type": "search",
                "source_name": "Google",
                "published_at": "2025-11-24T11:00:00Z",
                "content": "Test content 2"
            }
        ]

        # Mock ScoutAgentRunner 和 create_scout_agent（lazy import 位置）
        with patch("src.agents.scout_agent.ScoutAgentRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner.collect_articles.return_value = {
                "status": "success",
                "articles": mock_articles
            }
            mock_runner_class.return_value = mock_runner

            with patch("src.agents.scout_agent.create_scout_agent") as mock_create_agent:
                mock_create_agent.return_value = Mock()

                # Mock article_store
                orchestrator.article_store.get_by_url.return_value = None
                orchestrator.article_store.store_article.side_effect = [1, 2]

                collected, stored = orchestrator._run_phase1_scout()

                assert collected == 2
                assert stored == 2
                assert orchestrator.article_store.store_article.call_count == 2

    def test_run_phase1_scout_with_duplicates(self, orchestrator):
        """測試 Phase 1: Scout 有重複文章"""
        mock_articles = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "source_type": "rss",
                "source_name": "Test Source",
                "content": "Test content"
            },
            {
                "url": "https://example.com/article2",
                "title": "Test Article 2",
                "source_type": "rss",
                "source_name": "Test Source",
                "content": "Test content 2"
            }
        ]

        with patch("src.agents.scout_agent.ScoutAgentRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner.collect_articles.return_value = {
                "status": "success",
                "articles": mock_articles
            }
            mock_runner_class.return_value = mock_runner

            with patch("src.agents.scout_agent.create_scout_agent") as mock_create_agent:
                mock_create_agent.return_value = Mock()

                # 第一篇已存在，第二篇是新的
                orchestrator.article_store.get_by_url.side_effect = [
                    {"id": 1, "url": "https://example.com/article1"},  # 已存在
                    None  # 不存在
                ]
                orchestrator.article_store.store_article.return_value = 2

                collected, stored = orchestrator._run_phase1_scout()

                assert collected == 2
                assert stored == 1  # 只有 1 篇新文章
                assert orchestrator.article_store.store_article.call_count == 1

    def test_run_phase1_scout_failure(self, orchestrator):
        """測試 Phase 1: Scout 失敗"""
        with patch("src.agents.scout_agent.ScoutAgentRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner.collect_articles.return_value = {
                "status": "error",
                "error_message": "API error"
            }
            mock_runner_class.return_value = mock_runner

            with patch("src.agents.scout_agent.create_scout_agent") as mock_create_agent:
                mock_create_agent.return_value = Mock()

                with pytest.raises(Exception) as exc_info:
                    orchestrator._run_phase1_scout()

                assert "Scout failed" in str(exc_info.value)
                assert len(orchestrator.stats["errors"]) == 1

    def test_run_phase2_analyst_success(self, orchestrator):
        """測試 Phase 2: Analyst 成功"""
        # Mock pending articles
        pending_articles = [
            {
                "id": 1,
                "url": "https://example.com/article1",
                "title": "Test Article 1"
            },
            {
                "id": 2,
                "url": "https://example.com/article2",
                "title": "Test Article 2"
            }
        ]

        orchestrator.article_store.get_by_status.return_value = pending_articles

        # Mock content extraction (lazy import 位置)
        with patch("src.tools.content_extractor.extract_content") as mock_extract:
            mock_extract.return_value = {
                "status": "success",
                "content": "Full article content"
            }

            # Mock AnalystAgentRunner (lazy import 位置)
            with patch("src.agents.analyst_agent.AnalystAgentRunner") as mock_runner_class:
                mock_runner = Mock()
                # analyze_article 是 async 方法，返回 coroutine
                async def mock_analyze(*args, **kwargs):
                    return {
                        "status": "success",
                        "priority_score": 0.85
                    }
                mock_runner.analyze_article = mock_analyze
                mock_runner_class.return_value = mock_runner

                with patch("src.agents.analyst_agent.create_analyst_agent") as mock_create:
                    mock_create.return_value = Mock()

                    analyzed_count = orchestrator._run_phase2_analyst()

                    assert analyzed_count == 2
                    assert mock_extract.call_count == 2

    def test_run_phase2_analyst_partial_failure(self, orchestrator):
        """測試 Phase 2: Analyst 部分失敗"""
        pending_articles = [
            {"id": 1, "url": "https://example.com/article1", "title": "Test Article 1"},
            {"id": 2, "url": "https://example.com/article2", "title": "Test Article 2"}
        ]

        orchestrator.article_store.get_by_status.return_value = pending_articles

        with patch("src.tools.content_extractor.extract_content") as mock_extract:
            # 第一篇提取失敗，第二篇成功
            mock_extract.side_effect = [
                {"status": "error", "error_message": "Extraction failed"},
                {"status": "success", "content": "Full content"}
            ]

            with patch("src.agents.analyst_agent.AnalystAgentRunner") as mock_runner_class:
                mock_runner = Mock()
                async def mock_analyze(*args, **kwargs):
                    return {
                        "status": "success",
                        "priority_score": 0.85
                    }
                mock_runner.analyze_article = mock_analyze
                mock_runner_class.return_value = mock_runner

                with patch("src.agents.analyst_agent.create_analyst_agent") as mock_create:
                    mock_create.return_value = Mock()

                    analyzed_count = orchestrator._run_phase2_analyst()

                    assert analyzed_count == 1  # 只有 1 篇成功

    def test_run_phase2_analyst_no_pending(self, orchestrator):
        """測試 Phase 2: 沒有待分析文章"""
        orchestrator.article_store.get_by_status.return_value = []

        analyzed_count = orchestrator._run_phase2_analyst()

        assert analyzed_count == 0

    def test_run_phase3_curator_success(self, orchestrator):
        """測試 Phase 3: Curator 成功"""
        # Mock generate_daily_digest (lazy import 位置)
        with patch("src.agents.curator_daily.generate_daily_digest") as mock_generate:
            mock_generate.return_value = {
                "status": "success",
                "subject": "Daily Digest",
                "recipients": ["test@example.com"]
            }

            sent = orchestrator._run_phase3_curator(dry_run=False)

            assert sent is True
            mock_generate.assert_called_once()

    def test_run_phase3_curator_dry_run(self, orchestrator):
        """測試 Phase 3: Curator dry run"""
        # Dry run 模式不會調用 generate_daily_digest
        sent = orchestrator._run_phase3_curator(dry_run=True)

        assert sent is True

    def test_run_phase3_curator_failure(self, orchestrator):
        """測試 Phase 3: Curator 失敗"""
        with patch("src.agents.curator_daily.generate_daily_digest") as mock_generate:
            mock_generate.return_value = {
                "status": "error",
                "error_message": "Email sending failed"
            }

            sent = orchestrator._run_phase3_curator(dry_run=False)

            assert sent is False

    def test_run_full_pipeline_success(self, orchestrator):
        """測試完整流程成功"""
        # Mock Phase 1
        with patch.object(orchestrator, "_run_phase1_scout") as mock_phase1:
            mock_phase1.return_value = (30, 25)

            # Mock Phase 2
            with patch.object(orchestrator, "_run_phase2_analyst") as mock_phase2:
                mock_phase2.return_value = 20

                # Mock Phase 3
                with patch.object(orchestrator, "_run_phase3_curator") as mock_phase3:
                    mock_phase3.return_value = True

                    result = orchestrator.run(dry_run=False)

                    assert result["success"] is True
                    assert result["stats"]["phase1_collected"] == 30
                    assert result["stats"]["phase1_stored"] == 25
                    assert result["stats"]["phase2_analyzed"] == 20
                    assert result["stats"]["phase3_sent"] is True
                    assert len(result["errors"]) == 0

    def test_run_pipeline_no_articles_collected(self, orchestrator):
        """測試流程：沒有收集到文章"""
        with patch.object(orchestrator, "_run_phase1_scout") as mock_phase1:
            mock_phase1.return_value = (0, 0)

            result = orchestrator.run(dry_run=False)

            assert result["success"] is False
            assert result["stats"]["phase1_stored"] == 0

    def test_run_pipeline_no_articles_analyzed(self, orchestrator):
        """測試流程：沒有分析成功的文章"""
        with patch.object(orchestrator, "_run_phase1_scout") as mock_phase1:
            mock_phase1.return_value = (30, 25)

            with patch.object(orchestrator, "_run_phase2_analyst") as mock_phase2:
                mock_phase2.return_value = 0

                result = orchestrator.run(dry_run=False)

                assert result["success"] is False
                assert result["stats"]["phase2_analyzed"] == 0

    def test_run_pipeline_email_failed(self, orchestrator):
        """測試流程：Email 發送失敗"""
        with patch.object(orchestrator, "_run_phase1_scout") as mock_phase1:
            mock_phase1.return_value = (30, 25)

            with patch.object(orchestrator, "_run_phase2_analyst") as mock_phase2:
                mock_phase2.return_value = 20

                with patch.object(orchestrator, "_run_phase3_curator") as mock_phase3:
                    mock_phase3.return_value = False

                    result = orchestrator.run(dry_run=False)

                    assert result["success"] is False
                    assert result["stats"]["phase3_sent"] is False

    def test_run_pipeline_exception(self, orchestrator):
        """測試流程：發生異常"""
        with patch.object(orchestrator, "_run_phase1_scout") as mock_phase1:
            mock_phase1.side_effect = Exception("Unexpected error")

            result = orchestrator.run(dry_run=False)

            assert result["success"] is False
            assert len(result["errors"]) == 1
            assert "Unexpected error" in result["errors"][0]["error_message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
