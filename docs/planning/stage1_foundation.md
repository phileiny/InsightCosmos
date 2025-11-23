# Stage 1: Foundation (基础设施层)

> **阶段编号**: Stage 1
> **阶段目标**: 建立项目基础框架，确保开发环境就绪
> **前置依赖**: 无
> **预计时间**: 0.5 天 (4 小时)
> **状态**: Planning

---

## 🎯 阶段目标

### 核心目标

建立 InsightCosmos 项目的基础设施层，包括：
1. 创建标准化的项目目录结构
2. 建立环境配置管理系统
3. 定义项目依赖并创建 requirements.txt
4. 实现通用工具类：配置管理器和日志系统
5. 创建项目入口文件框架

### 为什么需要这个阶段？

基础设施层是整个项目的"地基"，确保：
- 所有后续开发有统一的项目结构
- 环境配置安全且易于管理（.env）
- 依赖明确，环境可复现
- 日志系统从一开始就建立，便于调试
- 配置读取统一，避免硬编码

---

## 📥 输入 (Input)

### 来自上一阶段的产出

- 无（这是第一个 Stage）

### 外部依赖

- **开发环境**:
  - Python 3.10 或更高版本
  - pip 包管理器
  - Git（版本控制）

- **必需的 API Keys**:
  - Google Gemini API Key
  - Google Custom Search API Key + Search Engine ID
  - Email 账号密码（SMTP）

- **开发工具**:
  - 代码编辑器（VS Code / PyCharm）
  - 终端/命令行工具

---

## 📤 输出 (Output)

### 代码产出

```
/InsightCosmos
├─ src/
│   └─ utils/
│       ├─ __init__.py
│       ├─ config.py          # 配置管理器
│       └─ logger.py          # 日志系统
│
├─ data/                      # 数据存储目录（占位）
│   └─ .gitkeep
│
├─ logs/                      # 日志文件目录
│   └─ .gitkeep
│
├─ .env                       # 环境变量（不提交到 Git）
├─ .env.example              # 环境变量模板
├─ .gitignore                # Git 忽略配置
├─ requirements.txt          # Python 依赖
└─ main.py                   # 项目入口文件（占位）
```

### 文档产出

- `docs/implementation/stage1_notes.md` - Stage 1 实作笔记
- `docs/validation/stage1_test_report.md` - Stage 1 测试报告

### 功能产出

- [x] 项目目录结构建立
- [x] 环境配置系统可用
- [x] 日志系统可用
- [x] 依赖清单完整
- [x] 入口文件就绪

---

## 🏗️ 技术设计

### 架构图

```
┌─────────────────────────────────────┐
│         Application Layer           │
│       (main.py + agents)            │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│         Utils Layer                 │
│  ┌──────────┐      ┌──────────┐    │
│  │ Config   │      │ Logger   │    │
│  │ Manager  │      │ System   │    │
│  └──────────┘      └──────────┘    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│      Environment & Dependencies     │
│      (.env + requirements.txt)      │
└─────────────────────────────────────┘
```

---

### 核心组件

#### 组件 1: Config Manager (配置管理器)

**职责**: 统一管理所有环境变量和配置项

**文件**: `src/utils/config.py`

**接口设计**:

```python
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

@dataclass
class Config:
    """
    项目配置类，从 .env 加载所有配置项

    Attributes:
        google_api_key: Google Gemini API Key
        search_api_key: Google Custom Search API Key
        search_engine_id: Google Custom Search Engine ID
        email_account: Email 发送账号
        email_password: Email 发送密码
        email_smtp_host: SMTP 服务器地址
        email_smtp_port: SMTP 端口
        database_path: SQLite 数据库路径
        user_name: 用户名（个性化用）
        user_interests: 用户兴趣（逗号分隔）

    Usage:
        >>> config = Config.load()
        >>> print(config.google_api_key)
    """

    # LLM API
    google_api_key: str

    # Search API
    search_api_key: str
    search_engine_id: str

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

    @classmethod
    def load(cls, env_path: str = ".env") -> "Config":
        """
        从 .env 文件加载配置

        Args:
            env_path: .env 文件路径，默认为项目根目录的 .env

        Returns:
            Config: 配置对象

        Raises:
            ValueError: 如果必需的配置项缺失
            FileNotFoundError: 如果 .env 文件不存在
        """
        pass

    def validate(self) -> bool:
        """
        验证配置的完整性和有效性

        Returns:
            bool: 配置是否有效

        Raises:
            ValueError: 配置项缺失或无效时抛出异常
        """
        pass
```

**输出格式**:

加载成功：
```python
Config(
    google_api_key="AIza...",
    search_api_key="AIza...",
    ...
)
```

加载失败：
```python
raise ValueError("Missing required config: GOOGLE_API_KEY")
```

