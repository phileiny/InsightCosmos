# -*- coding: utf-8 -*-
"""
Test Gemini API with Google Search Grounding

This script tests the modern approach using Gemini's built-in Google Search capability.

Usage:
    python tests/test_gemini_grounding.py

Prerequisites:
    - GOOGLE_API_KEY configured in .env
    - google-generativeai package installed
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import google.generativeai as genai
from src.utils.config import Config
from src.utils.logger import Logger


def test_gemini_grounding():
    """Test Gemini API with Google Search Grounding"""

    logger = Logger.get_logger("GeminiGroundingTest")

    print("=" * 80)
    print(" " * 20 + "Gemini API Grounding Test")
    print("=" * 80)

    # Load configuration
    try:
        config = Config.load()
        api_key = config.google_api_key
        logger.info(f"Loaded API Key: {api_key[:10]}...")
    except Exception as e:
        print(f"\n❌ Failed to load config: {e}")
        print("\nPlease ensure:")
        print("1. .env file exists")
        print("2. GOOGLE_API_KEY is set")
        return False

    # Configure Gemini API
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully")
        print("\n✅ Gemini API configured successfully")
    except Exception as e:
        print(f"\n❌ Failed to configure Gemini API: {e}")
        return False

    # Set up tools: Enable Google Search
    tools = [
        {
            "google_search_retrieval": {}
        }
    ]

    # Initialize model with Google Search capability
    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            tools=tools
        )
        logger.info("Model initialized with Google Search Grounding")
        print("✅ Model initialized: gemini-1.5-flash")
        print("✅ Google Search Grounding enabled")
    except Exception as e:
        print(f"\n❌ Failed to initialize model: {e}")
        return False

    # Test queries
    test_queries = [
        "What are the latest developments in AI multi-agent systems in 2024?",
        "What is the current state of robotics and AI integration?",
        "What are recent breakthroughs in large language models?"
    ]

    for i, query in enumerate(test_queries, 1):
        print("\n" + "=" * 80)
        print(f"Test {i}/{len(test_queries)}")
        print("=" * 80)
        print(f"Query: {query}")
        print("-" * 80)

        try:
            # Start chat and send message
            chat = model.start_chat()
            response = chat.send_message(query)

            # Print response
            print("\n📝 Response:")
            print(response.text)

            # Check for grounding metadata
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]

                if hasattr(candidate, 'grounding_metadata'):
                    grounding = candidate.grounding_metadata

                    print("\n🔍 Grounding Information:")

                    # Check for search entry point
                    if hasattr(grounding, 'search_entry_point') and grounding.search_entry_point:
                        print("\n--- Search Entry Point ---")
                        if hasattr(grounding.search_entry_point, 'rendered_content'):
                            print(grounding.search_entry_point.rendered_content)

                    # Check for grounding chunks (sources)
                    if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                        print(f"\n--- Sources ({len(grounding.grounding_chunks)}) ---")
                        for idx, chunk in enumerate(grounding.grounding_chunks[:5], 1):
                            if hasattr(chunk, 'web') and chunk.web:
                                print(f"{idx}. {chunk.web.uri}")
                                if hasattr(chunk.web, 'title'):
                                    print(f"   Title: {chunk.web.title}")

                    # Check grounding support
                    if hasattr(grounding, 'grounding_supports'):
                        print(f"\n✅ Grounding confidence: {len(grounding.grounding_supports)} supports found")
                else:
                    print("\n⚠️  No grounding metadata available")

            print("\n✅ Test passed")
            logger.info(f"Query {i} completed successfully")

        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            logger.error(f"Query {i} failed: {e}", exc_info=True)
            continue

        # Pause between requests
        if i < len(test_queries):
            print("\n⏸️  Pausing 2 seconds before next query...")
            import time
            time.sleep(2)

    print("\n" + "=" * 80)
    print(" " * 25 + "Test Complete")
    print("=" * 80)

    return True


def test_simple_query():
    """Simple test with a single query"""

    print("\n" + "=" * 80)
    print(" " * 20 + "Simple Grounding Test")
    print("=" * 80)

    try:
        # Load config
        config = Config.load()
        genai.configure(api_key=config.google_api_key)

        # Setup model with Google Search
        tools = [{"google_search_retrieval": {}}]
        model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)

        # Test query
        query = "What are the top AI news from the last week?"
        print(f"\n📤 Query: {query}")

        chat = model.start_chat()
        response = chat.send_message(query)

        print("\n📥 Response:")
        print(response.text)

        # Try to extract sources
        try:
            if response.candidates[0].grounding_metadata.grounding_chunks:
                print("\n🔗 Sources:")
                for chunk in response.candidates[0].grounding_metadata.grounding_chunks[:3]:
                    if hasattr(chunk, 'web') and chunk.web:
                        print(f"  - {chunk.web.uri}")
        except Exception:
            print("\n⚠️  Could not extract source URLs")

        print("\n✅ Simple test passed")
        return True

    except Exception as e:
        print(f"\n❌ Simple test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Gemini API Grounding Tests")

    # Run simple test first
    print("\n" + "=" * 80)
    print("PHASE 1: Simple Test")
    print("=" * 80)

    if test_simple_query():
        print("\n✅ Phase 1 passed - proceeding to full tests")

        print("\n" + "=" * 80)
        print("PHASE 2: Full Tests")
        print("=" * 80)

        test_gemini_grounding()
    else:
        print("\n❌ Phase 1 failed - please check your configuration")
        print("\nTroubleshooting:")
        print("1. Verify GOOGLE_API_KEY is set in .env")
        print("2. Ensure API key is valid")
        print("3. Check if Gemini API is enabled in Google Cloud Console")
        sys.exit(1)
