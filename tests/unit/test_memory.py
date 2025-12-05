"""
Unit tests for InsightCosmos Memory Layer

Tests cover:
- Database initialization and table creation
- Article CRUD operations
- Embedding storage and retrieval
- Similarity search functionality

Test Cases:
    TC-2-01: Database initialization success
    TC-2-02: Database creates all tables
    TC-2-03: ArticleStore creates article
    TC-2-04: ArticleStore URL deduplication
    TC-2-05: ArticleStore queries article
    TC-2-06: ArticleStore updates status
    TC-2-07: ArticleStore priority sorting
    TC-2-08: EmbeddingStore stores vector
    TC-2-09: EmbeddingStore gets vector
    TC-2-10: EmbeddingStore similarity search
    TC-2-11: EmbeddingStore cosine similarity
    TC-2-12: ArticleStore queries by date range

Run with: pytest tests/unit/test_memory.py -v
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from src.utils.config import Config
from src.memory import Database, ArticleStore, EmbeddingStore, ReportStore, Article


@pytest.fixture(scope='function')
def temp_db_path():
    """Create a temporary database path for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_insights.db"
    yield str(db_path)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def test_config(temp_db_path):
    """Create a test configuration"""
    config = Config(
        google_api_key="test_google_key",
        email_account="test@example.com",
        email_password="test_password",
        database_path=temp_db_path
    )
    return config


@pytest.fixture(scope='function')
def database(test_config):
    """Create and initialize a test database"""
    db = Database.from_config(test_config)
    db.init_db()
    yield db
    db.close()


@pytest.fixture(scope='function')
def article_store(database):
    """Create ArticleStore instance"""
    return ArticleStore(database)


@pytest.fixture(scope='function')
def embedding_store(database):
    """Create EmbeddingStore instance"""
    return EmbeddingStore(database)


# ========================================
# TC-2-01: Database Initialization Success
# ========================================

def test_database_initialization(test_config):
    """
    TC-2-01: Test database initialization from config

    Expected:
    - Database object created successfully
    - Database URL is correct
    """
    db = Database.from_config(test_config)

    assert db is not None
    assert 'test_insights.db' in db.database_url
    assert db.engine is not None
    assert db.SessionLocal is not None

    db.close()


# ========================================
# TC-2-02: Database Creates All Tables
# ========================================

def test_database_creates_all_tables(database):
    """
    TC-2-02: Test database creates all required tables

    Expected:
    - articles table exists
    - embeddings table exists
    - daily_reports table exists
    - weekly_reports table exists
    """
    stats = database.get_table_stats()

    assert 'articles' in stats
    assert 'embeddings' in stats
    assert 'daily_reports' in stats
    assert 'weekly_reports' in stats

    # All tables should be empty initially
    assert stats['articles'] == 0
    assert stats['embeddings'] == 0
    assert stats['daily_reports'] == 0
    assert stats['weekly_reports'] == 0


# ========================================
# TC-2-03: ArticleStore Creates Article
# ========================================

def test_article_store_create(article_store):
    """
    TC-2-03: Test creating a new article

    Expected:
    - Article ID is returned
    - Article can be retrieved by ID
    - Article data matches input
    """
    article_id = article_store.create(
        url="https://example.com/test-article",
        title="Test Article",
        content="This is test content",
        summary="Test summary",
        source="rss",
        source_name="Test Feed",
        tags=["AI", "Test"]
    )

    assert article_id > 0

    # Retrieve and verify
    article = article_store.get_by_id(article_id)

    assert article is not None
    assert article['id'] == article_id
    assert article['url'] == "https://example.com/test-article"
    assert article['title'] == "Test Article"
    assert article['content'] == "This is test content"
    assert article['summary'] == "Test summary"
    assert article['source'] == "rss"
    assert article['source_name'] == "Test Feed"
    assert article['status'] == "pending"
    assert article['tags'] == ["AI", "Test"]


# ========================================
# TC-2-04: ArticleStore URL Deduplication
# ========================================

def test_article_store_url_deduplication(article_store):
    """
    TC-2-04: Test URL deduplication

    Expected:
    - First article creation succeeds
    - Second article with same URL raises ValueError
    """
    url = "https://example.com/duplicate-test"

    # First creation should succeed
    article_id = article_store.create(
        url=url,
        title="First Article",
        source="rss"
    )

    assert article_id > 0

    # Second creation should fail
    with pytest.raises(ValueError, match="already exists"):
        article_store.create(
            url=url,
            title="Duplicate Article",
            source="rss"
        )


