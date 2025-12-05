"""
InsightCosmos Memory Layer

This module provides database management, article storage, and embedding functionality
for the InsightCosmos project.

Modules:
    - database: Database connection and session management
    - models: SQLAlchemy ORM models
    - article_store: Article CRUD operations
    - embedding_store: Embedding vector storage and similarity search

Usage:
    from src.memory import Database, ArticleStore, EmbeddingStore
    from src.utils.config import Config

    # Initialize database
    config = Config()
    db = Database.from_config(config)
    db.init_db()

    # Use article store
    article_store = ArticleStore(db)
    article_id = article_store.create(url="...", title="...", source="rss")

    # Use embedding store
    embedding_store = EmbeddingStore(db)
    embedding_store.store(article_id=article_id, vector=np.array([...]))
"""

from src.memory.database import Database
from src.memory.models import Article, Embedding, DailyReport, WeeklyReport, Base
from src.memory.article_store import ArticleStore
from src.memory.embedding_store import EmbeddingStore
from src.memory.report_store import ReportStore

__all__ = [
    'Database',
    'Article',
    'Embedding',
    'DailyReport',
    'WeeklyReport',
    'Base',
    'ArticleStore',
    'EmbeddingStore',
    'ReportStore',
]

__version__ = '1.0.0'
