"""
InsightCosmos Analyst Agent

Analyzes article content using LLM, extracts insights, and scores priority.

Classes:
    AnalystAgentRunner: Main runner for article analysis workflow

Functions:
    create_analyst_agent: Factory function to create configured Analyst Agent
    analyze_article: Convenience function for single article analysis

Usage:
    from src.agents.analyst_agent import create_analyst_agent, AnalystAgentRunner
    from src.memory.database import Database
    from src.memory.article_store import ArticleStore
    from src.memory.embedding_store import EmbeddingStore

    # Create agent
    agent = create_analyst_agent(
        user_name="Ray",
        user_interests="AI, Robotics, Multi-Agent Systems"
    )

    # Create runner
    db = Database.from_config(config)
    article_store = ArticleStore(db)
    embedding_store = EmbeddingStore(db)

    runner = AnalystAgentRunner(
        agent=agent,
        article_store=article_store,
        embedding_store=embedding_store
    )

    # Analyze articles
    result = await runner.analyze_article(article_id=123)
    batch_results = await runner.analyze_batch([1, 2, 3, 4, 5])
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import re
import logging
from datetime import datetime
import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from google.genai import Client

from src.memory.article_store import ArticleStore
from src.memory.embedding_store import EmbeddingStore
from src.utils.logger import Logger
from src.utils.config import Config


def create_analyst_agent(
    model: str = "gemini-2.5-flash",
    user_name: str = "Ray",
    user_interests: str = "AI, Robotics, Multi-Agent Systems",
    prompt_path: Optional[Path] = None
) -> LlmAgent:
    """
    Create Analyst Agent

    Creates a configured LlmAgent for analyzing articles and extracting insights.

    Args:
        model: Gemini model name (default: "gemini-2.5-flash")
        user_name: User name for personalized analysis
        user_interests: User interests for relevance scoring
        prompt_path: Path to prompt template file (optional)

    Returns:
        LlmAgent: Configured Analyst Agent

    Example:
        >>> agent = create_analyst_agent()
        >>> # Agent is ready for analysis
        >>> agent = create_analyst_agent(
        ...     model="gemini-2.5-pro",
        ...     user_name="Alice",
        ...     user_interests="Machine Learning, Computer Vision"
        ... )
    """
    # Load prompt template
    if prompt_path is None:
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "analyst_prompt.txt"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        instruction = f.read()

    # Replace template variables
    instruction = instruction.replace("{{USER_NAME}}", user_name)
    instruction = instruction.replace("{{USER_INTERESTS}}", user_interests)

    # Create agent
    agent = LlmAgent(
        name="AnalystAgent",
        model=model,
        description="Analyzes AI and Robotics articles, extracts insights, and scores priority.",
        instruction=instruction,
        output_key="analysis_result"
    )

    return agent


class AnalystAgentRunner:
    """
    Analyst Agent Runner

    Orchestrates the article analysis workflow:
    1. Fetches articles from ArticleStore
    2. Invokes AnalystAgent for analysis
    3. Generates embeddings
    4. Stores results in ArticleStore and EmbeddingStore

    Attributes:
        agent (LlmAgent): Analyst Agent instance
        article_store (ArticleStore): Article storage
        embedding_store (EmbeddingStore): Embedding storage
        logger (Logger): Logger instance
        session_service (InMemorySessionService): ADK session service
        app_name (str): ADK application name

    Example:
        >>> runner = AnalystAgentRunner(agent, article_store, embedding_store)
        >>> result = await runner.analyze_article(123)
        >>> print(result['analysis']['priority_score'])
        0.85
    """

    def __init__(
        self,
        agent: LlmAgent,
        article_store: ArticleStore,
        embedding_store: EmbeddingStore,
        logger: Optional[logging.Logger] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize AnalystAgentRunner

        Args:
            agent: Analyst Agent instance
            article_store: Article storage
            embedding_store: Embedding storage
            logger: Logger instance (optional)
            config: Configuration instance (optional)
        """
        self.agent = agent
        self.article_store = article_store
        self.embedding_store = embedding_store
        self.logger = logger or Logger.get_logger("AnalystAgentRunner")
        self.config = config or Config()

        # ADK Runner setup
        self.session_service = InMemorySessionService()
        self.app_name = "insightcosmos_analyst"

        # Embedding client
        self.genai_client = Client(api_key=self.config.GOOGLE_API_KEY)

    async def analyze_article(
        self,
        article_id: int,
        skip_if_analyzed: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze single article

        Args:
            article_id: Article ID
            skip_if_analyzed: Skip if article already analyzed (default: True)

        Returns:
            dict: Analysis result
            {
                "status": "success" | "error" | "skipped",
                "article_id": int,
                "analysis": {...},
                "embedding_id": int
            }

        Raises:
            ValueError: If article not found or content empty
            RuntimeError: If LLM invocation fails

        Example:
            >>> result = await runner.analyze_article(123)
            >>> if result['status'] == 'success':
            ...     print(f"Priority: {result['analysis']['priority_score']}")
        """
        try:
            # 1. Fetch article
            article = self.article_store.get_by_id(article_id)
            if not article:
                raise ValueError(f"Article not found: {article_id}")

            # Skip if already analyzed
            if skip_if_analyzed and article.get('status') == 'analyzed':
                self.logger.info(f"Article {article_id} already analyzed, skipping")
                return {
                    "status": "skipped",
                    "article_id": article_id,
                    "message": "Article already analyzed"
                }

            # Check content
            if not article.get('content'):
                raise ValueError(f"Article content is empty: {article_id}")

            self.logger.info(f"Analyzing article {article_id}: {article['title'][:50]}...")

            # 2. Prepare input
            user_input = self._prepare_input(article)

            # 3. Invoke LLM
            response_text = await self._invoke_llm(article_id, user_input)

            # 4. Parse analysis
            analysis = self._parse_analysis(response_text)

            # 5. Generate embedding
            embedding_text = self._prepare_embedding_text(analysis)
            embedding = await self._generate_embedding(embedding_text)

            # 6. Store results
            self.article_store.update_analysis(
                article_id=article_id,
                analysis=analysis,
                priority_score=analysis['priority_score']
            )

            # 7. Store embedding
            embedding_id = None
            if embedding:
                import numpy as np
                embedding_id = self.embedding_store.store(
                    article_id=article_id,
                    embedding=np.array(embedding),
                    model=self.config.EMBEDDING_MODEL
                )

            self.logger.info(
                f"Successfully analyzed article {article_id} "
                f"(priority: {analysis['priority_score']:.2f})"
            )

            return {
                "status": "success",
                "article_id": article_id,
                "analysis": analysis,
                "embedding_id": embedding_id,
                "analyzed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze article {article_id}: {e}")
            return {
                "status": "error",
                "article_id": article_id,
                "error_message": str(e),
                "suggestion": self._get_error_suggestion(e)
            }

    async def analyze_batch(
        self,
        article_ids: List[int],
        max_concurrent: int = 5,
        skip_if_analyzed: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze batch of articles

        Args:
            article_ids: List of article IDs
            max_concurrent: Maximum concurrent analyses (default: 5)
            skip_if_analyzed: Skip already analyzed articles (default: True)

        Returns:
            dict: Batch analysis results
            {
                "total": int,
                "succeeded": int,
                "failed": int,
                "skipped": int,
                "results": List[dict]
            }

        Example:
            >>> results = await runner.analyze_batch([1, 2, 3, 4, 5])
            >>> print(f"Success: {results['succeeded']}/{results['total']}")
        """
        self.logger.info(f"Starting batch analysis of {len(article_ids)} articles")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _analyze_with_semaphore(article_id: int) -> Dict[str, Any]:
            async with semaphore:
                return await self.analyze_article(article_id, skip_if_analyzed)

        # Run analyses concurrently
        results = await asyncio.gather(
            *[_analyze_with_semaphore(aid) for aid in article_ids],
            return_exceptions=True
        )

        # Process results
        succeeded = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'success')
        failed = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'error')
        skipped = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'skipped')

        self.logger.info(
            f"Batch analysis complete: {succeeded} succeeded, {failed} failed, {skipped} skipped"
        )

        return {
            "total": len(article_ids),
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
            "results": [r for r in results if isinstance(r, dict)]
        }

    async def analyze_pending(
        self,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Analyze all pending articles (status='pending')

        Args:
            limit: Maximum number of articles to analyze (default: 50)

        Returns:
            dict: Batch analysis results

        Example:
            >>> results = await runner.analyze_pending(limit=20)
            >>> print(f"Analyzed {results['succeeded']} articles")
        """
        self.logger.info(f"Fetching pending articles (limit={limit})")

        # Get pending articles
        pending_articles = self.article_store.get_by_status('pending', limit=limit)
        article_ids = [a['id'] for a in pending_articles]

        if not article_ids:
            self.logger.info("No pending articles found")
            return {
                "total": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 0,
                "results": []
            }

        self.logger.info(f"Found {len(article_ids)} pending articles")

        # Analyze batch
        return await self.analyze_batch(article_ids, skip_if_analyzed=False)

    def _prepare_input(self, article: Dict[str, Any]) -> str:
        """
        Prepare LLM input text

        Args:
            article: Article dictionary

        Returns:
            str: Formatted input text
        """
        # Limit content length to avoid token overflow
        max_content_length = 10000
        content = article.get('content', '')
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[內容已截斷...]"

        return f"""請分析以下文章：

標題：{article.get('title', 'Unknown')}
URL：{article.get('url', 'Unknown')}
來源：{article.get('source_name', 'Unknown')} ({article.get('source', 'unknown')})
發布時間：{article.get('published_at', 'Unknown')}

內容：
{content}

請按照指令格式提供結構化分析結果。
"""

    async def _invoke_llm(self, article_id: int, user_input: str) -> str:
        """
        Invoke LLM for analysis

        Args:
            article_id: Article ID (for session ID)
            user_input: Input text

        Returns:
            str: LLM response text

        Raises:
            RuntimeError: If LLM invocation fails
        """
        try:
            # Create runner
            runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service
            )

            # Create session
            session_id = f"analysis_{article_id}_{datetime.utcnow().timestamp()}"
            await self.session_service.create_session(
                app_name=self.app_name,
                user_id="system",
                session_id=session_id
            )

            # Run agent
            response_text = ""
            async for event in runner.run_async(
                user_id="system",
                session_id=session_id,
                new_message=Content(parts=[Part(text=user_input)], role="user")
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    break

            if not response_text:
                raise RuntimeError("LLM returned empty response")

            return response_text

        except Exception as e:
            self.logger.error(f"LLM invocation failed: {e}")
            raise RuntimeError(f"LLM invocation failed: {e}")

    def _parse_analysis(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response JSON

        Args:
            response_text: LLM response text (may be wrapped in markdown)

        Returns:
            dict: Parsed analysis result

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Remove markdown wrapper if present
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text

            # Parse JSON
            analysis = json.loads(json_str)

            # Validate required fields
            required_fields = [
                'summary', 'key_insights', 'tech_stack',
                'category', 'trends', 'relevance_score',
                'priority_score', 'reasoning'
            ]

            for field in required_fields:
                if field not in analysis:
                    self.logger.warning(f"Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")

            # Validate scores
            if not (0.0 <= analysis['relevance_score'] <= 1.0):
                self.logger.warning(f"Invalid relevance_score: {analysis['relevance_score']}")
                analysis['relevance_score'] = max(0.0, min(1.0, analysis['relevance_score']))

            if not (0.0 <= analysis['priority_score'] <= 1.0):
                self.logger.warning(f"Invalid priority_score: {analysis['priority_score']}")
                analysis['priority_score'] = max(0.0, min(1.0, analysis['priority_score']))

            return analysis

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse analysis JSON: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            # Return default analysis
            return self._get_default_analysis()

    def _get_default_analysis(self) -> Dict[str, Any]:
        """
        Get default analysis result (when LLM output is invalid)

        Returns:
            dict: Default analysis structure
        """
        return {
            "summary": "無法生成摘要（LLM 輸出格式錯誤）",
            "key_insights": [],
            "tech_stack": [],
            "category": "Unknown",
            "trends": [],
            "relevance_score": 0.0,
            "priority_score": 0.0,
            "reasoning": "LLM 返回格式無效，使用預設分析結果。"
        }

    def _prepare_embedding_text(self, analysis: Dict[str, Any]) -> str:
        """
        Prepare text for embedding generation

        Combines summary and key insights for semantic representation.

        Args:
            analysis: Analysis result

        Returns:
            str: Text for embedding
        """
        text_parts = [analysis.get('summary', '')]

        insights = analysis.get('key_insights', [])
        if insights:
            text_parts.extend(insights)

        return ' '.join(text_parts)

    async def _generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> Optional[List[float]]:
        """
        Generate embedding vector

        Args:
            text: Text to embed
            model: Embedding model name (optional)

        Returns:
            List[float] | None: Embedding vector or None if failed
        """
        if not text or not text.strip():
            self.logger.warning("Empty text for embedding, skipping")
            return None

        try:
            model = model or self.config.EMBEDDING_MODEL
            result = self.genai_client.models.embed_content(
                model=model,
                contents=text
            )

            embedding = result.embeddings[0].values
            self.logger.debug(f"Generated embedding (dim={len(embedding)})")

            return embedding

        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            # Return None instead of zero vector to indicate failure
            return None

    def _get_error_suggestion(self, error: Exception) -> str:
        """
        Get error suggestion based on exception type

        Args:
            error: Exception instance

        Returns:
            str: Suggestion for fixing the error
        """
        error_str = str(error).lower()

        if "not found" in error_str:
            return "檢查文章 ID 是否正確，或文章是否已被刪除。"
        elif "empty" in error_str or "content" in error_str:
            return "文章內容為空，建議檢查 Content Extractor 是否正常運作。"
        elif "quota" in error_str or "limit" in error_str:
            return "API 配額已用盡，請稍後再試或檢查配額設定。"
        elif "timeout" in error_str:
            return "請求超時，建議減少文章長度或增加超時時間。"
        elif "json" in error_str or "parse" in error_str:
            return "LLM 返回格式錯誤，可能需要優化 Prompt 或檢查模型輸出。"
        else:
            return "未知錯誤，請檢查日誌以獲取更多資訊。"


# Convenience function
async def analyze_article(
    article_id: int,
    config: Optional[Config] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze single article

    Args:
        article_id: Article ID
        config: Configuration instance (optional)

    Returns:
        dict: Analysis result

    Example:
        >>> from src.agents.analyst_agent import analyze_article
        >>> result = await analyze_article(123)
        >>> print(result['analysis']['priority_score'])
    """
    from src.memory.database import Database

    config = config or Config()

    # Create dependencies
    agent = create_analyst_agent(
        user_name=config.USER_NAME,
        user_interests=config.USER_INTERESTS
    )

    db = Database.from_config(config)
    article_store = ArticleStore(db)
    embedding_store = EmbeddingStore(db)

    runner = AnalystAgentRunner(
        agent=agent,
        article_store=article_store,
        embedding_store=embedding_store,
        config=config
    )

    return await runner.analyze_article(article_id)
