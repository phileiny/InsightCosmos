<p align="center">
  <img src="InsightCosmos_logo.png" alt="InsightCosmos Logo" width="200"/>
</p>

<h1 align="center">InsightCosmos</h1>
<p align="center"><em>Personal AI Intelligence Universe</em></p>
<p align="center">Your Autonomous AI Agent for Daily & Weekly Intelligence Across AI + Robotics</p>

<p align="center">
  <strong>English</strong> | <a href="README_zh_TW.md">繁體中文</a>
</p>

---

InsightCosmos is a "universe-class AI intelligence engine" built for individuals.
It automatically collects and analyzes important AI and Robotics information from across the web daily and weekly, delivering:

- 🔍 Automated Collection (AI scans the universe)
- 🧠 Autonomous Analysis (AI reasoning & insights)
- 🧩 Structured Memory (Vector knowledge base)
- 📬 Smart Reports (Daily / Weekly)

Directly to your Email.

InsightCosmos leverages the **Google AI Agent Model (Tools / Memory / Planning)**,
with "multi-agent, multi-tool, autonomous reasoning" at its core, becoming your personal intelligence universe.

---

# 🌌 Features

## ✔ Daily Intelligence Digest
- Automatic RSS + Google Search collection
- LLM analysis of technical content, trends, and context for each article
- Prioritized by personal value relevance
- 5-10 most important universe events delivered to your Email

## ✔ Weekly Deep Report
- Analysis of the week's content topic distribution
- Identification of 2-3 major AI/Robotics trends
- Actionable recommendations for the coming week

## ✔ Multi-Agent Architecture (Google Agent Style)
InsightCosmos consists of 3 core agents:

1. **Scout Agent** - Information exploration
2. **Analyst Agent** - Technical insights
3. **Curator Agent** - Report generation

(Enterprise edition includes Hunter, Learner, Coordinator Agents)

## ✔ Memory Layer (Personal Vector Universe)
- SQLite stores original content and analysis
- Embeddings form your private knowledge universe

## ✔ Lightweight, Local, Personal
- Single developer, single maintainer
- No servers, no large databases required
- Can run daily on a laptop or workstation

---

# 🏗️ System Architecture

<p align="center">
  <img src="system structure.png" alt="InsightCosmos System Architecture" width="700"/>
</p>

---

# 📁 Project Structure

```
InsightCosmos/
├── src/
│   ├── agents/                    # AI Agent modules
│   │   ├── scout_agent.py         # Information exploration agent
│   │   ├── analyst_agent.py       # Technical analysis agent
│   │   ├── curator_daily.py       # Daily report agent
│   │   └── curator_weekly.py      # Weekly report agent
│   │
│   ├── tools/                     # Tool library
│   │   ├── fetcher.py             # RSS fetcher
│   │   ├── google_search_grounding.py    # Google Search Grounding
│   │   ├── content_extractor.py   # Content extraction tool
│   │   ├── digest_formatter.py    # Report formatter
│   │   ├── email_sender.py        # Email sender
│   │   ├── trend_analysis.py      # Trend analysis tool
│   │   └── vector_clustering.py   # Vector clustering tool
│   │
│   ├── memory/                    # Memory layer modules
│   │   ├── database.py            # SQLite database management
│   │   ├── article_store.py       # Article storage management
│   │   ├── embedding_store.py     # Vector storage management
│   │   ├── models.py              # Data model definitions
│   │   └── schema.sql             # Database schema
│   │
│   ├── orchestrator/              # Orchestrator modules
│   │   ├── daily_runner.py        # Daily workflow orchestration
│   │   ├── weekly_runner.py       # Weekly workflow orchestration
│   │   └── utils.py               # Orchestrator utilities
│   │
│   └── utils/                     # Common utilities
│       ├── config.py              # Configuration management
│       └── logger.py              # Logging management
│
├── prompts/                       # Prompt templates
│   ├── analyst_prompt.txt         # Analyst agent prompt
│   ├── daily_prompt.txt           # Daily report prompt
│   ├── weekly_prompt.txt          # Weekly report prompt
│   └── scout_prompt.txt           # Scout agent prompt
│
├── tests/                         # Test modules
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── evaluation/                # Evaluation tests
│
├── docs/                          # Documentation
│   ├── planning/                  # Planning documents
│   ├── implementation/            # Implementation documents
│   └── optimization/              # Optimization records
│
├── data/                          # Data storage
│   └── insights.db                # SQLite database
│
├── scripts/                       # Execution scripts
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
└── README.md                      # Project description
```

---

# ⚙️ Setup

## System Requirements

- Python 3.10+ (3.11 or 3.13 recommended)
- At least 4GB RAM
- Stable internet connection
- Google Gemini API Key

## Install

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
# Edit .env with your configuration

# 5. Initialize database
python -m src.memory.database

# 6. Test run (no email sent)
python -m src.orchestrator.daily_runner --dry-run
```

## Configure `.env`

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

# Database (Optional, defaults to data/insights.db)
DATABASE_PATH=data/insights.db

# Personal Configuration
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems

# Log Level
LOG_LEVEL=INFO
```

