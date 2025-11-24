#!/usr/bin/env python3
"""Scout Agent Debug Test Script"""

import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents.scout_agent import ScoutAgentRunner
from src.utils.logger import Logger

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logger = Logger.get_logger("TestScout")

    print("=" * 80)
    print("Scout Agent Debug Test")
    print("=" * 80)
    print()

    try:
        logger.info("Creating Scout Agent Runner...")
        runner = ScoutAgentRunner()
        logger.info("Scout Agent Runner created")
        print()

        logger.info("Starting article collection...")
        print()

        result = runner.collect_articles()

        print()
        print("=" * 80)
        print("Test Results")
        print("=" * 80)
        print("Status:", result['status'])
        print("Total Articles:", result['total_count'])
        print("Sources:", result.get('sources', {}))
        print()

        if result['articles']:
            print("Sample Articles:")
            for idx, article in enumerate(result['articles'][:3], 1):
                title = article.get('title', 'N/A')[:60]
                print(f"  {idx}. {title}...")
                print(f"     URL: {article.get('url', 'N/A')}")
                print(f"     Source: {article.get('source', 'N/A')}")
                print()

        print("=" * 80)

        if result['status'] == 'success':
            logger.info("Test completed successfully")
            return 0
        else:
            logger.error("Test failed")
            return 1

    except KeyboardInterrupt:
        print()
        logger.warning("Test interrupted by user")
        return 130

    except Exception as e:
        print()
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
