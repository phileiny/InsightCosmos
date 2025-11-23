# Stage 3: RSS Fetcher Tool

> **階段編號**: Stage 3
> **階段目標**: 實作 RSS 文章抓取功能
> **前置依賴**: Stage 1 (Foundation), Stage 2 (Memory Layer)
> **預計時間**: 1 天 (6-8 小時)
> **狀態**: Planning

---

## 🎯 階段目標

### 核心目標

建立 RSS Feed 抓取工具，為 Scout Agent 提供文章收集能力：

1. 實作 RSS feed 解析功能
2. 提取文章元數據（標題、URL、摘要、發布時間）
3. 實作錯誤處理機制
4. 支援多個 RSS 來源批次抓取
5. 建立完整的測試覆蓋

### 為什麼需要這個階段？

RSS Fetcher 是 Scout Agent 的核心工具之一：
- **自動收集** - 定時從 RSS feeds 獲取最新文章
- **結構化數據** - 提供統一格式的文章資料
- **去重基礎** - 透過 URL 識別重複文章
- **時間追蹤** - 記錄文章發布與抓取時間
- **可靠性** - 處理網路錯誤與解析失敗

---

## 📥 輸入 (Input)

### 來自上一階段的產出

- Stage 1: Foundation
  - `src/utils/config.py` - 配置管理
  - `src/utils/logger.py` - 日誌系統

- Stage 2: Memory Layer
  - `src/memory/article_store.py` - 文章存儲（用於去重檢查）
  - `src/memory/models.py` - Article 模型定義

### 外部依賴

- **Python 套件**:
  - `feedparser>=6.0.10` - RSS/Atom feed 解析（已在 requirements.txt）
  - `requests>=2.31.0` - HTTP 請求（已在 requirements.txt）

- **RSS Feed 來源**（測試用）:
  - TechCrunch AI: `https://techcrunch.com/category/artificial-intelligence/feed/`
  - VentureBeat AI: `https://venturebeat.com/category/ai/feed/`

---

## 📤 輸出 (Output)

### 代碼產出

```
src/tools/
├── __init__.py           # 模組初始化
└── fetcher.py            # RSS Fetcher 工具
```

### 測試產出

```
tests/unit/
└── test_fetcher.py       # RSS Fetcher 單元測試
```

### 文檔產出

- `docs/implementation/stage3_notes.md` - Stage 3 實作筆記
- `docs/validation/stage3_test_report.md` - Stage 3 測試報告

### 功能產出

- [x] RSS feed 解析功能
- [x] 文章元數據提取
- [x] 錯誤處理（網路、解析、無效 URL）
- [x] 批次抓取支援
- [x] 超時控制
- [x] 結構化輸出

---

## 🏗️ 技術設計

### 架構圖

```
┌─────────────────────────────────────────────┐
│           Scout Agent (未來)                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│          RSS Fetcher Tool                   │
│                                             │
│  fetch_rss_feeds(feed_urls: List[str])     │
│         ↓                                   │
│  ┌──────────────────────┐                  │
│  │ 1. 驗證 URL          │                  │
│  │ 2. HTTP 請求         │                  │
│  │ 3. feedparser 解析   │                  │
│  │ 4. 元數據提取        │                  │
│  │ 5. 錯誤處理          │                  │
│  └──────────────────────┘                  │
│         ↓                                   │
│  return List[Article]                       │
└─────────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│         ArticleStore (Stage 2)              │
│         去重檢查、存儲                       │
└─────────────────────────────────────────────┘
```

---

## 🔧 核心組件設計

### RSS Fetcher (fetcher.py)

**職責**: RSS feed 抓取與解析

**接口設計**:

