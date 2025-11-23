"""
Unit tests for InsightCosmos Google Search Tool

Tests cover:
- GoogleSearchTool initialization
- API URL building
- Single search
- Batch search
- Result parsing
- Domain extraction
- Quota detection
- Error handling

Test Cases:
    TC-4-01: GoogleSearchTool initialization (with credentials)
    TC-4-02: GoogleSearchTool initialization (without credentials)
    TC-4-03: Build API URL
    TC-4-04: Single search (success)
    TC-4-05: Single search (API error - quota exceeded)
    TC-4-06: Single search (network error - timeout)
    TC-4-07: Batch search (all success)
    TC-4-08: Batch search (partial failure)
    TC-4-09: Parse search result
    TC-4-10: Extract domain from URL
    TC-4-11: Detect quota exceeded (True - 403)
    TC-4-12: Detect quota exceeded (True - 429)
    TC-4-13: Detect quota exceeded (False - other error)
    TC-4-14: Validate API credentials (success)
    TC-4-15: Validate API credentials (failure)
    TC-4-16: max_results range enforcement

Run with: pytest tests/unit/test_google_search.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.tools.google_search import GoogleSearchTool


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def search_tool():
    """Create GoogleSearchTool instance with mock credentials"""
    with patch('src.tools.google_search.Config') as MockConfig:
        mock_config = Mock()
        mock_config.google_search_api_key = "test_api_key"
        mock_config.google_search_engine_id = "test_engine_id"
        MockConfig.return_value = mock_config

        return GoogleSearchTool(
            api_key="test_api_key",
            engine_id="test_engine_id"
        )


@pytest.fixture
def mock_search_response():
    """Mock Google Search API response"""
    return {
        'items': [
            {
                'title': 'Test Article 1',
                'link': 'https://example.com/article1',
                'snippet': 'This is a test snippet about AI...',
                'pagemap': {
                    'metatags': [
                        {
                            'og:description': 'Full description about AI research'
                        }
                    ]
                }
            },
            {
                'title': 'Test Article 2',
                'link': 'https://www.techcrunch.com/article2',
                'snippet': 'Another test snippet about robotics...',
                'pagemap': {}
            }
        ],
        'searchInformation': {
            'totalResults': '1000'
        }
    }


# ========================================
# TC-4-01: GoogleSearchTool Initialization (with credentials)
# ========================================

def test_search_tool_initialization_with_credentials():
    """
    TC-4-01: Test GoogleSearchTool initialization with credentials

    Given: Valid API key and Engine ID
    When: Creating GoogleSearchTool instance
    Then: Instance is created successfully with correct attributes
    """
    search_tool = GoogleSearchTool(
        api_key="test_key",
        engine_id="test_engine"
    )

    assert search_tool.api_key == "test_key"
    assert search_tool.engine_id == "test_engine"
    assert search_tool.timeout == 30  # default
    assert search_tool.API_ENDPOINT == "https://www.googleapis.com/customsearch/v1"


# ========================================
# TC-4-02: GoogleSearchTool Initialization (without credentials)
# ========================================

def test_search_tool_initialization_without_credentials():
    """
    TC-4-02: Test GoogleSearchTool initialization without credentials

    Given: No API key or Engine ID provided
    When: Creating GoogleSearchTool instance without credentials in Config
    Then: ValueError is raised
    """
    with patch('src.tools.google_search.Config') as MockConfig:
        MockConfig.side_effect = AttributeError("Config not found")

        with pytest.raises(ValueError) as exc_info:
            GoogleSearchTool()

        assert "API credentials not found" in str(exc_info.value)


# ========================================
# TC-4-03: Build API URL
# ========================================

def test_build_api_url(search_tool):
    """
    TC-4-03: Test building Google Search API URL

    Given: Search query and parameters
    When: Building API URL
    Then: URL contains correct parameters
    """
    url = search_tool.build_api_url(
        query="AI robotics",
        max_results=10,
        date_restrict='d7',
        language='lang_en'
    )

    assert "https://www.googleapis.com/customsearch/v1" in url
    assert "key=test_api_key" in url
    assert "cx=test_engine_id" in url
    assert "q=AI+robotics" in url or "q=AI%20robotics" in url
    assert "num=10" in url
    assert "dateRestrict=d7" in url
    assert "lr=lang_en" in url


# ========================================
# TC-4-04: Single Search (Success)
# ========================================

@patch('src.tools.google_search.requests.get')
def test_single_search_success(mock_get, search_tool, mock_search_response):
    """
    TC-4-04: Test single search (success)

    Given: Valid search query
    When: Calling search_articles
    Then: Returns success status with articles
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_search_response
    mock_get.return_value = mock_response

    result = search_tool.search_articles("AI robotics", max_results=5)

    assert result['status'] == 'success'
    assert result['query'] == 'AI robotics'
    assert len(result['articles']) == 2
    assert result['total_results'] == 1000
    assert result['quota_exceeded'] is False
    assert result['error_message'] is None

    # Check first article structure
    article = result['articles'][0]
    assert article['url'] == 'https://example.com/article1'
    assert article['title'] == 'Test Article 1'
    assert article['source'] == 'google_search'
    assert article['search_query'] == 'AI robotics'


