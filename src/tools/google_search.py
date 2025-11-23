"""
InsightCosmos Google Search Tool

Provides Google Custom Search API integration for article discovery.

Classes:
    GoogleSearchTool: Google Custom Search API client

Usage:
    from src.tools.google_search import GoogleSearchTool

    search_tool = GoogleSearchTool(
        api_key="YOUR_API_KEY",
        engine_id="YOUR_ENGINE_ID"
    )
    result = search_tool.search_articles(
        query="AI multi-agent systems",
        max_results=10
    )

    print(f"Total articles: {len(result['articles'])}")
    for article in result['articles']:
        print(f"- {article['title']}")
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse, quote_plus
import logging

import requests

from src.utils.logger import Logger
from src.utils.config import Config


class GoogleSearchTool:
    """
    Google Custom Search API client

    Provides functionality for:
    - Searching articles via Google Custom Search API
    - Parsing search results
    - Batch searching multiple queries
    - Quota management and error handling

    Attributes:
        api_key (str): Google Search API key
        engine_id (str): Custom Search Engine ID
        timeout (int): HTTP request timeout in seconds
        logger (Logger): Logger instance

    Example:
        >>> search_tool = GoogleSearchTool()
        >>> result = search_tool.search_articles("AI robotics", max_results=5)
        >>> print(f"Found {len(result['articles'])} articles")
    """

    API_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        engine_id: Optional[str] = None,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Google Search Tool

        Args:
            api_key: Google Search API key (None to read from Config)
            engine_id: Custom Search Engine ID (None to read from Config)
            timeout: HTTP request timeout in seconds (default: 30)
            logger: Logger instance (optional)

        Raises:
            ValueError: If API key or Engine ID is missing

        Example:
            >>> search_tool = GoogleSearchTool()  # Read from config
            >>> search_tool = GoogleSearchTool(api_key="...", engine_id="...")
        """
        self.logger = logger or Logger.get_logger("GoogleSearchTool")

        # Get credentials from Config if not provided
        if api_key is None or engine_id is None:
            try:
                config = Config.load()
                self.api_key = api_key or config.google_search_api_key
                self.engine_id = engine_id or config.google_search_engine_id
            except (AttributeError, FileNotFoundError, ValueError) as e:
                self.logger.error(f"Failed to get API credentials from Config: {e}")
                raise ValueError(
                    "Google Search API credentials not found. "
                    "Please set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in .env"
                ) from e
        else:
            self.api_key = api_key
            self.engine_id = engine_id

        # Validate credentials
        if not self.api_key or not self.engine_id:
            raise ValueError(
                "Google Search API credentials are required. "
                "Please provide api_key and engine_id or set them in .env"
            )

        self.timeout = timeout

        self.logger.info(
            f"GoogleSearchTool initialized (timeout={timeout}s, "
            f"engine_id={self.engine_id[:8]}...)"
        )

    def search_articles(
        self,
        query: str,
        max_results: int = 10,
        date_restrict: str = 'd7',
        language: str = 'lang_en'
    ) -> Dict[str, Any]:
        """
        Search articles and return structured results

        Args:
            query: Search query string
            max_results: Maximum number of results (1-10, default: 10)
            date_restrict: Date restriction (d7=7days, w1=1week, m1=1month)
            language: Language restriction (lang_en, lang_zh-TW)

        Returns:
            dict: {
                "status": "success" | "error",
                "query": str,
                "articles": List[Dict],
                "total_results": int,
                "error_message": str (if error),
                "quota_exceeded": bool,
                "searched_at": datetime
            }

        Example:
            >>> result = search_tool.search_articles("AI agents", max_results=5)
            >>> print(result['total_results'])
        """
        self.logger.info(f"Searching articles: query='{query}', max_results={max_results}")

        # Validate and adjust max_results
        max_results = max(1, min(max_results, 10))

        # Build API URL
        url = self.build_api_url(query, max_results, date_restrict, language)

        try:
            # Make API request
            response = requests.get(url, timeout=self.timeout)
            searched_at = datetime.now(timezone.utc)

            # Check for quota exceeded (403 error)
            if response.status_code == 429 or (
                response.status_code == 403 and
                'quotaExceeded' in response.text
            ):
                self.logger.warning(f"Google Search API quota exceeded for query: {query}")
                return {
                    "status": "error",
                    "query": query,
                    "articles": [],
                    "total_results": 0,
                    "error_message": "Google Search API quota exceeded. Please try again later.",
                    "quota_exceeded": True,
                    "searched_at": searched_at
                }

            # Check for other HTTP errors
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                self.logger.error(f"API request failed: {error_msg}")
                return {
                    "status": "error",
                    "query": query,
                    "articles": [],
                    "total_results": 0,
                    "error_message": error_msg,
                    "quota_exceeded": False,
                    "searched_at": searched_at
                }

            # Parse response
            data = response.json()

            # Extract articles
            items = data.get('items', [])
            articles = [
                self.parse_search_result(item, query)
                for item in items
            ]

            total_results = int(data.get('searchInformation', {}).get('totalResults', 0))

            self.logger.info(
                f"Search completed: {len(articles)} articles returned "
                f"(total: {total_results})"
            )

            return {
                "status": "success",
                "query": query,
                "articles": articles,
                "total_results": total_results,
                "error_message": None,
                "quota_exceeded": False,
                "searched_at": searched_at
            }

        except requests.Timeout:
            self.logger.error(f"Search request timed out for query: {query}")
            return {
                "status": "error",
                "query": query,
                "articles": [],
                "total_results": 0,
                "error_message": f"Request timed out after {self.timeout} seconds",
                "quota_exceeded": False,
                "searched_at": datetime.now(timezone.utc)
            }

        except requests.RequestException as e:
            self.logger.error(f"Search request failed: {e}")
            return {
                "status": "error",
                "query": query,
                "articles": [],
                "total_results": 0,
                "error_message": f"Network error: {str(e)}",
                "quota_exceeded": False,
                "searched_at": datetime.now(timezone.utc)
            }

        except Exception as e:
            self.logger.error(f"Unexpected error during search: {e}")
            return {
                "status": "error",
                "query": query,
                "articles": [],
                "total_results": 0,
                "error_message": f"Unexpected error: {str(e)}",
                "quota_exceeded": False,
                "searched_at": datetime.now(timezone.utc)
            }

    def batch_search(
        self,
        queries: List[str],
        max_results_per_query: int = 10
    ) -> Dict[str, Any]:
        """
        Batch search multiple queries

        Args:
            queries: List of search query strings
            max_results_per_query: Maximum results per query (default: 10)

        Returns:
            dict: {
                "status": "success" | "partial" | "error",
                "articles": List[Dict],  # All articles merged
                "errors": List[Dict],
                "summary": {
                    "total_queries": int,
                    "successful_queries": int,
                    "failed_queries": int,
                    "total_articles": int,
                    "quota_exceeded": bool
                }
            }

        Example:
            >>> result = search_tool.batch_search(
            ...     ["AI agents", "robotics news"],
            ...     max_results_per_query=5
            ... )
            >>> print(result['summary'])
        """
        self.logger.info(f"Batch search started: {len(queries)} queries")

        all_articles = []
        errors = []
        successful_queries = 0
        quota_exceeded = False

        for query in queries:
            result = self.search_articles(query, max_results=max_results_per_query)

            if result['status'] == 'success':
                all_articles.extend(result['articles'])
                successful_queries += 1
            else:
                errors.append({
                    "query": query,
                    "error_type": "QuotaExceeded" if result['quota_exceeded'] else "SearchError",
                    "error_message": result['error_message']
                })
                if result['quota_exceeded']:
                    quota_exceeded = True
                    self.logger.warning("Quota exceeded - stopping batch search")
                    break  # Stop on quota exceeded

        failed_queries = len(queries) - successful_queries

        # Determine overall status
        if successful_queries == 0:
            status = "error"
        elif successful_queries < len(queries):
            status = "partial"
        else:
            status = "success"

        summary = {
            "total_queries": len(queries),
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "total_articles": len(all_articles),
            "quota_exceeded": quota_exceeded
        }

        self.logger.info(
            f"Batch search completed: {successful_queries}/{len(queries)} successful, "
            f"{len(all_articles)} articles total"
        )

        return {
            "status": status,
            "articles": all_articles,
            "errors": errors,
            "summary": summary
        }

    def parse_search_result(
        self,
        item: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Parse single search result into structured article data

        Args:
            item: Google Search API result item
            query: Original search query

        Returns:
            dict: {
                "url": str,
                "title": str,
                "summary": str,
                "content": str,
                "published_at": datetime,
                "source": "google_search",
                "source_name": str,
                "tags": List[str],
                "search_query": str
            }

        Example:
            >>> item = {"title": "...", "link": "...", "snippet": "..."}
            >>> article = search_tool.parse_search_result(item, "AI news")
            >>> print(article['source'])
            'google_search'
        """
        url = item.get('link', '')
        title = item.get('title', '')
        snippet = item.get('snippet', '')

        # Try to get fuller description from pagemap
        pagemap = item.get('pagemap', {})
        metatags = pagemap.get('metatags', [{}])[0]
        description = metatags.get('og:description', snippet)

        # Extract domain as source_name
        source_name = self.extract_domain(url)

        # Extract tags from query
        tags = [tag.strip() for tag in query.split() if len(tag.strip()) > 2]

        # Use current time as published_at (search results don't have publish date)
        published_at = datetime.now(timezone.utc)

        return {
            "url": url,
            "title": title,
            "summary": snippet,
            "content": description,
            "published_at": published_at,
            "source": "google_search",
            "source_name": source_name,
            "tags": tags,
            "search_query": query
        }

    def build_api_url(
        self,
        query: str,
        max_results: int,
        date_restrict: str,
        language: str
    ) -> str:
        """
        Build Google Search API request URL

        Args:
            query: Search query
            max_results: Number of results (1-10)
            date_restrict: Date restriction
            language: Language restriction

        Returns:
            str: Complete API request URL

        Example:
            >>> url = search_tool.build_api_url("AI", 10, "d7", "lang_en")
            >>> 'q=AI' in url
            True
        """
        # URL-encode query
        encoded_query = quote_plus(query)

        # Build URL with parameters
        url = (
            f"{self.API_ENDPOINT}?"
            f"key={self.api_key}&"
            f"cx={self.engine_id}&"
            f"q={encoded_query}&"
            f"num={max_results}&"
            f"dateRestrict={date_restrict}&"
            f"lr={language}"
        )

        return url

    @staticmethod
    def extract_domain(url: str) -> str:
        """
        Extract domain name from URL as source name

        Args:
            url: Article URL

        Returns:
            str: Domain name (without www.)

        Example:
            >>> GoogleSearchTool.extract_domain("https://www.example.com/article")
            'example.com'
            >>> GoogleSearchTool.extract_domain("https://blog.openai.com/post")
            'blog.openai.com'
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain if domain else 'unknown'

        except Exception:
            return 'unknown'

    @staticmethod
    def is_quota_exceeded(error_response: Dict[str, Any]) -> bool:
        """
        Check if error is quota exceeded

        Args:
            error_response: API error response

        Returns:
            bool: True if quota exceeded

        Example:
            >>> error = {"error": {"code": 429}}
            >>> GoogleSearchTool.is_quota_exceeded(error)
            True
        """
        if not isinstance(error_response, dict):
            return False

        error = error_response.get('error', {})

        # Check error code
        error_code = error.get('code', 0)
        if error_code in [403, 429]:
            return True

        # Check error message
        error_message = error.get('message', '').lower()
        if 'quota' in error_message or 'rate limit' in error_message:
            return True

        return False

    def validate_api_credentials(self) -> bool:
        """
        Validate API credentials by making a test request

        Returns:
            bool: True if credentials are valid

        Example:
            >>> if search_tool.validate_api_credentials():
            ...     print("Credentials are valid")
        """
        try:
            self.logger.info("Validating API credentials...")

            # Make a minimal test request
            test_url = (
                f"{self.API_ENDPOINT}?"
                f"key={self.api_key}&"
                f"cx={self.engine_id}&"
                f"q=test&"
                f"num=1"
            )

            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                self.logger.info("API credentials validated successfully")
                return True
            else:
                self.logger.warning(
                    f"API credentials validation failed: HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            self.logger.error(f"API credentials validation error: {e}")
            return False