```python
from typing import List, Dict, Any, Optional
from datetime import datetime
import feedparser
import requests
from src.utils.logger import Logger


class RSSFetcher:
    """
    RSS Feed 抓取工具

    提供 RSS/Atom feed 的抓取與解析功能

    Attributes:
        timeout (int): HTTP 請求超時時間（秒）
        user_agent (str): HTTP User-Agent
        logger (Logger): 日誌記錄器

    Example:
        >>> fetcher = RSSFetcher(timeout=10)
        >>> articles = fetcher.fetch_rss_feeds([
        ...     'https://techcrunch.com/feed/'
        ... ])
        >>> print(f"Fetched {len(articles)} articles")
    """

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str = "InsightCosmos/1.0",
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化 RSS Fetcher

        Args:
            timeout: HTTP 請求超時時間（秒）
            user_agent: HTTP User-Agent 字符串
            logger: 日誌記錄器
        """
        pass

    def fetch_rss_feeds(
        self,
        feed_urls: List[str],
        max_articles_per_feed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批次抓取多個 RSS feeds

        Args:
            feed_urls: RSS feed URL 列表
            max_articles_per_feed: 每個 feed 最多返回文章數

        Returns:
            dict: {
                "status": "success" | "partial" | "error",
                "articles": List[Article],
                "errors": List[Error],
                "summary": {
                    "total_feeds": int,
                    "successful_feeds": int,
                    "failed_feeds": int,
                    "total_articles": int
                }
            }

        Example:
            >>> result = fetcher.fetch_rss_feeds([
            ...     'https://techcrunch.com/feed/',
            ...     'https://invalid-url.com/feed/'
            ... ])
            >>> print(result['summary'])
        """
        pass

    def fetch_single_feed(
        self,
        feed_url: str,
        max_articles: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        抓取單個 RSS feed

        Args:
            feed_url: RSS feed URL
            max_articles: 最多返回文章數

        Returns:
            dict: {
                "status": "success" | "error",
                "feed_url": str,
                "feed_title": str,
                "articles": List[Dict],
                "error_message": str (if error),
                "fetched_at": datetime
            }

        Raises:
            ValueError: 無效的 URL
            requests.RequestException: 網路請求失敗
            FeedParserError: Feed 解析失敗
        """
        pass

    def parse_feed_entry(
        self,
        entry: Any,
        feed_title: str,
        feed_url: str
    ) -> Dict[str, Any]:
        """
        解析單個 feed entry 為結構化文章數據

        Args:
            entry: feedparser entry 對象
            feed_title: Feed 標題
            feed_url: Feed URL

        Returns:
            dict: {
                "url": str,
                "title": str,
                "summary": str,
                "content": str,
                "published_at": datetime,
                "source": "rss",
                "source_name": str,
                "tags": List[str]
            }
        """
        pass

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        驗證 URL 格式

        Args:
            url: 要驗證的 URL

        Returns:
            bool: URL 是否有效
        """
        pass

    @staticmethod
    def parse_published_date(date_str: str) -> Optional[datetime]:
        """
        解析 RSS 發布時間

        支援多種日期格式：
        - RFC 2822 (e.g., 'Wed, 20 Nov 2024 10:00:00 GMT')
        - ISO 8601 (e.g., '2024-11-20T10:00:00Z')

        Args:
            date_str: 日期字符串

        Returns:
            Optional[datetime]: 解析後的日期時間，失敗返回 None
        """
        pass
```

---

## 🧪 測試策略

### 單元測試

**測試文件**: `tests/unit/test_fetcher.py`

**測試案例清單**:

| 測試案例 ID | 測試內容 | 輸入 | 期望輸出 | 優先級 |
|-----------|---------|------|---------|--------|
| TC-3-01 | RSSFetcher 初始化 | timeout=10 | RSSFetcher 物件 | High |
| TC-3-02 | 有效 URL 驗證 | https://example.com/feed | True | High |
| TC-3-03 | 無效 URL 驗證 | invalid-url | False | High |
| TC-3-04 | 單個 RSS feed 抓取（成功） | 有效 feed URL | 文章列表 | High |
| TC-3-05 | 單個 RSS feed 抓取（無效URL） | 無效 URL | error 狀態 | High |
| TC-3-06 | 批次抓取（全部成功） | 3 個有效 URLs | 所有文章 | High |
| TC-3-07 | 批次抓取（部分失敗） | 2 成功 + 1 失敗 | partial 狀態 | Medium |
| TC-3-08 | 文章數量限制 | max=5 | 最多 5 篇 | Medium |
| TC-3-09 | 解析 entry 元數據 | entry 對象 | 結構化數據 | High |
| TC-3-10 | 解析發布時間（RFC 2822） | RFC 2822 字串 | datetime | Medium |
| TC-3-11 | 解析發布時間（ISO 8601） | ISO 8601 字串 | datetime | Medium |
| TC-3-12 | 解析發布時間（無效格式） | 無效字串 | None | Low |

### Mock 策略

使用 `unittest.mock` 模擬外部依賴：

```python
from unittest.mock import Mock, patch

# Mock feedparser.parse
@patch('feedparser.parse')
def test_fetch_single_feed(mock_parse):
    mock_parse.return_value = {
        'feed': {'title': 'Test Feed'},
        'entries': [...]
    }
    # 測試邏輯
```

---

## ✅ 驗收標準 (Acceptance Criteria)

### 功能驗收

- [ ] 能成功解析有效的 RSS feed URL
- [ ] 能提取文章元數據：title, url, summary, published_at
- [ ] 能處理無效 URL（返回錯誤而非崩潰）
- [ ] 能處理網路超時（timeout 機制生效）
- [ ] 能處理 feed 解析失敗（malformed XML）
- [ ] 批次抓取返回正確的統計資訊
- [ ] 支援 max_articles_per_feed 限制
- [ ] 解析多種日期格式（RFC 2822, ISO 8601）

### 品質驗收

- [ ] 單元測試通過率 = 100% (至少 12 個測試案例)
- [ ] 程式碼覆蓋率 >= 85%
- [ ] 所有函數有完整 docstring
- [ ] 所有函數有型別標註
- [ ] 錯誤處理覆蓋主要場景
- [ ] 日誌記錄關鍵操作

### 效能驗收

- [ ] 單個 feed 抓取 < 5 秒（正常網路）
- [ ] 10 個 feeds 批次抓取 < 30 秒
- [ ] 超時機制正常工作（可配置）

### 文檔驗收

- [ ] 程式碼註釋完整清晰
- [ ] 創建 `stage3_notes.md` 記錄實作過程
- [ ] 創建 `stage3_test_report.md` 記錄測試結果
- [ ] 工具 docstring 包含使用範例

---

## 🚧 風險與挑戰

### 已知風險

| 風險 | 影響 | 緩解方案 |
|------|------|---------|
| RSS feed 格式多樣 | 中 - 部分 feed 解析失敗 | 使用成熟的 feedparser 庫，支援 RSS/Atom |
| 網路不穩定 | 中 - 抓取失敗率高 | 實作超時、重試機制 |
| 日期格式多樣 | 低 - 部分日期解析失敗 | 支援多種格式，失敗時返回 None |
| 編碼問題 | 低 - 亂碼或解析錯誤 | feedparser 自動處理編碼 |

### 技術挑戰

1. **挑戰**: 不同網站的 RSS feed 格式差異
   - **解決方案**: 使用 feedparser（支援 RSS 0.9, 1.0, 2.0 和 Atom）

2. **挑戰**: 網路請求失敗處理
   - **解決方案**:
     - 設定合理的 timeout（30 秒）
     - 捕獲 requests.RequestException
     - 記錄詳細錯誤信息

3. **挑戰**: 日期解析的多樣性
   - **解決方案**:
     - feedparser 自動處理 `published_parsed` 欄位
     - 手動解析 RFC 2822 和 ISO 8601
     - 解析失敗時使用當前時間

---

## 📊 數據結構定義

### Article 數據格式

