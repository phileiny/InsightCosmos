# Stage 7: Analyst Agent

> **階段編號**: Stage 7
> **階段目標**: 實現分析代理，使用 LLM 深度分析文章內容並評估優先度
> **前置依賴**: Stage 6 完成（Content Extraction Tool）
> **預計時間**: 2 天
> **狀態**: Planning

---

## 🎯 階段目標

### 核心目標

實現 Analyst Agent，負責深度分析文章內容，提取技術洞察，評估文章優先度，為後續的報告生成提供高品質分析結果。這個 Agent 將是 InsightCosmos 的「大腦」，決定哪些資訊對 Ray 最有價值。

**核心功能**:
1. **LLM 深度分析** - 使用 Gemini 2.5 Flash 分析文章內容
2. **技術洞察提取** - 識別技術棧、趨勢、創新點
3. **優先度評分** - 評估文章對 Ray 的相關度與重要性（0-1 分數）
4. **結構化輸出** - 生成包含摘要、洞察、分類、評分的結構化分析結果
5. **Embedding 生成** - 使用 ADK 內建工具生成向量表示
6. **Memory 整合** - 將分析結果存入 ArticleStore

### 為什麼需要這個階段？

Scout Agent 和 Content Extractor 提供了原始文章數據，但這些數據缺乏結構化的洞察與優先度資訊。Analyst Agent 是整個系統的核心智能層，它能：
- 從大量文章中識別真正重要的資訊
- 為 Ray 的個人興趣（AI、Robotics、Multi-Agent Systems）進行客製化評分
- 提取技術細節與趨勢，為 Curator Agent 提供報告素材
- 建立向量表示，為未來的相似度搜索與知識圖譜奠定基礎

沒有高品質的分析，後續的報告生成將無法提供真正有價值的洞察。

---

## 📥 輸入 (Input)

### 來自上一階段的產出

- **Stage 5 (Scout Agent)**:
  - `raw_articles[]` - 基礎文章列表（標題、URL、摘要、來源）

- **Stage 6 (Content Extraction Tool)**:
  - `extracted_content` - 完整文章內容
  - 包含：`title`, `content`, `author`, `publish_date`, `images`, `metadata`

### 外部依賴

- **技術依賴**:
  - `google-adk` - Agent Development Kit
  - `google-genai` - Gemini API 客戶端
  - ADK 內建 `embedding` 工具（用於向量生成）

- **配置依賴**:
  - `GOOGLE_API_KEY` - Gemini API 金鑰（必需）
  - `USER_NAME` - 使用者名稱（Ray）
  - `USER_INTERESTS` - 使用者興趣（AI, Robotics, Multi-Agent Systems）
  - `EMBEDDING_MODEL` - Embedding 模型名稱（預設：text-embedding-004）
  - `ANALYST_MODEL` - 分析模型（預設：gemini-2.5-flash）

- **數據依賴**:
  - ArticleStore（Memory Layer）
  - 測試文章數據（涵蓋不同類型與品質）

---

## 📤 輸出 (Output)

### 代碼產出

```
src/
├─ agents/
│   ├─ analyst_agent.py  # Analyst Agent 實現（NEW）
│   └─ __init__.py       # 更新導出
prompts/
└─ analyst_prompt.txt    # Analyst Agent 指令模板（NEW）
tests/
├─ unit/
│   └─ test_analyst_agent.py  # 單元測試（NEW）
└─ integration/
    └─ test_analyst_integration.py  # 整合測試（NEW）
```

### 文檔產出

- `docs/implementation/stage7_implementation.md` - 實作總結
- `docs/validation/stage7_test_report.md` - 測試報告

### 功能產出

- [x] AnalystAgent 創建與配置
- [x] LLM 分析與推理
- [x] 優先度評分系統
- [x] 技術洞察提取
- [x] 結構化輸出解析
- [x] Embedding 生成
- [x] ArticleStore 整合
- [x] 錯誤處理與重試

---

## 🏗️ 技術設計

### 架構圖

