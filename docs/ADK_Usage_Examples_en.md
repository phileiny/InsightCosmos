# InsightCosmos: Google ADK Core Application Examples

The following code snippets from the `InsightCosmos` project demonstrate how to apply **Google Agent Development Kit (ADK)** and **Gemini API** to build autonomous AI agent systems. This project implements **6 key concepts** from the course requirements.

---

## 1. Multi-agent System - Sequential Agents ⭐

**Course Concept**: Sequential agents

**Architecture Overview**: 
This project adopts a **Sequential** architecture pattern: Scout (Collection) → Analyst (Analysis) → Curator (Curation). The Orchestrator coordinates the workflow of these agents, handles data flow and error recovery, embodying "System 2" (slow thinking/planning) system design. Each phase's output becomes the input for the next phase, ensuring data flow integrity.

**Code Snippet** (`src/orchestrator/daily_runner.py`):
```python
def run(self):
    # Phase 1: Scout Agent (Collect raw intelligence)
    self.logger.info("Starting Scout Agent...")
    collected, stored = self._run_phase1_scout()
    
    if stored == 0:
        self.logger.warning("No new articles stored. Aborting pipeline.")
        return self.get_summary()
    
    # Phase 2: Analyst Agent (Deep reasoning and scoring)
    # Only starts when Phase 1 has new data
    self.logger.info("Starting Analyst Agent...")
    analyzed_count = self._run_phase2_analyst()
    
    if analyzed_count == 0:
        self.logger.warning("No articles analyzed. Aborting pipeline.")
        return self.get_summary()
    
    # Phase 3: Curator Agent (Generate final deliverable)
    # Aggregates Phase 2 analysis results to generate Daily Digest
    self.logger.info("Starting Curator Agent...")
    sent = self._run_phase3_curator()
    
    return {"success": True, "stats": {...}}
```

---

## 2. Tools - Built-in Tools (Google Search) ⭐

**Course Concept**: Built-in tools, such as Google Search

**Architecture Overview**: 
Agents need "hands" to interact with the external world. This demonstrates how to use Gemini's **Built-in Grounding Tool** (Google Search). Unlike traditional Function Calling that requires custom web scraping, ADK allows directly mounting Search as a native tool on the model, enabling real-time information retrieval with source citations.

**Code Snippet** (`src/tools/google_search_grounding.py`):
```python
# Initialize model with Google Search tool
self.model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    tools=[{"google_search": {}}]  # Enable built-in Grounding tool
)

# Execute search (model automatically decides when to search and integrates results)
response = chat.send_message(
    f"Search for recent articles about: {query}. "
    f"Return relevant articles with URLs."
)

# Extract structured data from Grounding Metadata
if hasattr(candidate, 'grounding_metadata'):
    for chunk in grounding_metadata.grounding_chunks:
        if hasattr(chunk, 'web'):
            # Get trusted source links
            url = chunk.web.uri
            title = chunk.web.title
```

---

## 3. Tools - Custom Tools ⭐

**Course Concept**: Custom tools

**Architecture Overview**: 
In addition to built-in tools, ADK supports custom tools. This shows how to wrap Python functions as ADK tools for agents to call. The `fetch_rss` tool fetches articles from RSS feeds and returns structured JSON data.

**Code Snippet** (`src/agents/scout_agent.py`):
```python
def fetch_rss(feed_urls: List[str], max_articles_per_feed: int = 10) -> Dict[str, Any]:
    """
    Batch fetch articles from RSS feeds
    
    This is an ADK-compatible tool function that wraps the RSSFetcher class.
    The LLM will understand how to use this tool based on this docstring.
    
    Args:
        feed_urls: List of RSS feed URLs
        max_articles_per_feed: Maximum articles per feed (default 10)
    
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

# Register tools when creating Scout Agent
agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash", api_key=api_key),
    name="ScoutAgent",
    tools=[fetch_rss, search_articles]  # Register custom tools
)
```

---

## 4. Sessions & State Management ⭐

**Course Concept**: Sessions & state management (e.g. InMemorySessionService)

**Architecture Overview**: 
LLMs are inherently stateless, but agents need to be stateful. ADK provides `SessionService` and `Runner` to manage conversation history and state. This code demonstrates how to create an independent, isolated Session for each task (e.g., analyzing an article), ensuring contexts don't contaminate each other—a critical pattern for enterprise-grade agents.

**Code Snippet** (`src/agents/analyst_agent.py`):
```python
# Initialize Session service (InMemory or Database options)
self.session_service = InMemorySessionService()

# Create unique Session ID for each task
session_id = f"analysis_{article_id}_{timestamp}"
await self.session_service.create_session(
    app_name="InsightCosmos",
    user_id="system",
    session_id=session_id
)

# Use Runner to execute Agent (automatically handles conversation history and context)
runner = Runner(
    agent=self.agent,
    app_name="InsightCosmos",
    session_service=self.session_service
)

# Execute and get results
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

**Course Concept**: Long term memory (e.g. Memory Bank)

**Architecture Overview**: 
This is the agent's "Long-term Memory". Using Gemini's Embedding model (`text-embedding-004`), unstructured text is transformed into vectors and stored in a SQLite database. This enables agents to perform semantic search and deduplication, not just keyword matching. This is key technology for implementing "Personalization" and "Recall".

**Code Snippet** (`src/memory/embedding_store.py`):
```python
# Generate vectors using Gemini Embedding model
result = self.genai_client.models.embed_content(
    model="text-embedding-004",
    contents=text
)
embedding = result.embeddings[0].values

# Store vectors to database
embedding_id = self.embedding_store.store(
    article_id=article_id,
    vector=np.array(embedding),
    model="text-embedding-004"
)

# Calculate Cosine Similarity for retrieval
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
    
    # Return most relevant memory fragments
    return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
```

---

## 6. Observability - Logging ⭐

**Course Concept**: Observability: Logging, Tracing, Metrics

**Architecture Overview**: 
This project implements a structured logging system where each agent and tool has detailed execution logs. Logs include timestamps, module names, log levels, and message content, stored in the `logs/` directory. This is crucial for debugging, monitoring, and performance analysis.

**Code Snippet** (`src/utils/logger.py`):
```python
class Logger:
    """
    Unified logging manager
    
    Provides structured logging with file and console output support.
    """
    
    @staticmethod
    def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
        """
        Get or create Logger instance
        
        Args:
            name: Logger name (typically module name)
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            logging.Logger: Configured Logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"{name}.log",
            encoding="utf-8"
        )
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger

# Usage example
self.logger = Logger.get_logger("ScoutAgent")
self.logger.info("Starting article collection...")
self.logger.error(f"Failed to fetch RSS: {error}")
```

---

## Course Concept Mapping Table

| Course Concept | Implementation Location | Description |
|---------------|------------------------|-------------|
| **Sequential Agents** | `src/orchestrator/daily_runner.py` | Scout → Analyst → Curator sequential execution |
| **Built-in Tools (Google Search)** | `src/tools/google_search_grounding.py` | Using Gemini Grounding API |
| **Custom Tools** | `src/agents/scout_agent.py` | RSS Fetcher, Content Extractor |
| **Sessions & State Management** | `src/agents/analyst_agent.py` | InMemorySessionService |
| **Long-term Memory** | `src/memory/embedding_store.py` | Vector Store + Embedding |
| **Logging** | `src/utils/logger.py` | Structured logging system |

**Total**: Implements **6** course key concepts (minimum requirement: 3) ✅
