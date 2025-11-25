# Stage 10: Curator Weekly Agent - 測試報告

> **階段**: Phase 1 - Stage 10/12
> **目標**: 測試每週深度情報報告生成與趨勢分析功能
> **測試日期**: 2025-11-25
> **負責人**: Ray 張瑞涵
> **狀態**: ✅ 核心實作完成，待完整測試驗證

---

## 📋 目錄

1. [測試總覽](#測試總覽)
2. [單元測試](#單元測試)
3. [整合測試](#整合測試)
4. [手動測試](#手動測試)
5. [測試數據](#測試數據)
6. [已知問題](#已知問題)
7. [驗收結果](#驗收結果)

---

## 🎯 測試總覽

### 測試範圍

| 模組 | 文件 | 測試項目 | 狀態 |
|------|------|----------|------|
| VectorClusteringTool | `vector_clustering.py` | K-Means 聚類、關鍵字提取 | ⏳ 待測試 |
| TrendAnalysisTool | `trend_analysis.py` | 趨勢識別、新興話題偵測 | ⏳ 待測試 |
| CuratorWeeklyRunner | `curator_weekly.py` | 完整週報生成流程 | ⏳ 待測試 |
| Weekly Prompt | `weekly_prompt.txt` | LLM 輸出結構化 | ⏳ 待測試 |

### 測試依賴

- **scikit-learn**: 需安裝 `>=1.3.0`
- **numpy**: 已安裝
- **資料庫**: 需有已分析的文章數據
- **Embedding**: 需有已生成的向量數據

---

## 🧪 單元測試

### 測試文件規劃

#### 1. VectorClusteringTool 測試

**文件**: `tests/unit/test_vector_clustering.py`

**測試案例**:

| 測試案例 | 說明 | 預期結果 | 狀態 |
|----------|------|----------|------|
| `test_kmeans_clustering_basic` | 基本 K-Means 聚類 | 返回正確數量的集群 | ⏳ |
| `test_kmeans_with_metadata` | 含元數據的聚類 | 集群包含文章資訊 | ⏳ |
| `test_dynamic_cluster_count` | 動態調整集群數 | 不超過文章數-1 | ⏳ |
| `test_silhouette_score` | 聚類質量評分 | 返回有效分數 | ⏳ |
| `test_extract_keywords` | TF-IDF 關鍵字提取 | 返回 Top K 關鍵字 | ⏳ |
| `test_representative_articles` | 代表性文章篩選 | 按優先度排序 | ⏳ |
| `test_invalid_input` | 無效輸入處理 | 返回錯誤訊息 | ⏳ |
| `test_insufficient_data` | 文章數不足 | 返回錯誤訊息 | ⏳ |

#### 2. TrendAnalysisTool 測試

**文件**: `tests/unit/test_trend_analysis.py`

**測試案例**:

| 測試案例 | 說明 | 預期結果 | 狀態 |
|----------|------|----------|------|
| `test_identify_hot_trends` | 熱門趨勢識別 | 返回符合條件的趨勢 | ⏳ |
| `test_trend_score_calculation` | 趨勢分數計算 | 正確計算公式 | ⏳ |
| `test_detect_emerging_topics` | 新興話題偵測 | 識別低頻高優先度 | ⏳ |
| `test_keyword_extraction` | 關鍵字提取統計 | 正確統計詞頻 | ⏳ |
| `test_stopwords_filtering` | 停用詞過濾 | 過濾常見詞 | ⏳ |
| `test_empty_input` | 空輸入處理 | 返回空列表 | ⏳ |
| `test_generate_summary` | 趨勢摘要生成 | 返回結構化摘要 | ⏳ |

#### 3. CuratorWeeklyRunner 測試

**文件**: `tests/unit/test_curator_weekly.py`

**測試案例**:

| 測試案例 | 說明 | 預期結果 | 狀態 |
|----------|------|----------|------|
| `test_runner_init` | Runner 初始化 | 正確初始化依賴 | ⏳ |
| `test_get_weekly_articles` | 週文章查詢 | 返回日期範圍內文章 | ⏳ |
| `test_cluster_articles` | 文章聚類調用 | 正確調用聚類工具 | ⏳ |
| `test_analyze_trends` | 趨勢分析調用 | 正確調用趨勢工具 | ⏳ |
| `test_prepare_llm_input` | LLM 輸入準備 | 正確格式化數據 | ⏳ |
| `test_parse_llm_output` | LLM 輸出解析 | 支援 JSON/Markdown | ⏳ |
| `test_format_simple_text` | 簡單文字格式化 | 輸出可讀文字 | ⏳ |
| `test_format_simple_html` | 簡單 HTML 格式化 | 輸出有效 HTML | ⏳ |
| `test_dry_run_mode` | 測試模式 | 不發送郵件 | ⏳ |

---

## 🔗 整合測試

### 測試文件規劃

**文件**: `tests/integration/test_curator_weekly_integration.py`

**測試案例**:

| 測試案例 | 說明 | 預期結果 | 狀態 |
|----------|------|----------|------|
| `test_clustering_with_embeddings` | 聚類與 Embedding 整合 | 正確聚類文章向量 | ⏳ |
| `test_trend_with_clusters` | 趨勢分析與聚類整合 | 基於聚類識別趨勢 | ⏳ |
| `test_full_pipeline_mock` | Mock 數據完整流程 | 流程正確執行 | ⏳ |
| `test_full_pipeline_real` | 真實數據完整流程 | 生成有效週報 | ⏳ |
| `test_llm_report_generation` | LLM 報告生成 | 返回結構化 JSON | ⏳ |
| `test_email_dry_run` | Email 測試模式 | 正確格式化郵件 | ⏳ |

---

## 🖥️ 手動測試

### 測試 1: Import 測試

**命令**:
```bash
python test_stage10_import.py
```

**預期輸出**:
```
============================================================
Stage 10 Import Test
============================================================

[Test 1] VectorClusteringTool import...
✓ VectorClusteringTool import successful

[Test 2] TrendAnalysisTool import...
✓ TrendAnalysisTool import successful

[Test 3] CuratorWeeklyRunner import...
✓ CuratorWeeklyRunner import successful

[Test 4] scikit-learn availability...
✓ scikit-learn version: 1.x.x

============================================================
Import Test Complete
============================================================
```

**狀態**: ⏳ 待執行

### 測試 2: 聚類功能測試

**命令**:
```python
from src.tools.vector_clustering import VectorClusteringTool
import numpy as np

# 創建測試數據
embeddings = np.random.rand(20, 768)
metadata = [
    {"article_id": i, "title": f"Article {i}", "priority_score": 0.8}
    for i in range(20)
]

# 測試聚類
tool = VectorClusteringTool(n_clusters=3)
result = tool.cluster_embeddings(embeddings, metadata)

print(f"Status: {result['status']}")
print(f"Clusters: {result['n_clusters']}")
print(f"Silhouette: {result.get('silhouette_score', 'N/A')}")
```

**預期結果**:
- Status: success
- Clusters: 3
- Silhouette: > 0.0 (有效分數)

**狀態**: ⏳ 待執行

### 測試 3: 趨勢分析測試

**命令**:
```python
from src.tools.trend_analysis import TrendAnalysisTool

# 創建測試集群
clusters = [
    {"cluster_id": 0, "article_count": 10, "average_priority": 0.85},
    {"cluster_id": 1, "article_count": 5, "average_priority": 0.75},
    {"cluster_id": 2, "article_count": 3, "average_priority": 0.90}
]

# 測試熱門趨勢識別
tool = TrendAnalysisTool()
hot_trends = tool.identify_hot_trends(clusters, min_article_count=5, min_avg_priority=0.75)

print(f"Hot trends found: {len(hot_trends)}")
for trend in hot_trends:
    print(f"  - Cluster {trend['cluster_id']}: score={trend['trend_score']:.2f}")
```

**預期結果**:
- 識別出 2 個熱門趨勢（cluster_id 0 和 1）
- 按趨勢分數排序

**狀態**: ⏳ 待執行

### 測試 4: 完整週報生成（Dry Run）

**命令**:
```bash
python -c "
from src.agents.curator_weekly import generate_weekly_report
result = generate_weekly_report(dry_run=True)
print(f'Status: {result[\"status\"]}')
if result['status'] == 'success':
    print(f'Subject: {result[\"subject\"]}')
    print(f'HTML length: {len(result.get(\"html_body\", \"\"))} chars')
else:
    print(f'Error: {result.get(\"error_message\", \"Unknown\")}')
"
```

**預期結果**:
- Status: success
- Subject: InsightCosmos Weekly Report - YYYY-MM-DD to YYYY-MM-DD
- HTML length: > 1000 chars

**狀態**: ⏳ 待執行

### 測試 5: 完整週報生成（Production）

**命令**:
```bash
python -c "
from src.agents.curator_weekly import generate_weekly_report
result = generate_weekly_report(dry_run=False)
print(f'Status: {result[\"status\"]}')
"
```

**預期結果**:
- Status: success
- Email 成功發送到指定信箱

**狀態**: ⏳ 待執行

---

## 📊 測試數據

### 測試數據需求

| 數據類型 | 最低數量 | 建議數量 | 說明 |
|----------|----------|----------|------|
| 已分析文章 | 15 | 30-50 | status='analyzed' |
| Embedding 向量 | 15 | 30-50 | 對應文章 ID |
| 高優先度文章 | 5 | 10-20 | priority_score >= 0.6 |

### 測試數據驗證

**查詢已分析文章數量**:
```sql
SELECT COUNT(*) FROM articles WHERE status = 'analyzed';
```

**查詢 Embedding 數量**:
```sql
SELECT COUNT(*) FROM embeddings;
```

**查詢高優先度文章**:
```sql
SELECT COUNT(*) FROM articles
WHERE status = 'analyzed' AND priority_score >= 0.6;
```

---

## ⚠️ 已知問題

### 問題 1: scikit-learn 未安裝

**問題描述**: 虛擬環境中可能尚未安裝 scikit-learn

**影響**: 聚類功能無法執行

**解決方案**:
```bash
source .venv/bin/activate
pip install scikit-learn>=1.3.0
```

### 問題 2: 文章數量不足

**問題描述**: 資料庫中可能沒有足夠的已分析文章

**影響**: 聚類效果差或無法執行

**解決方案**:
1. 先執行 Daily Pipeline 收集文章
2. 或手動插入測試數據

### 問題 3: DigestFormatter Weekly 方法未實作

**問題描述**: `format_weekly_html()` 和 `format_weekly_text()` 尚未實作

**影響**: 使用臨時簡單格式

**解決方案**: 使用內建的 `_format_simple_html()` 和 `_format_simple_text()` 方法（已實作）

---

## ✅ 驗收結果

### 功能驗收

| 功能 | 驗收標準 | 結果 | 備註 |
|------|----------|------|------|
| 文章聚類 | 能聚類成 3-5 個主題 | ⏳ | 待測試 |
| 關鍵字提取 | 每集群 3-5 個關鍵字 | ⏳ | 待測試 |
| 熱門趨勢識別 | 識別 2-3 個趨勢 | ⏳ | 待測試 |
| 新興話題偵測 | 偵測 1-2 個新話題 | ⏳ | 待測試 |
| LLM 報告生成 | 生成結構化 JSON | ⏳ | 待測試 |
| HTML 格式化 | 生成有效 HTML | ⏳ | 待測試 |
| Email 發送 | 成功發送郵件 | ⏳ | 待測試 |

### 品質驗收

| 指標 | 驗收標準 | 結果 | 備註 |
|------|----------|------|------|
| 聚類質量 | Silhouette >= 0.5 | ⏳ | 待測試 |
| 關鍵字相關性 | 人工判斷相符 | ⏳ | 待測試 |
| 趨勢準確性 | 人工判斷合理 | ⏳ | 待測試 |
| 報告可讀性 | 結構清晰 | ⏳ | 待測試 |

### 測試驗收

| 指標 | 驗收標準 | 結果 | 備註 |
|------|----------|------|------|
| 單元測試通過率 | 100% | ⏳ | 待編寫 |
| 整合測試通過率 | >= 90% | ⏳ | 待編寫 |
| 代碼覆蓋率 | >= 85% | ⏳ | 待測量 |

### 性能驗收

| 指標 | 驗收標準 | 結果 | 備註 |
|------|----------|------|------|
| 聚類耗時 | < 5 秒 (50 篇) | ⏳ | 待測試 |
| LLM 生成耗時 | < 30 秒 | ⏳ | 待測試 |
| 總執行時間 | < 2 分鐘 | ⏳ | 待測試 |

---

## 📝 測試執行記錄

### 執行日期: 待補充

**執行環境**:
- OS: Linux (WSL2)
- Python: 3.10+
- scikit-learn: 待確認

**執行結果**:
- 單元測試: 待執行
- 整合測試: 待執行
- 手動測試: 待執行

**問題記錄**:
- 待補充

---

## 🎯 下一步

1. **安裝 scikit-learn**
   ```bash
   pip install scikit-learn>=1.3.0
   ```

2. **執行 Import 測試**
   ```bash
   python test_stage10_import.py
   ```

3. **執行手動功能測試**

4. **編寫單元測試**

5. **執行完整測試套件**

---

**創建者**: Ray 張瑞涵
**創建日期**: 2025-11-25
**最後更新**: 2025-11-25
**狀態**: 測試規劃完成，待執行
