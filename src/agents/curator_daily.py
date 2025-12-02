"""
InsightCosmos Curator Daily Agent

Generates daily AI and Robotics digest from analyzed articles.

This module provides:
- CuratorDailyAgent: LLM Agent for curating daily digest
- CuratorDailyRunner: Runner for executing the curator workflow
- Helper functions for digest generation and email sending

The Curator Daily Agent:
1. Fetches top priority analyzed articles from Memory
2. Uses LLM to generate structured digest
3. Formats digest into HTML and plain text emails
4. Sends digest via email

Architecture:
    ArticleStore (Memory)
        ↓
    CuratorDailyAgent (LLM curation)
        ↓
    DigestFormatter (HTML + Text)
        ↓
    EmailSender (SMTP delivery)

Usage:
    from src.agents.curator_daily import CuratorDailyRunner, create_curator_agent
    from src.utils.config import Config
    from src.memory.database import Database
    from src.memory.article_store import ArticleStore

    # Initialize
    config = Config.from_env()
    db = Database.from_config(config)
    article_store = ArticleStore(db)

    # Create agent
    agent = create_curator_agent(config)

    # Run curator
    runner = CuratorDailyRunner(
        agent=agent,
        article_store=article_store,
        config=config
    )

    result = runner.generate_and_send_digest(
        recipient_email="ray@example.com",
        max_articles=10
    )
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
import json
import re

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

from src.memory.article_store import ArticleStore
from src.tools.email_sender import EmailSender, EmailConfig
from src.tools.digest_formatter import DigestFormatter
from src.utils.config import Config
from src.utils.logger import Logger


def create_curator_agent(config: Config) -> LlmAgent:
    """
    Create Curator Daily Agent

    Args:
        config: Application configuration

    Returns:
        LlmAgent: Configured Curator Daily Agent

    Example:
        >>> config = Config.from_env()
        >>> agent = create_curator_agent(config)
    """
    # Load prompt template
    prompt_template = _load_prompt_template()

    # Replace template variables
    instruction = prompt_template.replace('{{USER_NAME}}', config.user_name)
    instruction = instruction.replace('{{USER_INTERESTS}}', config.user_interests)

    # Create agent
    agent = LlmAgent(
        name="CuratorDailyAgent",
        model="gemini-2.5-flash",
        description="Curates daily AI and Robotics digest from analyzed articles",
        instruction=instruction,
        tools=[]  # No tools needed - LLM only generates structured content
    )

    return agent


def _load_prompt_template() -> str:
    """
    Load prompt template from file

    Returns:
        str: Prompt template content

    Raises:
        FileNotFoundError: If prompt template file not found
    """
    import os
    from pathlib import Path

    # Get project root (assumes this file is in src/agents/)
    project_root = Path(__file__).parent.parent.parent
    prompt_path = project_root / 'prompts' / 'daily_prompt.txt'

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


class CuratorDailyRunner:
    """
    Curator Daily Agent Runner

    Orchestrates the daily digest generation and email sending workflow.

    Workflow:
        1. Fetch top priority analyzed articles from ArticleStore
        2. Invoke LLM to generate structured digest
        3. Format digest into HTML and plain text
        4. Send email via SMTP

    Example:
        >>> runner = CuratorDailyRunner(agent, article_store, config)
        >>> result = runner.generate_and_send_digest(
        ...     recipient_email="ray@example.com",
        ...     max_articles=10
        ... )
        >>> print(result['status'])
        success
    """

    def __init__(
        self,
        agent: LlmAgent,
        article_store: ArticleStore,
        config: Config
    ):
        """
        Initialize CuratorDailyRunner

        Args:
            agent: Curator Daily Agent
            article_store: Article storage instance
            config: Application configuration
        """
        self.agent = agent
        self.article_store = article_store
        self.config = config
        self.logger = Logger.get_logger(__name__)

        # Initialize formatter and email sender
        self.formatter = DigestFormatter()
        self.email_sender = self._create_email_sender()

        # Initialize ADK components
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name="InsightCosmos",
            agent=self.agent,
            session_service=self.session_service
        )

    def _create_email_sender(self) -> EmailSender:
        """Create EmailSender from config"""
        email_config = EmailConfig(
            smtp_host=self.config.smtp_host,
            smtp_port=self.config.smtp_port,
            sender_email=self.config.email_account,
            sender_password=self.config.email_password,
            use_tls=self.config.smtp_use_tls
        )
        return EmailSender(email_config)

    def generate_and_send_digest(
        self,
        recipient_email: str,
        max_articles: int = 10,
        digest_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate daily digest and send via email

        Args:
            recipient_email: Recipient email address
            max_articles: Maximum number of articles to include (default: 10)
            digest_date: Date for the digest (default: today)

        Returns:
            dict: {
                "status": "success" | "error",
                "digest": dict (if success),
                "email_result": dict (if success),
                "error": str (if error)
            }

        Example:
            >>> result = runner.generate_and_send_digest(
            ...     recipient_email="ray@example.com",
            ...     max_articles=10
            ... )
        """
        try:
            # Step 1: Fetch analyzed articles
            self.logger.info(f"Fetching top {max_articles} analyzed articles...")
            articles = self.fetch_analyzed_articles(max_articles)

            if not articles:
                self.logger.warning("No analyzed articles found")
                return {
                    "status": "error",
                    "error": "No analyzed articles available for digest"
                }

            self.logger.info(f"Fetched {len(articles)} articles")

            # Step 2: Generate digest
            self.logger.info("Generating daily digest...")
            digest = self.generate_digest(articles, digest_date)

            if not digest:
                self.logger.error("Failed to generate digest")
                return {
                    "status": "error",
                    "error": "LLM failed to generate valid digest"
                }

            self.logger.info("Digest generated successfully")

            # Step 3: Format digest
            self.logger.info("Formatting digest for email...")
            html_body = self.formatter.format_html(digest)
            text_body = self.formatter.format_text(digest)

            # Step 4: Send email
            self.logger.info(f"Sending digest to {recipient_email}...")
            email_result = self.email_sender.send(
                to_email=recipient_email,
                subject=f"InsightCosmos Daily Digest - {digest['date']}",
                html_body=html_body,
                text_body=text_body
            )

            if email_result['status'] == 'success':
                self.logger.info("✅ Daily digest sent successfully")
                return {
                    "status": "success",
                    "digest": digest,
                    "email_result": email_result
                }
            else:
                self.logger.error(f"Failed to send email: {email_result.get('error')}")
                return {
                    "status": "error",
                    "error": f"Email sending failed: {email_result.get('error')}",
                    "digest": digest,
                    "email_result": email_result
                }

        except Exception as e:
            self.logger.error(f"Error in generate_and_send_digest: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def fetch_analyzed_articles(self, max_articles: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch top priority analyzed articles from ArticleStore

        Args:
            max_articles: Maximum number of articles to fetch

        Returns:
            List[dict]: List of article dictionaries

        Example:
            >>> articles = runner.fetch_analyzed_articles(max_articles=10)
        """
        try:
            # Fetch more articles than needed to allow for deduplication
            articles = self.article_store.get_top_priority(
                limit=max_articles * 3,  # Fetch 3x to have buffer for dedup
                status='analyzed'
            )

            # Ensure all articles have required fields
            processed_articles = []
            for article in articles:
                # Parse tags if it's a string or list
                tags = article.get('tags', '')
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',') if t.strip()]
                elif tags is None:
                    tags = []

                # Extract analysis data (key_insights and priority_reasoning)
                analysis = article.get('analysis', {}) or {}

                # Parse key_insights from analysis
                key_insights = analysis.get('key_insights', [])
                if isinstance(key_insights, str):
                    try:
                        key_insights = json.loads(key_insights)
                    except json.JSONDecodeError:
                        # Try splitting by comma or newline
                        key_insights = [
                            k.strip()
                            for k in re.split(r'[,\n]', key_insights)
                            if k.strip()
                        ]

                # Get priority_reasoning from analysis
                priority_reasoning = analysis.get('priority_reasoning', '')

                # Get title - prefer analysis summary for google_search_grounding articles
                # (their original titles are often garbled URL encodings)
                original_title = article.get('title', 'Untitled')
                analysis_summary = analysis.get('summary', '')

                # Check if title looks like garbled text (contains many uppercase/numbers pattern)
                is_garbled = (
                    len(original_title) > 50 and
                    original_title.startswith('Auziyq')
                ) or article.get('source') == 'google_search_grounding'

                # Use analysis summary as title if original is garbled, truncate to first sentence
                if is_garbled and analysis_summary:
                    # Take first sentence or first 80 chars
                    title = analysis_summary.split('。')[0][:80]
                    if len(analysis_summary) > 80:
                        title += '...'
                else:
                    title = original_title

                processed_article = {
                    'id': article.get('id'),
                    'title': title,
                    'url': article.get('url', ''),
                    'summary': analysis_summary or article.get('summary', ''),
                    'key_insights': key_insights,
                    'priority_score': article.get('priority_score', 0.0),
                    'priority_reasoning': priority_reasoning,
                    'tags': tags,
                    'published_at': article.get('published_at'),
                    'source_name': article.get('source_name', 'Unknown')
                }

                processed_articles.append(processed_article)

            # Deduplicate articles with similar content
            deduplicated = self._deduplicate_articles(processed_articles, max_articles)
            self.logger.info(f"Deduplicated {len(processed_articles)} -> {len(deduplicated)} articles")

            return deduplicated

        except Exception as e:
            self.logger.error(f"Error fetching analyzed articles: {e}")
            return []

    def _deduplicate_articles(
        self,
        articles: List[Dict[str, Any]],
        max_count: int
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate articles based on summary similarity

        Uses simple keyword overlap to detect similar articles.
        Keeps higher priority article when duplicates found.

        Args:
            articles: List of processed articles (already sorted by priority)
            max_count: Maximum number of articles to return

        Returns:
            List[dict]: Deduplicated article list
        """
        if not articles:
            return []

        deduplicated = []
        seen_keywords = []  # List of keyword sets for each kept article

        for article in articles:
            if len(deduplicated) >= max_count:
                break

            # Extract keywords from summary (use first 150 chars for better dedup)
            summary = article.get('summary', '')[:150]  # Truncate to focus on core topic
            title = article.get('title', '')
            combined_text = f"{title} {summary}".lower()

            # Extract Chinese/English words and significant terms
            # For Chinese: extract 2-4 character phrases for better matching
            chinese_phrases = re.findall(r'[\u4e00-\u9fff]{2,4}', combined_text)
            english_words = re.findall(r'[A-Za-z]{3,}', combined_text)
            keywords = set(chinese_phrases + english_words)

            # Add important domain terms as single keywords for better matching
            domain_terms = ['vla', 'vlm', 'llm', 'amr', 'agv', 'cobot', 'humanoid',
                           '機器人', '協作', '自主', '導航', '視覺', '語言', '動作']
            for term in domain_terms:
                if term in combined_text:
                    keywords.add(f"__domain_{term}")  # Prefix to give more weight

            # Check similarity with already selected articles
            is_duplicate = False
            for seen in seen_keywords:
                if len(keywords) > 0 and len(seen) > 0:
                    # Calculate Jaccard similarity
                    intersection = len(keywords & seen)
                    union = len(keywords | seen)
                    similarity = intersection / union if union > 0 else 0

                    # If > 35% similar, consider as duplicate (lowered from 40%)
                    if similarity > 0.35:
                        is_duplicate = True
                        self.logger.info(
                            f"Skipping duplicate article: {article.get('id')} - "
                            f"{article.get('title', '')[:40]}... (similarity: {similarity:.2f})"
                        )
                        break

            if not is_duplicate:
                deduplicated.append(article)
                seen_keywords.append(keywords)

        return deduplicated

    def generate_digest(
        self,
        articles: List[Dict[str, Any]],
        digest_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate daily digest using LLM

        Args:
            articles: List of article dictionaries
            digest_date: Date for the digest (default: today)

        Returns:
            Optional[dict]: Digest data or None if generation failed

        Example:
            >>> digest = runner.generate_digest(articles)
        """
        if not articles:
            self.logger.warning("No articles provided for digest generation")
            return None

        # Prepare digest date
        if digest_date is None:
            digest_date = date.today()

        date_str = digest_date.strftime('%Y-%m-%d')

        # Prepare LLM input
        articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
        user_input = f"""請根據以下文章列表生成今日摘要（日期: {date_str}）：

```json
{articles_json}
```

請以 JSON 格式回覆。"""

        # Invoke LLM
        try:
            response = self._invoke_llm(user_input)

            if not response:
                self.logger.error("LLM returned empty response")
                return None

            # Parse digest JSON
            digest = self._parse_digest_json(response)

            if not digest:
                self.logger.error("Failed to parse digest JSON from LLM response")
                return None

            # Ensure date is set
            if 'date' not in digest:
                digest['date'] = date_str

            return digest

        except Exception as e:
            self.logger.error(f"Error generating digest: {e}")
            return None

    async def _invoke_llm_async(self, user_input: str) -> Optional[str]:
        """
        Invoke LLM and get response (async)

        Args:
            user_input: User input message

        Returns:
            Optional[str]: LLM response or None if failed
        """
        try:
            # Create session
            session_id = "curator_session"
            user_id = "ray"
            await self.session_service.create_session(
                app_name="InsightCosmos",
                user_id=user_id,
                session_id=session_id
            )

            # Run agent (use run_async with correct Content object)
            response_text = ""
            events_gen = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=Content(parts=[Part(text=user_input)], role="user")
            )

            async for event in events_gen:
                # Check if this is final response and extract text
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    break

            if not response_text:
                self.logger.warning("LLM returned empty response")
                return None

            return response_text.strip()

        except Exception as e:
            import traceback
            self.logger.error(f"Error invoking LLM: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _invoke_llm(self, user_input: str) -> Optional[str]:
        """
        Invoke LLM and get response (sync wrapper)

        Args:
            user_input: User input message

        Returns:
            Optional[str]: LLM response or None if failed
        """
        import asyncio
        try:
            return asyncio.run(self._invoke_llm_async(user_input))
        except Exception as e:
            self.logger.error(f"Error in sync wrapper: {e}")
            return None

    def _parse_digest_json(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse digest JSON from LLM response

        Supports:
        - Plain JSON
        - JSON wrapped in Markdown code blocks (```json ... ```)

        Args:
            response: LLM response text

        Returns:
            Optional[dict]: Parsed digest data or None if parsing failed
        """
        try:
            # Try parsing as plain JSON first
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass

            # Try extracting JSON from Markdown code block
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            # Try extracting JSON from generic code block
            code_match = re.search(r'```\s*\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                json_str = code_match.group(1)
                return json.loads(json_str)

            self.logger.error("No valid JSON found in LLM response")
            return None

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing digest JSON: {e}")
            return None


# Convenience function
def generate_daily_digest(
    config: Config,
    recipient_email: str,
    max_articles: int = 10
) -> Dict[str, Any]:
    """
    Convenience function to generate and send daily digest

    Args:
        config: Application configuration
        recipient_email: Recipient email address
        max_articles: Maximum number of articles (default: 10)

    Returns:
        dict: Result of digest generation and sending

    Example:
        >>> from src.utils.config import Config
        >>> config = Config.from_env()
        >>> result = generate_daily_digest(
        ...     config=config,
        ...     recipient_email="ray@example.com",
        ...     max_articles=10
        ... )
    """
    from src.memory.database import Database
    from src.memory.article_store import ArticleStore

    # Initialize components
    db = Database.from_config(config)
    article_store = ArticleStore(db)
    agent = create_curator_agent(config)

    # Create runner
    runner = CuratorDailyRunner(
        agent=agent,
        article_store=article_store,
        config=config
    )

    # Generate and send digest
    return runner.generate_and_send_digest(
        recipient_email=recipient_email,
        max_articles=max_articles
    )
