#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InsightCosmos 生產模式執行腳本（含詳細日誌記錄）

此腳本會：
1. 執行完整的每日情報收集流程
2. 記錄詳細的資料來源資訊
3. 生成執行報告並保存到 docs/optimization/
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# 確保可以導入專案模組
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.orchestrator.daily_runner import DailyPipelineOrchestrator


def main():
    """主執行函數"""

    # 初始化
    print("=" * 80)
    print("InsightCosmos - 每日情報收集與分析 (生產模式)")
    print("=" * 80)
    print()

    # 載入配置
    print("📋 載入配置...")
    try:
        config = Config.from_env()
        print(f"✓ 配置載入成功")
        print(f"  使用者: {config.user_name}")
        print(f"  興趣領域: {config.user_interests}")
        print()
    except Exception as e:
        print(f"✗ 配置載入失敗: {e}")
        sys.exit(1)

    # 顯示資料來源資訊
    print("📡 資料來源配置:")
    print()
    print("  【RSS Feeds】")
    rss_feeds = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://spectrum.ieee.org/feeds/topic/robotics.rss",
        "https://www.therobotreport.com/feed/"
    ]
    for idx, feed in enumerate(rss_feeds, 1):
        print(f"    {idx}. {feed}")
    print(f"    → 每個 Feed 收集: 5 篇文章")
    print()

    print("  【Google Search Grounding】")
    interests = config.get_interests_list()
    print(f"    基於使用者興趣生成搜尋查詢: {', '.join(interests)}")
    print(f"    → 每個查詢收集: 5 篇文章")
    print()

    print("=" * 80)
    print()

    # 記錄開始時間
    start_time = datetime.now()
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")

    # 執行 Pipeline
    print("🚀 開始執行 Daily Pipeline...")
    print()

    try:
        orchestrator = DailyPipelineOrchestrator(config)
        result = orchestrator.run(dry_run=False)

        # 記錄結束時間
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 顯示執行結果
        print()
        print("=" * 80)
        print("執行結果摘要")
        print("=" * 80)

        if result["success"]:
            print("✓ Pipeline 執行成功")
        else:
            print("✗ Pipeline 執行失敗或部分失敗")

        print()
        print(f"執行時間: {duration:.1f} 秒")
        print(f"收集文章數: {result['stats']['phase1_collected']}")
        print(f"新存儲文章數: {result['stats']['phase1_stored']}")
        print(f"分析文章數: {result['stats']['phase2_analyzed']}")
        print(f"郵件發送: {'✓' if result['stats']['phase3_sent'] else '✗'}")

        if result['errors']:
            print(f"\n錯誤數量: {len(result['errors'])}")
            for error in result['errors']:
                print(f"  - {error['phase']}: {error['error_message']}")

        print()
        print("=" * 80)

        # 生成詳細報告
        report = generate_report(
            config=config,
            result=result,
            start_time=start_time,
            end_time=end_time,
            rss_feeds=rss_feeds
        )

        # 保存報告
        report_dir = Path("docs/optimization")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"production_run_{timestamp}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📄 執行報告已保存: {report_file}")

        # 保存 JSON 格式的詳細數據
        json_file = report_dir / f"production_run_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "execution_info": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration
                },
                "config": {
                    "user_name": config.user_name,
                    "user_interests": config.user_interests,
                    "interests_list": config.get_interests_list()
                },
                "data_sources": {
                    "rss_feeds": rss_feeds,
                    "rss_articles_per_feed": 5,
                    "google_search_queries": f"Generated based on: {config.user_interests}",
                    "google_search_results_per_query": 5
                },
                "result": result
            }, f, indent=2, ensure_ascii=False)

        print(f"📊 詳細數據已保存: {json_file}")
        print()

        # 退出碼
        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  執行被使用者中斷")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_report(config, result, start_time, end_time, rss_feeds):
    """生成 Markdown 格式的執行報告"""

    duration = (end_time - start_time).total_seconds()

    report = f"""# InsightCosmos 每日情報收集執行報告

**執行時間**: {start_time.strftime("%Y-%m-%d %H:%M:%S")} ~ {end_time.strftime("%H:%M:%S")}
**執行時長**: {duration:.1f} 秒
**執行模式**: 生產模式 (Production)
**執行狀態**: {'✅ 成功' if result['success'] else '❌ 失敗'}

---

## 📡 資料來源配置

### RSS Feeds

本次執行從以下 RSS 來源收集文章：

"""

    for idx, feed in enumerate(rss_feeds, 1):
        # 提取網站名稱
        if "techcrunch.com" in feed:
            source_name = "TechCrunch AI"
        elif "venturebeat.com" in feed:
            source_name = "VentureBeat AI"
        elif "spectrum.ieee.org" in feed:
            source_name = "IEEE Spectrum Robotics"
        elif "therobotreport.com" in feed:
            source_name = "The Robot Report"
        else:
            source_name = "Unknown"

        report += f"{idx}. **{source_name}**\n"
        report += f"   - URL: `{feed}`\n"
        report += f"   - 每次收集: 5 篇文章\n\n"

    report += f"""
**RSS 總計**: {len(rss_feeds)} 個來源，預期收集最多 {len(rss_feeds) * 5} 篇文章

### Google Search Grounding

基於使用者興趣自動生成搜尋查詢：

**使用者興趣**: {config.user_interests}

Scout Agent 會根據以下興趣領域生成搜尋查詢：
"""

    interests = config.get_interests_list()
    for interest in interests:
        report += f"- **{interest}**: 生成相關的最新資訊搜尋查詢\n"

    report += f"""
**搜尋策略**:
- 每個興趣領域至少生成 1 個搜尋查詢
- 每個查詢收集最多 5 篇文章
- 使用 Google Search Grounding API (透過 Gemini API)

---

## 📊 執行結果統計

### Phase 1: Scout Agent (資料收集)

| 指標 | 數值 |
|------|------|
| 收集文章總數 | {result['stats']['phase1_collected']} |
| 新存儲文章數 | {result['stats']['phase1_stored']} |
| 重複文章數 | {result['stats']['phase1_collected'] - result['stats']['phase1_stored']} |

### Phase 2: Analyst Agent (內容分析)

| 指標 | 數值 |
|------|------|
| 分析文章數 | {result['stats']['phase2_analyzed']} |
| 分析成功率 | {(result['stats']['phase2_analyzed'] / result['stats']['phase1_stored'] * 100) if result['stats']['phase1_stored'] > 0 else 0:.1f}% |

### Phase 3: Curator Agent (報告生成與發送)

| 指標 | 數值 |
|------|------|
| 郵件發送狀態 | {'✅ 成功' if result['stats']['phase3_sent'] else '❌ 失敗'} |
| 收件人 | {config.email_account} |

---

## ⚠️ 錯誤與警告

"""

    if result['errors']:
        report += f"**錯誤數量**: {len(result['errors'])}\n\n"
        for idx, error in enumerate(result['errors'], 1):
            report += f"### 錯誤 {idx}\n\n"
            report += f"- **階段**: {error['phase']}\n"
            report += f"- **類型**: {error['error_type']}\n"
            report += f"- **訊息**: {error['error_message']}\n"
            report += f"- **時間**: {error['timestamp']}\n\n"
    else:
        report += "**無錯誤** ✅\n\n"

    report += f"""
---

## 🎯 資料流程說明

### 完整 Pipeline 流程

```
1. Scout Agent (資料收集)
   ├─ RSS Fetcher
   │  └─ 從 {len(rss_feeds)} 個 RSS 來源收集文章
   │
   └─ Google Search Grounding
      └─ 基於 {len(interests)} 個興趣領域生成查詢並搜尋

2. Analyst Agent (內容分析)
   ├─ Content Extraction: 提取完整文章內容
   ├─ LLM Analysis: 使用 Gemini 2.5 Flash 分析
   └─ Embedding: 生成向量嵌入並存儲

3. Curator Agent (報告生成)
   ├─ Digest Formatting: 生成每日摘要
   └─ Email Delivery: 透過 SMTP 發送報告
```

### 資料去重機制

系統在以下階段執行去重：

1. **Scout Agent 內部**: 基於 URL 去重
2. **ArticleStore 存儲**: 檢查 URL 是否已存在於資料庫
3. **最終輸出**: 確保不會分析或發送重複內容

---

## 📝 備註

- 本報告由 `run_production_with_log.py` 自動生成
- 詳細日誌請查看系統日誌輸出
- JSON 格式的原始數據已同時保存

**生成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    return report


if __name__ == "__main__":
    main()
