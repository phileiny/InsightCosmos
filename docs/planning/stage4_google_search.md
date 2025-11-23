# Stage 4: Google Search Tool

> **階段編號**: Stage 4
> **階段目標**: 實作 Google Custom Search API 整合
> **前置依賴**: Stage 1 (Foundation), Stage 2 (Memory Layer), Stage 3 (RSS Tool)
> **預計時間**: 1 天 (6-8 小時)
> **狀態**: Planning

---

## 🎯 階段目標

### 核心目標

建立 Google Search 工具，為 Scout Agent 提供主動搜尋能力：

1. 實作 Google Custom Search API 整合
2. 關鍵字搜尋與結果解析
3. 配額管理與錯誤處理
4. 結構化輸出（與 RSS 格式一致）
5. 與 RSS 結果合併去重能力
6. 建立完整的測試覆蓋

### 為什麼需要這個階段？

Google Search Tool 是 Scout Agent 的第二個核心工具：

- **主動探索** - 不依賴 RSS feed，能搜尋最新關鍵字
- **補充來源** - RSS 可能遺漏的重要文章
- **靈活查詢** - 根據用戶興趣動態調整搜尋關鍵字
- **趨勢追蹤** - 搜尋特定主題的最新發展
- **去重整合** - 與 RSS 結果合併，避免重複

---

## 📥 輸入 (Input)

### 來自上一階段的產出

- Stage 1: Foundation
  - `src/utils/config.py` - 配置管理（需新增 Google API 配置）
  - `src/utils/logger.py` - 日誌系統

- Stage 2: Memory Layer
  - `src/memory/article_store.py` - 文章存儲（用於去重檢查）
  - `src/memory/models.py` - Article 模型定義

- Stage 3: RSS Tool
  - `src/tools/fetcher.py` - RSS 抓取（參考數據結構）

### 外部依賴

- **API 服務**:
  - Google Custom Search JSON API
  - 需要：
    - `GOOGLE_SEARCH_API_KEY` - API 金鑰
    - `GOOGLE_SEARCH_ENGINE_ID` - 自定義搜尋引擎 ID

- **Python 套件**:
  - `requests>=2.31.0` - HTTP 請求（已在 requirements.txt）
  - `urllib.parse` - URL 編碼（標準庫）

- **API 限制**:
  - 免費版：100 次/天
  - 每次請求最多 10 個結果
  - 需要 API Key 和 Search Engine ID

---

## 📤 輸出 (Output)

### 代碼產出

```
src/tools/
├── __init__.py           # 更新：加入 GoogleSearchTool
├── fetcher.py            # 已存在 (Stage 3)
└── google_search.py      # 新增：Google Search 工具
```

### 測試產出

```
tests/unit/
├── test_fetcher.py           # 已存在 (Stage 3)
└── test_google_search.py     # 新增：Google Search 測試

tests/
└── manual_test_google_search.py  # 新增：手動測試腳本
```

### 配置產出

```
.env.example              # 更新：加入 Google Search API 配置
```

### 文檔產出

- `docs/implementation/stage4_notes.md` - Stage 4 實作筆記
- `docs/validation/stage4_test_report.md` - Stage 4 測試報告

### 功能產出

- [x] Google Custom Search API 調用
- [x] 關鍵字搜尋功能
- [x] 搜尋結果解析與結構化
- [x] 配額管理（檢測 403 錯誤）
- [x] 錯誤處理（API 錯誤、網路錯誤）
- [x] 與 RSS 格式兼容的輸出
- [x] 結果去重（URL based）

---

## 🏗️ 技術設計

### 架構圖

