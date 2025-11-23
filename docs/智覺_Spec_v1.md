# 智覺個人版 1.0 完整規格書（Spec）

## 1. 核心目標
建立一個個人情報 AI Agent，每日與每週自動輸出 AI + Robotics 情報摘要。

## 2. Agents
### 2.1 Scout Agent
- RSS 來源收集
- Google Search（固定關鍵字）
- 去重

### 2.2 Analyst Agent
- 使用 LLM 進行文章解讀
- 提取 TL;DR、重點、產業影響、對 Ray 之意義
- 產生 priority score
- 儲存 embedding

### 2.3 Curator Agent
- Daily Digest（精選 5–10 條）
- Weekly Deep Report（趨勢分析）

## 3. Memory
- SQLite：articles, analysis, digests
- Embedding：向量搜尋支援週報

## 4. Tools
- Fetcher（RSS）
- Google Search Tool
- Embedding Tool
- Email Sender

## 5. Pipelines
### Daily
1. Scout 抓取來源
2. Analyst 分析
3. 更新 Memory
4. Curator Daily 產生日報
5. Email 寄出

### Weekly
1. Memory 抓週資料
2. 趨勢分析
3. Curator Weekly 產週報
4. Email 寄出

## 6. MVP 限制
- 不含 Hunter / Learner / Coordinator
- 無圖形 UI
- 不做自動來源學習
- 每日最多 30 則資訊