# ========================================
# TC-2-05: ArticleStore Queries Article
# ========================================

def test_article_store_query(article_store):
    """
    TC-2-05: Test querying articles by ID and URL

    Expected:
    - Can query by ID
    - Can query by URL
    - Returns None for non-existent articles
    """
    # Create test article
    article_id = article_store.create(
        url="https://example.com/query-test",
        title="Query Test Article",
        source="search"
    )

    # Query by ID
    article_by_id = article_store.get_by_id(article_id)
    assert article_by_id is not None
    assert article_by_id['id'] == article_id

    # Query by URL
    article_by_url = article_store.get_by_url("https://example.com/query-test")
    assert article_by_url is not None
    assert article_by_url['id'] == article_id

    # Query non-existent
    non_existent = article_store.get_by_id(99999)
    assert non_existent is None


# ========================================
# TC-2-06: ArticleStore Updates Status
# ========================================

def test_article_store_update_status(article_store):
    """
    TC-2-06: Test updating article status

    Expected:
    - Status can be updated
    - Updated status is persisted
    """
    # Create article
    article_id = article_store.create(
        url="https://example.com/status-test",
        title="Status Test",
        source="rss"
    )

    # Verify initial status
    article = article_store.get_by_id(article_id)
    assert article['status'] == "pending"

    # Update status
    success = article_store.update_status(article_id, "analyzed")
    assert success is True

    # Verify updated status
    article = article_store.get_by_id(article_id)
    assert article['status'] == "analyzed"

    # Update again
    success = article_store.update_status(article_id, "reported")
    assert success is True

    article = article_store.get_by_id(article_id)
    assert article['status'] == "reported"


# ========================================
# TC-2-07: ArticleStore Priority Sorting
# ========================================

def test_article_store_priority_sorting(article_store):
    """
    TC-2-07: Test getting top priority articles

    Expected:
    - Articles returned in descending priority order
    - Limit parameter works correctly
    """
    # Create articles with different priority scores
    articles_data = [
        ("https://example.com/article1", "Article 1", 0.9),
        ("https://example.com/article2", "Article 2", 0.5),
        ("https://example.com/article3", "Article 3", 0.7),
        ("https://example.com/article4", "Article 4", 0.3),
        ("https://example.com/article5", "Article 5", 0.8),
    ]

    for url, title, score in articles_data:
        article_id = article_store.create(url=url, title=title, source="rss")
        article_store.update(article_id, priority_score=score, status="analyzed")

    # Get top 3 articles
    top_articles = article_store.get_top_priority(limit=3, status="analyzed")

    assert len(top_articles) == 3
    assert top_articles[0]['priority_score'] == 0.9
    assert top_articles[1]['priority_score'] == 0.8
    assert top_articles[2]['priority_score'] == 0.7


# ========================================
# TC-2-08: EmbeddingStore Stores Vector
# ========================================

def test_embedding_store_store_vector(article_store, embedding_store):
    """
    TC-2-08: Test storing embedding vector

    Expected:
    - Embedding ID is returned
    - Embedding can be retrieved
    """
    # Create article first
    article_id = article_store.create(
        url="https://example.com/embedding-test",
        title="Embedding Test",
        source="rss"
    )

    # Create test vector
    vector = np.random.rand(768)

    # Store embedding
    embedding_id = embedding_store.store(
        article_id=article_id,
        vector=vector,
        model="test-model"
    )

    assert embedding_id > 0

    # Verify embedding exists
    exists = embedding_store.exists(article_id, model="test-model")
    assert exists is True


# ========================================
# TC-2-09: EmbeddingStore Gets Vector
# ========================================

