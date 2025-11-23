# -*- coding: utf-8 -*-
"""
Test script for Google Search Grounding Tool

This script validates the new Gemini-based search implementation.

Usage:
    python tests/test_google_search_grounding.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.google_search_grounding import GoogleSearchGroundingTool
from src.utils.logger import Logger


def test_basic_search():
    """Test basic search functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Search")
    print("="*60)

    try:
        search_tool = GoogleSearchGroundingTool()
        print("✅ GoogleSearchGroundingTool initialized successfully")

        result = search_tool.search_articles(
            query="AI multi-agent systems",
            max_results=5
        )

        print(f"\nSearch status: {result['status']}")
        print(f"Query: {result['query']}")
        print(f"Total results: {result['total_results']}")
        print(f"Articles found: {len(result['articles'])}")

        if result['status'] == 'success' and len(result['articles']) > 0:
            print("\n✅ TEST PASSED: Search returned results")

            print("\nSample article:")
            article = result['articles'][0]
            print(f"  Title: {article['title']}")
            print(f"  URL: {article['url']}")
            print(f"  Source: {article['source_name']}")
            print(f"  Tags: {article['tags']}")

            return True
        else:
            print(f"\n❌ TEST FAILED: {result.get('error_message', 'No results')}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_search():
    """Test batch search functionality"""
    print("\n" + "="*60)
    print("TEST 2: Batch Search")
    print("="*60)

    try:
        search_tool = GoogleSearchGroundingTool()

        queries = [
            "robotics AI news",
            "large language models",
            "reinforcement learning"
        ]

        result = search_tool.batch_search(
            queries=queries,
            max_results_per_query=3
        )

        print(f"\nBatch search status: {result['status']}")
        print(f"Summary: {result['summary']}")
        print(f"Total articles: {len(result['articles'])}")

        if result['status'] in ['success', 'partial'] and len(result['articles']) > 0:
            print("\n✅ TEST PASSED: Batch search returned results")

            if result['errors']:
                print(f"\n⚠️  Errors encountered: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"  - {error['query']}: {error['error_message']}")

            return True
        else:
            print(f"\n❌ TEST FAILED: Batch search failed")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_validation():
    """Test API credentials validation"""
    print("\n" + "="*60)
    print("TEST 3: API Credentials Validation")
    print("="*60)

    try:
        search_tool = GoogleSearchGroundingTool()

        is_valid = search_tool.validate_api_credentials()

        if is_valid:
            print("\n✅ TEST PASSED: API credentials are valid")
            return True
        else:
            print("\n❌ TEST FAILED: API credentials are invalid")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_date_restrict():
    """Test date restriction functionality"""
    print("\n" + "="*60)
    print("TEST 4: Date Restriction")
    print("="*60)

    try:
        search_tool = GoogleSearchGroundingTool()

        result = search_tool.search_articles(
            query="AI news",
            max_results=5,
            date_restrict="past week"
        )

        print(f"\nSearch status: {result['status']}")
        print(f"Articles found: {len(result['articles'])}")

        if result['status'] == 'success':
            print("\n✅ TEST PASSED: Date restriction applied successfully")
            return True
        else:
            print(f"\n❌ TEST FAILED: {result.get('error_message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Google Search Grounding Tool - Test Suite")
    print("="*60)

    # Set up logging
    logger = Logger.get_logger("test_google_search_grounding", log_level="INFO")

    tests = [
        ("API Validation", test_api_validation),
        ("Basic Search", test_basic_search),
        ("Batch Search", test_batch_search),
        ("Date Restriction", test_date_restrict),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
