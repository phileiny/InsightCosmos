"""
Unit Tests for Curator Daily Agent

測試 CuratorDailyAgent 和 CuratorDailyRunner 的所有功能。

測試涵蓋範圍:
    - Agent 創建
    - Prompt 模板變數替換
    - JSON 解析（plain JSON 和 Markdown 包裝）
    - 報告生成（Mock LLM）
    - 格式化與發送（Mock EmailSender）
    - 完整流程（Mock）
    - 錯誤處理

執行方式:
    pytest tests/unit/test_curator_daily.py -v
    pytest tests/unit/test_curator_daily.py::TestCuratorDailyAgent -v
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime, timedelta

from src.agents.curator_daily import (
    create_curator_agent,
    CuratorDailyRunner,
    generate_daily_digest,
    _load_prompt_template,
    DEFAULT_FIRST_RUN_DAYS
)
from src.utils.config import Config
from src.memory.article_store import ArticleStore
from src.tools.email_sender import EmailConfig


class TestCuratorDailyAgent:
    """Test Curator Daily Agent creation and configuration"""

    @pytest.fixture
    def mock_config(self):
        """建立測試用 Config"""
        return Config(
            google_api_key="test_api_key",
            user_name="Ray",
            user_interests="AI, Robotics, Multi-Agent Systems",
            database_path=":memory:",
            email_account="test@example.com",
            email_password="test_password"
        )

    def test_create_curator_agent(self, mock_config):
        """測試 Curator Daily Agent 創建"""
        agent = create_curator_agent(mock_config)

        # 驗證 Agent 屬性
        assert agent is not None
        assert agent.name == "CuratorDailyAgent"
        assert agent.description == "Curates daily AI and Robotics digest from analyzed articles"
        assert agent.tools == []  # No tools for curator

        # 驗證 instruction 包含使用者資訊
        assert "Ray" in agent.instruction
        assert "AI, Robotics, Multi-Agent Systems" in agent.instruction

    def test_load_prompt_with_variables(self, mock_config):
        """測試 Prompt 模板變數替換"""
        # 載入原始模板
        template = _load_prompt_template()

        # 驗證模板包含變數佔位符
        assert '{{USER_NAME}}' in template
        assert '{{USER_INTERESTS}}' in template

        # 創建 Agent 並驗證變數替換
        agent = create_curator_agent(mock_config)

        # 驗證變數已被替換
        assert '{{USER_NAME}}' not in agent.instruction
        assert '{{USER_INTERESTS}}' not in agent.instruction
        assert 'Ray' in agent.instruction
        assert 'AI, Robotics, Multi-Agent Systems' in agent.instruction


class TestCuratorDailyRunner:
    """Test CuratorDailyRunner class"""

    @pytest.fixture
    def mock_config(self):
        return Config(
            google_api_key="test_api_key",
            user_name="Ray",
            user_interests="AI, Robotics",
            database_path=":memory:",
            email_account="test@example.com",
            email_password="test_password",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_use_tls=True
        )

    @pytest.fixture
    def mock_article_store(self):
        """建立 Mock ArticleStore"""
        store = Mock(spec=ArticleStore)
        # Add mock database for ReportStore initialization
        store.database = Mock()
        return store

    @pytest.fixture
    def sample_articles(self):
        """建立測試用文章數據"""
        return [
            {
                "id": 1,
                "title": "Google Releases Gemini 2.0",
                "url": "https://example.com/gemini-2.0",
                "summary": "Google 發布 Gemini 2.0，原生支援工具調用。",
                "key_insights": ["原生工具調用", "性能提升 40%", "支援多模態"],
                "priority_score": 0.95,
                "priority_reasoning": "重大技術突破",
                "tags": "AI,LLM",
                "published_at": "2025-11-24T10:00:00Z",
                "source_name": "Google AI Blog"
            },
            {
                "id": 2,
                "title": "Tesla Optimus Update",
                "url": "https://example.com/optimus",
                "summary": "Tesla Optimus 展示複雜操作能力。",
                "key_insights": ["靈巧操作", "95% 精準度", "量產計劃"],
                "priority_score": 0.88,
                "priority_reasoning": "商業化進展",
                "tags": "Robotics,Manipulation",
                "published_at": "2025-11-24T11:00:00Z",
                "source_name": "Tesla Engineering"
            }
        ]

    @pytest.fixture
    def sample_digest(self):
        """建立測試用 Digest 數據"""
        return {
            "date": "2025-11-24",
            "total_articles": 2,
            "top_articles": [
                {
                    "title": "Google Releases Gemini 2.0",
                    "url": "https://example.com/gemini-2.0",
                    "summary": "Google 發布 Gemini 2.0，原生支援工具調用。",
                    "key_takeaway": "原生工具調用將簡化 Agent 開發。",
                    "priority_score": 0.95,
                    "tags": ["AI", "LLM"]
                },
                {
                    "title": "Tesla Optimus Update",
                    "url": "https://example.com/optimus",
                    "summary": "Tesla Optimus 展示複雜操作能力。",
                    "key_takeaway": "人形機器人商業化加速。",
                    "priority_score": 0.88,
                    "tags": ["Robotics", "Manipulation"]
                }
            ],
            "daily_insight": "今日重點聚焦於 AI 與 Robotics 的工程化進展。",
            "recommended_action": "建議深入了解 Gemini 2.0 的工具調用機制。"
        }

    def test_runner_initialization(self, mock_config, mock_article_store):
        """測試 CuratorDailyRunner 初始化"""
        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        assert runner.agent == agent
        assert runner.article_store == mock_article_store
        assert runner.config == mock_config
        assert runner.formatter is not None
        assert runner.email_sender is not None

    def test_fetch_analyzed_articles(
        self,
        mock_config,
        mock_article_store,
        sample_articles
    ):
        """測試從 ArticleStore 取得文章"""
        # Mock get_top_priority
        mock_article_store.get_top_priority.return_value = sample_articles

        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        # 取得文章
        articles = runner.fetch_analyzed_articles(max_articles=10)

        # 驗證結果
        assert len(articles) == 2
        assert articles[0]['title'] == "Google Releases Gemini 2.0"
        assert articles[0]['tags'] == ["AI", "LLM"]  # 字串被轉為陣列
        assert articles[1]['tags'] == ["Robotics", "Manipulation"]

        # 驗證 mock 被調用 (新版本傳入時間過濾參數)
        mock_article_store.get_top_priority.assert_called_once()
        call_kwargs = mock_article_store.get_top_priority.call_args[1]
        assert call_kwargs['limit'] == 30  # 內部使用 30，後續再切到 max_articles
        assert call_kwargs['status'] == 'analyzed'
        # 時間過濾參數應存在（可為 None）
        assert 'fetched_after' in call_kwargs
        assert 'fetched_before' in call_kwargs

    def test_fetch_analyzed_articles_empty(self, mock_config, mock_article_store):
        """測試取得空文章列表"""
        mock_article_store.get_top_priority.return_value = []

        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        articles = runner.fetch_analyzed_articles(max_articles=10)

        assert articles == []

    def test_parse_digest_json_plain(self, mock_config, mock_article_store, sample_digest):
        """測試解析 plain JSON"""
        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        # Plain JSON 字串
        json_str = json.dumps(sample_digest, ensure_ascii=False)

        # 解析
        digest = runner._parse_digest_json(json_str)

        # 驗證
        assert digest is not None
        assert digest['date'] == "2025-11-24"
        assert digest['total_articles'] == 2
        assert len(digest['top_articles']) == 2

    def test_parse_digest_json_in_markdown(
        self,
        mock_config,
        mock_article_store,
        sample_digest
    ):
        """測試解析 Markdown 包裝的 JSON"""
        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        # Markdown 包裝的 JSON
        json_str = json.dumps(sample_digest, ensure_ascii=False, indent=2)
        markdown_response = f"""根據文章列表，我生成了今日摘要：

