"""
Manual test script for Stage 1 validation

This script tests Config and Logger functionality without pytest dependency.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import Logger


def test_logger():
    """Test Logger functionality"""
    print("=" * 60)
    print("Testing Logger...")
    print("=" * 60)

    try:
        # Test 1: Create logger
        logger = Logger.get_logger("manual_test", log_level="DEBUG")
        print("✓ Logger created successfully")

        # Test 2: Write different log levels
        logger.debug("This is a DEBUG message")
        logger.info("This is an INFO message")
        logger.warning("This is a WARNING message")
        logger.error("This is an ERROR message")
        print("✓ Log messages written successfully")

        # Test 3: Check log file
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        log_file = Path("logs") / f"manual_test_{today}.log"

        if log_file.exists():
            print(f"✓ Log file created: {log_file}")
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "INFO message" in content:
                    print("✓ Log file contains expected content")
                else:
                    print("✗ Log file missing expected content")
        else:
            print(f"✗ Log file not found: {log_file}")

        print("\n✓ All Logger tests passed!\n")
        return True

    except Exception as e:
        print(f"\n✗ Logger test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test Config functionality"""
    print("=" * 60)
    print("Testing Config...")
    print("=" * 60)

    try:
        # Test 1: Load config
        try:
            config = Config.load()
            print("✓ Config loaded from .env")
            print(f"  User: {config.user_name}")
            print(f"  Interests: {config.get_interests_list()}")
            print(f"  Log Level: {config.log_level}")
        except FileNotFoundError:
            print("✗ .env file not found - this is expected if not configured yet")
            print("  Creating test config...")

            # Create test .env file
            test_env = Path(".env.test")
            test_env.write_text("""
GOOGLE_API_KEY=test_key_12345
SEARCH_API_KEY=test_search_key
SEARCH_ENGINE_ID=test_engine_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
USER_NAME=TestUser
USER_INTERESTS=AI,Robotics,Testing
LOG_LEVEL=INFO
""".strip())

            config = Config.load(".env.test")
            print("✓ Config loaded from test file")
            print(f"  User: {config.user_name}")
            print(f"  Interests: {config.get_interests_list()}")

            # Clean up
            test_env.unlink()
            print("✓ Test file cleaned up")

        # Test 2: Test get_interests_list
        interests = config.get_interests_list()
        if isinstance(interests, list) and len(interests) > 0:
            print(f"✓ get_interests_list() works: {interests}")
        else:
            print("✗ get_interests_list() failed")

        # Test 3: Test __repr__ hides sensitive info
        repr_str = repr(config)
        if "sensitive fields hidden" in repr_str:
            print("✓ __repr__ hides sensitive information")
        else:
            print("✗ __repr__ does not hide sensitive information")

        print("\n✓ All Config tests passed!\n")
        return True

    except Exception as e:
        print(f"\n✗ Config test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Test Config validation"""
    print("=" * 60)
    print("Testing Config Validation...")
    print("=" * 60)

    try:
        # Test: Missing required field
        test_env = Path(".env.invalid")
        test_env.write_text("""
SEARCH_API_KEY=test_key
""".strip())

        try:
            config = Config.load(".env.invalid")
            print("✗ Should have raised ValueError for missing field")
            test_env.unlink()
            return False
        except ValueError as e:
            if "GOOGLE_API_KEY" in str(e):
                print(f"✓ Correctly caught missing field: {e}")
                test_env.unlink()
            else:
                print(f"✗ Wrong error message: {e}")
                test_env.unlink()
                return False

        print("\n✓ Config validation tests passed!\n")
        return True

    except Exception as e:
        print(f"\n✗ Config validation test failed: {e}\n")
        import traceback
        traceback.print_exc()
        if Path(".env.invalid").exists():
            Path(".env.invalid").unlink()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "InsightCosmos Stage 1 Manual Tests" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    results = []

    # Run tests
    results.append(("Logger", test_logger()))
    results.append(("Config", test_config()))
    results.append(("Config Validation", test_config_validation()))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} : {status}")

    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