```
┌─────────────────────────────────────────────┐
│           Scout Agent (未來)                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│        Google Search Tool                   │
│                                             │
│  search_articles(query: str, max_results)  │
│         ↓                                   │
│  ┌──────────────────────┐                  │
│  │ 1. 構建 API 請求     │                  │
│  │ 2. 檢查配額          │                  │
│  │ 3. 調用 Google API   │                  │
│  │ 4. 解析搜尋結果      │                  │
│  │ 5. 結構化輸出        │                  │
│  │ 6. 錯誤處理          │                  │
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

### Google Custom Search API

**API 端點**:
```
GET https://www.googleapis.com/customsearch/v1
```

**請求參數**:
```python
params = {
    'key': GOOGLE_SEARCH_API_KEY,      # API 金鑰
    'cx': GOOGLE_SEARCH_ENGINE_ID,     # 搜尋引擎 ID
    'q': query,                         # 搜尋關鍵字
    'num': max_results,                 # 結果數量（1-10）
    'dateRestrict': 'd7',              # 限制時間範圍（7天內）
    'lr': 'lang_en',                    # 語言限制（英文）
}
```

**回應格式**:
```json
{
  "items": [
    {
      "title": "Article Title",
      "link": "https://example.com/article",
      "snippet": "Brief description...",
      "pagemap": {
        "metatags": [{
          "og:description": "Full description..."
        }]
      }
    }
  ],
  "searchInformation": {
    "totalResults": "1000"
  }
}
```

---

## 🔧 核心組件設計

### GoogleSearchTool (google_search.py)

**職責**: Google Custom Search API 調用與結果解析

**接口設計**:

```python
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from urllib.parse import quote_plus
from src.utils.logger import Logger
from src.utils.config import Config


class GoogleSearchTool:
    """
    Google Custom Search API 工具

    提供關鍵字搜尋與結果結構化功能

    Attributes:
        api_key (str): Google Search API 金鑰
        engine_id (str): Custom Search Engine ID
        timeout (int): HTTP 請求超時時間（秒）
        logger (Logger): 日誌記錄器

    Example:
        >>> search_tool = GoogleSearchTool(
        ...     api_key="YOUR_API_KEY",
        ...     engine_id="YOUR_ENGINE_ID"
        ... )
        >>> articles = search_tool.search_articles(
        ...     query="AI robotics",
        ...     max_results=10
        ... )
        >>> print(f"Found {len(articles)} articles")
    """

    API_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        engine_id: Optional[str] = None,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化 Google Search Tool

        Args:
            api_key: Google Search API 金鑰（None 則從 Config 讀取）
            engine_id: Custom Search Engine ID（None 則從 Config 讀取）
            timeout: HTTP 請求超時時間（秒）
            logger: 日誌記錄器（None 則創建新的）

        Raises:
            ValueError: API Key 或 Engine ID 缺失
        """
        pass

    def search_articles(
        self,
        query: str,
        max_results: int = 10,
        date_restrict: str = 'd7',
        language: str = 'lang_en'
    ) -> Dict[str, Any]:
        """
        搜尋文章並返回結構化結果

        Args:
            query: 搜尋關鍵字
            max_results: 最多返回結果數（1-10）
            date_restrict: 時間限制（d7=最近7天, w1=最近1週, m1=最近1月）
            language: 語言限制（lang_en, lang_zh-TW）

        Returns:
            dict: {
                "status": "success" | "error",
                "query": str,
                "articles": List[Dict],
                "total_results": int,
                "error_message": str (if error),
                "quota_exceeded": bool,
                "searched_at": datetime
            }

        Example:
            >>> result = search_tool.search_articles(
            ...     query="multi-agent AI systems",
            ...     max_results=5,
            ...     date_restrict='d3'
            ... )
            >>> print(result['total_results'])
        """
        pass

    def batch_search(
        self,
        queries: List[str],
        max_results_per_query: int = 10
    ) -> Dict[str, Any]:
        """
        批次搜尋多個關鍵字

        Args:
            queries: 搜尋關鍵字列表
            max_results_per_query: 每個關鍵字最多返回結果數

        Returns:
            dict: {
                "status": "success" | "partial" | "error",
                "articles": List[Dict],  # 所有文章合併
                "errors": List[Dict],
                "summary": {
                    "total_queries": int,
                    "successful_queries": int,
                    "failed_queries": int,
                    "total_articles": int,
                    "quota_exceeded": bool
                }
            }

        Example:
            >>> result = search_tool.batch_search([
            ...     "AI agents",
            ...     "robotics news",
            ...     "multi-agent systems"
            ... ], max_results_per_query=5)
            >>> print(result['summary'])
        """
        pass

    def parse_search_result(
        self,
        item: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        解析單個搜尋結果為結構化文章數據

        Args:
            item: Google Search API 返回的單個 item
            query: 原始搜尋關鍵字

        Returns:
            dict: {
                "url": str,
                "title": str,
                "summary": str,
                "content": str,  # 從 snippet 提取
                "published_at": datetime,  # 使用當前時間
                "source": "google_search",
                "source_name": str,  # 從 URL 提取 domain
                "tags": List[str],  # 從 query 提取
                "search_query": str  # 記錄搜尋關鍵字
            }

        Example:
            >>> item = {"title": "...", "link": "...", "snippet": "..."}
            >>> article = search_tool.parse_search_result(item, "AI news")
            >>> print(article['source'])
            'google_search'
        """
        pass

    def build_api_url(
        self,
        query: str,
        max_results: int,
        date_restrict: str,
        language: str
    ) -> str:
        """
        構建 Google Search API 請求 URL

        Args:
            query: 搜尋關鍵字
            max_results: 結果數量
            date_restrict: 時間限制
            language: 語言限制

        Returns:
            str: 完整的 API 請求 URL

        Example:
            >>> url = search_tool.build_api_url(
            ...     query="AI news",
            ...     max_results=10,
            ...     date_restrict='d7',
            ...     language='lang_en'
            ... )
            >>> 'q=AI+news' in url
            True
        """
        pass

    @staticmethod
    def extract_domain(url: str) -> str:
        """
        從 URL 提取域名作為來源名稱

        Args:
            url: 文章 URL

        Returns:
            str: 域名（去除 www.）

        Example:
            >>> GoogleSearchTool.extract_domain("https://www.example.com/article")
            'example.com'
        """
        pass

    @staticmethod
    def is_quota_exceeded(error_response: Dict[str, Any]) -> bool:
        """
        檢查錯誤是否為配額超限

        Args:
            error_response: API 錯誤回應

        Returns:
            bool: 是否為配額超限錯誤

        Example:
            >>> error = {"error": {"code": 429, "message": "Quota exceeded"}}
            >>> GoogleSearchTool.is_quota_exceeded(error)
            True
        """
        pass

    def validate_api_credentials(self) -> bool:
        """
        驗證 API 憑證是否有效

        Returns:
            bool: 憑證是否有效

        Example:
            >>> search_tool.validate_api_credentials()
            True
        """
        pass
