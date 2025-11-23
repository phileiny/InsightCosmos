# Stage 5: Scout Agent (探索代理)

> **阶段编号**: Stage 5
> **阶段目标**: 实现信息收集 Agent，自动从 RSS 和 Google Search 收集 AI/Robotics 领域文章
> **前置依赖**: Stage 4 完成（Google Search Tool）
> **预计时间**: 1.5 天
> **状态**: Planning

---

## 🎯 阶段目标

### 核心目标

实现 Scout Agent，作为 InsightCosmos 信息宇宙的第一层——**自动探索层**。Scout Agent 负责：

1. **自动收集文章**：使用 RSS Fetcher 和 Google Search Grounding 工具收集 AI/Robotics 相关文章
2. **智能去重**：基于 URL 和标题的去重逻辑，避免重复内容
3. **数量控制**：每次运行收集 20-30 篇高质量文章
4. **结构化输出**：返回标准化的文章列表，供后续 Analyst Agent 分析

Scout Agent 是整个系统的**起点**，其质量直接影响后续的分析和报告生成。

### 为什么需要这个阶段？

1. **完成 Agent 架构的第一步**：验证 Google ADK 的 LlmAgent 框架在项目中的可行性
2. **工具编排能力**：测试多工具（RSS + Search）的协同使用
3. **数据质量保证**：建立去重和过滤机制，为后续分析提供干净的数据源
4. **端到端验证**：首次实现"输入空 → 输出文章列表"的完整流程

---

## 📥 输入 (Input)

### 来自上一阶段的产出

- **Stage 3 (RSS Tool)**:
  - `src/tools/fetcher.py` - RSSFetcher 类
  - 能够批量抓取 RSS feeds 并返回结构化文章列表

- **Stage 4 (Google Search Tool)**:
  - `src/tools/google_search_grounding_v2.py` - GoogleSearchGroundingTool 类
  - 基于 Gemini Grounding 的搜索功能，返回搜索结果

- **Stage 1 (Foundation)**:
  - `src/utils/config.py` - 配置管理
  - `src/utils/logger.py` - 日志系统

### 外部依赖

- **技术依赖**:
  - Google ADK (`google.adk.agents`)
  - Google Gen AI SDK (`google.genai`)
  - Python 3.10+

- **配置依赖**:
  - `GOOGLE_API_KEY` - Gemini API 密钥（已在 .env 中配置）

- **数据依赖**:
  - **RSS Feeds 列表** - 测试用的 AI/Robotics RSS 源
    ```python
    TEST_RSS_FEEDS = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.roboticsbusinessreview.com/feed/"
    ]
    ```
  - **搜索关键词列表** - 测试用的搜索查询
    ```python
    TEST_SEARCH_QUERIES = [
        "AI multi-agent systems",
        "robotics automation 2025",
        "large language models research"
    ]
    ```

---

## 📤 输出 (Output)

### 代码产出

```
src/
└─ agents/
    ├─ __init__.py          # Agents 模块初始化
    └─ scout_agent.py       # Scout Agent 实现

prompts/
└─ scout_prompt.txt         # Scout Agent 指令 Prompt

tests/
└─ integration/
    └─ test_scout_agent.py  # Scout Agent 集成测试
```

### 文档产出

- `docs/implementation/stage5_scout_implementation.md` - 实作笔记
- `docs/validation/stage5_scout_test_report.md` - 测试报告

### 功能产出

- [ ] Scout Agent 能调用 RSS Fetcher 工具收集文章
- [ ] Scout Agent 能调用 Google Search Grounding 工具搜索文章
- [ ] 能自动去重（基于 URL）
- [ ] 能限制输出数量（20-30 篇）
- [ ] 输出格式符合规范（标准化的文章字典列表）
- [ ] Agent 能通过 ADK Runner 运行

---

## 🏗️ 技术设计

### 架构图

