"""
Unit tests for utilities module (Config and Logger)

Tests cover:
- Config loading and validation
- Logger creation and functionality
- Error handling scenarios
"""

import pytest
import os
import tempfile
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import Logger


class TestConfig:
    """Test cases for Config class"""

    def test_config_load_success(self, tmp_path):
        """TC-1-01: Config 加载成功 - 有效的 .env"""
        # 创建临时 .env 文件
        env_file = tmp_path / ".env.test"
        env_content = """
GOOGLE_API_KEY=test_google_key
GOOGLE_SEARCH_API_KEY=test_search_key
GOOGLE_SEARCH_ENGINE_ID=test_engine_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
DATABASE_PATH=data/test.db
USER_NAME=TestUser
USER_INTERESTS=AI,Robotics
LOG_LEVEL=INFO
"""
        env_file.write_text(env_content.strip())

        # 加载配置
        config = Config.load(str(env_file))

        # 验证
        assert config.google_api_key == "test_google_key"
        assert config.google_search_api_key == "test_search_key"
        assert config.google_search_engine_id == "test_engine_id"
        assert config.email_account == "test@example.com"
        assert config.email_password == "test_password"
        assert config.user_name == "TestUser"
        assert config.user_interests == "AI,Robotics"

    def test_config_missing_required_field(self, tmp_path):
        """TC-1-02: Config 缺失必需字段 - 缺失 GOOGLE_API_KEY"""
        # 创建缺失必需字段的 .env 文件
        env_file = tmp_path / ".env.test"
        env_content = """
GOOGLE_SEARCH_API_KEY=test_search_key
GOOGLE_SEARCH_ENGINE_ID=test_engine_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
"""
        env_file.write_text(env_content.strip())

        # 验证抛出 ValueError
        with pytest.raises(ValueError, match="Missing or invalid config.*GOOGLE_API_KEY"):
            Config.load(str(env_file))

    def test_config_file_not_found(self):
        """TC-1-03: Config 文件不存在"""
        # 验证抛出 FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            Config.load("/nonexistent/path/.env")

    def test_config_invalid_placeholder_values(self, tmp_path):
        """TC-1-07: Config 包含占位符值 - your_*_here"""
        # 创建包含占位符的 .env 文件
        env_file = tmp_path / ".env.test"
        env_content = """
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_SEARCH_API_KEY=test_search_key
GOOGLE_SEARCH_ENGINE_ID=test_engine_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
"""
        env_file.write_text(env_content.strip())

        # 验证抛出 ValueError
        with pytest.raises(ValueError, match="Missing or invalid config.*GOOGLE_API_KEY"):
            Config.load(str(env_file))

    def test_config_get_interests_list(self, tmp_path):
        """TC-1-08: Config 获取兴趣列表"""
        # 创建临时 .env 文件
        env_file = tmp_path / ".env.test"
        env_content = """
GOOGLE_API_KEY=test_key
GOOGLE_SEARCH_API_KEY=test_key
GOOGLE_SEARCH_ENGINE_ID=test_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
USER_INTERESTS=AI, Robotics, Machine Learning
"""
        env_file.write_text(env_content.strip())

        config = Config.load(str(env_file))
        interests = config.get_interests_list()

        assert interests == ["AI", "Robotics", "Machine Learning"]
        assert len(interests) == 3

    def test_config_invalid_log_level(self, tmp_path):
        """TC-1-09: Config 无效的日志级别"""
        # 创建包含无效日志级别的 .env 文件
        env_file = tmp_path / ".env.test"
        env_content = """
GOOGLE_API_KEY=test_key
GOOGLE_SEARCH_API_KEY=test_key
GOOGLE_SEARCH_ENGINE_ID=test_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
LOG_LEVEL=INVALID_LEVEL
"""
        env_file.write_text(env_content.strip())

        # 验证抛出 ValueError
        with pytest.raises(ValueError, match="Invalid log level"):
            Config.load(str(env_file))

    def test_config_repr_hides_sensitive_info(self, tmp_path):
        """TC-1-10: Config __repr__ 隐藏敏感信息"""
        env_file = tmp_path / ".env.test"
        env_content = """
GOOGLE_API_KEY=super_secret_key
GOOGLE_SEARCH_API_KEY=test_key
GOOGLE_SEARCH_ENGINE_ID=test_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=secret_password
USER_NAME=TestUser
"""
        env_file.write_text(env_content.strip())

        config = Config.load(str(env_file))
        repr_str = repr(config)

        # 验证敏感信息不在字符串表示中
        assert "super_secret_key" not in repr_str
        assert "secret_password" not in repr_str
        assert "sensitive fields hidden" in repr_str
        assert "TestUser" in repr_str  # 非敏感信息可见