```

---

## 🧪 測試策略

### 單元測試

**測試文件**: `tests/unit/test_google_search.py`

**測試案例清單**:

| 測試案例 ID | 測試內容 | 輸入 | 期望輸出 | 優先級 |
|-----------|---------|------|---------|--------|
| TC-4-01 | GoogleSearchTool 初始化（有憑證） | api_key, engine_id | GoogleSearchTool 物件 | High |
| TC-4-02 | GoogleSearchTool 初始化（無憑證） | None | ValueError | High |
| TC-4-03 | 構建 API URL | query="AI" | 包含正確參數的 URL | High |
| TC-4-04 | 單次搜尋（成功） | "AI news" | 文章列表 | High |
| TC-4-05 | 單次搜尋（API 錯誤） | Mock 403 | error 狀態 + quota_exceeded=True | High |
| TC-4-06 | 單次搜尋（網路錯誤） | Mock timeout | error 狀態 | Medium |
| TC-4-07 | 批次搜尋（全部成功） | 3 個關鍵字 | 所有文章合併 | High |
| TC-4-08 | 批次搜尋（部分失敗） | 2 成功 + 1 失敗 | partial 狀態 | Medium |
| TC-4-09 | 解析搜尋結果 | API item 對象 | 結構化文章數據 | High |
| TC-4-10 | 提取域名 | https://www.example.com/path | example.com | Medium |
| TC-4-11 | 檢測配額超限（True） | 403 錯誤 | True | High |
| TC-4-12 | 檢測配額超限（False） | 其他錯誤 | False | Medium |
| TC-4-13 | 驗證 API 憑證（有效） | 有效憑證 | True | Medium |
| TC-4-14 | 驗證 API 憑證（無效） | 無效憑證 | False | Medium |
| TC-4-15 | max_results 範圍檢查 | max_results=15 | 自動調整為 10 | Low |
| TC-4-16 | 空搜尋結果處理 | query 無結果 | articles=[] | Medium |

### Mock 策略

使用 `unittest.mock` 模擬 API 調用：

```python
from unittest.mock import Mock, patch

