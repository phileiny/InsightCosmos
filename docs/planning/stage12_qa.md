# Stage 12: QA & Optimization (品質保證與優化)

> **建立日期**: 2025-11-25
> **預計時間**: 2 天
> **目標**: 完善測試、評估、效能優化與文檔

---

## 🎯 目標概述

Stage 12 是 Phase 1 的最終驗收階段，目標是：

1. **測試覆蓋率提升** - Daily Orchestrator 測試從 52.6% 提升到 90%+
2. **ADK Evaluation 配置** - 建立正式的評估框架
3. **效能優化** - 確保日報流程 < 5 分鐘完成
4. **文檔完善** - API 參考文件與測試結果報告

---

## 📋 任務清單

### 任務 1: 修正 Daily Orchestrator 測試 (52.6% → 90%+)

**問題分析**：
- 現有 19 個測試，10 個通過，9 個失敗
- 失敗原因：Mock 路徑不正確
  - 實際程式碼使用 lazy import（在方法內部 import）
  - 測試 Mock 路徑需要調整為 `src.agents.scout_agent.ScoutAgentRunner` 等

**修正方案**：
```python
# 錯誤方式（模組層級 Mock，但實際是 lazy import）
with patch("src.orchestrator.daily_runner.collect_articles") as mock:
    ...

# 正確方式（Mock 實際 import 的模組）
with patch("src.agents.scout_agent.ScoutAgentRunner") as mock_runner_class:
    ...
```

**需要修正的測試**：
- [ ] `test_run_phase1_scout_success`
- [ ] `test_run_phase1_scout_with_duplicates`
- [ ] `test_run_phase1_scout_failure`
- [ ] `test_run_phase2_analyst_success`
- [ ] `test_run_phase2_analyst_partial_failure`
- [ ] `test_run_phase3_curator_success`
- [ ] `test_run_phase3_curator_dry_run`
- [ ] `test_run_phase3_curator_failure`

**驗收標準**：
- 所有 19 個單元測試通過
- 測試覆蓋率 >= 90%

---

### 任務 2: ADK Evaluation 配置

**產出檔案**：
```
tests/
└─ evaluation/
    ├─ evalset.json          # 評估案例集
    └─ eval_config.json      # 評估配置
```

**評估案例設計**：

#### Scout Agent 評估
```json
{
  "eval_id": "scout_basic_collection",
  "description": "Scout Agent 基本收集功能",
  "conversation": [
    {
      "user_content": "收集今日 AI 和 Robotics 新聞",
      "expected_tools": ["fetch_rss", "search_articles"],
      "criteria": {
        "tool_trajectory_match": true,
        "min_articles": 10
      }
    }
  ]
}
```

#### Analyst Agent 評估
```json
{
  "eval_id": "analyst_quality_analysis",
  "description": "Analyst Agent 分析品質",
  "conversation": [
    {
      "user_content": "分析這篇文章並給出優先度評分",
      "criteria": {
        "has_summary": true,
        "has_key_insights": true,
        "has_priority_score": true,
        "priority_score_range": [0, 1]
      }
    }
  ]
}
```

#### Curator Agent 評估
```json
{
  "eval_id": "curator_daily_digest",
  "description": "Curator Agent 日報生成",
  "criteria": {
    "has_headline": true,
    "has_articles_section": true,
    "article_count_range": [5, 10]
  }
}
```

**評估配置**：
```json
{
  "evaluator": {
    "model": "gemini-2.5-flash",
    "criteria_model": "custom"
  },
  "thresholds": {
    "tool_trajectory_avg_score": 0.9,
    "response_match_score": 0.8
  }
}
```

---

### 任務 3: 效能優化與測試

**效能目標**：
| 指標 | 目標 | 說明 |
|------|------|------|
| Daily Pipeline | < 5 分鐘 | 包含 Scout + Analyst + Curator |
| Weekly Pipeline | < 2 分鐘 | 50+ 文章的週報生成 |
| 單文章分析 | < 15 秒 | LLM 分析 + Embedding |

