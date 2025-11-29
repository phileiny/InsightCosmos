# -*- coding: utf-8 -*-
"""
InsightCosmos Google Search Tool (Gemini Grounding - Official SDK)

Uses the new unified Google Gen AI SDK (google-genai) for Google Search Grounding.
Based on official documentation from googleapis/python-genai v1.33.0

Classes:
    GoogleSearchGroundingTool: Gemini-based search client using official SDK

Usage:
    from src.tools.google_search_grounding_v2 import GoogleSearchGroundingTool

    search_tool = GoogleSearchGroundingTool()
    result = search_tool.search_articles(
        query="AI multi-agent systems",
        max_results=10
    )

References:
    - Official SDK: https://github.com/googleapis/python-genai
    - Context7 Documentation: /googleapis/python-genai v1.33.0
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from google import genai
from google.genai import types

from src.utils.logger import Logger
from src.utils.config import Config


class GoogleSearchGroundingTool:
    """
    Google Search client using Gemini Grounding (Official SDK)

    Uses the new unified Google Gen AI SDK for search grounding.
    This implementation follows the official documentation from googleapis/python-genai.

    Attributes:
        api_key (str): Google Gemini API key
        model_name (str): Gemini model to use
        client (genai.Client): Gen AI client instance
        logger (Logger): Logger instance

    Example:
        >>> search_tool = GoogleSearchGroundingTool()
        >>> result = search_tool.search_articles("AI robotics", max_results=5)
        >>> print(f"Found {len(result['articles'])} articles")
    """

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Google Search Grounding Tool

        Args:
            api_key: Google Gemini API key (None to read from Config)
            model_name: Gemini model name (default: gemini-2.5-flash)
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

        self.model_name = model_name

        # Initialize client using official SDK
        self.client = genai.Client(api_key=self.api_key)

        self.logger.info(
            f"GoogleSearchGroundingTool initialized (model={model_name})"
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

            # Perform search using official SDK
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(google_search=types.GoogleSearch())
                    ]
                )
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

        Based on official SDK documentation:
        - grounding_metadata.web_search_queries: Search queries used
        - grounding_metadata.grounding_chunks: Search result chunks with URLs

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
            # Check if response has candidates
            if not response.candidates or len(response.candidates) == 0:
                self.logger.warning("No candidates found in response")
                return articles

            candidate = response.candidates[0]

            # Check if grounding metadata exists
            if not hasattr(candidate, 'grounding_metadata'):
                self.logger.warning("No grounding metadata found in response")
                return articles

            grounding_metadata = candidate.grounding_metadata

            # Extract from grounding_chunks (official SDK format)
            if hasattr(grounding_metadata, 'grounding_chunks'):
                for chunk in grounding_metadata.grounding_chunks:
                    if hasattr(chunk, 'web'):
                        article = self.parse_grounding_chunk(chunk.web, query)
                        if article:
                            articles.append(article)

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

            # If title is empty or just a domain, try to extract from URL path
            if not title or title == source_name or '.' in title and '/' not in title:
                title = self.extract_title_from_url(url)

            # Skip if we still couldn't get a meaningful title
            if not title or title == source_name:
                self.logger.debug(f"Skipping article with no title: {url}")
                return None

            # Extract tags from query
            tags = [tag.strip() for tag in query.split() if len(tag.strip()) > 2]

            return {
                "url": url,
                "title": title,
                "summary": title,  # Use title as summary
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

    @staticmethod
    def extract_title_from_url(url: str) -> str:
        """
        Extract a potential title from URL path

        Args:
            url: Article URL

        Returns:
            str: Extracted title or empty string

        Example:
            >>> GoogleSearchGroundingTool.extract_title_from_url(
            ...     "https://example.com/blog/my-article-title"
            ... )
            'My Article Title'
        """
        try:
            from urllib.parse import urlparse, unquote

            parsed = urlparse(url)
            path = parsed.path.strip('/')

            if not path:
                return ''

            # Get the last path segment
            segments = path.split('/')
            last_segment = segments[-1] if segments else ''

            # Remove file extension if present
            if '.' in last_segment:
                last_segment = last_segment.rsplit('.', 1)[0]

            # Convert URL-encoded characters and dashes/underscores to spaces
            title = unquote(last_segment)
            title = title.replace('-', ' ').replace('_', ' ')

            # Capitalize words
            title = title.title()

            # Skip if it looks like an ID or date (too short, all numbers, etc.)
            if len(title) < 10 or title.replace(' ', '').isdigit():
                return ''

            return title

        except Exception:
            return ''

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

    def close(self):
        """
        Close the client and release resources

        Example:
            >>> search_tool = GoogleSearchGroundingTool()
            >>> # ... use the tool
            >>> search_tool.close()
        """
        if hasattr(self, 'client'):
            self.client.close()
            self.logger.info("Client closed successfully")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
