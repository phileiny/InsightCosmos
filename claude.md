# InsightCosmos - Claude Code 專案一致性指南

> **文件版本**: 1.0
> **建立日期**: 2025-11-19
> **專案階段**: Phase 1 - 個人宇宙版
> **技術框架**: Google ADK (Agent Development Kit)

---

## 📋 文件目的

本文件是 InsightCosmos 專案的**核心一致性指南**，用於：

1. **統一開發理念** - 確保所有開發遵循相同的架構哲學
2. **保持技術一致** - 明確技術選型與實現標準
3. **指導 AI 協作** - 為 Claude Code 提供專案上下文
4. **文件系統規範** - 建立「規劃→實作→驗證」的開發節奏
5. **說明文件語言統一** - 一律使用繁體中文記錄與備註

---

## 🌌 專案核心理念

### 專案定位

InsightCosmos 是一個**個人 AI 情報宇宙引擎**，透過多代理系統自動收集、分析、結構化 AI 與 Robotics 領域的重要資訊，並透過 Daily/Weekly 報告形式提供智慧洞察。

**核心價值主張**:
- 🔍 **自動探索** - AI Agent 主動掃描宇宙級資訊源
- 🧠 **自主推理** - LLM 深度分析與洞察提取
- 🧩 **結構化記憶** - Vector Memory + SQLite 知識庫
- 📬 **智慧報告** - 個人化的每日／每週情報摘要

### 設計哲學

基於 **Google AI Agent 模型**的三大支柱：

```
┌─────────────────────────────────────┐
│     Google Agent 三大支柱            │
│                                     │
│  Tools    +    Memory    +  Planning│
│  工具使用      記憶管理      規劃推理   │
└─────────────────────────────────────┘
```

**關鍵原則**:

1. **Think-Act-Observe 循環** - 所有 Agent 遵循「思考→行動→觀察→迭代」模式
2. **模組化多 Agent** - 單一職責 Agent 協作，而非單一全能 Agent
3. **記憶驅動決策** - Session（短期）+ Memory（長期）雙層記憶
4. **工具原子化** - 每個工具職責單一、文件清晰、輸出結構化
5. **品質優先** - 從 Day 0 建立可觀測性與評估機制
6. **工具正確** — 當問題與「程式庫／framework 的使用方式、設定步驟、API 文件、版本差異」有關時，一律優先呼叫 `context7` 這個 MCP 查詢最新官方文件與程式碼範例，再回答我。
- 回答時請註明你是根據 Context7 取得的文件（例如來源套件與版本說明）。

---

## 🏗️ 技術架構總覽

### 系統架構圖

```
┌───────────────────────────────────────────────────────────┐
│                  InsightCosmos v1.0                       │
│                   (個人宇宙版)                             │
└───────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│            Daily / Weekly Orchestrator                    │
│          (SequentialAgent 順序編排)                        │
└───────────────────────────────────────────────────────────┘
                            ↓
┌─────────────┬─────────────┬─────────────┬─────────────────┐
│             │             │             │                 │
│  Scout      │  Analyst    │  Curator    │  Email          │
│  Agent      │  Agent      │  Agent      │  Delivery       │
│             │             │             │                 │
│ RSS +       │ LLM 分析    │ Daily/      │ SMTP            │
│ Search      │ + 推理      │ Weekly      │ 發送            │
│             │             │ 報告        │                 │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│                  Memory Universe                          │
│  ┌──────────────────┐      ┌──────────────────┐          │
│  │  SQLite DB       │      │  Vector Store    │          │
│  │  (結構化存儲)     │      │  (Embedding)     │          │
│  └──────────────────┘      └──────────────────┘          │
└───────────────────────────────────────────────────────────┘
```



### Agent 職責分工

| Agent | 類型 | 職責 | 輸出 |
|-------|------|------|------|
| **Scout Agent** | 資訊探索 | RSS + Google Search 收集、去重 | `raw_articles[]` |
| **Analyst Agent** | 技術洞察 | LLM 分析、打分、Embedding | `analyzed_articles[]` |
| **Curator Agent** | 報告生成 | Daily Digest / Weekly Report | `email_content` |

### 技術棧選型

#### 核心框架
- **ADK (Agent Development Kit)** - Google 官方 Agent 開發框架
- **Python 3.10+** - 開發語言
- **Gemini 2.5 Flash** - 主力 LLM（效率優先）
- **Gemini 2.5 Pro** - 複雜分析場景（可選）