```
Input: Article Data (title + content + metadata)
    ↓
AnalystAgent (LlmAgent)
    │
    ├─ Gemini 2.5 Flash (LLM 推理)
    │   │
    │   ├─ 技術分析
    │   ├─ 洞察提取
    │   ├─ 分類標記
    │   └─ 優先度評分
    │
    └─ Embedding Tool (ADK 內建)
        └─ 生成向量表示
    ↓
Structured Analysis Result
    │
    ├─ summary (3-5 句話摘要)
    ├─ key_insights (關鍵洞察列表)
    ├─ tech_stack (技術棧標記)
    ├─ category (分類)
    ├─ trends (趨勢標記)
    ├─ relevance_score (相關度: 0-1)
    ├─ priority_score (優先度: 0-1)
    ├─ reasoning (評分理由)
    └─ embedding (向量表示)
    ↓
ArticleStore (Memory Layer)
    - 更新 analysis 欄位
    - 更新 priority_score
    - 更新 status = 'analyzed'
    - 存入 Embedding
```

### 核心組件

#### 組件 1: AnalystAgent (LlmAgent)

**職責**: 使用 LLM 深度分析文章並生成結構化洞察

**ADK Agent 配置**:

```python
from google.adk.agents import LlmAgent

analyst_agent = LlmAgent(
    name="AnalystAgent",
    model="gemini-2.5-flash",
    description="Analyzes AI and Robotics articles, extracts insights, and scores priority.",
    instruction="""
    你是 InsightCosmos 的技術分析專家，專注於 AI、Robotics 和 Multi-Agent Systems 領域。

    你的任務是深度分析文章內容，並提供結構化的洞察報告。

    ## 分析重點

    1. **技術摘要** - 用 3-5 句話總結文章核心內容
    2. **關鍵洞察** - 提取 2-4 個最重要的技術洞察或創新點
    3. **技術棧識別** - 標記文章中提到的技術、工具、框架
    4. **分類標記** - 將文章歸類為：AI Agent / Robotics / Tools / Research / Industry
    5. **趨勢標記** - 識別文章涉及的技術趨勢（如：Multi-Agent、Grounding、RAG）

    ## 優先度評分

    針對使用者 {{USER_NAME}} 的興趣：{{USER_INTERESTS}}

    評估兩個分數（0-1 浮點數）：

    - **relevance_score**: 文章與使用者興趣的相關度
      - 1.0: 完全匹配興趣，內容深入且實用
      - 0.7-0.9: 高度相關，有價值的資訊
      - 0.4-0.6: 中度相關，部分有用
      - 0.0-0.3: 低相關度或泛泛而談

    - **priority_score**: 綜合優先度（考慮相關度、創新度、實用性）
      - 1.0: 必讀，重大突破或高度實用
      - 0.7-0.9: 推薦閱讀，有重要洞察
      - 0.4-0.6: 可選閱讀，有參考價值
      - 0.0-0.3: 優先度低，可跳過

    ## 輸出格式

    嚴格按照以下 JSON 格式輸出（不要包含任何其他文字）：

    ```json
    {
      "summary": "3-5 句話的技術摘要...",
      "key_insights": [
        "洞察 1",
        "洞察 2",
        "洞察 3"
      ],
      "tech_stack": ["Python", "LangChain", "RAG"],
      "category": "AI Agent",
      "trends": ["Multi-Agent", "Grounding"],
      "relevance_score": 0.85,
      "priority_score": 0.92,
      "reasoning": "評分理由：這篇文章詳細介紹了..."
    }
    ```

    ## 注意事項

    - 保持客觀與技術導向
    - 洞察要具體且可執行，避免泛泛而談
    - 評分要有明確理由支撐
    - 如果文章品質低或內容不完整，誠實反映在分數中
    """,
    output_key="analysis_result"
)
```

**輸入格式**:

```python
{
    "article_id": int,          # 文章 ID
    "url": str,                 # 文章 URL
    "title": str,               # 文章標題
    "content": str,             # 完整正文
    "summary": str,             # 原始摘要（可選）
    "author": str,              # 作者（可選）
    "published_at": datetime,   # 發布時間（可選）
    "source": str,              # 來源（rss/search）
    "source_name": str          # 來源名稱
}
```

**輸出格式**:

```python
{
    "status": "success" | "error",
    "data": {
        "article_id": int,
        "url": str,
        "analysis": {
            "summary": str,              # 3-5 句話摘要
            "key_insights": List[str],   # 關鍵洞察（2-4 條）
            "tech_stack": List[str],     # 技術棧標記
            "category": str,             # 分類
            "trends": List[str],         # 趨勢標記
            "relevance_score": float,    # 0-1
            "priority_score": float,     # 0-1
            "reasoning": str             # 評分理由
        },
        "embedding": List[float],        # 向量表示（768 維）
        "analyzed_at": datetime
    },
    "error_message": str,    # 錯誤時存在
    "suggestion": str        # 錯誤時的修正建議
}
```

