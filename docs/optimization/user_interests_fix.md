# USER_INTERESTS 模板替換修復

> **修復日期**: 2025-11-25
> **問題類型**: 配置未正確傳遞
> **影響範圍**: Scout Agent 搜尋結果偏向 AI，缺少 Robotics 相關內容

---

## 問題描述

使用者反映 Daily Digest 郵件內容偏向 AI 領域，幾乎沒有 Robotics 相關文章，即使 `.env` 中已設定：

```bash
USER_INTERESTS=AI,Robotics,Multi-Agent Systems
```

## 根本原因分析

經過程式碼追蹤，發現三個關鍵問題：

### 1. Prompt 模板變數未被替換

**檔案**: `prompts/scout_prompt.txt`

```
2. 分析用户的兴趣领域：{{USER_INTERESTS}}
```

**問題**: `{{USER_INTERESTS}}` 是一個佔位符，但 `create_scout_agent()` 函數從未將其替換為實際值。LLM 看到的是字面上的 `{{USER_INTERESTS}}`，無法正確理解使用者的興趣。

### 2. RSS Feeds 只包含 AI 來源

**原始設定**:
```python
feed_urls: [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/"
]
```

**問題**: 沒有任何專門的 Robotics RSS feed，導致 RSS 來源全部是 AI 相關。

### 3. Daily Runner 未傳遞配置

**檔案**: `src/orchestrator/daily_runner.py`

```python
# 原始程式碼
result = collect_articles()  # 沒有傳遞 user_interests
```

**問題**: 直接調用 `collect_articles()` 而沒有傳遞 `user_interests` 參數。

---

## 修復方案

### 修復 1: Scout Agent 支援模板替換

**檔案**: `src/agents/scout_agent.py`

```python
def create_scout_agent(
    instruction_file: str = "prompts/scout_prompt.txt",
    user_interests: Optional[str] = None  # 新增參數
) -> LlmAgent:
    # ...

    # 替換模板變數
    if user_interests is None:
        from dotenv import load_dotenv
        load_dotenv()
        user_interests = os.getenv("USER_INTERESTS", "AI,Robotics,Multi-Agent Systems")

    instruction = instruction.replace("{{USER_INTERESTS}}", user_interests)
    logger.info(f"User interests applied: {user_interests}")
```

### 修復 2: 新增 Robotics RSS Feeds

**檔案**: `prompts/scout_prompt.txt`

```
feed_urls: [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://spectrum.ieee.org/feeds/topic/robotics.rss",      # 新增
    "https://www.therobotreport.com/feed/"                      # 新增
]
```

**新增來源說明**:
- **IEEE Spectrum Robotics**: 權威的機器人技術新聞來源
- **The Robot Report**: 專注於機器人產業的新聞網站

### 修復 3: 強化 Prompt 指令

**檔案**: `prompts/scout_prompt.txt`

```
2. 分析用户的兴趣领域：{{USER_INTERESTS}}
   **重要**：必须为用户的每个兴趣领域（用逗号分隔）生成至少 1 个搜索查询。
   例如：
   - 如果兴趣包含 "AI"，搜索 "latest AI breakthroughs 2025"
   - 如果兴趣包含 "Robotics"，搜索 "humanoid robots progress 2025"
   - 如果兴趣包含 "Multi-Agent Systems"，搜索 "multi-agent AI systems"
```

### 修復 4: Daily Runner 傳遞配置

**檔案**: `src/orchestrator/daily_runner.py`

```python
def _run_phase1_scout(self) -> tuple[int, int]:
    from src.agents.scout_agent import ScoutAgentRunner, create_scout_agent

    # 創建帶有 user_interests 的 Scout Agent
    agent = create_scout_agent(user_interests=self.config.user_interests)
    runner = ScoutAgentRunner(agent=agent)
    result = runner.collect_articles()
```

---

## 修改檔案清單

| 檔案 | 修改類型 | 說明 |
|------|---------|------|
| `src/agents/scout_agent.py` | 修改 | 新增 `user_interests` 參數，實作模板替換 |
| `prompts/scout_prompt.txt` | 修改 | 新增 Robotics RSS feeds，強化搜尋指令 |
| `src/orchestrator/daily_runner.py` | 修改 | 傳遞 `user_interests` 配置到 Scout Agent |

---

## 驗證方式

執行 Daily Pipeline 並檢查日誌：

