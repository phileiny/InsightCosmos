# -*- coding: utf-8 -*-
"""
InsightCosmos Scout Agent

Scout Agent 是信息收集代理，负责从 RSS feeds 和 Google Search 收集 AI/Robotics 领域的文章。

Classes:
    ScoutAgentRunner: Scout Agent 运行器

Functions:
    fetch_rss: ADK 工具包装器 - RSS 文章抓取
    search_articles: ADK 工具包装器 - Google Search 文章搜索
    create_scout_agent: 创建 Scout Agent 实例

Usage:
    from src.agents.scout_agent import ScoutAgentRunner

    runner = ScoutAgentRunner()
    result = runner.collect_articles()
    print(f"Collected {result['total_count']} articles")

References:
    - Planning Doc: docs/planning/stage5_scout_agent.md
    - ADK LlmAgent: https://github.com/google/adk-docs/blob/main/docs/agents/llm-agents.md
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import logging
import os

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins import LoggingPlugin
from google.genai import types

from src.tools import RSSFetcher, GoogleSearchGroundingTool
from src.utils.logger import Logger


# ============================================================================
# Article Classification Utilities
# ============================================================================

def categorize_article(title: str, content: str = "") -> str:
    """
    快速分類文章

    根據標題和內容關鍵字判斷文章屬於哪個分類，
    用於 Daily Digest 分組顯示。

    Args:
        title: 文章標題
        content: 文章內容或摘要（可選）

    Returns:
        str: 分類標籤
            - "robotics": 純機器人
            - "ai_robotics": AI + 機器人交集
            - "ai_general": 純 AI
            - "industry": 其他產業新聞

    Example:
        >>> categorize_article("Boston Dynamics unveils new humanoid robot")
        'robotics'
        >>> categorize_article("GPT-5 announcement from OpenAI")
        'ai_general'
    """
    text = f"{title} {content}".lower()

    robotics_keywords = [
        "robot", "robotics", "cobot", "amr", "agv", "manipulation",
        "gripper", "humanoid", "warehouse automation", "delivery robot",
        "service robot", "pudu", "keenon", "boston dynamics", "機器人",
        "unitree", "universal robots", "figure ai", "agility", "tesla bot"
    ]

    ai_robotics_keywords = [
        "embodied ai", "robot learning", "sim-to-real", "vla",
        "robot foundation model", "isaac sim", "robot manipulation",
        "vision language action", "robot training"
    ]

    ai_keywords = [
        "llm", "gpt", "claude", "gemini", "language model", "chatbot",
        "openai", "anthropic", "transformer", "neural network", "deep learning"
    ]

    robotics_score = sum(1 for kw in robotics_keywords if kw in text)
    ai_robotics_score = sum(1 for kw in ai_robotics_keywords if kw in text)
    ai_score = sum(1 for kw in ai_keywords if kw in text)

    if robotics_score >= 2 and ai_score >= 1:
        return "ai_robotics"
    elif robotics_score >= 1:
        return "robotics"
    elif ai_robotics_score >= 1:
        return "ai_robotics"
    elif ai_score >= 1:
        return "ai_general"
    else:
        return "industry"


def is_competitor_news(title: str, content: str = "") -> bool:
    """
    檢查是否為競品新聞

    用於標記重要的競品動態，可在報告中特別標註。

    Args:
        title: 文章標題
        content: 文章內容或摘要（可選）

    Returns:
        bool: True 如果是競品相關新聞

    Example:
        >>> is_competitor_news("Pudu Robotics raises $100M Series C")
        True
        >>> is_competitor_news("New AI model released")
        False
    """
    text = f"{title} {content}".lower()
    competitors = [
        "pudu", "keenon", "bear robotics", "segway", "gaussian",
        "优必选", "unitree", "宇树", "figure ai", "agility",
        "boston dynamics", "sanctuary ai", "apptronik"
    ]
    return any(comp in text for comp in competitors)


def get_article_stats(articles: list) -> dict:
    """
    統計文章分類分佈

    Args:
        articles: 文章列表，每篇文章需包含 title 欄位

    Returns:
        dict: 分類統計
            {
                "robotics": 10,
                "ai_robotics": 5,
                "ai_general": 8,
                "industry": 2,
                "competitor_news": 3,
                "total": 25
            }
    """
    stats = {
        "robotics": 0,
        "ai_robotics": 0,
        "ai_general": 0,
        "industry": 0,
        "competitor_news": 0,
        "total": len(articles)
    }

    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")

        category = categorize_article(title, summary)
        stats[category] += 1

        if is_competitor_news(title, summary):
            stats["competitor_news"] += 1

    return stats


# ============================================================================
# ADK Tool Wrappers
# ============================================================================

def fetch_rss(feed_urls: List[str], max_articles_per_feed: int = 10) -> Dict[str, Any]:
    """
    从 RSS feeds 批量抓取文章

    这是一个 ADK 兼容的工具函数，包装了 RSSFetcher 类的功能。
    LLM 将根据此 docstring 理解如何使用这个工具。

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
        20
    """
    logger = Logger.get_logger("fetch_rss")
    logger.info(f"🔧 [TOOL] fetch_rss called")
    logger.info(f"  → Feeds: {len(feed_urls)}, Max per feed: {max_articles_per_feed}")

    import time
    start_time = time.time()

    try:
        fetcher = RSSFetcher(timeout=30)
        result = fetcher.fetch_rss_feeds(
            feed_urls=feed_urls,
            max_articles_per_feed=max_articles_per_feed
        )
        elapsed = time.time() - start_time
        logger.info(f"  ✓ fetch_rss returned {result['summary']['total_articles']} articles in {elapsed:.1f}s")
        return result

    except Exception as e:
        logger.error(f"fetch_rss failed: {e}")
        return {
            "status": "error",
            "articles": [],
            "errors": [{
                "error_type": "FetcherError",
                "error_message": f"Failed to fetch RSS feeds: {str(e)}"
            }],
            "summary": {
                "total_feeds": len(feed_urls),
                "successful_feeds": 0,
                "total_articles": 0
            }
        }


def search_articles(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    使用 Google Search Grounding 搜索文章

    这是一个 ADK 兼容的工具函数，包装了 GoogleSearchGroundingTool 类的功能。
    LLM 将根据此 docstring 理解如何使用这个工具。

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
        5
    """
    logger = Logger.get_logger("search_articles")
    logger.info(f"🔧 [TOOL] search_articles called")
    logger.info(f"  → Query: '{query}', Max results: {max_results}")

    import time
    start_time = time.time()

    try:
        search_tool = GoogleSearchGroundingTool()
        result = search_tool.search_articles(query=query, max_results=max_results)
        search_tool.close()

        elapsed = time.time() - start_time
        logger.info(f"  ✓ search_articles returned {result['total_results']} articles in {elapsed:.1f}s")
        return result

    except Exception as e:
        logger.error(f"search_articles failed: {e}")
        return {
            "status": "error",
            "query": query,
            "articles": [],
            "total_results": 0,
            "error_message": f"Failed to search articles: {str(e)}"
        }


