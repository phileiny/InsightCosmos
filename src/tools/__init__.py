"""
InsightCosmos Tools Module

This module provides tools for the InsightCosmos agents to interact with
external data sources and services.

Tools:
    - RSSFetcher: RSS/Atom feed fetching and parsing
    - GoogleSearchGroundingTool: Google Search via Gemini Grounding (official SDK)
    - ContentExtractor: Article content extraction from URLs
    - EmailSender: Email sending utility with SMTP support
    - DigestFormatter: Format digest data into HTML and plain text emails
    - VectorClusteringTool: Vector clustering for topic identification (K-Means/DBSCAN)
    - TrendAnalysisTool: Hot trend identification and emerging topic detection

Usage:
    from src.tools import RSSFetcher, GoogleSearchGroundingTool, ContentExtractor

    # RSS Feed
    fetcher = RSSFetcher()
    result = fetcher.fetch_rss_feeds(['https://example.com/feed/'])

    # Google Search Grounding (推荐)
    with GoogleSearchGroundingTool() as search_tool:
        result = search_tool.search_articles('AI robotics')

    # Content Extraction
    extractor = ContentExtractor()
    article = extractor.extract('https://example.com/article')

Version History:
    - 1.4.0: 新增 VectorClusteringTool (Stage 10)
    - 1.3.0: 新增 EmailSender 與 DigestFormatter (Stage 8)
    - 1.2.0: 新增 ContentExtractor (trafilatura + BeautifulSoup)
    - 1.1.0: 迁移到 Gemini Search Grounding (googleapis/python-genai v1.33.0)
    - 1.0.0: 初始版本 (Custom Search API)
"""

from src.tools.fetcher import RSSFetcher
from src.tools.google_search_grounding_v2 import GoogleSearchGroundingTool
from src.tools.content_extractor import ContentExtractor, extract_content
from src.tools.email_sender import EmailSender, EmailConfig, send_email
from src.tools.digest_formatter import DigestFormatter, format_html, format_text
from src.tools.vector_clustering import VectorClusteringTool, cluster_articles
from src.tools.trend_analysis import TrendAnalysisTool, analyze_weekly_trends

# 保留旧的 import 以向后兼容（如果需要）
try:
    from src.tools.google_search import GoogleSearchTool
    _HAS_LEGACY_SEARCH = True
except ImportError:
    _HAS_LEGACY_SEARCH = False
    GoogleSearchTool = None  # type: ignore

__all__ = [
    'RSSFetcher',
    'GoogleSearchGroundingTool',
    'ContentExtractor',
    'extract_content',
    'EmailSender',
    'EmailConfig',
    'send_email',
    'DigestFormatter',
    'format_html',
    'format_text',
    'VectorClusteringTool',
    'cluster_articles',
    'TrendAnalysisTool',
    'analyze_weekly_trends',
]

# 如果需要旧版本，可以添加到 __all__
if _HAS_LEGACY_SEARCH:
    __all__.append('GoogleSearchTool')

__version__ = '1.4.0'
