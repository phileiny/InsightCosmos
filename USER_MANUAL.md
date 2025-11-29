# InsightCosmos User Manual

> **Version**: 1.1.0
> **Last Updated**: 2025-11-26
> **Stage**: Phase 1 - Personal Universe Edition (Complete)

**English** | [繁體中文](USER_MANUAL_zh_TW.md)

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Daily and Weekly Reports](#daily-and-weekly-reports)
3. [Personalization](#personalization)
4. [Data Management](#data-management)
5. [Advanced Settings](#advanced-settings)
6. [Deployment Guide](#deployment-guide)
7. [Backup and Restore](#backup-and-restore)
8. [FAQ](#faq)
9. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### System Requirements

- Python 3.10+ (3.11 or 3.13 recommended)
- At least 4GB RAM
- Stable internet connection
- Google Gemini API Key

### First-time Installation

```bash
# 1. Clone the project
git clone https://github.com/your-repo/InsightCosmos.git
cd InsightCosmos

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your configuration (see details below)

# 5. Initialize database
python -m src.memory.database

# 6. Test run (no email sent)
python -m src.orchestrator.daily_runner --dry-run
```

### Environment Variable Configuration (.env)

```bash
# Google Gemini API (Required)
# Get from https://aistudio.google.com/apikey
GOOGLE_API_KEY=your_gemini_api_key

# Email Configuration (Required)
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Use Gmail App Password

# SMTP Settings (Optional, defaults to Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true

# Database (Optional, defaults to data/insights.db)
DATABASE_PATH=data/insights.db

# Personal Configuration
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems

# Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

### Gmail App Password Setup

1. Go to [Google Account Security Settings](https://myaccount.google.com/security)
2. Enable "2-Step Verification"
3. At the bottom of the "2-Step Verification" page, click "App passwords"
4. Select "Mail" and your device
5. Generate password and copy to `EMAIL_PASSWORD` in `.env`

---

## 📬 Daily and Weekly Reports

### Daily Pipeline

The Daily Pipeline executes three stages:
1. **Scout Agent**: Collects articles from RSS and Google Search
2. **Analyst Agent**: Analyzes articles using LLM, scores, and extracts insights
3. **Curator Agent**: Generates and sends daily digest email

#### Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Production mode (collect + analyze + send email)
python -m src.orchestrator.daily_runner

# Test mode (no email sent, view report content)
python -m src.orchestrator.daily_runner --dry-run

# Verbose logging mode (for debugging)
python -m src.orchestrator.daily_runner --verbose

# Combined usage
python -m src.orchestrator.daily_runner --dry-run --verbose
```

#### Execution Time

| Stage | Estimated Time |
|-------|----------------|
| Scout (Collection) | 30-60 seconds |
| Analyst (Analysis) | 1-3 minutes |
| Curator (Report) | 10-30 seconds |
| **Total** | **2-5 minutes** |

### Weekly Pipeline

The Weekly Pipeline analyzes a week's articles, performing topic clustering and trend identification:
1. Query high-priority articles analyzed within the week
2. Use vector clustering to identify topic groups
3. Analyze hot trends and emerging topics
4. Generate weekly report using LLM
5. Send weekly report email

#### Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Production mode (analyze + send email)
python -m src.orchestrator.weekly_runner

# Test mode (no email sent)
python -m src.orchestrator.weekly_runner --dry-run

# Verbose logging mode
python -m src.orchestrator.weekly_runner --verbose

# Specify date range
python -m src.orchestrator.weekly_runner --week-start 2025-11-18 --week-end 2025-11-24

# Combined usage
python -m src.orchestrator.weekly_runner --dry-run --verbose
```

#### Weekly Report Output

| Item | Description |
|------|-------------|
| Topic Clusters | Groups articles into 3-7 topic clusters by similarity |
| Hot Trends | High-frequency, high-priority keywords |
| Emerging Topics | Low-frequency but high-priority emerging keywords |
| Weekly Summary | LLM-generated weekly summary report |

#### Execution Time

| Stage | Estimated Time |
|-------|----------------|
| Data Query | < 1 second |
| Vector Clustering | 1-2 seconds |
| Trend Analysis | < 1 second |
| LLM Report | 10-15 seconds |
| Email Sending | 2-3 seconds |
| **Total** | **15-20 seconds** |

### Automated Scheduling

#### Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Run daily digest at 8 AM every day
0 8 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner >> /path/to/logs/daily_$(date +\%Y\%m\%d).log 2>&1

# Run weekly report at 8 PM every Sunday
0 20 * * 0 cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.weekly_runner >> /path/to/logs/weekly_$(date +\%Y\%m\%d).log 2>&1
```

#### Complete Example (with log rotation)

```bash
# Run daily digest at 8 AM every day
0 8 * * * cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python -m src.orchestrator.daily_runner >> /Users/ray/sides/InsightCosmos/logs/daily_$(date +\%Y\%m\%d).log 2>&1

# Run weekly report at 8 PM every Sunday
0 20 * * 0 cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python -m src.orchestrator.weekly_runner >> /Users/ray/sides/InsightCosmos/logs/weekly_$(date +\%Y\%m\%d).log 2>&1

# Clean up data older than 90 days on the 1st of each month
0 0 1 * * cd /Users/ray/sides/InsightCosmos && /Users/ray/sides/InsightCosmos/venv/bin/python scripts/cleanup_old_data.py --days 90 >> /Users/ray/sides/InsightCosmos/logs/cleanup.log 2>&1
```

#### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set Trigger (daily at 8 AM)
4. Set Action:
   - **Program**: `C:\path\to\InsightCosmos\venv\Scripts\python.exe`
   - **Arguments**: `-m src.orchestrator.daily_runner`
   - **Start in**: `C:\path\to\InsightCosmos`
5. Finish

---

## 🎯 Personalization

### 1. Modify Interest Areas and Topics

Edit the `USER_INTERESTS` variable in `.env`:

```bash
# .env

# Basic settings
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems

# Customize your interest areas (comma-separated)
# Example 1: Broader areas
USER_INTERESTS=AI,Machine Learning,Computer Vision,NLP,Robotics,Autonomous Systems

# Example 2: More focused areas
USER_INTERESTS=Large Language Models,Prompt Engineering,AI Agents,RAG

# Example 3: Cross-domain
USER_INTERESTS=AI,Healthcare,Drug Discovery,Medical Imaging

# Example 4: Technical + Business
USER_INTERESTS=AI,Startups,Venture Capital,Product Management
```

### 2. Adjust RSS Sources

Edit `src/agents/scout_agent.py`, modify the `DEFAULT_FEEDS` list:

```python
# src/agents/scout_agent.py

DEFAULT_FEEDS = [
    # Existing sources
    "https://feeds.feedburner.com/blogspot/gJZg",  # Google AI Blog
    "https://openai.com/blog/rss",                  # OpenAI Blog
    "https://www.deepmind.com/blog/rss.xml",        # DeepMind Blog

    # Add your custom sources
    "https://huggingface.co/blog/feed.xml",         # Hugging Face Blog
    "https://blog.research.google/feeds/posts/default", # Google Research
    "https://arxiv-sanity-lite.com/rss",            # ArXiv ML Papers
    "https://www.reddit.com/r/MachineLearning/.rss", # Reddit ML
    "https://news.ycombinator.com/rss",             # Hacker News

    # Industry media
    "https://venturebeat.com/category/ai/feed/",    # VentureBeat AI
    "https://techcrunch.com/category/artificial-intelligence/feed/", # TechCrunch AI
]
```

**Tips**:
- Use [RSS.app](https://rss.app/) to convert any website to RSS feed
- Use [Feedly](https://feedly.com/) to discover more high-quality RSS sources
- Ensure RSS feed URLs are valid (test in browser)

### 3. Adjust Search Keywords

Edit `src/agents/scout_agent.py`, modify `DEFAULT_SEARCH_QUERIES`:

```python
# src/agents/scout_agent.py

DEFAULT_SEARCH_QUERIES = [
    # Existing keywords
    "AI breakthrough OR AGI OR artificial general intelligence",
    "OpenAI OR Anthropic OR Google AI latest",
    "multimodal AI OR vision language model",

    # Add your custom keywords
    # Technical direction
    "retrieval augmented generation RAG",
    "prompt engineering best practices",
    "AI agent framework OR autonomous agents",

    # Application scenarios
    "AI in healthcare OR medical AI",
    "robotics manipulation OR robot learning",
    "self-driving OR autonomous vehicles",

    # Business and trends
    "AI startup funding OR AI investment",
    "AI regulation OR AI policy",
    "AGI safety OR AI alignment",

    # Research frontiers
    "transformer architecture OR attention mechanism",
    "reinforcement learning from human feedback RLHF",
    "mixture of experts MoE",
]
```

**Search Tips**:
- Use `OR` to connect synonyms: `"AGI OR artificial general intelligence"`
- Use quotes for exact matches: `"large language model"`
- Use `-` to exclude keywords: `"AI -cryptocurrency"`
- Limit time range: add `after:2025-01-01` to search queries

### 4. Adjust Content Priority Algorithm

Edit `prompts/analyst_prompt.txt`, adjust scoring criteria:

```
Your scoring criteria (0.0-1.0):

**High Priority (0.8-1.0)**:
- Technical breakthroughs (new models, architectures, theories)
- Highly relevant to {user_interests}
- Has practical application value or code
- From top research institutions or companies
- Has detailed technical details or paper links

**Medium Priority (0.5-0.7)**:
- Industry trend analysis
- Application case studies
- Tool or framework releases
- Related but non-core areas

**Low Priority (0.0-0.4)**:
- News reports or press releases
- Unrelated to {user_interests}
- Lacks technical depth
- Outdated or duplicate content
```

You can adjust these criteria based on your needs. For example:

- **Academic-oriented**: Increase paper weight, decrease news weight
- **Business-oriented**: Increase product release, funding news weight
- **Engineering-oriented**: Increase open source tools, code example weight

---

## 📧 Multi-recipient Email Configuration

### Method 1: Modify Curator Agent (Single send to multiple recipients)

Edit `src/agents/curator_daily.py`, modify recipient list:

```python
# src/agents/curator_daily.py

def generate_daily_digest(
    config: Config,
    recipient_email: str = None,  # Single recipient (backward compatible)
    recipient_emails: List[str] = None,  # New: multiple recipients
    max_articles: int = 10
) -> Dict[str, Any]:
    """
    Generate and send daily intelligence digest

    Args:
        config: Configuration object
        recipient_email: Single recipient (deprecated)
        recipient_emails: List of recipients (recommended)
        max_articles: Maximum number of articles to include
    """

    # Backward compatibility: if only single recipient provided
    if recipient_emails is None:
        if recipient_email:
            recipient_emails = [recipient_email]
        else:
            recipient_emails = [config.email_account]

    # Generate email content (same as before)
    html_body = formatter.format_digest(...)
    text_body = formatter.format_digest_text(...)

    # Send to multiple recipients
    results = []
    for email in recipient_emails:
        result = sender.send(
            to_email=email,
            subject=f"InsightCosmos Daily Digest - {today_str}",
            html_body=html_body,
            text_body=text_body
        )
        results.append({
            "email": email,
            "status": result["status"]
        })

    return {
        "status": "success" if all(r["status"] == "success" for r in results) else "partial",
        "recipients": results,
        "total_sent": sum(1 for r in results if r["status"] == "success"),
        "total_failed": sum(1 for r in results if r["status"] != "success")
    }
```

### Method 2: Configure Multiple Recipients via Environment Variables

Edit `.env` file:

```bash
# .env

# Primary recipient (yourself)
EMAIL_ACCOUNT=your_email@gmail.com

# Additional recipients list (comma-separated)
ADDITIONAL_RECIPIENTS=colleague1@example.com,colleague2@example.com,team@company.com

# Or use CC/BCC
EMAIL_CC=colleague@example.com
EMAIL_BCC=archive@company.com
```

### Method 3: Team Shared Mailing List

Use your email provider's mailing list feature:

1. **Gmail**: Create Google Group
   - Visit [groups.google.com](https://groups.google.com)
   - Create a group (e.g., `insightcosmos-team@googlegroups.com`)
   - Add team members to the group
   - Set `EMAIL_ACCOUNT` in `.env` to the group email address

2. **Self-hosted mailing list**:
   ```bash
   # .env
   EMAIL_ACCOUNT=team-digest@your-company.com
   ```
   Have IT set up `team-digest@your-company.com` to forward to all team members

---

## 🔍 Expanding Data Collection

### 1. Increase RSS Feeds

```python
# src/agents/scout_agent.py

DEFAULT_FEEDS = [
    # Academic sources (10+)
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.LG",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.CV",
    "https://proceedings.mlr.press/feed.xml",

    # Companies and research institutions (20+)
    "https://openai.com/blog/rss",
    "https://www.anthropic.com/blog/rss",
    "https://www.deepmind.com/blog/rss.xml",
    "https://ai.meta.com/blog/rss/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://azure.microsoft.com/en-us/blog/topics/ai/feed/",

    # Open source communities (10+)
    "https://huggingface.co/blog/feed.xml",
    "https://blog.langchain.dev/feed/",
    "https://www.llamaindex.ai/blog/rss.xml",

    # Media and news (10+)
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
]
```

**Notes**:
- More RSS feeds = longer fetch time
- Test in batches to ensure each feed works
- May need to adjust timeout settings (see below)

### 2. Increase Search Queries

```python
# src/agents/scout_agent.py

# Add search queries
DEFAULT_SEARCH_QUERIES = [
    # Existing queries (5-10)
    # ...

    # New queries (10-20)
    # By topic
    "large language model benchmarks",
    "AI agent reasoning capabilities",
    "vision transformer architecture",
    # ...
]

# Adjust search parameters
def search_articles(queries: List[str], max_results_per_query: int = 5):
    """
    Args:
        max_results_per_query: Max results per query (default 5, can adjust to 10-20)
    """
```

### 3. Add Other Data Sources

#### Method A: Add Twitter/X API (requires API Key)

```python
# src/tools/twitter_fetcher.py

import tweepy
from typing import List, Dict

def fetch_tweets(
    keywords: List[str],
    max_tweets: int = 50
) -> List[Dict]:
    """
    Fetch related tweets from Twitter

    Requires .env:
        TWITTER_API_KEY=xxx
        TWITTER_API_SECRET=xxx
        TWITTER_ACCESS_TOKEN=xxx
        TWITTER_ACCESS_TOKEN_SECRET=xxx
    """
    # Implementation omitted
    pass
```

#### Method B: Add Reddit API

```python
# src/tools/reddit_fetcher.py

import praw
from typing import List, Dict

def fetch_reddit_posts(
    subreddits: List[str] = ["MachineLearning", "artificial", "LocalLLaMA"],
    time_filter: str = "day",  # day, week, month
    limit: int = 50
) -> List[Dict]:
    """
    Fetch hot posts from Reddit

    Requires .env:
        REDDIT_CLIENT_ID=xxx
        REDDIT_CLIENT_SECRET=xxx
        REDDIT_USER_AGENT=InsightCosmos/1.0
    """
    # Implementation omitted
    pass
```

#### Method C: Add GitHub Trending

```python
# src/tools/github_fetcher.py

import requests
from typing import List, Dict

def fetch_trending_repos(
    language: str = "python",
    since: str = "daily"  # daily, weekly, monthly
) -> List[Dict]:
    """
    Fetch trending repos from GitHub

    Uses GitHub Trending API (unofficial):
    https://github-trending-api.now.sh/repositories?language=python&since=daily
    """
    url = f"https://github-trending-api.now.sh/repositories"
    params = {"language": language, "since": since}
    response = requests.get(url, params=params)
    return response.json()
```

Then integrate in `src/agents/scout_agent.py`:

```python
# src/agents/scout_agent.py

from src.tools.twitter_fetcher import fetch_tweets
from src.tools.reddit_fetcher import fetch_reddit_posts
from src.tools.github_fetcher import fetch_trending_repos

def collect_articles(
    user_prompt: str = None,
    enable_twitter: bool = False,
    enable_reddit: bool = True,
    enable_github: bool = True
) -> Dict[str, Any]:
    articles = []

    # Existing sources
    articles.extend(fetch_rss_articles(...))
    articles.extend(search_articles(...))

    # New sources (optional)
    if enable_twitter:
        articles.extend(fetch_tweets(...))

    if enable_reddit:
        articles.extend(fetch_reddit_posts(...))

    if enable_github:
        articles.extend(fetch_trending_repos(...))

    # Deduplicate and return
    return deduplicate_and_return(articles)
```

---

## 🤖 Switching LLM Models

InsightCosmos uses **Google ADK (Agent Development Kit)**, supporting multiple LLM models.

### 1. Use Different Gemini Models

Edit `src/agents/analyst_agent.py` and `src/agents/curator_daily.py`:

```python
# src/agents/analyst_agent.py

from google.adk.genai import Gemini

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        # Option 1: Gemini 2.5 Flash (default, fast, cheap)
        model=Gemini(model="gemini-2.5-flash"),

        # Option 2: Gemini 2.0 Flash (stable version)
        # model=Gemini(model="gemini-2.0-flash-exp"),

        # Option 3: Gemini 2.5 Pro (more powerful, but slower and more expensive)
        # model=Gemini(model="gemini-2.5-pro-preview"),

        # Option 4: Gemini 1.5 Pro (stable version)
        # model=Gemini(model="gemini-1.5-pro"),

        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### 2. Use OpenAI GPT Models (requires additional configuration)

ADK also supports OpenAI models. Install and configure first:

```bash
# .env
OPENAI_API_KEY=sk-xxx
```

```python
# src/agents/analyst_agent.py

from google.adk.openai import OpenAI  # Note: import from ADK

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        # Use OpenAI GPT-4o
        model=OpenAI(model="gpt-4o"),

        # Or GPT-4o-mini (cheaper)
        # model=OpenAI(model="gpt-4o-mini"),

        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### 3. Use Anthropic Claude Models

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-xxx
```

```python
# src/agents/analyst_agent.py

from google.adk.anthropic import Anthropic

def create_analyst_agent(...):
    agent = LlmAgent(
        name="AnalystAgent",
        # Use Claude 3.7 Sonnet
        model=Anthropic(model="claude-3-7-sonnet-20250219"),

        # Or Claude 3.5 Haiku (cheapest)
        # model=Anthropic(model="claude-3-5-haiku"),

        instruction=ANALYST_INSTRUCTION,
        tools=[],
        output_key="analysis"
    )
    return agent
```

### Model Selection Recommendations

| Scenario | Recommended Model | Reason |
|----------|-------------------|--------|
| Cost Priority | Gemini 2.5 Flash | Cheapest, fastest |
| Speed Priority | Gemini 2.0 Flash | Ultra-fast response, suitable for real-time |
| Quality Priority | Claude 3.7 Sonnet | Strong reasoning, high text quality |
| Balanced | GPT-4o | Speed and quality balanced |
| Testing/Development | Gemini Flash | High free quota, suitable for development |

---

## 📊 Data Management

### 1. View Database Contents

#### Method A: Use SQLite Command Line

```bash
# Enter database
sqlite3 data/insights.db

# View all articles
SELECT id, title, source, status, priority_score, created_at FROM articles ORDER BY created_at DESC LIMIT 10;

# View high-priority articles
SELECT id, title, priority_score FROM articles WHERE priority_score >= 0.8 ORDER BY priority_score DESC;

# View article count by source
SELECT source_name, COUNT(*) as count FROM articles GROUP BY source_name ORDER BY count DESC;

# View article count by status
SELECT status, COUNT(*) as count FROM articles GROUP BY status;

# Export to CSV
.headers on
.mode csv
.output articles_export.csv
SELECT * FROM articles WHERE created_at > date('now', '-7 days');
.output stdout
```

#### Method B: Use Python Script

Create query tool:

```python
# scripts/query_database.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import Database
from src.utils.config import Config
import json

def main():
    config = Config.from_env()
    db = Database.from_config(config)

    # Query high-score articles from last 7 days
    query = """
    SELECT id, title, source_name, priority_score, created_at
    FROM articles
    WHERE created_at > date('now', '-7 days')
      AND priority_score >= 0.7
    ORDER BY priority_score DESC, created_at DESC
    """

    results = db.conn.execute(query).fetchall()

    print(f"Found {len(results)} high-priority articles:")
    print("=" * 80)

    for row in results:
        print(f"[{row[4]}] ({row[3]:.2f}) {row[1]}")
        print(f"  Source: {row[2]}")
        print()

if __name__ == "__main__":
    main()
```

Usage:

```bash
python scripts/query_database.py
```

#### Method C: Use SQLite GUI Tools

Recommended tools:
- **DB Browser for SQLite** (Free): https://sqlitebrowser.org/
- **TablePlus** (Mac/Windows): https://tableplus.com/
- **DataGrip** (JetBrains): https://www.jetbrains.com/datagrip/

Steps:
1. Download and install the tool
2. Open `data/insights.db`
3. Use GUI to browse, query, export data

### 2. Clean Up Old Data

```python
# scripts/cleanup_old_data.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import Database
from src.utils.config import Config
from datetime import datetime, timedelta

def cleanup_old_articles(days: int = 90):
    """
    Delete articles older than N days

    Args:
        days: Keep data from last N days (default 90 days)
    """
    config = Config.from_env()
    db = Database.from_config(config)

    cutoff_date = datetime.now() - timedelta(days=days)

    # Count items to delete
    count_query = "SELECT COUNT(*) FROM articles WHERE created_at < ?"
    count = db.conn.execute(count_query, (cutoff_date,)).fetchone()[0]

    print(f"Found {count} articles older than {days} days")

    if count == 0:
        print("No articles to delete")
        return

    # Confirm
    confirm = input(f"Delete {count} articles? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled")
        return

    # Delete articles
    delete_query = "DELETE FROM articles WHERE created_at < ?"
    db.conn.execute(delete_query, (cutoff_date,))
    db.conn.commit()

    print(f"Deleted {count} articles")

    # VACUUM to reclaim space
    print("Optimizing database...")
    db.conn.execute("VACUUM")
    print("Done!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clean up old articles")
    parser.add_argument("--days", type=int, default=90, help="Keep articles from last N days")
    args = parser.parse_args()

    cleanup_old_articles(args.days)
```

Usage:

```bash
# Delete data older than 90 days
python scripts/cleanup_old_data.py

# Delete data older than 30 days
python scripts/cleanup_old_data.py --days 30
```

### 3. Export Data

```python
# scripts/export_data.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import Database
from src.utils.config import Config
import json
import csv
from datetime import datetime

def export_to_json(output_file: str = "export.json"):
    """Export data to JSON"""
    config = Config.from_env()
    db = Database.from_config(config)

    query = "SELECT * FROM articles ORDER BY created_at DESC"
    results = db.conn.execute(query).fetchall()

    # Get column names
    columns = [description[0] for description in db.conn.execute(query).description]

    # Convert to dict list
    data = [dict(zip(columns, row)) for row in results]

    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"Exported {len(data)} articles to {output_file}")

def export_to_csv(output_file: str = "export.csv"):
    """Export data to CSV"""
    config = Config.from_env()
    db = Database.from_config(config)

    query = "SELECT * FROM articles ORDER BY created_at DESC"
    results = db.conn.execute(query).fetchall()

    # Get column names
    columns = [description[0] for description in db.conn.execute(query).description]

    # Write CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(results)

    print(f"Exported {len(results)} articles to {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export database")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    parser.add_argument("--output", help="Output file name")
    args = parser.parse_args()

    if args.format == "json":
        output = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_to_json(output)
    else:
        output = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_to_csv(output)
```

Usage:

```bash
# Export to JSON
python scripts/export_data.py --format json

# Export to CSV
python scripts/export_data.py --format csv --output my_data.csv
```

---

## 🚀 Deployment Guide

### 1. Local Deployment (Automated)

#### Method A: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add scheduled task (run at 8 AM daily)
0 8 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner >> /path/to/logs/daily.log 2>&1

# Save and exit
```

#### Method B: systemd Service (Linux)

Create systemd service file:

```ini
# /etc/systemd/system/insightcosmos.service

[Unit]
Description=InsightCosmos Daily Pipeline
After=network.target

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/InsightCosmos
ExecStart=/path/to/venv/bin/python -m src.orchestrator.daily_runner
StandardOutput=append:/path/to/logs/daily.log
StandardError=append:/path/to/logs/error.log

[Install]
WantedBy=multi-user.target
```

Create timer file:

```ini
# /etc/systemd/system/insightcosmos.timer

[Unit]
Description=Run InsightCosmos Daily at 8 AM

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable timer
sudo systemctl enable insightcosmos.timer

# Start timer
sudo systemctl start insightcosmos.timer

# Check status
sudo systemctl status insightcosmos.timer
```

### 2. Deploy to Google Cloud Run

**Advantages**:
- Fully managed
- Auto-scaling (including scale to 0)
- Good integration with Google AI

**Steps**:

1. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Initialize database
RUN python -m src.memory.database

# Run
CMD ["python", "-m", "src.orchestrator.daily_runner"]
```

2. Deploy to Cloud Run:
```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud run deploy insightcosmos \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=xxx,EMAIL_ACCOUNT=xxx,EMAIL_PASSWORD=xxx
```

3. Set up Cloud Scheduler (scheduled execution):
```bash
gcloud scheduler jobs create http daily-pipeline \
  --schedule="0 8 * * *" \
  --uri="https://insightcosmos-xxx.run.app" \
  --http-method=GET
```

---

## 💾 Backup and Restore

### 1. Database Backup

#### Automated Backup Script

```python
# scripts/backup_database.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
from datetime import datetime
from src.utils.config import Config

def backup_database(backup_dir: str = "backups"):
    """
    Backup database

    Args:
        backup_dir: Backup directory
    """
    config = Config.from_env()
    db_path = Path(config.database_path)

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    # Create backup directory
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    # Backup filename (with timestamp)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"insights_backup_{timestamp}.db"

    # Copy database
    print(f"Backing up database to {backup_file}...")
    shutil.copy2(db_path, backup_file)

    # Compress backup (optional)
    import gzip
    with open(backup_file, 'rb') as f_in:
        with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Delete uncompressed backup
    backup_file.unlink()

    print(f"Backup completed: {backup_file}.gz")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Backup InsightCosmos database")
    parser.add_argument("--dir", default="backups", help="Backup directory")
    args = parser.parse_args()

    backup_database(args.dir)
```

Usage:

```bash
# Manual backup
python scripts/backup_database.py

# Specify backup directory
python scripts/backup_database.py --dir /path/to/backups
```

### 2. Restore Database

```bash
# Decompress backup
gunzip backups/insights_backup_20251126_080000.db.gz

# Overwrite existing database
cp backups/insights_backup_20251126_080000.db data/insights.db
```

---

## ❓ FAQ

### Q1: How to test if email configuration is correct?

```bash
# Use test script
python -c "
from src.tools.email_sender import EmailSender, EmailConfig
from src.utils.config import Config

config = Config.from_env()
email_config = EmailConfig(
    sender_email=config.email_account,
    sender_password=config.email_password
)

sender = EmailSender(email_config)
result = sender.send(
    to_email=config.email_account,
    subject='InsightCosmos Test Email',
    text_body='This is a test email from InsightCosmos.'
)
print(result)
"
```

### Q2: How to view pipeline execution logs?

```bash
# View recent logs
tail -f logs/insightcosmos.log

# Search for specific errors
grep "ERROR" logs/insightcosmos.log

# View logs for specific date
cat logs/insightcosmos.log | grep "2025-11-26"
```

### Q3: How to limit API usage costs?

1. Reduce number of articles processed daily
2. Use cheaper models (Gemini Flash)
3. Reduce RSS feeds and search query count

### Q4: How to speed up pipeline execution?

1. Use faster LLM models (Gemini 2.5 Flash)
2. Reduce number of data sources
3. Adjust `max_articles` parameter

### Q5: How to handle Rate Limit errors?

Add delays in orchestrator:

```python
# src/orchestrator/daily_runner.py

import time

for idx, article_dict in enumerate(pending_articles, 1):
    # Pause 10 seconds every 5 articles
    if idx % 5 == 0:
        self.logger.info("  Pausing to avoid rate limit...")
        time.sleep(10)

    # Analyze article
    result = runner.analyze_article(...)
```

---

## 🔧 Troubleshooting

### Issue 1: Cannot Send Email (Authentication Failed)

**Symptoms**:
```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Solutions**:

1. Ensure using **App Password** (not account password)
   - Gmail: https://support.google.com/accounts/answer/185833
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Generate new app password
   - Update password in `.env` `EMAIL_PASSWORD`

2. Ensure `.env` format is correct (no extra spaces):
   ```bash
   EMAIL_ACCOUNT=your_email@gmail.com
   EMAIL_PASSWORD=abcd efgh ijkl mnop  # Note: App Password spaces are normal
   ```

### Issue 2: Google Search Grounding Failed

**Symptoms**:
```
Error: Google Search Grounding failed
```

**Solutions**:

1. Ensure API Key is valid and has Search Grounding permissions
   - Visit [Google AI Studio](https://aistudio.google.com/apikey)
   - Confirm API Key status is "Active"
   - Confirm sufficient free quota

2. Check network connection (Search Grounding requires internet)

### Issue 3: Database Locked

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Cause**: Multiple processes accessing SQLite database simultaneously

**Solutions**:

1. Ensure no multiple pipelines running:
   ```bash
   ps aux | grep daily_runner
   # If multiple, kill extras
   kill <PID>
   ```

2. Increase SQLite timeout:
   ```python
   # src/memory/database.py

   self.conn = sqlite3.connect(
       database_path,
       timeout=30.0  # Increase timeout (default 5.0)
   )
   ```

### Issue 4: RSS Feed Cannot Be Read

**Symptoms**:
```
Error fetching RSS feed: HTTP 403 Forbidden
```

**Cause**: Some websites block crawlers or feedparser's default User-Agent

**Solution**:

Modify `src/tools/fetcher.py` to add User-Agent:

```python
# src/tools/fetcher.py

import feedparser
import requests

def fetch_rss_feed(feed_url: str) -> Dict[str, Any]:
    try:
        # Use requests to fetch content first (with custom User-Agent)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Then parse with feedparser
        feed = feedparser.parse(response.content)

        # ... continue processing
    except Exception as e:
        # ...
```

---

## 📈 Performance Metrics

Phase 1 Complete Edition performance metrics:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Daily Pipeline Execution | < 5 minutes | 2-3 minutes | ✅ |
| Weekly Pipeline Execution | < 2 minutes | ~17 seconds | ✅ |
| Single Article Analysis | < 15 seconds | 3-5 seconds | ✅ |
| RSS Batch Fetch (10 feeds) | < 30 seconds | 10-15 seconds | ✅ |
| Test Coverage | >= 95% | 97.4% | ✅ |

---

## 📞 Support and Community

### Get Help

- **GitHub Issues**: https://github.com/your-repo/InsightCosmos/issues
- **Documentation**: `docs/` folder contains complete technical documentation
- **API Reference**: `docs/implementation/api_reference.md`

### Related Documents

- [README.md](README.md) - Project description and quick start (English)
- [README_zh_TW.md](README_zh_TW.md) - Project description and quick start (繁體中文)
- [USER_MANUAL_zh_TW.md](USER_MANUAL_zh_TW.md) - Complete User Manual (繁體中文)
- [CLAUDE.md](CLAUDE.md) - Claude Code project guide
- [PROGRESS.md](PROGRESS.md) - Development progress tracking
- `docs/planning/` - Planning documents
- `docs/implementation/` - Implementation documents
- `docs/validation/` - Testing and validation reports
- `docs/optimization/` - Performance optimization records

### License

MIT License - See `LICENSE` file for details

---

**Last Updated**: 2025-11-26
**Maintainer**: Ray Chang
**Version**: 1.1.0 (Phase 1 Complete Edition)