# ============================================================================
# Scout Agent Creation
# ============================================================================

def create_scout_agent(
    instruction_file: str = "prompts/scout_prompt.txt",
    user_interests: Optional[str] = None
) -> LlmAgent:
    """
    创建 Scout Agent 实例

    根据 Prompt 模板创建一个配置好的 Scout Agent，包含 RSS 和 Search 工具。

    Args:
        instruction_file: Prompt 模板文件路径（默认 prompts/scout_prompt.txt）
        user_interests: 用户兴趣列表（逗号分隔），用于替换 prompt 模板中的 {{USER_INTERESTS}}

    Returns:
        LlmAgent: 配置好的 Scout Agent

    Raises:
        FileNotFoundError: 如果 instruction_file 不存在

    Example:
        >>> agent = create_scout_agent(user_interests="AI,Robotics,Multi-Agent Systems")
        >>> print(agent.name)
        'ScoutAgent'
    """
    logger = Logger.get_logger("create_scout_agent")

    # 加载 Prompt 模板
    if not os.path.exists(instruction_file):
        raise FileNotFoundError(
            f"Instruction file not found: {instruction_file}\n"
            f"Please ensure the file exists at the specified path."
        )

    with open(instruction_file, "r", encoding="utf-8") as f:
        instruction = f.read()

    logger.info(f"Loaded instruction from {instruction_file}")

    # 替換模板變數
    if user_interests is None:
        # 從環境變數讀取
        from dotenv import load_dotenv
        load_dotenv()
        user_interests = os.getenv("USER_INTERESTS", "AI,Robotics,Multi-Agent Systems")

    instruction = instruction.replace("{{USER_INTERESTS}}", user_interests)
    logger.info(f"User interests applied: {user_interests}")

    from google.adk.models import Gemini
    from dotenv import load_dotenv

    # 載入環境變數
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment variables. "
            "Please set it in .env file or environment."
        )

    # 创建 Scout Agent
    agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash", api_key=api_key),
        name="ScoutAgent",
        description="Collects AI and Robotics articles from RSS feeds and Google Search",
        instruction=instruction,
        tools=[fetch_rss, search_articles]
    )

    logger.info("Scout Agent created successfully")
    return agent


