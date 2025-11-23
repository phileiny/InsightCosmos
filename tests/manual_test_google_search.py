# -*- coding: utf-8 -*-
"""
Manual Test Script for Google Search Tool

This script tests the GoogleSearchTool with real API calls.

WARNING: This will consume your Google Search API quota!
- Free tier: 100 queries/day
- Each test query counts against quota

Usage:
    python tests/manual_test_google_search.py

Prerequisites:
    - .env file configured with GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID
    - Valid Google Custom Search API credentials
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.google_search import GoogleSearchTool
from src.utils.logger import Logger
import json
from datetime import datetime


def print_separator():
    """Print visual separator"""
    print("\n" + "=" * 80 + "\n")


def test_1_initialization():
    """Test 1: GoogleSearchTool initialization"""
    print_separator()
    print("TEST 1: GoogleSearchTool Initialization")
    print_separator()

    try:
        search_tool = GoogleSearchTool()
        print("✅ GoogleSearchTool initialized successfully")
        print(f"   - API Endpoint: {search_tool.API_ENDPOINT}")
        print(f"   - Timeout: {search_tool.timeout}s")
        print(f"   - Engine ID: {search_tool.engine_id[:10]}...")
        return search_tool
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        print("\nPlease check:")
        print("1. .env file exists")
        print("2. GOOGLE_SEARCH_API_KEY is set")
        print("3. GOOGLE_SEARCH_ENGINE_ID is set")
        sys.exit(1)


def test_2_validate_credentials(search_tool):
    """Test 2: Validate API credentials"""
    print_separator()
    print("TEST 2: Validate API Credentials")
    print_separator()

    print("⏳ Validating credentials... (this uses 1 API quota)")

    is_valid = search_tool.validate_api_credentials()

    if is_valid:
        print("✅ API credentials are valid")
    else:
        print("❌ API credentials validation failed")
        print("\nPlease check:")
        print("1. API Key is correct")
        print("2. Custom Search Engine ID is correct")
        print("3. API is enabled in Google Cloud Console")
        sys.exit(1)


def test_3_single_search(search_tool):
    """Test 3: Single search"""
    print_separator()
    print("TEST 3: Single Search")
    print_separator()

    query = "AI multi-agent systems"
    max_results = 5

    print(f"🔍 Searching: '{query}'")
    print(f"   Max Results: {max_results}")
    print(f"   Date Restriction: Last 7 days")
    print()

    result = search_tool.search_articles(
        query=query,
        max_results=max_results,
        date_restrict='d7'
    )

    print(f"Status: {result['status']}")
    print(f"Total Results (estimate): {result['total_results']}")
    print(f"Articles Returned: {len(result['articles'])}")
    print(f"Quota Exceeded: {result['quota_exceeded']}")
    print(f"Searched At: {result['searched_at']}")

    if result['status'] == 'success':
        print("\n✅ Search successful!")
        print("\nArticles:")
        for i, article in enumerate(result['articles'], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")
            print(f"   Source: {article['source_name']}")
            print(f"   Summary: {article['summary'][:100]}...")
            print(f"   Tags: {', '.join(article['tags'][:3])}")
    else:
        print(f"\n❌ Search failed: {result['error_message']}")
        if result['quota_exceeded']:
            print("\n⚠️  API quota exceeded. Please try again tomorrow.")
            sys.exit(1)


def test_4_batch_search(search_tool):
    """Test 4: Batch search"""
    print_separator()
    print("TEST 4: Batch Search")
    print_separator()

    queries = [
        "AI agents",
        "robotics news",
        "large language models"
    ]
    max_results_per_query = 3

    print(f"🔍 Batch searching {len(queries)} queries:")
    for i, q in enumerate(queries, 1):
        print(f"   {i}. '{q}'")
    print(f"\n   Max Results Per Query: {max_results_per_query}")
    print()

    result = search_tool.batch_search(
        queries=queries,
        max_results_per_query=max_results_per_query
    )

    print(f"Status: {result['status']}")
    print(f"\nSummary:")
    print(f"   Total Queries: {result['summary']['total_queries']}")
    print(f"   Successful: {result['summary']['successful_queries']}")
    print(f"   Failed: {result['summary']['failed_queries']}")
    print(f"   Total Articles: {result['summary']['total_articles']}")
    print(f"   Quota Exceeded: {result['summary']['quota_exceeded']}")

    if result['status'] in ['success', 'partial']:
        print("\n✅ Batch search completed!")

        # Show unique sources
        sources = set(article['source_name'] for article in result['articles'])
        print(f"\nUnique Sources ({len(sources)}):")
        for source in sorted(sources):
            count = sum(1 for a in result['articles'] if a['source_name'] == source)
            print(f"   - {source}: {count} articles")

        # Show sample articles
        print("\nSample Articles:")
        for i, article in enumerate(result['articles'][:5], 1):
            print(f"\n{i}. [{article['search_query']}] {article['title']}")
            print(f"   {article['url'][:70]}...")

    if result['errors']:
        print(f"\n⚠️  {len(result['errors'])} errors occurred:")
        for error in result['errors']:
            print(f"   - Query '{error['query']}': {error['error_message']}")

    if result['summary']['quota_exceeded']:
        print("\n⚠️  API quota exceeded during batch search")


def test_5_domain_extraction():
    """Test 5: Domain extraction"""
    print_separator()
    print("TEST 5: Domain Extraction")
    print_separator()

    test_urls = [
        "https://www.techcrunch.com/ai/article",
        "https://blog.openai.com/research",
        "http://news.ycombinator.com/item?id=123",
        "https://www.arxiv.org/abs/2024.01234",
        "invalid-url"
    ]

    print("Testing domain extraction from various URLs:\n")

    for url in test_urls:
        domain = GoogleSearchTool.extract_domain(url)
        print(f"   {url}")
        print(f"   → {domain}\n")

    print("✅ Domain extraction test complete")


def test_6_quota_detection():
    """Test 6: Quota exceeded detection"""
    print_separator()
    print("TEST 6: Quota Exceeded Detection")
    print_separator()

    test_cases = [
        ({"error": {"code": 403, "message": "Quota exceeded"}}, True, "403 quota error"),
        ({"error": {"code": 429, "message": "Rate limit"}}, True, "429 rate limit"),
        ({"error": {"code": 500, "message": "Server error"}}, False, "500 server error"),
        ({"error": {"code": 200}}, False, "200 success"),
    ]

    print("Testing quota detection:\n")

    for error_response, expected, description in test_cases:
        result = GoogleSearchTool.is_quota_exceeded(error_response)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {description}: {result} (expected: {expected})")

    print("\n✅ Quota detection test complete")


def save_results_to_file(search_tool):
    """Save test results to JSON file"""
    print_separator()
    print("SAVING TEST RESULTS")
    print_separator()

    # Run a quick search and save results
    result = search_tool.search_articles(
        query="AI robotics",
        max_results=3,
        date_restrict='d7'
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tests/google_search_results_{timestamp}.json"

    output_data = {
        "timestamp": timestamp,
        "test_query": "AI robotics",
        "status": result['status'],
        "total_results": result['total_results'],
        "articles_count": len(result['articles']),
        "articles": result['articles'],
        "quota_exceeded": result['quota_exceeded']
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")


def main():
    """Main test runner"""
    print("\n" + "=" * 80)
    print(" " * 20 + "Google Search Tool - Manual Test")
    print("=" * 80)

    logger = Logger.get_logger("ManualTest")
    logger.info("Starting manual tests for Google Search Tool")

    try:
        # Test 1: Initialization
        search_tool = test_1_initialization()

        # Test 2: Validate credentials
        test_2_validate_credentials(search_tool)

        # Test 3: Single search
        test_3_single_search(search_tool)

        # Test 4: Batch search
        test_4_batch_search(search_tool)

        # Test 5: Domain extraction
        test_5_domain_extraction()

        # Test 6: Quota detection
        test_6_quota_detection()

        # Save results
        save_results_to_file(search_tool)

        # Final summary
        print_separator()
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
        print_separator()
        print("\nAPI Quota Usage:")
        print("   - Test 2 (Validation): 1 query")
        print("   - Test 3 (Single Search): 1 query")
        print("   - Test 4 (Batch Search): 3 queries")
        print("   - Save Results: 1 query")
        print("   TOTAL: ~6 queries used")
        print("\nRemaining quota: ~94/100 (if starting fresh)")
        print_separator()

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        logger.error(f"Manual test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
