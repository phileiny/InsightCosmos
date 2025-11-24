"""
整合測試: Daily Pipeline

測試完整的日報流程整合（使用真實的資料庫與部分 Mock）。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import tempfile
import os

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.daily_runner import DailyPipelineOrchestrator, run_daily_pipeline
from src.utils.config import Config
from src.memory.database import Database
from src.memory.article_store import ArticleStore
from src.memory.embedding_store import EmbeddingStore


@pytest.fixture
def test_db_path():
    """創建臨時資料庫路徑"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    yield db_path
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def test_config(test_db_path):
    """創建測試配置"""
    config = Config(
        database_path=test_db_path,
        google_api_key="test_api_key_12345",
        email_account="test@example.com",
        email_password="test_password",
        user_name="Test User",
        user_interests="AI, Robotics, Multi-Agent Systems"
    )
    return config


@pytest.fixture
def orchestrator_with_real_db(test_config):
    """創建使用真實資料庫的 Orchestrator"""
    orchestrator = DailyPipelineOrchestrator(test_config)
    return orchestrator


class TestDailyPipelineIntegration:
    """整合測試：Daily Pipeline"""

    def test_orchestrator_initialization_with_real_db(self, test_config, test_db_path):
        """測試使用真實資料庫的初始化"""
        orchestrator = DailyPipelineOrchestrator(test_config)

        assert orchestrator.config == test_config
        assert orchestrator.db is not None
        assert orchestrator.article_store is not None
        assert orchestrator.embedding_store is not None

        # 驗證資料庫文件存在
        assert os.path.exists(test_db_path)

    def test_full_pipeline_dry_run_with_mocks(self, orchestrator_with_real_db):
        """測試完整流程（dry run，使用 Mock）"""
        orchestrator = orchestrator_with_real_db

        # Mock Scout Agent
        mock_articles = [
            {
                "url": f"https://example.com/article{i}",
                "title": f"Test Article {i}",
                "source_type": "rss",
                "source_name": "Test Source",
                "published_at": "2025-11-24T10:00:00Z",
                "content": "Test content"
            }
            for i in range(1, 6)
        ]

        with patch("src.orchestrator.daily_runner.collect_articles") as mock_collect:
            mock_collect.return_value = {
                "status": "success",
                "articles": mock_articles
            }

            # Mock Content Extractor
            with patch("src.orchestrator.daily_runner.extract_content") as mock_extract:
                mock_extract.return_value = {
                    "status": "success",
                    "content": "Full article content for testing. " * 100  # 足夠長的內容
                }

                # Mock Analyst Agent
                with patch("src.orchestrator.daily_runner.AnalystAgentRunner") as mock_runner_class:
                    mock_runner = Mock()
                    mock_runner_class.return_value = mock_runner
                    mock_runner.analyze_article.return_value = {
                        "status": "success",
                        "priority_score": 0.85,
                        "summary": "Test summary",
                        "key_insights": ["Insight 1", "Insight 2"]
                    }

                    # Mock Curator Agent
                    with patch("src.orchestrator.daily_runner.generate_daily_digest") as mock_generate:
                        mock_generate.return_value = {
                            "status": "success",
                            "subject": "Daily Digest - 2025-11-24",
                            "recipients": ["test@example.com"]
                        }

                        # 執行流程
                        result = orchestrator.run(dry_run=True)

                        # 驗證結果
                        assert result["success"] is True
                        assert result["stats"]["phase1_collected"] == 5
                        assert result["stats"]["phase1_stored"] == 5
                        assert result["stats"]["phase2_analyzed"] == 5
                        assert result["stats"]["phase3_sent"] is True
                        assert len(result["errors"]) == 0

    def test_pipeline_phase1_failure(self, orchestrator_with_real_db):
        """測試 Phase 1 失敗場景"""
        orchestrator = orchestrator_with_real_db

        with patch("src.orchestrator.daily_runner.collect_articles") as mock_collect:
            mock_collect.return_value = {
                "status": "error",
                "error_message": "API quota exceeded"
            }

            result = orchestrator.run(dry_run=True)

            assert result["success"] is False
            assert len(result["errors"]) >= 1

    def test_pipeline_phase2_all_fail(self, orchestrator_with_real_db):
        """測試 Phase 2 全部失敗場景"""
        orchestrator = orchestrator_with_real_db

        mock_articles = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "source_type": "rss",
                "source_name": "Test Source",
                "content": "Test"
            }
        ]

        with patch("src.orchestrator.daily_runner.collect_articles") as mock_collect:
            mock_collect.return_value = {
                "status": "success",
                "articles": mock_articles
            }

            # Content extraction 全部失敗
            with patch("src.orchestrator.daily_runner.extract_content") as mock_extract:
                mock_extract.return_value = {
                    "status": "error",
                    "error_message": "Content extraction failed"
                }

                result = orchestrator.run(dry_run=True)

                assert result["success"] is False
                assert result["stats"]["phase2_analyzed"] == 0

    def test_pipeline_with_database_persistence(self, orchestrator_with_real_db):
        """測試資料庫持久化"""
        orchestrator = orchestrator_with_real_db

        mock_articles = [
            {
                "url": "https://example.com/unique-article",
                "title": "Unique Test Article",
                "source_type": "rss",
                "source_name": "Test Source",
                "published_at": "2025-11-24T10:00:00Z",
                "content": "Test content"
            }
        ]

        with patch("src.orchestrator.daily_runner.collect_articles") as mock_collect:
            mock_collect.return_value = {
                "status": "success",
                "articles": mock_articles
            }

            with patch("src.orchestrator.daily_runner.extract_content") as mock_extract:
                mock_extract.return_value = {
                    "status": "success",
                    "content": "Full content"
                }

                with patch("src.orchestrator.daily_runner.AnalystAgentRunner") as mock_runner_class:
                    mock_runner = Mock()
                    mock_runner_class.return_value = mock_runner
                    mock_runner.analyze_article.return_value = {
                        "status": "success",
                        "priority_score": 0.9
                    }

                    with patch("src.orchestrator.daily_runner.generate_daily_digest") as mock_generate:
                        mock_generate.return_value = {
                            "status": "success",
                            "subject": "Test",
                            "recipients": ["test@example.com"]
                        }

                        # 第一次運行
                        result1 = orchestrator.run(dry_run=True)
                        assert result1["stats"]["phase1_stored"] == 1

                        # 第二次運行（同樣的文章）
                        result2 = orchestrator.run(dry_run=True)
                        assert result2["stats"]["phase1_stored"] == 0  # 已存在，不再存儲

    def test_run_daily_pipeline_function(self, test_config):
        """測試便捷函數 run_daily_pipeline"""
        with patch("src.orchestrator.daily_runner.Config.load_from_env") as mock_load:
            mock_load.return_value = test_config

            with patch("src.orchestrator.daily_runner.DailyPipelineOrchestrator") as mock_orchestrator_class:
                mock_orchestrator = Mock()
                mock_orchestrator_class.return_value = mock_orchestrator
                mock_orchestrator.run.return_value = {
                    "success": True,
                    "stats": {},
                    "errors": []
                }

                result = run_daily_pipeline(dry_run=True, verbose=False)

                assert result["success"] is True
                mock_orchestrator.run.assert_called_once_with(dry_run=True)

    def test_article_store_integration(self, orchestrator_with_real_db):
        """測試 ArticleStore 整合"""
        article_store = orchestrator_with_real_db.article_store

        # 創建文章
        article_id = article_store.create_article(
            url="https://example.com/test",
            title="Test Article",
            source_type="rss",
            source_name="Test Source"
        )

        assert article_id is not None

        # 獲取文章
        article = article_store.get_by_id(article_id)
        assert article is not None
        assert article["title"] == "Test Article"
        assert article["status"] == "collected"

        # 檢查 get_by_url
        found = article_store.get_by_url("https://example.com/test")
        assert found is not None
        assert found["id"] == article_id

    def test_error_handling_in_pipeline(self, orchestrator_with_real_db):
        """測試流程中的錯誤處理"""
        orchestrator = orchestrator_with_real_db

        with patch("src.orchestrator.daily_runner.collect_articles") as mock_collect:
            # Scout 拋出異常
            mock_collect.side_effect = RuntimeError("Network error")

            result = orchestrator.run(dry_run=True)

            assert result["success"] is False
            assert len(result["errors"]) >= 1
            assert "Network error" in str(result["errors"])


@pytest.mark.manual
class TestDailyPipelineManual:
    """手動測試（需要真實 API Key）"""

    def test_full_pipeline_with_real_apis(self):
        """
        完整流程測試（需要真實 API Key）

        執行方式：
        pytest tests/integration/test_daily_pipeline.py::TestDailyPipelineManual::test_full_pipeline_with_real_apis -v -m manual
        """
        # 載入真實配置
        config = Config.load_from_env()

        # 執行流程（dry run）
        result = run_daily_pipeline(dry_run=True, verbose=True)

        # 驗證
        assert result["success"] is True
        assert result["stats"]["phase1_collected"] > 0
        assert result["stats"]["phase2_analyzed"] > 0
        assert result["stats"]["phase3_sent"] is True

        print("\n=== Pipeline Result ===")
        print(f"Collected: {result['stats']['phase1_collected']}")
        print(f"Analyzed: {result['stats']['phase2_analyzed']}")
        print(f"Duration: {result['stats']['duration_seconds']:.1f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