```python
{
    "url": "https://example.com/article",
    "title": "Article Title",
    "summary": "Brief summary...",
    "content": "Full content...",  # 如果 RSS 包含
    "published_at": datetime(2024, 11, 20, 10, 0, 0),
    "source": "rss",
    "source_name": "TechCrunch",
    "tags": ["AI", "Tech"]  # 從 RSS categories 提取
}
```

### Feed Result 格式

```python
{
    "status": "success",  # success | partial | error
    "feed_url": "https://example.com/feed/",
    "feed_title": "Example Feed",
    "articles": [...],  # List of Article dicts
    "error_message": None,
    "fetched_at": datetime(2024, 11, 20, 10, 0, 0)
}
```

### Batch Result 格式

```python
{
    "status": "success",  # success | partial | error
    "articles": [...],  # All articles from all feeds
    "errors": [
        {
            "feed_url": "...",
            "error_type": "NetworkError",
            "error_message": "..."
        }
    ],
    "summary": {
        "total_feeds": 3,
        "successful_feeds": 2,
        "failed_feeds": 1,
        "total_articles": 45
    }
}
```

---

## 📚 參考資料

### 技術文檔

- [feedparser 文檔](https://feedparser.readthedocs.io/en/latest/)
- [RSS 2.0 規範](https://validator.w3.org/feed/docs/rss2.html)
- [Atom 規範](https://validator.w3.org/feed/docs/atom.html)
- [RFC 2822 日期格式](https://www.rfc-editor.org/rfc/rfc2822)

### 內部參考

- `CLAUDE.md` - 編碼規範
- `docs/planning/stage1_foundation.md` - Stage 1 規劃
- `docs/planning/stage2_memory.md` - Stage 2 規劃
- `docs/project_breakdown.md` - 整體規劃

---

## 📝 開發清單 (Checklist)

### 規劃階段 ✓

- [x] 完成本規劃文檔
- [x] API 接口設計完成
- [x] 測試案例規劃完成

### 實作階段

- [ ] 創建 `src/tools/__init__.py`
- [ ] 實作 `src/tools/fetcher.py`
  - [ ] RSSFetcher 類初始化
  - [ ] fetch_single_feed() 方法
  - [ ] fetch_rss_feeds() 批次抓取
  - [ ] parse_feed_entry() 解析
  - [ ] validate_url() URL 驗證
  - [ ] parse_published_date() 日期解析
- [ ] 編寫單元測試 `tests/unit/test_fetcher.py`
- [ ] 本地測試通過
- [ ] 更新 `docs/implementation/dev_log.md`

### 驗證階段

- [ ] 單元測試全部通過
- [ ] 手動測試真實 RSS feeds
- [ ] 效能基準測試
- [ ] 完成 `docs/validation/stage3_test_report.md`
- [ ] 完成 `docs/implementation/stage3_notes.md`

---

## 🎯 下一步行動

### 立即開始（實作階段）

1. 創建 `src/tools/` 目錄結構（5 分鐘）
2. 實作 RSSFetcher 類（90 分鐘）
   - 初始化與配置
   - URL 驗證
   - 單個 feed 抓取
   - 批次抓取
3. 實作輔助方法（60 分鐘）
   - parse_feed_entry()
   - parse_published_date()
4. 編寫單元測試（120 分鐘）
5. 驗證與文檔（60 分鐘）

### 準備工作

- 確認 feedparser 已安裝（在 requirements.txt 中）
- 確認 requests 已安裝（在 requirements.txt 中）
- 準備測試用的 RSS feed URLs

---

## 📊 時間分配

| 階段 | 預計時間 | 佔比 |
|------|---------|------|
| 規劃 | 1.0 小時 | 12.5% |
| 實作 | 5.5 小時 | 68.75% |
| 驗證 | 1.5 小時 | 18.75% |
| **總計** | **8.0 小時** | **100%** |

---

**創建日期**: 2025-11-21
**最後更新**: 2025-11-21
**負責人**: Ray 張瑞涵
**狀態**: Planning Complete → Ready for Implementation