# ============================================================================
# Scout Agent Runner
# ============================================================================

class ScoutAgentRunner:
    """
    Scout Agent 运行器

    提供简单的接口来运行 Scout Agent 并收集文章。

    Attributes:
        agent: Scout Agent 实例
        runner: ADK Runner 实例
        session_service: 会话管理服务
        logger: 日志记录器

    Example:
        >>> runner = ScoutAgentRunner()
        >>> result = runner.collect_articles()
        >>> print(f"Collected {len(result['articles'])} articles")
    """

    APP_NAME = "agents"  # 必須匹配 ADK agent 載入路徑推斷的名稱
    USER_ID = "system"
    SESSION_ID = "scout_session_001"

    def __init__(
        self,
        agent: Optional[LlmAgent] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化 Scout Agent Runner

        Args:
            agent: Scout Agent 实例（可选，默认创建新实例）
            logger: Logger 实例（可选）

        Example:
            >>> runner = ScoutAgentRunner()
            >>> # 或使用自定义 Agent
            >>> custom_agent = create_scout_agent()
            >>> runner = ScoutAgentRunner(agent=custom_agent)
        """
        self.logger = logger or Logger.get_logger("ScoutAgentRunner")

        # 创建或使用提供的 Agent
        self.agent = agent or create_scout_agent()

        # 初始化会话服务
        self.session_service = InMemorySessionService()

        # 创建 Runner
        self.runner = Runner(
            agent=self.agent,
            app_name=self.APP_NAME,
            session_service=self.session_service
        )

        # Session 會在首次調用 collect_articles 時創建
        self._session_initialized = False

        self.logger.info("ScoutAgentRunner initialized")

    async def _ensure_session(self):
        """確保 session 已創建（內部使用）"""
        if not self._session_initialized:
            await self.session_service.create_session(
                app_name=self.APP_NAME,
                user_id=self.USER_ID,
                session_id=self.SESSION_ID
            )
            self._session_initialized = True
            self.logger.debug(f"Session created: {self.SESSION_ID}")

    def collect_articles(self, user_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        运行 Scout Agent 收集文章

        Args:
            user_prompt: 用户提示（可选，默认使用标准提示）

        Returns:
            dict: {
                "status": "success" | "error",
                "articles": List[Dict],
                "total_count": int,
                "sources": Dict[str, int],
                "collected_at": datetime,
                "error_message": str (if error)
            }

        Example:
            >>> result = runner.collect_articles()
            >>> print(result['total_count'])
            25
        """
        import asyncio

        self.logger.info("Starting article collection...")

        # 使用默认提示或自定义提示
        if user_prompt is None:
            user_prompt = "收集今日 AI 和 Robotics 领域的最新文章"

        # 创建用户消息
        content = types.Content(
            role='user',
            parts=[types.Part(text=user_prompt)]
        )

        async def _collect_async():
            try:
                # 確保 session 已創建
                self.logger.info("  [1/4] Creating session...")
                await self._ensure_session()
                self.logger.info("  ✓ Session created")

                # 运行 Agent（使用 run_async）
                self.logger.info("  [2/4] Starting LLM Agent execution...")
                self.logger.info(f"  → User prompt: {user_prompt}")

                import time
                start_time = time.time()

                events_gen = self.runner.run_async(
                    user_id=self.USER_ID,
                    session_id=self.SESSION_ID,
                    new_message=content
                )

                # 提取最终结果
                self.logger.info("  [3/4] Processing LLM events...")
                final_result = None
                event_count = 0

                async for event in events_gen:
                    event_count += 1
                    elapsed = time.time() - start_time

                    # 每 10 個事件或每 30 秒記錄一次進度
                    if event_count % 10 == 0 or elapsed > 30:
                        self.logger.info(f"  → Processing event #{event_count} (elapsed: {elapsed:.1f}s)")

                    self.logger.debug(f"Event: {event}")

                    if event.is_final_response() and event.content:
                        self.logger.info(f"  ✓ Received final response (elapsed: {elapsed:.1f}s)")
                        final_result = self._parse_agent_output(event)

                # 如果没有获取到最终结果
                if final_result is None:
                    total_time = time.time() - start_time
                    self.logger.warning(f"  ✗ Agent did not return a final response after {total_time:.1f}s and {event_count} events")
                    return {
                        "status": "error",
                        "articles": [],
                        "total_count": 0,
                        "sources": {},
                        "collected_at": datetime.now(timezone.utc),
                        "error_message": "Agent did not return a final response"
                    }

                # 添加收集时间
                final_result['collected_at'] = datetime.now(timezone.utc)

                total_time = time.time() - start_time
                self.logger.info(
                    f"  [4/4] Article collection completed: {final_result.get('total_count', 0)} articles in {total_time:.1f}s"
                )

                return final_result

            except Exception as e:
                self.logger.error(f"Article collection failed: {e}")
                return {
                    "status": "error",
                    "articles": [],
                    "total_count": 0,
                    "sources": {},
                    "collected_at": datetime.now(timezone.utc),
                    "error_message": f"Collection error: {str(e)}"
                }

        # 使用 asyncio.run 執行 async 函數
        return asyncio.run(_collect_async())

    def _parse_agent_output(self, event) -> Dict[str, Any]:
        """
        解析 Agent 输出事件

        Args:
            event: ADK Event 对象

        Returns:
            dict: 解析后的结果

        Raises:
            ValueError: 如果无法解析输出
        """
        self.logger.info("  → Parsing agent output...")

        try:
            # 获取文本内容
            if not event.content or not event.content.parts:
                raise ValueError("Event has no content or parts")

            text_content = None
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    text_content = part.text
                    break

            if not text_content:
                raise ValueError("No text content found in event parts")

            content_length = len(text_content)
            self.logger.info(f"  → Raw text content length: {content_length} chars")
            self.logger.debug(f"Raw text content preview: {text_content[:500]}...")

            # 尝试解析 JSON
            # Agent 可能返回 Markdown 格式的 JSON（```json ... ```）
            text_content = text_content.strip()

            # 移除可能的 Markdown 代码块标记
            if text_content.startswith("```json"):
                text_content = text_content[7:]  # 移除 ```json
            if text_content.startswith("```"):
                text_content = text_content[3:]  # 移除 ```
            if text_content.endswith("```"):
                text_content = text_content[:-3]  # 移除结尾的 ```

            text_content = text_content.strip()

            # 解析 JSON
            self.logger.info("  → Parsing JSON...")

            # 修復常見的 JSON 轉義問題
            text_content = self._sanitize_json_string(text_content)

            result = json.loads(text_content)
            self.logger.info("  ✓ JSON parsed successfully")

            # 验证必需字段
            if "articles" not in result:
                raise ValueError("Output missing 'articles' field")

            raw_article_count = len(result["articles"])
            self.logger.info(f"  → Found {raw_article_count} articles in JSON")

            # 添加默认值
            if "status" not in result:
                result["status"] = "success"

            if "total_count" not in result:
                result["total_count"] = len(result["articles"])

            if "sources" not in result:
                result["sources"] = self._count_sources(result["articles"])

            # 执行去重（保险机制）
            self.logger.info("  → Deduplicating articles...")
            result["articles"] = self._deduplicate_articles(result["articles"])
            result["total_count"] = len(result["articles"])

            self.logger.info(f"  ✓ Parsed {result['total_count']} unique articles successfully")
            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.debug(f"Raw content: {text_content}")
            raise ValueError(f"Invalid JSON output from agent: {e}")

        except Exception as e:
            self.logger.error(f"Failed to parse agent output: {e}")
            raise

    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重文章列表（基于 URL）

        Args:
            articles: 文章列表

        Returns:
            List[Dict]: 去重后的文章列表
        """
        seen_urls = set()
        unique_articles = []

        for article in articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        removed_count = len(articles) - len(unique_articles)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} duplicate articles")

        return unique_articles

    def _sanitize_json_string(self, text: str) -> str:
        """
        修復 LLM 生成的 JSON 中常見的轉義問題

        Args:
            text: 原始 JSON 字串

        Returns:
            str: 修復後的 JSON 字串
        """
        import re

        # 修復無效的轉義序列
        # JSON 只允許: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
        # LLM 有時會生成 \x, \', 或其他無效轉義

        # 修復常見問題：
        # 1. \' -> ' （單引號不需要在 JSON 中轉義）
        text = text.replace("\\'", "'")

        # 2. 修復錯誤的 URL 轉義（例如 \/ 是合法的，但有時會有問題）
        # 保持 \/ 不變

        # 3. 修復可能的非法轉義字符
        # 使用正則表達式找出所有的 \X 模式（X 不是合法的轉義字符）
        valid_escapes = {'n', 'r', 't', 'b', 'f', '\\', '"', '/', 'u'}

        def fix_escape(match):
            char = match.group(1)
            if char in valid_escapes:
                return match.group(0)  # 保持原樣
            elif char == 'u':
                return match.group(0)  # Unicode 轉義
            else:
                # 移除無效的反斜線
                return char

        # 匹配所有反斜線後跟著一個字符的模式
        text = re.sub(r'\\([^u])', fix_escape, text)

        return text

    def _count_sources(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        统计文章来源

        Args:
            articles: 文章列表

        Returns:
            Dict[str, int]: 来源统计 {"rss": 10, "google_search_grounding": 5}
        """
        sources = {}
        for article in articles:
            source = article.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        return sources


# ============================================================================
# Convenience Function
# ============================================================================

def collect_articles() -> Dict[str, Any]:
    """
    便捷函数：快速收集文章

    这是一个简化的接口，用于快速运行 Scout Agent。

    Returns:
        dict: 收集结果

    Example:
        >>> from src.agents.scout_agent import collect_articles
        >>> result = collect_articles()
        >>> print(f"Collected {result['total_count']} articles")
    """
    runner = ScoutAgentRunner()
    return runner.collect_articles()


# ============================================================================
# Main - for testing
# ============================================================================

if __name__ == "__main__":
    # 快速测试
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🚀 Testing Scout Agent...\n")

    try:
        result = collect_articles()

        print(f"\n{'='*60}")
        print(f"Status: {result['status']}")
        print(f"Total Articles: {result['total_count']}")
        print(f"Sources: {result['sources']}")
        print(f"Collected At: {result['collected_at']}")
        print(f"{'='*60}\n")

        if result['articles']:
            print("Sample Article:")
            sample = result['articles'][0]
            print(f"  Title: {sample.get('title', 'N/A')}")
            print(f"  URL: {sample.get('url', 'N/A')}")
            print(f"  Source: {sample.get('source', 'N/A')}")
            print(f"  Published: {sample.get('published_at', 'N/A')}")

        sys.exit(0 if result['status'] == 'success' else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
