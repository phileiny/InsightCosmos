"""
Unit Tests for Digest Formatter

測試 DigestFormatter 類的所有功能，包括 HTML 和純文字格式化。

測試涵蓋範圍:
    - 基本 HTML 格式化
    - 含行動建議的 HTML
    - 優先度顏色標記
    - 基本純文字格式化
    - 含行動建議的純文字
    - 空文章列表處理
    - 特殊字元處理
    - 長內容處理

執行方式:
    pytest tests/unit/test_digest_formatter.py -v
    pytest tests/unit/test_digest_formatter.py::TestDigestFormatterHTML -v
"""

import pytest
from datetime import datetime

from src.tools.digest_formatter import DigestFormatter, format_html, format_text


class TestDigestFormatterInitialization:
    """Test DigestFormatter initialization"""

    def test_formatter_initialization(self):
        """測試 DigestFormatter 初始化"""
        formatter = DigestFormatter()

        assert formatter is not None
        assert formatter.logger is not None


class TestDigestFormatterHTML:
    """Test DigestFormatter.format_html method"""

    @pytest.fixture
    def formatter(self):
        """建立測試用 DigestFormatter"""
        return DigestFormatter()

    @pytest.fixture
    def sample_digest_basic(self):
        """基本測試數據（無 recommended_action）"""
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
                    "priority_score": 0.75,
                    "tags": ["Robotics", "Manipulation"]
                }
            ],
            "daily_insight": "今日重點聚焦於 AI 與 Robotics 的工程化進展。"
        }

    @pytest.fixture
    def sample_digest_with_action(self):
        """含行動建議的測試數據"""
        return {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "summary": "Test summary.",
                    "key_takeaway": "Test takeaway.",
                    "priority_score": 0.85,
                    "tags": ["AI"]
                }
            ],
            "daily_insight": "Test insight.",
            "recommended_action": "建議深入了解 Gemini 2.0 的工具調用機制。"
        }

    def test_format_html_basic(self, formatter, sample_digest_basic):
        """測試基本 HTML 格式化"""
        html = formatter.format_html(sample_digest_basic)

        # 驗證 HTML 結構
        assert '<!DOCTYPE html>' in html
        assert '<html lang="zh-TW">' in html
        assert 'InsightCosmos Daily Digest' in html

        # 驗證日期
        assert '2025年11月24日' in html
        assert '2 篇精選文章' in html

        # 驗證文章內容
        assert 'Google Releases Gemini 2.0' in html
        assert 'https://example.com/gemini-2.0' in html
        assert '原生支援工具調用' in html
        assert '原生工具調用將簡化 Agent 開發' in html

        # 驗證 tags
        assert 'AI' in html
        assert 'LLM' in html
        assert 'Robotics' in html

        # 驗證 priority_score
        assert '0.95' in html
        assert '0.75' in html

        # 驗證洞察區塊
        assert '今日洞察' in html
        assert '今日重點聚焦於 AI 與 Robotics 的工程化進展' in html

        # 驗證 footer
        assert 'Powered by Google ADK & Gemini 2.5' in html

    def test_format_html_with_action(self, formatter, sample_digest_with_action):
        """測試含 recommended_action 的 HTML 格式化"""
        html = formatter.format_html(sample_digest_with_action)

        # 驗證行動建議區塊
        assert '建議行動' in html
        assert '建議深入了解 Gemini 2.0 的工具調用機制' in html
        assert 'action-section' in html

    def test_format_html_priority_colors(self, formatter):
        """測試優先度顏色標記（high/medium/low）"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 3,
            "top_articles": [
                {
                    "title": "High Priority Article",
                    "url": "https://example.com/high",
                    "summary": "High priority summary.",
                    "key_takeaway": "High priority takeaway.",
                    "priority_score": 0.95,  # >= 0.9 → high-priority
                    "tags": ["AI"]
                },
                {
                    "title": "Medium Priority Article",
                    "url": "https://example.com/medium",
                    "summary": "Medium priority summary.",
                    "key_takeaway": "Medium priority takeaway.",
                    "priority_score": 0.75,  # >= 0.7 → medium-priority
                    "tags": ["Robotics"]
                },
                {
                    "title": "Low Priority Article",
                    "url": "https://example.com/low",
                    "summary": "Low priority summary.",
                    "key_takeaway": "Low priority takeaway.",
                    "priority_score": 0.50,  # < 0.7 → low-priority
                    "tags": ["Tools"]
                }
            ],
            "daily_insight": "Test insight."
        }

        html = formatter.format_html(digest)

        # 驗證優先度 CSS class
        assert 'high-priority' in html
        assert 'medium-priority' in html
        assert 'low-priority' in html

    def test_format_html_empty_articles(self, formatter):
        """測試空文章列表處理"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 0,
            "top_articles": [],
            "daily_insight": "今日無文章。"
        }

        html = formatter.format_html(digest)

        # 驗證顯示「暫無文章」
        assert '暫無文章' in html
        assert 'InsightCosmos Daily Digest' in html
        assert '今日無文章' in html

    def test_format_html_special_characters(self, formatter):
        """測試特殊字元處理（HTML escape）"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Article with <script>alert('XSS')</script>",
                    "url": "https://example.com/test",
                    "summary": "Summary with & < > characters.",
                    "key_takeaway": "Takeaway with \"quotes\" and 'apostrophes'.",
                    "priority_score": 0.80,
                    "tags": ["AI"]
                }
            ],
            "daily_insight": "Insight with special chars: & < > \" '."
        }

        html = formatter.format_html(digest)

        # 驗證特殊字元被轉義（HTML escape）
        assert '&lt;script&gt;' in html  # < 被轉義為 &lt;
        assert '&amp;' in html           # & 被轉義為 &amp;
        assert '&gt;' in html            # > 被轉義為 &gt;

        # 確保沒有原始的危險字元
        assert '<script>' not in html

    def test_format_html_long_content(self, formatter):
        """測試長內容處理（確保不會因過長而崩潰）"""
        long_summary = "A" * 1000  # 1000 字元的摘要
        long_takeaway = "B" * 500  # 500 字元的核心要點

        digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Long Content Article",
                    "url": "https://example.com/long",
                    "summary": long_summary,
                    "key_takeaway": long_takeaway,
                    "priority_score": 0.80,
                    "tags": ["AI"]
                }
            ],
            "daily_insight": "Insight."
        }

        html = formatter.format_html(digest)

        # 驗證長內容被正確包含（不崩潰）
        assert long_summary in html
        assert long_takeaway in html
        assert 'Long Content Article' in html

    def test_format_html_tags_as_string(self, formatter):
        """測試 tags 為逗號分隔字串時的處理"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "summary": "Test summary.",
                    "key_takeaway": "Test takeaway.",
                    "priority_score": 0.80,
                    "tags": "AI, Robotics, Multi-Agent"  # 字串格式，而非陣列
                }
            ],
            "daily_insight": "Test insight."
        }

        html = formatter.format_html(digest)

        # 驗證 tags 被正確分割並顯示
        assert 'AI' in html
        assert 'Robotics' in html
        assert 'Multi-Agent' in html

    def test_format_html_missing_optional_fields(self, formatter):
        """測試缺少可選欄位時的處理"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Minimal Article",
                    "url": "https://example.com/minimal"
                    # 缺少 summary, key_takeaway, priority_score, tags
                }
            ]
            # 缺少 daily_insight, recommended_action
        }

        # 應該不會崩潰，使用預設值
        html = formatter.format_html(digest)

        assert 'Minimal Article' in html
        assert 'InsightCosmos Daily Digest' in html


class TestDigestFormatterText:
    """Test DigestFormatter.format_text method"""

    @pytest.fixture
    def formatter(self):
        return DigestFormatter()

    @pytest.fixture
    def sample_digest_basic(self):
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
                    "priority_score": 0.75,
                    "tags": ["Robotics"]
                }
            ],
            "daily_insight": "今日重點聚焦於 AI 與 Robotics 的工程化進展。"
        }

    def test_format_text_basic(self, formatter, sample_digest_basic):
        """測試基本純文字格式化"""
        text = formatter.format_text(sample_digest_basic)

        # 驗證標題區塊
        assert 'InsightCosmos Daily Digest' in text
        assert '2025年11月24日' in text
        assert '今日精選: 2 篇文章' in text

        # 驗證文章內容
        assert '[1] Google Releases Gemini 2.0' in text
        assert 'https://example.com/gemini-2.0' in text
        assert '摘要:' in text
        assert 'Google 發布 Gemini 2.0' in text
        assert '核心要點:' in text
        assert '原生工具調用將簡化 Agent 開發' in text

        # 驗證 tags 與優先度
        assert '標籤: AI, LLM' in text
        assert '優先度: 0.95' in text

        # 驗證洞察區塊
        assert '今日洞察' in text
        assert '今日重點聚焦於 AI 與 Robotics 的工程化進展' in text

        # 驗證 footer
        assert 'InsightCosmos 自動生成' in text
        assert 'Powered by Google ADK & Gemini 2.5' in text

    def test_format_text_with_action(self, formatter):
        """測試含 recommended_action 的純文字格式化"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "summary": "Test summary.",
                    "key_takeaway": "Test takeaway.",
                    "priority_score": 0.85,
                    "tags": ["AI"]
                }
            ],
            "daily_insight": "Test insight.",
            "recommended_action": "建議深入了解 Gemini 2.0 的工具調用機制。"
        }

        text = formatter.format_text(digest)

        # 驗證行動建議區塊
        assert '建議行動' in text
        assert '建議深入了解 Gemini 2.0 的工具調用機制' in text

    def test_format_text_empty_articles(self, formatter):
        """測試空文章列表處理"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 0,
            "top_articles": [],
            "daily_insight": "今日無文章。"
        }

        text = formatter.format_text(digest)

        # 驗證顯示「暫無文章」
        assert '暫無文章' in text
        assert 'InsightCosmos Daily Digest' in text
        assert '今日無文章' in text

    def test_format_text_tags_as_string(self, formatter):
        """測試 tags 為字串時的處理"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "summary": "Test summary.",
                    "key_takeaway": "Test takeaway.",
                    "priority_score": 0.80,
                    "tags": "AI, Robotics, Multi-Agent"  # 字串格式
                }
            ],
            "daily_insight": "Test insight."
        }

        text = formatter.format_text(digest)

        # 驗證 tags 被正確處理
        assert '標籤: AI, Robotics, Multi-Agent' in text

    def test_format_text_structure(self, formatter, sample_digest_basic):
        """測試純文字格式結構清晰（使用分隔線）"""
        text = formatter.format_text(sample_digest_basic)

        # 驗證分隔線存在
        assert '=' * 60 in text  # 標題分隔線
        assert '-' * 60 in text  # 文章分隔線

    def test_format_text_missing_optional_fields(self, formatter):
        """測試缺少可選欄位時的處理"""
        digest = {
            "date": "2025-11-24",
            "total_articles": 1,
            "top_articles": [
                {
                    "title": "Minimal Article",
                    "url": "https://example.com/minimal"
                }
            ]
        }

        # 應該不會崩潰
        text = formatter.format_text(digest)

        assert 'Minimal Article' in text
        assert 'InsightCosmos Daily Digest' in text