> **Gmail App Password**: Go to [Google Account Security](https://myaccount.google.com/security) → 2-Step Verification → App passwords

---

# 📬 Usage

## Daily Pipeline

The Daily Pipeline executes three stages:
1. **Scout Agent**: Collects articles from RSS and Google Search
2. **Analyst Agent**: Analyzes articles using LLM, scores, and extracts insights
3. **Curator Agent**: Generates and sends daily digest email

```bash
# Production mode (collect + analyze + send email)
python -m src.orchestrator.daily_runner

# Test mode (no email sent)
python -m src.orchestrator.daily_runner --dry-run

# Verbose logging mode
python -m src.orchestrator.daily_runner --verbose
```

| Stage | Estimated Time |
|-------|----------------|
| Scout (Collection) | 30-60 seconds |
| Analyst (Analysis) | 1-3 minutes |
| Curator (Report) | 10-30 seconds |
| **Total** | **2-5 minutes** |

## Weekly Pipeline

The Weekly Pipeline analyzes a week's articles, performing topic clustering and trend identification.

```bash
# Production mode
python -m src.orchestrator.weekly_runner

# Test mode
python -m src.orchestrator.weekly_runner --dry-run

# Specify date range
python -m src.orchestrator.weekly_runner --week-start 2025-11-18 --week-end 2025-11-24
```

| Item | Description |
|------|-------------|
| Topic Clusters | Groups articles into 3-7 topic clusters by similarity |
| Hot Trends | High-frequency, high-priority keywords |
| Emerging Topics | Low-frequency but high-priority emerging keywords |

---

# ⏰ Automation

## Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Run daily digest at 8 AM every day
0 8 * * * cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.daily_runner >> logs/daily.log 2>&1

# Run weekly report at 8 PM every Sunday
0 20 * * 0 cd /path/to/InsightCosmos && /path/to/venv/bin/python -m src.orchestrator.weekly_runner >> logs/weekly.log 2>&1
```

## Windows Task Scheduler

1. Open Task Scheduler
2. Create a basic task, set trigger (daily at 8 AM)
3. Set action:
   - **Program**: `C:\path\to\InsightCosmos\venv\Scripts\python.exe`
   - **Arguments**: `-m src.orchestrator.daily_runner`
   - **Start in**: `C:\path\to\InsightCosmos`

---

# 🎯 Customization

## Modify Interest Areas

Edit `USER_INTERESTS` in `.env`:

```bash
# Example 1: AI and Robotics
USER_INTERESTS=AI,Robotics,Multi-Agent Systems

# Example 2: LLM Focus
USER_INTERESTS=Large Language Models,Prompt Engineering,AI Agents,RAG

# Example 3: Cross-domain
USER_INTERESTS=AI,Healthcare,Drug Discovery,Medical Imaging
```

## Adjust RSS Sources

Edit `DEFAULT_FEEDS` in `src/agents/scout_agent.py`.

## Switch LLM Models

InsightCosmos uses Google ADK, supporting multiple LLMs:

| Scenario | Recommended Model | Reason |
|----------|-------------------|--------|
| Cost Priority | Gemini 2.5 Flash | Cheapest, fastest |
| Quality Priority | Claude 3.7 Sonnet | Strong reasoning |
| Balanced | GPT-4o | Speed and quality balanced |

---

# 📊 Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Daily Pipeline Execution | < 5 minutes | 2-3 minutes |
| Weekly Pipeline Execution | < 2 minutes | ~17 seconds |
| Single Article Analysis | < 15 seconds | 3-5 seconds |
| Test Coverage | >= 95% | 97.4% |

---

# 🔧 Troubleshooting

## Cannot Send Email

Ensure you're using Gmail **App Password** (not account password):
- Google Account → Security → 2-Step Verification → App passwords

## Google Search Grounding Failed

Ensure API Key is valid and has sufficient quota: [Google AI Studio](https://aistudio.google.com/apikey)

## Database Locked

Ensure no multiple pipelines are running simultaneously:
```bash
ps aux | grep daily_runner
```

---

# 🚀 Roadmap

### v1.0 (Personal Universe) ✅
- Daily & Weekly Intelligence
- SQLite + Embedding Memory
- RSS + Google Search Tools
- Email Delivery

### v2.0 (Smart Universe)
- Automatic source discovery
- Topic preference learning
- Trend clustering and tracking
- Knowledge Graph (Knowledge Nebula)

### v3.0 (Enterprise Universe)
- Full multi-agent architecture
- Hunter / Learner / Coordinator
- SaaS Intelligence Platform

---

# 📚 Documentation

- [USER_MANUAL.md](USER_MANUAL.md) - Complete User Manual (English)
- [USER_MANUAL_zh_TW.md](USER_MANUAL_zh_TW.md) - Complete User Manual (繁體中文)
- [CLAUDE.md](CLAUDE.md) - Claude Code Project Guide
- [PROGRESS.md](PROGRESS.md) - Development Progress Tracking
- `docs/planning/` - Planning Documents
- `docs/implementation/` - Implementation Documents

---

# ✨ Slogan

> "Your Personal Intelligence Universe."

---

# ✨ Author

**Ray Chang**
InsightCosmos Project
Personal AI Intelligence Universe

---

# 📄 License

MIT License
