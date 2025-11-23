
# InsightCosmos – Personal AI Intelligence Universe
*Your Autonomous AI Agent for Daily & Weekly Intelligence Across AI + Robotics*

InsightCosmos 是一個為個人打造的「宇宙級 AI 情報引擎」。  
它每天、每週自動從網路各處收集與分析 AI 與 Robotics 相關的重要資訊，並將：

- 🔍 自動蒐集（AI 掃描宇宙）
- 🧠 自主分析（AI 推理洞察）
- 🧩 結構化記憶（向量知識庫）
- 📬 智能報告（Daily / Weekly）

寄到你的 Email。

InsightCosmos 採用 **Google AI Agent 模型（Tools / Memory / Planning）**，  
以「多代理、多工具、自主推理」為核心，成為你的個人情報宇宙。

---

# 🌌 Features

## ✔ Daily Intelligence Digest（每日情報摘要）
- RSS + Google Search 自動抓取
- LLM 分析每篇內容的技術、趨勢、背景脈絡
- 根據「對 Ray 個人價值」排序
- 5–10 則最重要的宇宙事件寄 Email 給你

## ✔ Weekly Deep Report（每週深度情報）
- 分析本週全部內容的主題分布
- 推理 2–3 個本週 AI / Robotics 主趨勢
- 給出你（Ray）下一週可採行的行動建議

## ✔ Multi-Agent Architecture（Google Agent Style）
InsightCosmos 由 3 個核心代理組成：

1. **Scout Agent** – 資訊探索  
2. **Analyst Agent** – 技術洞察  
3. **Curator Agent** – 報告生成

（企業版則包含 Hunter、Learner、Coordinator Agent）

## ✔ Memory Layer（個人向量宇宙）
- SQLite 儲存資訊原文與分析內容
- Embedding 形成你的私人知識宇宙

## ✔ Lightweight, Local, Personal
- 單人開發、單人維護
- 不需要伺服器、不需要大型 DB
- 可在筆電或工作環境每天跑一次

---

# 🏗️ System Architecture

```
┌───────────────────────────────┐
│      Daily / Weekly Runner     │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│          Scout Agent           │
│   - RSS / Google Search        │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│          Analyst Agent         │
│   - LLM Analysis               │
│   - Reflection                 │
│   - Priority Scoring           │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│         Memory Universe        │
│   - SQLite DB                  │
│   - Embedding Vector Store     │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│          Curator Agent         │
│   - Daily Digest               │
│   - Weekly Report              │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│         Email Delivery         │
└───────────────────────────────┘
```

---

# 📁 Project Structure

```
/InsightCosmos
 ├─ agents/
 │   ├─ scout_agent.py
 │   ├─ analyst_agent.py
 │   ├─ curator_daily.py
 │   ├─ curator_weekly.py
 │
 ├─ tools/
 │   ├─ fetcher.py
 │   ├─ google_search.py
 │   ├─ embedding.py
 │   ├─ email_sender.py
 │
 ├─ memory/
 │   ├─ db.py
 │   ├─ schema.sql
 │
 ├─ orchestrator/
 │   ├─ daily_runner.py
 │   ├─ weekly_runner.py
 │
 ├─ prompts/
 │   ├─ analyst_prompt.txt
 │   ├─ daily_prompt.txt
 │   ├─ weekly_prompt.txt
 │   ├─ reflection_prompt.txt
 │
 ├─ main_daily.py
 ├─ main_weekly.py
 ├─ config.py
 ├─ README.md
```

---

# ⚙️ Setup

## Install

```bash
pip install openai feedparser python-dotenv
```

## Configure `.env`

```
OPENAI_API_KEY=xxx
SEARCH_API_KEY=xxx
EMAIL_ACCOUNT=xxx
EMAIL_PASSWORD=xxx
```

## Initialize DB

```bash
python memory/db.py
```

## Run Daily Digest

```bash
python main_daily.py
```

## Run Weekly Report

```bash
python main_weekly.py
```

---

# 🚀 Roadmap

### v1.0（個人宇宙）
- Daily & Weekly Intelligence  
- SQLite + Embedding Memory  
- RSS + Google Search Tools  
- Email 推送

### v2.0（智慧宇宙）
- 自動來源發現  
- 主題偏好學習  
- 趨勢聚類、持續追蹤  
- 星际級情報圖譜（Knowledge Nebula）

### v3.0（企業宇宙）
- 多代理完整架構  
- Hunter / Learner / Coordinator  
- SaaS Intelligence Platform  

---

# ✨ Slogan Examples
- “Your Personal Intelligence Universe.”
- “See the Patterns of the AI Cosmos.”
- “Exploring the Universe of AI Insight.”
- “Your AI Agent for Knowledge Across the Cosmos.”

---

# 🎨 Logo Prompt for Midjourney

```
InsightCosmos logo, cosmic intelligence theme, sleek modern lines, nebula-inspired shapes, glowing orbit rings, minimalistic futuristic emblem, dark space palette with blue-purple gradients, clean vector style, AI and robotics symbolism subtly integrated, ultra-high resolution, branding-ready, 8k
```

---

# ✨ Author
Ray Chang  
InsightCosmos Project  
Personal AI Intelligence Universe
