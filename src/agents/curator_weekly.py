"""
Curator Weekly Agent

每週深度情報報告生成器，負責：
1. 聚合本週已分析的文章
2. 進行向量聚類識別主題
3. 分析熱門趨勢與新興話題
4. 使用 LLM 生成深度報告
5. 格式化並發送 Email

Author: Ray 張瑞涵
Created: 2025-11-25
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import numpy as np

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.memory.database import Database
from src.memory.article_store import ArticleStore
from src.memory.embedding_store import EmbeddingStore
from src.tools.vector_clustering import VectorClusteringTool
from src.tools.trend_analysis import TrendAnalysisTool
from src.tools.digest_formatter import DigestFormatter
from src.tools.email_sender import EmailSender


def create_weekly_curator_agent() -> LlmAgent:
    """
    創建 Weekly Curator Agent

    Returns:
        LlmAgent: Weekly Curator Agent 實例

    Example:
        >>> agent = create_weekly_curator_agent()
        >>> print(agent.name)
        WeeklyCurator
    """
    # 載入 Prompt
    with open("prompts/weekly_prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    # 創建 Agent（不需要額外工具，數據已預處理）
    # 根據 ADK 文件，Python 中直接使用模型字串
    agent = LlmAgent(
        name="WeeklyCurator",
        model="gemini-2.0-flash",  # 使用穩定版模型
        instruction=prompt,
        tools=[],  # Weekly Curator 不需要工具，直接接收處理好的數據
        output_key="weekly_report"
    )

    return agent


class CuratorWeeklyRunner:
    """
    Weekly Curator Agent 運行器

    負責完整的週報生成流程：
    1. 查詢本週文章與 Embeddings
    2. 向量聚類
    3. 趨勢分析
    4. LLM 生成報告
    5. 格式化 HTML/Text
    6. 發送 Email

    Attributes:
        config (Config): 配置對象
        db (Database): 資料庫連接
        article_store (ArticleStore): 文章存儲
        embedding_store (EmbeddingStore): 向量存儲
        logger (Logger): 日誌記錄器
    """

    def __init__(self, config: Config):
        """
        初始化 Weekly Curator Runner

        Args:
            config: 配置對象
        """
        self.config = config
        self.db = Database.from_config(config)
        self.article_store = ArticleStore(self.db)
        self.embedding_store = EmbeddingStore(self.db)
        self.logger = setup_logger("WeeklyCurator")

    def generate_weekly_report(
        self,
        week_start: Optional[str] = None,  # "YYYY-MM-DD"
        week_end: Optional[str] = None,    # "YYYY-MM-DD"
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        生成週報並發送

        Args:
            week_start: 週開始日期（默認為 7 天前）
            week_end: 週結束日期（默認為今天）
            dry_run: 是否為測試模式（不發送郵件）

        Returns:
            dict: {
                "status": "success" | "error",
                "subject": str,
                "recipients": list,
                "html_body": str,
                "text_body": str,
                "total_articles": int,
                "analyzed_articles": int,
                "num_clusters": int,
                "hot_trends": int,
                "emerging_topics": int,
                "email_sent": bool,
                "error_message": str,  # 錯誤時
                "suggestion": str      # 錯誤時
            }

        Example:
            >>> runner = CuratorWeeklyRunner(config)
            >>> result = runner.generate_weekly_report(dry_run=True)
            >>> print(result["subject"])
            InsightCosmos Weekly Report - 2025-11-18 to 2025-11-24
        """
        self.logger.info("=" * 60)
        self.logger.info("Weekly Report Generation Started")
        self.logger.info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
        self.logger.info("=" * 60)

        # 統計數據收集
        stats = {
            "total_articles": 0,
            "analyzed_articles": 0,
            "num_clusters": 0,
            "hot_trends": 0,
            "emerging_topics": 0
        }

        try:
            # 1. 查詢本週文章
            self.logger.info("\n[Step 1/5] Querying weekly articles...")
            articles = self._get_weekly_articles(week_start, week_end)

            if not articles:
                return {
                    "status": "error",
                    "error_type": "no_articles",
                    "error_message": "No analyzed articles found for this week",
                    "suggestion": "Run Daily Pipeline to collect and analyze articles first",
                    **stats
                }

            stats["total_articles"] = len(articles)
            stats["analyzed_articles"] = len(articles)
            self.logger.info(f"Found {len(articles)} analyzed articles")

            # 2. 向量聚類
            self.logger.info("\n[Step 2/5] Clustering articles by topic...")
            clustering_result = self._cluster_articles(articles)

            if clustering_result["status"] != "success":
                return {**clustering_result, **stats}

            clusters = clustering_result["clusters"]
            stats["num_clusters"] = len(clusters)
            self.logger.info(f"Identified {len(clusters)} topic clusters")

            # 3. 趨勢分析
            self.logger.info("\n[Step 3/5] Analyzing trends...")
            trend_result = self._analyze_trends(articles, clusters)
            stats["hot_trends"] = len(trend_result['hot_trends'])
            stats["emerging_topics"] = len(trend_result['emerging_topics'])
            self.logger.info(f"Found {stats['hot_trends']} hot trends")
            self.logger.info(f"Found {stats['emerging_topics']} emerging topics")

            # 4. LLM 生成報告
            self.logger.info("\n[Step 4/5] Generating report with LLM...")
            report_data = self._generate_report_with_llm(
                articles, clusters, trend_result, week_start, week_end
            )

            if report_data["status"] != "success":
                return {**report_data, **stats}

            # 5. 格式化並發送
            self.logger.info("\n[Step 5/5] Formatting and sending email...")
            send_result = self._format_and_send(report_data["report"], dry_run)

            self.logger.info("\n" + "=" * 60)
            if send_result["status"] == "success":
                self.logger.info("Weekly Report Generation Completed Successfully")
            else:
                self.logger.error("Weekly Report Generation Failed")
            self.logger.info("=" * 60)

            # 合併統計數據到結果
            send_result.update(stats)
            send_result["email_sent"] = not dry_run and send_result["status"] == "success"
            return send_result

        except Exception as e:
            self.logger.error(f"Weekly report generation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "suggestion": "Check logs for detailed error information",
                **stats
            }

    def _get_weekly_articles(
        self,
        week_start: Optional[str],
        week_end: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        查詢本週文章

        Args:
            week_start: 週開始日期
            week_end: 週結束日期

        Returns:
            List[dict]: 文章列表
        """
        # 計算日期範圍（默認為過去 7 天）
        if week_end is None:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(week_end, "%Y-%m-%d")

        if week_start is None:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(week_start, "%Y-%m-%d")

        self.logger.info(f"Date range: {start_date.date()} to {end_date.date()}")

        # 查詢已分析的文章（status='analyzed'）
        articles = self.article_store.get_by_date_range(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            status="analyzed",
            min_priority=0.6  # 過濾低優先度文章
        )

        return articles

    def _cluster_articles(
        self,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        向量聚類

        Args:
            articles: 文章列表

        Returns:
            dict: 聚類結果
        """
        # 獲取文章 IDs
        article_ids = [a["id"] for a in articles]

        # 查詢 Embeddings
        embeddings_data = self.embedding_store.get_embeddings(article_ids)

        if not embeddings_data:
            return {
                "status": "error",
                "error_type": "no_embeddings",
                "error_message": "No embeddings found for articles",
                "suggestion": "Ensure Analyst Agent has generated embeddings"
            }

        # 建立 article_id -> embedding 的映射
        embedding_map = {e["article_id"]: e["embedding"] for e in embeddings_data}

        # 只保留有 embedding 的文章
        articles_with_embeddings = [
            article for article in articles
            if article["id"] in embedding_map
        ]

        # 檢查是否有足夠的文章進行聚類
        if len(articles_with_embeddings) < 2:
            return {
                "status": "error",
                "error_type": "insufficient_embeddings",
                "error_message": f"Only {len(articles_with_embeddings)} articles have embeddings (minimum: 2)",
                "suggestion": "Run Analyst Agent to generate more embeddings"
            }

        self.logger.info(
            f"Clustering {len(articles_with_embeddings)} articles "
            f"(filtered from {len(articles)} total)"
        )

        # 組織成 numpy 矩陣（按過濾後的文章順序）
        embeddings_matrix = np.array([
            embedding_map[article["id"]]
            for article in articles_with_embeddings
        ])

        # 準備元數據（使用過濾後的文章）
        metadata = []
        for article in articles_with_embeddings:
            metadata.append({
                "article_id": article["id"],
                "title": article["title"],
                "summary": article.get("summary", ""),
                "tags": article.get("tags", ""),
                "priority_score": article.get("priority_score", 0.0)
            })

        # 動態調整聚類數量（使用有 embedding 的文章數）
        n_articles = len(articles_with_embeddings)
        if n_articles >= 40:
            n_clusters = 5
        elif n_articles >= 25:
            n_clusters = 4
        elif n_articles >= 15:
            n_clusters = 3
        else:
            n_clusters = 2

        self.logger.info(f"Using {n_clusters} clusters for {n_articles} articles")

        # 執行聚類
        clustering_tool = VectorClusteringTool(n_clusters=n_clusters)
        result = clustering_tool.cluster_embeddings(embeddings_matrix, metadata)

        # 如果成功，提取關鍵字
        if result["status"] == "success":
            for cluster in result["clusters"]:
                keywords = clustering_tool.extract_cluster_keywords(
                    cluster, articles, top_k=5
                )
                cluster["keywords"] = keywords
                self.logger.info(
                    f"Cluster {cluster['cluster_id']}: "
                    f"{cluster['article_count']} articles, "
                    f"keywords: {', '.join(keywords[:3])}"
                )

        return result

    def _analyze_trends(
        self,
        articles: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        趨勢分析

        Args:
            articles: 文章列表
            clusters: 聚類結果

        Returns:
            dict: 趨勢分析結果
        """
        trend_tool = TrendAnalysisTool()

        # 識別熱門趨勢
        hot_trends = trend_tool.identify_hot_trends(
            clusters,
            min_article_count=5,
            min_avg_priority=0.75
        )

        # 偵測新興話題
        emerging_topics = trend_tool.detect_emerging_topics(
            articles,
            previous_articles=None,  # Phase 1 不比較上週
            min_priority=0.7,
            min_article_count=2
        )

        return {
            "hot_trends": hot_trends,
            "emerging_topics": emerging_topics
        }

    def _generate_report_with_llm(
        self,
        articles: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        trend_result: Dict[str, Any],
        week_start: Optional[str],
        week_end: Optional[str]
    ) -> Dict[str, Any]:
        """
        使用 LLM 生成報告

        Args:
            articles: 文章列表
            clusters: 聚類結果
            trend_result: 趨勢分析結果
            week_start: 週開始日期
            week_end: 週結束日期

        Returns:
            dict: LLM 生成的報告數據
        """
        # 準備輸入數據
        input_data = self._prepare_llm_input(
            articles, clusters, trend_result, week_start, week_end
        )

        # 創建 Agent
        agent = create_weekly_curator_agent()

        # 調用 Agent（使用 async 方式，參考 Daily Curator）
        try:
            import asyncio
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai.types import Content, Part

            # 將輸入數據轉為 JSON 字串
            input_json = json.dumps(input_data, ensure_ascii=False, indent=2)
            user_input = f"請根據以下數據生成週報：\n\n{input_json}"

            # 創建 session service 和 runner
            session_service = InMemorySessionService()
            runner = Runner(
                agent=agent,
                app_name="InsightCosmos",
                session_service=session_service
            )

            # 定義 async 函數
            async def invoke_llm_async():
                user_id = self.config.user_name or "user"
                session_id = "weekly_curator_session"

                # 創建 session
                await session_service.create_session(
                    app_name="InsightCosmos",
                    user_id=user_id,
                    session_id=session_id
                )

                # 執行 LLM
                response_text = ""
                events_gen = runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=Content(parts=[Part(text=user_input)], role="user")
                )

                async for event in events_gen:
                    # 檢查是否是最終響應
                    if event.is_final_response() and event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        break

                return response_text.strip() if response_text else None

            # 執行 async 函數
            final_response = asyncio.run(invoke_llm_async())

            if not final_response:
                raise Exception("No final response from LLM")

            # 解析輸出
            report_json = self._parse_llm_output(final_response)

            if report_json is None:
                return {
                    "status": "error",
                    "error_type": "parse_error",
                    "error_message": "Failed to parse LLM output as JSON",
                    "suggestion": "Check LLM output format in logs"
                }

            self.logger.info("LLM report generated successfully")

            return {
                "status": "success",
                "report": report_json
            }

        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "suggestion": "Check GOOGLE_API_KEY and API quota"
            }

    def _prepare_llm_input(
        self,
        articles: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        trend_result: Dict[str, Any],
        week_start: Optional[str],
        week_end: Optional[str]
    ) -> Dict[str, Any]:
        """
        準備 LLM 輸入數據

        Args:
            articles: 文章列表
            clusters: 聚類結果
            trend_result: 趨勢分析結果
            week_start: 週開始日期
            week_end: 週結束日期

        Returns:
            dict: 格式化的輸入數據
        """
        # 計算日期
        if week_end is None:
            end_date = datetime.now().date()
        else:
            end_date = datetime.strptime(week_end, "%Y-%m-%d").date()

        if week_start is None:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(week_start, "%Y-%m-%d").date()

        # 準備集群數據（加入代表性文章）
        clusters_with_articles = []
        for cluster in clusters:
            cluster_data = {
                "cluster_id": cluster["cluster_id"],
                "article_count": cluster["article_count"],
                "average_priority": cluster["average_priority"],
                "keywords": cluster.get("keywords", []),
                "representative_articles": []
            }

            # 取前 3 篇代表性文章
            for article_info in cluster["articles"][:3]:
                article_id = article_info["article_id"]
                # 從完整文章列表中找到這篇文章
                full_article = next(
                    (a for a in articles if a["id"] == article_id),
                    None
                )
                if full_article:
                    cluster_data["representative_articles"].append({
                        "title": full_article["title"],
                        "url": full_article["url"],
                        "summary": full_article.get("summary", ""),
                        "priority_score": full_article.get("priority_score", 0.0)
                    })

            clusters_with_articles.append(cluster_data)

        # 準備 Top 文章（全局 Top 10）
        top_articles = sorted(
            articles,
            key=lambda x: x.get("priority_score", 0.0),
            reverse=True
        )[:10]

        top_articles_data = []
        for article in top_articles:
            top_articles_data.append({
                "title": article["title"],
                "url": article["url"],
                "summary": article.get("summary", ""),
                "priority_score": article.get("priority_score", 0.0),
                "tags": article.get("tags", ""),
                "key_insights": article.get("key_insights", [])
            })

        # 組合完整輸入
        return {
            "week_start": str(start_date),
            "week_end": str(end_date),
            "total_articles": len(articles),
            "analyzed_articles": len(articles),
            "topic_clusters": clusters_with_articles,
            "hot_trends": trend_result["hot_trends"],
            "emerging_topics": trend_result["emerging_topics"],
            "top_articles_overall": top_articles_data
        }

    def _parse_llm_output(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 輸出（支援純 JSON 或 Markdown 包裝）

        Args:
            response_text: LLM 回應文本

        Returns:
            dict or None: 解析後的 JSON，失敗返回 None
        """
        # 嘗試直接解析 JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # 嘗試提取 Markdown 包裝的 JSON
        import re
        json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 解析失敗
        self.logger.error(f"Failed to parse LLM output: {response_text[:200]}...")
        return None

    def _format_and_send(
        self,
        report_data: Dict[str, Any],
        dry_run: bool
    ) -> Dict[str, Any]:
        """
        格式化並發送郵件

        Args:
            report_data: LLM 生成的報告數據
            dry_run: 是否為測試模式

        Returns:
            dict: 發送結果
        """
        # 格式化（使用 DigestFormatter 的 weekly 方法）
        formatter = DigestFormatter()

        # 暫時使用 Daily 格式（後續會擴展 Weekly 格式）
        # TODO: 實作 format_weekly_html() 和 format_weekly_text()

        # 簡單格式化（臨時方案）
        subject = f"InsightCosmos Weekly Report - {report_data.get('week_start', 'N/A')} to {report_data.get('week_end', 'N/A')}"

        # 組織文本內容
        text_body = self._format_simple_text(report_data)
        html_body = self._format_simple_html(report_data)

        # 發送郵件
        if not dry_run:
            from src.tools.email_sender import EmailConfig
            email_config = EmailConfig(
                smtp_host=self.config.smtp_host,
                smtp_port=self.config.smtp_port,
                sender_email=self.config.email_account,
                sender_password=self.config.email_password,
                use_tls=self.config.smtp_use_tls
            )
            sender = EmailSender(email_config)
            send_result = sender.send(
                to_email=self.config.email_account,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )

            if send_result["status"] == "success":
                self.logger.info(f"Email sent to {self.config.email_account}")
            else:
                self.logger.error(f"Email sending failed: {send_result.get('error_message')}")

            return {
                "status": send_result["status"],
                "subject": subject,
                "recipients": [self.config.email_account],
                "html_body": html_body,
                "text_body": text_body,
                "error_message": send_result.get("error_message"),
                "suggestion": send_result.get("suggestion")
            }
        else:
            self.logger.info("DRY RUN: Email not sent")
            return {
                "status": "success",
                "subject": subject,
                "recipients": [self.config.email_account],
                "html_body": html_body,
                "text_body": text_body
            }

    def _format_simple_text(self, report_data: Dict[str, Any]) -> str:
        """簡單的純文字格式化（臨時方案）"""
        lines = []
        lines.append("=" * 80)
        lines.append("InsightCosmos Weekly Report")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"週總結: {report_data.get('week_summary', 'N/A')}")
        lines.append("")
        lines.append("=" * 80)
        lines.append("熱門趨勢")
        lines.append("=" * 80)

        for i, trend in enumerate(report_data.get("hot_trends", []), 1):
            lines.append(f"\n{i}. {trend.get('trend_name', 'N/A')}")
            lines.append(f"   證據: {trend.get('evidence', 'N/A')}")
            lines.append(f"   建議: {trend.get('action_suggestion', 'N/A')}")

        lines.append("\n" + "=" * 80)
        lines.append("Top 文章")
        lines.append("=" * 80)

        for i, article in enumerate(report_data.get("top_articles", []), 1):
            lines.append(f"\n{i}. {article.get('title', 'N/A')}")
            lines.append(f"   {article.get('url', 'N/A')}")
            lines.append(f"   要點: {article.get('key_takeaway', 'N/A')}")

        lines.append("\n" + "=" * 80)
        lines.append("Generated by InsightCosmos")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _format_simple_html(self, report_data: Dict[str, Any]) -> str:
        """簡單的 HTML 格式化（臨時方案）"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ background: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; }}
        .trend {{ background: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .article {{ background: #e8f5e9; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .footer {{ margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>InsightCosmos Weekly Report</h1>

    <div class="summary">
        <strong>週總結:</strong> {report_data.get('week_summary', 'N/A')}
    </div>

    <h2>🔥 熱門趨勢</h2>
"""

        for i, trend in enumerate(report_data.get("hot_trends", []), 1):
            html += f"""
    <div class="trend">
        <h3>{i}. {trend.get('trend_name', 'N/A')}</h3>
        <p><strong>證據:</strong> {trend.get('evidence', 'N/A')}</p>
        <p><strong>建議:</strong> {trend.get('action_suggestion', 'N/A')}</p>
    </div>
"""

        html += "<h2>📰 Top 文章</h2>"

        for i, article in enumerate(report_data.get("top_articles", []), 1):
            html += f"""
    <div class="article">
        <h3>{i}. <a href="{article.get('url', '#')}">{article.get('title', 'N/A')}</a></h3>
        <p><strong>要點:</strong> {article.get('key_takeaway', 'N/A')}</p>
    </div>
"""

        html += """
    <div class="footer">
        <p>Generated by InsightCosmos | Your Personal Intelligence Universe</p>
    </div>
</body>
</html>
"""
        return html


# ============================================================================
# 便捷函數
# ============================================================================

def generate_weekly_report(
    config: Optional[Config] = None,
    week_start: Optional[str] = None,
    week_end: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    便捷函數：生成週報

    Args:
        config: 配置對象（默認從環境變數載入）
        week_start: 週開始日期（默認 7 天前）
        week_end: 週結束日期（默認今天）
        dry_run: 是否為測試模式

    Returns:
        dict: 生成結果

    Example:
        >>> from src.agents.curator_weekly import generate_weekly_report
        >>> result = generate_weekly_report(dry_run=True)
        >>> print(result["subject"])
        InsightCosmos Weekly Report - 2025-11-18 to 2025-11-24
    """
    if config is None:
        config = Config.from_env()

    runner = CuratorWeeklyRunner(config)
    return runner.generate_weekly_report(week_start, week_end, dry_run)
