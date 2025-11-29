# InsightCosmos: Google ADK 核心應用範例

以下摘錄自 `InsightCosmos` 專案的程式碼片段，展示如何應用 **Google Agent Development Kit (ADK)** 與 **Gemini API** 來構建自主 AI Agent 系統。本專案符合課程要求的 **6 項關鍵概念**。

---

## 1. Multi-agent System - Sequential Agents ⭐

**課程概念**: Sequential agents (順序代理)

**架構說明**: 
本專案採用 **Sequential (順序)** 架構模式：Scout (收集) → Analyst (分析) → Curator (策展)。Orchestrator 負責協調這些 Agent 的工作流，處理數據流轉和錯誤恢復，體現了 "System 2" (慢思考/規劃) 的系統設計。每個階段的輸出是下一階段的輸入，確保數據流的完整性。

**程式碼片段** (`src/orchestrator/daily_runner.py`):
```python
def run(self):
    # Phase 1: Scout Agent (收集原始情報)
    self.logger.info("Starting Scout Agent...")
    collected, stored = self._run_phase1_scout()
    
    if stored == 0:
        self.logger.warning("No new articles stored. Aborting pipeline.")
        return self.get_summary()
    
    # Phase 2: Analyst Agent (深度推理與評分)
    # 只有當 Phase 1 有新資料時才啟動
    self.logger.info("Starting Analyst Agent...")
    analyzed_count = self._run_phase2_analyst()
    
    if analyzed_count == 0:
        self.logger.warning("No articles analyzed. Aborting pipeline.")
        return self.get_summary()
    
    # Phase 3: Curator Agent (生成最終交付物)
    # 匯總 Phase 2 的分析結果，生成 Daily Digest
    self.logger.info("Starting Curator Agent...")
    sent = self._run_phase3_curator()
    
    return {"success": True, "stats": {...}}
```

---

## 2. Tools - Built-in Tools (Google Search) ⭐

**課程概念**: Built-in tools, such as Google Search

**架構說明**: 
Agent 需要 "手" 來接觸外部世界。這裡展示了如何使用 Gemini 的 **Built-in Grounding Tool** (Google Search)。不同於傳統的 Function Calling 需要自己寫爬蟲，ADK 允許直接將 Search 作為原生工具掛載到模型上，讓模型能即時獲取最新資訊並附帶來源引用 (Citations)。

**程式碼片段** (`src/tools/google_search_grounding.py`):
```python
# 初始化帶有 Google Search 工具的模型
self.model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    tools=[{"google_search": {}}]  # 啟用內建 Grounding 工具
)

# 執行搜索 (模型會自動決定何時搜索並整合結果)
response = chat.send_message(
    f"Search for recent articles about: {query}. "
    f"Return relevant articles with URLs."
)

# 從 Grounding Metadata 中提取結構化數據
if hasattr(candidate, 'grounding_metadata'):
    for chunk in grounding_metadata.grounding_chunks:
        if hasattr(chunk, 'web'):
            # 獲取可信的來源連結
            url = chunk.web.uri
            title = chunk.web.title
```

---

## 3. Tools - Custom Tools ⭐

**課程概念**: Custom tools

**架構說明**: 
除了內建工具，ADK 也支援自定義工具。這裡展示了如何將 Python 函數包裝成 ADK 工具，讓 Agent 能夠呼叫。`fetch_rss` 工具負責從 RSS feeds 抓取文章，並返回結構化的 JSON 數據。

**程式碼片段** (`src/agents/scout_agent.py`):
```python
def fetch_rss(feed_urls: List[str], max_articles_per_feed: int = 10) -> Dict[str, Any]:
    """
    從 RSS feeds 批量抓取文章
    
    這是一個 ADK 兼容的工具函數，包裝了 RSSFetcher 類的功能。
    LLM 將根據此 docstring 理解如何使用這個工具。
    
    Args:
        feed_urls: RSS feed URL 列表
        max_articles_per_feed: 每個 feed 的最大文章數（默認 10）
    
    Returns:
        dict: {
            "status": "success" | "partial" | "error",
            "articles": List[Dict],
            "summary": {...}
        }
    """
    fetcher = RSSFetcher(timeout=30)
    result = fetcher.fetch_rss_feeds(
        feed_urls=feed_urls,
        max_articles_per_feed=max_articles_per_feed
    )
    return result

# 創建 Scout Agent 時註冊工具
agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash", api_key=api_key),
    name="ScoutAgent",
    tools=[fetch_rss, search_articles]  # 註冊自定義工具
)
```

---

## 4. Sessions & State Management ⭐

**課程概念**: Sessions & state management (e.g. InMemorySessionService)