```json
{json_str}
```

以上是今日摘要。"""

        # 解析
        digest = runner._parse_digest_json(markdown_response)

        # 驗證
        assert digest is not None
        assert digest['date'] == "2025-11-24"
        assert digest['total_articles'] == 2

    def test_parse_digest_invalid_json(self, mock_config, mock_article_store):
        """測試解析無效 JSON"""
        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        # 無效 JSON
        invalid_json = "This is not JSON at all"

        # 解析（應該返回 None）
        digest = runner._parse_digest_json(invalid_json)

        assert digest is None

    def test_generate_digest_with_mock_llm(
        self,
        mock_config,
        mock_article_store,
        sample_articles,
        sample_digest
    ):
        """測試使用 Mock LLM 生成報告"""
        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        # Mock _invoke_llm
        mock_llm_response = json.dumps(sample_digest, ensure_ascii=False)
        with patch.object(runner, '_invoke_llm', return_value=mock_llm_response):
            digest = runner.generate_digest(sample_articles)

            # 驗證結果
            assert digest is not None
            assert digest['date'] == "2025-11-24"
            assert digest['total_articles'] == 2
            assert len(digest['top_articles']) == 2

    def test_generate_digest_empty_articles(self, mock_config, mock_article_store):
        """測試空文章列表時生成報告"""
        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        digest = runner.generate_digest([])

        # 應該返回 None
        assert digest is None

    def test_generate_and_send_digest_success(
        self,
        mock_config,
        mock_article_store,
        sample_articles,
        sample_digest
    ):
        """測試完整的生成與發送流程（Mock）"""
        # Mock ArticleStore
        mock_article_store.get_top_priority.return_value = sample_articles

        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        # Mock LLM
        mock_llm_response = json.dumps(sample_digest, ensure_ascii=False)
        with patch.object(runner, '_invoke_llm', return_value=mock_llm_response):
            # Mock EmailSender
            with patch.object(runner.email_sender, 'send') as mock_send:
                mock_send.return_value = {
                    "status": "success",
                    "message": "Email sent successfully"
                }

                # 執行
                result = runner.generate_and_send_digest(
                    recipient_email="ray@example.com",
                    max_articles=10
                )

                # 驗證結果
                assert result['status'] == 'success'
                assert 'digest' in result
                assert 'email_result' in result
                assert result['digest']['date'] == "2025-11-24"

                # 驗證 EmailSender 被調用
                mock_send.assert_called_once()
                call_args = mock_send.call_args
                assert call_args.kwargs['to_email'] == "ray@example.com"
                assert "InsightCosmos Daily Digest - 2025-11-24" in call_args.kwargs['subject']
                assert call_args.kwargs['html_body'] is not None
                assert call_args.kwargs['text_body'] is not None

    def test_generate_and_send_digest_no_articles(
        self,
        mock_config,
        mock_article_store
    ):
        """測試無文章時的處理 (新行為: 返回 skip 狀態)"""
        # Mock ArticleStore 返回空列表
        mock_article_store.get_top_priority.return_value = []

        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        result = runner.generate_and_send_digest(
            recipient_email="ray@example.com",
            max_articles=10
        )

        # 新行為: 返回 'skip' 狀態而非 'error' (Phase 4 時間過濾功能)
        assert result['status'] == 'skip'
        assert 'No new articles' in result['message']
        assert 'period_start' in result
        assert 'period_end' in result

    def test_generate_and_send_digest_llm_failure(
        self,
        mock_config,
        mock_article_store,
        sample_articles
    ):
        """測試 LLM 生成失敗時的處理"""
        mock_article_store.get_top_priority.return_value = sample_articles

        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        # Mock LLM 返回無效 JSON
        with patch.object(runner, '_invoke_llm', return_value="Invalid JSON"):
            result = runner.generate_and_send_digest(
                recipient_email="ray@example.com",
                max_articles=10
            )

            # 驗證錯誤處理
            assert result['status'] == 'error'
            assert 'LLM failed to generate valid digest' in result['error']

    def test_generate_and_send_digest_email_failure(
        self,
        mock_config,
        mock_article_store,
        sample_articles,
        sample_digest
    ):
        """測試 Email 發送失敗時的處理"""
        mock_article_store.get_top_priority.return_value = sample_articles

        agent = create_curator_agent(mock_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=mock_article_store,
            config=mock_config
        )

        mock_llm_response = json.dumps(sample_digest, ensure_ascii=False)
        with patch.object(runner, '_invoke_llm', return_value=mock_llm_response):
            # Mock EmailSender 返回失敗
            with patch.object(runner.email_sender, 'send') as mock_send:
                mock_send.return_value = {
                    "status": "error",
                    "error": "SMTP connection failed"
                }

                result = runner.generate_and_send_digest(
                    recipient_email="ray@example.com",
                    max_articles=10
                )

                # 驗證錯誤處理
                assert result['status'] == 'error'
                assert 'Email sending failed' in result['error']
                assert 'digest' in result  # Digest 仍然生成


class TestConvenienceFunction:
    """Test generate_daily_digest convenience function"""

    def test_generate_daily_digest_with_mock(self):
        """測試 generate_daily_digest 便利函式"""
        mock_config = Config(
            google_api_key="test_api_key",
            user_name="Ray",
            user_interests="AI, Robotics",
            database_path=":memory:",
            email_account="test@example.com",
            email_password="test_password"
        )

        sample_digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "summary": "Test summary.",
                    "key_takeaway": "Test takeaway.",
                    "priority_score": 0.80,
                    "tags": ["AI"]
                }
            ],
            "daily_insight": "Test insight."
        }

        # Mock Database and ArticleStore (內部 inline import)
        with patch('src.memory.database.Database') as mock_db_class:
            with patch('src.memory.article_store.ArticleStore') as mock_store_class:
                # Mock instances
                mock_db = Mock()
                mock_store = Mock()
                mock_store.database = mock_db  # Add database for ReportStore
                mock_db_class.from_config.return_value = mock_db
                mock_store_class.return_value = mock_store

                # Mock get_top_priority
                mock_store.get_top_priority.return_value = [
                    {
                        "id": 1,
                        "title": "Test Article",
                        "url": "https://example.com/test",
                        "summary": "Test summary.",
                        "key_insights": ["Insight 1"],
                        "priority_score": 0.80,
                        "priority_reasoning": "Test reasoning",
                        "tags": "AI",
                        "published_at": "2025-11-24T10:00:00Z",
                        "source_name": "Test Source"
                    }
                ]

                # Mock ReportStore to avoid database access
                with patch('src.agents.curator_daily.ReportStore') as mock_report_store_class:
                    mock_report_store = Mock()
                    mock_report_store_class.return_value = mock_report_store
                    mock_report_store.get_last_daily_report.return_value = None

                    # Mock LLM and EmailSender
                    with patch('src.agents.curator_daily.CuratorDailyRunner') as mock_runner_class:
                        mock_runner = Mock()
                        mock_runner_class.return_value = mock_runner
                        mock_runner.generate_and_send_digest.return_value = {
                            "status": "success",
                            "digest": sample_digest
                        }

                        # 執行
                        result = generate_daily_digest(
                            config=mock_config,
                            recipient_email="ray@example.com",
                            max_articles=10
                        )

                        # 驗證
                        assert result['status'] == 'success'
                        assert 'digest' in result


def test_module_imports():
    """測試模組可以正確匯入"""
    from src.agents.curator_daily import (
        create_curator_agent,
        CuratorDailyRunner,
        generate_daily_digest
    )

    assert create_curator_agent is not None
    assert CuratorDailyRunner is not None
    assert generate_daily_digest is not None


# ========================================
# Time Filter Tests (Phase 4)
# ========================================

class TestCuratorTimeFilter:
    """Test time-based filtering functionality"""

    @pytest.fixture
    def mock_config(self):
        return Config(
            google_api_key="test_api_key",
            user_name="Ray",
            user_interests="AI, Robotics",
            database_path=":memory:",
            email_account="test@example.com",
            email_password="test_password",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_use_tls=True
        )

    @pytest.fixture
    def mock_article_store(self):
        """Build Mock ArticleStore with database attribute"""
        store = Mock(spec=ArticleStore)
        store.database = Mock()
        return store

    def test_first_run_uses_30_days(self, mock_config, mock_article_store):
        """
        TC-CUR-01: Test first run uses 30 days as default period

        Expected:
        - When no previous report exists, period_start is 30 days before period_end
        """
        agent = create_curator_agent(mock_config)

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(agent, mock_article_store, mock_config)
            period_start, period_end = runner._determine_time_period()

            # Verify: period_start should be ~30 days before period_end
            expected_start = period_end - timedelta(days=DEFAULT_FIRST_RUN_DAYS)
            assert abs((period_start - expected_start).total_seconds()) < 1

    def test_subsequent_run_uses_last_period_end(self, mock_config, mock_article_store):
        """
        TC-CUR-02: Test subsequent run uses last report's period_end

        Expected:
        - period_start equals the previous report's period_end
        """
        agent = create_curator_agent(mock_config)
        last_period_end = datetime(2025, 12, 4, 8, 0, 0)

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = {
                'period_end': last_period_end.isoformat()
            }
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(agent, mock_article_store, mock_config)
            period_start, period_end = runner._determine_time_period()

            # Verify: period_start should equal last period_end
            assert period_start == last_period_end

    def test_no_articles_returns_skip(self, mock_config, mock_article_store):
        """
        TC-CUR-03: Test returns skip status when no articles in time range

        Expected:
        - status is 'skip'
        - message indicates no new articles
        """
        mock_article_store.get_top_priority.return_value = []

        agent = create_curator_agent(mock_config)

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(agent, mock_article_store, mock_config)
            result = runner.generate_and_send_digest("test@example.com")

            assert result['status'] == 'skip'
            assert 'No new articles' in result.get('message', '')
            assert 'period_start' in result
            assert 'period_end' in result

    def test_saves_report_on_success(self, mock_config, mock_article_store):
        """
        TC-CUR-04: Test saves report record after successful email send

        Expected:
        - create_daily_report is called after email success
        """
        mock_article_store.get_top_priority.return_value = [
            {
                'id': 1,
                'title': 'Test Article',
                'url': 'http://test.com',
                'summary': 'Test summary',
                'analysis': {},
                'tags': 'AI',
                'priority_score': 0.9,
                'source_name': 'Test'
            }
        ]

        agent = create_curator_agent(mock_config)

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(agent, mock_article_store, mock_config)

            sample_digest = {
                'date': '2025-12-05',
                'top_articles': [],
                'daily_insight': 'Test insight'
            }

            with patch.object(runner, '_invoke_llm', return_value=json.dumps(sample_digest)):
                with patch.object(runner.email_sender, 'send') as mock_send:
                    mock_send.return_value = {'status': 'success'}

                    result = runner.generate_and_send_digest("test@example.com")

                    assert result['status'] == 'success'
                    # Verify create_daily_report was called
                    assert mock_report_store.create_daily_report.called

    def test_does_not_save_report_on_email_failure(self, mock_config, mock_article_store):
        """
        TC-CUR-05: Test does not save report when email fails

        Expected:
        - create_daily_report is NOT called when email fails
        """
        mock_article_store.get_top_priority.return_value = [
            {
                'id': 1,
                'title': 'Test Article',
                'url': 'http://test.com',
                'summary': 'Test summary',
                'analysis': {},
                'tags': 'AI',
                'priority_score': 0.9,
                'source_name': 'Test'
            }
        ]

        agent = create_curator_agent(mock_config)

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(agent, mock_article_store, mock_config)

            sample_digest = {
                'date': '2025-12-05',
                'top_articles': [],
                'daily_insight': 'Test insight'
            }

            with patch.object(runner, '_invoke_llm', return_value=json.dumps(sample_digest)):
                with patch.object(runner.email_sender, 'send') as mock_send:
                    mock_send.return_value = {'status': 'error', 'error': 'SMTP failed'}

                    result = runner.generate_and_send_digest("test@example.com")

                    assert result['status'] == 'error'
                    # Verify create_daily_report was NOT called
                    assert not mock_report_store.create_daily_report.called

    def test_fetch_articles_with_time_params(self, mock_config, mock_article_store):
        """
        TC-CUR-06: Test fetch_analyzed_articles passes time parameters

        Expected:
        - get_top_priority is called with fetched_after and fetched_before
        """
        mock_article_store.get_top_priority.return_value = []

        agent = create_curator_agent(mock_config)

        with patch('src.agents.curator_daily.ReportStore') as MockReportStore:
            mock_report_store = Mock()
            mock_report_store.get_last_daily_report.return_value = None
            MockReportStore.return_value = mock_report_store

            runner = CuratorDailyRunner(agent, mock_article_store, mock_config)

            period_start = datetime(2025, 12, 4, 8, 0)
            period_end = datetime(2025, 12, 5, 8, 0)

            runner.fetch_analyzed_articles(
                max_articles=10,
                fetched_after=period_start,
                fetched_before=period_end
            )

            # Verify get_top_priority was called with time params
            mock_article_store.get_top_priority.assert_called_once_with(
                limit=30,  # 10 * 3
                status='analyzed',
                fetched_after=period_start,
                fetched_before=period_end
            )