class TestDigestFormatterHelpers:
    """Test DigestFormatter helper methods"""

    @pytest.fixture
    def formatter(self):
        return DigestFormatter()

    def test_get_priority_class_high(self, formatter):
        """測試高優先度（>= 0.9）CSS class"""
        assert formatter._get_priority_class(0.95) == 'high-priority'
        assert formatter._get_priority_class(0.90) == 'high-priority'

    def test_get_priority_class_medium(self, formatter):
        """測試中優先度（>= 0.7）CSS class"""
        assert formatter._get_priority_class(0.85) == 'medium-priority'
        assert formatter._get_priority_class(0.70) == 'medium-priority'

    def test_get_priority_class_low(self, formatter):
        """測試低優先度（< 0.7）CSS class"""
        assert formatter._get_priority_class(0.65) == 'low-priority'
        assert formatter._get_priority_class(0.50) == 'low-priority'
        assert formatter._get_priority_class(0.00) == 'low-priority'


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.fixture
    def sample_digest(self):
        return {
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

    def test_format_html_function(self, sample_digest):
        """測試 format_html 便利函式"""
        html = format_html(sample_digest)

        assert 'InsightCosmos Daily Digest' in html
        assert 'Test Article' in html
        assert '<!DOCTYPE html>' in html

    def test_format_text_function(self, sample_digest):
        """測試 format_text 便利函式"""
        text = format_text(sample_digest)

        assert 'InsightCosmos Daily Digest' in text
        assert 'Test Article' in text


def test_module_imports():
    """測試模組可以正確匯入"""
    from src.tools.digest_formatter import DigestFormatter, format_html, format_text

    assert DigestFormatter is not None
    assert format_html is not None
    assert format_text is not None