# ========================================
# TC-4-05: Single Search (API Error - Quota Exceeded)
# ========================================

@patch('src.tools.google_search.requests.get')
def test_single_search_quota_exceeded(mock_get, search_tool):
    """
    TC-4-05: Test single search (quota exceeded)

    Given: API quota is exceeded
    When: Calling search_articles
    Then: Returns error status with quota_exceeded=True
    """
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = 'quotaExceeded'
    mock_get.return_value = mock_response

    result = search_tool.search_articles("AI robotics")

    assert result['status'] == 'error'
    assert result['quota_exceeded'] is True
    assert 'quota exceeded' in result['error_message'].lower()
    assert len(result['articles']) == 0


# ========================================
# TC-4-06: Single Search (Network Error - Timeout)
# ========================================

@patch('src.tools.google_search.requests.get')
def test_single_search_timeout(mock_get, search_tool):
    """
    TC-4-06: Test single search (network timeout)

    Given: Network request times out
    When: Calling search_articles
    Then: Returns error status with timeout message
    """
    import requests
    mock_get.side_effect = requests.Timeout("Connection timed out")

    result = search_tool.search_articles("AI robotics")

    assert result['status'] == 'error'
    assert 'timed out' in result['error_message'].lower()
    assert result['quota_exceeded'] is False
    assert len(result['articles']) == 0


# ========================================
# TC-4-07: Batch Search (All Success)
# ========================================

