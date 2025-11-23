# -*- coding: utf-8 -*-
"""
Unit Tests for Scout Agent Tools

Tests the ADK tool wrappers (fetch_rss and search_articles) for Scout Agent.

Test Coverage:
    - fetch_rss tool wrapper
    - search_articles tool wrapper
    - Tool docstring completeness
    - Error handling

Usage:
    pytest tests/unit/test_scout_tools.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.agents.scout_agent import fetch_rss, search_articles


class TestFetchRSSTool:
    """Test suite for fetch_rss tool wrapper"""

    def test_fetch_rss_success(self):
        """TC-5-01: fetch_rss 工具正常调用"""
        # Mock RSSFetcher
        with patch('src.agents.scout_agent.RSSFetcher') as MockFetcher:
            mock_instance = MockFetcher.return_value
            mock_instance.fetch_rss_feeds.return_value = {
                'status': 'success',
                'articles': [
                    {
                        'url': 'https://example.com/article1',
                        'title': 'Test Article 1',
                        'summary': 'Summary 1',
                        'published_at': datetime.now(timezone.utc),
                        'source': 'rss',
                        'source_name': 'Example Feed'
                    }
                ],
                'errors': [],
                'summary': {
                    'total_feeds': 1,
                    'successful_feeds': 1,
                    'total_articles': 1
                }
            }

            # Call the tool
            result = fetch_rss(['https://example.com/feed/'])

            # Assertions
            assert result['status'] == 'success'
            assert len(result['articles']) == 1
            assert result['summary']['total_articles'] == 1
            assert 'url' in result['articles'][0]
            assert 'title' in result['articles'][0]

            # Verify RSSFetcher was called correctly
            MockFetcher.assert_called_once_with(timeout=30)
            mock_instance.fetch_rss_feeds.assert_called_once_with(
                feed_urls=['https://example.com/feed/'],
                max_articles_per_feed=10
            )

    def test_fetch_rss_with_max_articles(self):
        """Test fetch_rss with custom max_articles_per_feed"""
        with patch('src.agents.scout_agent.RSSFetcher') as MockFetcher:
            mock_instance = MockFetcher.return_value
            mock_instance.fetch_rss_feeds.return_value = {
                'status': 'success',
                'articles': [],
                'errors': [],
                'summary': {
                    'total_feeds': 1,
                    'successful_feeds': 1,
                    'total_articles': 0
                }
            }

            # Call with custom max_articles_per_feed
            result = fetch_rss(['https://example.com/feed/'], max_articles_per_feed=5)

            # Verify max_articles_per_feed was passed
            mock_instance.fetch_rss_feeds.assert_called_once_with(
                feed_urls=['https://example.com/feed/'],
                max_articles_per_feed=5
            )

    def test_fetch_rss_empty_list(self):
        """TC-5-02: fetch_rss 处理空列表"""
        with patch('src.agents.scout_agent.RSSFetcher') as MockFetcher:
            mock_instance = MockFetcher.return_value
            mock_instance.fetch_rss_feeds.return_value = {
                'status': 'success',
                'articles': [],
                'errors': [],
                'summary': {
                    'total_feeds': 0,
                    'successful_feeds': 0,
                    'total_articles': 0
                }
            }

            result = fetch_rss([])

            assert result['status'] == 'success'
            assert result['summary']['total_feeds'] == 0
            assert len(result['articles']) == 0

    def test_fetch_rss_exception_handling(self):
        """TC-5-03: fetch_rss 处理异常"""
        with patch('src.agents.scout_agent.RSSFetcher') as MockFetcher:
            # Simulate exception
            MockFetcher.side_effect = Exception("Network error")

            result = fetch_rss(['https://example.com/feed/'])

            # Should return error status
            assert result['status'] == 'error'
            assert len(result['errors']) > 0
            assert 'error_message' in result['errors'][0]
            assert 'Network error' in result['errors'][0]['error_message']
            assert result['summary']['successful_feeds'] == 0

    def test_fetch_rss_docstring_exists(self):
        """TC-5-05: 验证 fetch_rss 有完整的 docstring"""
        assert fetch_rss.__doc__ is not None
        assert len(fetch_rss.__doc__) > 0
        assert 'Args:' in fetch_rss.__doc__
        assert 'Returns:' in fetch_rss.__doc__
        assert 'Example:' in fetch_rss.__doc__


class TestSearchArticlesTool:
    """Test suite for search_articles tool wrapper"""

    def test_search_articles_success(self):
        """TC-5-04: search_articles 工具正常调用"""
        with patch('src.agents.scout_agent.GoogleSearchGroundingTool') as MockSearch:
            mock_instance = MockSearch.return_value
            mock_instance.search_articles.return_value = {
                'status': 'success',
                'query': 'AI multi-agent systems',
                'articles': [
                    {
                        'url': 'https://example.com/search-result',
                        'title': 'Search Result Article',
                        'summary': 'Summary',
                        'published_at': datetime.now(timezone.utc),
                        'source': 'google_search_grounding',
                        'source_name': 'example.com'
                    }
                ],
                'total_results': 1,
                'error_message': None
            }

            result = search_articles('AI multi-agent systems', max_results=10)

            # Assertions
            assert result['status'] == 'success'
            assert result['query'] == 'AI multi-agent systems'
            assert len(result['articles']) == 1
            assert result['total_results'] == 1

            # Verify GoogleSearchGroundingTool was called
            MockSearch.assert_called_once()
            mock_instance.search_articles.assert_called_once_with(
                query='AI multi-agent systems',
                max_results=10
            )
            mock_instance.close.assert_called_once()

    def test_search_articles_with_max_results(self):
        """Test search_articles with custom max_results"""
        with patch('src.agents.scout_agent.GoogleSearchGroundingTool') as MockSearch:
            mock_instance = MockSearch.return_value
            mock_instance.search_articles.return_value = {
                'status': 'success',
                'query': 'robotics',
                'articles': [],
                'total_results': 0,
                'error_message': None
            }

            result = search_articles('robotics', max_results=5)

            # Verify max_results was passed
            mock_instance.search_articles.assert_called_once_with(
                query='robotics',
                max_results=5
            )

    def test_search_articles_exception_handling(self):
        """TC-5-06: search_articles 处理异常"""
        with patch('src.agents.scout_agent.GoogleSearchGroundingTool') as MockSearch:
            # Simulate exception during initialization
            MockSearch.side_effect = Exception("API error")

            result = search_articles('test query')

            # Should return error status
            assert result['status'] == 'error'
            assert 'error_message' in result
            assert 'API error' in result['error_message']
            assert result['total_results'] == 0
            assert len(result['articles']) == 0

    def test_search_articles_tool_exception_handling(self):
        """Test search_articles handling tool.search_articles exception"""
        with patch('src.agents.scout_agent.GoogleSearchGroundingTool') as MockSearch:
            mock_instance = MockSearch.return_value
            # Simulate exception during search
            mock_instance.search_articles.side_effect = Exception("Search failed")

            result = search_articles('test query')

            assert result['status'] == 'error'
            assert 'Search failed' in result['error_message']

    def test_search_articles_docstring_exists(self):
        """TC-5-07: 验证 search_articles 有完整的 docstring"""
        assert search_articles.__doc__ is not None
        assert len(search_articles.__doc__) > 0
        assert 'Args:' in search_articles.__doc__
        assert 'Returns:' in search_articles.__doc__
        assert 'Example:' in search_articles.__doc__


class TestToolsIntegration:
    """Integration tests for tools working together"""

    def test_both_tools_have_consistent_output_format(self):
        """Verify both tools return consistent output format"""
        with patch('src.agents.scout_agent.RSSFetcher') as MockFetcher, \
             patch('src.agents.scout_agent.GoogleSearchGroundingTool') as MockSearch:

            # Setup mocks
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.fetch_rss_feeds.return_value = {
                'status': 'success',
                'articles': [{'url': 'rss-url', 'title': 'RSS Article'}],
                'summary': {'total_articles': 1}
            }

            mock_search = MockSearch.return_value
            mock_search.search_articles.return_value = {
                'status': 'success',
                'articles': [{'url': 'search-url', 'title': 'Search Article'}],
                'total_results': 1
            }

            # Call both tools
            rss_result = fetch_rss(['https://example.com/feed/'])
            search_result = search_articles('test query')

            # Both should have 'status' and 'articles'
            assert 'status' in rss_result
            assert 'articles' in rss_result
            assert 'status' in search_result
            assert 'articles' in search_result

            # Articles should have consistent structure
            assert isinstance(rss_result['articles'], list)
            assert isinstance(search_result['articles'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
