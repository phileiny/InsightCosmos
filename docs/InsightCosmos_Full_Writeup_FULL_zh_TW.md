# 🚀 InsightCosmos -- Capstone Full Writeup（繁體中文版）

## 1. 引言與靈感來源（Introduction & Inspiration）

AI 與機器人領域的進展速度，已經快到任何人都無法靠手動方式完全追蹤。
每天都有來自數十個來源的新論文、新模型、新框架、新突破與新產業動態湧現。

對一位全職工程師或研究員來說，保持資訊更新已不再是「閱讀能力」的問題------\
而是**資訊超載**的問題。

我打造 InsightCosmos，是為了回答一個簡單的問題：

**如果有一個自主 AI agent 能每天持續掃描整個 AI
宇宙，並只把我真正需要知道的那些資訊整理給我------會是什麼樣子？**

InsightCosmos 是一套個人智慧系統，充當多代理人的觀測站，\
替我處理資訊，並產出具結構化且可行動的洞察。

------------------------------------------------------------------------

## 2. 專案概述 --- InsightCosmos 能做什麼（Project Overview）

InsightCosmos 是一套 **全自動（fully autonomous）** 的 AI 情報處理管線。

### Daily（每日）

-   從 RSS 與搜尋結果抓取新資訊\
-   使用 LLM 推理分析內容\
-   評分與抽取洞察\
-   儲存至向量記憶（Vector Memory）\
-   產生《每日情報摘要》\
-   透過 Email 寄送

### Weekly（每週）

-   取回過去 7 天的完整資料\
-   執行嵌入聚類（clustering）\
-   分析趨勢（trend analysis）\
-   產生《每週深度報告》\
-   以 Email 寄送

**部署之後無需手動操作。**\
InsightCosmos 是一個永遠運轉的「個人智慧宇宙」。

------------------------------------------------------------------------

## 3. 系統架構（Google AI Agent 風格）

InsightCosmos 採用 Google 的 Agentic System 原則：

-   **Autonomous behavior（自主行為）**
-   **Tool use（工具調用）**
-   **Reasoning & reflection（推理與反思）**
-   **Memory-based decisions（基於記憶決策）**
-   **Goal-oriented execution（目標導向執行）**

### 系統概念流程（Pipeline）

    ┌───────────────────────────────┐
    │       Daily / Weekly Runner    │
    └───────────────┬───────────────┘
                    ↓
    ┌───────────────────────────────┐
    │          Scout Agent           │
    │   - RSS & Search collection    │
    │   - Deduplication via vectors  │
    └───────────────┬───────────────┘
                    ↓
    ┌───────────────────────────────┐
    │          Analyst Agent         │
    │   - LLM reasoning              │
    │   - TL;DR + insights           │
    │   - Relevance scoring          │
    │   - Reflection for quality     │
    │   - Embedding creation         │
    └───────────────┬───────────────┘
                    ↓
    ┌───────────────────────────────┐
    │        Memory Universe         │
    │   - SQLite structured storage  │
    │   - Embedding vector memory    │
    └───────────────┬───────────────┘
                    ↓
    ┌───────────────────────────────┐
    │          Curator Agent         │
    │   - Daily Digest               │
    │   - Weekly Deep Report         │
    └───────────────┬───────────────┘
                    ↓
    ┌───────────────────────────────┐
    │         Email Delivery         │
    └───────────────────────────────┘

------------------------------------------------------------------------

## 4. 代理人分工（Agents Breakdown）

------------------------------------------------------------------------

### 4.1 **Scout Agent --- 探索（Discovery）**

Scout Agent 的任務是：

-   蒐集 RSS 來源\
-   Google Search 搜尋新主題\
-   抽取 metadata\
-   使用向量相似度做重複內容過濾（deduplication）

確保只有高價值、不重複的記事進入系統。

------------------------------------------------------------------------

### 4.2 **Analyst Agent --- 理解與推理（Understanding & Reasoning）**

對每個蒐集到的項目，Analyst Agent 會：

-   閱讀內容\
-   解構：
    -   關鍵技術概念\
    -   為何重要\
    -   與我的興趣或研究方向的相關性\
-   進行 CoT 推理\
-   執行反思（reflection）強化品質\
-   產生 Insight Score（0--10 分）\
-   建立向量嵌入

