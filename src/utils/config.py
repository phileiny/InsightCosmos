"""
Configuration Manager for InsightCosmos

This module provides centralized configuration management for the InsightCosmos project.
All environment variables are loaded from .env file and validated.
"""

from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path


@dataclass
class Config:
    """
    项目配置类，从 .env 加载所有配置项

    Attributes:
        google_api_key: Google Gemini API Key
        google_search_api_key: Google Custom Search API Key
        google_search_engine_id: Google Custom Search Engine ID
        email_account: Email 发送账号
        email_password: Email 发送密码
        email_smtp_host: SMTP 服务器地址
        email_smtp_port: SMTP 端口
        database_path: SQLite 数据库路径
        user_name: 用户名（个性化用）
        user_interests: 用户兴趣（逗号分隔）
        log_level: 日志级别

    Usage:
        >>> config = Config.load()
        >>> print(config.google_api_key)
    """

    # Google Gemini API (统一 API Key)
    # 用于 LLM 推理和 Google Search Grounding
    google_api_key: str

    # Email
    email_account: str
    email_password: str
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587

    # Database
    database_path: str = "data/insights.db"

    # User Profile
    user_name: str = "Ray"
    user_interests: str = "AI,Robotics,Multi-Agent Systems"

    # Logging
    log_level: str = "INFO"

    @classmethod
    def load(cls, env_path: str = ".env") -> "Config":
        """
        从 .env 文件加载配置

        Args:
            env_path: .env 文件路径，默认为项目根目录的 .env

        Returns:
            Config: 配置对象

        Raises:
            FileNotFoundError: 如果 .env 文件不存在
            ValueError: 如果必需的配置项缺失或无效

        Example:
            >>> config = Config.load()
            >>> config = Config.load(".env.production")
        """
        # 1. 检查文件是否存在
        env_file = Path(env_path)
        if not env_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {env_path}. "
                f"Please copy .env.example to .env and fill in your credentials."
            )

        # 2. 加载环境变量
        load_dotenv(env_path)

        # 3. 读取并创建 Config 对象
        try:
            config = cls(
                google_api_key=os.getenv("GOOGLE_API_KEY", ""),
                email_account=os.getenv("EMAIL_ACCOUNT", ""),
                email_password=os.getenv("EMAIL_PASSWORD", ""),
                email_smtp_host=os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
                email_smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
                database_path=os.getenv("DATABASE_PATH", "data/insights.db"),
                user_name=os.getenv("USER_NAME", "Ray"),
                user_interests=os.getenv("USER_INTERESTS", "AI,Robotics,Multi-Agent Systems"),
                log_level=os.getenv("LOG_LEVEL", "INFO")
            )

            # 4. 验证配置
            config.validate()

            return config

        except ValueError as e:
            raise ValueError(f"Failed to load configuration: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error loading configuration: {e}")

    def validate(self) -> bool:
        """
        验证配置的完整性和有效性

        Returns:
            bool: 配置是否有效

        Raises:
            ValueError: 配置项缺失或无效时抛出异常

        Example:
            >>> config.validate()
            True
        """
        # 验证必需字段
        required_fields = [
            ("google_api_key", "GOOGLE_API_KEY"),
            ("email_account", "EMAIL_ACCOUNT"),
            ("email_password", "EMAIL_PASSWORD")
        ]

        for field_name, env_name in required_fields:
            value = getattr(self, field_name)
            if not value or value.strip() == "" or "your_" in value.lower():
                raise ValueError(
                    f"Missing or invalid config: {env_name}. "
                    f"Please set it in your .env file."
                )

        # 验证端口号
        if not isinstance(self.email_smtp_port, int) or self.email_smtp_port <= 0:
            raise ValueError(
                f"Invalid SMTP port: {self.email_smtp_port}. "
                f"Must be a positive integer."
            )

        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log level: {self.log_level}. "
                f"Must be one of {valid_log_levels}."
            )

        # 验证数据库路径
        db_path = Path(self.database_path)
        db_dir = db_path.parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(
                    f"Cannot create database directory: {db_dir}. Error: {e}"
                )

        return True

    def get_interests_list(self) -> list[str]:
        """
        获取用户兴趣列表

        Returns:
            list[str]: 兴趣列表

        Example:
            >>> config.get_interests_list()
            ['AI', 'Robotics', 'Multi-Agent Systems']
        """
        return [interest.strip() for interest in self.user_interests.split(",")]

    def __repr__(self) -> str:
        """
        安全的字符串表示（隐藏敏感信息）

        Returns:
            str: 配置的字符串表示
        """
        return (
            f"Config("
            f"user_name='{self.user_name}', "
            f"interests={self.get_interests_list()}, "
            f"database_path='{self.database_path}', "
            f"log_level='{self.log_level}', "
            f"[sensitive fields hidden]"
            f")"
        )