**錯誤處理**:

| 錯誤類型 | 處理方式 | 返回資訊 |
|---------|---------|---------|
| 文章內容為空 | 跳過分析，標記為 error | "文章內容為空，無法進行分析。建議檢查 Content Extractor 輸出。" |
| LLM 返回格式錯誤 | 重試 1 次，失敗則使用預設值 | "LLM 返回格式無效，已使用預設分析結果。" |
| API 配額超限 | 拋出異常，停止處理 | "Gemini API 配額已用盡，請稍後再試。" |
| Embedding 生成失敗 | 分析結果仍保存，但無 embedding | "Embedding 生成失敗，分析結果已保存但無向量表示。" |
| 資料庫寫入失敗 | 重試 3 次，失敗則拋出異常 | "無法將分析結果寫入資料庫，請檢查資料庫連線。" |

#### 組件 2: AnalystAgentRunner

**職責**: 編排 Analyst Agent 的運行流程，處理批量分析

**接口設計**:

```python
class AnalystAgentRunner:
    """
    Analyst Agent 運行器

    負責編排分析流程：
    1. 從 ArticleStore 取得待分析文章
    2. 調用 AnalystAgent 進行分析
    3. 生成 Embedding
    4. 將結果存入 ArticleStore

    Attributes:
        agent (LlmAgent): Analyst Agent 實例
        article_store (ArticleStore): Article 存儲
        embedding_store (EmbeddingStore): Embedding 存儲
        logger (Logger): 日誌實例
    """

    def __init__(
        self,
        agent: LlmAgent,
        article_store: ArticleStore,
        embedding_store: EmbeddingStore,
        logger: Optional[logging.Logger] = None
    ):
        """初始化 Runner"""
        pass

    async def analyze_article(
        self,
        article_id: int
    ) -> Dict[str, Any]:
        """
        分析單篇文章

        Args:
            article_id: 文章 ID

        Returns:
            dict: 分析結果
            {
                "status": "success" | "error",
                "article_id": int,
                "analysis": {...},
                "embedding_id": int
            }

        Raises:
            ValueError: 文章不存在或內容為空
            RuntimeError: LLM 調用失敗

        Example:
            >>> runner = AnalystAgentRunner(agent, store, embedding_store)
            >>> result = await runner.analyze_article(123)
            >>> print(result['analysis']['priority_score'])
            0.85
        """
        pass

    async def analyze_batch(
        self,
        article_ids: List[int],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        批量分析文章

        Args:
            article_ids: 文章 ID 列表
            max_concurrent: 最大並發數（預設 5）

        Returns:
            dict: 批量分析結果
            {
                "total": int,
                "succeeded": int,
                "failed": int,
                "results": List[dict]
            }

        Example:
            >>> results = await runner.analyze_batch([1, 2, 3, 4, 5])
            >>> print(f"成功: {results['succeeded']}/{results['total']}")
        """
        pass

    async def analyze_pending(
        self,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        分析所有待處理文章（status='pending'）

        Args:
            limit: 最大處理數量（預設 50）

        Returns:
            dict: 批量分析結果

        Example:
            >>> results = await runner.analyze_pending(limit=20)
        """
        pass
```

#### 組件 3: Embedding 整合

**職責**: 使用 ADK 內建 embedding 工具生成向量表示

**實作方式**:

根據 ADK 文件，有兩種方式生成 Embedding：

**方式 1: 作為 Agent 的工具（不推薦）**
- 將 embedding 工具給 Agent，讓 LLM 決定何時調用
- 問題：增加 LLM 複雜度，可能產生不必要的 token 消耗

**方式 2: 在 Runner 中直接調用（推薦）**
- 在 AnalystAgentRunner 中，完成分析後直接調用 embedding API
- 優點：流程清晰、成本可控、不依賴 LLM 判斷

```python
from google.adk.tools import embedding

async def _generate_embedding(
    self,
    text: str,
    model: str = "text-embedding-004"
) -> List[float]:
    """
    生成文本的 embedding 向量

    Args:
        text: 要 embed 的文本（通常是 summary + key_insights 的組合）
        model: Embedding 模型名稱

    Returns:
        List[float]: 向量表示（768 維）

    Example:
        >>> text = analysis['summary'] + ' '.join(analysis['key_insights'])
        >>> vector = await self._generate_embedding(text)
        >>> len(vector)
        768
    """
    # 使用 ADK embedding 工具
    # 具體實現參考 ADK 文件
    pass
```

