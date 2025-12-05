# Curator Daily Agent - 日報生成邏輯詳解

> **文件版本**: 1.0
> **建立日期**: 2025-12-05
> **最後更新**: 2025-12-05

---

## 目錄

1. [概述](#概述)
2. [完整流程圖](#完整流程圖)
3. [Step 1: 文章篩選](#step-1-文章篩選)
4. [Step 2: 去重機制](#step-2-去重機制)
5. [Step 3: LLM 摘要生成](#step-3-llm-摘要生成)
6. [Step 4: 格式化與發送](#step-4-格式化與發送)
7. [已知問題與改進建議](#已知問題與改進建議)
8. [相關檔案](#相關檔案)

---

## 概述

Curator Daily Agent 負責從已分析的文章中策展出每日精選，生成結構化摘要並透過 Email 發送給使用者。

**核心職責：**
- 從 Memory (SQLite) 取得高優先度文章
- 去重相似內容
- 使用 LLM 生成結構化日報
- 格式化為 HTML/Text 郵件並發送

**技術棧：**
- LLM: Gemini 2.5 Flash
- Database: SQLite
- Email: SMTP over TLS

---

## 完整流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 3: Curator Agent                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: 從資料庫取得文章                                        │
│  ────────────────────────────────────────────────────────────── │
│  article_store.get_top_priority(limit=30, status='analyzed')    │
│                                                                 │
│  SQL 邏輯:                                                       │
│    SELECT * FROM articles                                       │
│    WHERE status = 'analyzed'                                    │
│      AND priority_score IS NOT NULL                             │
│    ORDER BY priority_score DESC                                 │
│    LIMIT 30                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: 去重處理 (Jaccard Similarity)                          │
│  ────────────────────────────────────────────────────────────── │
│  對每篇文章:                                                     │
│    1. 提取 title + summary[:150] 的關鍵字                       │
│    2. 中文: 2-4 字詞組                                          │
│    3. 英文: 3+ 字母單詞                                         │
│    4. 領域詞加權                                                │
│                                                                 │
│  相似度計算:                                                     │
│    Jaccard = |A ∩ B| / |A ∪ B|                                  │
│    如果 Jaccard > 0.35 → 判定為重複，跳過                        │
│                                                                 │
│  結果: 30 篇 → 10 篇 (去重後)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: LLM 生成摘要                                           │
│  ────────────────────────────────────────────────────────────── │
│  輸入給 Gemini 2.5 Flash:                                       │
│    - 10 篇文章的 JSON                                           │
│    - Prompt: prompts/daily_prompt.txt                           │
│    - 個人化變數: {{USER_NAME}}, {{USER_INTERESTS}}              │
│                                                                 │
│  LLM 輸出:                                                       │
│    - top_articles: 精簡摘要 + 核心要點                          │
│    - daily_insight: 趨勢總結                                    │
│    - recommended_action: 建議行動                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: 格式化並發送                                           │
│  ────────────────────────────────────────────────────────────── │
│  DigestFormatter:                                               │
│    - format_html(): 響應式 HTML 郵件                            │
│    - format_text(): 純文本備用                                  │
│                                                                 │
│  EmailSender:                                                   │
│    - SMTP over TLS → 發送到 recipient_email                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: 文章篩選

### 程式碼位置

- `src/memory/article_store.py`: `get_top_priority()`
- `src/agents/curator_daily.py`: `fetch_analyzed_articles()`

### 篩選邏輯

```python
# src/memory/article_store.py (Lines 250-280)
def get_top_priority(self, limit: int = 10, status: Optional[str] = None):
    query = session.query(Article).filter(
        Article.priority_score.isnot(None)
    )

    if status:
        query = query.filter(Article.status == status)

    query = query.order_by(desc(Article.priority_score))
    query = query.limit(limit)

    return [article.to_dict() for article in query.all()]
```

### 調用方式

```python
# src/agents/curator_daily.py (Lines 296-301)
articles = self.article_store.get_top_priority(
    limit=max_articles * 3,  # 取 30 篇，為去重預留空間
    status='analyzed'
)
```

### 文章資料結構

每篇文章包含以下欄位：

| 欄位 | 說明 | 範例 |
|------|------|------|
| `id` | 文章 ID | 1019 |
| `title` | 標題 | "Google Releases Gemini 2.0" |
| `url` | 原文連結 | "https://..." |
| `summary` | 分析摘要 | "Google 發布..." |
| `analysis` | 完整分析 JSON | `{key_insights, priority_reasoning}` |
| `priority_score` | 優先度 (0-1) | 0.95 |
| `tags` | 標籤 | "AI,LLM" |
| `source` | 來源類型 | "rss" / "google_search_grounding" |
| `source_name` | 來源名稱 | "TechCrunch" |
| `published_at` | 發布時間 | "2025-12-05" |
| `fetched_at` | 收集時間 | "2025-12-05 08:00:00" |
| `status` | 狀態 | "analyzed" |

---

## Step 2: 去重機制

### 程式碼位置

`src/agents/curator_daily.py`: `_deduplicate_articles()` (Lines 377-445)

### 去重演算法

採用 **Jaccard 相似度** 進行關鍵字比對：

```python
def _deduplicate_articles(self, articles, max_count):
    deduplicated = []
    seen_keywords = []

    for article in articles:
        if len(deduplicated) >= max_count:
            break

        # 1. 提取關鍵字
        combined_text = f"{title} {summary[:150]}".lower()

        # 中文: 2-4 字詞組
        chinese_phrases = re.findall(r'[\u4e00-\u9fff]{2,4}', combined_text)

        # 英文: 3+ 字母單詞
        english_words = re.findall(r'[A-Za-z]{3,}', combined_text)

        keywords = set(chinese_phrases + english_words)

        # 2. 領域詞加權
        domain_terms = [
            'vla', 'vlm', 'llm', 'amr', 'agv', 'cobot', 'humanoid',
            '機器人', '協作', '自主', '導航', '視覺', '語言', '動作'
        ]
        for term in domain_terms:
            if term in combined_text:
                keywords.add(f"__domain_{term}")  # 加權標記

        # 3. 計算 Jaccard 相似度
        is_duplicate = False
        for seen in seen_keywords:
            intersection = len(keywords & seen)
            union = len(keywords | seen)
            similarity = intersection / union if union > 0 else 0

            if similarity > 0.35:  # 閾值 35%
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(article)
            seen_keywords.append(keywords)

    return deduplicated
```

### 相似度計算範例

| 文章 A 關鍵字 | 文章 B 關鍵字 | 交集 | 聯集 | Jaccard | 結果 |
|---------------|---------------|------|------|---------|------|
| {robot, vla, manipulation, 機器人} | {robot, vla, arm, 機器人} | 3 | 5 | 0.60 | 重複 |
| {llm, agent, google, gemini} | {robot, humanoid, tesla} | 0 | 7 | 0.00 | 保留 |
| {nvidia, cuda, gpu, 程式} | {nvidia, gpu, 加速, 運算} | 2 | 6 | 0.33 | 保留 |

### 去重參數

- **閾值**: 0.35 (35% 相似度以上判定為重複)
- **取樣倍數**: 3x (取 30 篇，去重後保留 10 篇)
- **領域詞**: 加上 `__domain_` 前綴以增加權重

---

## Step 3: LLM 摘要生成

### 程式碼位置

- `src/agents/curator_daily.py`: `generate_digest()` (Lines 447-508)
- `prompts/daily_prompt.txt`: Prompt 模板

### Prompt 結構

```markdown
# Curator Daily Agent Instruction

## 角色定義
你是 InsightCosmos 的每日情報策展人（Daily Curator），專注於從已分析的
AI 與 Robotics 文章中提煉精華，為 {{USER_NAME}} 生成精簡而有洞察力的每日摘要。

## 任務目標
1. 整合關鍵資訊
2. 識別共同趨勢
3. 提取核心要點
4. 生成可行動的建議（可選）

## 使用者背景
- 姓名: {{USER_NAME}}
- 專業興趣: {{USER_INTERESTS}}
- 需求: 快速掌握每日重要進展，無需閱讀全文

## 執行步驟

### Step 1: 文章分析
- 理解核心內容（根據 summary + key_insights）
- 評估對使用者的價值
- 提取 1 個最重要的要點（key_takeaway）

### Step 2: 趨勢識別
- 識別文章間的共同主題
- 發現技術趨勢或產業動態
- 總結為 2-3 句話的「今日洞察」

### Step 3: 行動建議（可選）
- 如果有明確的學習方向或行動建議，簡短說明

## 輸出格式（JSON）
{
  "date": "YYYY-MM-DD",
  "total_articles": 10,
  "top_articles": [
    {
      "title": "原文章標題",
      "url": "原文章 URL",
      "summary": "精簡摘要（1-2 句，不超過 100 字）",
      "key_takeaway": "核心要點（1 句話，20-40 字）",
      "priority_score": 0.92,
      "tags": ["AI", "Robotics"]
    }
  ],
  "daily_insight": "今日趨勢總結（2-3 句，100-150 字）",
  "recommended_action": "建議行動（可選，1 句話）"
}

## 品質標準
- summary: 1-2 句話，不超過 100 字
- key_takeaway: 1 句話，20-40 字
- daily_insight: 2-3 句話，100-150 字
```

### LLM 調用流程

```python
# src/agents/curator_daily.py (Lines 475-508)
def generate_digest(self, articles, digest_date=None):
    # 1. 準備日期
    date_str = digest_date.strftime('%Y-%m-%d') if digest_date else date.today().strftime('%Y-%m-%d')

    # 2. 構建 LLM 輸入
    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
    user_input = f"""請根據以下文章列表生成今日摘要（日期: {date_str}）：

```json
{articles_json}
```

請以 JSON 格式回覆。"""

    # 3. 調用 LLM
    response = self._invoke_llm(user_input)

    # 4. 解析 JSON 回應
    digest = self._parse_digest_json(response)

    return digest
```

### JSON 解析支援格式

```python
# 支援的回應格式：
# 1. 純 JSON
{"date": "2025-12-05", ...}

# 2. Markdown JSON code block
```json
{"date": "2025-12-05", ...}
```

# 3. 通用 code block
```
{"date": "2025-12-05", ...}
```
```

---

## Step 4: 格式化與發送

### 程式碼位置

- `src/tools/digest_formatter.py`: `DigestFormatter`
- `src/tools/email_sender.py`: `EmailSender`

### HTML 格式化

```python
# src/tools/digest_formatter.py
class DigestFormatter:
    def format_html(self, digest: Dict) -> str:
        """生成響應式 HTML 郵件"""
        # 特色：
        # - 響應式設計 (max-width: 600px)
        # - 優先度視覺化 (顏色編碼)
        #   - 高優先度 (≥0.85): #ea4335 (紅)
        #   - 中優先度 (≥0.70): #fbbc04 (橙)
        #   - 低優先度 (<0.70): #34a853 (綠)
        # - 現代設計風格
```

### HTML 模板結構

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* 響應式樣式 */
        .container { max-width: 600px; margin: 0 auto; }
        .high-priority { border-left: 4px solid #ea4335; }
        .medium-priority { border-left: 4px solid #fbbc04; }
        .low-priority { border-left: 4px solid #34a853; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>InsightCosmos Daily Digest</h1>
            <div class="date">2025-12-05 | 10 篇精選文章</div>
        </div>

        <!-- Articles -->
        <div class="article high-priority">
            <div class="article-title">
                <a href="URL">[1] 文章標題</a>
            </div>
            <div class="article-summary">摘要內容</div>
            <div class="article-takeaway">核心要點</div>
            <div class="article-meta">
                <span class="tag">AI</span>
                <span class="priority-score">0.92</span>
            </div>
        </div>

        <!-- Daily Insight -->
        <div class="insight-section">
            <h2>今日洞察</h2>
            <p>洞察內容...</p>
        </div>

        <!-- Recommended Action -->
        <div class="action-section">
            <h2>建議行動</h2>
            <p>建議內容...</p>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>由 InsightCosmos 自動生成 | Powered by Google ADK & Gemini 2.5</p>
        </div>
    </div>
</body>
</html>
```

### Email 發送

```python
# src/tools/email_sender.py
class EmailSender:
    def send(self, to_email, subject, html_body, text_body):
        """發送 HTML + 純文本郵件"""
        # 使用 SMTP over TLS
        # 支援 Gmail SMTP (smtp.gmail.com:587)
```

---

## 已知問題與改進建議

### 問題 1: 缺少日期過濾

**現象：** 每天的日報可能包含多天前的舊文章，導致內容重複。

**原因：** `get_top_priority()` 只按 `priority_score` 排序，沒有限制 `fetched_at` 時間範圍。

**建議修改：**

```python
# src/memory/article_store.py
def get_top_priority(self, limit=10, status=None, days_back=1):
    query = session.query(Article).filter(
        Article.priority_score.isnot(None)
    )

    if status:
        query = query.filter(Article.status == status)

    # 加入時間過濾
    if days_back:
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(Article.fetched_at >= cutoff)

    query = query.order_by(desc(Article.priority_score))
    query = query.limit(limit)

    return [article.to_dict() for article in query.all()]
```

### 問題 2: 去重閾值可能過低

**現象：** 0.35 的 Jaccard 閾值可能讓一些相關但不同的文章被誤判為重複。

**建議：** 可考慮：
- 提高閾值至 0.40-0.45
- 使用 Embedding 向量相似度替代關鍵字匹配
- 結合標題相似度和內容相似度的加權計算

### 問題 3: Google Search Grounding 文章標題亂碼

**現象：** 來自 `google_search_grounding` 的文章標題常為 URL 編碼亂碼（如 "Auziyqgxzshk..."）

**目前處理：** 使用 `analysis.summary` 的第一句作為替代標題

```python
# src/agents/curator_daily.py (Lines 338-350)
is_garbled = (
    len(original_title) > 50 and
    original_title.startswith('Auziyq')
) or article.get('source') == 'google_search_grounding'

if is_garbled and analysis_summary:
    title = analysis_summary.split('。')[0][:80]
```

---

## 相關檔案

| 檔案路徑 | 說明 |
|---------|------|
| `src/agents/curator_daily.py` | Curator Daily Agent 主程式 |
| `src/agents/curator_weekly.py` | Curator Weekly Agent (週報) |
| `prompts/daily_prompt.txt` | 日報生成 Prompt |
| `prompts/weekly_prompt.txt` | 週報生成 Prompt |
| `src/memory/article_store.py` | 文章資料存取 |
| `src/tools/digest_formatter.py` | 郵件格式化工具 |
| `src/tools/email_sender.py` | Email 發送工具 |
| `src/tools/trend_analysis.py` | 趨勢分析工具 (週報用) |
| `src/orchestrator/daily_runner.py` | 日報完整流程編排 |

---

## 參考資料

- [Google ADK 文件](https://google.github.io/adk-docs/)
- [CLAUDE.md](../../CLAUDE.md) - 專案一致性指南
- [Phase 1 Overview](../planning/phase1_overview.md) - 第一階段規劃

---

*文件維護者: Ray 張瑞涵*
*最後更新: 2025-12-05*
