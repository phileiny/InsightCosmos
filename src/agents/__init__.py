"""
InsightCosmos Agents Module

This module provides AI agents for the InsightCosmos system.

Agents:
    - ScoutAgent: Collects AI and Robotics articles from RSS feeds and Google Search
    - AnalystAgent: Analyzes articles, extracts insights, and scores priority

Usage:
    from src.agents import ScoutAgentRunner, AnalystAgentRunner, collect_articles

    # Scout Agent - Collect articles
    scout_runner = ScoutAgentRunner()
    articles = scout_runner.collect_articles()
    print(f"Collected {articles['total_count']} articles")

    # Analyst Agent - Analyze articles
    analyst_runner = AnalystAgentRunner(agent, article_store, embedding_store)
    result = await analyst_runner.analyze_pending(limit=20)
    print(f"Analyzed {result['succeeded']} articles")

Version History:
    - 1.0.0: Scout Agent implementation (Stage 5)
    - 1.1.0: Analyst Agent implementation (Stage 7)
"""

from src.agents.scout_agent import (
    ScoutAgentRunner,
    create_scout_agent,
    collect_articles,
    fetch_rss,
    search_articles
)

from src.agents.analyst_agent import (
    AnalystAgentRunner,
    create_analyst_agent,
    analyze_article
)

__all__ = [
    # Scout Agent
    'ScoutAgentRunner',
    'create_scout_agent',
    'collect_articles',
    'fetch_rss',
    'search_articles',
    # Analyst Agent
    'AnalystAgentRunner',
    'create_analyst_agent',
    'analyze_article'
]

__version__ = '1.1.0'
