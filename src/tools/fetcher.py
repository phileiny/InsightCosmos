"""
InsightCosmos RSS Fetcher Tool

Provides RSS/Atom feed fetching and parsing functionality.

Classes:
    RSSFetcher: RSS feed fetcher and parser

Usage:
    from src.tools.fetcher import RSSFetcher

    fetcher = RSSFetcher(timeout=30)
    result = fetcher.fetch_rss_feeds([
        'https://techcrunch.com/category/artificial-intelligence/feed/',
        'https://venturebeat.com/category/ai/feed/'
    ])

    print(f"Total articles: {result['summary']['total_articles']}")
    for article in result['articles']:
        print(f"- {article['title']}")
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
import logging
import time

import feedparser
import requests
from email.utils import parsedate_to_datetime

from src.utils.logger import Logger


class RSSFetcher:
    """
    RSS Feed fetcher and parser

    Provides functionality for:
    - Fetching RSS/Atom feeds
    - Parsing feed entries
    - Extracting article metadata
    - Batch processing multiple feeds
    - Error handling and recovery

    Attributes:
        timeout (int): HTTP request timeout in seconds
        user_agent (str): HTTP User-Agent string
        logger (Logger): Logger instance

    Example:
        >>> fetcher = RSSFetcher(timeout=10)
        >>> result = fetcher.fetch_single_feed('https://example.com/feed/')
        >>> print(f"Fetched {len(result['articles'])} articles")
    """

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str = "InsightCosmos/1.0 (AI News Aggregator)",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize RSS Fetcher

        Args:
            timeout: HTTP request timeout in seconds (default: 30)
            user_agent: HTTP User-Agent string
            logger: Logger instance (optional)

        Example:
            >>> fetcher = RSSFetcher(timeout=15)
        """
        self.timeout = timeout
        self.user_agent = user_agent
        self.logger = logger or Logger.get_logger("RSSFetcher")

        # Configure feedparser
        feedparser.USER_AGENT = user_agent

        self.logger.info(f"RSSFetcher initialized (timeout={timeout}s)")

    def fetch_rss_feeds(
        self,
        feed_urls: List[str],
        max_articles_per_feed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Batch fetch multiple RSS feeds

        Args:
            feed_urls: List of RSS feed URLs
            max_articles_per_feed: Maximum articles per feed (optional)

        Returns:
            dict: {
                "status": "success" | "partial" | "error",
                "articles": List[Dict],  # All articles from all feeds
                "errors": List[Dict],    # Errors for failed feeds
                "summary": {
                    "total_feeds": int,
                    "successful_feeds": int,
                    "failed_feeds": int,
                    "total_articles": int
                }
            }

        Example:
            >>> result = fetcher.fetch_rss_feeds([
            ...     'https://techcrunch.com/feed/',
            ...     'https://venturebeat.com/feed/'
            ... ], max_articles_per_feed=10)
            >>> print(result['summary'])
        """
        self.logger.info(f"Starting batch fetch: {len(feed_urls)} feeds")

        all_articles = []
        errors = []
        successful_count = 0
        failed_count = 0

        for feed_url in feed_urls:
            try:
                result = self.fetch_single_feed(feed_url, max_articles_per_feed)

                if result['status'] == 'success':
                    all_articles.extend(result['articles'])
                    successful_count += 1
                    self.logger.info(
                        f"✓ {feed_url}: {len(result['articles'])} articles"
                    )
                else:
                    failed_count += 1
                    errors.append({
                        'feed_url': feed_url,
                        'error_type': 'FetchError',
                        'error_message': result.get('error_message', 'Unknown error')
                    })
                    self.logger.warning(f"✗ {feed_url}: {result.get('error_message')}")

            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                errors.append({
                    'feed_url': feed_url,
                    'error_type': type(e).__name__,
                    'error_message': error_msg
                })
                self.logger.error(f"✗ {feed_url}: {error_msg}")

        # Determine overall status
        if successful_count == len(feed_urls):
            status = "success"
        elif successful_count > 0:
            status = "partial"
        else:
            status = "error"

        summary = {
            'total_feeds': len(feed_urls),
            'successful_feeds': successful_count,
            'failed_feeds': failed_count,
            'total_articles': len(all_articles)
        }

        self.logger.info(
            f"Batch fetch complete: {successful_count}/{len(feed_urls)} feeds, "
            f"{len(all_articles)} articles"
        )

        return {
            'status': status,
            'articles': all_articles,
            'errors': errors,
            'summary': summary
        }

    def fetch_single_feed(
        self,
        feed_url: str,
        max_articles: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch single RSS feed

        Args:
            feed_url: RSS feed URL
            max_articles: Maximum number of articles to return (optional)

        Returns:
            dict: {
                "status": "success" | "error",
                "feed_url": str,
                "feed_title": str,
                "articles": List[Dict],
                "error_message": str (if error),
                "fetched_at": datetime
            }

        Example:
            >>> result = fetcher.fetch_single_feed(
            ...     'https://techcrunch.com/feed/',
            ...     max_articles=5
            ... )
            >>> if result['status'] == 'success':
            ...     print(f"Feed: {result['feed_title']}")
        """
        fetched_at = datetime.now(timezone.utc)

        # Validate URL
        if not self.validate_url(feed_url):
            return {
                'status': 'error',
                'feed_url': feed_url,
                'error_message': f'Invalid URL format: {feed_url}',
                'fetched_at': fetched_at
            }

        try:
            # Fetch feed with timeout
            self.logger.debug(f"Fetching feed: {feed_url}")

            # Use requests to fetch with timeout, then parse
            headers = {'User-Agent': self.user_agent}
            response = requests.get(
                feed_url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            # Parse feed
            feed = feedparser.parse(response.content)

            # Check for feed errors
            bozo = getattr(feed, 'bozo', False)
            if bozo and not getattr(feed, 'entries', []):
                bozo_exception = getattr(feed, 'bozo_exception', None)
                if bozo_exception:
                    error_msg = getattr(bozo_exception, 'getMessage', lambda: str(bozo_exception))()
                else:
                    error_msg = 'Unknown parsing error'
                return {
                    'status': 'error',
                    'feed_url': feed_url,
                    'error_message': f'Feed parsing error: {error_msg}',
                    'fetched_at': fetched_at
                }

            # Extract feed metadata
            feed_info = getattr(feed, 'feed', {})
            feed_title = feed_info.get('title', 'Unknown Feed') if isinstance(feed_info, dict) else 'Unknown Feed'

            # Parse entries
            articles = []
            all_entries = getattr(feed, 'entries', [])
            entries = all_entries[:max_articles] if max_articles else all_entries

            for entry in entries:
                try:
                    article = self.parse_feed_entry(entry, feed_title, feed_url)
                    articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Failed to parse entry: {e}")
                    continue

            return {
                'status': 'success',
                'feed_url': feed_url,
                'feed_title': feed_title,
                'articles': articles,
                'fetched_at': fetched_at
            }

        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'feed_url': feed_url,
                'error_message': f'Request timeout after {self.timeout} seconds',
                'fetched_at': fetched_at
            }

        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'feed_url': feed_url,
                'error_message': f'Network error: {str(e)}',
                'fetched_at': fetched_at
            }

        except Exception as e:
            return {
                'status': 'error',
                'feed_url': feed_url,
                'error_message': f'Unexpected error: {str(e)}',
                'fetched_at': fetched_at
            }

    def parse_feed_entry(
        self,
        entry: Any,
        feed_title: str,
        feed_url: str
    ) -> Dict[str, Any]:
        """
        Parse single feed entry to structured article data

        Args:
            entry: feedparser entry object
            feed_title: Feed title
            feed_url: Feed URL

        Returns:
            dict: {
                "url": str,
                "title": str,
                "summary": str,
                "content": str,
                "published_at": datetime,
                "source": "rss",
                "source_name": str,
                "tags": List[str]
            }

        Example:
            >>> article = fetcher.parse_feed_entry(entry, "TechCrunch", "...")
            >>> print(article['title'])
        """
        # Extract URL (required)
        url = entry.get('link', '')
        if not url:
            raise ValueError("Entry missing 'link' field")

        # Extract title (required)
        title = entry.get('title', 'Untitled')

        # Extract summary
        summary = entry.get('summary', '')
        if not summary:
            summary = entry.get('description', '')

        # Extract content (if available)
        content = ''
        if hasattr(entry, 'content'):
            # Some feeds have content as list
            if isinstance(entry.content, list) and len(entry.content) > 0:
                content = entry.content[0].get('value', '')
            else:
                content = str(entry.content)
        elif hasattr(entry, 'description'):
            content = entry.description
        else:
            content = entry.get('description', '')

        # Extract published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                # Convert struct_time to datetime
                import time
                published_at = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed),
                    tz=timezone.utc
                )
            except:
                pass

        if not published_at and hasattr(entry, 'published') and entry.published:
            published_at = self.parse_published_date(entry.published)

        if not published_at:
            # Try to get from dict-style access
            pub_date = entry.get('published') if hasattr(entry, 'get') else None
            if pub_date:
                published_at = self.parse_published_date(pub_date)

        # Use current time if no published date
        if not published_at:
            published_at = datetime.now(timezone.utc)

        # Extract tags/categories
        tags = []
        if hasattr(entry, 'tags') and entry.tags:
            tags = [tag.get('term', '') for tag in entry.tags if hasattr(tag, 'get') and tag.get('term')]

        return {
            'url': url,
            'title': title,
            'summary': summary,
            'content': content,
            'published_at': published_at,
            'source': 'rss',
            'source_name': feed_title,
            'tags': tags
        }

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is valid, False otherwise

        Example:
            >>> RSSFetcher.validate_url('https://example.com/feed/')
            True
            >>> RSSFetcher.validate_url('invalid-url')
            False
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False

    @staticmethod
    def parse_published_date(date_str: str) -> Optional[datetime]:
        """
        Parse RSS published date string

        Supports multiple date formats:
        - RFC 2822 (e.g., 'Wed, 20 Nov 2024 10:00:00 GMT')
        - ISO 8601 (e.g., '2024-11-20T10:00:00Z')

        Args:
            date_str: Date string to parse

        Returns:
            Optional[datetime]: Parsed datetime, or None if parsing fails

        Example:
            >>> date = RSSFetcher.parse_published_date('Wed, 20 Nov 2024 10:00:00 GMT')
            >>> print(date)
        """
        if not date_str:
            return None

        try:
            # Try RFC 2822 format first (common in RSS)
            return parsedate_to_datetime(date_str)
        except:
            pass

        try:
            # Try ISO 8601 format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass

        return None
