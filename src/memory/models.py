"""
InsightCosmos Memory Models

SQLAlchemy ORM models for the InsightCosmos database.

Models:
    - Article: Article data and metadata
    - Embedding: Article embedding vectors
    - DailyReport: Daily digest reports
    - WeeklyReport: Weekly summary reports

Usage:
    from src.memory.models import Article, Embedding

    article = Article(
        url="https://example.com/article",
        title="Article Title",
        source="rss",
        fetched_at=datetime.utcnow()
    )
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
import json

Base = declarative_base()


class Article(Base):
    """
    Article ORM model

    Represents a collected article with metadata and analysis results.

    Attributes:
        id (int): Primary key
        url (str): Article URL (unique)
        title (str): Article title
        content (str): Article content
        summary (str): Article summary
        source (str): Source type ('rss' or 'search')
        source_name (str): Source name (feed name, etc.)
        published_at (datetime): Article publish time
        fetched_at (datetime): When we fetched the article
        status (str): Processing status ('pending', 'analyzed', 'reported')
        priority_score (float): Priority score from Analyst Agent
        analysis (str): Analysis result in JSON format
        tags (str): Comma-separated tags
        created_at (datetime): Record creation time
        updated_at (datetime): Record update time
        embeddings (relationship): Related embeddings
    """
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    source = Column(Text, nullable=False)
    source_name = Column(Text)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, nullable=False)
    status = Column(Text, nullable=False, default='pending', index=True)
    priority_score = Column(Float, index=True)
    analysis = Column(Text)  # JSON string
    tags = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    embeddings = relationship(
        "Embedding",
        back_populates="article",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Article to dictionary

        Returns:
            dict: Article data as dictionary

        Example:
            >>> article = Article(url="...", title="...")
            >>> data = article.to_dict()
            >>> print(data['title'])
        """
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'source': self.source,
            'source_name': self.source_name,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
            'status': self.status,
            'priority_score': self.priority_score,
            'analysis': json.loads(self.analysis) if self.analysis else None,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation"""
        return f"<Article(id={self.id}, title='{self.title[:30]}...', status='{self.status}')>"


class Embedding(Base):
    """
    Embedding ORM model

    Represents an article's embedding vector for similarity search.

    Attributes:
        id (int): Primary key
        article_id (int): Foreign key to articles table
        embedding (bytes): Serialized numpy array (using pickle)
        model (str): Model name (e.g., 'text-embedding-3')
        dimension (int): Vector dimension
        created_at (datetime): Record creation time
        article (relationship): Related article
    """
    __tablename__ = 'embeddings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        Integer,
        ForeignKey('articles.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    embedding = Column(LargeBinary, nullable=False)  # Serialized numpy array
    model = Column(Text, nullable=False, index=True)
    dimension = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    article = relationship("Article", back_populates="embeddings")

    def to_dict(self, include_vector: bool = False) -> Dict[str, Any]:
        """
        Convert Embedding to dictionary

        Args:
            include_vector: Whether to include the embedding vector (default: False)

        Returns:
            dict: Embedding data as dictionary

        Example:
            >>> embedding = Embedding(article_id=1, ...)
            >>> data = embedding.to_dict()
            >>> print(data['model'])
        """
        result = {
            'id': self.id,
            'article_id': self.article_id,
            'model': self.model,
            'dimension': self.dimension,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_vector:
            import pickle
            result['embedding'] = pickle.loads(self.embedding).tolist()

        return result

    def __repr__(self) -> str:
        """String representation"""
        return f"<Embedding(id={self.id}, article_id={self.article_id}, model='{self.model}', dim={self.dimension})>"


class DailyReport(Base):
    """
    Daily Report ORM model

    Represents a daily digest report.

    Attributes:
        id (int): Primary key
        report_date (datetime): Report date (unique)
        article_count (int): Number of articles included
        top_articles (str): JSON array of article IDs
        content (str): Report content in Markdown format
        sent_at (datetime): Email sent timestamp
        created_at (datetime): Record creation time
    """
    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(DateTime, unique=True, nullable=False, index=True)
    article_count = Column(Integer, nullable=False)
    top_articles = Column(Text, nullable=False)  # JSON array
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DailyReport to dictionary

        Returns:
            dict: Report data as dictionary
        """
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'article_count': self.article_count,
            'top_articles': json.loads(self.top_articles) if self.top_articles else [],
            'content': self.content,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation"""
        return f"<DailyReport(id={self.id}, date='{self.report_date}', articles={self.article_count})>"


class WeeklyReport(Base):
    """
    Weekly Report ORM model

    Represents a weekly summary report.

    Attributes:
        id (int): Primary key
        week_start (datetime): Week start date
        week_end (datetime): Week end date
        article_count (int): Number of articles included
        top_themes (str): JSON array of themes
        content (str): Report content in Markdown format
        sent_at (datetime): Email sent timestamp
        created_at (datetime): Record creation time
    """
    __tablename__ = 'weekly_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    article_count = Column(Integer, nullable=False)
    top_themes = Column(Text)  # JSON array
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert WeeklyReport to dictionary

        Returns:
            dict: Report data as dictionary
        """
        return {
            'id': self.id,
            'week_start': self.week_start.isoformat() if self.week_start else None,
            'week_end': self.week_end.isoformat() if self.week_end else None,
            'article_count': self.article_count,
            'top_themes': json.loads(self.top_themes) if self.top_themes else [],
            'content': self.content,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation"""
        return f"<WeeklyReport(id={self.id}, {self.week_start} to {self.week_end}, articles={self.article_count})>"