**错误处理**:

| 错误类型 | 处理方式 | 返回信息 |
|---------|---------|---------|
| .env 文件不存在 | 抛出 FileNotFoundError | "Configuration file not found: .env. Please copy .env.example to .env and fill in your credentials." |
| 必需字段缺失 | 抛出 ValueError | "Missing required config: {FIELD_NAME}" |
| 字段格式错误 | 抛出 ValueError | "Invalid config format for {FIELD_NAME}: {reason}" |

---

#### 组件 2: Logger System (日志系统)

**职责**: 提供统一的日志记录功能

**文件**: `src/utils/logger.py`

**接口设计**:

```python
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

    Usage:
        >>> logger = Logger.get_logger("scout_agent")
        >>> logger.info("Starting to fetch RSS feeds")
        >>> logger.error("Failed to connect", exc_info=True)
    """

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
            2025-11-19 10:30:45 - scout_agent - INFO - Task started
        """
        pass

    @staticmethod
    def setup_file_handler(
        logger: logging.Logger,
        log_dir: str,
        name: str
    ) -> None:
        """
        为 logger 添加文件处理器

        日志文件命名格式: {log_dir}/{name}_{YYYYMMDD}.log
        """
        pass

    @staticmethod
    def setup_console_handler(logger: logging.Logger) -> None:
        """
        为 logger 添加控制台处理器
        """
        pass
```

**输出格式**:

日志格式：
```
2025-11-19 10:30:45,123 - scout_agent - INFO - Starting to fetch RSS feeds
2025-11-19 10:30:46,456 - scout_agent - ERROR - Connection failed: timeout
```

**错误处理**:

| 错误类型 | 处理方式 | 返回信息 |
|---------|---------|---------|
| 日志目录无法创建 | 尝试创建，失败则警告 | "Failed to create log directory: {path}" |
| 文件写入权限不足 | 降级为仅控制台输出 | "Log file not writable, console only" |

---

## 🔧 实作细节

### 步骤 1: 创建项目目录结构

**目标**: 建立标准化的目录结构

**实作要点**:
- 创建所有必需的目录
- 在空目录中添加 `.gitkeep` 以便 Git 追踪
- 确保目录权限正确

**命令**:

```bash
# 创建目录结构
mkdir -p src/utils
mkdir -p src/agents
mkdir -p src/tools
mkdir -p src/memory
mkdir -p src/orchestrator
mkdir -p data
mkdir -p logs
mkdir -p prompts
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/evaluation

# 创建 .gitkeep
touch data/.gitkeep
touch logs/.gitkeep
```

---

### 步骤 2: 创建 .gitignore

**目标**: 配置 Git 忽略规则

**实作要点**:
- 忽略敏感配置文件 (.env)
- 忽略生成的文件 (日志、数据库、缓存)
- 忽略 Python 相关文件

**代码示例**:

```gitignore
# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Logs
logs/
*.log

# Database
data/
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
embeddings/
temp/
```

---

### 步骤 3: 创建 .env.example 模板

**目标**: 提供环境变量配置模板

**代码示例**:

```bash
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Google Custom Search API
SEARCH_API_KEY=your_search_api_key_here
SEARCH_ENGINE_ID=your_search_engine_id_here

# Email Configuration
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Database
DATABASE_PATH=data/insights.db

# User Profile
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems

# Logging
LOG_LEVEL=INFO
```

---

### 步骤 4: 创建 requirements.txt

**目标**: 定义项目依赖

**实作要点**:
- 包含 Google ADK 及其依赖
- 包含常用工具库
- 固定版本号确保可复现

**代码示例**:

```txt
# Google AI Development Kit
google-adk>=0.1.0

# Google GenAI
google-generativeai>=0.3.0

# Environment management
python-dotenv>=1.0.0

# HTTP & Web
requests>=2.31.0
feedparser>=6.0.10
beautifulsoup4>=4.12.0
lxml>=4.9.3

# Database
sqlalchemy>=2.0.0

# Utilities
pydantic>=2.0.0
```

---

### 步骤 5: 实现 Config Manager

**实作要点**:
- 使用 dataclass 定义配置结构
- 使用 python-dotenv 加载 .env
- 完整的错误处理和验证

**代码框架**:

```python
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path

@dataclass
class Config:
    # ... (字段定义见上文)

    @classmethod
    def load(cls, env_path: str = ".env") -> "Config":
        # 1. 检查文件是否存在
        if not Path(env_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {env_path}")

        # 2. 加载环境变量
        load_dotenv(env_path)

        # 3. 读取并创建 Config 对象
        try:
            config = cls(
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                search_api_key=os.getenv("SEARCH_API_KEY"),
                search_engine_id=os.getenv("SEARCH_ENGINE_ID"),
                email_account=os.getenv("EMAIL_ACCOUNT"),
                email_password=os.getenv("EMAIL_PASSWORD"),
                email_smtp_host=os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
                email_smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
                database_path=os.getenv("DATABASE_PATH", "data/insights.db"),
                user_name=os.getenv("USER_NAME", "Ray"),
                user_interests=os.getenv("USER_INTERESTS", "AI,Robotics")
            )

            # 4. 验证配置
            config.validate()

            return config

        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def validate(self) -> bool:
        # 验证必需字段
        required_fields = [
            ("google_api_key", "GOOGLE_API_KEY"),
            ("search_api_key", "SEARCH_API_KEY"),
            ("search_engine_id", "SEARCH_ENGINE_ID"),
            ("email_account", "EMAIL_ACCOUNT"),
            ("email_password", "EMAIL_PASSWORD")
        ]

        for field_name, env_name in required_fields:
            value = getattr(self, field_name)
            if not value or value == f"your_{field_name}_here":
                raise ValueError(f"Missing or invalid config: {env_name}")

        return True
```

---

### 步骤 6: 实现 Logger System

**实作要点**:
- 同时输出到文件和控制台
- 格式化日志输出
- 自动创建日志目录

**代码框架**:

```python
import logging
from pathlib import Path
from datetime import datetime

class Logger:
    _loggers = {}  # 缓存已创建的 logger

    @staticmethod
    def get_logger(name: str, log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
        # 避免重复创建
        if name in Logger._loggers:
            return Logger._loggers[name]

        # 创建 logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))

        # 清除已有 handlers（避免重复）
        logger.handlers.clear()

        # 添加文件处理器
        Logger.setup_file_handler(logger, log_dir, name)

        # 添加控制台处理器
        Logger.setup_console_handler(logger)

        # 缓存
        Logger._loggers[name] = logger

        return logger

    @staticmethod
    def setup_file_handler(logger: logging.Logger, log_dir: str, name: str) -> None:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 日志文件名：{name}_{YYYYMMDD}.log
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_path / f"{name}_{today}.log"

        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # 格式化
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    @staticmethod
    def setup_console_handler(logger: logging.Logger) -> None:
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化（控制台简化版）
        formatter = logging.Formatter(
            "%(levelname)s - %(name)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
```

---

### 步骤 7: 创建 main.py 入口文件

**目标**: 建立项目入口框架

**代码示例**:

```python
"""
InsightCosmos - Personal AI Intelligence Universe
Main entry point
"""

from src.utils.config import Config
from src.utils.logger import Logger

def main():
    """
    InsightCosmos 主程序入口
    """
    # 初始化 logger
    logger = Logger.get_logger("insightcosmos")
    logger.info("=" * 50)
    logger.info("InsightCosmos Starting...")
    logger.info("=" * 50)

    try:
        # 加载配置
        config = Config.load()
        logger.info("Configuration loaded successfully")
        logger.info(f"User: {config.user_name}")
        logger.info(f"Interests: {config.user_interests}")

        # TODO: 后续阶段添加 Agent 启动逻辑
        logger.info("System initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}", exc_info=True)
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
```

---

## 🧪 测试策略

### 单元测试

**测试文件**: `tests/unit/test_utils.py`

**测试案例清单**:

| 测试案例 ID | 测试内容 | 输入 | 期望输出 | 优先级 |
|-----------|---------|------|---------|--------|
| TC-1-01 | Config 加载成功 | 有效的 .env | Config 对象 | High |
| TC-1-02 | Config 缺失必需字段 | .env 缺失 GOOGLE_API_KEY | ValueError | High |
| TC-1-03 | Config 文件不存在 | 不存在的路径 | FileNotFoundError | High |
| TC-1-04 | Logger 创建成功 | name="test" | Logger 对象 | High |
| TC-1-05 | Logger 写入文件 | logger.info("test") | 日志文件包含 "test" | Medium |
| TC-1-06 | Logger 输出到控制台 | logger.info("test") | 控制台显示 "test" | Medium |

**关键测试场景**:

1. **正常场景 - Config 加载**:
   ```python
   def test_config_load_success():
       # 创建临时 .env
       with open(".env.test", "w") as f:
           f.write("GOOGLE_API_KEY=test_key\n")
           f.write("SEARCH_API_KEY=test_key\n")
           # ... 其他必需字段

       # 加载配置
       config = Config.load(".env.test")

       # 验证
       assert config.google_api_key == "test_key"
       assert config.search_api_key == "test_key"
   ```

2. **异常场景 - Config 缺失字段**:
   ```python
   def test_config_missing_field():
       with open(".env.test", "w") as f:
           f.write("SEARCH_API_KEY=test_key\n")

       with pytest.raises(ValueError, match="Missing.*GOOGLE_API_KEY"):
           Config.load(".env.test")
   ```

