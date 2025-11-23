"""
InsightCosmos Tools Module

This module provides tools for the InsightCosmos agents to interact with
external data sources and services.

Tools:
    - RSSFetcher: RSS/Atom feed fetching and parsing
    - GoogleSearchGroundingTool: Google Search via Gemini Grounding (official SDK)
    - ContentExtractor: Article content extraction from URLs

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
    - 1.2.0: 新增 ContentExtractor (trafilatura + BeautifulSoup)
    - 1.1.0: 迁移到 Gemini Search Grounding (googleapis/python-genai v1.33.0)
    - 1.0.0: 初始版本 (Custom Search API)
"""

from src.tools.fetcher import RSSFetcher
from src.tools.google_search_grounding_v2 import GoogleSearchGroundingTool
from src.tools.content_extractor import ContentExtractor, extract_content

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
]

# 如果需要旧版本，可以添加到 __all__
if _HAS_LEGACY_SEARCH:
    __all__.append('GoogleSearchTool')

__version__ = '1.2.0'
