# Stage 7: Analyst Agent - 規劃大綱

> **階段編號**: Stage 7
> **階段目標**: 實現分析代理，使用 LLM 深度分析文章內容
> **前置依賴**: Stage 6 完成（Content Extraction Tool）
> **預計時間**: 2 天
> **狀態**: Outline（待詳細規劃）

---

## 🎯 核心目標

實現 Analyst Agent，負責深度分析文章內容，提取技術洞察，評估文章優先度，為後續的報告生成提供高品質分析結果。

**核心功能**:
1. LLM 深度分析文章內容
2. 技術洞察提取（技術棧、趨勢、創新點）
3. 優先度評分（對 Ray 的價值評估）
4. Reflection 機制（自我反思與改進）
5. Embedding 生成（用於向量搜索）
6. 與 Memory Universe 整合（存儲分析結果）

---

## 📥 輸入輸出

### 輸入
- **來自 Scout Agent**: 文章列表（標題、URL、摘要、來源）
- **來自 Content Extractor**: 完整文章內容（正文、元數據）

### 輸出
```python
{
    "article_id": "uuid",
    "url": "https://...",
    "title": "...",
    "analysis": {
        "summary": "3-5 句話摘要",
        "key_insights": [
            "洞察 1",
            "洞察 2",
            "洞察 3"
        ],
        "tech_stack": ["Python", "LLM", "RAG"],
        "category": "AI Agent" | "Robotics" | "Tools" | "Research",
        "trends": ["Multi-Agent", "Grounding"],
        "relevance_score": 0.85,  # 0-1，對 Ray 的相關度
        "priority_score": 0.92,   # 0-1，優先度
        "reasoning": "評分理由..."
    },
    "embedding": [0.1, 0.2, ...],  # 向量表示
    "analyzed_at": datetime
}
```

---

## 🛠️ 技術選型

### ADK Agent 類型
- **LlmAgent**: 主力分析 Agent
- **可選 Reflection**: 自我反思機制（提高分析品質）

### Prompt 設計
- `prompts/analyst_prompt.txt` - 主分析指令
- `prompts/analyst_reflection_prompt.txt` - Reflection 指令（可選）

### 工具需求
- **Embedding 工具**: ADK 內建 `embedding` 工具
- **存儲工具**: 與 ArticleStore 整合

---

## 📋 待解決問題

### 1. 優先度評分邏輯
**問題**: 如何量化文章對 Ray 的價值？

**可能方案**:
- **方案 A**: LLM 直接打分（0-1）+ 說明理由
- **方案 B**: 多維度評分（相關度、創新度、實用度）後加權
- **方案 C**: 結合 LLM 評分與規則（如：來源權重、關鍵字匹配）

**傾向**: 方案 A（簡單可靠）

---

### 2. Reflection 機制
**問題**: 是否需要 Reflection？如何實現？

**方案**:
- **方案 A**: 不使用 Reflection（簡化，Stage 7 v1）
- **方案 B**: 單層 Reflection（分析後反思一次）
- **方案 C**: 多層 Reflection（迭代改進）

**傾向**: 方案 A（Phase 1 先求穩定）

---

### 3. Embedding 生成
**問題**: 對什麼內容生成 Embedding？

**方案**:
- **方案 A**: 對完整文章內容
- **方案 B**: 對摘要 + 關鍵洞察
- **方案 C**: 對標題 + 摘要

**傾向**: 方案 B（平衡資訊量與向量品質）

---

### 4. 批量分析 vs 逐篇分析
**問題**: 如何處理多篇文章？

**方案**:
- **方案 A**: 逐篇分析（簡單、可控）
- **方案 B**: 批量分析（效率高，但可能降低品質）

**傾向**: 方案 A（確保品質）

---

## 🧪 測試策略

### 單元測試
- AnalystAgent 創建
- Prompt 模板加載
- 分析結果結構驗證
- 優先度評分範圍驗證（0-1）
- Embedding 生成

### 整合測試
- 與 Content Extractor 整合
- 與 Memory Universe 整合
- 完整分析流程（Mock LLM）

### 手動測試
- 真實文章分析（需要 GOOGLE_API_KEY）
- 分析品質人工評估

---

## 📝 開發清單

### Phase 1: 規劃
- [ ] 研究 ADK LlmAgent 用法
- [ ] 研究 ADK Embedding 工具
- [ ] 設計 Analyst Prompt 模板
- [ ] 設計優先度評分邏輯
- [ ] 創建詳細規劃文檔

### Phase 2: 實作
- [ ] 創建 `prompts/analyst_prompt.txt`
- [ ] 實作 AnalystAgent 類
- [ ] 實作優先度評分邏輯
- [ ] 實作 Embedding 生成
- [ ] 實作與 Memory 整合

### Phase 3: 測試
- [ ] 編寫單元測試
- [ ] 編寫整合測試
- [ ] 手動測試與品質評估

### Phase 4: 文檔
- [ ] 實作總結文檔
- [ ] 測試驗證報告
- [ ] 更新 dev_log.md

---

## 🔗 參考資料

### ADK 文檔
- [LlmAgent](https://google.github.io/adk-docs/agents/)
- [Embedding Tool](https://google.github.io/adk-docs/tools/)
- [Reflection](https://google.github.io/adk-docs/agents/reflection/)

### 內部參考
- `docs/planning/stage5_scout_agent.md` - Agent 設計參考
- `docs/planning/stage6_content_extraction.md` - 輸入數據格式
- `CLAUDE.md` - Agent 設計規範

---

## 🎯 下一步

告訴 Claude：**"開始進行 Stage 7 - Analyst Agent"**

Claude 會：
1. 創建詳細規劃文檔 `stage7_analyst_agent.md`
2. 研究 ADK Reflection 機制
3. 設計 Analyst Prompt 模板
4. 規劃優先度評分邏輯
5. 開始實作

---

**創建日期**: 2025-11-23
**狀態**: Outline（待完善為詳細規劃）
