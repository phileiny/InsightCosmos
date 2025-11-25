# Stage 10: Curator Weekly Agent - 實作筆記

> **階段**: Phase 1 - Stage 10/12
> **目標**: 實現每週深度情報報告生成與趨勢分析
> **實作日期**: 2025-11-25
> **負責人**: Ray 張瑞涵
> **狀態**: ✅ 核心實作完成（待測試驗證）

---

## 📋 目錄

1. [實作總覽](#實作總覽)
2. [VectorClusteringTool 實作](#vectorclusteringtool-實作)
3. [TrendAnalysisTool 實作](#trendanalysistool-實作)
4. [Weekly Prompt 設計](#weekly-prompt-設計)
5. [CuratorWeeklyRunner 實作](#curatorweeklyrunner-實作)
6. [模組更新](#模組更新)
7. [測試指南](#測試指南)
8. [已知問題](#已知問題)
9. [下一步](#下一步)

---

## 🎯 實作總覽

### 完成內容

Stage 10 核心實作已完成，包含：

1. ✅ **VectorClusteringTool** - 向量聚類工具（~350 行）
2. ✅ **TrendAnalysisTool** - 趨勢分析工具（~330 行）
3. ✅ **Weekly Prompt** - LLM 指令模板（~300 行）
4. ✅ **CuratorWeeklyRunner** - 週報運行器（~650 行）
5. ✅ **模組更新** - __init__.py 與依賴更新

**總代碼量**: ~1,660 行（不含測試）

### 技術棧

- **聚類算法**: scikit-learn (K-Means, DBSCAN)
- **關鍵字提取**: TF-IDF (scikit-learn)
- **LLM**: Gemini 2.0 Flash Exp
- **記憶層**: ArticleStore + EmbeddingStore (SQLite + NumPy)

---

## 🧩 VectorClusteringTool 實作

### 文件位置

`src/tools/vector_clustering.py`

### 核心類設計

```python
class VectorClusteringTool:
    """
    向量聚類工具

    使用 K-Means 或 DBSCAN 對文章 Embeddings 進行聚類
    """

    def __init__(
        self,
        method: str = "kmeans",
        n_clusters: int = 4,
        random_state: int = 42
    ):
        """初始化聚類工具"""

    def cluster_embeddings(
        self,
        embeddings: np.ndarray,
        article_metadata: List[Dict]
    ) -> Dict:
        """主要聚類方法"""

    def extract_cluster_keywords(
        self,
        cluster: Dict,
        all_articles: List[Dict],
        top_k: int = 5
    ) -> List[str]:
        """TF-IDF 關鍵字提取"""

    def find_representative_articles(
        self,
        cluster: Dict,
        top_n: int = 3
    ) -> List[Dict]:
        """找出代表性文章"""
```

### 關鍵實作細節

#### 1. K-Means 聚類

```python
def _cluster_kmeans(self, embeddings, metadata):
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    # 動態調整聚類數量（不能超過文章數）
    n_clusters = min(self.n_clusters, len(embeddings) - 1)

    # K-Means 聚類（多次初始化取最佳）
    kmeans = KMeans(
        n_clusters=n_clusters,
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
        "n_clusters": n_clusters,
        "silhouette_score": float(score)
    }
```

#### 2. TF-IDF 關鍵字提取

```python
def extract_cluster_keywords(self, cluster, all_articles, top_k=5):
    from sklearn.feature_extraction.text import TfidfVectorizer

    # 準備集群文本
    cluster_texts = [
        a["title"] + " " + a.get("summary", "")
        for a in all_articles
        if a["article_id"] in cluster["article_ids"]
    ]

    # 準備背景語料
    all_texts = [
        a["title"] + " " + a.get("summary", "")
        for a in all_articles
    ]

    # TF-IDF 向量化
    vectorizer = TfidfVectorizer(
        max_features=100,
        stop_words="english",
        ngram_range=(1, 2)  # 1-2 個詞的短語
    )
    vectorizer.fit(all_texts)

    # 計算集群的 TF-IDF
    cluster_tfidf = vectorizer.transform(cluster_texts)
    avg_tfidf = cluster_tfidf.mean(axis=0).A1

    # 提取 Top K
    top_indices = avg_tfidf.argsort()[-top_k:][::-1]
    keywords = [vectorizer.get_feature_names_out()[i] for i in top_indices]

    return keywords
```

#### 3. 動態聚類數量調整

在 `CuratorWeeklyRunner._cluster_articles()` 中：

```python
# 動態調整聚類數量
n_articles = len(articles)
if n_articles >= 40:
    n_clusters = 5
elif n_articles >= 25:
    n_clusters = 4
elif n_articles >= 15:
    n_clusters = 3
else:
    n_clusters = 2
```

### 設計決策

1. **K-Means 為主力**
   - 優勢：簡單高效、結果穩定、易於解釋
   - 適用：文章數量適中（30-70 篇）
   - 參數：`n_init=10` 確保結果穩定

2. **DBSCAN 為備用**
   - 優勢：自動發現集群數量
   - 劣勢：參數調整較複雜
   - 應用：文章主題分散時使用

3. **Silhouette Score 評估**
   - 範圍：-1 到 1
   - 目標：>= 0.5 為良好聚類
   - 用途：監控聚類質量

---

## 📈 TrendAnalysisTool 實作

### 文件位置

`src/tools/trend_analysis.py`

### 核心類設計

```python
class TrendAnalysisTool:
    """趨勢分析工具"""

    def identify_hot_trends(
        self,
        clusters: List[Dict],
        min_article_count: int = 5,
        min_avg_priority: float = 0.75
    ) -> List[Dict]:
        """識別熱門趨勢"""

    def detect_emerging_topics(
        self,
        current_articles: List[Dict],
        previous_articles: Optional[List[Dict]] = None,
        min_priority: float = 0.7
    ) -> List[Dict]:
        """偵測新興話題"""

    def _extract_keywords_from_articles(
        self,
        articles: List[Dict]
    ) -> Dict[str, Dict]:
        """從文章中提取關鍵字統計"""
```

### 關鍵實作細節

#### 1. 熱門趨勢識別

```python
def identify_hot_trends(self, clusters, min_article_count=5, min_avg_priority=0.75):
    hot_trends = []

    for cluster in clusters:
        article_count = cluster.get("article_count", 0)
        avg_priority = cluster.get("average_priority", 0.0)

        # 檢查標準：文章多 + 優先度高
        if (article_count >= min_article_count and
            avg_priority >= min_avg_priority):

            # 計算趨勢分數
            normalized_count = min(article_count / 10, 1.0)
            trend_score = normalized_count * avg_priority

            hot_trends.append({
                "cluster_id": cluster["cluster_id"],
                "article_count": article_count,
                "average_priority": avg_priority,
                "trend_score": trend_score,
                "evidence": f"{article_count} 篇文章，平均優先度 {avg_priority:.2f}"
            })

    # 按趨勢分數排序
    hot_trends.sort(key=lambda x: x["trend_score"], reverse=True)

    return hot_trends
```

#### 2. 新興話題偵測

```python
def detect_emerging_topics(self, current_articles, previous_articles=None, min_priority=0.7):
    # 提取本週關鍵字
    current_keywords = self._extract_keywords_from_articles(current_articles)

    # 如果有上週數據，找出新關鍵字
    if previous_articles:
        previous_keywords = self._extract_keywords_from_articles(previous_articles)
        new_keywords = set(current_keywords.keys()) - set(previous_keywords.keys())
    else:
        # 無上週數據，使用低頻高優先度的關鍵字
        new_keywords = [
            k for k, v in current_keywords.items()
            if v["count"] <= 5 and v["avg_priority"] >= min_priority
        ]

    # 聚合成新興話題
    emerging_topics = []
    for keyword in new_keywords:
        keyword_info = current_keywords.get(keyword)
        if keyword_info and keyword_info["avg_priority"] >= min_priority:
            emerging_topics.append({
                "topic_keywords": [keyword],
                "article_count": keyword_info["count"],
                "first_appearance": keyword_info["first_date"],
                "average_priority": keyword_info["avg_priority"],
                "articles": keyword_info["articles"][:3]
            })

    # 按優先度排序
    emerging_topics.sort(key=lambda x: x["average_priority"], reverse=True)

    return emerging_topics
```

#### 3. 關鍵字提取

```python
def _extract_keywords_from_articles(self, articles):
    from collections import defaultdict
    import re

    keyword_stats = defaultdict(lambda: {
        "count": 0,
        "priorities": [],
        "dates": [],
        "articles": []
    })

    # 停用詞
    stopwords = {
        "with", "from", "that", "this", "have", "been", "more",
        # ... 更多停用詞
    }

    for article in articles:
        # 從標題、標籤、摘要提取文本
        text = ""
        text += article.get("title", "") + " "
        text += article.get("tags", "") + " "
        text += article.get("summary", "")[:200]

        # 提取至少 4 字元的單詞
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())

        # 過濾停用詞
        words = [w for w in words if w not in stopwords]

        # 統計（每篇文章每個詞只計數一次）
        for word in set(words):
            keyword_stats[word]["count"] += 1
            keyword_stats[word]["priorities"].append(article.get("priority_score", 0.0))
            # ...

    # 計算平均值
    result = {}
    for keyword, stats in keyword_stats.items():
        result[keyword] = {
            "count": stats["count"],
            "avg_priority": sum(stats["priorities"]) / len(stats["priorities"]),
            "first_date": min(stats["dates"]) if stats["dates"] else "",
            "articles": sorted(stats["articles"], key=lambda x: x["priority_score"], reverse=True)
        }

    return result
```

### 設計決策

1. **趨勢分數公式**
   - `trend_score = (article_count / 10) * avg_priority`
   - 平衡：文章數量 vs 優先度
   - 標準化：10 篇文章視為滿分

2. **新興話題標準**
   - 低頻（<= 5 篇）+ 高優先度（>= 0.7）
   - 或：本週首次出現的關鍵字
   - 目的：發現潛力話題，而非已知熱門

3. **關鍵字提取策略**
   - 最小長度：4 字元（過濾 "is", "the" 等）
   - 去重：每篇文章每個詞只計數一次
   - 停用詞：擴展的英文停用詞列表

---

## 📝 Weekly Prompt 設計

### 文件位置

`prompts/weekly_prompt.txt`

### Prompt 結構

```
你是 InsightCosmos 的「週報策展人」(Weekly Curator)

## 你的任務
- 本週總結
- 主題集群分析
- 熱門趨勢識別
- 新興話題偵測
- Top 文章推薦
- 洞察總結
- 行動建議

## 輸入資料
{JSON 格式的輸入數據定義}

## 輸出格式
{嚴格的 JSON Schema}

## 寫作風格指南
- 語言：繁體中文
- 簡潔有力
- 技術準確
- 洞察深刻
- 行動導向

## Example
{完整示例輸出}
```

### 關鍵設計

1. **明確角色定位**
   - 「週報策展人」而非通用 AI
   - 針對 Ray 的興趣領域
   - 技術水平：高級開發者

2. **結構化輸出**
   - 嚴格 JSON 格式（不使用 Markdown 包裝）
   - 7 個主要欄位
   - 每個欄位都有明確的格式要求

3. **質量標準**
   - 趨勢識別準確性
   - 洞察深度
   - 行動建議具體性
   - 文字流暢性

4. **完整示例**
   - 提供真實的輸出範例
   - 展示期望的寫作風格
   - 明確數據與洞察的關係

---

## 🎨 CuratorWeeklyRunner 實作

### 文件位置

`src/agents/curator_weekly.py`

### 核心流程

```
generate_weekly_report()
    ↓
1. _get_weekly_articles()       # 查詢本週文章（7 天）
    ↓
2. _cluster_articles()           # 向量聚類（K-Means）
    ↓
3. _analyze_trends()             # 趨勢分析
    ↓
4. _generate_report_with_llm()   # LLM 生成報告
    ↓
5. _format_and_send()            # 格式化並發送
```

### 關鍵方法實作

#### 1. 查詢本週文章

```python
def _get_weekly_articles(self, week_start, week_end):
    # 計算日期範圍（默認過去 7 天）
    if week_end is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(week_end, "%Y-%m-%d")

    if week_start is None:
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(week_start, "%Y-%m-%d")

    # 查詢已分析的文章
    articles = self.article_store.get_by_date_range(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        status="analyzed",
        min_priority=0.6  # 過濾低優先度
    )

    return articles
```

#### 2. 向量聚類

```python
def _cluster_articles(self, articles):
    # 獲取 Embeddings
    article_ids = [a["id"] for a in articles]
    embeddings_data = self.embedding_store.get_embeddings(article_ids)

    if not embeddings_data:
        return {
            "status": "error",
            "error_type": "no_embeddings",
            "error_message": "No embeddings found"
        }

    # 組織成 numpy 矩陣
    embeddings_matrix = np.array([e["embedding"] for e in embeddings_data])

    # 準備元數據
    metadata = [
        {
            "article_id": a["id"],
            "title": a["title"],
            "summary": a.get("summary", ""),
            "tags": a.get("tags", ""),
            "priority_score": a.get("priority_score", 0.0)
        }
        for a in articles
    ]

    # 動態調整聚類數量
    n_articles = len(articles)
    n_clusters = 5 if n_articles >= 40 else (4 if n_articles >= 25 else 3)

    # 執行聚類
    clustering_tool = VectorClusteringTool(n_clusters=n_clusters)
    result = clustering_tool.cluster_embeddings(embeddings_matrix, metadata)

    # 提取關鍵字
    if result["status"] == "success":
        for cluster in result["clusters"]:
            keywords = clustering_tool.extract_cluster_keywords(cluster, articles, top_k=5)
            cluster["keywords"] = keywords

    return result
```

#### 3. LLM 報告生成

```python
def _generate_report_with_llm(self, articles, clusters, trend_result, week_start, week_end):
    # 準備輸入數據
    input_data = self._prepare_llm_input(articles, clusters, trend_result, week_start, week_end)

    # 創建 Agent
    agent = create_weekly_curator_agent()

    # 調用 LLM
    session_service = InMemorySessionService()
    session = session_service.create_session()

    input_json = json.dumps(input_data, ensure_ascii=False, indent=2)

    response = agent.send_message(
        message=f"請根據以下數據生成週報：\n\n{input_json}",
        session=session
    )

    # 解析輸出（支援 Markdown 包裝）
    report_json = self._parse_llm_output(response.final_response)

    if report_json is None:
        return {
            "status": "error",
            "error_type": "parse_error",
            "error_message": "Failed to parse LLM output"
        }

    return {
        "status": "success",
        "report": report_json
    }
```

#### 4. 準備 LLM 輸入

```python
def _prepare_llm_input(self, articles, clusters, trend_result, week_start, week_end):
    # 集群數據（含代表性文章）
    clusters_with_articles = []
    for cluster in clusters:
        cluster_data = {
            "cluster_id": cluster["cluster_id"],
            "article_count": cluster["article_count"],
            "average_priority": cluster["average_priority"],
            "keywords": cluster.get("keywords", []),
            "representative_articles": []
        }

        # 取前 3 篇代表性文章
        for article_info in cluster["articles"][:3]:
            full_article = next((a for a in articles if a["id"] == article_info["article_id"]), None)
            if full_article:
                cluster_data["representative_articles"].append({
                    "title": full_article["title"],
                    "url": full_article["url"],
                    "summary": full_article.get("summary", ""),
                    "priority_score": full_article.get("priority_score", 0.0)
                })

        clusters_with_articles.append(cluster_data)

    # Top 文章（全局 Top 10）
    top_articles = sorted(articles, key=lambda x: x.get("priority_score", 0.0), reverse=True)[:10]

    # 組合完整輸入
    return {
        "week_start": str(start_date),
        "week_end": str(end_date),
        "total_articles": len(articles),
        "analyzed_articles": len(articles),
        "topic_clusters": clusters_with_articles,
        "hot_trends": trend_result["hot_trends"],
        "emerging_topics": trend_result["emerging_topics"],
        "top_articles_overall": top_articles_data
    }
```

#### 5. 簡單格式化（臨時方案）

```python
def _format_and_send(self, report_data, dry_run):
    # 生成主題
    subject = f"InsightCosmos Weekly Report - {report_data.get('week_start')} to {report_data.get('week_end')}"

    # 格式化（臨時使用簡單格式）
    text_body = self._format_simple_text(report_data)
    html_body = self._format_simple_html(report_data)

    # 發送郵件
    if not dry_run:
        sender = EmailSender(self.config)
        send_result = sender.send_html_email(
            to_email=self.config.email_account,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        return send_result
    else:
        return {
            "status": "success",
            "subject": subject,
            "recipients": [self.config.email_account],
            "html_body": html_body,
            "text_body": text_body
        }
```

### 設計決策

1. **日期範圍**
   - 默認：過去 7 天
   - 可自定義：`week_start` 和 `week_end`
   - 格式：`YYYY-MM-DD`

2. **最低優先度閾值**
   - 查詢文章：>= 0.6
   - 熱門趨勢：>= 0.75
   - 新興話題：>= 0.7

3. **動態聚類數量**
   - 40+ 篇：5 個集群
   - 25-39 篇：4 個集群
   - 15-24 篇：3 個集群
   - <15 篇：2 個集群

4. **錯誤處理**
   - 分層錯誤處理（每個步驟獨立）
   - 詳細錯誤訊息與建議
   - 狀態碼："success" 或 "error"

---

## 🔧 模組更新

### 1. src/tools/__init__.py

**版本**: 1.4.0

**更新內容**:
```python
from src.tools.vector_clustering import VectorClusteringTool, cluster_articles
from src.tools.trend_analysis import TrendAnalysisTool, analyze_weekly_trends

__all__ = [
    # ... existing exports
    'VectorClusteringTool',
    'cluster_articles',
    'TrendAnalysisTool',
    'analyze_weekly_trends',
]
```

### 2. src/agents/__init__.py

**版本**: 1.3.0

**更新內容**:
```python
from src.agents.curator_weekly import (
    CuratorWeeklyRunner,
    create_weekly_curator_agent,
    generate_weekly_report
)

__all__ = [
    # ... existing exports
    'CuratorWeeklyRunner',
    'create_weekly_curator_agent',
    'generate_weekly_report'
]
```

### 3. requirements.txt

**新增依賴**:
```txt
scikit-learn>=1.3.0  # K-Means, DBSCAN, TF-IDF
```

---

## 🧪 測試指南

### 手動測試步驟

#### 1. 安裝依賴

```bash
# 啟動虛擬環境
source .venv/bin/activate

# 安裝 scikit-learn
pip install scikit-learn>=1.3.0
```

#### 2. Import 測試

```bash
# 運行測試腳本
python test_stage10_import.py
```

**預期輸出**:
```
============================================================
Stage 10 Import Test
============================================================

[Test 1] VectorClusteringTool import...
✓ VectorClusteringTool import successful
✓ VectorClusteringTool initialization: method=kmeans, n_clusters=3

[Test 2] TrendAnalysisTool import...
✓ TrendAnalysisTool import successful
✓ TrendAnalysisTool initialization successful

[Test 3] CuratorWeeklyRunner import...
✓ CuratorWeeklyRunner import successful
✓ create_weekly_curator_agent import successful
✓ generate_weekly_report import successful

[Test 4] Tools module export...
✓ VectorClusteringTool exported from src.tools
✓ TrendAnalysisTool exported from src.tools

[Test 5] Agents module export...
✓ CuratorWeeklyRunner exported from src.agents
✓ create_weekly_curator_agent exported from src.agents
✓ generate_weekly_report exported from src.agents

[Test 6] scikit-learn availability...
✓ scikit-learn version: 1.5.x
✓ sklearn.cluster.KMeans import successful
✓ sklearn.feature_extraction.text.TfidfVectorizer import successful

============================================================
Import Test Complete
============================================================
```

#### 3. 功能測試（需要已分析的文章）

```bash
# 啟動虛擬環境
source .venv/bin/activate

# 運行 Weekly Curator（Dry Run）
python -c "from src.agents.curator_weekly import generate_weekly_report; result = generate_weekly_report(dry_run=True); print(result['status'])"
```

### 單元測試（待編寫）

需要創建以下測試文件：

1. **`tests/unit/test_vector_clustering.py`**
   - `test_kmeans_clustering_basic()`
   - `test_extract_cluster_keywords()`
   - `test_find_representative_articles()`
   - `test_invalid_input_handling()`

2. **`tests/unit/test_trend_analysis.py`**
   - `test_identify_hot_trends()`
   - `test_detect_emerging_topics()`
   - `test_extract_keywords_from_articles()`

3. **`tests/unit/test_curator_weekly.py`**
   - `test_runner_initialization()`
   - `test_get_weekly_articles()`
   - `test_cluster_articles()`
   - `test_analyze_trends()`
   - `test_generate_report_with_llm()`

### 整合測試（待編寫）

**`tests/integration/test_curator_weekly.py`**
- `test_weekly_pipeline_with_mock_data()`
- `test_weekly_clustering_integration()`
- `test_weekly_trend_analysis_integration()`

---

## ⚠️ 已知問題

### 1. scikit-learn 安裝問題

**問題**: WSL 環境下虛擬環境命令執行異常緩慢

**影響**: 無法在當前會話中完成安裝與測試

**解決方案**:
```bash
# 手動安裝（在虛擬環境外）
pip install --user scikit-learn

# 或在虛擬環境中（可能需要較長時間）
source .venv/bin/activate
pip install scikit-learn>=1.3.0
```

### 2. DigestFormatter 未擴展

**問題**: `format_weekly_html()` 和 `format_weekly_text()` 尚未實作

**當前方案**: 使用臨時的簡單格式化方法

**待完成**:
- 創建豐富的 Weekly HTML 格式
- 創建結構化的 Weekly Text 格式

### 3. 測試覆蓋率

**問題**: 尚未編寫單元測試與整合測試

**影響**: 代碼未經充分測試驗證

**優先級**: 高（下一步工作）

---

## 🎯 下一步

### 立即執行（本階段）

1. ✅ **核心實作** - 已完成
2. ⏳ **安裝 scikit-learn** - 待手動執行
3. ⏳ **Import 測試** - 待執行 `test_stage10_import.py`
4. ⏳ **基本功能測試** - 運行 dry_run 模式

### 近期計劃（Stage 10 完善）

1. **擴展 DigestFormatter**
   - 實作 `format_weekly_html()`
   - 實作 `format_weekly_text()`
   - 設計豐富的視覺化樣式

2. **編寫測試**
   - VectorClustering 單元測試
   - TrendAnalysis 單元測試
   - CuratorWeekly 整合測試

3. **優化與調整**
   - 調整聚類參數（基於實際數據）
   - 調整趨勢識別閾值
   - 優化 Prompt（基於 LLM 輸出）

### 後續階段（Stage 11-12）

1. **Stage 11**: Weekly Pipeline 集成
   - 創建 Weekly Orchestrator
   - 整合完整週報流程
   - 排程與自動執行

2. **Stage 12**: 質量保證與優化
   - 完整測試覆蓋
   - 性能優化
   - 文檔完善
   - 部署準備

---

## 📊 統計數據

### 代碼統計

| 模組 | 文件 | 行數 | 說明 |
|------|------|------|------|
| VectorClusteringTool | vector_clustering.py | ~350 | K-Means, TF-IDF |
| TrendAnalysisTool | trend_analysis.py | ~330 | 趨勢分析 |
| CuratorWeeklyRunner | curator_weekly.py | ~650 | 週報運行器 |
| Weekly Prompt | weekly_prompt.txt | ~300 | LLM 指令 |
| 測試腳本 | test_stage10_import.py | ~120 | Import 測試 |
| **總計** | **5 個文件** | **~1,750 行** | **核心實作** |

### 模組更新

| 文件 | 版本 | 變更 |
|------|------|------|
| src/tools/__init__.py | 1.3.0 → 1.4.0 | +2 exports |
| src/agents/__init__.py | 1.2.0 → 1.3.0 | +3 exports |
| requirements.txt | - | +1 dependency |

---

## 🎓 技術亮點

### 1. 動態參數調整

根據文章數量自動調整聚類數量，確保聚類效果：

```python
n_articles = len(articles)
n_clusters = 5 if n_articles >= 40 else (4 if n_articles >= 25 else 3)
```

### 2. TF-IDF 關鍵字提取

使用 scikit-learn 的 TfidfVectorizer，支援 1-2 個詞的短語：

```python
vectorizer = TfidfVectorizer(
    max_features=100,
    stop_words="english",
    ngram_range=(1, 2)
)
```

### 3. 結構化 LLM 輸出

設計詳細的 Prompt，確保 LLM 輸出結構化 JSON：

```python
# Prompt 明確要求
"請嚴格按照以下 JSON 格式輸出（**不要使用 Markdown 包裝**）"
```

### 4. 錯誤處理策略

每個方法都返回結構化的結果，包含狀態碼、錯誤訊息與建議：

```python
return {
    "status": "error",
    "error_type": "no_embeddings",
    "error_message": "No embeddings found for articles",
    "suggestion": "Ensure Analyst Agent has generated embeddings"
}
```

---

## 📚 參考資料

### 技術文件

- [scikit-learn Clustering](https://scikit-learn.org/stable/modules/clustering.html)
- [scikit-learn TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [Silhouette Score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)

### 專案文件

- `docs/planning/stage10_curator_weekly.md` - 規劃文檔
- `docs/planning/stage8_curator_daily.md` - Daily Curator 參考
- `docs/planning/stage7_analyst_agent.md` - Analyst Agent 參考
- `CLAUDE.md` - 專案一致性指南

---

**創建者**: Ray 張瑞涵
**創建日期**: 2025-11-25
**最後更新**: 2025-11-25
**狀態**: ✅ 核心實作完成，待測試驗證