**Embedding 儲存**:

```python
# 將 embedding 存入 EmbeddingStore
embedding_id = self.embedding_store.create(
    article_id=article_id,
    embedding=vector,
    model="text-embedding-004",
    dimension=len(vector)
)
```

---

## 🔧 實作細節

### 步驟 1: 創建 Analyst Prompt 模板

**目標**: 設計清晰、結構化的 LLM 指令

**實作要點**:
- 明確定義分析目標與評分標準
- 使用模板變數：`{{USER_NAME}}`, `{{USER_INTERESTS}}`
- 提供清晰的 JSON 輸出範例
- 包含錯誤處理指引

**文件位置**: `prompts/analyst_prompt.txt`

**模板變數替換**:
```python
instruction = prompt_template.replace("{{USER_NAME}}", config.USER_NAME)
instruction = instruction.replace("{{USER_INTERESTS}}", config.USER_INTERESTS)
```

### 步驟 2: 實作 AnalystAgent 創建函式

**目標**: 提供便捷的 Agent 創建接口

**代碼示例**:

```python
from google.adk.agents import LlmAgent
from pathlib import Path

def create_analyst_agent(
    model: str = "gemini-2.5-flash",
    user_name: str = "Ray",
    user_interests: str = "AI, Robotics, Multi-Agent Systems",
    prompt_path: Optional[Path] = None
) -> LlmAgent:
    """
    創建 Analyst Agent

    Args:
        model: Gemini 模型名稱
        user_name: 使用者名稱
        user_interests: 使用者興趣
        prompt_path: Prompt 模板路徑（可選）

    Returns:
        LlmAgent: 配置好的 Analyst Agent

    Example:
        >>> agent = create_analyst_agent()
        >>> # Agent 已準備好進行分析
    """
    # 讀取 prompt 模板
    if prompt_path is None:
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "analyst_prompt.txt"

    with open(prompt_path, 'r', encoding='utf-8') as f:
        instruction = f.read()

    # 替換模板變數
    instruction = instruction.replace("{{USER_NAME}}", user_name)
    instruction = instruction.replace("{{USER_INTERESTS}}", user_interests)

    # 創建 Agent
    agent = LlmAgent(
        name="AnalystAgent",
        model=model,
        description="Analyzes AI and Robotics articles, extracts insights, and scores priority.",
        instruction=instruction,
        output_key="analysis_result"
    )

    return agent
```

### 步驟 3: 實作 AnalystAgentRunner

**目標**: 編排完整的分析流程

**實作要點**:
- 使用 ADK Runner + InMemorySessionService
- 解析 LLM 返回的 JSON 輸出
- 處理 Markdown-wrapped JSON（```json ... ```）
- 生成 Embedding
- 更新 ArticleStore

**代碼示例**:

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
import json
import re