```
┌─────────────────────────────────────────────────────┐
│                  Scout Agent                        │
│           (LlmAgent - Gemini 2.5 Flash)             │
└─────────────────────────────────────────────────────┘
                        │
                        │ uses tools
                        ↓
        ┌───────────────┴───────────────┐
        │                               │
        ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│  fetch_rss       │          │  search_articles │
│  (Tool Wrapper)  │          │  (Tool Wrapper)  │
└──────────────────┘          └──────────────────┘
        │                               │
        ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│  RSSFetcher      │          │  GoogleSearch    │
│  (Class)         │          │  GroundingTool   │
└──────────────────┘          └──────────────────┘
                        │
                        ↓
                  去重 & 限制数量
                        │
                        ↓
              ┌─────────────────┐
              │  raw_articles   │
              │  (List[Dict])   │
              └─────────────────┘
```

### 核心组件

#### 组件 1: Scout Agent (LlmAgent)

**职责**: 编排 RSS 和 Search 工具，收集文章并去重

**定义**:

```python
from google.adk.agents import LlmAgent

scout_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ScoutAgent",
    description="Collects AI and Robotics articles from RSS feeds and Google Search",
    instruction=SCOUT_INSTRUCTION,  # 从 prompts/scout_prompt.txt 加载
    tools=[fetch_rss, search_articles],  # ADK 工具函数
    output_key="raw_articles"  # 可选：指定输出键
)
```

**Instruction 设计**:

```
你是 InsightCosmos 的信息探索代理（Scout Agent）。你的任务是自动收集 AI 和 Robotics 领域的最新文章。

## 任务目标
收集 20-30 篇高质量文章，涵盖以下主题：
- AI（人工智能）：Large Language Models, Multi-Agent Systems, AI Safety
- Robotics（机器人）：自动化、机器人控制、人机协作

## 执行步骤
1. 使用 fetch_rss 工具从预定义的 RSS feeds 收集文章
2. 使用 search_articles 工具搜索以下关键词：
   - "AI multi-agent systems"
   - "robotics automation"
   - "large language models research"
3. 合并所有文章并去重（基于 URL）
4. 限制最终输出为 20-30 篇文章

## 可用工具
- fetch_rss(feed_urls: List[str]) -> Dict
  - 批量抓取 RSS feeds
  - 返回结构化文章列表

- search_articles(query: str, max_results: int) -> Dict
  - 使用 Google Search Grounding 搜索文章
  - 返回搜索结果列表

## 输出格式
返回一个包含以下字段的字典：
{
    "status": "success",
    "articles": [
        {
            "url": "https://...",
            "title": "文章标题",
            "summary": "文章摘要",
            "published_at": datetime,
            "source": "rss" | "google_search_grounding",
            "source_name": "来源名称"
        },
        ...
    ],
    "total_count": 25,
    "sources": {
        "rss": 15,
        "search": 10
    }
}

## 质量标准
- 文章必须与 AI 或 Robotics 相关
- 优先选择最近发布的文章（1 周内）
- 避免重复的 URL
- 确保来源多样性（不要全部来自同一个网站）
```

#### 组件 2: ADK Tool Wrappers

**职责**: 将现有的工具类包装为 ADK 兼容的 FunctionTool

**fetch_rss 工具包装器**:

```python
from typing import List, Dict, Any
from src.tools import RSSFetcher

def fetch_rss(feed_urls: List[str], max_articles_per_feed: int = 10) -> Dict[str, Any]:
    """
    从 RSS feeds 批量抓取文章

    Args:
        feed_urls: RSS feed URL 列表
        max_articles_per_feed: 每个 feed 的最大文章数（默认 10）

    Returns:
        dict: {
            "status": "success" | "partial" | "error",
            "articles": List[Dict],  # 文章列表
            "errors": List[Dict],    # 错误列表
            "summary": {
                "total_feeds": int,
                "successful_feeds": int,
                "total_articles": int
            }
        }

    Example:
        >>> result = fetch_rss([
        ...     'https://techcrunch.com/category/artificial-intelligence/feed/',
        ...     'https://venturebeat.com/category/ai/feed/'
        ... ])
        >>> print(result['summary']['total_articles'])
    """
    try:
        fetcher = RSSFetcher(timeout=30)
        result = fetcher.fetch_rss_feeds(
            feed_urls=feed_urls,
            max_articles_per_feed=max_articles_per_feed
        )
        return result
    except Exception as e:
        return {
            "status": "error",
            "articles": [],
            "errors": [{"error_type": "FetcherError", "error_message": str(e)}],
            "summary": {"total_feeds": 0, "successful_feeds": 0, "total_articles": 0}
        }
```

