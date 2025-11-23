"""
Integration Tests for Analyst Agent

Tests the full workflow of AnalystAgent with real database and mocked LLM.

Test Coverage:
    - End-to-end article analysis
    - Batch analysis
    - Memory integration (ArticleStore + EmbeddingStore)
    - Error handling in real scenarios

Run:
    pytest tests/integration/test_analyst_integration.py -v
    pytest tests/integration/test_analyst_integration.py::TestAnalystMemoryIntegration -v

Manual Tests (require GOOGLE_API_KEY):
    pytest tests/integration/test_analyst_integration.py::TestRealLLMAnalysis -v -m manual
"""

import pytest
import json
import tempfile
import asyncio
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime

from src.agents.analyst_agent import create_analyst_agent, AnalystAgentRunner
from src.memory.database import Database
from src.memory.article_store import ArticleStore
from src.memory.embedding_store import EmbeddingStore
from src.utils.config import Config


class TestAnalystMemoryIntegration:
    """Test AnalystAgent integration with real Memory layer"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
        db_path = temp_file.name
        temp_file.close()

        # Create database with minimal config
        config = Config(
            google_api_key="test_key",
            email_account="test@example.com",
            email_password="test_password",
            database_path=db_path
        )

        db = Database.from_config(config)
        # Initialize tables
        db.init_db()

        yield db, config

        # Cleanup
        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def article_store(self, temp_db):
        """Create ArticleStore with temp database"""
        db, config = temp_db
        return ArticleStore(db)

    @pytest.fixture
    def embedding_store(self, temp_db):
        """Create EmbeddingStore with temp database"""
        db, config = temp_db
        return EmbeddingStore(db)

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent"""
        agent = Mock()
        agent.name = "AnalystAgent"
        agent.model = "gemini-2.5-flash"
        return agent

    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = Mock()
        config.GOOGLE_API_KEY = "test_key"
        config.EMBEDDING_MODEL = "text-embedding-004"
        config.USER_NAME = "Ray"
        config.USER_INTERESTS = "AI, Robotics"
        return config

    @pytest.fixture
    def runner(self, mock_agent, article_store, embedding_store, mock_config):
        """Create runner with real stores"""
        return AnalystAgentRunner(
            agent=mock_agent,
            article_store=article_store,
            embedding_store=embedding_store,
            config=mock_config
        )

    @pytest.fixture
    def sample_article_id(self, article_store):
        """Create a sample article and return its ID"""
        article_id = article_store.create(
            url="https://example.com/test-article",
            title="Test Article: Multi-Agent Systems with Google ADK",
            content="""
            This is a detailed article about building multi-agent systems using Google's
            Agent Development Kit (ADK). The article covers Sequential, Parallel, and Loop
            agents, along with best practices for agent orchestration.

            Key topics include:
            - Agent architecture design
            - Tool integration
            - Memory management
            - Evaluation frameworks

            The article provides code examples in Python and discusses real-world use cases
            in AI and Robotics applications.
            """,
            summary="A comprehensive guide to multi-agent systems with Google ADK.",
            source="rss",
            source_name="AI Research Blog",
            published_at=datetime(2025, 11, 23, 10, 0, 0)
        )
        return article_id

    @pytest.mark.asyncio
    async def test_analyze_article_stores_in_database(
        self,
        runner,
        article_store,
        embedding_store,
        sample_article_id
    ):
        """Test that analysis results are correctly stored in database"""
        # Mock LLM response
        mock_analysis = {
            "summary": "Comprehensive guide to multi-agent systems.",
            "key_insights": [
                "ADK supports Sequential, Parallel, Loop agents",
                "Tool integration is crucial for agent capabilities"
            ],
            "tech_stack": ["Google ADK", "Python", "Gemini"],
            "category": "AI Agent",
            "trends": ["Multi-Agent", "Agent Orchestration"],
            "relevance_score": 0.95,
            "priority_score": 0.90,
            "reasoning": "Highly relevant to Ray's interest in Multi-Agent Systems."
        }

        mock_llm_response = json.dumps(mock_analysis)

        # Mock LLM and embedding
        with patch.object(runner, '_invoke_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response

            with patch.object(runner, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
                test_embedding = [0.1] * 768
                mock_embed.return_value = test_embedding

                # Run analysis
                result = await runner.analyze_article(sample_article_id, skip_if_analyzed=False)

                # Verify result
                assert result['status'] == 'success'
                assert result['article_id'] == sample_article_id

                # Verify article was updated in database
                article = article_store.get_by_id(sample_article_id)
                assert article is not None
                assert article['status'] == 'analyzed'
                assert article['priority_score'] == 0.90
                assert article['analysis'] is not None
                assert article['analysis']['summary'] == mock_analysis['summary']

                # Verify embedding was stored
                assert result['embedding_id'] is not None
                embedding = embedding_store.get_by_article_id(sample_article_id)
                assert embedding is not None
                assert embedding['dimension'] == 768

    @pytest.mark.asyncio
    async def test_analyze_batch_articles(
        self,
        runner,
        article_store,
        embedding_store
    ):
        """Test batch analysis of multiple articles"""
        # Create multiple test articles
        article_ids = []
        for i in range(3):
            article_id = article_store.create(
                url=f"https://example.com/article-{i}",
                title=f"Test Article {i}",
                content=f"Content for article {i} about AI and robotics.",
                source="rss",
                source_name="Test Blog"
            )
            article_ids.append(article_id)

        # Mock LLM and embedding
        mock_analysis = {
            "summary": "Test summary",
            "key_insights": ["Insight 1", "Insight 2"],
            "tech_stack": ["Python"],
            "category": "AI Agent",
            "trends": ["AI"],
            "relevance_score": 0.75,
            "priority_score": 0.70,
            "reasoning": "Test reasoning"
        }

        with patch.object(runner, '_invoke_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(mock_analysis)

            with patch.object(runner, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [0.1] * 768

                # Run batch analysis
                batch_result = await runner.analyze_batch(article_ids, max_concurrent=2)

                # Verify results
                assert batch_result['total'] == 3
                assert batch_result['succeeded'] == 3
                assert batch_result['failed'] == 0

                # Verify all articles were analyzed
                for article_id in article_ids:
                    article = article_store.get_by_id(article_id)
                    assert article['status'] == 'analyzed'
                    assert article['priority_score'] is not None

    @pytest.mark.asyncio
    async def test_analyze_pending_articles(
        self,
        runner,
        article_store
    ):
        """Test analyzing all pending articles"""
        # Create pending articles
        for i in range(5):
            article_store.create(
                url=f"https://example.com/pending-{i}",
                title=f"Pending Article {i}",
                content=f"Pending content {i}",
                source="rss"
            )

        # Mock LLM and embedding
        mock_analysis = {
            "summary": "Test",
            "key_insights": ["Insight"],
            "tech_stack": [],
            "category": "AI Agent",
            "trends": [],
            "relevance_score": 0.5,
            "priority_score": 0.5,
            "reasoning": "Test"
        }

        with patch.object(runner, '_invoke_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(mock_analysis)

            with patch.object(runner, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [0.1] * 768

                # Run analyze_pending
                result = await runner.analyze_pending(limit=10)

                # Verify results
                assert result['total'] == 5
                assert result['succeeded'] == 5

                # Verify no pending articles remain
                pending = article_store.get_by_status('pending', limit=100)
                assert len(pending) == 0

    @pytest.mark.asyncio
    async def test_error_handling_invalid_article(
        self,
        runner,
        article_store
    ):
        """Test error handling when article doesn't exist"""
        result = await runner.analyze_article(article_id=99999)

        assert result['status'] == 'error'
        assert 'not found' in result['error_message'].lower()
        assert result['suggestion'] is not None

    @pytest.mark.asyncio
    async def test_error_handling_llm_failure(
        self,
        runner,
        sample_article_id
    ):
        """Test error handling when LLM fails"""
        # Mock LLM to raise exception
        with patch.object(runner, '_invoke_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = RuntimeError("LLM API error")

            result = await runner.analyze_article(sample_article_id, skip_if_analyzed=False)

            assert result['status'] == 'error'
            assert 'LLM' in result['error_message'] or 'API' in result['error_message']

    @pytest.mark.asyncio
    async def test_skip_already_analyzed(
        self,
        runner,
        article_store,
        sample_article_id
    ):
        """Test that already analyzed articles are skipped"""
        # Mark article as analyzed
        article_store.update_analysis(
            article_id=sample_article_id,
            analysis={"summary": "Previous analysis"},
            priority_score=0.8
        )

        # Try to analyze again
        result = await runner.analyze_article(sample_article_id, skip_if_analyzed=True)

        assert result['status'] == 'skipped'
        assert result['article_id'] == sample_article_id


@pytest.mark.manual
class TestRealLLMAnalysis:
    """
    Manual tests that require real GOOGLE_API_KEY

    These tests are marked with @pytest.mark.manual and are skipped by default.
    Run with: pytest -m manual tests/integration/test_analyst_integration.py

    Prerequisites:
    - Set GOOGLE_API_KEY environment variable
    - Ensure internet connection
    """

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
        db_path = temp_file.name
        temp_file.close()

        config = Config(
            google_api_key=os.getenv("GOOGLE_API_KEY", "test_key"),
            email_account="test@example.com",
            email_password="test_password",
            database_path=db_path
        )

        db = Database.from_config(config)
        # Initialize tables
        db.init_db()

        yield db, config

        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def real_runner(self, temp_db):
        """Create runner with real agent and stores"""
        db, config = temp_db

        # Create real agent
        agent = create_analyst_agent(
            user_name=config.USER_NAME,
            user_interests=config.USER_INTERESTS
        )

        # Create stores
        article_store = ArticleStore(db)
        embedding_store = EmbeddingStore(db)

        return AnalystAgentRunner(
            agent=agent,
            article_store=article_store,
            embedding_store=embedding_store,
            config=config
        )

    @pytest.fixture
    def real_article_id(self, temp_db):
        """Create a real test article"""
        db, config = temp_db
        article_store = ArticleStore(db)

        return article_store.create(
            url="https://example.com/adk-test",
            title="Building Multi-Agent Systems with Google ADK",
            content="""
            Google's Agent Development Kit (ADK) provides a powerful framework for building
            sophisticated AI agents. The key components include:

            1. LlmAgent - Single agent with LLM-powered reasoning
            2. SequentialAgent - Chains agents in sequential order
            3. ParallelAgent - Runs agents concurrently
            4. LoopAgent - Iterative agent execution

            ADK also provides built-in tools like google_search, memory management with
            InMemoryMemoryService, and evaluation frameworks for quality assurance.

            Best practices include:
            - Clear agent instructions
            - Modular tool design
            - Comprehensive error handling
            - Regular evaluation and testing
            """,
            source="rss",
            source_name="ADK Documentation"
        )

    @pytest.mark.asyncio
    async def test_real_llm_analysis(self, real_runner, real_article_id):
        """
        Test real LLM analysis with Google Gemini API

        This test requires:
        - Valid GOOGLE_API_KEY
        - Internet connection
        - Gemini API quota

        Expected behavior:
        - LLM generates structured analysis
        - Embedding is created
        - Results are stored in database
        """
        result = await real_runner.analyze_article(real_article_id, skip_if_analyzed=False)

        # Verify success
        assert result['status'] == 'success', f"Analysis failed: {result.get('error_message')}"

        # Verify analysis structure
        analysis = result['analysis']
        assert 'summary' in analysis
        assert 'key_insights' in analysis
        assert 'priority_score' in analysis
        assert 'reasoning' in analysis

        # Verify scores are in valid range
        assert 0.0 <= analysis['relevance_score'] <= 1.0
        assert 0.0 <= analysis['priority_score'] <= 1.0

        # Verify embedding was created
        assert result['embedding_id'] is not None

        # Print results for manual inspection
        print("\n=== Real LLM Analysis Result ===")
        print(f"Summary: {analysis['summary']}")
        print(f"Key Insights: {analysis['key_insights']}")
        print(f"Tech Stack: {analysis['tech_stack']}")
        print(f"Category: {analysis['category']}")
        print(f"Trends: {analysis['trends']}")
        print(f"Relevance Score: {analysis['relevance_score']}")
        print(f"Priority Score: {analysis['priority_score']}")
        print(f"Reasoning: {analysis['reasoning']}")
        print("================================\n")

    @pytest.mark.asyncio
    async def test_real_embedding_generation(self, real_runner, real_article_id):
        """
        Test real embedding generation with Google Embedding API

        Verifies that embeddings are correctly generated and have expected dimensions.
        """
        result = await real_runner.analyze_article(real_article_id, skip_if_analyzed=False)

        assert result['status'] == 'success'

        # Get embedding from database
        embedding = real_runner.embedding_store.get_by_article_id(real_article_id)

        assert embedding is not None
        assert embedding['dimension'] == 768  # text-embedding-004 dimension
        assert embedding['model'] == 'text-embedding-004'

        print(f"\n=== Embedding Info ===")
        print(f"Model: {embedding['model']}")
        print(f"Dimension: {embedding['dimension']}")
        print(f"Embedding ID: {embedding['id']}")
        print("======================\n")
