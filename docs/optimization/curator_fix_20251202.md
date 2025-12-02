# Curator 修復報告 - 2025-12-02

## 問題描述

1. **標題亂碼**: Google Search Grounding 來源的文章標題顯示為 URL 編碼（如 `Auziyq...`）
2. **內容重複**: 多篇相似主題的文章（如 VLA 模型）同時出現在日報中

## 修復內容

### 1. 標題修復 (`src/agents/curator_daily.py`)

```python
# 檢測 Google Search Grounding 來源的亂碼標題
is_garbled = (
    len(original_title) > 50 and
    original_title.startswith('Auziyq')
) or article.get('source') == 'google_search_grounding'

# 使用 analysis summary 的第一句話作為標題
if is_garbled and analysis_summary:
    title = analysis_summary.split('。')[0][:80]
```

### 2. 去重邏輯 (`_deduplicate_articles` 方法)

```python
# 使用 Jaccard 相似度比較文章摘要（前 150 字元）
summary = article.get('summary', '')[:150]
title = article.get('title', '')
combined_text = f"{title} {summary}".lower()

# 提取 2-4 字元中文片語 + 英文關鍵字
chinese_phrases = re.findall(r'[\u4e00-\u9fff]{2,4}', combined_text)
english_words = re.findall(r'[A-Za-z]{3,}', combined_text)
keywords = set(chinese_phrases + english_words)

# 加入領域關鍵字權重
domain_terms = ['vla', 'vlm', 'llm', 'amr', 'agv', 'cobot', 'humanoid',
               '機器人', '協作', '自主', '導航', '視覺', '語言', '動作']
for term in domain_terms:
    if term in combined_text:
        keywords.add(f"__domain_{term}")

# 相似度 > 35% 視為重複（從 50% → 40% → 35%）
if similarity > 0.35:
    is_duplicate = True
```

## 執行結果

### v1 測試（閾值 50%）
- 去重效果: 30 → 10 篇
- VLA 相關文章: 4 篇（仍有重複）

### v2 測試（閾值 40%）
- 去重效果: 30 → 9 篇
- VLA 相關文章: 3 篇（略有改善）

### v3 測試（閾值 35%）- 最終版本
- 去重效果: 30 → 10 篇
- Email 發送: 成功發送到 sourcecor103@gmail.com
- VLA 相關文章: 3 篇（OpenVLA, Mantis, 1 篇綜述）
- 標題顯示: 使用 analysis summary 的中文摘要

## 待改進

1. **語意相似度**: 當前使用詞彙重疊的 Jaccard 相似度，可考慮使用 embedding 向量計算語意相似度

2. **Google Search URL**: 文章 URL 仍是 Google 重定向 URL，可考慮在 Scout 階段解析出真實 URL

---
*報告生成時間: 2025-12-02 21:00*