------------------------------------------------------------------------

### 4.3 **Curator Agent --- 綜整（Synthesis）**

Curator Agent 負責輸出最終的資訊：

#### Daily Digest（每日摘要）

-   挑選前 5--10 筆最重要資訊\
-   生成具洞察、可行動的敘述\
-   以 Email 格式化成 Markdown

#### Weekly Deep Report（每週深度報告）

-   回溯過去 7 天的記憶\
-   嵌入聚類找出趨勢\
-   分析 2--3 個主要的每週主題\
-   提供個人化建議

Curator Agent 的存在，讓系統從單純自動化變成**真正有智慧的編輯器**。

------------------------------------------------------------------------

## 5. 工具使用（Tool Use）

InsightCosmos 展示多種工具的協作：

  工具                 用途
  -------------------- ------------------
  HTTP / RSS Fetcher   抓取內容
  Search Tool          尋找新興 AI 趨勢
  Embedding Tool       相似搜尋與聚類
  Email Tool           寄送報告
  SQLite               輕量結構化記憶庫

符合 Capstone 必要條件：\
**LLM + Tools + Memory = 自主智慧循環**

------------------------------------------------------------------------

## 6. 記憶宇宙（Memory Universe）

InsightCosmos 的記憶由兩部分組成：

### 1. SQLite 結構化資料庫

儲存：

-   文章資料\
-   分析結果\
-   每日/每週輸出\
-   中繼資訊

### 2. 向量記憶（Embedding Vector Store）

用於：

-   文件去重\
-   主題聚類\
-   趨勢辨識\
-   每週報告分析

記憶不只是存資料，而是讓系統能**基於過去做推理**。

------------------------------------------------------------------------

## 7. 範例輸出（Sample Outputs）

------------------------------------------------------------------------

### Daily Digest 範例

**Top AI & Robotics Intelligence --- Feb 2025**

1.  **OpenAI 發表新一代多模態機器人模型**
    -   核心概念：操作 + 視覺 + 規劃的統一架構\
    -   為何重要：朝汎用機器人前進的大步\
    -   與我研究的相關性：高度一致
2.  **Google 推出 agentic workflow APIs**
    -   越來越接近多代理系統的標準化\
        ...

------------------------------------------------------------------------

### Weekly Deep Report 範例

**本週 AI 情報趨勢**

#### 趨勢 1 --- Agentic Robotics Integration

-   LLM 推理與 embodied control 加速融合\
-   顯著影響新論文的方向集中於自主規劃

#### 趨勢 2 --- 模型統一化

-   各大科技公司在押注 multi-task / multi-modal 統一架構

**下週建議行動**\
- 研究 Embodied Agents benchmark\
- 在 InsightCosmos 內嘗試建 prototype evaluator

------------------------------------------------------------------------

## 8. 成果與影響（Results & Impact）

InsightCosmos 成功解決了真實的資訊痛點：

✔ 免去每天掃描大量來源\
✔ 收到的都是洞察，而不是雜訊\
✔ 每週研究時間從數小時 → 幾分鐘\
✔ 系統完全自動化、零維護\
✔ agent 逐漸成為我的「外掛大腦」

InsightCosmos 將資訊超載轉換為**策略優勢**。

------------------------------------------------------------------------

## 9. 未來發展（Future Work）

### v2 --- Intelligent Universe（智慧宇宙）

-   自動計算來源品質評分\
-   個人化主題偏好學習\
-   透過向量演化的興趣模型\
-   視覺化知識圖 Nebula Map

### v3 --- Enterprise Universe（企業宇宙）

-   多使用者版本\
-   Hunter / Learner / Coordinator Agents\
-   組織級情報管線\
-   Intelligence-as-a-Service 平台

InsightCosmos 將逐步成為一個完整的 AI Intelligence 生態系統。

------------------------------------------------------------------------

## 10. 結論（Conclusion）

InsightCosmos 並不是一支自動化腳本------\
它是一個具記憶、能推理、可使用工具、可自主運作的 AI Agent 系統。

它展現出：

-   多代理架構\
-   推理與反思能力\
-   工具協作能力\
-   基於記憶的智慧行為\
-   完整自主的端到端管線

InsightCosmos 展示了 AI agent 的未來：

**不再是被動助手，而是主動的智慧夥伴。**
