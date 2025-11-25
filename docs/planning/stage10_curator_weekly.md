# Stage 10: Curator Weekly Agent - 規劃文件

> **階段**: Phase 1 - Stage 10/12
> **目標**: 實現每週深度情報報告生成與趨勢分析
> **預計時間**: 2 天
> **創建日期**: 2025-11-25
> **負責人**: Ray 張瑞涵

---

## 📋 目錄

1. [目標說明](#目標說明)
2. [輸入/輸出定義](#輸入輸出定義)
3. [技術設計](#技術設計)
4. [Curator Weekly Agent 設計](#curator-weekly-agent-設計)
5. [Vector Clustering 工具設計](#vector-clustering-工具設計)
6. [趨勢分析設計](#趨勢分析設計)
7. [Weekly Report 格式設計](#weekly-report-格式設計)
8. [實作計劃](#實作計劃)
9. [測試策略](#測試策略)
10. [驗收標準](#驗收標準)
11. [風險與對策](#風險與對策)

---

## 🎯 目標說明

### 核心目標

實現 **Curator Weekly Agent**，負責分析本週所有已分析的文章，識別主題趨勢、進行向量聚類、生成深度洞察報告，並透過 Email 發送給使用者。

### 與 Daily Curator 的差異

| 維度 | Daily Curator | Weekly Curator |
|------|---------------|----------------|
| **時間範圍** | 24 小時 | 7 天 |
| **文章數量** | 5-10 篇 | 30-70 篇 |
| **分析深度** | 單篇優先度排序 | 主題聚類與趨勢識別 |
| **技術難點** | 文章篩選 | Vector Clustering、趨勢分析 |
| **報告內容** | Top 文章列表 | 主題分布、趨勢洞察、行動建議 |
| **報告長度** | 簡短摘要 (500-800 字) | 深度報告 (1500-2500 字) |

### 具體功能

1. **文章聚合**
   - 從 Memory 中取得本週已分析的文章（過去 7 天）
   - 過濾低優先度文章（priority_score < 0.6）
   - 取得對應的 Embedding 向量

2. **主題聚類**
   - 使用 K-Means 或 DBSCAN 對 Embedding 進行聚類
   - 識別 3-5 個主題集群
   - 為每個集群提取代表性文章與關鍵字

3. **趨勢分析**
   - 分析主題演化（本週 vs 上週）
   - 識別熱門趨勢（high priority + 多篇文章）
   - 識別新興話題（首次出現的主題）

4. **深度報告生成**
   - 使用 LLM 整合所有分析結果
   - 生成結構化的 Weekly Report
   - 包含：主題總覽、趨勢洞察、重點文章、行動建議
   - 支援 HTML 與純文字格式

5. **Email 發送**
   - 使用與 Daily Curator 相同的 EmailSender
   - 支援更豐富的 HTML 格式（圖表、分類展示）

### 與其他模組的關係

```
┌────────────────────────────────────────────────────┐
│              Curator Weekly Agent                  │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │ 1. 查詢本週文章                           │    │
│  │    → ArticleStore.get_by_date_range()    │    │
│  │    → EmbeddingStore.get_embeddings()     │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 2. Vector Clustering                     │    │
│  │    → K-Means / DBSCAN                    │    │
│  │    → 識別 3-5 個主題集群                  │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 3. 趨勢分析                               │    │
│  │    → 熱門趨勢識別                         │    │
│  │    → 新興話題偵測                         │    │
│  │    → 主題演化分析                         │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 4. LLM 深度報告生成                       │    │
│  │    → Gemini 2.5 Flash                    │    │
│  │    → Weekly Report (HTML + Text)         │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 5. Email 發送                             │    │
│  │    → EmailSender (SMTP)                  │    │
│  └──────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

---

## 📥 輸入/輸出定義

### 輸入

**來源 1**: `ArticleStore.get_by_date_range(start_date, end_date, min_priority=0.6)`

**數據結構**:
```python
[
    {
        "id": 1,
        "title": "文章標題",
        "url": "https://example.com/article",
        "summary": "文章摘要（LLM 生成）",
        "key_insights": ["洞察1", "洞察2", "洞察3"],
        "priority_score": 0.85,
        "priority_reasoning": "為何重要的理由",
        "tags": "AI,Multi-Agent,Robotics",
        "tech_stack": "Python,TensorFlow,ROS",
        "published_at": "2025-11-20T10:00:00Z",
        "source_name": "TechCrunch",
        "analyzed_at": "2025-11-20T12:00:00Z"
    },
    # ... 30-70 篇文章
]
```

**來源 2**: `EmbeddingStore.get_embeddings(article_ids)`

**數據結構**:
```python
[
    {
        "article_id": 1,
        "embedding": np.array([0.12, 0.34, ..., 0.89]),  # 768 維向量
        "created_at": "2025-11-20T12:00:00Z"
    },
    # ...
]
```

### 輸出

**1. Weekly Report 結構化數據**:
```python
{
    "week_start": "2025-11-18",
    "week_end": "2025-11-24",
    "total_articles": 52,
    "analyzed_articles": 48,
    "high_priority_articles": 25,

    # 主題聚類結果
    "topic_clusters": [
        {
            "cluster_id": 0,
            "topic_name": "Multi-Agent Systems Breakthroughs",  # LLM 生成
            "article_count": 12,
            "average_priority": 0.87,
            "key_keywords": ["multi-agent", "collaboration", "distributed AI"],
            "representative_articles": [
                {
                    "title": "...",
                    "url": "...",
                    "summary": "...",
                    "priority_score": 0.92
                },
                # Top 3 文章
            ]
        },
        # ... 3-5 個集群
    ],

    # 趨勢分析
    "trend_analysis": {
        "hot_trends": [
            {
                "trend_name": "AI Agent 商業化加速",
                "evidence": "本週 8 篇文章提及企業級部署",
                "significance": "相較上週增長 60%",
                "action_suggestion": "關注 Google ADK、LangGraph 的企業案例"
            },
            # ... 2-3 個熱門趨勢
        ],
        "emerging_topics": [
            {
                "topic": "Robotics Foundation Models",
                "first_appearance": "2025-11-22",
                "article_count": 3,
                "why_important": "可能是下一個技術突破方向"
            },
            # ... 1-2 個新興話題
        ]
    },

    # 重點文章（跨集群）
    "top_articles_overall": [
        {
            "title": "...",
            "url": "...",
            "summary": "...",
            "priority_score": 0.95,
            "why_top": "技術突破性強且實用性高"
        },
        # Top 5-7 篇
    ],

    # 洞察總結
    "weekly_insights": [
        "本週 AI Agent 領域呈現商業化加速趨勢",
        "Multi-Agent Systems 從學術研究轉向實際應用",
        "Robotics 與 AI 的融合出現新的突破"
    ],

    # 行動建議
    "recommended_actions": [
        "深入研究 Google ADK 的 Multi-Agent 架構",
        "追蹤 Robotics Foundation Models 的研究進展",
        "關注企業級 AI Agent 部署案例"
    ]
}
```

**2. HTML Email**:
- 豐富的視覺化呈現（主題分布圖、趨勢圖表）
- 分類展示（按集群、按優先度）
- 折疊/展開功能（避免過長）
- 可點擊的連結與標籤

**3. 純文字 Email**:
- 結構清晰的層次（# 標題）
- 易於閱讀的格式
- 適合純文字客戶端

### 副作用

1. **Email 發送記錄**: 記錄到日誌中
2. **聚類結果儲存**: 可選（未來可用於趨勢追蹤）

---

## 🏗️ 技術設計

### 整體架構

```
CuratorWeeklyAgent (LlmAgent)
    ↓
CuratorWeeklyRunner
    ↓ 呼叫
┌────────────────────────────────────────┐
│         VectorClusteringTool           │
│  (src/tools/vector_clustering.py)     │
│                                        │
│  - cluster_embeddings()                │
│  - extract_cluster_keywords()          │
│  - find_representative_articles()      │
└────────────────────────────────────────┘
    ↓ 呼叫
┌────────────────────────────────────────┐
│         TrendAnalysisTool              │
│  (src/tools/trend_analysis.py)        │
│                                        │
│  - identify_hot_trends()               │
│  - detect_emerging_topics()            │
│  - compare_with_previous_week()        │
└────────────────────────────────────────┘
    ↓ 呼叫
┌────────────────────────────────────────┐
│         DigestFormatter                │
│  (src/tools/digest_formatter.py)      │
│  - 擴展支援 Weekly Report              │
│  - format_weekly_html()                │
│  - format_weekly_text()                │
└────────────────────────────────────────┘
    ↓ 呼叫
┌────────────────────────────────────────┐
│         EmailSender                    │
│  (src/tools/email_sender.py)          │
│  - send_html_email()                   │
└────────────────────────────────────────┘
```

### 技術選型

#### 1. Vector Clustering

**選擇**: scikit-learn

**理由**:
- 成熟穩定、文檔完善
- 支援多種聚類算法（K-Means, DBSCAN, Agglomerative）
- 與 NumPy 無縫整合（Embedding 已是 np.array）

**算法選擇**:

**主力**: K-Means
- **優點**: 簡單高效、結果穩定、易於解釋
- **適用場景**: 文章數量適中（30-70 篇）
- **缺點**: 需預設集群數量（k=3-5）

**備用**: DBSCAN
- **優點**: 自動發現集群數量、處理噪音點
- **適用場景**: 文章主題分散、無明確集群數
- **缺點**: 參數調整較複雜（eps, min_samples）

**初步策略**: 優先使用 K-Means (k=4)，如效果不佳再嘗試 DBSCAN

#### 2. 關鍵字提取

**選擇**: TF-IDF (scikit-learn)

**理由**:
- 簡單有效、無需訓練
- 適合短文本（文章標題 + summary）
- 可直接用於關鍵字提取

**替代方案**: LLM 提取（更準確但成本高）

#### 3. 趨勢分析

**方法**: 統計分析 + LLM 推理

**流程**:
1. **統計分析**（Python）
   - 計算主題出現頻率
   - 比較本週 vs 上週
   - 識別新主題

2. **LLM 推理**（Gemini）
   - 理解趨勢意義
   - 生成行動建議
   - 撰寫洞察總結

### 依賴套件

新增依賴：
```txt
scikit-learn>=1.3.0  # K-Means, DBSCAN, TF-IDF
```

現有依賴（無需新增）：
```txt
numpy>=1.24.0        # 向量運算
```

---

## 🎨 Curator Weekly Agent 設計

### Prompt 模板設計

**文件**: `prompts/weekly_prompt.txt`

**設計原則**:
1. **明確角色** - 定位為「週報策展人」
2. **結構化輸出** - 要求 JSON 格式
3. **深度分析** - 強調趨勢識別與洞察提取
4. **個人化** - 針對 Ray 的興趣（AI、Robotics、Multi-Agent）

**Prompt 結構草案**:

```
你是 InsightCosmos 的「週報策展人」(Weekly Curator)，專門為 Ray 張瑞涵生成每週 AI 與 Robotics 領域的深度情報報告。

## 你的任務

根據本週收集的文章與聚類分析結果，生成一份結構化的週報，包含：
1. 主題分布總覽
2. 熱門趨勢識別
3. 新興話題偵測
4. 重點文章推薦
5. 洞察總結
6. 行動建議

## 輸入資料

你將收到以下資料：

1. **文章聚類結果** (topic_clusters):
   - 每個集群的代表性文章
   - 集群關鍵字
   - 文章數量與平均優先度

2. **趨勢分析結果** (trend_statistics):
   - 熱門主題（high frequency + high priority）
   - 新興主題（首次出現）
   - 與上週的變化

3. **Top 文章列表** (top_articles):
   - 本週優先度最高的文章

## 輸出格式

請以 JSON 格式輸出，包含以下欄位：

{
    "week_summary": "本週總結（2-3 句話）",

    "topic_clusters": [
        {
            "cluster_id": 0,
            "topic_name": "集群主題名稱（簡短有力）",
            "description": "集群描述（1-2 句）",
            "significance": "為何重要（1 句）"
        },
        // ... 3-5 個集群
    ],

    "hot_trends": [
        {
            "trend_name": "趨勢名稱",
            "evidence": "支持證據（引用文章）",
            "significance": "為何重要",
            "action_suggestion": "建議行動"
        },
        // ... 2-3 個熱門趨勢
    ],

    "emerging_topics": [
        {
            "topic": "新興話題名稱",
            "why_important": "為何值得關注",
            "suggested_tracking": "建議追蹤方向"
        },
        // ... 1-2 個新興話題
    ],

    "top_articles": [
        {
            "title": "文章標題",
            "why_top": "為何入選 Top（1 句）",
            "key_takeaway": "核心要點（1-2 句）"
        },
        // ... 5-7 篇
    ],

    "weekly_insights": [
        "洞察 1",
        "洞察 2",
        "洞察 3"
    ],

    "recommended_actions": [
        "行動建議 1",
        "行動建議 2",
        "行動建議 3"
    ]
}

## 寫作風格

- 簡潔有力，避免冗詞
- 技術準確，避免過度簡化
- 洞察深刻，超越表面現象
- 行動導向，提供實用建議
- 針對 Ray 的興趣（AI Agent、Multi-Agent Systems、Robotics）

## 質量標準

- 趨勢識別準確（不過度解讀）
- 洞察有深度（不只是羅列事實）
- 行動建議具體（可執行）
- 文字流暢易讀（適合週末閱讀）

## Example

[提供一個示例輸出]
```

### Agent 類設計

**文件**: `src/agents/curator_weekly.py`

**類**: `CuratorWeeklyAgent`

**主要方法**:

```python
def create_weekly_curator_agent() -> LlmAgent:
    """
    創建 Weekly Curator Agent

    Returns:
        LlmAgent: Weekly Curator Agent 實例
    """
    prompt = load_prompt("prompts/weekly_prompt.txt")

    agent = LlmAgent(
        name="WeeklyCurator",
        model=Gemini(model="gemini-2.5-flash-lite"),
        instruction=prompt,
        # Weekly Curator 不需要額外工具（數據已預處理）
        tools=[],
        output_key="weekly_report"
    )

    return agent
```

### Runner 類設計

**文件**: `src/agents/curator_weekly.py`

**類**: `CuratorWeeklyRunner`

**主要方法**:

```python
class CuratorWeeklyRunner:
    """
    Weekly Curator Agent 運行器

    負責完整的週報生成流程：
    1. 查詢本週文章與 Embeddings
    2. 向量聚類
    3. 趨勢分析
    4. LLM 生成報告
    5. 格式化 HTML/Text
    6. 發送 Email
    """

    def __init__(self, config: Config):
        """初始化"""
        self.config = config
        self.db = Database.from_config(config)
        self.article_store = ArticleStore(self.db)
        self.embedding_store = EmbeddingStore(self.db)
        self.logger = setup_logger("WeeklyCurator")

    def generate_weekly_report(
        self,
        week_start: str = None,  # "YYYY-MM-DD", 默認為 7 天前
        week_end: str = None,    # "YYYY-MM-DD", 默認為今天
        dry_run: bool = False
    ) -> dict:
        """
        生成週報並發送

        Args:
            week_start: 週開始日期（默認 7 天前）
            week_end: 週結束日期（默認今天）
            dry_run: 是否為測試模式（不發送郵件）

        Returns:
            dict: {
                "status": "success" | "error",
                "subject": str,
                "recipients": list,
                "html_body": str,
                "text_body": str,
                "error_message": str,  # 錯誤時
                "suggestion": str      # 錯誤時
            }
        """
        # 實作流程
        pass

    def _get_weekly_articles(self, start_date, end_date) -> List[dict]:
        """查詢本週文章"""
        pass

    def _cluster_articles(self, articles, embeddings) -> dict:
        """向量聚類"""
        pass

    def _analyze_trends(self, articles, clusters) -> dict:
        """趨勢分析"""
        pass

    def _generate_report_with_llm(self, clusters, trends, top_articles) -> dict:
        """使用 LLM 生成報告"""
        pass

    def _format_and_send(self, report_data, dry_run) -> dict:
        """格式化並發送郵件"""
        pass
```

**便捷函數**:

```python
def generate_weekly_report(
    config: Config = None,
    week_start: str = None,
    week_end: str = None,
    dry_run: bool = False
) -> dict:
    """
    便捷函數：生成週報

    Example:
        >>> from src.agents.curator_weekly import generate_weekly_report
        >>> result = generate_weekly_report(dry_run=True)
        >>> print(result["subject"])
    """
    if config is None:
        config = Config.from_env()

    runner = CuratorWeeklyRunner(config)
    return runner.generate_weekly_report(week_start, week_end, dry_run)
```

---

## 🧩 Vector Clustering 工具設計

### 工具文件

**文件**: `src/tools/vector_clustering.py`

### 核心類設計

```python
class VectorClusteringTool:
    """
    向量聚類工具

    使用 K-Means 或 DBSCAN 對文章 Embeddings 進行聚類，
    識別主題集群並提取關鍵字。

    Attributes:
        method (str): 聚類方法 ("kmeans" | "dbscan")
        n_clusters (int): 集群數量（K-Means 用）
        random_state (int): 隨機種子（確保可重現）
    """

    def __init__(
        self,
        method: str = "kmeans",
        n_clusters: int = 4,
        random_state: int = 42
    ):
        """初始化"""
        self.method = method
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.logger = setup_logger("VectorClustering")

    def cluster_embeddings(
        self,
        embeddings: np.ndarray,
        article_metadata: List[dict]
    ) -> dict:
        """
        對 Embeddings 進行聚類

        Args:
            embeddings: 向量矩陣，shape (n_articles, embedding_dim)
            article_metadata: 文章元數據列表
                [
                    {
                        "article_id": 1,
                        "title": "...",
                        "summary": "...",
                        "tags": "AI,Robotics",
                        "priority_score": 0.85
                    },
                    ...
                ]

        Returns:
            dict: {
                "status": "success" | "error",
                "clusters": [
                    {
                        "cluster_id": 0,
                        "article_ids": [1, 5, 12, ...],
                        "article_count": 12,
                        "average_priority": 0.87,
                        "centroid": np.array([...]),  # 集群中心向量
                        "articles": [
                            {
                                "article_id": 1,
                                "title": "...",
                                "distance_to_centroid": 0.23
                            },
                            ...
                        ]
                    },
                    ...
                ],
                "n_clusters": 4,
                "silhouette_score": 0.65,  # 聚類質量評分
                "error_message": str,  # 錯誤時
                "suggestion": str      # 錯誤時
            }
        """
        try:
            if self.method == "kmeans":
                return self._cluster_kmeans(embeddings, article_metadata)
            elif self.method == "dbscan":
                return self._cluster_dbscan(embeddings, article_metadata)
            else:
                return {
                    "status": "error",
                    "error_type": "invalid_method",
                    "error_message": f"Unknown clustering method: {self.method}",
                    "suggestion": "Use 'kmeans' or 'dbscan'"
                }
        except Exception as e:
            self.logger.error(f"Clustering failed: {e}")
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "suggestion": "Check embeddings shape and article_metadata format"
            }

    def _cluster_kmeans(self, embeddings, metadata) -> dict:
        """K-Means 聚類"""
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        # 聚類
        kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10
        )
        labels = kmeans.fit_predict(embeddings)

        # 計算聚類質量
        score = silhouette_score(embeddings, labels)

        # 組織結果
        clusters = self._organize_clusters(
            labels, embeddings, metadata, kmeans.cluster_centers_
        )

        return {
            "status": "success",
            "clusters": clusters,
            "n_clusters": self.n_clusters,
            "silhouette_score": float(score)
        }

    def _cluster_dbscan(self, embeddings, metadata) -> dict:
        """DBSCAN 聚類"""
        from sklearn.cluster import DBSCAN

        # DBSCAN 聚類（參數需調整）
        dbscan = DBSCAN(eps=0.5, min_samples=3)
        labels = dbscan.fit_predict(embeddings)

        # 計算集群中心（手動計算）
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # 移除噪音點

        cluster_centers = []
        for label in unique_labels:
            mask = labels == label
            centroid = embeddings[mask].mean(axis=0)
            cluster_centers.append(centroid)

        # 組織結果
        clusters = self._organize_clusters(
            labels, embeddings, metadata, cluster_centers
        )

        return {
            "status": "success",
            "clusters": clusters,
            "n_clusters": len(unique_labels),
            "silhouette_score": None  # DBSCAN 不計算此指標
        }

    def _organize_clusters(self, labels, embeddings, metadata, centroids) -> List[dict]:
        """組織聚類結果"""
        clusters = []
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # 跳過噪音點

        for i, label in enumerate(sorted(unique_labels)):
            mask = labels == label
            cluster_embeddings = embeddings[mask]
            cluster_metadata = [m for m, is_in in zip(metadata, mask) if is_in]

            # 計算每篇文章到集群中心的距離
            centroid = centroids[i] if i < len(centroids) else cluster_embeddings.mean(axis=0)
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)

            # 組織文章數據
            articles = []
            for meta, dist in zip(cluster_metadata, distances):
                articles.append({
                    "article_id": meta["article_id"],
                    "title": meta["title"],
                    "priority_score": meta["priority_score"],
                    "distance_to_centroid": float(dist)
                })

            # 排序（優先度高 + 距離中心近）
            articles.sort(key=lambda x: (
                -x["priority_score"],  # 優先度降序
                x["distance_to_centroid"]  # 距離升序
            ))

            clusters.append({
                "cluster_id": int(label),
                "article_ids": [a["article_id"] for a in articles],
                "article_count": len(articles),
                "average_priority": float(np.mean([a["priority_score"] for a in articles])),
                "centroid": centroid.tolist(),
                "articles": articles
            })

        return clusters

    def extract_cluster_keywords(
        self,
        cluster: dict,
        all_articles: List[dict],
        top_k: int = 5
    ) -> List[str]:
        """
        提取集群關鍵字（TF-IDF）

        Args:
            cluster: 單個集群數據
            all_articles: 所有文章（用於計算 IDF）
            top_k: 返回前 k 個關鍵字

        Returns:
            List[str]: 關鍵字列表
        """
        from sklearn.feature_extraction.text import TfidfVectorizer

        # 準備文本（集群內文章）
        cluster_texts = [
            a["title"] + " " + a.get("summary", "")
            for a in all_articles
            if a["article_id"] in cluster["article_ids"]
        ]

        # 準備背景文本（所有文章）
        all_texts = [
            a["title"] + " " + a.get("summary", "")
            for a in all_articles
        ]

        # TF-IDF
        vectorizer = TfidfVectorizer(max_features=100, stop_words="english")
        vectorizer.fit(all_texts)

        # 計算集群的 TF-IDF
        cluster_tfidf = vectorizer.transform(cluster_texts)
        avg_tfidf = cluster_tfidf.mean(axis=0).A1

        # 提取 Top K
        top_indices = avg_tfidf.argsort()[-top_k:][::-1]
        keywords = [vectorizer.get_feature_names_out()[i] for i in top_indices]

        return keywords

    def find_representative_articles(
        self,
        cluster: dict,
        top_n: int = 3
    ) -> List[dict]:
        """
        找出集群代表性文章（最接近中心 + 高優先度）

        Args:
            cluster: 集群數據
            top_n: 返回前 n 篇文章

        Returns:
            List[dict]: 代表性文章列表
        """
        # 已在 _organize_clusters 中排序
        return cluster["articles"][:top_n]
```

### 便捷函數

```python
def cluster_articles(
    embeddings: np.ndarray,
    article_metadata: List[dict],
    method: str = "kmeans",
    n_clusters: int = 4
) -> dict:
    """
    便捷函數：文章聚類

    Example:
        >>> from src.tools.vector_clustering import cluster_articles
        >>> result = cluster_articles(embeddings, metadata, n_clusters=4)
        >>> print(f"Found {result['n_clusters']} clusters")
    """
    tool = VectorClusteringTool(method=method, n_clusters=n_clusters)
    return tool.cluster_embeddings(embeddings, article_metadata)
```

---

## 📈 趨勢分析設計

### 工具文件

**文件**: `src/tools/trend_analysis.py`

### 核心類設計

```python
class TrendAnalysisTool:
    """
    趨勢分析工具

    分析文章主題分布、識別熱門趨勢、偵測新興話題。

    Attributes:
        logger (Logger): 日誌記錄器
    """

    def __init__(self):
        """初始化"""
        self.logger = setup_logger("TrendAnalysis")

    def identify_hot_trends(
        self,
        clusters: List[dict],
        min_article_count: int = 5,
        min_avg_priority: float = 0.75
    ) -> List[dict]:
        """
        識別熱門趨勢

        標準：
        1. 文章數量多（>= min_article_count）
        2. 平均優先度高（>= min_avg_priority）

        Args:
            clusters: 聚類結果
            min_article_count: 最少文章數
            min_avg_priority: 最低平均優先度

        Returns:
            List[dict]: [
                {
                    "cluster_id": 0,
                    "article_count": 12,
                    "average_priority": 0.87,
                    "trend_score": 0.92,  # 綜合評分
                    "evidence": "12 篇文章，平均優先度 0.87"
                },
                ...
            ]
        """
        hot_trends = []

        for cluster in clusters:
            if (cluster["article_count"] >= min_article_count and
                cluster["average_priority"] >= min_avg_priority):

                # 計算趨勢分數（文章數 * 平均優先度）
                trend_score = (
                    cluster["article_count"] / 10 *  # 標準化到 0-1
                    cluster["average_priority"]
                )

                hot_trends.append({
                    "cluster_id": cluster["cluster_id"],
                    "article_count": cluster["article_count"],
                    "average_priority": cluster["average_priority"],
                    "trend_score": min(trend_score, 1.0),
                    "evidence": f"{cluster['article_count']} 篇文章，平均優先度 {cluster['average_priority']:.2f}"
                })

        # 按趨勢分數排序
        hot_trends.sort(key=lambda x: x["trend_score"], reverse=True)

        return hot_trends

    def detect_emerging_topics(
        self,
        current_articles: List[dict],
        previous_articles: List[dict] = None,
        min_priority: float = 0.7
    ) -> List[dict]:
        """
        偵測新興話題

        標準：
        1. 本週首次出現（或上週沒有）
        2. 優先度較高（>= min_priority）
        3. 文章標題/摘要包含新關鍵字

        Args:
            current_articles: 本週文章
            previous_articles: 上週文章（可選）
            min_priority: 最低優先度閾值

        Returns:
            List[dict]: [
                {
                    "topic_keywords": ["robotics", "foundation", "model"],
                    "article_count": 3,
                    "first_appearance": "2025-11-22",
                    "articles": [
                        {"title": "...", "url": "...", "priority_score": 0.85},
                        ...
                    ]
                },
                ...
            ]
        """
        from collections import Counter
        import re

        # 提取本週關鍵字
        current_keywords = self._extract_keywords_from_articles(current_articles)

        # 提取上週關鍵字（如果有）
        if previous_articles:
            previous_keywords = self._extract_keywords_from_articles(previous_articles)
            # 找出新關鍵字
            new_keywords = set(current_keywords.keys()) - set(previous_keywords.keys())
        else:
            # 無上週數據，使用低頻但高優先度的關鍵字
            new_keywords = [k for k, v in current_keywords.items() if v["count"] <= 5]

        # 聚合成主題
        emerging_topics = []
        for keyword in new_keywords:
            keyword_info = current_keywords.get(keyword)
            if keyword_info and keyword_info["avg_priority"] >= min_priority:
                emerging_topics.append({
                    "topic_keywords": [keyword],
                    "article_count": keyword_info["count"],
                    "first_appearance": keyword_info["first_date"],
                    "average_priority": keyword_info["avg_priority"],
                    "articles": keyword_info["articles"][:3]  # Top 3
                })

        # 按優先度排序
        emerging_topics.sort(key=lambda x: x["average_priority"], reverse=True)

        return emerging_topics

    def _extract_keywords_from_articles(self, articles: List[dict]) -> dict:
        """
        從文章中提取關鍵字統計

        Returns:
            dict: {
                "keyword": {
                    "count": 5,
                    "avg_priority": 0.82,
                    "first_date": "2025-11-22",
                    "articles": [...]
                },
                ...
            }
        """
        from collections import defaultdict
        import re

        keyword_stats = defaultdict(lambda: {
            "count": 0,
            "priorities": [],
            "dates": [],
            "articles": []
        })

        for article in articles:
            # 從標題和標籤提取關鍵字
            text = article.get("title", "") + " " + article.get("tags", "")
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())  # 至少 4 字元

            # 過濾常見詞
            stopwords = {"with", "from", "that", "this", "have", "been", "more"}
            words = [w for w in words if w not in stopwords]

            for word in set(words):  # 去重
                keyword_stats[word]["count"] += 1
                keyword_stats[word]["priorities"].append(article.get("priority_score", 0))
                keyword_stats[word]["dates"].append(article.get("published_at", ""))
                keyword_stats[word]["articles"].append({
                    "title": article["title"],
                    "url": article["url"],
                    "priority_score": article.get("priority_score", 0)
                })

        # 計算平均值
        result = {}
        for keyword, stats in keyword_stats.items():
            result[keyword] = {
                "count": stats["count"],
                "avg_priority": sum(stats["priorities"]) / len(stats["priorities"]),
                "first_date": min(stats["dates"]) if stats["dates"] else "",
                "articles": sorted(
                    stats["articles"],
                    key=lambda x: x["priority_score"],
                    reverse=True
                )
            }

        return result

    def compare_with_previous_week(
        self,
        current_clusters: List[dict],
        previous_clusters: List[dict] = None
    ) -> dict:
        """
        與上週比較（可選功能，Phase 1 可簡化）

        Args:
            current_clusters: 本週聚類結果
            previous_clusters: 上週聚類結果

        Returns:
            dict: {
                "growth_topics": [...],      # 增長主題
                "declining_topics": [...],   # 衰退主題
                "stable_topics": [...]       # 穩定主題
            }
        """
        # Phase 1 簡化版本：僅返回空結果
        return {
            "growth_topics": [],
            "declining_topics": [],
            "stable_topics": []
        }
```

### 便捷函數

```python
def analyze_weekly_trends(
    clusters: List[dict],
    current_articles: List[dict],
    previous_articles: List[dict] = None
) -> dict:
    """
    便捷函數：週趨勢分析

    Returns:
        dict: {
            "hot_trends": [...],
            "emerging_topics": [...]
        }

    Example:
        >>> from src.tools.trend_analysis import analyze_weekly_trends
        >>> result = analyze_weekly_trends(clusters, articles)
        >>> print(f"Found {len(result['hot_trends'])} hot trends")
    """
    tool = TrendAnalysisTool()

    hot_trends = tool.identify_hot_trends(clusters)
    emerging_topics = tool.detect_emerging_topics(current_articles, previous_articles)

    return {
        "hot_trends": hot_trends,
        "emerging_topics": emerging_topics
    }
```

---

## 📧 Weekly Report 格式設計

### HTML Email 設計

**擴展**: `src/tools/digest_formatter.py`

**新增方法**:

```python
def format_weekly_html(weekly_report: dict) -> str:
    """
    生成週報 HTML 格式

    Args:
        weekly_report: LLM 生成的週報數據

    Returns:
        str: HTML 字串
    """
    # HTML 模板（更豐富的樣式）
    pass
```

**設計要點**:

1. **頂部總結區**
   - 週期標註（2025-11-18 to 2025-11-24）
   - 統計數據（總文章數、分析數、高優先度數）
   - 週總結（1-2 句話）

2. **主題集群展示**
   - 每個集群一個卡片
   - 包含：主題名稱、文章數、關鍵字、代表性文章
   - 可視化：進度條顯示文章數量佔比

3. **熱門趨勢區**
   - 突出顯示（彩色標籤）
   - 趨勢名稱 + 證據 + 意義 + 建議行動
   - 排序：趨勢分數降序

4. **新興話題區**
   - 標註「NEW」徽章
   - 話題名稱 + 為何重要 + 追蹤建議

5. **Top 文章列表**
   - 編號列表（1-7）
   - 文章標題（可點擊）+ 入選理由 + 要點

6. **洞察與行動建議**
   - 洞察列表（bullet points）
   - 行動建議（checkbox 風格）

### 純文字 Email 設計

**新增方法**:

```python
def format_weekly_text(weekly_report: dict) -> str:
    """
    生成週報純文字格式

    Args:
        weekly_report: LLM 生成的週報數據

    Returns:
        str: 純文字字串
    """
    # Markdown-like 格式
    pass
```

**設計要點**:

```
================================================================================
InsightCosmos Weekly Report
Week: 2025-11-18 to 2025-11-24
================================================================================

📊 WEEKLY SUMMARY
--------------------------------------------------------------------------------
Total Articles: 52 | Analyzed: 48 | High Priority: 25

本週 AI Agent 領域呈現商業化加速趨勢，Multi-Agent Systems 從學術研究
轉向實際應用，Robotics 與 AI 的融合出現新的突破。

================================================================================
🔥 HOT TRENDS
================================================================================

1. Multi-Agent Systems 商業化加速
   Evidence: 本週 12 篇文章，平均優先度 0.87
   Significance: 相較上月增長 60%，企業級部署案例顯著增加
   Action: 深入研究 Google ADK 的 Multi-Agent 架構

2. AI Agent 開發工具成熟
   Evidence: ...
   Significance: ...
   Action: ...

================================================================================
🌱 EMERGING TOPICS
================================================================================

• Robotics Foundation Models
  Why Important: 可能是下一個技術突破方向
  Suggested Tracking: 關注 Google DeepMind、OpenAI 的機器人研究

================================================================================
📰 TOP ARTICLES
================================================================================

1. [Title] Multi-Agent Systems: The Next Frontier in AI
   URL: https://...
   Why Top: 技術突破性強且實用性高
   Key Takeaway: 提出新的 Multi-Agent 協作架構...

2. [Title] ...

...

================================================================================
💡 WEEKLY INSIGHTS
================================================================================

• 本週 AI Agent 領域呈現商業化加速趨勢
• Multi-Agent Systems 從學術研究轉向實際應用
• Robotics 與 AI 的融合出現新的突破

================================================================================
✅ RECOMMENDED ACTIONS
================================================================================

[ ] 深入研究 Google ADK 的 Multi-Agent 架構
[ ] 追蹤 Robotics Foundation Models 的研究進展
[ ] 關注企業級 AI Agent 部署案例

================================================================================
Generated by InsightCosmos | Your Personal Intelligence Universe
================================================================================
```

---

## 🛠️ 實作計劃

### 文件結構

```
src/
├─ tools/
│   ├─ vector_clustering.py       # 新增
│   ├─ trend_analysis.py          # 新增
│   └─ digest_formatter.py        # 擴展（新增 weekly 方法）
├─ agents/
│   └─ curator_weekly.py          # 新增
prompts/
└─ weekly_prompt.txt              # 新增
```

### 開發步驟

#### Step 1: Vector Clustering 工具 (3 小時)

1. 創建 `src/tools/vector_clustering.py`
2. 實作 `VectorClusteringTool` 類
3. 實作 K-Means 聚類方法
4. 實作關鍵字提取方法
5. 實作代表性文章篩選
6. 編寫單元測試

#### Step 2: Trend Analysis 工具 (2 小時)

1. 創建 `src/tools/trend_analysis.py`
2. 實作 `TrendAnalysisTool` 類
3. 實作熱門趨勢識別
4. 實作新興話題偵測
5. 編寫單元測試

#### Step 3: Weekly Prompt 設計 (1 小時)

1. 創建 `prompts/weekly_prompt.txt`
2. 撰寫詳細指令
3. 設計輸出結構
4. 準備示例輸出

#### Step 4: Weekly Curator Agent (3 小時)

1. 創建 `src/agents/curator_weekly.py`
2. 實作 `create_weekly_curator_agent()` 函數
3. 實作 `CuratorWeeklyRunner` 類
4. 實作 `generate_weekly_report()` 方法
5. 整合所有工具（clustering, trend, formatter, email）

#### Step 5: 擴展 DigestFormatter (2 小時)

1. 修改 `src/tools/digest_formatter.py`
2. 新增 `format_weekly_html()` 方法
3. 新增 `format_weekly_text()` 方法
4. 設計豐富的 HTML 樣式

#### Step 6: 測試與驗證 (3 小時)

1. 編寫單元測試
2. 編寫整合測試
3. 手動端到端測試
4. 調整參數與優化

#### Step 7: 文檔與總結 (1 小時)

1. 編寫實作筆記
2. 編寫測試報告
3. 更新 PROGRESS.md
4. 更新 src/agents/__init__.py

---

## 🧪 測試策略

### 單元測試

#### 1. VectorClusteringTool 測試

**文件**: `tests/unit/test_vector_clustering.py`

**測試案例**:

1. `test_kmeans_clustering_basic()` - 基本聚類功能
2. `test_kmeans_clustering_with_metadata()` - 包含元數據的聚類
3. `test_cluster_organization()` - 聚類結果組織
4. `test_extract_cluster_keywords()` - 關鍵字提取
5. `test_find_representative_articles()` - 代表性文章篩選
6. `test_invalid_embeddings_shape()` - 錯誤輸入處理
7. `test_silhouette_score_calculation()` - 聚類質量評分

#### 2. TrendAnalysisTool 測試

**文件**: `tests/unit/test_trend_analysis.py`

**測試案例**:

1. `test_identify_hot_trends()` - 熱門趨勢識別
2. `test_detect_emerging_topics()` - 新興話題偵測
3. `test_extract_keywords_from_articles()` - 關鍵字提取
4. `test_trend_score_calculation()` - 趨勢分數計算
5. `test_empty_articles()` - 空文章列表處理

#### 3. CuratorWeeklyRunner 測試

**文件**: `tests/unit/test_curator_weekly.py`

**測試案例**:

1. `test_runner_initialization()` - 初始化測試
2. `test_get_weekly_articles()` - 週文章查詢
3. `test_cluster_articles()` - 聚類調用
4. `test_analyze_trends()` - 趨勢分析調用
5. `test_generate_report_with_llm()` - LLM 報告生成（Mock）
6. `test_format_and_send()` - 格式化與發送
7. `test_full_pipeline_dry_run()` - 完整流程測試（dry_run=True）

#### 4. DigestFormatter 擴展測試

**文件**: `tests/unit/test_digest_formatter.py`（擴展）

**新增測試案例**:

1. `test_format_weekly_html()` - HTML 格式化
2. `test_format_weekly_text()` - 純文字格式化
3. `test_weekly_html_structure()` - HTML 結構驗證
4. `test_weekly_text_readability()` - 純文字可讀性

### 整合測試

**文件**: `tests/integration/test_curator_weekly.py`

**測試案例**:

1. `test_weekly_pipeline_with_mock_data()` - 使用 Mock 數據的完整流程
2. `test_weekly_clustering_integration()` - 聚類與文章整合
3. `test_weekly_trend_analysis_integration()` - 趨勢分析整合
4. `test_weekly_llm_report_generation()` - LLM 報告生成（需真實 API）
5. `test_weekly_email_sending()` - Email 發送（dry_run=False，手動）

### 端到端測試（手動）

**測試案例**:

1. **完整週報生成（測試模式）**
   ```bash
   python -c "from src.agents.curator_weekly import generate_weekly_report; generate_weekly_report(dry_run=True)"
   ```
   預期：完整流程執行，輸出報告內容到控制台

2. **完整週報生成（生產模式）**
   ```bash
   python -c "from src.agents.curator_weekly import generate_weekly_report; generate_weekly_report()"
   ```
   預期：完整流程執行，發送郵件到指定信箱

3. **聚類質量驗證**
   - 檢查聚類數量（應為 3-5 個）
   - 檢查 Silhouette Score（應 > 0.5）
   - 檢查集群大小分布（不應過度不均）

4. **趨勢識別驗證**
   - 檢查熱門趨勢數量（應為 2-3 個）
   - 檢查新興話題數量（應為 1-2 個）
   - 檢查趨勢合理性（人工判斷）

---

## ✅ 驗收標準

### 功能驗收

- [ ] **文章聚類** - 能正確將本週文章聚類成 3-5 個主題
- [ ] **關鍵字提取** - 每個集群能提取 3-5 個代表性關鍵字
- [ ] **趨勢識別** - 能識別 2-3 個熱門趨勢
- [ ] **新興話題偵測** - 能偵測 1-2 個新興話題
- [ ] **LLM 報告生成** - 能生成結構化的週報數據
- [ ] **HTML 格式化** - 能生成美觀的 HTML Email
- [ ] **純文字格式化** - 能生成易讀的純文字 Email
- [ ] **Email 發送** - 能成功發送週報到指定信箱

### 品質驗收

- [ ] **聚類質量** - Silhouette Score >= 0.5
- [ ] **關鍵字相關性** - 關鍵字與集群主題相符（人工判斷）
- [ ] **趨勢準確性** - 趨勢識別合理（人工判斷）
- [ ] **報告可讀性** - 報告內容流暢、結構清晰
- [ ] **洞察深度** - 洞察超越簡單羅列，有分析價值

### 測試驗收

- [ ] **單元測試通過率** - 100%
- [ ] **整合測試通過率** - >= 90%
- [ ] **代碼覆蓋率** - 核心邏輯覆蓋率 >= 85%
- [ ] **文檔完整性** - 所有公開方法有 docstring

### 性能驗收

- [ ] **聚類耗時** - 50 篇文章聚類 < 5 秒
- [ ] **LLM 生成耗時** - 報告生成 < 30 秒
- [ ] **總執行時間** - 完整流程 < 2 分鐘（50 篇文章）

---

## ⚠️ 風險與對策

### 風險 1: 聚類質量不穩定

**風險描述**: K-Means 依賴初始中心點，可能導致聚類結果不穩定

**影響**: 每次執行得到不同的主題分布

**對策**:
1. 設置 `random_state=42` 確保可重現性
2. 使用 `n_init=10` 多次初始化取最佳結果
3. 如效果仍不佳，嘗試 DBSCAN 或 Agglomerative Clustering

**優先級**: 高

---

### 風險 2: 文章數量不足

**風險描述**: 某些週文章數量 < 30 篇，聚類效果差

**影響**: 無法形成有意義的集群

**對策**:
1. 設置最小文章數閾值（如 20 篇）
2. 文章不足時降級為「Top 文章列表」模式（類似 Daily）
3. 動態調整聚類數量（文章少時 k=2-3）

**優先級**: 中

---

### 風險 3: LLM 輸出格式錯誤

**風險描述**: LLM 偶爾返回非標準 JSON 格式

**影響**: 報告生成失敗

**對策**:
1. 使用與 Daily Curator 相同的 JSON 解析策略（支援 Markdown 包裝）
2. 實現降級解析（部分欄位缺失時補充默認值）
3. 記錄原始輸出便於調試

**優先級**: 中

---

### 風險 4: 關鍵字提取不準確

**風險描述**: TF-IDF 可能提取到無意義的關鍵字

**影響**: 集群主題不明確

**對策**:
1. 擴展停用詞列表（stopwords）
2. 設置最小詞長（>= 4 字元）
3. 如效果不佳，改用 LLM 提取關鍵字（成本高但準確）

**優先級**: 低

---

### 風險 5: 週報過長

**風險描述**: 50+ 篇文章的週報可能過於冗長

**影響**: 用戶閱讀負擔重

**對策**:
1. 限制每個集群最多顯示 3 篇代表性文章
2. 限制 Top 文章列表為 5-7 篇
3. 設計可折疊的 HTML 區塊（詳細內容可選擇展開）

**優先級**: 低

---

## 📚 參考資料

### 技術文件

- [scikit-learn Clustering](https://scikit-learn.org/stable/modules/clustering.html)
- [scikit-learn TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [Silhouette Score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)

### ADK 官方文件

- [LlmAgent](https://google.github.io/adk-docs/agents/llm/)
- [Sessions & Memory](https://google.github.io/adk-docs/sessions/)

### 專案內部文件

- `docs/planning/stage8_curator_daily.md` - Daily Curator 設計
- `docs/planning/stage7_analyst_agent.md` - Analyst Agent 設計
- `CLAUDE.md` - 專案一致性指南

---

## 🎯 下一步

完成 Stage 10 後，接續：

1. **Stage 11**: Weekly Pipeline 集成（週報流程編排）
2. **Stage 12**: 質量保證與優化（QA & Optimization）

---

**創建者**: Ray 張瑞涵
**創建日期**: 2025-11-25
**最後更新**: 2025-11-25
**狀態**: 規劃完成，待實作
