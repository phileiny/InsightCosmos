"""
Manual integration test for RSS Fetcher

This tests the fetcher with real RSS feeds to verify functionality.
Run manually: python tests/manual_test_fetcher.py
"""

import sys
sys.path.insert(0, '.')

from src.tools.fetcher import RSSFetcher

def test_real_rss_feed():
    """Test with a real RSS feed"""
    fetcher = RSSFetcher(timeout=10)

    # Test with a reliable RSS feed
    feed_url = 'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml'

    print(f"Fetching feed: {feed_url}")
    result = fetcher.fetch_single_feed(feed_url, max_articles=3)

    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Feed Title: {result['feed_title']}")
        print(f"Articles count: {len(result['articles'])}")

        for i, article in enumerate(result['articles'], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")
            print(f"   Published: {article['published_at']}")
            print(f"   Tags: {article['tags']}")
    else:
        print(f"Error: {result.get('error_message')}")

if __name__ == '__main__':
    test_real_rss_feed()