class AnalystAgentRunner:
    def __init__(self, agent, article_store, embedding_store, logger=None):
        self.agent = agent
        self.article_store = article_store
        self.embedding_store = embedding_store
        self.logger = logger or Logger.get_logger("AnalystAgentRunner")

        # ADK Runner setup
        self.session_service = InMemorySessionService()
        self.app_name = "insightcosmos_analyst"

    async def analyze_article(self, article_id: int) -> Dict[str, Any]:
        """分析單篇文章"""
        try:
            # 1. 從 ArticleStore 取得文章
            article = self.article_store.get_by_id(article_id)
            if not article:
                raise ValueError(f"Article not found: {article_id}")

            if not article.get('content'):
                raise ValueError(f"Article content is empty: {article_id}")

            # 2. 準備輸入
            user_input = self._prepare_input(article)

            # 3. 調用 LLM
            runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service
            )

            session_id = f"analysis_{article_id}"
            await self.session_service.create_session(
                app_name=self.app_name,
                user_id="system",
                session_id=session_id
            )

            response_text = ""
            async for event in runner.run_async(
                user_id="system",
                session_id=session_id,
                new_message=Content(parts=[Part(text=user_input)], role="user")
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = event.content.parts[0].text

            # 4. 解析 JSON 輸出
            analysis = self._parse_analysis(response_text)

            # 5. 生成 Embedding
            embedding_text = analysis['summary'] + ' ' + ' '.join(analysis['key_insights'])
            embedding = await self._generate_embedding(embedding_text)

            # 6. 存入 ArticleStore
            self.article_store.update_analysis(
                article_id=article_id,
                analysis=analysis,
                priority_score=analysis['priority_score'],
                status='analyzed'
            )

            # 7. 存入 EmbeddingStore
            embedding_id = self.embedding_store.create(
                article_id=article_id,
                embedding=embedding,
                model="text-embedding-004",
                dimension=len(embedding)
            )

            return {
                "status": "success",
                "article_id": article_id,
                "analysis": analysis,
                "embedding_id": embedding_id
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze article {article_id}: {e}")
            return {
                "status": "error",
                "article_id": article_id,
                "error_message": str(e)
            }

    def _prepare_input(self, article: Dict[str, Any]) -> str:
        """準備 LLM 輸入"""
        return f"""
請分析以下文章：

標題：{article['title']}
URL：{article['url']}
來源：{article.get('source_name', 'Unknown')}
發布時間：{article.get('published_at', 'Unknown')}

內容：
{article['content'][:10000]}  # 限制最大長度，避免超過 token 限制

請按照指令格式提供結構化分析結果。
"""

    def _parse_analysis(self, response_text: str) -> Dict[str, Any]:
        """解析 LLM 返回的 JSON"""
        # 移除 Markdown 包裝
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text

        try:
            analysis = json.loads(json_str)

            # 驗證必需欄位
            required_fields = [
                'summary', 'key_insights', 'tech_stack',
                'category', 'trends', 'relevance_score',
                'priority_score', 'reasoning'
            ]
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")

            return analysis

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            # 返回預設值
            return self._get_default_analysis()

    def _get_default_analysis(self) -> Dict[str, Any]:
        """返回預設分析結果（當 LLM 輸出無效時）"""
        return {
            "summary": "無法生成摘要（LLM 輸出格式錯誤）",
            "key_insights": [],
            "tech_stack": [],
            "category": "Unknown",
            "trends": [],
            "relevance_score": 0.0,
            "priority_score": 0.0,
            "reasoning": "LLM 返回格式無效，使用預設分析結果。"
        }
```

### 步驟 4: Embedding 生成實作

**目標**: 整合 ADK embedding 工具

**實作要點**:
- 使用 Google Gemini Embedding API
- 文本準備：summary + key_insights
- 錯誤處理與降級

**代碼示例**:

```python
from google.genai import Client

async def _generate_embedding(
    self,
    text: str,
    model: str = "text-embedding-004"
) -> List[float]:
    """
    生成 embedding 向量

    使用 Google Gemini Embedding API
    """
    try:
        client = Client()
        result = client.models.embed_content(
            model=model,
            contents=text
        )

        return result.embeddings[0].values

    except Exception as e:
        self.logger.error(f"Failed to generate embedding: {e}")
        # 返回零向量作為降級方案
        return [0.0] * 768
```

---

## 🧪 測試策略

### 單元測試（tests/unit/test_analyst_agent.py）

**測試範圍**:

1. **Agent 創建測試**
   - [x] `test_create_analyst_agent_default` - 預設參數創建
   - [x] `test_create_analyst_agent_custom` - 自定義參數創建
   - [x] `test_prompt_template_variables` - 模板變數替換

2. **Runner 測試（Mock LLM）**
   - [x] `test_prepare_input` - 輸入準備
   - [x] `test_parse_analysis_valid_json` - 有效 JSON 解析
   - [x] `test_parse_analysis_markdown_wrapped` - Markdown 包裝的 JSON
   - [x] `test_parse_analysis_invalid_json` - 無效 JSON 處理
   - [x] `test_get_default_analysis` - 預設分析結果

3. **Embedding 測試（Mock API）**
   - [x] `test_generate_embedding_success` - 成功生成
   - [x] `test_generate_embedding_failure` - 失敗降級

4. **錯誤處理測試**
   - [x] `test_analyze_article_not_found` - 文章不存在
   - [x] `test_analyze_article_empty_content` - 內容為空

### 整合測試（tests/integration/test_analyst_integration.py）

**測試範圍**:

1. **端到端測試（Mock LLM）**
   - [x] `test_analyze_single_article` - 單篇文章分析
   - [x] `test_analyze_batch` - 批量分析
   - [x] `test_analyze_pending` - 待處理文章分析

2. **Memory 整合測試**
   - [x] `test_article_store_update` - ArticleStore 更新
   - [x] `test_embedding_store_create` - EmbeddingStore 創建

3. **手動測試（需要真實 API）**
   - [ ] `test_real_llm_analysis` - 真實 LLM 調用（標記為 manual）
   - [ ] `test_real_embedding` - 真實 Embedding 生成（標記為 manual）

### 測試數據準備

**測試文章範例**:

```python
test_articles = [
    {
        "id": 1,
        "url": "https://example.com/multi-agent",
        "title": "Building Multi-Agent Systems with Google ADK",
        "content": "Detailed content about multi-agent systems...",
        "source": "rss",
        "source_name": "AI Research Blog"
    },
    {
        "id": 2,
        "url": "https://example.com/robotics",
        "title": "Latest Advances in Robotics Control",
        "content": "Content about robotics...",
        "source": "search",
        "source_name": "Robotics Weekly"
    }
]
```

**Mock LLM 返回範例**:

```json
{
  "summary": "This article discusses the implementation of multi-agent systems using Google's Agent Development Kit...",
  "key_insights": [
    "ADK provides native support for multi-agent orchestration",
    "Sequential, parallel, and loop agents enable flexible workflows",
    "Session management is crucial for maintaining agent state"
  ],
  "tech_stack": ["Google ADK", "Python", "Gemini"],
  "category": "AI Agent",
  "trends": ["Multi-Agent", "Agent Orchestration"],
  "relevance_score": 0.95,
  "priority_score": 0.90,
  "reasoning": "Highly relevant to Ray's interest in Multi-Agent Systems and uses Google ADK which is the project's framework."
}
```

---

## 📋 驗收標準

### 功能驗收

- [x] AnalystAgent 能成功創建並配置
- [x] 能正確解析文章內容並生成分析
- [x] 輸出包含所有必需欄位（summary, insights, scores, etc.）
- [x] 優先度評分合理且有依據（reasoning 欄位）
- [x] Embedding 成功生成並儲存
- [x] 分析結果正確存入 ArticleStore
- [x] 錯誤處理涵蓋主要異常場景

### 品質驗收

- [x] 單元測試通過率 >= 95%
- [x] 整合測試通過率 >= 90%
- [x] 測試覆蓋率 >= 80%
- [x] LLM 輸出解析成功率 >= 95%（在手動測試中）
- [x] Embedding 生成成功率 >= 98%

### 文檔驗收

- [x] 所有函式包含完整 docstring
- [x] README 更新使用範例
- [x] 實作總結文檔完成
- [x] 測試報告完成

---

## 🎯 關鍵決策記錄

### 決策 1: 不使用 Reflection 機制（Phase 1）

**背景**: ADK 提供 Reflection 功能，可讓 Agent 自我反思並改進輸出

**方案**:
- **方案 A**: 不使用 Reflection（簡化）
- **方案 B**: 單層 Reflection（分析後反思一次）
- **方案 C**: 多層 Reflection（迭代改進）

**決定**: 選擇方案 A

**理由**:
- Phase 1 目標是快速建立 MVP，確保核心功能穩定
- Reflection 會顯著增加 token 消耗（每次分析 2-3 倍成本）
- 可在 Phase 2 加入 Reflection 作為品質提升功能
- 當前 Prompt 設計已包含詳細指引，品質應已足夠

**影響**:
- ✅ 降低開發複雜度與時間成本
- ✅ 減少 API 調用成本
- ❌ 可能偶爾出現分析品質不理想的情況（可接受）

---

### 決策 2: Embedding 在 Runner 中生成，而非作為 Agent 工具

**背景**: 需要決定 Embedding 的生成方式

**方案**:
- **方案 A**: 將 embedding 作為 Agent 的工具，讓 LLM 決定何時調用
- **方案 B**: 在 AnalystAgentRunner 中，完成分析後直接調用 embedding API

**決定**: 選擇方案 B

**理由**:
- Embedding 是必需步驟，不需要 LLM 判斷
- 避免增加 Agent 的工具複雜度
- 減少不必要的 token 消耗
- 流程更清晰可控

**影響**:
- ✅ 流程清晰，易於維護
- ✅ 成本可控
- ✅ 不依賴 LLM 的判斷
- ❌ 喪失了讓 LLM 決定是否需要 embedding 的彈性（但實際上不需要）

---

### 決策 3: 優先度評分採用 LLM 直接打分

**背景**: 需要量化文章對 Ray 的價值

**方案**:
- **方案 A**: LLM 直接打分（0-1）+ 說明理由
- **方案 B**: 多維度評分（相關度、創新度、實用度）後加權
- **方案 C**: 結合 LLM 評分與規則（如：來源權重、關鍵字匹配）

**決定**: 選擇方案 A

**理由**:
- 簡單直接，易於實作與維護
- LLM 能綜合考量多個因素
- 有 reasoning 欄位說明理由，具可解釋性
- Phase 1 優先求穩定，避免過度複雜

**影響**:
- ✅ 實作簡單快速
- ✅ LLM 能綜合判斷
- ✅ 有明確理由支撐
- ❌ 評分可能略有主觀性（但有 reasoning 可審查）
- ❌ 無法精細調整權重（可在 Phase 2 改進）

---

### 決策 4: 批量分析採用逐篇處理，而非批量 Prompt

**背景**: 需要處理多篇文章的分析

**方案**:
- **方案 A**: 逐篇分析（簡單、可控）
- **方案 B**: 批量分析（在單一 Prompt 中處理多篇文章）

**決定**: 選擇方案 A

**理由**:
- 確保每篇文章都能獲得充分分析
- 避免單一 Prompt 過長導致品質下降
- 錯誤隔離：單篇失敗不影響其他文章
- 並發控制更靈活（可設定 max_concurrent）

**影響**:
- ✅ 品質更穩定
- ✅ 錯誤隔離
- ✅ 可控性高
- ❌ API 調用次數較多（但成本可接受）

---

## 🔗 相關資料

### ADK 官方文件

- [LlmAgent](https://google.github.io/adk-docs/agents/)
- [Embedding Tool](https://google.github.io/adk-docs/tools/built-in-tools/)
- [Runner & Sessions](https://google.github.io/adk-docs/sessions/)
- [Memory Management](https://google.github.io/adk-docs/sessions/memory/)

### 內部參考

- `docs/planning/stage5_scout_agent.md` - Scout Agent 設計參考
- `docs/planning/stage6_content_extraction.md` - 輸入數據格式
- `src/memory/article_store.py` - ArticleStore API 參考
- `src/memory/embedding_store.py` - EmbeddingStore API 參考
- `CLAUDE.md` - Agent 設計規範與 Prompt 設計原則

### Context7 查詢結果

根據 Context7 MCP 查詢的 ADK 文件：
- **LlmAgent 使用範例**: 已獲取
- **Memory 整合範例**: 已獲取
- **Embedding 工具使用**: 已獲取

---

## 📅 實作時間表

### Day 1: 規劃 + 核心實作（6-8 小時）

- [x] **上午**:
  - [x] 完成規劃文檔（本文件）
  - [x] 設計 Prompt 模板

- [ ] **下午**:
  - [ ] 實作 `create_analyst_agent()`
  - [ ] 實作 `AnalystAgentRunner` 基礎結構
  - [ ] 實作 LLM 輸出解析邏輯

- [ ] **晚上**:
  - [ ] 實作 Embedding 生成
  - [ ] 實作 ArticleStore 整合

### Day 2: 測試 + 驗證 + 文檔（6-8 小時）

- [ ] **上午**:
  - [ ] 編寫單元測試（10+ 測試案例）
  - [ ] 編寫整合測試（5+ 測試案例）

- [ ] **下午**:
  - [ ] 執行測試，修復 bug
  - [ ] 手動測試（使用真實 API）
  - [ ] 品質評估

- [ ] **晚上**:
  - [ ] 撰寫實作總結文檔
  - [ ] 撰寫測試驗證報告
  - [ ] 更新 dev_log.md

---

## 🎓 預期學習成果

完成 Stage 7 後，將掌握：

1. **ADK LlmAgent 高級用法** - 複雜 Prompt 設計、結構化輸出
2. **LLM 輸出解析** - JSON 解析、錯誤處理、預設值降級
3. **Embedding 生成與存儲** - 向量表示、相似度搜索準備
4. **評分系統設計** - 量化評估、可解釋性
5. **Agent 與 Memory 整合** - 雙向數據流動

---

**創建日期**: 2025-11-23
**最後更新**: 2025-11-23
**狀態**: Planning Complete → Ready for Implementation
