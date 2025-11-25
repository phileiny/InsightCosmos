#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 10 驗證：系統整合測試
測試完整的 InsightCosmos Phase 1 系統整合
"""

import pytest
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSystemIntegration:
    """系統整合測試：驗證所有模組能夠正確整合"""

    def test_all_core_modules_importable(self):
        """測試：所有核心模組可以導入"""
        # Utils
        from src.utils.config import Config
        from src.utils.logger import Logger

        # Memory
        from src.memory.database import Database
        from src.memory.article_store import ArticleStore
        from src.memory.embedding_store import EmbeddingStore

        # Tools
        from src.tools import (
            RSSFetcher,
            GoogleSearchGroundingTool,
            ContentExtractor,
            EmailSender,
            DigestFormatter,
        )

        # Agents
        from src.agents.scout_agent import collect_articles, create_scout_agent
        from src.agents.analyst_agent import create_analyst_agent, AnalystAgentRunner
        from src.agents.curator_daily import generate_daily_digest

        # Orchestrator
        from src.orchestrator.daily_runner import DailyPipelineOrchestrator

        # 如果所有導入成功，測試通過
        assert True

    def test_config_system(self):
        """測試：配置系統正常工作"""
        from src.utils.config import Config

        # 測試配置載入（會使用 .env.example 或當前 .env）
        try:
            config = Config.load()
            assert config is not None
            assert hasattr(config, 'google_api_key')
            assert hasattr(config, 'database_path')
            assert hasattr(config, 'user_name')
            assert hasattr(config, 'user_interests')
        except FileNotFoundError:
            # 如果沒有 .env，測試手動創建配置
            config = Config(
                google_api_key="test_key",
                email_account="test@example.com",
                email_password="test_password",
                database_path="test.db",
                user_name="Test User",
                user_interests="AI,Robotics"
            )
            assert config.get_interests_list() == ["AI", "Robotics"]

    def test_memory_layer_integration(self):
        """測試：記憶層整合"""
        from src.utils.config import Config
        from src.memory.database import Database
        from src.memory.article_store import ArticleStore
        from src.memory.embedding_store import EmbeddingStore
        import tempfile
        import os

        # 使用臨時資料庫
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            test_db = tmp.name

        try:
            # 創建配置
            config = Config(
                google_api_key="test_key",
                email_account="test@example.com",
                email_password="test_password",
                database_path=test_db,
                user_name="Test",
                user_interests="AI"
            )

            # 初始化資料庫
            db = Database.from_config(config)
            db.init_db()

            # 測試 ArticleStore
            article_store = ArticleStore(db)
            article_id = article_store.store_article({
                "url": "https://test.com/article1",
                "title": "Test Article",
                "summary": "Test summary",
                "source": "test",
                "status": "collected"
            })
            assert article_id is not None

            # 測試查詢
            article = article_store.get_by_id(article_id)
            assert article is not None
            assert article['title'] == "Test Article"

            # 測試 EmbeddingStore
            embedding_store = EmbeddingStore(db)
            import numpy as np
            test_embedding = np.random.rand(768)

            embedding_id = embedding_store.store(
                article_id=article_id,
                vector=test_embedding,
                model="test-model"
            )
            assert embedding_id is not None

        finally:
            # 清理
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_tools_integration(self):
        """測試：工具層整合"""
        from src.tools import RSSFetcher, ContentExtractor, DigestFormatter

        # 測試 RSSFetcher 初始化
        fetcher = RSSFetcher(timeout=10)
        assert fetcher is not None

        # 測試 ContentExtractor 初始化
        extractor = ContentExtractor(timeout=10)
        assert extractor is not None

        # 測試 DigestFormatter 初始化
        formatter = DigestFormatter()
        assert formatter is not None

    def test_agent_creation(self):
        """測試：Agent 創建"""
        import tempfile
        import os

        # 創建臨時 prompt 文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("Test prompt with {{USER_INTERESTS}}")
            tmp_prompt = tmp.name

        try:
            from src.agents.scout_agent import create_scout_agent
            from src.agents.analyst_agent import create_analyst_agent

            # 測試 Scout Agent 創建（使用實際 prompt 文件）
            scout_prompt = "prompts/scout_prompt.txt"
            if os.path.exists(scout_prompt):
                try:
                    scout_agent = create_scout_agent(
                        instruction_file=scout_prompt,
                        user_interests="AI,Robotics"
                    )
                    assert scout_agent is not None
                    assert scout_agent.name == "ScoutAgent"
                except ValueError as e:
                    # API key 問題可以跳過
                    if "GOOGLE_API_KEY" in str(e):
                        pytest.skip("GOOGLE_API_KEY not configured")
                    else:
                        raise

            # 測試 Analyst Agent 創建
            analyst_prompt = "prompts/analyst_prompt.txt"
            if os.path.exists(analyst_prompt):
                try:
                    analyst_agent = create_analyst_agent(
                        user_name="Test User",
                        user_interests="AI,Robotics"
                    )
                    assert analyst_agent is not None
                    assert analyst_agent.name == "AnalystAgent"
                except ValueError as e:
                    if "GOOGLE_API_KEY" in str(e):
                        pytest.skip("GOOGLE_API_KEY not configured")
                    else:
                        raise

        finally:
            if os.path.exists(tmp_prompt):
                os.remove(tmp_prompt)

    def test_orchestrator_initialization(self):
        """測試：Orchestrator 初始化"""
        from src.orchestrator.daily_runner import DailyPipelineOrchestrator
        from src.utils.config import Config
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            test_db = tmp.name

        try:
            config = Config(
                google_api_key="test_key",
                email_account="test@example.com",
                email_password="test_password",
                database_path=test_db,
                user_name="Test",
                user_interests="AI,Robotics"
            )

            orchestrator = DailyPipelineOrchestrator(config)
            assert orchestrator is not None
            assert orchestrator.config == config
            assert orchestrator.db is not None
            assert orchestrator.article_store is not None
            assert orchestrator.embedding_store is not None
            assert orchestrator.logger is not None

            # 測試統計初始化
            assert orchestrator.stats['phase1_collected'] == 0
            assert orchestrator.stats['phase2_analyzed'] == 0
            assert orchestrator.stats['phase3_sent'] == False

        finally:
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_data_flow_structure(self):
        """測試：數據流結構正確性"""
        from src.memory.article_store import ArticleStore
        from src.utils.config import Config
        from src.memory.database import Database
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            test_db = tmp.name

        try:
            config = Config(
                google_api_key="test_key",
                email_account="test@example.com",
                email_password="test_password",
                database_path=test_db,
                user_name="Test",
                user_interests="AI"
            )

            db = Database.from_config(config)
            db.init_db()
            article_store = ArticleStore(db)

            # 模擬完整數據流
            # Phase 1: Scout 收集文章
            article_id = article_store.store_article({
                "url": "https://test.com/article",
                "title": "Test Article",
                "summary": "Test summary",
                "source": "rss",
                "status": "collected"  # Phase 1 狀態
            })

            # Phase 2: Analyst 分析文章
            import json
            article_store.update(article_id,
                content="Full content",
                analysis=json.dumps({"insight": "test"}),
                priority_score=0.8,
                status="analyzed"  # Phase 2 狀態
            )

            # 驗證數據流
            article = article_store.get_by_id(article_id)
            assert article['status'] == 'analyzed'
            assert article['content'] == 'Full content'
            assert article['priority_score'] == 0.8

        finally:
            if os.path.exists(test_db):
                os.remove(test_db)


class TestSystemReadiness:
    """系統就緒檢查：確保系統可以運行"""

    def test_required_directories_exist(self):
        """測試：必要目錄存在"""
        dirs_to_check = [
            "src/agents",
            "src/tools",
            "src/memory",
            "src/utils",
            "src/orchestrator",
            "prompts",
            "data",
            "tests",
            "docs"
        ]

        for dir_path in dirs_to_check:
            assert Path(dir_path).exists(), f"Required directory missing: {dir_path}"

    def test_required_files_exist(self):
        """測試：必要文件存在"""
        files_to_check = [
            "requirements.txt",
            ".env.example",
            "README.md",
            "CLAUDE.md",
            "src/__init__.py",
            "prompts/scout_prompt.txt",
            "prompts/analyst_prompt.txt",
            "prompts/daily_prompt.txt"
        ]

        for file_path in files_to_check:
            assert Path(file_path).exists(), f"Required file missing: {file_path}"

    def test_python_version(self):
        """測試：Python 版本符合要求"""
        import sys
        version = sys.version_info
        assert version.major == 3
        assert version.minor >= 10, "Python 3.10+ required"


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v", "--tb=short"])