# Mock requests.get
@patch('requests.get')
def test_search_articles(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'items': [
            {
                'title': 'Test Article',
                'link': 'https://example.com/article',
                'snippet': 'Test snippet'
            }
        ],
        'searchInformation': {'totalResults': '1'}
    }
    mock_get.return_value = mock_response
    # 測試邏輯
```

### 手動測試腳本

**測試文件**: `tests/manual_test_google_search.py`

```python
"""
Google Search Tool 手動測試腳本

測試真實 API 調用功能
"""

from src.tools.google_search import GoogleSearchTool
from src.utils.logger import Logger
import json

def test_real_search():
    """測試真實的 Google Search API"""
    logger = Logger.get_logger("manual_test")
    search_tool = GoogleSearchTool()

    # 測試 1: 單次搜尋
    logger.info("=== 測試 1: 單次搜尋 ===")
    result = search_tool.search_articles(
        query="AI multi-agent systems",
        max_results=5,
        date_restrict='d7'
    )
    logger.info(f"狀態: {result['status']}")
    logger.info(f"找到 {len(result['articles'])} 篇文章")

    # 測試 2: 批次搜尋
    logger.info("\n=== 測試 2: 批次搜尋 ===")
    batch_result = search_tool.batch_search(
        queries=["AI agents", "robotics news"],
        max_results_per_query=3
    )
    logger.info(f"總共找到 {batch_result['summary']['total_articles']} 篇文章")

if __name__ == "__main__":
    test_real_search()