def test_embedding_store_get_vector(article_store, embedding_store):
    """
    TC-2-09: Test retrieving embedding vector

    Expected:
    - Retrieved vector matches stored vector
    - Returns None for non-existent embeddings
    """
    # Create article
    article_id = article_store.create(
        url="https://example.com/get-vector-test",
        title="Get Vector Test",
        source="rss"
    )

    # Create and store vector
    original_vector = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

    embedding_store.store(
        article_id=article_id,
        vector=original_vector,
        model="test-model"
    )

    # Retrieve vector
    retrieved_vector = embedding_store.get(article_id, model="test-model")

    assert retrieved_vector is not None
    assert isinstance(retrieved_vector, np.ndarray)
    assert len(retrieved_vector) == len(original_vector)
    np.testing.assert_array_almost_equal(retrieved_vector, original_vector)

    # Try to get non-existent embedding
    non_existent = embedding_store.get(article_id, model="non-existent-model")
    assert non_existent is None


# ========================================
# TC-2-10: EmbeddingStore Similarity Search
# ========================================

def test_embedding_store_similarity_search(article_store, embedding_store):
    """
    TC-2-10: Test finding similar articles

    Expected:
    - Returns top K most similar articles
    - Results are ordered by similarity (descending)
    """
    # Create articles with embeddings
    vectors = [
        np.array([1.0, 0.0, 0.0]),  # Article 1
        np.array([0.9, 0.1, 0.0]),  # Article 2 (similar to 1)
        np.array([0.0, 1.0, 0.0]),  # Article 3 (different)
    ]

    article_ids = []
    for i, vector in enumerate(vectors):
        article_id = article_store.create(
            url=f"https://example.com/similarity-test-{i}",
            title=f"Similarity Test {i}",
            source="rss"
        )
        article_ids.append(article_id)

        embedding_store.store(
            article_id=article_id,
            vector=vector,
            model="test-model"
        )

    # Query with a vector similar to Article 1
    query_vector = np.array([0.95, 0.05, 0.0])

    similar = embedding_store.find_similar(
        vector=query_vector,
        top_k=2,
        model="test-model"
    )

    assert len(similar) == 2

    # First result should be Article 1 or 2 (both similar)
    # Similarity scores should be in descending order
    assert similar[0][1] >= similar[1][1]


# ========================================
# TC-2-11: EmbeddingStore Cosine Similarity
# ========================================

def test_embedding_store_cosine_similarity():
    """
    TC-2-11: Test cosine similarity calculation

    Expected:
    - Identical vectors have similarity 1.0
    - Orthogonal vectors have similarity 0.0
    - Opposite vectors have similarity -1.0
    """
    # Identical vectors
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([1, 0, 0])
    similarity = EmbeddingStore.cosine_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 1e-6

    # Orthogonal vectors
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([0, 1, 0])
    similarity = EmbeddingStore.cosine_similarity(vec1, vec2)
    assert abs(similarity - 0.0) < 1e-6

    # Opposite vectors
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([-1, 0, 0])
    similarity = EmbeddingStore.cosine_similarity(vec1, vec2)
    assert abs(similarity - (-1.0)) < 1e-6

    # Similar vectors (45 degrees)
    vec1 = np.array([1, 0])
    vec2 = np.array([1, 1])
    similarity = EmbeddingStore.cosine_similarity(vec1, vec2)
    expected = 1 / np.sqrt(2)  # cos(45°) ≈ 0.707
    assert abs(similarity - expected) < 1e-6


# ========================================
# TC-2-12: ArticleStore Queries by Date Range
# ========================================

def test_article_store_query_by_date(article_store):
    """
    TC-2-12: Test querying articles by date range

    Expected:
    - get_recent() returns articles from last N days
    - Older articles are excluded
    """
    # Create articles with different fetch times
    # (We'll manually update fetched_at for testing)

    # Recent article (today)
    recent_id = article_store.create(
        url="https://example.com/recent",
        title="Recent Article",
        source="rss"
    )

    # Old article (10 days ago)
    old_id = article_store.create(
        url="https://example.com/old",
        title="Old Article",
        source="rss"
    )

    # Update old article's fetched_at
    old_date = datetime.utcnow() - timedelta(days=10)
    article_store.update(old_id, fetched_at=old_date)

    # Get recent articles (last 7 days)
    recent_articles = article_store.get_recent(days=7)

    # Should only include the recent article
    assert len(recent_articles) >= 1
    assert any(a['id'] == recent_id for a in recent_articles)
    assert not any(a['id'] == old_id for a in recent_articles)

    # Get all articles (last 30 days)
    all_articles = article_store.get_recent(days=30)

    # Should include both articles
    assert len(all_articles) >= 2
    assert any(a['id'] == recent_id for a in all_articles)
    assert any(a['id'] == old_id for a in all_articles)


