"""
InsightCosmos Database Manager

Handles database connection, initialization, and session management.

Classes:
    Database: Database connection and session manager

Usage:
    from src.utils.config import Config
    from src.memory.database import Database

    config = Config()
    db = Database.from_config(config)
    db.init_db()

    with db.get_session() as session:
        # Use session to query database
        articles = session.query(Article).all()
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Generator, Optional
from contextlib import contextmanager
import sqlite3
import logging

from src.utils.config import Config
from src.utils.logger import Logger
from src.memory.models import Base


class Database:
    """
    Database connection and session manager

    Responsibilities:
    - Create and manage SQLite database connection
    - Initialize database schema
    - Provide session context manager
    - Enable SQLite foreign key constraints
    - Enable WAL mode for better concurrency

    Attributes:
        database_url (str): Database connection URL
        engine: SQLAlchemy engine
        SessionLocal: SQLAlchemy session factory
        logger (Logger): Logger instance

    Example:
        >>> config = Config()
        >>> db = Database.from_config(config)
        >>> db.init_db()
        >>> with db.get_session() as session:
        ...     articles = session.query(Article).all()
    """

    def __init__(self, database_url: str, logger: Optional[logging.Logger] = None):
        """
        Initialize database connection

        Args:
            database_url: SQLite database URL (e.g., 'sqlite:///data/insights.db')
            logger: Logger instance for logging database operations

        Example:
            >>> db = Database('sqlite:///data/insights.db')
        """
        self.database_url = database_url
        self.logger = logger or Logger.get_logger("Database")

        # Ensure database directory exists
        self._ensure_database_directory()

        # Create SQLAlchemy engine
        self.engine = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30.0  # 30 seconds timeout for locks
            },
            poolclass=StaticPool,  # Use static pool for SQLite
            echo=False  # Set to True for SQL debugging
        )

        # Enable foreign key constraints for all connections
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Enable foreign keys and WAL mode for each connection"""
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self.logger.info(f"Database initialized: {database_url}")

    @classmethod
    def from_config(cls, config: Config) -> "Database":
        """
        Create Database instance from Config

        Args:
            config: Config instance containing database settings

        Returns:
            Database: Database instance

        Example:
            >>> config = Config(...)
            >>> db = Database.from_config(config)
        """
        database_path = config.database_path
        database_url = f"sqlite:///{database_path}"

        logger = Logger.get_logger("Database")
        logger.info(f"Creating database from config: {database_path}")

        return cls(database_url, logger)

    def _ensure_database_directory(self) -> None:
        """
        Ensure the database directory exists

        Creates the parent directory if it doesn't exist.
        """
        if self.database_url.startswith('sqlite:///'):
            db_path = self.database_url.replace('sqlite:///', '')
            db_dir = Path(db_path).parent

            if not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created database directory: {db_dir}")

    def init_db(self, drop_all: bool = False) -> None:
        """
        Initialize database schema

        Creates all tables defined in models.py and executes schema.sql
        for additional constraints and indexes.

        Args:
            drop_all: If True, drop all existing tables first (default: False)
                     WARNING: This will delete all data!

        Example:
            >>> db.init_db()  # Create tables if not exist
            >>> db.init_db(drop_all=True)  # Recreate all tables
        """
        try:
            if drop_all:
                self.logger.warning("Dropping all existing tables...")
                Base.metadata.drop_all(bind=self.engine)

            # Create all tables from models
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")

            # Execute schema.sql for additional constraints
            self._execute_schema_sql()

            # Verify tables were created
            self._verify_tables()

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def _execute_schema_sql(self) -> None:
        """
        Execute schema.sql for additional constraints and indexes

        This ensures triggers and other SQL-specific features are properly set up.
        """
        try:
            schema_path = Path(__file__).parent / 'schema.sql'

            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()

                with self.engine.connect() as conn:
                    # Split by semicolon and execute each statement
                    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                    for statement in statements:
                        if statement and not statement.startswith('--'):
                            conn.execute(text(statement))
                    conn.commit()

                self.logger.info("Schema SQL executed successfully")
            else:
                self.logger.warning(f"schema.sql not found at {schema_path}")

        except Exception as e:
            self.logger.error(f"Failed to execute schema.sql: {e}")
            # Not raising exception here as tables are already created by create_all

    def _verify_tables(self) -> None:
        """
        Verify that all required tables exist

        Raises:
            RuntimeError: If required tables are missing
        """
        expected_tables = ['articles', 'embeddings', 'daily_reports', 'weekly_reports']

        with self.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            existing_tables = [row[0] for row in result]

        missing_tables = set(expected_tables) - set(existing_tables)

        if missing_tables:
            raise RuntimeError(f"Missing tables: {missing_tables}")

        self.logger.info(f"Verified tables: {', '.join(expected_tables)}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session as context manager

        Automatically commits on success and rolls back on error.

        Yields:
            Session: SQLAlchemy session

        Example:
            >>> with db.get_session() as session:
            ...     article = Article(url="...", title="...")
            ...     session.add(article)
            ...     # Automatically commits here

        Raises:
            Exception: Any exception during database operations
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Session error, rolling back: {e}")
            raise
        finally:
            session.close()

    def execute_raw_sql(self, sql: str) -> None:
        """
        Execute raw SQL statement

        Args:
            sql: SQL statement to execute

        Example:
            >>> db.execute_raw_sql("DELETE FROM articles WHERE status='pending'")

        Warning:
            Use with caution. Prefer ORM methods for type safety.
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            self.logger.info(f"Executed raw SQL: {sql[:50]}...")
        except Exception as e:
            self.logger.error(f"Failed to execute raw SQL: {e}")
            raise

    def get_table_stats(self) -> dict:
        """
        Get statistics about database tables

        Returns:
            dict: Table names and row counts

        Example:
            >>> stats = db.get_table_stats()
            >>> print(f"Articles: {stats['articles']}")
        """
        stats = {}

        with self.engine.connect() as conn:
            tables = ['articles', 'embeddings', 'daily_reports', 'weekly_reports']

            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[table] = count

        return stats

    def close(self) -> None:
        """
        Close database connection

        Disposes the engine and closes all connections.

        Example:
            >>> db.close()
        """
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __repr__(self) -> str:
        """String representation"""
        return f"<Database(url='{self.database_url}')>"