```

---

## ✅ 驗收標準 (Acceptance Criteria)

### 功能驗收

- [ ] 能成功調用 Google Custom Search API
- [ ] 能解析 API 回應並提取文章資訊
- [ ] 能處理配額超限錯誤（403 Forbidden）
- [ ] 能處理網路錯誤（timeout, connection error）
- [ ] 能處理 API 錯誤（invalid key, invalid engine ID）
- [ ] 批次搜尋能正確合併結果
- [ ] max_results 參數能限制結果數量（1-10）
- [ ] 輸出格式與 RSS 工具一致（可合併去重）
- [ ] 能提取域名作為 source_name

### 品質驗收

- [ ] 單元測試通過率 = 100% (至少 16 個測試案例)
- [ ] 程式碼覆蓋率 >= 85%
- [ ] 所有函數有完整 docstring
- [ ] 所有函數有型別標註
- [ ] 錯誤處理覆蓋主要場景
- [ ] 日誌記錄關鍵操作

### 效能驗收

- [ ] 單次搜尋 < 3 秒（正常網路）
- [ ] 批次搜尋（3 個關鍵字）< 10 秒
- [ ] 超時機制正常工作（可配置）

### 文檔驗收

- [ ] 程式碼註釋完整清晰
- [ ] 創建 `stage4_notes.md` 記錄實作過程
- [ ] 創建 `stage4_test_report.md` 記錄測試結果
- [ ] 工具 docstring 包含使用範例
- [ ] 更新 `.env.example` 包含 Google API 配置

---

## 🚧 風險與挑戰

### 已知風險

| 風險 | 影響 | 緩解方案 |
|------|------|---------|
| API 配額限制（100次/天） | 高 - 測試與開發受限 | 實作配額檢測、Mock 測試為主、手動測試謹慎使用 |
| API 金鑰洩露 | 高 - 安全風險 | 使用 .env 檔案、加入 .gitignore、文檔強調安全 |
| 搜尋結果質量不佳 | 中 - 文章相關性低 | 優化搜尋關鍵字、使用 dateRestrict 限制時間 |
| 網路不穩定 | 中 - API 調用失敗 | 實作超時、重試機制、詳細錯誤日誌 |

### 技術挑戰

1. **挑戰**: API 配額管理
   - **解決方案**:
     - 檢測 403 錯誤並設置 `quota_exceeded` 標誌
     - 日誌記錄每次 API 調用
     - 提供友好的錯誤提示

2. **挑戰**: 搜尋結果缺少發布時間
   - **解決方案**:
     - 使用當前時間作為 `published_at`
     - 記錄 `searched_at` 作為獲取時間
     - 文檔說明此限制

3. **挑戰**: 與 RSS 結果格式統一
   - **解決方案**:
     - 參考 RSSFetcher 的輸出格式
     - 使用相同的 Article 數據結構
     - 添加 `source` 欄位區分來源（"rss" vs "google_search"）

4. **挑戰**: 搜尋關鍵字優化
   - **解決方案**:
     - Phase 1 使用固定關鍵字（從 Config 讀取）
     - Phase 2 由 Scout Agent 動態生成
     - 支援 date_restrict 參數控制時間範圍

---

## 📊 數據結構定義

### Article 數據格式（與 RSS 一致）

```python
{
    "url": "https://example.com/article",
    "title": "Article Title",
    "summary": "Brief summary from snippet...",
    "content": "Full snippet content...",
    "published_at": datetime.now(),  # 使用搜尋時間
    "source": "google_search",  # 區分來源
    "source_name": "example.com",  # 從 URL 提取域名
    "tags": ["AI", "robotics"],  # 從搜尋關鍵字提取
    "search_query": "AI robotics"  # 記錄搜尋關鍵字
}
```

### Search Result 格式

```python
{
    "status": "success",  # success | error
    "query": "AI robotics",
    "articles": [...],  # List of Article dicts
    "total_results": 1000,  # 總搜尋結果數（API 提供）
    "error_message": None,
    "quota_exceeded": False,
    "searched_at": datetime.now()
}
```

### Batch Search Result 格式

```python
{
    "status": "success",  # success | partial | error
    "articles": [...],  # 所有文章合併（去重）
    "errors": [
        {
            "query": "...",
            "error_type": "QuotaExceeded",
            "error_message": "..."
        }
    ],
    "summary": {
        "total_queries": 3,
        "successful_queries": 2,
        "failed_queries": 1,
        "total_articles": 15,
        "quota_exceeded": True
    }
}
```

---

## 📚 參考資料

### API 文檔

- [Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview)
- [API 參數說明](https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list)
- [創建自定義搜尋引擎](https://programmablesearchengine.google.com/about/)
- [API Key 取得](https://console.cloud.google.com/apis/credentials)

### 內部參考

- `CLAUDE.md` - 編碼規範
- `docs/planning/stage3_rss_tool.md` - RSS Tool 規劃（參考數據結構）
- `src/tools/fetcher.py` - RSS Fetcher 實作（參考格式）
- `docs/project_breakdown.md` - 整體規劃

---

## 📝 開發清單 (Checklist)

### 規劃階段 ✓

- [x] 完成本規劃文檔
- [x] API 接口設計完成
- [x] 測試案例規劃完成

### 實作階段

- [ ] 更新 `src/tools/__init__.py`（加入 GoogleSearchTool）
- [ ] 更新 `.env.example`（加入 Google API 配置）
- [ ] 實作 `src/tools/google_search.py`
  - [ ] GoogleSearchTool 類初始化
  - [ ] build_api_url() 方法
  - [ ] search_articles() 單次搜尋
  - [ ] batch_search() 批次搜尋
  - [ ] parse_search_result() 解析結果
  - [ ] extract_domain() 提取域名
  - [ ] is_quota_exceeded() 配額檢測
  - [ ] validate_api_credentials() 憑證驗證
- [ ] 編寫單元測試 `tests/unit/test_google_search.py`
- [ ] 編寫手動測試 `tests/manual_test_google_search.py`
- [ ] 本地測試通過
- [ ] 更新 `docs/implementation/dev_log.md`

### 驗證階段

- [ ] 單元測試全部通過
- [ ] 手動測試真實 API（謹慎使用配額）
- [ ] 與 RSS 結果格式兼容性測試
- [ ] 完成 `docs/validation/stage4_test_report.md`
- [ ] 完成 `docs/implementation/stage4_notes.md`

---

## 🎯 下一步行動

### 立即開始（實作階段）

1. **設置 Google API**（30 分鐘）
   - 註冊 Google Cloud Console
   - 創建 API Key
   - 設置 Custom Search Engine
   - 配置 `.env` 檔案

2. **實作 GoogleSearchTool 類**（120 分鐘）
   - 初始化與配置
   - build_api_url() 方法
   - search_articles() 核心搜尋
   - parse_search_result() 解析

3. **實作批次搜尋**（60 分鐘）
   - batch_search() 方法
   - 錯誤處理與合併邏輯

4. **實作輔助方法**（45 分鐘）
   - extract_domain()
   - is_quota_exceeded()
   - validate_api_credentials()

5. **編寫測試**（150 分鐘）
   - 16 個單元測試案例
   - 手動測試腳本

6. **驗證與文檔**（60 分鐘）

### 準備工作

- [ ] 註冊 Google Cloud Console 帳號
- [ ] 創建 Custom Search Engine
- [ ] 取得 API Key 和 Engine ID
- [ ] 測試 API 調用（使用 curl 或 Postman）

### Google API 設置步驟

1. **創建 API Key**:
   - 前往 https://console.cloud.google.com/apis/credentials
   - 點擊「CREATE CREDENTIALS」→「API key」
   - 複製 API Key

2. **創建 Custom Search Engine**:
   - 前往 https://programmablesearchengine.google.com/
   - 點擊「Add」創建新的搜尋引擎
   - 設置搜尋範圍（整個網路）
   - 複製 Search Engine ID

3. **配置 .env**:
   ```bash
   GOOGLE_SEARCH_API_KEY=your_api_key_here
   GOOGLE_SEARCH_ENGINE_ID=your_engine_id_here
   ```

---

## 📊 時間分配

| 階段 | 預計時間 | 佔比 |
|------|---------|------|
| 規劃 | 1.0 小時 | 12.5% |
| API 設置 | 0.5 小時 | 6.25% |
| 實作 | 5.0 小時 | 62.5% |
| 驗證 | 1.5 小時 | 18.75% |
| **總計** | **8.0 小時** | **100%** |

---

## 🔐 安全注意事項

### API Key 安全

1. **絕對不要**:
   - ❌ 將 API Key 提交到 Git
   - ❌ 在程式碼中硬編碼 API Key
   - ❌ 在公開平台分享 API Key

2. **必須做**:
   - ✅ 使用 `.env` 檔案存儲
   - ✅ 將 `.env` 加入 `.gitignore`
   - ✅ 使用 `.env.example` 作為模板（不含真實金鑰）
   - ✅ 定期更換 API Key
   - ✅ 設置 API Key 使用限制（Google Cloud Console）

---

## 📈 成功指標

### Stage 4 完成標準

- [ ] Google Search API 整合成功
- [ ] 能搜尋並返回結構化文章（與 RSS 格式一致）
- [ ] 配額管理機制正常運作
- [ ] 所有測試通過（100% 通過率）
- [ ] 文檔完整（規劃、實作、驗證）
- [ ] 代碼質量符合規範（docstring, type hints, logging）

### 與 Stage 5 的銜接

Stage 4 完成後，Scout Agent (Stage 5) 將能夠：
- 同時使用 RSS Tool 和 Google Search Tool
- 合併兩種來源的文章並去重
- 根據關鍵字動態搜尋補充內容

---

**創建日期**: 2025-11-21
**最後更新**: 2025-11-21
**負責人**: Ray 張瑞涵
**狀態**: Planning Complete → Ready for Implementation