# ========================================
# Additional Edge Case Tests
# ========================================

def test_article_store_exists_method(article_store):
    """Test ArticleStore.exists() method"""
    url = "https://example.com/exists-test"

    # Should not exist initially
    assert article_store.exists(url) is False

    # Create article
    article_store.create(url=url, title="Exists Test", source="rss")

    # Should exist now
    assert article_store.exists(url) is True


def test_article_store_count_by_status(article_store):
    """Test ArticleStore.count_by_status() method"""
    # Create articles with different statuses
    id1 = article_store.create(url="https://example.com/1", title="1", source="rss")
    id2 = article_store.create(url="https://example.com/2", title="2", source="rss")
    id3 = article_store.create(url="https://example.com/3", title="3", source="rss")

    # All should be pending initially
    assert article_store.count_by_status("pending") == 3
    assert article_store.count_by_status("analyzed") == 0

    # Update some statuses
    article_store.update_status(id1, "analyzed")
    article_store.update_status(id2, "analyzed")

    # Verify counts
    assert article_store.count_by_status("pending") == 1
    assert article_store.count_by_status("analyzed") == 2


def test_embedding_store_delete(article_store, embedding_store):
    """Test EmbeddingStore.delete() method"""
    # Create article and embedding
    article_id = article_store.create(
        url="https://example.com/delete-test",
        title="Delete Test",
        source="rss"
    )

    vector = np.random.rand(10)
    embedding_store.store(article_id=article_id, vector=vector, model="test-model")

    # Verify it exists
    assert embedding_store.exists(article_id, model="test-model") is True

    # Delete it
    success = embedding_store.delete(article_id, model="test-model")
    assert success is True

    # Verify it's gone
    assert embedding_store.exists(article_id, model="test-model") is False


def test_cascade_delete(article_store, embedding_store, database):
    """Test that deleting an article cascades to delete embeddings"""
    # Create article and embedding
    article_id = article_store.create(
        url="https://example.com/cascade-test",
        title="Cascade Test",
        source="rss"
    )

    vector = np.random.rand(10)
    embedding_store.store(article_id=article_id, vector=vector, model="test-model")

    # Verify embedding exists
    assert embedding_store.exists(article_id, model="test-model") is True

    # Delete article
    article_store.delete(article_id)

    # Embedding should be automatically deleted
    assert embedding_store.exists(article_id, model="test-model") is False


# ========================================
# TC-2-13: DailyReport Period Columns
# ========================================

def test_daily_report_has_period_columns():
    """
    TC-2-13: Test DailyReport model has period_start and period_end columns

    Expected:
    - DailyReport has period_start attribute
    - DailyReport has period_end attribute
    """
    from src.memory.models import DailyReport

    assert hasattr(DailyReport, 'period_start')
    assert hasattr(DailyReport, 'period_end')


def test_daily_report_to_dict_includes_period():
    """
    TC-2-14: Test DailyReport.to_dict() includes period columns

    Expected:
    - to_dict() returns period_start
    - to_dict() returns period_end
    - Values are correctly formatted as ISO strings
    """
    from src.memory.models import DailyReport

    report = DailyReport(
        report_date=datetime(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 8, 0),
        article_count=10,
        top_articles='[1,2,3]',
        content='{}'
    )

    result = report.to_dict()

    assert 'period_start' in result
    assert 'period_end' in result
    assert result['period_start'] == '2025-12-04T08:00:00'
    assert result['period_end'] == '2025-12-05T08:00:00'


def test_daily_report_period_nullable():
    """
    TC-2-15: Test DailyReport period columns are nullable for backward compatibility

    Expected:
    - DailyReport can be created without period_start/period_end
    - to_dict() returns None for missing period values
    """
    from src.memory.models import DailyReport

    # Create report without period columns (backward compatibility)
    report = DailyReport(
        report_date=datetime(2025, 12, 5),
        article_count=10,
        top_articles='[1,2,3]',
        content='{}'
    )

    result = report.to_dict()

    assert result['period_start'] is None
    assert result['period_end'] is None