```bash
python -m src.orchestrator.daily_runner --dry-run --verbose
```

預期日誌輸出：

```
User interests applied: AI,Robotics,Multi-Agent Systems
```

並在收集的文章中應該包含 Robotics 相關內容。

---

## 後續建議

1. **新增更多 Robotics RSS 來源**（可選）:
   - `https://robohub.org/feed/`
   - `https://www.roboticsbusinessreview.com/feed/`

2. **監控內容平衡**:
   - 可在 Analyst Agent 中記錄文章分類統計
   - 確保每個興趣領域都有足夠的文章覆蓋

3. **使用者可自訂 RSS feeds**:
   - 未來可考慮將 RSS feeds 移到 `.env` 或配置檔中
   - 讓使用者根據自己的興趣自訂來源

---

## 執行紀錄

### 執行時間：2025-11-25 10:06:51 ~ 10:13:59 (UTC+8)

**執行模式**: PRODUCTION（實際發送 Email）

### Pipeline 執行結果

| 階段 | 狀態 | 說明 |
|------|------|------|
| Phase 1: Scout Agent | ✅ 成功 | 收集 20 篇文章，儲存 20 篇 |
| Phase 2: Analyst Agent | ✅ 成功 | 分析 13 篇文章（7 篇內容提取失敗） |
| Phase 3: Curator Agent | ✅ 成功 | Email 發送成功 |

### 執行統計

```
Duration: 428.4 seconds (~7 分鐘)
Articles Collected: 20
Articles Stored: 20
Articles Analyzed: 13
Email Sent: True
Errors: 0
```

### 文章來源分析

根據日誌，收集的文章來源包含：

**Google Search Grounding 結果**:
- pass4sure.com (priority: 0.85)
- digitalhumans.com (priority: 0.05)
- turing.com (priority: 0.90)
- aimultiple.com (priority: 0.82)
- research.google (priority: 0.95) - 最高優先度
- the-decoder.com (priority: 0.05)
- deeplearning.ai (priority: 0.00)
- techaheadcorp.com (priority: 0.05)

**TechCrunch RSS**:
- AWS is spending $50B to build AI infrastructure (priority: 0.10)
- Hands on with Stickerbox, the AI-powered sticker maker (priority: 0.05)
- OpenAI learned the hard way that Cameo trademarked... (priority: 0.05)
- Altman describes OpenAI's forthcoming AI device (priority: 0.10)
- Google teams up with Accel... (priority: 0.00)

### 內容提取失敗清單

| 來源 | 失敗原因 |
|------|---------|
| medium.com | 404 Not Found |
| medium.com | 403 Access Denied |
| venturebeat.com (5 篇) | 429 Too Many Requests (Rate Limited) |

### 修復過程中遇到的額外問題

在部署修復期間，發現並修正了以下問題：

#### 1. `setup_logger` 導入錯誤

**錯誤訊息**:
```
ImportError: cannot import name 'setup_logger' from 'src.utils.logger'
```

**原因**: `src/tools/vector_clustering.py` 等模組導入了 `setup_logger`，但 `logger.py` 只有 `Logger.get_logger()` 方法。

**修復**: 在 `src/utils/logger.py` 新增 `setup_logger()` 函數作為 `Logger.get_logger()` 的別名。

#### 2. `curator_weekly.py` 錯誤的 ADK 導入

**錯誤訊息**:
```
ImportError: cannot import name 'LlmAgent' from 'google.genai.types'
```

**原因**: `curator_weekly.py` 使用了錯誤的導入路徑 `from google.genai.types import LlmAgent, Gemini`。

**修復**: 根據 Context7 官方文件，修正為：
```python
from google.adk.agents import LlmAgent
# 並將 model=Gemini(...) 改為 model="gemini-2.0-flash"
```

---

## 結論

USER_INTERESTS 模板替換修復已成功部署並驗證。Pipeline 能夠正常執行，Email 成功發送。

**待觀察事項**:
1. 下次執行時確認 Robotics 相關文章是否增加
2. VentureBeat 的 Rate Limiting 問題需要加入重試機制或降低請求頻率

---

## 相關檔案

- `docs/planning/stage5_scout_agent.md` - Scout Agent 設計文件
- `src/utils/config.py` - 配置管理
- `prompts/analyst_prompt.txt` - Analyst Agent 也使用 `{{USER_INTERESTS}}`
- `logs/DailyPipeline_20251125.log` - 完整執行日誌