#### 工具與服務
- **RSS Parser** - `feedparser` 套件
- **Google Search** - ADK 內建 `google_search` 工具
- **Embedding** - ADK 內建 `embedding` 工具
- **SQLite** - 輕量級結構化儲存
- **Email** - SMTP（可使用 Gmail API）

#### 開發工具
- **Version Control** - Git
- **Environment** - `.env` + `python-dotenv`
- **Testing** - ADK Evaluation Framework
- **Observability** - LoggingPlugin + OpenTelemetry（可選）

---

## 📁 專案結構規範

### 目錄組織

```
/InsightCosmos
├─ docs/                        # 文件系統
│   ├─ planning/                # 規劃階段文件
│   │   ├─ phase1_overview.md   # 第一階段總覽
│   │   ├─ agent_design.md      # Agent 設計文件
│   │   └─ tools_spec.md        # 工具規格說明
│   ├─ implementation/          # 實作階段文件
│   │   ├─ dev_log.md           # 開發日誌
│   │   └─ api_reference.md     # API 參考
│   ├─ validation/              # 驗證階段文件
│   │   ├─ test_cases.json      # 測試案例
│   │   └─ eval_config.json     # 評估設定
│   └─ reference/               # 參考資料（已有）
│       ├─ 5D_AI_Agent_Summary.md
│       ├─ adk-速查文檔.html
│       └─ ...
│
├─ src/                         # 原始碼
│   ├─ agents/                  # Agent 實作
│   │   ├─ scout_agent.py
│   │   ├─ analyst_agent.py
│   │   └─ curator_agent.py
│   ├─ tools/                   # 工具函式
│   │   ├─ fetcher.py
│   │   ├─ google_search.py
│   │   ├─ embedding.py
│   │   └─ email_sender.py
│   ├─ memory/                  # 記憶層
│   │   ├─ db.py
│   │   └─ schema.sql
│   ├─ orchestrator/            # 編排器
│   │   ├─ daily_runner.py
│   │   └─ weekly_runner.py
│   └─ utils/                   # 工具類
│       ├─ config.py
│       └─ logger.py
│
├─ prompts/                     # Prompt 模板
│   ├─ analyst_prompt.txt
│   ├─ daily_prompt.txt
│   ├─ weekly_prompt.txt
│   └─ reflection_prompt.txt
│
├─ tests/                       # 測試文件
│   ├─ unit/
│   ├─ integration/
│   └─ evaluation/
│
├─ data/                        # 資料存儲
│   ├─ insights.db              # SQLite 資料庫
│   └─ embeddings/              # 向量儲存
│
├─ .env.example                 # 環境變數模板
├─ .gitignore
├─ requirements.txt             # 依賴清單
├─ README.md                    # 專案說明
├─ claude.md                    # 本文件
└─ main.py                      # 入口檔案
```



---

## 🔄 開發節奏：規劃→實作→驗證

### Phase 1: 規劃階段 (Planning)

**目標**：在撰寫程式碼之前完成架構設計與文件

**交付物**：
1. `docs/planning/phase1_overview.md` - 第一階段總覽  
2. `docs/planning/agent_design.md` - 三大 Agent 詳細設計  
3. `docs/planning/tools_spec.md` - 工具函式規格  
4. `docs/planning/memory_design.md` - Memory 層設計  
5. `docs/planning/eval_strategy.md` - 評估策略  

**驗收標準**：
- [ ] 每個 Agent 的 instruction、tools、output_key 明確  
- [ ] 每個工具的輸入／輸出／錯誤處理定義清晰  
- [ ] Memory schema 完整設計  
- [ ] 測試案例清單準備完成  

### Phase 2: 實作階段 (Implementation)

**目標**：依照規劃文件實現程式碼

**開發順序**：
1. **Memory Layer** → 先建立資料層  
2. **Tools** → 實作工具函式  
3. **Scout Agent** → 第一個 Agent  
4. **Analyst Agent** → 核心分析邏輯  
5. **Curator Agent** → 報告產生  
6. **Orchestrator** → 串接整體流程  

**開發規範**：
- 每個模組完成後需更新 `docs/implementation/dev_log.md`  
- 重要程式碼必須包含 docstring  
- 工具函式必須具有型別標註  

### Phase 3: 驗證階段 (Validation)

**目標**：確保品質與功能正確性

**驗證清單**：
1. **單元測試** - 每個工具函式獨立測試  
2. **整合測試** - Agent 協作流程測試  
3. **ADK Evaluation** - 使用官方評估框架  
4. **人工審查** - Sample outputs 內容品質檢查  

**交付物**：
- `docs/validation/test_results.md` - 測試報告  
- `docs/validation/eval_metrics.md` - 評估指標  
- `docs/validation/known_issues.md` - 已知問題清單  

