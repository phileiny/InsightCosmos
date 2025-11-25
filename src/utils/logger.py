"""
Logger System for InsightCosmos

This module provides centralized logging functionality for the InsightCosmos project.
Logs are written to both console and file with proper formatting.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """
    日志管理器，提供统一的日志记录功能

    Features:
        - 自动创建日志目录
        - 同时输出到文件和控制台
        - 支持不同日志级别
        - 日志文件按日期命名
        - 避免重复创建 logger

    Usage:
        >>> logger = Logger.get_logger("scout_agent")
        >>> logger.info("Starting to fetch RSS feeds")
        >>> logger.error("Failed to connect", exc_info=True)
    """

    _loggers: dict[str, logging.Logger] = {}  # 缓存已创建的 logger

    @staticmethod
    def get_logger(
        name: str,
        log_level: str = "INFO",
        log_dir: str = "logs"
    ) -> logging.Logger:
        """
        获取或创建一个 logger 实例

        Args:
            name: Logger 名称（通常是模块名或 Agent 名）
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件存储目录

        Returns:
            logging.Logger: 配置好的 logger 实例

        Example:
            >>> logger = Logger.get_logger("scout_agent")
            >>> logger.info("Task started")
            INFO - scout_agent - Task started
        """
        # 避免重复创建
        if name in Logger._loggers:
            return Logger._loggers[name]

        # 创建 logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # 清除已有 handlers（避免重复）
        logger.handlers.clear()

        # 防止日志传播到根 logger
        logger.propagate = False

        # 添加文件处理器
        try:
            Logger.setup_file_handler(logger, log_dir, name)
        except Exception as e:
            # 如果文件处理器创建失败，只使用控制台
            print(f"Warning: Failed to create file handler: {e}")

        # 添加控制台处理器
        Logger.setup_console_handler(logger)

        # 缓存
        Logger._loggers[name] = logger

        return logger

    @staticmethod
    def setup_file_handler(
        logger: logging.Logger,
        log_dir: str,
        name: str
    ) -> None:
        """
        为 logger 添加文件处理器

        日志文件命名格式: {log_dir}/{name}_{YYYYMMDD}.log

        Args:
            logger: Logger 实例
            log_dir: 日志目录
            name: Logger 名称

        Raises:
            Exception: 如果无法创建日志目录或文件
        """
        # 创建日志目录
        log_path = Path(log_dir)
        try:
            log_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create log directory: {log_path}. Error: {e}")

        # 日志文件名：{name}_{YYYYMMDD}.log
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_path / f"{name}_{today}.log"

        try:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)

            # 格式化（文件包含完整信息）
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

        except Exception as e:
            raise Exception(f"Failed to create file handler for {log_file}. Error: {e}")

    @staticmethod
    def setup_console_handler(logger: logging.Logger) -> None:
        """
        为 logger 添加控制台处理器

        Args:
            logger: Logger 实例
        """
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化（控制台简化版）
        formatter = logging.Formatter(
            "%(levelname)s - %(name)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    @staticmethod
    def set_level(logger: logging.Logger, level: str) -> None:
        """
        动态设置 logger 的日志级别

        Args:
            logger: Logger 实例
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Example:
            >>> logger = Logger.get_logger("test")
            >>> Logger.set_level(logger, "DEBUG")
        """
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    @staticmethod
    def clear_cache() -> None:
        """
        清除 logger 缓存

        主要用于测试场景，避免 logger 实例复用

        Example:
            >>> Logger.clear_cache()
        """
        Logger._loggers.clear()


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    便捷函數：創建 logger 實例

    這是 Logger.get_logger() 的別名，提供更簡潔的調用方式。

    Args:
        name: Logger 名稱
        log_level: 日誌級別

    Returns:
        logging.Logger: 配置好的 logger 實例

    Example:
        >>> from src.utils.logger import setup_logger
        >>> logger = setup_logger("my_module")
        >>> logger.info("Hello!")
    """
    return Logger.get_logger(name, log_level)
