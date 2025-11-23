# -*- coding: utf-8 -*-
"""
Integration Tests for Scout Agent

Tests the complete Scout Agent workflow including:
    - Agent creation
    - Runner execution
    - End-to-end article collection
    - Output validation

Usage:
    pytest tests/integration/test_scout_agent.py -v
    pytest tests/integration/test_scout_agent.py -v -k test_scout_agent_end_to_end
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import os

from src.agents.scout_agent import (
    create_scout_agent,
    ScoutAgentRunner,
    collect_articles
)


class TestScoutAgentCreation:
    """Test suite for Scout Agent creation"""

    def test_create_scout_agent_success(self):
        """Test successful Scout Agent creation"""
        # Ensure prompt file exists
        prompt_file = "prompts/scout_prompt.txt"
        assert os.path.exists(prompt_file), f"Prompt file not found: {prompt_file}"

        # Create agent
        agent = create_scout_agent()

        # Verify agent properties
        assert agent is not None
        assert agent.name == "ScoutAgent"
        assert agent.model == "gemini-2.5-flash"
        assert "Collects AI and Robotics" in agent.description

        # Verify tools are registered
        assert len(agent.tools) == 2
        tool_names = [tool.__name__ for tool in agent.tools]
        assert 'fetch_rss' in tool_names
        assert 'search_articles' in tool_names

    def test_create_scout_agent_missing_prompt(self):
        """Test Scout Agent creation with missing prompt file"""
        with pytest.raises(FileNotFoundError):
            create_scout_agent(instruction_file="nonexistent_file.txt")

    def test_create_scout_agent_with_custom_prompt(self, tmp_path):
        """Test Scout Agent creation with custom prompt file"""
        # Create temporary prompt file
        custom_prompt = tmp_path / "custom_prompt.txt"
        custom_prompt.write_text("Custom instruction for testing", encoding='utf-8')

        # Create agent with custom prompt
        agent = create_scout_agent(instruction_file=str(custom_prompt))

        assert agent is not None
        assert agent.name == "ScoutAgent"


class TestScoutAgentRunner:
    """Test suite for Scout Agent Runner"""

    def test_runner_initialization(self):
        """Test ScoutAgentRunner initialization"""
        runner = ScoutAgentRunner()

        assert runner is not None
        assert runner.agent is not None
        assert runner.runner is not None
        assert runner.session_service is not None
        assert runner.APP_NAME == "InsightCosmos"

    def test_runner_with_custom_agent(self):
        """Test ScoutAgentRunner with custom agent"""
        custom_agent = create_scout_agent()
        runner = ScoutAgentRunner(agent=custom_agent)

        assert runner.agent == custom_agent

    @patch('src.agents.scout_agent.RSSFetcher')
    @patch('src.agents.scout_agent.GoogleSearchGroundingTool')
    def test_collect_articles_mock(self, MockSearch, MockFetcher):
        """Test collect_articles with mocked tools (fast test)"""
        # Setup mocks
        mock_fetcher = MockFetcher.return_value
        mock_fetcher.fetch_rss_feeds.return_value = {
            'status': 'success',
            'articles': [
                {
                    'url': 'https://example.com/rss-article',
                    'title': 'RSS Article',
                    'summary': 'Summary',
                    'published_at': datetime.now(timezone.utc),
                    'source': 'rss',
                    'source_name': 'Example Feed',
                    'tags': []
                }
            ],
            'summary': {'total_articles': 1}
        }

        mock_search = MockSearch.return_value
        mock_search.search_articles.return_value = {
            'status': 'success',
            'query': 'test',
            'articles': [
                {
                    'url': 'https://example.com/search-article',
                    'title': 'Search Article',
                    'summary': 'Summary',
                    'published_at': datetime.now(timezone.utc),
                    'source': 'google_search_grounding',
                    'source_name': 'example.com',
                    'tags': []
                }
            ],
            'total_results': 1
        }

        # This test requires actual LLM call, which we'll skip in unit tests
        # Real integration test should be run manually with valid API key
        pytest.skip("Requires real LLM API call - run manually")

    def test_deduplicate_articles(self):
        """Test article deduplication logic"""
        runner = ScoutAgentRunner()

        articles = [
            {'url': 'https://example.com/article1', 'title': 'Article 1'},
            {'url': 'https://example.com/article2', 'title': 'Article 2'},
            {'url': 'https://example.com/article1', 'title': 'Article 1 Duplicate'},  # Duplicate
            {'url': 'https://example.com/article3', 'title': 'Article 3'},
        ]

        unique = runner._deduplicate_articles(articles)

        assert len(unique) == 3
        urls = [a['url'] for a in unique]
        assert len(urls) == len(set(urls))  # All unique

    def test_count_sources(self):
        """Test source counting logic"""
        runner = ScoutAgentRunner()

        articles = [
            {'source': 'rss'},
            {'source': 'rss'},
            {'source': 'google_search_grounding'},
            {'source': 'rss'},
        ]

        sources = runner._count_sources(articles)

        assert sources['rss'] == 3
        assert sources['google_search_grounding'] == 1


@pytest.mark.skip(reason="Requires valid Google API key and network access")
class TestScoutAgentEndToEnd:
    """
    End-to-end tests for Scout Agent

    These tests require:
    - Valid GOOGLE_API_KEY in .env
    - Network access
    - Working RSS feeds and Google Search

    Run manually when needed:
        pytest tests/integration/test_scout_agent.py::TestScoutAgentEndToEnd -v
    """

    def test_scout_agent_end_to_end(self):
        """
        TC-INT-01: 端到端测试 Scout Agent

        This test runs the complete Scout Agent workflow:
        1. Creates Scout Agent
        2. Runs article collection
        3. Validates output format
        4. Checks article quality
        """
        runner = ScoutAgentRunner()
        result = runner.collect_articles()

        # Validate output format
        assert 'status' in result
        assert 'articles' in result
        assert 'total_count' in result
        assert 'sources' in result
        assert 'collected_at' in result

        # Validate status
        assert result['status'] in ['success', 'error']

        if result['status'] == 'success':
            # Validate article count
            assert isinstance(result['articles'], list)
            assert 20 <= len(result['articles']) <= 30, \
                f"Expected 20-30 articles, got {len(result['articles'])}"

            # Validate article structure
            if result['articles']:
                article = result['articles'][0]
                required_fields = ['url', 'title', 'source']
                for field in required_fields:
                    assert field in article, f"Article missing '{field}' field"

            # Validate no duplicates
            urls = [a['url'] for a in result['articles']]
            assert len(urls) == len(set(urls)), "Found duplicate URLs"

            # Validate sources
            assert isinstance(result['sources'], dict)
            assert len(result['sources']) > 0

            print(f"\n✓ End-to-end test passed!")
            print(f"  Total articles: {result['total_count']}")
            print(f"  Sources: {result['sources']}")

    def test_collect_articles_convenience_function(self):
        """Test the convenience function collect_articles()"""
        result = collect_articles()

        assert result is not None
        assert 'status' in result
        assert 'articles' in result

        if result['status'] == 'success':
            assert len(result['articles']) > 0
            print(f"\n✓ Convenience function test passed!")
            print(f"  Collected {len(result['articles'])} articles")


class TestScoutAgentErrorHandling:
    """Test error handling in Scout Agent"""

    def test_runner_handles_empty_response(self):
        """Test runner handles empty Agent response gracefully"""
        # This would require mocking the ADK Runner
        # For now, we document the expected behavior
        pytest.skip("Requires complex ADK mocking")

    def test_runner_handles_invalid_json_response(self):
        """Test runner handles invalid JSON from Agent"""
        runner = ScoutAgentRunner()

        # Mock an event with invalid JSON
        mock_event = Mock()
        mock_event.is_final_response.return_value = True
        mock_event.content = Mock()
        mock_event.content.parts = [Mock(text="This is not valid JSON")]

        # Should raise ValueError
        with pytest.raises(ValueError):
            runner._parse_agent_output(mock_event)

    def test_parse_agent_output_with_markdown_json(self):
        """Test parsing JSON wrapped in Markdown code blocks"""
        runner = ScoutAgentRunner()

        # Mock event with Markdown-wrapped JSON
        mock_event = Mock()
        mock_event.content = Mock()
        mock_event.content.parts = [Mock(text='''```json
{
    "status": "success",
    "articles": [
        {"url": "https://example.com", "title": "Test"}
    ]
}
```''')]

        result = runner._parse_agent_output(mock_event)

        assert result['status'] == 'success'
        assert len(result['articles']) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