class TestLogger:
    """Test cases for Logger class"""

    def setup_method(self):
        """每个测试前清除 logger 缓存"""
        Logger.clear_cache()

    def test_logger_creation_success(self):
        """TC-1-04: Logger 创建成功"""
        logger = Logger.get_logger("test_logger")

        assert logger is not None
        assert logger.name == "test_logger"
        assert len(logger.handlers) >= 1  # 至少有控制台处理器

    def test_logger_write_to_file(self, tmp_path):
        """TC-1-05: Logger 写入文件"""
        log_dir = tmp_path / "logs"
        logger = Logger.get_logger("test_file_logger", log_dir=str(log_dir))

        # 写入日志
        test_message = "Test log message"
        logger.info(test_message)

        # 验证日志文件存在并包含消息
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"test_file_logger_{today}.log"

        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert test_message in log_content

    def test_logger_console_output(self, capsys):
        """TC-1-06: Logger 输出到控制台"""
        logger = Logger.get_logger("test_console_logger")

        # 写入日志
        test_message = "Console test message"
        logger.info(test_message)

        # 验证控制台输出
        captured = capsys.readouterr()
        assert test_message in captured.err or test_message in captured.out

    def test_logger_different_levels(self, tmp_path):
        """TC-1-11: Logger 不同日志级别"""
        log_dir = tmp_path / "logs"
        logger = Logger.get_logger("test_levels", log_level="DEBUG", log_dir=str(log_dir))

        # 写入不同级别的日志
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # 验证日志文件包含所有级别
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"test_levels_{today}.log"

        log_content = log_file.read_text(encoding="utf-8")
        assert "Debug message" in log_content
        assert "Info message" in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content

    def test_logger_caching(self):
        """TC-1-12: Logger 缓存机制"""
        logger1 = Logger.get_logger("cached_logger")
        logger2 = Logger.get_logger("cached_logger")

        # 验证返回相同实例
        assert logger1 is logger2

    def test_logger_set_level(self):
        """TC-1-13: Logger 动态设置日志级别"""
        logger = Logger.get_logger("level_test", log_level="INFO")

        # 修改日志级别
        Logger.set_level(logger, "DEBUG")

        # 验证级别已更改
        import logging
        assert logger.level == logging.DEBUG


class TestIntegration:
    """Integration tests for Config and Logger working together"""

    def test_config_and_logger_integration(self, tmp_path):
        """TC-1-14: Config 和 Logger 集成测试"""
        # 创建配置
        env_file = tmp_path / ".env.test"
        env_content = """
GOOGLE_API_KEY=test_key
GOOGLE_SEARCH_API_KEY=test_key
GOOGLE_SEARCH_ENGINE_ID=test_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
LOG_LEVEL=DEBUG
"""
        env_file.write_text(env_content.strip())

        # 加载配置
        config = Config.load(str(env_file))

        # 创建 logger 使用配置的日志级别
        log_dir = tmp_path / "logs"
        logger = Logger.get_logger("integration_test", log_level=config.log_level, log_dir=str(log_dir))

        # 验证日志级别
        import logging
        assert logger.level == logging.DEBUG

        # 写入日志
        logger.info(f"User: {config.user_name}")
        logger.info(f"Interests: {config.user_interests}")

        # 验证日志文件
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"integration_test_{today}.log"

        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert config.user_name in log_content