@patch('src.tools.google_search.requests.get')
def test_batch_search_all_success(mock_get, search_tool, mock_search_response):
    """
    TC-4-07: Test batch search (all success)

    Given: Multiple search queries
    When: Calling batch_search
    Then: Returns success status with all articles
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_search_response
    mock_get.return_value = mock_response

    result = search_tool.batch_search(
        queries=["AI agents", "robotics news"],
        max_results_per_query=5
    )

    assert result['status'] == 'success'
    assert result['summary']['total_queries'] == 2
    assert result['summary']['successful_queries'] == 2
    assert result['summary']['failed_queries'] == 0
    assert result['summary']['total_articles'] == 4  # 2 queries * 2 articles each
    assert result['summary']['quota_exceeded'] is False


# ========================================
# TC-4-08: Batch Search (Partial Failure)
# ========================================

@patch('src.tools.google_search.requests.get')
def test_batch_search_partial_failure(mock_get, search_tool, mock_search_response):
    """
    TC-4-08: Test batch search (partial failure)

    Given: Multiple queries, one fails
    When: Calling batch_search
    Then: Returns partial status with some articles and errors
    """
    # First call succeeds, second fails
    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = mock_search_response

    error_response = Mock()
    error_response.status_code = 403
    error_response.text = 'quotaExceeded'

    mock_get.side_effect = [success_response, error_response]

    result = search_tool.batch_search(
        queries=["AI agents", "robotics news"],
        max_results_per_query=5
    )

    assert result['status'] == 'partial'
    assert result['summary']['successful_queries'] == 1
    assert result['summary']['failed_queries'] == 1
    assert result['summary']['quota_exceeded'] is True
    assert len(result['errors']) == 1
    assert result['errors'][0]['query'] == 'robotics news'


# ========================================
# TC-4-09: Parse Search Result
# ========================================

def test_parse_search_result(search_tool):
    """
    TC-4-09: Test parsing search result item

    Given: Search result item from API
    When: Calling parse_search_result
    Then: Returns structured article data
    """
    item = {
        'title': 'AI Research Paper',
        'link': 'https://www.example.com/research',
        'snippet': 'Brief description of AI research',
        'pagemap': {
            'metatags': [
                {
                    'og:description': 'Full description of the research'
                }
            ]
        }
    }

    article = search_tool.parse_search_result(item, "AI research")

    assert article['url'] == 'https://www.example.com/research'
    assert article['title'] == 'AI Research Paper'
    assert article['summary'] == 'Brief description of AI research'
    assert article['content'] == 'Full description of the research'
    assert article['source'] == 'google_search'
    assert article['source_name'] == 'example.com'
    assert article['search_query'] == 'AI research'
    assert 'AI' in article['tags'] or 'research' in article['tags']
    assert isinstance(article['published_at'], datetime)


# ========================================
# TC-4-10: Extract Domain from URL
# ========================================

def test_extract_domain():
    """
    TC-4-10: Test extracting domain from URL

    Given: Various URL formats
    When: Calling extract_domain
    Then: Returns correct domain name
    """
    assert GoogleSearchTool.extract_domain("https://www.example.com/article") == "example.com"
    assert GoogleSearchTool.extract_domain("https://blog.openai.com/post") == "blog.openai.com"
    assert GoogleSearchTool.extract_domain("http://techcrunch.com") == "techcrunch.com"
    assert GoogleSearchTool.extract_domain("https://www.news.bbc.co.uk/tech") == "news.bbc.co.uk"
    assert GoogleSearchTool.extract_domain("invalid-url") == "unknown"


# ========================================
# TC-4-11: Detect Quota Exceeded (True - 403)
# ========================================

def test_is_quota_exceeded_403():
    """
    TC-4-11: Test quota detection (403 error)

    Given: 403 error response
    When: Calling is_quota_exceeded
    Then: Returns True
    """
    error_response = {
        'error': {
            'code': 403,
            'message': 'Quota exceeded'
        }
    }

    assert GoogleSearchTool.is_quota_exceeded(error_response) is True


# ========================================
# TC-4-12: Detect Quota Exceeded (True - 429)
# ========================================

def test_is_quota_exceeded_429():
    """
    TC-4-12: Test quota detection (429 error)

    Given: 429 rate limit error
    When: Calling is_quota_exceeded
    Then: Returns True
    """
    error_response = {
        'error': {
            'code': 429,
            'message': 'Rate limit exceeded'
        }
    }

    assert GoogleSearchTool.is_quota_exceeded(error_response) is True


# ========================================
# TC-4-13: Detect Quota Exceeded (False - Other Error)
# ========================================

def test_is_quota_exceeded_other_error():
    """
    TC-4-13: Test quota detection (other error)

    Given: Non-quota error (e.g., 500)
    When: Calling is_quota_exceeded
    Then: Returns False
    """
    error_response = {
        'error': {
            'code': 500,
            'message': 'Internal server error'
        }
    }

    assert GoogleSearchTool.is_quota_exceeded(error_response) is False


# ========================================
# TC-4-14: Validate API Credentials (Success)
# ========================================

@patch('src.tools.google_search.requests.get')
def test_validate_credentials_success(mock_get, search_tool):
    """
    TC-4-14: Test API credentials validation (success)

    Given: Valid API credentials
    When: Calling validate_api_credentials
    Then: Returns True
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = search_tool.validate_api_credentials()

    assert result is True


# ========================================
# TC-4-15: Validate API Credentials (Failure)
# ========================================

@patch('src.tools.google_search.requests.get')
def test_validate_credentials_failure(mock_get, search_tool):
    """
    TC-4-15: Test API credentials validation (failure)

    Given: Invalid API credentials
    When: Calling validate_api_credentials
    Then: Returns False
    """
    mock_response = Mock()
    mock_response.status_code = 403
    mock_get.return_value = mock_response

    result = search_tool.validate_api_credentials()

    assert result is False


# ========================================
# TC-4-16: max_results Range Enforcement
# ========================================

@patch('src.tools.google_search.requests.get')
def test_max_results_range_enforcement(mock_get, search_tool, mock_search_response):
    """
    TC-4-16: Test max_results range enforcement (1-10)

    Given: max_results outside valid range
    When: Calling search_articles
    Then: max_results is adjusted to valid range
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_search_response
    mock_get.return_value = mock_response

    # Test max_results > 10 (should be clamped to 10)
    result = search_tool.search_articles("AI", max_results=15)

    # Check the actual API call
    call_args = mock_get.call_args
    assert 'num=10' in call_args[0][0]  # URL should have num=10

    # Test max_results < 1 (should be clamped to 1)
    result = search_tool.search_articles("AI", max_results=0)

    call_args = mock_get.call_args
    assert 'num=1' in call_args[0][0]  # URL should have num=1


# ========================================
# Summary Statistics
# ========================================

def test_summary():
    """
    Test Summary for Stage 4: Google Search Tool

    Total Tests: 16
    Coverage:
    - Initialization: 2 tests
    - URL Building: 1 test
    - Single Search: 3 tests
    - Batch Search: 2 tests
    - Result Parsing: 1 test
    - Domain Extraction: 1 test
    - Quota Detection: 3 tests
    - Credential Validation: 2 tests
    - Range Enforcement: 1 test
    """
    pass