def test_daily_report_repr():
    """
    TC-2-16: Test DailyReport __repr__ includes period info

    Expected:
    - String representation includes period information
    """
    from src.memory.models import DailyReport

    report = DailyReport(
        id=1,
        report_date=datetime(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 8, 0),
        article_count=10,
        top_articles='[1,2,3]',
        content='{}'
    )

    repr_str = repr(report)

    assert 'period=' in repr_str
    assert '2025-12-04' in repr_str
    assert '2025-12-05' in repr_str


# ========================================
# TC-2-17 ~ TC-2-22: ReportStore Tests
# ========================================

@pytest.fixture(scope='function')
def report_store(database):
    """Create ReportStore instance"""
    return ReportStore(database)


def test_report_store_get_last_empty(report_store):
    """
    TC-2-17: Test get_last_daily_report returns None when no reports exist

    Expected:
    - Returns None for empty database
    """
    result = report_store.get_last_daily_report()
    assert result is None


def test_report_store_create_daily_report(report_store):
    """
    TC-2-18: Test creating a daily report

    Expected:
    - Report ID is returned
    - Report can be retrieved by date
    """
    from datetime import date as dt_date

    report_id = report_store.create_daily_report(
        report_date=dt_date(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 8, 0),
        article_count=10,
        top_articles=[1, 2, 3],
        content='{"test": true}'
    )

    assert report_id > 0

    # Verify can retrieve by date
    report = report_store.get_daily_report_by_date(dt_date(2025, 12, 5))
    assert report is not None
    assert report['article_count'] == 10


def test_report_store_get_last_after_create(report_store):
    """
    TC-2-19: Test get_last_daily_report after creating a report

    Expected:
    - Returns the created report
    - period_end is correctly formatted
    """
    from datetime import date as dt_date

    report_store.create_daily_report(
        report_date=dt_date(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 8, 0),
        article_count=10,
        top_articles=[1, 2, 3],
        content='{}'
    )

    result = report_store.get_last_daily_report()

    assert result is not None
    assert result['article_count'] == 10
    assert result['period_end'] == '2025-12-05T08:00:00'


def test_report_store_duplicate_date_updates(report_store):
    """
    TC-2-20: Test creating report with duplicate date updates existing

    Expected:
    - Same ID is returned
    - Data is updated
    """
    from datetime import date as dt_date

    # First creation
    id1 = report_store.create_daily_report(
        report_date=dt_date(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 8, 0),
        article_count=10,
        top_articles=[1, 2, 3],
        content='{}'
    )

    # Second creation with same date
    id2 = report_store.create_daily_report(
        report_date=dt_date(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 10, 0),  # Different time
        article_count=15,  # Different count
        top_articles=[1, 2, 3, 4, 5],
        content='{}'
    )

    assert id1 == id2  # Same record

    # Verify updated
    report = report_store.get_daily_report_by_date(dt_date(2025, 12, 5))
    assert report['article_count'] == 15


def test_report_store_get_last_returns_most_recent(report_store):
    """
    TC-2-21: Test get_last_daily_report returns most recent report

    Expected:
    - Returns the newest report by created_at
    """
    from datetime import date as dt_date
    import time

    # Create older report
    report_store.create_daily_report(
        report_date=dt_date(2025, 12, 3),
        period_start=datetime(2025, 12, 2),
        period_end=datetime(2025, 12, 3),
        article_count=5,
        top_articles=[1],
        content='{}'
    )

    # Small delay to ensure different created_at
    time.sleep(0.1)

    # Create newer report
    report_store.create_daily_report(
        report_date=dt_date(2025, 12, 5),
        period_start=datetime(2025, 12, 4),
        period_end=datetime(2025, 12, 5),
        article_count=10,
        top_articles=[2],
        content='{}'
    )

    # Get last should return newer one
    result = report_store.get_last_daily_report()

    assert result['article_count'] == 10


def test_report_store_update_sent_at(report_store):
    """
    TC-2-22: Test updating sent_at timestamp

    Expected:
    - sent_at is updated
    """
    from datetime import date as dt_date

    report_id = report_store.create_daily_report(
        report_date=dt_date(2025, 12, 5),
        period_start=datetime(2025, 12, 4, 8, 0),
        period_end=datetime(2025, 12, 5, 8, 0),
        article_count=10,
        top_articles=[1, 2, 3],
        content='{}'
    )

    # Update sent_at
    sent_time = datetime(2025, 12, 5, 9, 0)
    success = report_store.update_sent_at(report_id, sent_time)

    assert success is True

    # Verify
    report = report_store.get_daily_report_by_date(dt_date(2025, 12, 5))
    assert report['sent_at'] == '2025-12-05T09:00:00'


