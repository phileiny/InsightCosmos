"""
InsightCosmos Digest Formatter

Formats daily digest data into HTML and plain text email formats.

Classes:
    DigestFormatter: Formats digest data into email-ready HTML and text

Usage:
    from src.tools.digest_formatter import DigestFormatter

    formatter = DigestFormatter()

    digest_data = {
        "date": "2025-11-24",
        "total_articles": 5,
        "top_articles": [...],
        "daily_insight": "...",
        "recommended_action": "..."
    }

    html = formatter.format_html(digest_data)
    text = formatter.format_text(digest_data)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import html as html_module

from src.utils.logger import Logger


class DigestFormatter:
    """
    Digest formatter for email output

    Formats digest data into:
    - HTML email (primary format)
    - Plain text email (fallback format)

    Example:
        >>> formatter = DigestFormatter()
        >>> digest = {
        ...     "date": "2025-11-24",
        ...     "total_articles": 3,
        ...     "top_articles": [...]
        ... }
        >>> html_body = formatter.format_html(digest)
        >>> text_body = formatter.format_text(digest)
    """

    def __init__(self):
        """Initialize DigestFormatter"""
        self.logger = Logger.get_logger(__name__)

    def format_html(self, digest: Dict[str, Any]) -> str:
        """
        Format digest as HTML email

        Args:
            digest: Digest data containing:
                - date: str (YYYY-MM-DD)
                - total_articles: int
                - top_articles: List[dict]
                - daily_insight: str
                - recommended_action: str (optional)

        Returns:
            str: HTML email body

        Example:
            >>> html = formatter.format_html({
            ...     "date": "2025-11-24",
            ...     "total_articles": 2,
            ...     "top_articles": [...]
            ... })
        """
        # Extract data
        date = digest.get('date', datetime.now().strftime('%Y-%m-%d'))
        total_articles = digest.get('total_articles', 0)
        articles = digest.get('top_articles', [])
        daily_insight = digest.get('daily_insight', '')
        recommended_action = digest.get('recommended_action', '')

        # Format date (convert YYYY-MM-DD to Chinese format)
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y年%m月%d日')
        except:
            formatted_date = date

        # Generate articles HTML
        articles_html = self._format_articles_html(articles)

        # Generate action HTML (if exists)
        action_html = ""
        if recommended_action:
            action_html = f"""
        <div class="action-section">
            <div class="action-title">🎯 建議行動</div>
            <div>{html_module.escape(recommended_action)}</div>
        </div>
        """

        # Compose HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InsightCosmos Daily Digest - {html_module.escape(date)}</title>
    <style>
        /* Base styles */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}

        /* Container */
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        /* Header */
        .header {{
            border-bottom: 3px solid #4285f4;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}

        h1 {{
            color: #4285f4;
            margin: 0;
            font-size: 24px;
        }}

        .date {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}

        /* Article cards */
        .article {{
            border-left: 4px solid #e0e0e0;
            padding-left: 15px;
            margin-bottom: 25px;
        }}

        .article.high-priority {{
            border-left-color: #ea4335;
        }}

        .article.medium-priority {{
            border-left-color: #fbbc04;
        }}

        .article.low-priority {{
            border-left-color: #34a853;
        }}

        .article-title {{
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 8px 0;
        }}

        .article-title a {{
            color: #1a73e8;
            text-decoration: none;
        }}

        .article-title a:hover {{
            text-decoration: underline;
        }}

        .article-summary {{
            color: #5f6368;
            margin: 8px 0;
        }}

        .article-takeaway {{
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 10px;
            margin: 8px 0;
            font-style: italic;
        }}

        .article-meta {{
            font-size: 12px;
            color: #999;
            margin-top: 8px;
        }}

        .tag {{
            display: inline-block;
            background-color: #e8f0fe;
            color: #1967d2;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin-right: 5px;
        }}

        .priority-score {{
            color: #34a853;
            font-weight: 600;
        }}

        /* Insight section */
        .insight-section {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
        }}

        .insight-title {{
            font-weight: 600;
            color: #e65100;
            margin: 0 0 10px 0;
        }}

        /* Action section */
        .action-section {{
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
        }}

        .action-title {{
            font-weight: 600;
            color: #2e7d32;
            margin: 0 0 10px 0;
        }}

        /* Footer */
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}

        /* Responsive */
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .container {{
                padding: 20px;
            }}
            h1 {{
                font-size: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🌌 InsightCosmos Daily Digest</h1>
            <div class="date">{formatted_date} | {total_articles} 篇精選文章</div>
        </div>

        <!-- Articles -->
        {articles_html}

        <!-- Daily Insight -->
        <div class="insight-section">
            <div class="insight-title">💡 今日洞察</div>
            <div>{html_module.escape(daily_insight)}</div>
        </div>

        <!-- Recommended Action (optional) -->
        {action_html}

        <!-- Footer -->
        <div class="footer">
            <p>由 InsightCosmos 自動生成 | Powered by Google ADK & Gemini 2.5</p>
            <p>這是一封自動發送的郵件，請勿直接回覆。</p>
        </div>
    </div>
</body>
</html>"""

        return html

    def _format_articles_html(self, articles: List[Dict[str, Any]]) -> str:
        """
        Format articles as HTML

        Args:
            articles: List of article dictionaries

        Returns:
            str: HTML string for articles
        """
        if not articles:
            return '<div class="article"><p>暫無文章</p></div>'

        html_parts = []

        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Untitled')
            url = article.get('url', '#')
            summary = article.get('summary', '')
            key_takeaway = article.get('key_takeaway', '')
            priority_score = article.get('priority_score', 0.0)
            tags = article.get('tags', [])

            # Determine priority class
            priority_class = self._get_priority_class(priority_score)

            # Format tags
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]

            tags_html = ''.join(
                f'<span class="tag">{html_module.escape(tag)}</span>'
                for tag in tags
            )

            # Compose article HTML
            article_html = f"""
        <div class="article {priority_class}">
            <div class="article-title">
                <a href="{html_module.escape(url)}" target="_blank">[{i}] {html_module.escape(title)}</a>
            </div>
            <div class="article-summary">{html_module.escape(summary)}</div>
            <div class="article-takeaway">💡 {html_module.escape(key_takeaway)}</div>
            <div class="article-meta">
                {tags_html}
                <span class="priority-score">⭐ {priority_score:.2f}</span>
            </div>
        </div>"""

            html_parts.append(article_html)

        return '\n'.join(html_parts)

    def _get_priority_class(self, priority_score: float) -> str:
        """
        Get CSS class based on priority score

        Args:
            priority_score: Priority score (0.0-1.0)

        Returns:
            str: CSS class name
        """
        if priority_score >= 0.9:
            return 'high-priority'
        elif priority_score >= 0.7:
            return 'medium-priority'
        else:
            return 'low-priority'

    def format_text(self, digest: Dict[str, Any]) -> str:
        """
        Format digest as plain text email

        Args:
            digest: Digest data

        Returns:
            str: Plain text email body

        Example:
            >>> text = formatter.format_text({
            ...     "date": "2025-11-24",
            ...     "total_articles": 2,
            ...     "top_articles": [...]
            ... })
        """
        # Extract data
        date = digest.get('date', datetime.now().strftime('%Y-%m-%d'))
        total_articles = digest.get('total_articles', 0)
        articles = digest.get('top_articles', [])
        daily_insight = digest.get('daily_insight', '')
        recommended_action = digest.get('recommended_action', '')

        # Format date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y年%m月%d日')
        except:
            formatted_date = date

        # Build text
        lines = [
            "=" * 60,
            "  InsightCosmos Daily Digest",
            f"  {formatted_date}",
            "=" * 60,
            "",
            f"📊 今日精選: {total_articles} 篇文章",
            ""
        ]

        # Add articles
        if articles:
            for i, article in enumerate(articles, 1):
                title = article.get('title', 'Untitled')
                url = article.get('url', '#')
                summary = article.get('summary', '')
                key_takeaway = article.get('key_takeaway', '')
                priority_score = article.get('priority_score', 0.0)
                tags = article.get('tags', [])

                # Format tags
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',') if t.strip()]
                tags_str = ', '.join(tags)

                lines.extend([
                    "-" * 60,
                    f"[{i}] {title}",
                    "-" * 60,
                    f"🔗 {url}",
                    "",
                    "📝 摘要:",
                    summary,
                    "",
                    "💡 核心要點:",
                    key_takeaway,
                    "",
                    f"🏷️ 標籤: {tags_str}",
                    f"⭐ 優先度: {priority_score:.2f}",
                    ""
                ])
        else:
            lines.append("暫無文章")
            lines.append("")

        # Add daily insight
        lines.extend([
            "=" * 60,
            "💡 今日洞察",
            "=" * 60,
            daily_insight,
            ""
        ])

        # Add recommended action (if exists)
        if recommended_action:
            lines.extend([
                "=" * 60,
                "🎯 建議行動",
                "=" * 60,
                recommended_action,
                ""
            ])

        # Add footer
        lines.extend([
            "-" * 60,
            "由 InsightCosmos 自動生成",
            "Powered by Google ADK & Gemini 2.5",
            "-" * 60
        ])

        return '\n'.join(lines)


# Convenience functions
def format_html(digest: Dict[str, Any]) -> str:
    """
    Convenience function to format digest as HTML

    Args:
        digest: Digest data

    Returns:
        str: HTML email body

    Example:
        >>> html = format_html(digest_data)
    """
    formatter = DigestFormatter()
    return formatter.format_html(digest)


def format_text(digest: Dict[str, Any]) -> str:
    """
    Convenience function to format digest as plain text

    Args:
        digest: Digest data

    Returns:
        str: Plain text email body

    Example:
        >>> text = format_text(digest_data)
    """
    formatter = DigestFormatter()
    return formatter.format_text(digest)
