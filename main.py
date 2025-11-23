"""
InsightCosmos - Personal AI Intelligence Universe
Main entry point

This is the main entry point for the InsightCosmos system.
It initializes the configuration, logger, and will orchestrate the multi-agent system.
"""

from src.utils.config import Config
from src.utils.logger import Logger


def main() -> int:
    """
    InsightCosmos 主程序入口

    Returns:
        int: 退出码 (0 表示成功，非 0 表示失败)

    Example:
        >>> python main.py
    """
    # 初始化 logger
    logger = Logger.get_logger("insightcosmos")
    logger.info("=" * 60)
    logger.info("InsightCosmos - Personal AI Intelligence Universe")
    logger.info("=" * 60)

    try:
        # 加载配置
        logger.info("Loading configuration...")
        config = Config.load()
        logger.info("✓ Configuration loaded successfully")
        logger.info(f"  User: {config.user_name}")
        logger.info(f"  Interests: {config.user_interests}")
        logger.info(f"  Database: {config.database_path}")
        logger.info(f"  Log Level: {config.log_level}")

        # TODO: Stage 2+ - 初始化数据库
        logger.info("")
        logger.info("Database initialization will be implemented in Stage 2")

        # TODO: Stage 3-7 - 初始化 Agents
        logger.info("Agent initialization will be implemented in Stage 3-7")

        # TODO: Stage 8-9 - 启动 Orchestrator
        logger.info("Orchestrator will be implemented in Stage 8-9")

        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ System initialized successfully")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Status: Foundation complete - Ready for Stage 2")
        logger.info("Next: Implement Memory Layer (Database + Schema)")

        return 0

    except FileNotFoundError as e:
        logger.error(f"✗ Configuration file not found: {e}")
        logger.error("  Please copy .env.example to .env and fill in your credentials")
        return 1

    except ValueError as e:
        logger.error(f"✗ Configuration error: {e}")
        logger.error("  Please check your .env file")
        return 1

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