---

## 🎯 Phase 1 實施範圍

### ✅ 包含功能

**核心功能**：
1. ✅ **Scout Agent** - RSS + Google Search 自動收集  
2. ✅ **Analyst Agent** - LLM 分析與優先度評分  
3. ✅ **Curator Agent** - Daily Digest + Weekly Report  
4. ✅ **Memory Universe** - SQLite + Embedding  
5. ✅ **Email Delivery** - SMTP 推送  

**Agent 架構**：
- Sequential Agent（順序編排）  
- LLM Agent（核心推理）  
- Tool Integration（工具整合）  
- Session Management（會話管理）  

**品質保證**：
- LoggingPlugin（日誌紀錄）  
- Basic Evaluation（基礎評估）  

### ❌ 不包含功能（v2/v3）

**暫不實作**：
- ❌ Hunter / Learner / Coordinator Agent（企業版）  
- ❌ 自動來源探索與學習  
- ❌ 主題偏好自適應  
- ❌ 知識圖譜（Knowledge Nebula）  
- ❌ 多使用者支援（Multi-user）  
- ❌ A2A Protocol（跨 Agent 通訊）  
- ❌ Vertex AI 部署（本地優先）  

---

## 📐 程式碼編寫標準

### Agent 設計規範

**強制要求**：

```python
# ✅ 正確的 Agent 設計
agent = LlmAgent(
    name="ScoutAgent",  # 清晰命名
    model=Gemini(model="gemini-2.5-flash-lite"),  # 指定模型
    instruction="""
    你的任務是從 RSS 和 Google Search 收集 AI 與 Robotics 相關文章。

    步驟：
    1. 使用 fetch_rss 工具取得 RSS 文章
    2. 使用 google_search 工具搜尋關鍵字
    3. 合併並去重結果
    4. 回傳結構化文章列表
    """,  # 詳細指令
    tools=[fetch_rss, google_search],  # 工具列表
    output_key="raw_articles"  # 輸出鍵
)
```




**關鍵要求**:
1. ✅ 完整的 docstring（LLM 依賴此理解工具）
2. ✅ 型別標註（Python Type Hints）
3. ✅ 結構化回傳值（dict 格式）
4. ✅ 錯誤處理與建議（具可回復性）
5. ✅ Example 示例（協助理解）

### Prompt 設計規範

**存放位置**：`prompts/` 目錄

**命名規範**：
- `{agent_name}_prompt.txt` - Agent 主指令  
- `{task}_reflection_prompt.txt` - Reflection 提示  

**Prompt 結構**：

```
# {Agent Name} Instruction

## 角色定義
你是一個 {角色描述}，專注於 {核心職責}。

## 任務目標
{具體目標說明}

## 執行步驟
1. {步驟 1}
2. {步驟 2}
3. {步驟 3}

## 可用工具
- tool_1: {用途}
- tool_2: {用途}

## 輸出格式
{期望的輸出結構}

## 質量標準
- 標準 1
- 標準 2

## 示例
Input: {示例輸入}  
Output: {示例輸出}
```

---

## 🔍 質量保證原則

### 可觀測性（Observability）

**必須實施**：

```python
from google.adk.plugins import LoggingPlugin

# 所有 Agent 啟用日誌
agent = LlmAgent(
    plugins=[LoggingPlugin()]
)
```

**日誌等級**：
- `DEBUG` - 開發階段  
- `INFO` - 生產環境  
- `ERROR` - 錯誤追蹤  

### 評估框架（Evaluation）

**測試案例結構**：

```json
{
  "eval_set_id": "insightcosmos_v1",
  "eval_cases": [
    {
      "eval_id": "scout_basic",
      "description": "Scout Agent 基本收集功能",
      "conversation": [
        {
          "user_content": "收集今日 AI 新聞",
          "expected_tools": ["fetch_rss", "google_search"],
          "final_response": {...}
        }
      ]
    }
  ]
}
```

**評估指標**：
- `tool_trajectory_avg_score` >= 0.9（工具使用正確性）  
- `response_match_score` >= 0.8（輸出品質）  

---

## 🚀 部署與運行

### 環境配置

**.env 必需變數**：

```bash
# Google Gemini API (Required)
# Get API Key from: https://aistudio.google.com/apikey
# This single key is used for:
# - LLM inference (Gemini 2.0 Flash)
# - Google Search Grounding (no additional Search Engine ID needed)
GOOGLE_API_KEY=your_gemini_api_key

# Email
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Database
DATABASE_PATH=data/insights.db

# 個人配置
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems
```

