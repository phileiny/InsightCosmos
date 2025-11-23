"""
Unit Tests for Analyst Agent

Tests the AnalystAgent and AnalystAgentRunner functionality with mocked dependencies.

Test Coverage:
    - Agent creation
    - Prompt template loading and variable replacement
    - Input preparation
    - JSON parsing (valid, markdown-wrapped, invalid)
    - Default analysis generation
    - Error handling
    - Embedding text preparation

Run:
    pytest tests/unit/test_analyst_agent.py -v
    pytest tests/unit/test_analyst_agent.py::TestAnalystAgentCreation -v
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.agents.analyst_agent import (
    create_analyst_agent,
    AnalystAgentRunner
)
from src.utils.config import Config


class TestAnalystAgentCreation:
    """Test create_analyst_agent function"""

    def test_create_analyst_agent_default(self):
        """Test agent creation with default parameters"""
        agent = create_analyst_agent()

        assert agent is not None
        assert agent.name == "AnalystAgent"
        assert agent.model == "gemini-2.5-flash"
        assert agent.description == "Analyzes AI and Robotics articles, extracts insights, and scores priority."
        assert agent.output_key == "analysis_result"

    def test_create_analyst_agent_custom_model(self):
        """Test agent creation with custom model"""
        agent = create_analyst_agent(model="gemini-2.5-pro")

        assert agent.model == "gemini-2.5-pro"

    def test_create_analyst_agent_custom_user(self):
        """Test agent creation with custom user info"""
        agent = create_analyst_agent(
            user_name="Alice",
            user_interests="Machine Learning, Computer Vision"
        )

        # Check that template variables were replaced
        assert "Alice" in agent.instruction
        assert "Machine Learning, Computer Vision" in agent.instruction
        # Should not contain template markers
        assert "{{USER_NAME}}" not in agent.instruction
        assert "{{USER_INTERESTS}}" not in agent.instruction

    def test_prompt_template_variables_replaced(self):
        """Test that prompt template variables are correctly replaced"""
        agent = create_analyst_agent(
            user_name="Bob",
            user_interests="NLP, Transformers"
        )

        instruction = agent.instruction

        # Check replacements
        assert "Bob" in instruction
        assert "NLP, Transformers" in instruction

        # Check no template markers remain
        assert "{{" not in instruction
        assert "}}" not in instruction

    def test_prompt_template_file_not_found(self):
        """Test error handling when prompt file not found"""
        fake_path = Path("/nonexistent/path/fake_prompt.txt")

        with pytest.raises(FileNotFoundError):
            create_analyst_agent(prompt_path=fake_path)


class TestAnalystAgentRunner:
    """Test AnalystAgentRunner class"""

    @pytest.fixture
    def mock_agent(self):
        """Mock LlmAgent"""
        agent = Mock()
        agent.name = "AnalystAgent"
        agent.model = "gemini-2.5-flash"
        agent.description = "Test agent"
        agent.instruction = "Test instruction"
        agent.output_key = "analysis_result"
        return agent

    @pytest.fixture
    def mock_article_store(self):
        """Mock ArticleStore"""
        store = Mock()
        store.get_by_id = Mock()
        store.update_analysis = Mock()
        store.get_by_status = Mock()
        return store

    @pytest.fixture
    def mock_embedding_store(self):
        """Mock EmbeddingStore"""
        store = Mock()
        store.create = Mock(return_value=1)
        return store

    @pytest.fixture
    def mock_config(self):
        """Mock Config"""
        config = Mock(spec=Config)
        config.GOOGLE_API_KEY = "test_key"
        config.EMBEDDING_MODEL = "text-embedding-004"
        config.USER_NAME = "Ray"
        config.USER_INTERESTS = "AI, Robotics"
        return config

    @pytest.fixture
    def runner(self, mock_agent, mock_article_store, mock_embedding_store, mock_config):
        """Create AnalystAgentRunner with mocked dependencies"""
        return AnalystAgentRunner(
            agent=mock_agent,
            article_store=mock_article_store,
            embedding_store=mock_embedding_store,
            config=mock_config
        )

    def test_runner_initialization(self, runner, mock_agent, mock_article_store, mock_embedding_store):
        """Test runner initialization"""
        assert runner.agent == mock_agent
        assert runner.article_store == mock_article_store
        assert runner.embedding_store == mock_embedding_store
        assert runner.app_name == "insightcosmos_analyst"
        assert runner.session_service is not None

    def test_prepare_input(self, runner):
        """Test _prepare_input method"""
        article = {
            'id': 1,
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'content': 'This is test content about AI and robotics.',
            'source': 'rss',
            'source_name': 'Tech Blog',
            'published_at': '2025-11-23T10:00:00'
        }

        input_text = runner._prepare_input(article)

        assert 'Test Article' in input_text
        assert 'https://example.com/test' in input_text
        assert 'This is test content about AI and robotics.' in input_text
        assert 'Tech Blog' in input_text
        assert '請分析以下文章' in input_text

    def test_prepare_input_truncates_long_content(self, runner):
        """Test that long content is truncated"""
        long_content = 'A' * 15000  # 15k characters

        article = {
            'id': 1,
            'title': 'Test',
            'url': 'https://example.com',
            'content': long_content,
            'source': 'rss'
        }

        input_text = runner._prepare_input(article)

        # Should be truncated to ~10k + metadata
        assert len(input_text) < 12000
        assert '[內容已截斷...]' in input_text

    def test_parse_analysis_valid_json(self, runner):
        """Test parsing valid JSON response"""
        response_text = '''
        {
          "summary": "Test summary",
          "key_insights": ["Insight 1", "Insight 2"],
          "tech_stack": ["Python", "LLM"],
          "category": "AI Agent",
          "trends": ["Multi-Agent"],
          "relevance_score": 0.85,
          "priority_score": 0.78,
          "reasoning": "Test reasoning"
        }
        '''

        analysis = runner._parse_analysis(response_text)

        assert analysis['summary'] == "Test summary"
        assert len(analysis['key_insights']) == 2
        assert analysis['relevance_score'] == 0.85
        assert analysis['priority_score'] == 0.78

    def test_parse_analysis_markdown_wrapped(self, runner):
        """Test parsing markdown-wrapped JSON"""
        response_text = '''
        這是分析結果：

        ```json
        {
          "summary": "Markdown wrapped summary",
          "key_insights": ["Insight A"],
          "tech_stack": ["Go"],
          "category": "Tools",
          "trends": ["DevOps"],
          "relevance_score": 0.65,
          "priority_score": 0.60,
          "reasoning": "Markdown test"
        }
        ```

        分析完成。
        '''

        analysis = runner._parse_analysis(response_text)

        assert analysis['summary'] == "Markdown wrapped summary"
        assert analysis['relevance_score'] == 0.65

    def test_parse_analysis_invalid_json(self, runner):
        """Test handling of invalid JSON"""
        response_text = "This is not valid JSON at all!"

        analysis = runner._parse_analysis(response_text)

        # Should return default analysis
        assert analysis['summary'] == "無法生成摘要（LLM 輸出格式錯誤）"
        assert analysis['relevance_score'] == 0.0
        assert analysis['priority_score'] == 0.0

    def test_parse_analysis_missing_fields(self, runner):
        """Test handling of JSON with missing required fields"""
        response_text = '''
        {
          "summary": "Incomplete data",
          "key_insights": []
        }
        '''

        analysis = runner._parse_analysis(response_text)

        # Should return default analysis due to missing fields
        assert analysis['summary'] == "無法生成摘要（LLM 輸出格式錯誤）"

    def test_parse_analysis_invalid_score_range(self, runner):
        """Test that invalid scores are clamped to 0-1"""
        response_text = '''
        {
          "summary": "Test",
          "key_insights": [],
          "tech_stack": [],
          "category": "AI Agent",
          "trends": [],
          "relevance_score": 1.5,
          "priority_score": -0.2,
          "reasoning": "Test"
        }
        '''

        analysis = runner._parse_analysis(response_text)

        # Scores should be clamped
        assert 0.0 <= analysis['relevance_score'] <= 1.0
        assert 0.0 <= analysis['priority_score'] <= 1.0

    def test_get_default_analysis(self, runner):
        """Test _get_default_analysis method"""
        default = runner._get_default_analysis()

        assert default['summary'] == "無法生成摘要（LLM 輸出格式錯誤）"
        assert default['key_insights'] == []
        assert default['tech_stack'] == []
        assert default['category'] == "Unknown"
        assert default['trends'] == []
        assert default['relevance_score'] == 0.0
        assert default['priority_score'] == 0.0
        assert "LLM 返回格式無效" in default['reasoning']

    def test_prepare_embedding_text(self, runner):
        """Test _prepare_embedding_text method"""
        analysis = {
            'summary': 'This is a summary.',
            'key_insights': ['Insight 1', 'Insight 2', 'Insight 3']
        }

        text = runner._prepare_embedding_text(analysis)

        assert 'This is a summary.' in text
        assert 'Insight 1' in text
        assert 'Insight 2' in text
        assert 'Insight 3' in text

    def test_prepare_embedding_text_empty_insights(self, runner):
        """Test embedding text with no insights"""
        analysis = {
            'summary': 'Only summary.',
            'key_insights': []
        }

        text = runner._prepare_embedding_text(analysis)

        assert text == 'Only summary.'

    def test_get_error_suggestion(self, runner):
        """Test _get_error_suggestion method"""
        # Test various error types
        assert "檢查文章 ID" in runner._get_error_suggestion(ValueError("Article not found"))
        assert "內容為空" in runner._get_error_suggestion(ValueError("Content is empty"))
        assert "API 配額" in runner._get_error_suggestion(RuntimeError("Quota exceeded"))
        assert "超時" in runner._get_error_suggestion(TimeoutError("Request timeout"))
        assert "格式錯誤" in runner._get_error_suggestion(json.JSONDecodeError("Invalid JSON", "", 0))
        assert "未知錯誤" in runner._get_error_suggestion(Exception("Unknown error"))


class TestAnalystAgentIntegration:
    """Integration tests with mocked LLM and embedding"""

    @pytest.fixture
    def mock_agent(self):
        agent = Mock()
        agent.name = "AnalystAgent"
        agent.model = "gemini-2.5-flash"
        return agent

    @pytest.fixture
    def mock_article_store(self):
        store = Mock()

        # Mock get_by_id
        store.get_by_id = Mock(return_value={
            'id': 1,
            'title': 'Test Article About Multi-Agent Systems',
            'url': 'https://example.com/multi-agent',
            'content': 'This article discusses multi-agent systems using Google ADK...',
            'source': 'rss',
            'source_name': 'AI Research Blog',
            'published_at': '2025-11-23T10:00:00',
            'status': 'pending'
        })

        # Mock update_analysis
        store.update_analysis = Mock()

        # Mock get_by_status
        store.get_by_status = Mock(return_value=[
            {'id': 1, 'title': 'Article 1'},
            {'id': 2, 'title': 'Article 2'}
        ])

        return store

    @pytest.fixture
    def mock_embedding_store(self):
        store = Mock()
        store.create = Mock(return_value=101)
        return store

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.GOOGLE_API_KEY = "test_key"
        config.EMBEDDING_MODEL = "text-embedding-004"
        config.USER_NAME = "Ray"
        config.USER_INTERESTS = "AI, Robotics"
        return config

    @pytest.fixture
    def runner(self, mock_agent, mock_article_store, mock_embedding_store, mock_config):
        return AnalystAgentRunner(
            agent=mock_agent,
            article_store=mock_article_store,
            embedding_store=mock_embedding_store,
            config=mock_config
        )

    @pytest.mark.asyncio
    async def test_analyze_article_success(self, runner, mock_article_store, mock_embedding_store):
        """Test successful article analysis"""
        # Mock LLM response
        mock_llm_response = json.dumps({
            "summary": "This article discusses multi-agent systems.",
            "key_insights": ["ADK supports multi-agent orchestration", "Sequential agents are powerful"],
            "tech_stack": ["Google ADK", "Python"],
            "category": "AI Agent",
            "trends": ["Multi-Agent"],
            "relevance_score": 0.95,
            "priority_score": 0.90,
            "reasoning": "Highly relevant to Ray's interests."
        })

        # Mock _invoke_llm
        with patch.object(runner, '_invoke_llm', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_llm_response

            # Mock _generate_embedding
            with patch.object(runner, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [0.1] * 768

                # Run analysis
                result = await runner.analyze_article(article_id=1, skip_if_analyzed=False)

                # Verify result
                assert result['status'] == 'success'
                assert result['article_id'] == 1
                assert result['analysis']['priority_score'] == 0.90
                assert result['embedding_id'] == 101

                # Verify store calls
                mock_article_store.update_analysis.assert_called_once()
                mock_embedding_store.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_article_not_found(self, runner, mock_article_store):
        """Test analysis when article not found"""
        mock_article_store.get_by_id.return_value = None

        result = await runner.analyze_article(article_id=999)

        assert result['status'] == 'error'
        assert result['article_id'] == 999
        assert 'not found' in result['error_message'].lower()

    @pytest.mark.asyncio
    async def test_analyze_article_empty_content(self, runner, mock_article_store):
        """Test analysis when article content is empty"""
        mock_article_store.get_by_id.return_value = {
            'id': 1,
            'title': 'Test',
            'url': 'https://example.com',
            'content': '',  # Empty content
            'source': 'rss',
            'status': 'pending'
        }

        result = await runner.analyze_article(article_id=1)

        assert result['status'] == 'error'
        assert 'empty' in result['error_message'].lower()

    @pytest.mark.asyncio
    async def test_analyze_article_skip_if_analyzed(self, runner, mock_article_store):
        """Test skipping already analyzed articles"""
        mock_article_store.get_by_id.return_value = {
            'id': 1,
            'title': 'Test',
            'url': 'https://example.com',
            'content': 'Content',
            'source': 'rss',
            'status': 'analyzed'  # Already analyzed
        }

        result = await runner.analyze_article(article_id=1, skip_if_analyzed=True)

        assert result['status'] == 'skipped'
        assert result['article_id'] == 1


def test_module_imports():
    """Test that all expected symbols can be imported"""
    from src.agents.analyst_agent import (
        create_analyst_agent,
        AnalystAgentRunner,
        analyze_article
    )

    assert create_analyst_agent is not None
    assert AnalystAgentRunner is not None
    assert analyze_article is not None