**架構說明**: 
LLM 本身是無狀態的 (Stateless)，但 Agent 需要狀態 (Stateful)。ADK 提供了 `SessionService` 和 `Runner` 來管理對話歷史和狀態。這段代碼展示了如何為每個任務（例如分析一篇文章）創建一個獨立的、隔離的 Session，確保上下文不會互相污染，這是企業級 Agent 的重要模式。

**程式碼片段** (`src/agents/analyst_agent.py`):
```python
# 初始化 Session 服務 (可選 InMemory 或 Database)
self.session_service = InMemorySessionService()

# 為每個任務創建唯一的 Session ID
session_id = f"analysis_{article_id}_{timestamp}"
await self.session_service.create_session(
    app_name="InsightCosmos",
    user_id="system",
    session_id=session_id
)

# 使用 Runner 執行 Agent (自動處理對話歷史與上下文)
runner = Runner(
    agent=self.agent,
    app_name="InsightCosmos",
    session_service=self.session_service
)

# 執行並獲取結果
async for event in runner.run_async(
    user_id="system",
    session_id=session_id,
    new_message=Content(parts=[Part(text=user_input)], role="user")
):
    if event.is_final_response():
        response_text = event.content.parts[0].text
```

---

## 5. Long-term Memory ⭐

**課程概念**: Long term memory (e.g. Memory Bank)

**架構說明**: 
這是 Agent 的 "長期記憶" (Long-term Memory)。透過 Gemini 的 Embedding 模型 (`text-embedding-004`) 將非結構化的文本轉化為向量，並儲存在 SQLite 資料庫中。這讓 Agent 能夠進行語義搜索 (Semantic Search) 和去重 (Deduplication)，而不僅僅是關鍵字匹配。這是實現 "Personalization" (個人化) 和 "Recall" (回憶) 的關鍵技術。

**程式碼片段** (`src/memory/embedding_store.py`):
```python
# 使用 Gemini Embedding 模型生成向量
result = self.genai_client.models.embed_content(
    model="text-embedding-004",
    contents=text
)
embedding = result.embeddings[0].values

# 儲存向量到資料庫
embedding_id = self.embedding_store.store(
    article_id=article_id,
    vector=np.array(embedding),
    model="text-embedding-004"
)

# 計算餘弦相似度 (Cosine Similarity) 進行檢索
def find_similar(self, vector, top_k=10, threshold=0.7):
    embeddings = self.db.query(Embedding).all()
    similarities = []
    
    for embedding in embeddings:
        stored_vector = self.deserialize_vector(embedding.embedding)
        similarity = np.dot(vector, stored_vector) / (
            np.linalg.norm(vector) * np.linalg.norm(stored_vector)
        )
        
        if similarity >= threshold:
            similarities.append((embedding.article_id, float(similarity)))
    
    # 返回最相關的記憶片段
    return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
```

---

## 6. Observability - Logging ⭐

**課程概念**: Observability: Logging, Tracing, Metrics

**架構說明**: 
本專案實作了結構化的日誌系統，每個 Agent 和工具都有詳細的執行日誌。日誌包含時間戳、模組名稱、日誌級別和訊息內容，並儲存在 `logs/` 目錄中。這對於除錯、監控和效能分析非常重要。

**程式碼片段** (`src/utils/logger.py`):
```python
class Logger:
    """
    統一的日誌管理器
    
    提供結構化日誌記錄，支援檔案和控制台輸出。
    """
    
    @staticmethod
    def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
        """
        獲取或創建 Logger 實例
        
        Args:
            name: Logger 名稱（通常是模組名稱）
            log_level: 日誌級別（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        
        Returns:
            logging.Logger: 配置好的 Logger 實例
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # 檔案處理器
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"{name}.log",
            encoding="utf-8"
        )
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger

# 使用範例
self.logger = Logger.get_logger("ScoutAgent")
self.logger.info("Starting article collection...")
self.logger.error(f"Failed to fetch RSS: {error}")
```

---

## 課程概念對照表

| 課程概念 | 實作位置 | 說明 |
|---------|---------|------|
| **Sequential Agents** | `src/orchestrator/daily_runner.py` | Scout → Analyst → Curator 順序執行 |
| **Built-in Tools (Google Search)** | `src/tools/google_search_grounding.py` | 使用 Gemini Grounding API |
| **Custom Tools** | `src/agents/scout_agent.py` | RSS Fetcher, Content Extractor |
| **Sessions & State Management** | `src/agents/analyst_agent.py` | InMemorySessionService |
| **Long-term Memory** | `src/memory/embedding_store.py` | Vector Store + Embedding |
| **Logging** | `src/utils/logger.py` | 結構化日誌系統 |

**總計**: 符合 **6 項**課程關鍵概念（要求至少 3 項）✅
