# -*- coding: utf-8 -*-
"""
Simple test for Google Search Grounding Tool (Official SDK)

Based on googleapis/python-genai v1.33.0
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.google_search_grounding_v2 import GoogleSearchGroundingTool


def main():
    """Simple search test"""
    print("\n" + "="*60)
    print("Google Search Grounding Tool - Quick Test")
    print("(Using official googleapis/python-genai SDK)")
    print("="*60)

    try:
        # Initialize tool
        print("\nInitializing search tool...")
        search_tool = GoogleSearchGroundingTool()
        print("✓ Tool initialized")

        # Perform search
        print("\nSearching for: 'AI multi-agent systems'")
        result = search_tool.search_articles(
            query="AI multi-agent systems",
            max_results=5
        )

        # Display results
        print(f"\nStatus: {result['status']}")
        print(f"Query: {result['query']}")
        print(f"Articles found: {len(result['articles'])}")

        if result['status'] == 'success' and len(result['articles']) > 0:
            print("\n✓ Search successful!")
            print("\nSample articles:")
            for i, article in enumerate(result['articles'][:3], 1):
                print(f"\n{i}. {article['title']}")
                print(f"   URL: {article['url']}")
                print(f"   Source: {article['source_name']}")
        else:
            print(f"\n✗ Search failed: {result.get('error_message', 'Unknown error')}")

        # Close client
        search_tool.close()
        print("\n✓ Client closed")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