**search_articles 工具包装器**:

```python
from src.tools import GoogleSearchGroundingTool

def search_articles(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    使用 Google Search Grounding 搜索文章

    Args:
        query: 搜索查询字符串
        max_results: 最大返回结果数（默认 10）

    Returns:
        dict: {
            "status": "success" | "error",
            "query": str,
            "articles": List[Dict],
            "total_results": int,
            "error_message": str (if error)
        }

    Example:
        >>> result = search_articles("AI multi-agent systems", max_results=5)
        >>> print(result['total_results'])
    """
    try:
        search_tool = GoogleSearchGroundingTool()
        result = search_tool.search_articles(query=query, max_results=max_results)
        search_tool.close()
        return result
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "articles": [],
            "total_results": 0,
            "error_message": str(e)
        }
```

#### 组件 3: Scout Agent Runner

**职责**: 提供简单的接口运行 Scout Agent

**实现**:

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

class ScoutAgentRunner:
    """
    Scout Agent 运行器

    提供简单的接口来运行 Scout Agent

    Attributes:
        agent: Scout Agent 实例
        runner: ADK Runner 实例
        session_service: 会话管理服务

    Example:
        >>> scout_runner = ScoutAgentRunner()
        >>> result = scout_runner.collect_articles()
        >>> print(f"Collected {len(result['articles'])} articles")
    """

    def __init__(self, agent=None):
        """
        初始化 Scout Agent Runner

        Args:
            agent: Scout Agent 实例（可选，默认创建新实例）
        """
        from src.agents.scout_agent import create_scout_agent

        self.agent = agent or create_scout_agent()
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name="InsightCosmos",
            session_service=self.session_service
        )

        # 创建会话
        self.session = self.session_service.create_session(
            app_name="InsightCosmos",
            user_id="system",
            session_id="scout_session_001"
        )

    def collect_articles(self) -> Dict[str, Any]:
        """
        运行 Scout Agent 收集文章

        Returns:
            dict: {
                "status": "success" | "error",
                "articles": List[Dict],
                "total_count": int,
                "sources": Dict[str, int]
            }

        Example:
            >>> result = scout_runner.collect_articles()
            >>> print(result['total_count'])
        """
        # 创建用户消息
        content = types.Content(
            role='user',
            parts=[types.Part(text="收集今日 AI 和 Robotics 领域的最新文章")]
        )

        # 运行 Agent
        events = self.runner.run(
            user_id="system",
            session_id="scout_session_001",
            new_message=content
        )

        # 提取最终结果
        final_result = None
        for event in events:
            if event.is_final_response() and event.content:
                # 解析 Agent 的输出
                final_result = self._parse_agent_output(event)

        return final_result or {
            "status": "error",
            "articles": [],
            "total_count": 0,
            "error_message": "Agent did not return a final response"
        }

    def _parse_agent_output(self, event) -> Dict[str, Any]:
        """
        解析 Agent 输出事件

        Args:
            event: ADK Event 对象

        Returns:
            dict: 解析后的文章列表
        """
        # 实现输出解析逻辑
        # 这里需要根据 Agent 的实际输出格式进行调整
        pass
