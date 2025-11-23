"""
Unit tests for InsightCosmos RSS Fetcher Tool

Tests cover:
- RSSFetcher initialization
- URL validation
- Single feed fetching
- Batch feed fetching
- Feed entry parsing
- Date parsing
- Error handling

Test Cases:
    TC-3-01: RSSFetcher initialization
    TC-3-02: Valid URL validation
    TC-3-03: Invalid URL validation
    TC-3-04: Single RSS feed fetch (success)
    TC-3-05: Single RSS feed fetch (invalid URL)
    TC-3-06: Batch fetch (all success)
    TC-3-07: Batch fetch (partial failure)
    TC-3-08: Article limit enforcement
    TC-3-09: Parse feed entry metadata
    TC-3-10: Parse published date (RFC 2822)
    TC-3-11: Parse published date (ISO 8601)
    TC-3-12: Parse published date (invalid format)

Run with: pytest tests/unit/test_fetcher.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import feedparser

from src.tools.fetcher import RSSFetcher


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def fetcher():
    """Create RSSFetcher instance"""
    return RSSFetcher(timeout=10)


@pytest.fixture
def mock_feed_response():
    """Mock feedparser response"""
    return {
        'feed': {
            'title': 'Test Feed'
        },
        'entries': [
            {
                'link': 'https://example.com/article1',
                'title': 'Test Article 1',
                'summary': 'Summary 1',
                'published': 'Wed, 20 Nov 2024 10:00:00 GMT',
                'tags': [{'term': 'AI'}, {'term': 'Tech'}]
            },
            {
                'link': 'https://example.com/article2',
                'title': 'Test Article 2',
                'summary': 'Summary 2',
                'published': '2024-11-20T11:00:00Z'
            }
        ],
        'bozo': False
    }


# ========================================
# TC-3-01: RSSFetcher Initialization
# ========================================

def test_fetcher_initialization():
    """
    TC-3-01: Test RSSFetcher initialization

    Expected:
    - RSSFetcher object created successfully
    - Default timeout is 30 seconds
    - User agent is set
    """
    fetcher = RSSFetcher()

    assert fetcher is not None
    assert fetcher.timeout == 30
    assert 'InsightCosmos' in fetcher.user_agent
    assert fetcher.logger is not None


def test_fetcher_custom_timeout():
    """Test RSSFetcher with custom timeout"""
    fetcher = RSSFetcher(timeout=15)

    assert fetcher.timeout == 15


# ========================================
# TC-3-02: Valid URL Validation
# ========================================

def test_validate_url_valid():
    """
    TC-3-02: Test URL validation with valid URLs

    Expected:
    - HTTP and HTTPS URLs return True
    """
    assert RSSFetcher.validate_url('https://example.com/feed/') is True
    assert RSSFetcher.validate_url('http://example.com/feed/') is True
    assert RSSFetcher.validate_url('https://example.com/rss.xml') is True


# ========================================
# TC-3-03: Invalid URL Validation
# ========================================

def test_validate_url_invalid():
    """
    TC-3-03: Test URL validation with invalid URLs

    Expected:
    - Invalid URLs return False
    """
    assert RSSFetcher.validate_url('invalid-url') is False
    assert RSSFetcher.validate_url('ftp://example.com/feed/') is False
    assert RSSFetcher.validate_url('') is False
    assert RSSFetcher.validate_url('not a url at all') is False


# ========================================
# TC-3-04: Single RSS Feed Fetch (Success)
# ========================================

@patch('src.tools.fetcher.requests.get')
@patch('src.tools.fetcher.feedparser.parse')
def test_fetch_single_feed_success(mock_parse, mock_get, fetcher, mock_feed_response):
    """
    TC-3-04: Test fetching single RSS feed successfully

    Expected:
    - Returns success status
    - Articles list is populated
    - Feed title is extracted
    """
    # Mock HTTP response
    mock_response = Mock()
    mock_response.content = b'<rss>...</rss>'
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Mock feedparser
    mock_parse.return_value = mock_feed_response

    result = fetcher.fetch_single_feed('https://example.com/feed/')

    assert result['status'] == 'success'
    assert result['feed_title'] == 'Test Feed'
    assert len(result['articles']) == 2
    assert result['articles'][0]['title'] == 'Test Article 1'
    assert result['articles'][0]['url'] == 'https://example.com/article1'


# ========================================
# TC-3-05: Single RSS Feed Fetch (Invalid URL)
# ========================================

def test_fetch_single_feed_invalid_url(fetcher):
    """
    TC-3-05: Test fetching with invalid URL

    Expected:
    - Returns error status
    - Error message indicates invalid URL
    """
    result = fetcher.fetch_single_feed('invalid-url')

    assert result['status'] == 'error'
    assert 'Invalid URL format' in result['error_message']


# ========================================
# TC-3-06: Batch Fetch (All Success)
# ========================================

@patch('src.tools.fetcher.requests.get')
@patch('src.tools.fetcher.feedparser.parse')
def test_fetch_rss_feeds_all_success(mock_parse, mock_get, fetcher, mock_feed_response):
    """
    TC-3-06: Test batch fetching with all feeds successful

    Expected:
    - Returns success status
    - All articles collected
    - Summary shows all feeds successful
    """
    # Mock HTTP response
    mock_response = Mock()
    mock_response.content = b'<rss>...</rss>'
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Mock feedparser
    mock_parse.return_value = mock_feed_response

    feed_urls = [
        'https://example.com/feed1/',
        'https://example.com/feed2/',
        'https://example.com/feed3/'
    ]

    result = fetcher.fetch_rss_feeds(feed_urls)

    assert result['status'] == 'success'
    assert result['summary']['total_feeds'] == 3
    assert result['summary']['successful_feeds'] == 3
    assert result['summary']['failed_feeds'] == 0
    assert result['summary']['total_articles'] == 6  # 2 articles per feed * 3 feeds


# ========================================
# TC-3-07: Batch Fetch (Partial Failure)
# ========================================

@patch('src.tools.fetcher.requests.get')
@patch('src.tools.fetcher.feedparser.parse')
def test_fetch_rss_feeds_partial_failure(mock_parse, mock_get, fetcher, mock_feed_response):
    """
    TC-3-07: Test batch fetching with some feeds failing

    Expected:
    - Returns partial status
    - Successful feeds' articles collected
    - Errors recorded for failed feeds
    """
    def side_effect_get(url, *args, **kwargs):
        if 'fail' in url:
            raise requests.RequestException("Network error")
        mock_response = Mock()
        mock_response.content = b'<rss>...</rss>'
        mock_response.raise_for_status = Mock()
        return mock_response

    mock_get.side_effect = side_effect_get
    mock_parse.return_value = mock_feed_response

    feed_urls = [
        'https://example.com/feed1/',
        'https://example.com/fail-feed/',
        'https://example.com/feed2/'
    ]

    result = fetcher.fetch_rss_feeds(feed_urls)

    assert result['status'] == 'partial'
    assert result['summary']['total_feeds'] == 3
    assert result['summary']['successful_feeds'] == 2
    assert result['summary']['failed_feeds'] == 1
    assert len(result['errors']) == 1
    assert 'fail-feed' in result['errors'][0]['feed_url']


# ========================================
# TC-3-08: Article Limit Enforcement
# ========================================

@patch('src.tools.fetcher.requests.get')
@patch('src.tools.fetcher.feedparser.parse')
def test_fetch_with_max_articles(mock_parse, mock_get, fetcher):
    """
    TC-3-08: Test article count limit enforcement

    Expected:
    - Returns only max_articles number of articles
    - Even if feed has more entries
    """
    # Create mock feed with 10 articles
    mock_feed = {
        'feed': {'title': 'Test Feed'},
        'entries': [
            {
                'link': f'https://example.com/article{i}',
                'title': f'Article {i}',
                'summary': f'Summary {i}'
            }
            for i in range(10)
        ],
        'bozo': False
    }

    mock_response = Mock()
    mock_response.content = b'<rss>...</rss>'
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    mock_parse.return_value = mock_feed

    result = fetcher.fetch_single_feed('https://example.com/feed/', max_articles=5)

    assert result['status'] == 'success'
    assert len(result['articles']) == 5


# ========================================
# TC-3-09: Parse Feed Entry Metadata
# ========================================

def test_parse_feed_entry(fetcher):
    """
    TC-3-09: Test parsing feed entry to structured data

    Expected:
    - All metadata fields extracted correctly
    - Tags parsed from entry
    """
    # Use a dict with Mock-like behavior for tags
    class FakeTerm:
        def __init__(self, term):
            self.term = term

        def get(self, key, default=''):
            return getattr(self, key, default)

    mock_entry = {
        'link': 'https://example.com/article',
        'title': 'Test Article',
        'summary': 'Test summary',
        'description': 'Test description',
        'published': 'Wed, 20 Nov 2024 10:00:00 GMT'
    }

    # Create an object that supports both dict access and attribute access
    class Entry(dict):
        def __getattr__(self, name):
            return self.get(name)

    entry = Entry(mock_entry)
    entry.tags = [FakeTerm('AI'), FakeTerm('Tech')]

    article = fetcher.parse_feed_entry(entry, 'Test Feed', 'https://example.com/feed/')

    assert article['url'] == 'https://example.com/article'
    assert article['title'] == 'Test Article'
    assert article['summary'] == 'Test summary'
    assert article['source'] == 'rss'
    assert article['source_name'] == 'Test Feed'
    assert 'AI' in article['tags']
    assert 'Tech' in article['tags']


# ========================================
# TC-3-10: Parse Published Date (RFC 2822)
# ========================================

def test_parse_published_date_rfc2822():
    """
    TC-3-10: Test parsing RFC 2822 date format

    Expected:
    - Correctly parses date string
    - Returns datetime object
    """
    date_str = 'Wed, 20 Nov 2024 10:00:00 GMT'
    result = RSSFetcher.parse_published_date(date_str)

    assert result is not None
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 11
    assert result.day == 20


# ========================================
# TC-3-11: Parse Published Date (ISO 8601)
# ========================================

def test_parse_published_date_iso8601():
    """
    TC-3-11: Test parsing ISO 8601 date format

    Expected:
    - Correctly parses date string
    - Returns datetime object
    """
    date_str = '2024-11-20T10:00:00Z'
    result = RSSFetcher.parse_published_date(date_str)

    assert result is not None
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 11
    assert result.day == 20


# ========================================
# TC-3-12: Parse Published Date (Invalid Format)
# ========================================

def test_parse_published_date_invalid():
    """
    TC-3-12: Test parsing invalid date format

    Expected:
    - Returns None for invalid formats
    - Does not raise exception
    """
    assert RSSFetcher.parse_published_date('invalid-date') is None
    assert RSSFetcher.parse_published_date('') is None
    assert RSSFetcher.parse_published_date('not a date at all') is None


# ========================================
# Additional Edge Case Tests
# ========================================

def test_parse_entry_missing_link(fetcher):
    """Test parsing entry without link raises ValueError"""
    mock_entry = Mock()
    mock_entry.get = Mock(return_value='')

    with pytest.raises(ValueError, match="missing 'link' field"):
        fetcher.parse_feed_entry(mock_entry, 'Test Feed', 'https://example.com/feed/')


@patch('src.tools.fetcher.requests.get')
def test_fetch_timeout(mock_get, fetcher):
    """Test network timeout handling"""
    import requests
    mock_get.side_effect = requests.Timeout("Connection timeout")

    result = fetcher.fetch_single_feed('https://example.com/feed/')

    assert result['status'] == 'error'
    assert 'timeout' in result['error_message'].lower()


@patch('src.tools.fetcher.requests.get')
@patch('src.tools.fetcher.feedparser.parse')
def test_fetch_malformed_feed(mock_parse, mock_get, fetcher):
    """Test handling of malformed feed XML"""
    mock_response = Mock()
    mock_response.content = b'<rss>...</rss>'
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Mock feedparser to return error
    mock_parse.return_value = {
        'bozo': True,
        'bozo_exception': Exception("XML parsing error"),
        'entries': [],
        'feed': {}
    }

    result = fetcher.fetch_single_feed('https://example.com/feed/')

    assert result['status'] == 'error'
    assert 'parsing error' in result['error_message'].lower()