### 運行命令

```bash
# 初始化資料庫
python src/memory/db.py

# 執行日報
python orchestrator/daily_runner.py

# 執行週報
python orchestrator/weekly_runner.py

# 執行評估
adk eval src/agents evalset.json --config_file_path=eval_config.json
```



**禁止事項**:
```python
# ❌ 避免的設計
agent = Agent(
    instruction="收集文章",  # 指令過於模糊
    tools=[...]  # 未明確工具用途
)
```

### 工具設計規範

**標準模板**:

```python
def tool_name(param: str, tool_context: ToolContext = None) -> dict:
    """
    工具功能描述（LLM 會讀取這個）

    Args:
        param: 參數說明
        tool_context: ADK 上下文（可選）

    Returns:
        dict: {
            "status": "success" | "error",
            "data": {...},  # 成功時返回
            "error_message": str,  # 錯誤時返回
            "suggestion": str  # 錯誤時的修正建議
        }

    Example:
        >>> tool_name("test")
        {"status": "success", "data": {...}}
    """
    try:
        # 實作邏輯
        result = do_something(param)
        return {"status": "success", "data": result}
    except SpecificError as e:
        return {
            "status": "error",
            "error_type": "specific_error",
            "error_message": str(e),
            "suggestion": "具體的修正建議"
        }
```



---

## 📚 學習資源參考

### 官方文件
- [ADK 完整文件](https://google.github.io/adk-docs/)
- [Agents 概述](https://google.github.io/adk-docs/agents/)
- [Tools 開發](https://google.github.io/adk-docs/tools/)
- [Memory 系統](https://google.github.io/adk-docs/sessions/memory/)
- [評估框架](https://google.github.io/adk-docs/evaluate/)

### 內部參考
- `docs/reference/5D_AI_Agent_Summary.md` - ADK 學習總結
- `docs/reference/adk-速查文檔.html` - 快速查閱

---

## 🤖 Claude Code 使用指南

### 角色定位

Claude Code 作為開發助手，應該：

1. **理解上下文** — 閱讀本文檔理解專案整體架構  
2. **遵循規範** — 嚴格按照編碼標準生成程式碼  
3. **文件優先** — 先寫文件再寫程式碼  
4. **品質保證** — 主動建議測試與評估  
5. **增量開發** — 按照 Planning → Implementation → Validation 節奏  

### 常見任務模板

**任務 1: 設計新 Agent**
```
請按照 docs/planning/agent_design.md 模板，設計 {AgentName}:
1. 明確職責與目標
2. 定義 instruction
3. 列出需要的 tools
4. 設計輸出格式
5. 準備測試案例
```

**任務 2: 實作工具函式**
```
請實作 {tool_name} 工具：
1. 遵循 claude.md 中的工具設計規範
2. 包含完整 docstring
3. 結構化回傳值
4. 錯誤處理與建議
5. 提供使用示例
```

**任務 3: 更新文件**
```
完成 {feature} 後，更新：
1. docs/implementation/dev_log.md
2. docs/implementation/api_reference.md
3. README.md（如有必要）
```

---

## 🎯 成功標準

### Phase 1 完成定義

**功能完整性**：
- [x] Scout Agent 能自動收集文章  
- [x] Analyst Agent 能分析並評分  
- [x] Curator Agent 能生成日報／週報  
- [x] Memory 能持久化儲存  
- [x] Email 能成功發送  

**品質標準**：
- [x] 所有 Agent 有完整文件  
- [x] 所有工具有測試案例  
- [x] 評估通過率 >= 80%  
- [x] 日誌可追蹤完整流程  
- [x] 錯誤處理涵蓋主要場景  

**使用者體驗**：
- [x] 日報內容有價值（5–10 條高品質資訊）  
- [x] 週報能識別趨勢（2–3 個主題）  
- [x] 報告格式清晰易讀  
- [x] 系統能自動運行（無需人工干預）  

---

## 📝 版本歷史

| 版本 | 日期 | 變更說明 |
|------|------|---------|
| 1.1 | 2025-11-23 | 遷移至 Gemini Search Grounding，移除 Custom Search Engine ID 要求 |
| 1.0 | 2025-11-19 | 初始版本，定義 Phase 1 規範 |

---

## 🔗 相關文件

- `README.md` - 專案說明與快速開始  
- `docs/planning/phase1_overview.md` - 第一階段詳細規劃  
- `docs/reference/5D_AI_Agent_Summary.md` - ADK 技術學習總結  

---

**最後更新**：2025-11-19  
**維護者**：Ray 張瑞涵  
**專案倉庫**：InsightCosmos

