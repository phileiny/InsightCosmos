"""
InsightCosmos Article Store

Provides CRUD operations for article data.

Classes:
    ArticleStore: Article data management

Usage:
    from src.memory.database import Database
    from src.memory.article_store import ArticleStore

    db = Database.from_config(config)
    store = ArticleStore(db)

    # Create article
    article_id = store.create(
        url="https://example.com/article",
        title="Article Title",
        source="rss"
    )

    # Query article
    article = store.get_by_id(article_id)
    articles = store.get_by_status("pending")
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
import logging

from src.memory.models import Article
from src.memory.database import Database
from src.utils.logger import Logger


class ArticleStore:
    """
    Article storage management

    Provides CRUD operations for article data with support for:
    - Creating and updating articles
    - Querying by ID, URL, status, date range
    - Priority-based sorting
    - Deduplication by URL
    - Status tracking

    Attributes:
        database (Database): Database instance
        logger (Logger): Logger instance

    Example:
        >>> store = ArticleStore(db)
        >>> article_id = store.create(url="...", title="...", source="rss")
        >>> article = store.get_by_id(article_id)
        >>> articles = store.get_by_status("pending", limit=10)
    """

    def __init__(self, database: Database, logger: Optional[logging.Logger] = None):
        """
        Initialize ArticleStore

        Args:
            database: Database instance
            logger: Logger instance (optional)
        """
        self.database = database
        self.logger = logger or Logger.get_logger("ArticleStore")

    def create(
        self,
        url: str,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        source: str = "unknown",
        source_name: Optional[str] = None,
        published_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Create new article

        Args:
            url: Article URL (must be unique)
            title: Article title
            content: Article content (optional)
            summary: Article summary (optional)
            source: Source type ('rss', 'search', etc.)
            source_name: Source name (feed name, etc.)
            published_at: Article publish time (optional)
            tags: List of tags (optional)

        Returns:
            int: Article ID

        Raises:
            ValueError: If URL already exists

        Example:
            >>> article_id = store.create(
            ...     url="https://example.com/ai-news",
            ...     title="AI Breakthrough",
            ...     source="rss",
            ...     source_name="TechCrunch",
            ...     tags=["AI", "Research"]
            ... )
        """
        # Check if URL already exists
        if self.exists(url):
            raise ValueError(f"Article with URL already exists: {url}")

        try:
            with self.database.get_session() as session:
                article = Article(
                    url=url,
                    title=title,
                    content=content,
                    summary=summary,
                    source=source,
                    source_name=source_name,
                    published_at=published_at,
                    fetched_at=datetime.utcnow(),
                    status='pending',
                    tags=','.join(tags) if tags else None
                )

                session.add(article)
                session.flush()  # Get the ID before commit

                article_id = article.id

                self.logger.info(f"Created article: {article_id} - {title[:50]}")

                return article_id

        except Exception as e:
            self.logger.error(f"Failed to create article: {e}")
            raise

    def get_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        Get article by ID

        Args:
            article_id: Article ID

        Returns:
            Optional[dict]: Article data or None if not found

        Example:
            >>> article = store.get_by_id(1)
            >>> print(article['title'])
        """
        try:
            with self.database.get_session() as session:
                article = session.query(Article).filter(Article.id == article_id).first()

                if article:
                    return article.to_dict()
                return None

        except Exception as e:
            self.logger.error(f"Failed to get article by ID {article_id}: {e}")
            raise

    def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get article by URL (for deduplication)

        Args:
            url: Article URL

        Returns:
            Optional[dict]: Article data or None if not found

        Example:
            >>> article = store.get_by_url("https://example.com/article")
        """
        try:
            with self.database.get_session() as session:
                article = session.query(Article).filter(Article.url == url).first()

                if article:
                    return article.to_dict()
                return None

        except Exception as e:
            self.logger.error(f"Failed to get article by URL: {e}")
            raise

    def get_by_status(
        self,
        status: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get articles by status

        Args:
            status: Article status ('pending', 'analyzed', 'reported')
            limit: Maximum number of results (optional)

        Returns:
            List[dict]: List of articles

        Example:
            >>> pending_articles = store.get_by_status("pending", limit=10)
        """
        try:
            with self.database.get_session() as session:
                query = session.query(Article).filter(Article.status == status)
                query = query.order_by(desc(Article.fetched_at))

                if limit:
                    query = query.limit(limit)

                articles = query.all()

                return [article.to_dict() for article in articles]

        except Exception as e:
            self.logger.error(f"Failed to get articles by status: {e}")
            raise

    def get_recent(
        self,
        days: int = 7,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent articles (last N days)

        Args:
            days: Number of days to look back (default: 7)
            limit: Maximum number of results (optional)

        Returns:
            List[dict]: List of articles

        Example:
            >>> recent = store.get_recent(days=7, limit=20)
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            with self.database.get_session() as session:
                query = session.query(Article).filter(
                    Article.fetched_at >= cutoff_date
                )
                query = query.order_by(desc(Article.fetched_at))

                if limit:
                    query = query.limit(limit)

                articles = query.all()

                return [article.to_dict() for article in articles]

        except Exception as e:
            self.logger.error(f"Failed to get recent articles: {e}")
            raise

    def get_top_priority(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top priority articles

        Args:
            limit: Maximum number of results (default: 10)
            status: Filter by status (optional)

        Returns:
            List[dict]: List of articles ordered by priority score (descending)

        Example:
            >>> top_articles = store.get_top_priority(limit=5, status="analyzed")
        """
        try:
            with self.database.get_session() as session:
                query = session.query(Article).filter(
                    Article.priority_score.isnot(None)
                )

                if status:
                    query = query.filter(Article.status == status)

                query = query.order_by(desc(Article.priority_score))
                query = query.limit(limit)

                articles = query.all()

                return [article.to_dict() for article in articles]

        except Exception as e:
            self.logger.error(f"Failed to get top priority articles: {e}")
            raise

    def update(
        self,
        article_id: int,
        **kwargs
    ) -> bool:
        """
        Update article fields

        Args:
            article_id: Article ID
            **kwargs: Fields to update (e.g., status='analyzed', priority_score=0.8)

        Returns:
            bool: True if updated successfully, False if article not found

        Example:
            >>> store.update(1, status="analyzed", priority_score=0.85)
        """
        try:
            with self.database.get_session() as session:
                article = session.query(Article).filter(Article.id == article_id).first()

                if not article:
                    self.logger.warning(f"Article not found: {article_id}")
                    return False

                # Update fields
                for key, value in kwargs.items():
                    if hasattr(article, key):
                        setattr(article, key, value)

                # updated_at will be automatically updated by the trigger

                self.logger.info(f"Updated article {article_id}: {list(kwargs.keys())}")

                return True

        except Exception as e:
            self.logger.error(f"Failed to update article {article_id}: {e}")
            raise

    def update_status(
        self,
        article_id: int,
        status: str
    ) -> bool:
        """
        Update article status

        Args:
            article_id: Article ID
            status: New status ('pending', 'analyzed', 'reported')

        Returns:
            bool: True if updated successfully

        Example:
            >>> store.update_status(1, "analyzed")
        """
        return self.update(article_id, status=status)

    def update_analysis(
        self,
        article_id: int,
        analysis: Dict[str, Any],
        priority_score: float
    ) -> bool:
        """
        Update article analysis results

        Args:
            article_id: Article ID
            analysis: Analysis result dictionary
            priority_score: Priority score (0.0 - 1.0)

        Returns:
            bool: True if updated successfully

        Example:
            >>> store.update_analysis(
            ...     article_id=1,
            ...     analysis={"key_points": ["..."], "sentiment": "positive"},
            ...     priority_score=0.85
            ... )
        """
        return self.update(
            article_id,
            analysis=json.dumps(analysis),
            priority_score=priority_score,
            status='analyzed'
        )

    def delete(self, article_id: int) -> bool:
        """
        Delete article (and cascade delete embeddings)

        Args:
            article_id: Article ID

        Returns:
            bool: True if deleted successfully, False if not found

        Example:
            >>> store.delete(1)
        """
        try:
            with self.database.get_session() as session:
                article = session.query(Article).filter(Article.id == article_id).first()

                if not article:
                    self.logger.warning(f"Article not found for deletion: {article_id}")
                    return False

                session.delete(article)

                self.logger.info(f"Deleted article: {article_id}")

                return True

        except Exception as e:
            self.logger.error(f"Failed to delete article {article_id}: {e}")
            raise

    def exists(self, url: str) -> bool:
        """
        Check if article URL already exists (for deduplication)

        Args:
            url: Article URL

        Returns:
            bool: True if URL exists

        Example:
            >>> if not store.exists(url):
            ...     store.create(url=url, title=title, ...)
        """
        try:
            with self.database.get_session() as session:
                count = session.query(Article).filter(Article.url == url).count()
                return count > 0

        except Exception as e:
            self.logger.error(f"Failed to check article existence: {e}")
            raise

    def count_by_status(self, status: str) -> int:
        """
        Count articles by status

        Args:
            status: Article status

        Returns:
            int: Number of articles with the given status

        Example:
            >>> pending_count = store.count_by_status("pending")
            >>> print(f"Pending articles: {pending_count}")
        """
        try:
            with self.database.get_session() as session:
                count = session.query(Article).filter(Article.status == status).count()
                return count

        except Exception as e:
            self.logger.error(f"Failed to count articles by status: {e}")
            raise

    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all articles

        Args:
            limit: Maximum number of results (optional)

        Returns:
            List[dict]: List of all articles

        Example:
            >>> all_articles = store.get_all(limit=100)
        """
        try:
            with self.database.get_session() as session:
                query = session.query(Article).order_by(desc(Article.created_at))

                if limit:
                    query = query.limit(limit)

                articles = query.all()

                return [article.to_dict() for article in articles]

        except Exception as e:
            self.logger.error(f"Failed to get all articles: {e}")
            raise

    def store_article(self, article_data: Dict[str, Any]) -> int:
        """
        Store a complete article (convenience method for testing/migration)

        This method accepts a full article dictionary and stores it directly,
        including analysis results. Useful for testing and data migration.

        Args:
            article_data: Complete article dictionary with all fields

        Returns:
            int: Article ID

        Raises:
            ValueError: If URL already exists or required fields missing

        Example:
            >>> article_data = {
            ...     "url": "https://example.com/article",
            ...     "title": "Article Title",
            ...     "content": "Content...",
            ...     "summary": "Summary...",
            ...     "key_insights": ["insight1", "insight2"],
            ...     "priority_score": 0.85,
            ...     "priority_reasoning": "Important...",
            ...     "tags": "AI,Robotics",
            ...     "status": "analyzed",
            ...     "source_name": "TechCrunch",
            ...     "published_at": datetime.now()
            ... }
            >>> article_id = store.store_article(article_data)
        """
        # Check required fields
        if 'url' not in article_data or 'title' not in article_data:
            raise ValueError("Missing required fields: url and title")

        # Check if URL already exists
        if self.exists(article_data['url']):
            raise ValueError(f"Article with URL already exists: {article_data['url']}")

        try:
            with self.database.get_session() as session:
                # Handle tags conversion
                tags = article_data.get('tags')
                if isinstance(tags, list):
                    tags = ','.join(tags)

                # Build analysis JSON from key_insights and priority_reasoning
                analysis_dict = {}
                if 'key_insights' in article_data:
                    analysis_dict['key_insights'] = article_data['key_insights']
                if 'priority_reasoning' in article_data:
                    analysis_dict['priority_reasoning'] = article_data['priority_reasoning']

                analysis = json.dumps(analysis_dict) if analysis_dict else None

                article = Article(
                    url=article_data['url'],
                    title=article_data['title'],
                    content=article_data.get('content'),
                    summary=article_data.get('summary'),
                    priority_score=article_data.get('priority_score'),
                    analysis=analysis,
                    tags=tags,
                    source=article_data.get('source', 'unknown'),
                    source_name=article_data.get('source_name'),
                    published_at=article_data.get('published_at'),
                    fetched_at=article_data.get('fetched_at', datetime.utcnow()),
                    status=article_data.get('status', 'pending')
                )

                session.add(article)
                session.flush()

                article_id = article.id

                self.logger.info(f"Stored article: {article_id} - {article_data['title'][:50]}")

                return article_id

        except Exception as e:
            self.logger.error(f"Failed to store article: {e}")
            raise
