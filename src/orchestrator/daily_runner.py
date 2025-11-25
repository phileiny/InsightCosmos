"""
Daily Pipeline Orchestrator

負責串聯 Scout → Analyst → Curator 完整日報流程。

主要功能：
1. Phase 1: Scout Agent 收集文章
2. Phase 2: Analyst Agent 分析文章
3. Phase 3: Curator Agent 生成報告並發送

使用方式：
    python -m src.orchestrator.daily_runner --dry-run
    python -m src.orchestrator.daily_runner
"""

import sys
import argparse
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 確保可以導入專案模組
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import Logger
from src.memory.database import Database
from src.memory.article_store import ArticleStore
from src.memory.embedding_store import EmbeddingStore


class DailyPipelineOrchestrator:
    """
    日報流程編排器

    負責串聯 Scout → Analyst → Curator 完整流程，
    提供錯誤處理、重試、日誌等功能。

    Attributes:
        config (Config): 配置對象
        db (Database): 資料庫連接
        article_store (ArticleStore): 文章存儲
        embedding_store (EmbeddingStore): 向量存儲
        logger (Logger): 日誌記錄器
        stats (dict): 執行統計
    """

    def __init__(self, config: Config):
        """
        初始化編排器

        Args:
            config: 配置對象
        """
        self.config = config
        self.db = Database.from_config(config)
        self.db.init_db()

        self.article_store = ArticleStore(self.db)
        self.embedding_store = EmbeddingStore(self.db)

        self.logger = Logger.get_logger("DailyPipeline")

        # 執行統計
        self.stats = {
            "start_time": None,
            "end_time": None,
            "phase1_collected": 0,
            "phase1_stored": 0,
            "phase2_analyzed": 0,
            "phase3_sent": False,
            "errors": []
        }

    def run(self, dry_run: bool = False) -> Dict:
        """
        執行完整的日報流程

        流程：
        1. Phase 1: Scout Agent 收集文章
        2. Phase 2: Analyst Agent 分析文章
        3. Phase 3: Curator Agent 生成報告並發送

        Args:
            dry_run: 是否為測試模式（不發送郵件）

        Returns:
            dict: {
                "success": bool,
                "stats": {
                    "start_time": str,
                    "end_time": str,
                    "duration_seconds": float,
                    "phase1_collected": int,
                    "phase1_stored": int,
                    "phase2_analyzed": int,
                    "phase3_sent": bool
                },
                "errors": list
            }
        """
        self.stats["start_time"] = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("Daily Pipeline Started")
        self.logger.info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
        self.logger.info("=" * 60)

        try:
            # Phase 1: Scout
            self.logger.info("\n[Phase 1/3] Starting Scout Agent...")
            collected, stored = self._run_phase1_scout()
            self.stats["phase1_collected"] = collected
            self.stats["phase1_stored"] = stored
            self.logger.info(f"✓ Phase 1 Complete: Collected {collected} articles, Stored {stored} new articles")

            if stored == 0:
                self.logger.warning("No new articles stored. Aborting pipeline.")
                return self.get_summary()

            # Phase 2: Analyst
            self.logger.info("\n[Phase 2/3] Starting Analyst Agent...")
            analyzed_count = self._run_phase2_analyst()
            self.stats["phase2_analyzed"] = analyzed_count
            self.logger.info(f"✓ Phase 2 Complete: Analyzed {analyzed_count} articles")

            if analyzed_count == 0:
                self.logger.warning("No articles analyzed. Aborting pipeline.")
                return self.get_summary()

            # Phase 3: Curator
            self.logger.info("\n[Phase 3/3] Starting Curator Agent...")
            sent = self._run_phase3_curator(dry_run)
            self.stats["phase3_sent"] = sent

            if sent:
                self.logger.info("✓ Phase 3 Complete: Email sent successfully")
            else:
                self.logger.warning("✗ Phase 3 Failed: Email not sent")

            self.stats["end_time"] = datetime.now()
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Daily Pipeline Completed")
            self._print_summary()
            self.logger.info("=" * 60)

            return self.get_summary()

        except Exception as e:
            self.logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
            self._handle_error("pipeline", e)
            self.stats["end_time"] = datetime.now()
            return self.get_summary()

    def _run_phase1_scout(self) -> tuple[int, int]:
        """
        Phase 1: 使用 Scout Agent 收集文章

        Returns:
            tuple[int, int]: (收集的文章數, 新存儲的文章數)

        Raises:
            Exception: 如果收集過程失敗
        """
        from src.agents.scout_agent import ScoutAgentRunner, create_scout_agent

        try:
            # 調用 Scout Agent（傳遞 user_interests 配置）
            self.logger.info("  Calling Scout Agent...")
            self.logger.info(f"  User interests: {self.config.user_interests}")

            # 創建帶有 user_interests 的 Scout Agent
            agent = create_scout_agent(user_interests=self.config.user_interests)
            runner = ScoutAgentRunner(agent=agent)
            result = runner.collect_articles()

            if result["status"] != "success":
                raise Exception(f"Scout failed: {result.get('error_message', 'Unknown error')}")

            articles = result["articles"]
            self.logger.info(f"  Scout collected {len(articles)} articles")

            # 存儲到 ArticleStore（去重）
            stored_count = 0
            for article in articles:
                try:
                    # 檢查是否已存在
                    existing = self.article_store.get_by_url(article["url"])
                    if existing:
                        self.logger.debug(f"  Article already exists: {article['url']}")
                        continue

                    # 準備文章數據（status='collected' 表示待分析）
                    # 處理 published_at 時間格式
                    from dateutil import parser as date_parser
                    published_at = article.get("published_at")
                    if published_at and isinstance(published_at, str):
                        try:
                            published_at = date_parser.parse(published_at)
                        except:
                            published_at = None

                    article_data = {
                        "url": article["url"],
                        "title": article["title"],
                        "summary": article.get("summary", ""),
                        "source": article.get("source", "rss"),
                        "source_name": article.get("source_name", "Unknown"),
                        "published_at": published_at,
                        "status": "collected"
                    }

                    # 存儲新文章
                    article_id = self.article_store.store_article(article_data)
                    if article_id:
                        stored_count += 1
                        self.logger.debug(f"  Stored article {article_id}: {article['title'][:50]}")

                except Exception as e:
                    self.logger.warning(f"  Failed to store article {article.get('url', 'unknown')}: {e}")
                    continue

            return len(articles), stored_count

        except Exception as e:
            self.logger.error(f"Phase 1 (Scout) failed: {e}", exc_info=True)
            self._handle_error("phase1_scout", e)
            raise

    def _run_phase2_analyst(self) -> int:
        """
        Phase 2: 使用 Analyst Agent 分析文章

        Returns:
            int: 成功分析的文章數量
        """
        from src.agents.analyst_agent import AnalystAgentRunner, create_analyst_agent
        from src.tools.content_extractor import extract_content

        # 創建 Analyst Agent
        agent = create_analyst_agent(
            user_name=self.config.user_name,
            user_interests=self.config.user_interests
        )

        # 創建 Runner
        runner = AnalystAgentRunner(
            agent=agent,
            article_store=self.article_store,
            embedding_store=self.embedding_store,
            logger=self.logger,
            config=self.config
        )
        analyzed_count = 0

        # 獲取 'collected' 狀態的文章
        pending_articles = self.article_store.get_by_status("collected")
        self.logger.info(f"  Found {len(pending_articles)} pending articles to analyze")

        if len(pending_articles) == 0:
            self.logger.info("  No pending articles, checking if we should re-analyze recent articles...")
            # 可選：分析最近未分析的文章
            return 0

        for idx, article_dict in enumerate(pending_articles, 1):
            article_id = article_dict["id"]
            url = article_dict["url"]
            title = article_dict["title"]

            try:
                self.logger.info(f"  [{idx}/{len(pending_articles)}] Processing: {title[:60]}...")

                # 1. 提取完整內容
                self.logger.info(f"    → Extracting content from {url}")
                content_result = extract_content(url)

                if content_result["status"] != "success":
                    self.logger.warning(f"    ✗ Content extraction failed: {content_result.get('error_message', 'Unknown error')}")
                    # 標記為失敗，但繼續處理其他文章
                    self.article_store.update_status(article_id, "extraction_failed")
                    continue

                full_content = content_result["content"]
                self.logger.info(f"    ✓ Content extracted ({len(full_content)} chars)")

                # 更新文章內容到數據庫
                self.article_store.update(article_id, content=full_content)

                # 2. 分析文章
                self.logger.info(f"    → Analyzing article with LLM...")
                import asyncio
                analysis_result = asyncio.run(runner.analyze_article(article_id=article_id))

                if analysis_result["status"] == "success":
                    analyzed_count += 1
                    priority = analysis_result.get("priority_score", 0.0)
                    self.logger.info(f"    ✓ Analysis complete (priority: {priority:.2f})")
                else:
                    self.logger.warning(f"    ✗ Analysis failed: {analysis_result.get('error_message', 'Unknown error')}")

            except Exception as e:
                self.logger.error(f"  Error analyzing article {article_id}: {e}", exc_info=True)
                self._handle_error(f"phase2_analyst_article_{article_id}", e)
                continue

        return analyzed_count

    def _run_phase3_curator(self, dry_run: bool) -> bool:
        """
        Phase 3: 使用 Curator Agent 生成報告並發送

        Args:
            dry_run: 是否為測試模式（不發送郵件）

        Returns:
            bool: 是否成功發送
        """
        from src.agents.curator_daily import generate_daily_digest

        try:
            self.logger.info("  Calling Curator Agent...")

            # Dry-run mode: Skip email sending
            if dry_run:
                self.logger.info("  DRY RUN: Skipping Curator Agent (email generation)")
                self.logger.info("  → Would generate daily digest and send to: {}".format(
                    self.config.email_account
                ))
                return True

            # Normal mode: Generate and send digest
            result = generate_daily_digest(
                config=self.config,
                recipient_email=self.config.email_account,
                max_articles=10
            )

            if result["status"] == "success":
                self.logger.info(f"  ✓ Email sent to: {result.get('recipients', [])}")
                return True
            else:
                self.logger.error(f"  ✗ Curator failed: {result.get('error_message', 'Unknown error')}")
                return False

        except Exception as e:
            self.logger.error(f"Phase 3 (Curator) failed: {e}", exc_info=True)
            self._handle_error("phase3_curator", e)
            return False

    def _handle_error(self, phase: str, error: Exception):
        """
        記錄錯誤信息

        Args:
            phase: 發生錯誤的階段名稱
            error: 異常對象
        """
        error_info = {
            "phase": phase,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        self.stats["errors"].append(error_info)
        self.logger.error(f"Error in {phase}: {error}")

    def _print_summary(self):
        """列印執行摘要到日誌"""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        self.logger.info("Pipeline Summary:")
        if duration:
            self.logger.info(f"  Duration: {duration:.1f} seconds")
        self.logger.info(f"  Articles Collected: {self.stats['phase1_collected']}")
        self.logger.info(f"  Articles Stored: {self.stats['phase1_stored']}")
        self.logger.info(f"  Articles Analyzed: {self.stats['phase2_analyzed']}")
        self.logger.info(f"  Email Sent: {self.stats['phase3_sent']}")
        self.logger.info(f"  Errors: {len(self.stats['errors'])}")

        if self.stats["errors"]:
            self.logger.info("  Error Details:")
            for error in self.stats["errors"]:
                self.logger.info(f"    - {error['phase']}: {error['error_message']}")

    def get_summary(self) -> Dict:
        """
        獲取執行摘要

        Returns:
            dict: 執行結果摘要
        """
        success = (
            self.stats["phase1_stored"] > 0 and
            self.stats["phase2_analyzed"] > 0 and
            self.stats["phase3_sent"] and
            len(self.stats["errors"]) == 0
        )

        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        return {
            "success": success,
            "stats": {
                "start_time": self.stats["start_time"].isoformat() if self.stats["start_time"] else None,
                "end_time": self.stats["end_time"].isoformat() if self.stats["end_time"] else None,
                "duration_seconds": duration,
                "phase1_collected": self.stats["phase1_collected"],
                "phase1_stored": self.stats["phase1_stored"],
                "phase2_analyzed": self.stats["phase2_analyzed"],
                "phase3_sent": self.stats["phase3_sent"]
            },
            "errors": self.stats["errors"]
        }


def run_daily_pipeline(dry_run: bool = False, verbose: bool = False) -> Dict:
    """
    便捷函數：執行日報流程

    Args:
        dry_run: 是否為測試模式（不發送郵件）
        verbose: 是否啟用詳細日誌

    Returns:
        dict: 執行結果摘要

    Example:
        >>> result = run_daily_pipeline(dry_run=True)
        >>> print(f"Success: {result['success']}")
        >>> print(f"Analyzed: {result['stats']['phase2_analyzed']}")
    """
    # 載入配置
    config = Config.from_env()

    # 設置日誌級別
    if verbose:
        import logging
        logging.getLogger("DailyPipeline").setLevel(logging.DEBUG)

    # 創建並執行編排器
    orchestrator = DailyPipelineOrchestrator(config)
    result = orchestrator.run(dry_run=dry_run)

    return result


def main():
    """命令列入口"""
    parser = argparse.ArgumentParser(
        description="InsightCosmos Daily Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (不發送郵件)
  python -m src.orchestrator.daily_runner --dry-run

  # 生產模式
  python -m src.orchestrator.daily_runner

  # 詳細日誌
  python -m src.orchestrator.daily_runner --verbose

  # Dry run + 詳細日誌
  python -m src.orchestrator.daily_runner --dry-run --verbose
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="測試模式：執行流程但不發送郵件"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="啟用詳細日誌（DEBUG 級別）"
    )

    args = parser.parse_args()

    # 執行流程
    try:
        result = run_daily_pipeline(dry_run=args.dry_run, verbose=args.verbose)

        # 列印結果
        print("\n" + "=" * 60)
        if result["success"]:
            print("✓ Daily Pipeline Completed Successfully")
        else:
            print("✗ Daily Pipeline Completed with Errors")

        print("\nStats:")
        print(f"  Duration: {result['stats']['duration_seconds']:.1f}s")
        print(f"  Collected: {result['stats']['phase1_collected']}")
        print(f"  Stored: {result['stats']['phase1_stored']}")
        print(f"  Analyzed: {result['stats']['phase2_analyzed']}")
        print(f"  Email Sent: {result['stats']['phase3_sent']}")

        if result["errors"]:
            print(f"\nErrors: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"  - {error['phase']}: {error['error_message']}")

        print("=" * 60)

        # 退出碼
        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