# ========================================
# TC-2-23 ~ TC-2-28: ArticleStore Time Filter Tests
# ========================================

@pytest.fixture(scope='function')
def article_store_with_time_data(database):
    """Create ArticleStore with articles at different fetched_at times"""
    store = ArticleStore(database)
    now = datetime.utcnow()

    # 3 days ago article
    id1 = store.create(
        url="https://example.com/old",
        title="Old Article",
        source="test"
    )
    store.update(id1, fetched_at=now - timedelta(days=3), priority_score=0.9, status='analyzed')

    # 1 day ago article
    id2 = store.create(
        url="https://example.com/recent",
        title="Recent Article",
        source="test"
    )
    store.update(id2, fetched_at=now - timedelta(days=1), priority_score=0.8, status='analyzed')

    # Today article
    id3 = store.create(
        url="https://example.com/today",
        title="Today Article",
        source="test"
    )
    store.update(id3, fetched_at=now, priority_score=0.7, status='analyzed')

    return store, now


def test_get_top_priority_backward_compatible(article_store_with_time_data):
    """
    TC-2-23: Test get_top_priority without time params returns all articles (backward compatible)

    Expected:
    - Returns all analyzed articles when no time filter provided
    """
    store, _ = article_store_with_time_data

    articles = store.get_top_priority(limit=10, status='analyzed')

    assert len(articles) == 3


def test_get_top_priority_fetched_after_filter(article_store_with_time_data):
    """
    TC-2-24: Test fetched_after filter excludes older articles

    Expected:
    - Only returns articles fetched after the cutoff time
    """
    store, now = article_store_with_time_data

    # Only get articles from last 2 days
    cutoff = now - timedelta(days=2)
    articles = store.get_top_priority(
        limit=10,
        status='analyzed',
        fetched_after=cutoff
    )

    assert len(articles) == 2
    # Should not include the 3-day old article
    urls = [a['url'] for a in articles]
    assert 'https://example.com/old' not in urls


def test_get_top_priority_fetched_before_filter(article_store_with_time_data):
    """
    TC-2-25: Test fetched_before filter excludes newer articles

    Expected:
    - Only returns articles fetched before or at the cutoff time
    """
    store, now = article_store_with_time_data

    # Only get articles from before 2 days ago
    cutoff = now - timedelta(days=2)
    articles = store.get_top_priority(
        limit=10,
        status='analyzed',
        fetched_before=cutoff
    )

    assert len(articles) == 1
    assert articles[0]['url'] == 'https://example.com/old'


def test_get_top_priority_combined_filter(article_store_with_time_data):
    """
    TC-2-26: Test combined fetched_after and fetched_before filter

    Expected:
    - Returns articles within the specified time range
    """
    store, now = article_store_with_time_data

    # Get articles between 2 days ago and 12 hours ago
    after = now - timedelta(days=2)
    before = now - timedelta(hours=12)

    articles = store.get_top_priority(
        limit=10,
        status='analyzed',
        fetched_after=after,
        fetched_before=before
    )

    assert len(articles) == 1
    assert articles[0]['url'] == 'https://example.com/recent'


def test_get_top_priority_empty_result(article_store_with_time_data):
    """
    TC-2-27: Test returns empty list when no articles match time filter

    Expected:
    - Returns empty list for future time filter
    """
    store, now = article_store_with_time_data

    # Future time - no articles should match
    future = now + timedelta(days=1)
    articles = store.get_top_priority(
        limit=10,
        status='analyzed',
        fetched_after=future
    )

    assert len(articles) == 0


def test_get_top_priority_order_preserved(article_store_with_time_data):
    """
    TC-2-28: Test articles still ordered by priority_score with time filter

    Expected:
    - Results are ordered by priority_score descending
    """
    store, now = article_store_with_time_data

    articles = store.get_top_priority(
        limit=10,
        status='analyzed',
        fetched_after=now - timedelta(days=2)
    )

    # Should be sorted by priority_score descending
    scores = [a['priority_score'] for a in articles]
    assert scores == sorted(scores, reverse=True)