```

**输出格式**:

```python
{
    "status": "success",
    "articles": [
        {
            "url": "https://techcrunch.com/2025/11/23/ai-agents-breakthrough/",
            "title": "AI Agents Achieve New Breakthrough in Multi-Task Learning",
            "summary": "Researchers demonstrate...",
            "content": "",  # 初始为空，Stage 6 会填充
            "published_at": datetime(2025, 11, 23, 10, 0, 0, tzinfo=timezone.utc),
            "source": "rss",
            "source_name": "TechCrunch",
            "tags": ["AI", "agents", "machine learning"]
        },
        # ... 更多文章
    ],
    "total_count": 25,
    "sources": {
        "rss": 15,
        "google_search_grounding": 10
    },
    "collected_at": datetime.now(timezone.utc)
}
```

---

## 🔧 实作细节

### 步骤 1: 创建 Prompt 模板

**目标**: 编写清晰、可执行的 Scout Agent 指令

**实作要点**:
- 明确任务目标（收集 20-30 篇文章）
- 列出详细的执行步骤
- 说明每个工具的用途和参数
- 定义清晰的输出格式
- 设置质量标准

**文件位置**: `prompts/scout_prompt.txt`

### 步骤 2: 实现 ADK Tool Wrappers

**目标**: 包装现有工具类为 ADK FunctionTool

**实作要点**:
- 完整的 docstring（LLM 会读取）
- 类型标注（Type Hints）
- 错误处理与友好的错误消息
- 与现有工具类的接口对接

**文件位置**: `src/agents/scout_agent.py`

### 步骤 3: 创建 Scout Agent

**目标**: 使用 ADK LlmAgent 定义 Scout Agent

**实作要点**:
- 选择合适的模型（gemini-2.5-flash）
- 加载 Prompt 模板
- 注册工具函数
- 配置日志插件（LoggingPlugin）

**代码示例**:

```python
from google.adk.agents import LlmAgent
from google.adk.plugins import LoggingPlugin

def create_scout_agent() -> LlmAgent:
    """
    创建 Scout Agent 实例

    Returns:
        LlmAgent: 配置好的 Scout Agent

    Example:
        >>> agent = create_scout_agent()
        >>> print(agent.name)
        'ScoutAgent'
    """
    # 加载 Prompt
    with open("prompts/scout_prompt.txt", "r", encoding="utf-8") as f:
        instruction = f.read()

    # 创建 Agent
    agent = LlmAgent(
        model="gemini-2.5-flash",
        name="ScoutAgent",
        description="Collects AI and Robotics articles from RSS feeds and Google Search",
        instruction=instruction,
        tools=[fetch_rss, search_articles],
        plugins=[LoggingPlugin()]  # 启用日志
    )

    return agent
```

### 步骤 4: 实现 Runner

**目标**: 创建简单的运行接口

**实作要点**:
- 使用 InMemorySessionService（阶段 1 不需要持久化）
- 处理 Agent 输出事件
- 解析最终结果
- 错误处理

### 步骤 5: 去重逻辑

**目标**: 确保不返回重复文章

**实作选择**:

**方案 A**: 在 Agent Instruction 中要求去重（推荐）
```
3. 合并所有文章并去重（基于 URL）
4. 如果去重后超过 30 篇，保留最新的 30 篇
```

**方案 B**: 在 Runner 的 `_parse_agent_output` 中去重
```python
def _parse_agent_output(self, event) -> Dict[str, Any]:
    articles = self._extract_articles(event)

    # 去重
    seen_urls = set()
    unique_articles = []
    for article in articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)

    return {"articles": unique_articles, ...}
