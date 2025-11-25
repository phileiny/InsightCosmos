"""
Trend Analysis Tool

分析文章主題分布、識別熱門趨勢、偵測新興話題。

Author: Ray 張瑞涵
Created: 2025-11-25
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import re
from src.utils.logger import setup_logger


class TrendAnalysisTool:
    """
    趨勢分析工具

    分析文章主題分布、識別熱門趨勢、偵測新興話題。

    Attributes:
        logger (Logger): 日誌記錄器
    """

    def __init__(self):
        """初始化趨勢分析工具"""
        self.logger = setup_logger("TrendAnalysis")

    def identify_hot_trends(
        self,
        clusters: List[Dict[str, Any]],
        min_article_count: int = 5,
        min_avg_priority: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        識別熱門趨勢

        標準：
        1. 文章數量多（>= min_article_count）
        2. 平均優先度高（>= min_avg_priority）

        Args:
            clusters: 聚類結果列表
            min_article_count: 最少文章數閾值
            min_avg_priority: 最低平均優先度閾值

        Returns:
            List[dict]: [
                {
                    "cluster_id": 0,
                    "article_count": 12,
                    "average_priority": 0.87,
                    "trend_score": 0.92,  # 綜合評分
                    "evidence": "12 篇文章，平均優先度 0.87"
                },
                ...
            ]

        Example:
            >>> tool = TrendAnalysisTool()
            >>> hot_trends = tool.identify_hot_trends(clusters, min_article_count=5)
            >>> print(f"Found {len(hot_trends)} hot trends")
        """
        self.logger.info(f"Identifying hot trends (min_count={min_article_count}, min_priority={min_avg_priority})...")

        hot_trends = []

        for cluster in clusters:
            article_count = cluster.get("article_count", 0)
            avg_priority = cluster.get("average_priority", 0.0)

            # 檢查是否符合熱門趨勢標準
            if (article_count >= min_article_count and
                avg_priority >= min_avg_priority):

                # 計算趨勢分數（標準化後的文章數 * 平均優先度）
                # 假設 10 篇文章為滿分 1.0
                normalized_count = min(article_count / 10, 1.0)
                trend_score = normalized_count * avg_priority

                hot_trends.append({
                    "cluster_id": cluster["cluster_id"],
                    "article_count": article_count,
                    "average_priority": avg_priority,
                    "trend_score": trend_score,
                    "evidence": f"{article_count} 篇文章，平均優先度 {avg_priority:.2f}"
                })

        # 按趨勢分數排序
        hot_trends.sort(key=lambda x: x["trend_score"], reverse=True)

        self.logger.info(f"Found {len(hot_trends)} hot trends")

        return hot_trends

    def detect_emerging_topics(
        self,
        current_articles: List[Dict[str, Any]],
        previous_articles: Optional[List[Dict[str, Any]]] = None,
        min_priority: float = 0.7,
        min_article_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        偵測新興話題

        標準：
        1. 本週首次出現（或上週沒有）
        2. 優先度較高（>= min_priority）
        3. 文章數量達到閾值（>= min_article_count）

        Args:
            current_articles: 本週文章列表
            previous_articles: 上週文章列表（可選）
            min_priority: 最低優先度閾值
            min_article_count: 最少文章數閾值

        Returns:
            List[dict]: [
                {
                    "topic_keywords": ["robotics", "foundation", "model"],
                    "article_count": 3,
                    "first_appearance": "2025-11-22",
                    "average_priority": 0.85,
                    "articles": [
                        {"title": "...", "url": "...", "priority_score": 0.85},
                        ...
                    ]
                },
                ...
            ]

        Example:
            >>> tool = TrendAnalysisTool()
            >>> emerging = tool.detect_emerging_topics(current_articles)
            >>> print(f"Found {len(emerging)} emerging topics")
        """
        self.logger.info("Detecting emerging topics...")

        # 提取本週關鍵字
        current_keywords = self._extract_keywords_from_articles(current_articles)

        # 如果有上週數據，提取上週關鍵字
        if previous_articles:
            previous_keywords = self._extract_keywords_from_articles(previous_articles)
            # 找出新關鍵字（本週有但上週沒有）
            new_keywords = set(current_keywords.keys()) - set(previous_keywords.keys())
            self.logger.info(f"Found {len(new_keywords)} new keywords compared to previous week")
        else:
            # 無上週數據，使用低頻但高優先度的關鍵字
            new_keywords = [
                k for k, v in current_keywords.items()
                if v["count"] <= 5 and v["avg_priority"] >= min_priority
            ]
            self.logger.info(f"Found {len(new_keywords)} low-frequency high-priority keywords")

        # 聚合成新興話題
        emerging_topics = []
        for keyword in new_keywords:
            keyword_info = current_keywords.get(keyword)
            if not keyword_info:
                continue

            # 檢查是否符合新興話題標準
            if (keyword_info["avg_priority"] >= min_priority and
                keyword_info["count"] >= min_article_count):

                emerging_topics.append({
                    "topic_keywords": [keyword],
                    "article_count": keyword_info["count"],
                    "first_appearance": keyword_info["first_date"],
                    "average_priority": keyword_info["avg_priority"],
                    "articles": keyword_info["articles"][:3]  # Top 3
                })

        # 按平均優先度排序
        emerging_topics.sort(key=lambda x: x["average_priority"], reverse=True)

        self.logger.info(f"Found {len(emerging_topics)} emerging topics")

        return emerging_topics

    def _extract_keywords_from_articles(
        self,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        從文章中提取關鍵字統計

        Args:
            articles: 文章列表

        Returns:
            dict: {
                "keyword": {
                    "count": 5,
                    "avg_priority": 0.82,
                    "first_date": "2025-11-22",
                    "articles": [...]
                },
                ...
            }
        """
        keyword_stats = defaultdict(lambda: {
            "count": 0,
            "priorities": [],
            "dates": [],
            "articles": []
        })

        # 停用詞列表（常見無意義詞）
        stopwords = {
            "with", "from", "that", "this", "have", "been", "more", "they",
            "will", "would", "could", "should", "about", "there", "their",
            "which", "these", "those", "then", "than", "when", "where",
            "what", "while", "after", "before", "during", "within"
        }

        for article in articles:
            # 從標題、標籤、摘要中提取關鍵字
            text = ""
            text += article.get("title", "") + " "

            # 處理 tags（可能是字串或列表）
            tags = article.get("tags", "")
            if isinstance(tags, list):
                text += " ".join(tags) + " "
            else:
                text += str(tags) + " "

            text += article.get("summary", "")[:200]  # 只取摘要前 200 字元

            # 提取至少 4 字元的單詞（過濾太短的詞）
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())

            # 過濾停用詞
            words = [w for w in words if w not in stopwords]

            # 統計每個關鍵字
            for word in set(words):  # 去重（每篇文章每個詞只計數一次）
                keyword_stats[word]["count"] += 1
                keyword_stats[word]["priorities"].append(
                    article.get("priority_score", 0.0)
                )
                keyword_stats[word]["dates"].append(
                    article.get("published_at", "") or article.get("analyzed_at", "")
                )
                keyword_stats[word]["articles"].append({
                    "title": article.get("title", "Untitled"),
                    "url": article.get("url", ""),
                    "priority_score": article.get("priority_score", 0.0)
                })

        # 計算平均值與首次出現日期
        result = {}
        for keyword, stats in keyword_stats.items():
            if stats["count"] == 0:
                continue

            result[keyword] = {
                "count": stats["count"],
                "avg_priority": sum(stats["priorities"]) / len(stats["priorities"]),
                "first_date": min(stats["dates"]) if stats["dates"] else "",
                "articles": sorted(
                    stats["articles"],
                    key=lambda x: x["priority_score"],
                    reverse=True
                )
            }

        return result

    def compare_with_previous_week(
        self,
        current_clusters: List[Dict[str, Any]],
        previous_clusters: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        與上週比較（可選功能，Phase 1 簡化版本）

        Args:
            current_clusters: 本週聚類結果
            previous_clusters: 上週聚類結果（可選）

        Returns:
            dict: {
                "growth_topics": [...],      # 增長主題
                "declining_topics": [...],   # 衰退主題
                "stable_topics": [...]       # 穩定主題
            }

        Note:
            Phase 1 簡化實現，僅返回空列表。
            未來版本可擴展實現完整的週比較功能。
        """
        self.logger.info("Comparing with previous week (Phase 1: simplified)")

        # Phase 1 簡化版本：僅返回空結果
        # 未來可擴展：比較集群相似度、文章數量變化等
        return {
            "growth_topics": [],
            "declining_topics": [],
            "stable_topics": []
        }

    def generate_trend_summary(
        self,
        hot_trends: List[Dict[str, Any]],
        emerging_topics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成趨勢摘要（供 LLM 使用）

        Args:
            hot_trends: 熱門趨勢列表
            emerging_topics: 新興話題列表

        Returns:
            dict: {
                "total_hot_trends": 3,
                "total_emerging_topics": 2,
                "summary": "本週識別出 3 個熱門趨勢與 2 個新興話題",
                "top_trend": {...},
                "top_emerging": {...}
            }
        """
        summary = {
            "total_hot_trends": len(hot_trends),
            "total_emerging_topics": len(emerging_topics),
            "summary": f"本週識別出 {len(hot_trends)} 個熱門趨勢與 {len(emerging_topics)} 個新興話題",
            "top_trend": hot_trends[0] if hot_trends else None,
            "top_emerging": emerging_topics[0] if emerging_topics else None
        }

        return summary


# ============================================================================
# 便捷函數
# ============================================================================

def analyze_weekly_trends(
    clusters: List[Dict[str, Any]],
    current_articles: List[Dict[str, Any]],
    previous_articles: Optional[List[Dict[str, Any]]] = None,
    min_hot_article_count: int = 5,
    min_hot_priority: float = 0.75,
    min_emerging_priority: float = 0.7
) -> Dict[str, Any]:
    """
    便捷函數：週趨勢分析

    Args:
        clusters: 聚類結果列表
        current_articles: 本週文章列表
        previous_articles: 上週文章列表（可選）
        min_hot_article_count: 熱門趨勢最少文章數
        min_hot_priority: 熱門趨勢最低優先度
        min_emerging_priority: 新興話題最低優先度

    Returns:
        dict: {
            "hot_trends": [...],
            "emerging_topics": [...],
            "summary": {...}
        }

    Example:
        >>> from src.tools.trend_analysis import analyze_weekly_trends
        >>> result = analyze_weekly_trends(clusters, articles)
        >>> print(f"Found {len(result['hot_trends'])} hot trends")
        >>> print(f"Found {len(result['emerging_topics'])} emerging topics")
    """
    tool = TrendAnalysisTool()

    # 識別熱門趨勢
    hot_trends = tool.identify_hot_trends(
        clusters,
        min_article_count=min_hot_article_count,
        min_avg_priority=min_hot_priority
    )

    # 偵測新興話題
    emerging_topics = tool.detect_emerging_topics(
        current_articles,
        previous_articles,
        min_priority=min_emerging_priority
    )

    # 生成摘要
    summary = tool.generate_trend_summary(hot_trends, emerging_topics)

    return {
        "hot_trends": hot_trends,
        "emerging_topics": emerging_topics,
        "summary": summary
    }
