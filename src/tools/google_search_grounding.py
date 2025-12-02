"""
InsightCosmos Google Search Tool (Gemini Grounding)

Provides Google Search integration via Gemini's built-in Grounding feature.
This approach eliminates the need for Custom Search Engine ID.

Classes:
    GoogleSearchGroundingTool: Gemini-based search client

Usage:
    from src.tools.google_search_grounding import GoogleSearchGroundingTool

    search_tool = GoogleSearchGroundingTool()
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
import logging
import re

import google.generativeai as genai

from src.utils.logger import Logger
from src.utils.config import Config


class GoogleSearchGroundingTool:
    """
    Google Search client using Gemini Grounding

    Provides functionality for:
    - Searching articles via Gemini's built-in Google Search
    - Extracting grounding metadata (source URLs and snippets)
    - Batch searching multiple queries
    - Automatic result parsing and structuring

    Attributes:
        api_key (str): Google Gemini API key
        model_name (str): Gemini model to use
        timeout (int): Request timeout in seconds
        logger (Logger): Logger instance

    Example:
        >>> search_tool = GoogleSearchGroundingTool()
        >>> result = search_tool.search_articles("AI robotics", max_results=5)
        >>> print(f"Found {len(result['articles'])} articles")
    """

    DEFAULT_MODEL = "gemini-2.5-flash"  # 使用穩定版本

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Google Search Grounding Tool

        Args:
            api_key: Google Gemini API key (None to read from Config)
            model_name: Gemini model name (default: gemini-2.0-flash-exp)
            timeout: Request timeout in seconds (default: 30)
            logger: Logger instance (optional)

        Raises:
            ValueError: If API key is missing

        Example:
            >>> search_tool = GoogleSearchGroundingTool()  # Read from config
            >>> search_tool = GoogleSearchGroundingTool(api_key="...")
        """
        self.logger = logger or Logger.get_logger("GoogleSearchGroundingTool")

        # Get API key from Config if not provided
        if api_key is None:
            try:
                config = Config.load()
                self.api_key = config.google_api_key
            except (AttributeError, FileNotFoundError, ValueError) as e:
                self.logger.error(f"Failed to get API key from Config: {e}")
                raise ValueError(
                    "Google API key not found. "
                    "Please set GOOGLE_API_KEY in .env"
                ) from e
        else:
            self.api_key = api_key

        # Validate API key
        if not self.api_key:
            raise ValueError(
                "Google API key is required. "
                "Please provide api_key or set GOOGLE_API_KEY in .env"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        self.model_name = model_name
        self.timeout = timeout

        # Initialize model with Google Search tool
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=[{"google_search": {}}]
        )

        # 設定 request timeout（避免 API 呼叫無限等待）
        self.request_options = {"timeout": self.timeout}

        self.logger.info(
            f"GoogleSearchGroundingTool initialized "
            f"(model={model_name}, timeout={timeout}s)"
        )

    def search_articles(
        self,
        query: str,
        max_results: int = 10,
        date_restrict: Optional[str] = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Search articles using Gemini Grounding and return structured results

        Args:
            query: Search query string
            max_results: Maximum number of results (default: 10)
            date_restrict: Date restriction hint (e.g., "past week", "past month")
            language: Language preference (default: "en")

        Returns:
            dict: {
                "status": "success" | "error",
                "query": str,
                "articles": List[Dict],
                "total_results": int,
                "error_message": str (if error),
                "searched_at": datetime
            }

        Example:
            >>> result = search_tool.search_articles("AI agents", max_results=5)
            >>> print(result['total_results'])
        """
        self.logger.info(f"Searching articles: query='{query}', max_results={max_results}")

        try:
            # Build search prompt
            prompt = self.build_search_prompt(query, max_results, date_restrict, language)

            # Start chat and send search request (with timeout)
            chat = self.model.start_chat()
            response = chat.send_message(
                prompt,
                request_options=self.request_options
            )
            searched_at = datetime.now(timezone.utc)

            # Extract articles from grounding metadata
            articles = self.extract_articles_from_response(response, query)

            # Limit to max_results
            articles = articles[:max_results]

            self.logger.info(
                f"Search completed: {len(articles)} articles returned"
            )

            return {
                "status": "success",
                "query": query,
                "articles": articles,
                "total_results": len(articles),
                "error_message": None,
                "searched_at": searched_at
            }

        except Exception as e:
            self.logger.error(f"Search request failed: {e}")
            return {
                "status": "error",
                "query": query,
                "articles": [],
                "total_results": 0,
                "error_message": f"Search error: {str(e)}",
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
                    "total_articles": int
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

        for query in queries:
            result = self.search_articles(query, max_results=max_results_per_query)

            if result['status'] == 'success':
                all_articles.extend(result['articles'])
                successful_queries += 1
            else:
                errors.append({
                    "query": query,
                    "error_type": "SearchError",
                    "error_message": result['error_message']
                })

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
            "total_articles": len(all_articles)
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

    def build_search_prompt(
        self,
        query: str,
        max_results: int,
        date_restrict: Optional[str],
        language: str
    ) -> str:
        """
        Build search prompt for Gemini

        Args:
            query: Search query
            max_results: Number of results
            date_restrict: Date restriction hint
            language: Language preference

        Returns:
            str: Formatted search prompt

        Example:
            >>> prompt = search_tool.build_search_prompt("AI", 10, "past week", "en")
            >>> "search for" in prompt.lower()
            True
        """
        prompt_parts = [
            f"Search for recent articles about: {query}",
        ]

        if date_restrict:
            prompt_parts.append(f"Focus on articles from the {date_restrict}.")

        if language != 'en':
            prompt_parts.append(f"Prefer {language} language sources.")

        prompt_parts.append(
            f"Return up to {max_results} relevant articles with their URLs, titles, and brief summaries."
        )

        return " ".join(prompt_parts)

    def extract_articles_from_response(
        self,
        response,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Extract article data from Gemini response with grounding metadata

        Args:
            response: Gemini API response object
            query: Original search query

        Returns:
            List[Dict]: List of article dictionaries

        Example:
            >>> articles = search_tool.extract_articles_from_response(response, "AI")
            >>> len(articles) > 0
            True
        """
        articles = []

        try:
            # Check if grounding metadata exists
            candidate = response.candidates[0]

            if not hasattr(candidate, 'grounding_metadata'):
                self.logger.warning("No grounding metadata found in response")
                return articles

            grounding_metadata = candidate.grounding_metadata

            # Extract search entry point (contains search results)
            if hasattr(grounding_metadata, 'grounding_chunks'):
                for chunk in grounding_metadata.grounding_chunks:
                    if hasattr(chunk, 'web'):
                        web_chunk = chunk.web
                        article = self.parse_grounding_chunk(web_chunk, query)
                        if article:
                            articles.append(article)

            # Also parse from search_entry_point if available
            if hasattr(grounding_metadata, 'search_entry_point'):
                search_results = self.parse_search_entry_point(
                    grounding_metadata.search_entry_point,
                    query
                )
                articles.extend(search_results)

            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)

            self.logger.info(f"Extracted {len(unique_articles)} unique articles from response")
            return unique_articles

        except Exception as e:
            self.logger.error(f"Failed to extract articles from response: {e}")
            return []

    def parse_grounding_chunk(
        self,
        web_chunk,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a single grounding chunk into article data

        Args:
            web_chunk: Gemini web grounding chunk
            query: Original search query

        Returns:
            dict: Article data or None if parsing fails
        """
        try:
            url = web_chunk.uri if hasattr(web_chunk, 'uri') else ''
            title = web_chunk.title if hasattr(web_chunk, 'title') else ''

            if not url:
                return None

            # Extract domain as source_name
            source_name = self.extract_domain(url)

            # Extract tags from query
            tags = [tag.strip() for tag in query.split() if len(tag.strip()) > 2]

            return {
                "url": url,
                "title": title,
                "summary": title,  # Use title as summary if no snippet available
                "content": "",
                "published_at": datetime.now(timezone.utc),
                "source": "google_search_grounding",
                "source_name": source_name,
                "tags": tags,
                "search_query": query
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse grounding chunk: {e}")
            return None

    def parse_search_entry_point(
        self,
        search_entry_point,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Parse search entry point for additional article data

        Args:
            search_entry_point: Gemini search entry point metadata
            query: Original search query

        Returns:
            List[Dict]: List of article dictionaries
        """
        articles = []

        try:
            # The rendered_content contains formatted search results
            if hasattr(search_entry_point, 'rendered_content'):
                content = search_entry_point.rendered_content

                # Extract URLs from content using regex
                url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                urls = re.findall(url_pattern, content)

                for url in urls:
                    # Skip Google search result URLs
                    if 'google.com/search' in url:
                        continue

                    source_name = self.extract_domain(url)
                    tags = [tag.strip() for tag in query.split() if len(tag.strip()) > 2]

                    articles.append({
                        "url": url,
                        "title": source_name,  # Use domain as title
                        "summary": "",
                        "content": "",
                        "published_at": datetime.now(timezone.utc),
                        "source": "google_search_grounding",
                        "source_name": source_name,
                        "tags": tags,
                        "search_query": query
                    })

        except Exception as e:
            self.logger.warning(f"Failed to parse search entry point: {e}")

        return articles

    @staticmethod
    def extract_domain(url: str) -> str:
        """
        Extract domain name from URL as source name

        Args:
            url: Article URL

        Returns:
            str: Domain name (without www.)

        Example:
            >>> GoogleSearchGroundingTool.extract_domain("https://www.example.com/article")
            'example.com'
            >>> GoogleSearchGroundingTool.extract_domain("https://blog.openai.com/post")
            'blog.openai.com'
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain if domain else 'unknown'

        except Exception:
            return 'unknown'

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

            # Make a minimal test search
            result = self.search_articles("test", max_results=1)

            if result['status'] == 'success':
                self.logger.info("API credentials validated successfully")
                return True
            else:
                self.logger.warning(
                    f"API credentials validation failed: {result['error_message']}"
                )
                return False

        except Exception as e:
            self.logger.error(f"API credentials validation error: {e}")
            return False
