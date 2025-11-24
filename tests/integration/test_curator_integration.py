"""
Integration Tests for Curator Daily Agent

測試 Curator Daily Agent 與其他元件的整合，包括：
- ArticleStore 整合
- DigestFormatter 整合
- EmailSender 整合
- 完整流程整合（從資料庫到 Email）

測試涵蓋範圍:
    - 從 Memory 取得文章並生成報告（Mock LLM）
    - 格式化 HTML 與純文字
    - Email 發送（Mock SMTP）
    - 完整流程（Mock）
    - 真實 LLM 測試（手動標記）
    - 真實 Email 測試（手動標記）

執行方式:
    # 執行所有整合測試（不包含手動測試）
    pytest tests/integration/test_curator_integration.py -v

    # 執行包含真實 LLM 的測試（需要 API Key）
    pytest tests/integration/test_curator_integration.py -v -m "not manual"

    # 執行所有測試（包含手動測試）
    pytest tests/integration/test_curator_integration.py -v --run-manual
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import json

from src.agents.curator_daily import create_curator_agent, CuratorDailyRunner
from src.memory.database import Database
from src.memory.article_store import ArticleStore
from src.tools.digest_formatter import DigestFormatter
from src.tools.email_sender import EmailSender, EmailConfig
from src.utils.config import Config


@pytest.fixture
def test_config():
    """建立測試用 Config"""
    return Config(
        google_api_key=os.getenv('GOOGLE_API_KEY', 'test_api_key'),
        user_name="Ray",
        user_interests="AI, Robotics, Multi-Agent Systems",
        database_path=":memory:",  # 使用記憶體資料庫
        email_account="test@example.com",
        email_password="test_password",
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_use_tls=True
    )


@pytest.fixture
def test_database(test_config):
    """建立測試用資料庫（記憶體）"""
    db = Database.from_config(test_config)
    db.init_db()  # Initialize schema for in-memory database
    return db


@pytest.fixture
def test_article_store(test_database):
    """建立測試用 ArticleStore"""
    return ArticleStore(test_database)


@pytest.fixture
def sample_articles_for_db():
    """建立測試用文章數據（用於插入資料庫）"""
    return [
        {
            "url": "https://example.com/gemini-2.0",
            "title": "Google Releases Gemini 2.0 with Native Tool Use",
            "published_at": datetime(2025, 11, 24, 10, 0, 0),
            "source_name": "Google AI Blog",
            "content": "Full article content about Gemini 2.0...",
            "summary": "Google 發布 Gemini 2.0，原生支援工具調用，性能提升 40%。",
            "key_insights": json.dumps(["原生工具調用", "性能提升 40%", "支援多模態"]),
            "priority_score": 0.95,
            "priority_reasoning": "重大技術突破，影響 Agent 開發範式。",
            "tags": "AI,LLM",
            "status": "analyzed"
        },
        {
            "url": "https://example.com/optimus-manipulation",
            "title": "Tesla Optimus Robot Demonstrates Complex Manipulation",
            "published_at": datetime(2025, 11, 24, 11, 0, 0),
            "source_name": "Tesla Engineering",
            "content": "Full article content about Optimus...",
            "summary": "Tesla Optimus 展示 95% 精準度的複雜物體操作。",
            "key_insights": json.dumps(["靈巧操作", "95% 精準度", "量產計劃"]),
            "priority_score": 0.88,
            "priority_reasoning": "人形機器人商業化進展。",
            "tags": "Robotics,Manipulation",
            "status": "analyzed"
        },
        {
            "url": "https://example.com/multi-agent-systems",
            "title": "New Framework for Multi-Agent Coordination",
            "published_at": datetime(2025, 11, 24, 12, 0, 0),
            "source_name": "ArXiv",
            "content": "Full article content about multi-agent systems...",
            "summary": "新的多代理協調框架，提升協作效率 50%。",
            "key_insights": json.dumps(["協調效率提升", "去中心化架構", "可擴展性"]),
            "priority_score": 0.82,
            "priority_reasoning": "多代理系統技術進展。",
            "tags": "AI,Multi-Agent",
            "status": "analyzed"
        }
    ]


@pytest.fixture
def sample_digest():
    """建立測試用 Digest 數據（LLM 輸出）"""
    return {
        "date": "2025-11-24",
        "total_articles": 3,
        "top_articles": [
            {
                "title": "Google Releases Gemini 2.0 with Native Tool Use",
                "url": "https://example.com/gemini-2.0",
                "summary": "Google 發布 Gemini 2.0，原生支援工具調用，可能影響 Agent 開發範式。",
                "key_takeaway": "原生工具調用將簡化 Agent 開發，值得關注 ADK 更新。",
                "priority_score": 0.95,
                "tags": ["AI", "LLM"]
            },
            {
                "title": "Tesla Optimus Robot Demonstrates Complex Manipulation",
                "url": "https://example.com/optimus-manipulation",
                "summary": "Tesla Optimus 展示 95% 精準度的複雜物體操作，加速量產計劃。",
                "key_takeaway": "人形機器人靈巧操作技術突破，商業化加速。",
                "priority_score": 0.88,
                "tags": ["Robotics", "Manipulation"]
            },
            {
                "title": "New Framework for Multi-Agent Coordination",
                "url": "https://example.com/multi-agent-systems",
                "summary": "新的多代理協調框架，提升協作效率 50%。",
                "key_takeaway": "去中心化多代理架構提升系統可擴展性。",
                "priority_score": 0.82,
                "tags": ["AI", "Multi-Agent"]
            }
        ],
        "daily_insight": "今日重點聚焦於 AI 與 Robotics 的工程化進展：LLM 原生工具調用降低開發門檻，人形機器人操作精準度突破商業化關鍵，多代理系統協調效率顯著提升。",
        "recommended_action": "建議深入了解 Gemini 2.0 的工具調用機制，評估對現有 Agent 架構的影響。"
    }


class TestCuratorWithArticleStore:
    """測試 Curator 與 ArticleStore 的整合"""

    def test_fetch_and_process_articles(
        self,
        test_config,
        test_article_store,
        sample_articles_for_db
    ):
        """測試從資料庫取得文章並處理"""
        # 插入測試文章
        for article_data in sample_articles_for_db:
            test_article_store.store_article(article_data)

        # 建立 Curator Runner
        agent = create_curator_agent(test_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=test_article_store,
            config=test_config
        )

        # 取得文章
        articles = runner.fetch_analyzed_articles(max_articles=10)

        # 驗證結果
        assert len(articles) == 3
        assert articles[0]['priority_score'] == 0.95  # 最高優先度在前
        assert articles[0]['title'] == "Google Releases Gemini 2.0 with Native Tool Use"
        assert isinstance(articles[0]['tags'], list)  # 字串已轉為陣列
        assert "AI" in articles[0]['tags']

    def test_fetch_limited_articles(
        self,
        test_config,
        test_article_store,
        sample_articles_for_db
    ):
        """測試限制文章數量"""
        # 插入測試文章
        for article_data in sample_articles_for_db:
            test_article_store.store_article(article_data)

        agent = create_curator_agent(test_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=test_article_store,
            config=test_config
        )

        # 只取 2 篇
        articles = runner.fetch_analyzed_articles(max_articles=2)

        # 驗證結果
        assert len(articles) == 2
        assert articles[0]['priority_score'] >= articles[1]['priority_score']  # 確保排序


class TestCuratorWithFormatter:
    """測試 Curator 與 DigestFormatter 的整合"""

    def test_format_digest_html_and_text(self, test_config, sample_digest):
        """測試格式化 HTML 與純文字"""
        formatter = DigestFormatter()

        # 格式化 HTML
        html = formatter.format_html(sample_digest)

        # 驗證 HTML
        assert 'InsightCosmos Daily Digest' in html
        assert '<!DOCTYPE html>' in html
        assert 'Google Releases Gemini 2.0' in html
        assert '今日重點聚焦於 AI 與 Robotics' in html
        assert '建議深入了解 Gemini 2.0' in html

        # 格式化純文字
        text = formatter.format_text(sample_digest)

        # 驗證純文字
        assert 'InsightCosmos Daily Digest' in text
        assert 'Google Releases Gemini 2.0' in text
        assert '今日重點聚焦於 AI 與 Robotics' in text
        assert '建議深入了解 Gemini 2.0' in text

    def test_format_digest_with_priority_colors(self, test_config, sample_digest):
        """測試優先度顏色標記"""
        formatter = DigestFormatter()
        html = formatter.format_html(sample_digest)

        # 驗證 CSS class
        assert 'high-priority' in html  # 0.95 score
        assert 'medium-priority' in html  # 0.88 score


class TestCuratorWithEmailSender:
    """測試 Curator 與 EmailSender 的整合（Mock SMTP）"""

    def test_send_email_mock_smtp(self, test_config, sample_digest):
        """測試 Email 發送（Mock SMTP）"""
        # 建立 EmailSender
        email_config = EmailConfig(
            sender_email="test@example.com",
            sender_password="test_password"
        )
        email_sender = EmailSender(email_config)

        # 格式化 Digest
        formatter = DigestFormatter()
        html_body = formatter.format_html(sample_digest)
        text_body = formatter.format_text(sample_digest)

        # Mock SMTP
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # 發送 Email
            result = email_sender.send(
                to_email="ray@example.com",
                subject=f"InsightCosmos Daily Digest - {sample_digest['date']}",
                html_body=html_body,
                text_body=text_body
            )

            # 驗證結果
            assert result['status'] == 'success'
            assert 'Email sent to ray@example.com' in result['message']

            # 驗證 SMTP 調用
            mock_server.send_message.assert_called_once()


class TestCuratorFullPipeline:
    """測試 Curator 完整流程（Mock LLM）"""

    def test_full_curator_pipeline_with_mock(
        self,
        test_config,
        test_article_store,
        sample_articles_for_db,
        sample_digest
    ):
        """測試完整流程：資料庫 → LLM → 格式化 → Email（Mock）"""
        # 插入測試文章
        for article_data in sample_articles_for_db:
            test_article_store.store_article(article_data)

        # 建立 Curator Runner
        agent = create_curator_agent(test_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=test_article_store,
            config=test_config
        )

        # Mock LLM 回應
        mock_llm_response = json.dumps(sample_digest, ensure_ascii=False)

        with patch.object(runner, '_invoke_llm', return_value=mock_llm_response):
            # Mock EmailSender
            with patch.object(runner.email_sender, 'send') as mock_send:
                mock_send.return_value = {
                    "status": "success",
                    "message": "Email sent successfully"
                }

                # 執行完整流程
                result = runner.generate_and_send_digest(
                    recipient_email="ray@example.com",
                    max_articles=10
                )

                # 驗證結果
                assert result['status'] == 'success'
                assert 'digest' in result
                assert 'email_result' in result

                # 驗證 Digest 內容
                digest = result['digest']
                assert digest['date'] == sample_digest['date']
                assert digest['total_articles'] == 3
                assert len(digest['top_articles']) == 3

                # 驗證 Email 被調用
                mock_send.assert_called_once()

    def test_full_curator_pipeline_with_error_handling(
        self,
        test_config,
        test_article_store,
        sample_articles_for_db
    ):
        """測試完整流程的錯誤處理"""
        # 插入測試文章
        for article_data in sample_articles_for_db:
            test_article_store.store_article(article_data)

        agent = create_curator_agent(test_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=test_article_store,
            config=test_config
        )

        # Mock LLM 返回無效 JSON
        with patch.object(runner, '_invoke_llm', return_value="Invalid JSON response"):
            result = runner.generate_and_send_digest(
                recipient_email="ray@example.com",
                max_articles=10
            )

            # 驗證錯誤處理
            assert result['status'] == 'error'
            assert 'LLM failed to generate valid digest' in result['error']


# ===== 手動測試（需要真實 API Key 與 Email 設定）=====

@pytest.mark.manual
@pytest.mark.skipif(
    not os.getenv('GOOGLE_API_KEY'),
    reason="Requires GOOGLE_API_KEY environment variable"
)
class TestCuratorWithRealLLM:
    """測試 Curator 與真實 LLM 的整合（手動測試）"""

    def test_generate_digest_with_real_llm(
        self,
        test_config,
        test_article_store,
        sample_articles_for_db
    ):
        """使用真實 LLM 生成報告（手動測試）"""
        # 插入測試文章
        for article_data in sample_articles_for_db:
            test_article_store.store_article(article_data)

        # 建立 Curator Runner（使用真實 API Key）
        real_config = Config.from_env()
        agent = create_curator_agent(real_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=test_article_store,
            config=real_config
        )

        # 取得文章
        articles = runner.fetch_analyzed_articles(max_articles=10)

        # 生成 Digest（真實 LLM）
        digest = runner.generate_digest(articles)

        # 驗證結果
        assert digest is not None
        assert 'date' in digest
        assert 'total_articles' in digest
        assert 'top_articles' in digest
        assert 'daily_insight' in digest
        assert len(digest['top_articles']) > 0

        # 打印結果供人工檢查
        print("\n=== Generated Digest (Real LLM) ===")
        print(json.dumps(digest, ensure_ascii=False, indent=2))


@pytest.mark.manual
@pytest.mark.skipif(
    not all([os.getenv('EMAIL_ACCOUNT'), os.getenv('EMAIL_PASSWORD')]),
    reason="Requires EMAIL_ACCOUNT and EMAIL_PASSWORD environment variables"
)
class TestCuratorWithRealEmail:
    """測試 Curator 與真實 Email 的整合（手動測試）"""

    def test_send_real_email(self, test_config, sample_digest):
        """發送真實 Email（手動測試）"""
        # 載入真實 Email 設定
        real_config = Config.from_env()

        # 建立 EmailSender
        email_config = EmailConfig(
            sender_email=real_config.email_account,
            sender_password=real_config.email_password,
            smtp_host=real_config.smtp_host,
            smtp_port=real_config.smtp_port,
            use_tls=real_config.smtp_use_tls
        )

        # 測試連線
        email_sender = EmailSender(email_config)
        connection_result = email_sender.test_connection()

        assert connection_result['status'] == 'success', \
            f"Email connection failed: {connection_result.get('error')}"

        # 格式化 Digest
        formatter = DigestFormatter()
        html_body = formatter.format_html(sample_digest)
        text_body = formatter.format_text(sample_digest)

        # 發送測試郵件
        result = email_sender.send(
            to_email=real_config.email_account,  # 發送給自己
            subject=f"[TEST] InsightCosmos Daily Digest - {sample_digest['date']}",
            html_body=html_body,
            text_body=text_body
        )

        # 驗證結果
        assert result['status'] == 'success', \
            f"Email sending failed: {result.get('error')}"

        print("\n✅ Test email sent successfully!")
        print(f"   Check inbox: {real_config.email_account}")


@pytest.mark.manual
@pytest.mark.skipif(
    not all([os.getenv('GOOGLE_API_KEY'), os.getenv('EMAIL_ACCOUNT'), os.getenv('EMAIL_PASSWORD')]),
    reason="Requires GOOGLE_API_KEY, EMAIL_ACCOUNT, and EMAIL_PASSWORD"
)
class TestCuratorE2E:
    """端到端測試（真實 LLM + 真實 Email）"""

    def test_end_to_end_curator_pipeline(
        self,
        test_article_store,
        sample_articles_for_db
    ):
        """完整端到端測試（手動測試）"""
        # 插入測試文章
        for article_data in sample_articles_for_db:
            test_article_store.store_article(article_data)

        # 載入真實設定
        real_config = Config.from_env()

        # 建立 Curator Runner
        agent = create_curator_agent(real_config)
        runner = CuratorDailyRunner(
            agent=agent,
            article_store=test_article_store,
            config=real_config
        )

        # 執行完整流程（真實 LLM + 真實 Email）
        result = runner.generate_and_send_digest(
            recipient_email=real_config.email_account,  # 發送給自己
            max_articles=10
        )

        # 驗證結果
        assert result['status'] == 'success', \
            f"E2E test failed: {result.get('error')}"

        # 打印結果
        print("\n✅ End-to-End test completed successfully!")
        print(f"   Email sent to: {real_config.email_account}")
        print(f"   Digest date: {result['digest']['date']}")
        print(f"   Total articles: {result['digest']['total_articles']}")


def test_integration_module_imports():
    """測試整合測試模組可以正確匯入所有依賴"""
    from src.agents.curator_daily import create_curator_agent, CuratorDailyRunner
    from src.memory.database import Database
    from src.memory.article_store import ArticleStore
    from src.tools.digest_formatter import DigestFormatter
    from src.tools.email_sender import EmailSender, EmailConfig
    from src.utils.config import Config

    assert all([
        create_curator_agent,
        CuratorDailyRunner,
        Database,
        ArticleStore,
        DigestFormatter,
        EmailSender,
        EmailConfig,
        Config
    ])
