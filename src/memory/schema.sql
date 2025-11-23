-- InsightCosmos Database Schema
-- Version: 1.0
-- Created: 2025-11-21
-- Description: SQLite database schema for InsightCosmos Memory Layer

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrent performance
PRAGMA journal_mode = WAL;

-- ========================================
-- Table 1: articles
-- ========================================
-- Description: Stores collected articles with metadata and analysis results
-- Primary Key: id (auto-increment)
-- Unique Constraint: url (for deduplication)

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    source TEXT NOT NULL,  -- 'rss' or 'search'
    source_name TEXT,       -- RSS feed name or search engine
    published_at DATETIME,  -- Article publish time
    fetched_at DATETIME NOT NULL,  -- When we fetched the article
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'analyzed', 'reported'
    priority_score REAL,    -- Priority score from Analyst Agent (0.0 - 1.0)
    analysis TEXT,          -- Analysis result in JSON format
    tags TEXT,              -- Comma-separated tags
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for articles table
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_priority_score ON articles(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_articles_fetched_at ON articles(fetched_at DESC);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_articles_timestamp
AFTER UPDATE ON articles
BEGIN
    UPDATE articles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


-- ========================================
-- Table 2: embeddings
-- ========================================
-- Description: Stores article embedding vectors for similarity search
-- Primary Key: id (auto-increment)
-- Foreign Key: article_id -> articles(id) with CASCADE DELETE
-- Unique Constraint: (article_id, model) - one embedding per article per model

CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,    -- Serialized numpy array (using pickle)
    model TEXT NOT NULL,         -- Model name (e.g., 'text-embedding-3')
    dimension INTEGER NOT NULL,  -- Vector dimension
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    UNIQUE(article_id, model)
);

-- Indexes for embeddings table
CREATE INDEX IF NOT EXISTS idx_embeddings_article_id ON embeddings(article_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model);


-- ========================================
-- Table 3: daily_reports
-- ========================================
-- Description: Stores daily digest reports
-- Primary Key: id (auto-increment)
-- Unique Constraint: report_date (one report per day)

CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    article_count INTEGER NOT NULL,
    top_articles TEXT NOT NULL,  -- JSON array of article IDs
    content TEXT NOT NULL,        -- Report content in Markdown format
    sent_at DATETIME,             -- Email sent timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for daily_reports table
CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(report_date DESC);


-- ========================================
-- Table 4: weekly_reports
-- ========================================
-- Description: Stores weekly summary reports
-- Primary Key: id (auto-increment)
-- Unique Constraint: (week_start, week_end) - one report per week

CREATE TABLE IF NOT EXISTS weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    article_count INTEGER NOT NULL,
    top_themes TEXT,             -- JSON array of themes
    content TEXT NOT NULL,       -- Report content in Markdown format
    sent_at DATETIME,            -- Email sent timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(week_start, week_end)
);

-- Indexes for weekly_reports table
CREATE INDEX IF NOT EXISTS idx_weekly_reports_dates ON weekly_reports(week_start DESC, week_end DESC);


-- ========================================
-- Sample Data for Testing (Optional)
-- ========================================
-- Uncomment below to insert sample data for testing

-- INSERT INTO articles (url, title, content, source, source_name, fetched_at, status)
-- VALUES
--     ('https://example.com/ai-breakthrough',
--      'Major AI Breakthrough in 2024',
--      'Detailed article content here...',
--      'rss',
--      'TechCrunch',
--      CURRENT_TIMESTAMP,
--      'pending');