**優化方向**：

1. **並發控制**
   - Analyst Agent 批量分析使用 Semaphore 控制
   - 建議並發數: 3-5

2. **資料庫查詢優化**
   - 確保索引正確建立
   - 批量操作而非單筆操作

3. **內容提取優化**
   - 設置合理的超時時間 (10 秒)
   - 失敗快速跳過

**效能測試腳本**：
```python
import time
from src.orchestrator.daily_runner import run_daily_pipeline

start = time.time()
result = run_daily_pipeline(dry_run=True)
duration = time.time() - start

print(f"Pipeline duration: {duration:.1f}s")
assert duration < 300, f"Pipeline too slow: {duration}s > 300s"
```

---

### 任務 4: API 參考文件

**產出檔案**: `docs/implementation/api_reference.md`

**文件結構**：
```markdown
# InsightCosmos API Reference

## Agents
### ScoutAgent
### AnalystAgent
### CuratorDailyAgent
### CuratorWeeklyAgent

## Tools
### RSSFetcher
### GoogleSearchGroundingTool
### ContentExtractor
### DigestFormatter
### EmailSender
### VectorClusteringTool
### TrendAnalysisTool

## Memory
### Database
### ArticleStore
### EmbeddingStore

## Orchestrator
### DailyPipelineOrchestrator
### WeeklyPipelineOrchestrator

## Utils
### Config
### Logger
```

---

### 任務 5: 測試結果報告

**產出檔案**: `docs/validation/test_results.md`

**報告內容**：
1. 測試統計總覽
2. 各模組測試覆蓋率
3. 整合測試結果
4. 效能測試結果
5. 已知問題與限制

---

## 📊 驗收標準

### 功能驗收
- [ ] 所有單元測試通過 (目標 239/239，實際 88% → 95%+)
- [ ] 所有整合測試通過
- [ ] ADK Evaluation 配置完成
- [ ] 效能符合目標 (Daily < 5 分鐘)

### 文檔驗收
- [ ] API 參考文件完成
- [ ] 測試結果報告完成
- [ ] PROGRESS.md 更新

### 品質指標
| 指標 | 目標 | 說明 |
|------|------|------|
| 單元測試通過率 | >= 95% | 239 個測試案例 |
| 整合測試通過率 | >= 90% | 端到端流程驗證 |
| 效能達標率 | 100% | Daily < 5 分鐘 |
| 文檔完整度 | 100% | API + 測試報告 |

---

## 🔧 實作順序

1. **Day 1 上午**: 修正 Daily Orchestrator 測試
2. **Day 1 下午**: 建立 ADK Evaluation 配置
3. **Day 2 上午**: 效能測試與優化
4. **Day 2 下午**: 完善文檔、更新 PROGRESS.md

---

## 📝 備註

### 現有測試統計
```
Utils              100% (14/14) ✅
Memory             100% (16/16) ✅
Tools/Search       100% (14/14) ✅
Tools/Extract      100% (24/24) ✅
Tools/Digest       100% (26/26) ✅
Tools/Email        100% (18/18) ✅
Agents/Scout       100% (20/20) ✅
Agents/Analyst     100% (22/22) ✅
Agents/Curator     93.8% (15/16) ✅
Orchestrator/Daily 52.6% (10/19) ⚠️ ← 需修正
Orchestrator/Weekly 100% (18/18) ✅
────────────────────────────────────
Total             88% (209/239)
```

### 測試修正策略
Daily Orchestrator 測試失敗的根本原因是 **lazy import**：
- 實際程式碼在方法內部 import（如 `_run_phase1_scout` 內 `from src.agents.scout_agent import ...`）
- 測試 Mock 需要 patch 實際被 import 的位置

### 參考資源
- [ADK Evaluation 文件](https://google.github.io/adk-docs/evaluate/)
- [pytest-cov 文件](https://pytest-cov.readthedocs.io/)

---

**維護者**: Ray 張瑞涵
**最後更新**: 2025-11-25