```

**决定**: 采用方案 A + 方案 B 组合
- Instruction 要求 LLM 去重（减少不必要的 token 消耗）
- Runner 再次去重（保险机制）

---

## 🧪 测试策略

### 单元测试

**测试文件**: `tests/unit/test_scout_tools.py`

**测试案例清单**:

| 测试案例 ID | 测试内容 | 输入 | 期望输出 | 优先级 |
|-----------|---------|------|---------|--------|
| TC-5-01 | fetch_rss 工具正常调用 | 有效的 RSS URL 列表 | status="success", articles 非空 | High |
| TC-5-02 | fetch_rss 处理无效 URL | 无效 URL | status="error", 友好错误消息 | High |
| TC-5-03 | search_articles 工具正常调用 | 有效查询字符串 | status="success", articles 非空 | High |
| TC-5-04 | search_articles 处理网络错误 | 触发网络异常 | status="error", 错误信息 | Medium |
| TC-5-05 | 工具 docstring 完整性 | N/A | docstring 包含必要信息 | High |

**关键测试场景**:

1. **正常场景**: 工具能正常返回数据
   ```python
   def test_fetch_rss_success():
       result = fetch_rss([
           'https://techcrunch.com/category/artificial-intelligence/feed/'
       ])
       assert result['status'] == 'success'
       assert len(result['articles']) > 0
       assert 'url' in result['articles'][0]
       assert 'title' in result['articles'][0]
   ```

2. **边界场景**: 空列表输入
   ```python
   def test_fetch_rss_empty_list():
       result = fetch_rss([])
       assert result['status'] in ['success', 'error']
       assert result['summary']['total_feeds'] == 0
   ```

3. **异常场景**: 工具类抛出异常
   ```python
   def test_fetch_rss_exception(mocker):
       mocker.patch('src.tools.RSSFetcher.fetch_rss_feeds', side_effect=Exception("Network error"))
       result = fetch_rss(['https://example.com/feed/'])
       assert result['status'] == 'error'
       assert 'error_message' in result['errors'][0]
   ```

### 集成测试

**测试文件**: `tests/integration/test_scout_agent.py`

**测试场景**:

1. **端到端测试**:
   ```python
   def test_scout_agent_end_to_end():
       """测试 Scout Agent 完整流程"""
       runner = ScoutAgentRunner()
       result = runner.collect_articles()

       # 验证输出格式
       assert result['status'] == 'success'
       assert 20 <= len(result['articles']) <= 30

       # 验证文章字段
       article = result['articles'][0]
       assert 'url' in article
       assert 'title' in article
       assert 'source' in article

       # 验证去重
       urls = [a['url'] for a in result['articles']]
       assert len(urls) == len(set(urls))  # 无重复 URL
   ```

2. **工具调用轨迹测试** (ADK Evaluation):
   ```json
   {
     "eval_set_id": "scout_agent_v1",
     "eval_cases": [
       {
         "eval_id": "scout_basic",
         "description": "Scout Agent 基本收集功能",
         "conversation": [
           {
             "user_content": "收集今日 AI 新闻",
             "expected_tools": ["fetch_rss", "search_articles"],
             "final_response": {
               "contains": ["articles", "total_count"]
             }
           }
         ]
       }
     ]
   }
   ```

3. **性能测试**:
   ```python
   def test_scout_agent_performance():
       """测试 Scout Agent 运行时间"""
       import time

       runner = ScoutAgentRunner()
       start = time.time()
       result = runner.collect_articles()
       duration = time.time() - start

       # 应该在 60 秒内完成
       assert duration < 60
       assert result['status'] == 'success'
   ```

---

## ✅ 验收标准 (Acceptance Criteria)

### 功能验收

- [ ] Scout Agent 能成功调用 `fetch_rss` 工具
- [ ] Scout Agent 能成功调用 `search_articles` 工具
- [ ] 能自动去重（基于 URL）
- [ ] 输出文章数量在 20-30 篇范围内
- [ ] 输出格式符合规范（包含必需字段）
- [ ] 通过 Runner 接口能正常运行

### 质量验收

- [ ] 单元测试通过率 = 100%
- [ ] 集成测试通过（端到端）
- [ ] 所有函数有完整 docstring
- [ ] 所有函数有类型标注
- [ ] 工具错误处理覆盖主要场景
- [ ] 日志输出清晰可追踪

### 性能验收

- [ ] 单次运行时间 < 60 秒（包含网络请求）
- [ ] RSS feeds 批量抓取成功率 >= 80%
- [ ] Google Search 成功率 >= 90%

### ADK Evaluation 验收

- [ ] `tool_trajectory_avg_score` >= 0.9
- [ ] Agent 能正确选择工具
- [ ] Agent 能正确传递参数

### 文档验收

- [ ] Prompt 模板清晰完整
- [ ] 代码注释完整
- [ ] 实作笔记记录关键决策
- [ ] 测试报告包含所有测试结果

---

## 🚧 风险与挑战

### 已知风险

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| RSS feeds 部分失效 | 收集文章数量不足 | 1. 准备多个备用 feeds<br>2. 增加 Google Search 的查询数量 |
| Google Search API 配额限制 | 无法完成搜索 | 1. 合理控制每日运行次数<br>2. 优先使用 RSS，Search 作为补充 |
| LLM 未按指令去重 | 输出重复文章 | 1. 优化 Prompt 指令<br>2. Runner 中实现二次去重 |
| Agent 输出格式不稳定 | 解析失败 | 1. 在 Instruction 中明确 JSON 格式<br>2. 实现健壮的解析逻辑 |

### 技术挑战

1. **挑战 1**: ADK 工具包装器的 docstring 要求
   - **问题**: LLM 依赖 docstring 理解工具，格式必须清晰
   - **解决方案**:
     - 参考 ADK 官方示例
     - 包含完整的 Args、Returns、Example
     - 用简单的语言描述工具功能

2. **挑战 2**: Agent 输出解析
   - **问题**: ADK Event 的输出格式需要解析
   - **解决方案**:
     - 研究 ADK Event 结构
     - 实现通用的解析函数
     - 处理多种可能的输出格式

3. **挑战 3**: 去重逻辑的可靠性
   - **问题**: 相同内容可能有不同 URL（URL 参数、重定向等）
   - **解决方案**:
     - Stage 5 仅基于 URL 精确匹配去重
     - 后续 Stage 可引入标题相似度去重

---

## 📚 参考资料

### 技术文档

- [ADK LlmAgent 文档](https://github.com/google/adk-docs/blob/main/docs/agents/llm-agents.md)
- [ADK Function Tools 文档](https://github.com/google/adk-docs/blob/main/docs/tools/function-tools.md)
- [ADK Runner 文档](https://github.com/google/adk-docs/blob/main/docs/runners/)
- [Context7 - Google ADK 文档](/google/adk-docs)

### 内部参考

- `docs/reference/5D_AI_Agent_Summary.md` - Day 3: Agents, Tools, Think-Act-Observe
- `CLAUDE.md` - Agent 设计规范、工具设计规范
- `docs/planning/stage3_rss_tool.md` - RSS Fetcher 设计
- `docs/planning/stage4_google_search_v2.md` - Google Search Grounding 设计

### 示例代码

- ADK 官方示例：Weather Agent with Tools
  ```python
  agent = LlmAgent(
      model="gemini-2.5-flash",
      name="weather_agent",
      tools=[get_weather, get_current_time]
  )
  ```

---

## 📝 开发清单 (Checklist)

### 规划阶段 ✓

- [x] 完成本规划文档
- [ ] 评审通过

### 实作阶段

- [ ] 创建 `src/agents/` 目录
- [ ] 创建 `prompts/` 目录
- [ ] 编写 Scout Prompt 模板 (`prompts/scout_prompt.txt`)
- [ ] 实现 `fetch_rss` 工具包装器
- [ ] 实现 `search_articles` 工具包装器
- [ ] 实现 `create_scout_agent()` 函数
- [ ] 实现 `ScoutAgentRunner` 类
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 代码自测通过
- [ ] 更新 `docs/implementation/dev_log.md`

### 验证阶段

- [ ] 单元测试全部通过
- [ ] 集成测试通过
- [ ] 端到端测试验证
- [ ] ADK Evaluation 通过（可选）
- [ ] 性能测试达标
- [ ] 人工验收：检查输出文章质量
- [ ] 完成 `docs/validation/stage5_scout_test_report.md`
- [ ] 文档更新完成

---

## 🎯 下一步行动

### 立即开始

1. **创建目录结构**
   ```bash
   mkdir -p src/agents
   mkdir -p prompts
   mkdir -p tests/integration
   touch src/agents/__init__.py
   ```

2. **编写 Scout Prompt 模板**
   - 文件位置: `prompts/scout_prompt.txt`
   - 参考本文档中的 Instruction 设计

3. **实现工具包装器**
   - 在 `src/agents/scout_agent.py` 中实现 `fetch_rss` 和 `search_articles`

### 准备工作

- [ ] 确认 Google API Key 配置正确
- [ ] 准备测试用的 RSS feeds 列表
- [ ] 准备测试用的搜索关键词
- [ ] 阅读 ADK LlmAgent 官方文档

---

## 📊 时间分配

| 阶段 | 预计时间 | 占比 |
|------|---------|------|
| 规划 | 2 小时 | 17% |
| 实作 | 8 小时 | 66% |
| 验证 | 2 小时 | 17% |
| **总计** | **12 小时** | **100%** |

**实作细分**:
- Prompt 编写: 1 小时
- 工具包装器: 2 小时
- Agent 创建: 1 小时
- Runner 实现: 2 小时
- 测试编写: 2 小时

---

**创建日期**: 2025-11-23
**最后更新**: 2025-11-23
**负责人**: Ray 张瑞涵
**状态**: Planning → Implementation → Validation → Done