3. **正常场景 - Logger 使用**:
   ```python
   def test_logger_basic():
       logger = Logger.get_logger("test")

       # 测试不同级别
       logger.debug("Debug message")
       logger.info("Info message")
       logger.warning("Warning message")
       logger.error("Error message")

       # 验证日志文件存在
       log_file = Path("logs/test_20251119.log")
       assert log_file.exists()
   ```

### 集成测试

**测试场景**: 验证 main.py 能成功启动

**测试步骤**:
1. 准备有效的 .env 文件
2. 运行 `python main.py`
3. 检查日志输出
4. 验证程序正常退出

---

## ✅ 验收标准 (Acceptance Criteria)

### 功能验收

- [ ] 项目目录结构完整建立
- [ ] .env.example 模板完整
- [ ] requirements.txt 包含所有必需依赖
- [ ] Config.load() 能成功加载配置
- [ ] Config.validate() 能检测缺失字段
- [ ] Logger 能同时输出到文件和控制台
- [ ] main.py 能成功运行

### 质量验收

- [ ] 单元测试通过率 = 100% (至少 6 个测试案例)
- [ ] 代码覆盖率 >= 80%
- [ ] 所有函数有完整 docstring
- [ ] 所有函数有类型标注
- [ ] 错误处理覆盖主要场景（文件不存在、字段缺失）

### 性能验收

- [ ] Config.load() 执行时间 < 100ms
- [ ] Logger 初始化时间 < 50ms

### 文档验收

- [ ] 代码注释完整清晰
- [ ] 创建 `stage1_notes.md` 记录实作过程
- [ ] 创建 `stage1_test_report.md` 记录测试结果

---

## 🚧 风险与挑战

### 已知风险

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| .env 文件泄露到 Git | 高 - 敏感信息暴露 | .gitignore 正确配置 + 代码审查 |
| 依赖版本冲突 | 中 - 环境无法复现 | 固定版本号 + 测试安装 |
| 日志文件过大 | 低 - 磁盘占用 | 后续添加日志轮转（Stage 12） |

### 技术挑战

1. **挑战**: Python 版本兼容性
   - **解决方案**: 明确要求 Python 3.10+，使用类型标注新特性

2. **挑战**: Windows 路径问题
   - **解决方案**: 使用 pathlib.Path 处理所有路径

---

## 📚 参考资料

### 技术文档

- [python-dotenv 文档](https://pypi.org/project/python-dotenv/)
- [Python logging 官方文档](https://docs.python.org/3/library/logging.html)
- [dataclasses 文档](https://docs.python.org/3/library/dataclasses.html)

### 内部参考

- `claude.md` - 编码规范
- `docs/project_breakdown.md` - 整体规划

---

## 📝 开发清单 (Checklist)

### 规划阶段 ✓

- [x] 完成本规划文档
- [x] 评审通过（自我检查）

### 实作阶段

- [ ] 创建项目目录结构
- [ ] 创建 .gitignore
- [ ] 创建 .env.example
- [ ] 创建 requirements.txt
- [ ] 实现 Config Manager (src/utils/config.py)
- [ ] 实现 Logger System (src/utils/logger.py)
- [ ] 创建 main.py
- [ ] 创建 __init__.py 文件
- [ ] 编写单元测试
- [ ] 本地测试通过
- [ ] 更新 `docs/implementation/dev_log.md`

### 验证阶段

- [ ] 单元测试全部通过
- [ ] 运行 main.py 成功
- [ ] 日志文件正确生成
- [ ] 配置加载正确
- [ ] 完成 `docs/validation/stage1_test_report.md`
- [ ] 完成 `docs/implementation/stage1_notes.md`

---

## 🎯 下一步行动

### 立即开始（实作阶段）

1. 创建项目目录结构（5 分钟）
2. 创建配置文件（.gitignore, .env.example, requirements.txt）（10 分钟）
3. 实现 Config Manager（30 分钟）
4. 实现 Logger System（30 分钟）
5. 创建 main.py（15 分钟）
6. 编写单元测试（60 分钟）
7. 验证与文档（30 分钟）

### 准备工作

- 确认 Python 3.10+ 已安装
- 准备 .env 文件（复制 .env.example 并填入真实 API keys）

---

## 📊 时间分配

| 阶段 | 预计时间 | 占比 |
|------|---------|------|
| 规划 | 0.5 小时 | 12.5% |
| 实作 | 2.5 小时 | 62.5% |
| 验证 | 1.0 小时 | 25% |
| **总计** | **4.0 小时** | **100%** |

---

**创建日期**: 2025-11-19
**最后更新**: 2025-11-19
**负责人**: Ray 张瑞涵
**状态**: Planning Complete → Ready for Implementation
