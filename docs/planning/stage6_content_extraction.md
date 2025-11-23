# Stage 6: Content Extraction Tool

> **階段編號**: Stage 6
> **階段目標**: 實現文章內容提取工具，抓取 URL 完整正文
> **前置依賴**: Stage 5 完成（Scout Agent）
> **預計時間**: 1 天
> **狀態**: Planning

---

## 🎯 階段目標

### 核心目標

實現一個強大且可靠的 Content Extraction Tool，能夠從 URL 中提取高品質的文章內容，為 Analyst Agent 提供完整的分析素材。

這個工具將：
1. 從任意 URL 抓取 HTML 內容
2. 智能識別並提取文章主體內容
3. 清理無關元素（導航、廣告、側邊欄等）
4. 提取關鍵元數據（標題、作者、發布日期、圖片）
5. 提供結構化且一致的輸出格式

### 為什麼需要這個階段？

Scout Agent 收集的文章通常只包含標題和摘要，缺乏完整內容。Analyst Agent 需要完整的文章正文才能：
- 進行深度技術分析
- 識別關鍵洞察與趨勢
- 準確評估文章價值與優先度
- 提取具體的技術細節與數據

沒有高品質的內容提取，後續的分析與報告生成將受到嚴重限制。

---

## 📥 輸入 (Input)

### 來自上一階段的產出

- **Stage 5 (Scout Agent)**:
  - `raw_articles[]` - 文章列表，每篇包含 `url` 欄位
  - 示例: `[{"title": "...", "url": "https://...", "source": "..."}, ...]`

### 外部依賴

- **技術依賴**:
  - `trafilatura` - 主力內容提取套件（根據 Context7 查詢結果）
  - `beautifulsoup4` - HTML 解析（備用方案）
  - `requests` - HTTP 請求
  - `lxml` - XML/HTML 解析器（trafilatura 依賴）

- **配置依賴**:
  - （可選）`USER_AGENT` - 自定義 User-Agent 字串
  - （可選）`REQUEST_TIMEOUT` - HTTP 請求超時時間（預設 30 秒）
  - （可選）`MAX_RETRIES` - 最大重試次數（預設 3 次）

- **數據依賴**:
  - 測試 URL 列表（涵蓋不同網站類型）

---

## 📤 輸出 (Output)

### 代碼產出

```
src/
└─ tools/
    ├─ content_extractor.py  # 主要實現（NEW）
    └─ __init__.py           # 更新導出
tests/
└─ unit/
    └─ test_content_extractor.py  # 單元測試（NEW）
```

### 文檔產出

- `docs/implementation/stage6_notes.md` - 實作筆記
- `docs/validation/stage6_test_report.md` - 測試報告（可選）

### 功能產出

- [x] URL 內容抓取（HTTP GET）
- [x] HTML 解析與清理
- [x] 主體內容提取
- [x] 元數據提取（標題、作者、日期、圖片）
- [x] 錯誤處理與重試機制
- [x] 結構化輸出格式

---

## 🏗️ 技術設計

### 架構圖

```
Input: URL
    ↓
HTTP Request (requests)
    ↓
HTML Content
    ↓
Content Extraction (trafilatura)
    ↓
Metadata Extraction
    ↓
Output: Structured Article
```

### 核心組件

#### 組件 1: ContentExtractor 類

**職責**: 管理內容提取流程與配置

**類設計**:

```python
class ContentExtractor:
    """
    文章內容提取器

    使用 trafilatura 作為主力提取引擎，提供統一的接口。
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None
    ):
        """
        初始化提取器

        Args:
            timeout: HTTP 請求超時時間（秒）
            max_retries: 最大重試次數
            user_agent: 自定義 User-Agent（預設使用標準瀏覽器 UA）
        """
        pass

    def extract(self, url: str) -> dict:
        """
        從 URL 提取文章內容

        Args:
            url: 文章 URL

        Returns:
            dict: 結構化文章數據（見輸出格式）

        Raises:
            ValueError: URL 格式無效
            requests.RequestException: 網路請求失敗

        Example:
            >>> extractor = ContentExtractor()
            >>> article = extractor.extract("https://example.com/article")
            >>> print(article["title"])
            "Example Article Title"
        """
        pass

    def extract_batch(self, urls: List[str]) -> List[dict]:
        """
        批量提取多個 URL（順序執行）

        Args:
            urls: URL 列表

        Returns:
            List[dict]: 結構化文章列表（失敗的返回 error 狀態）
        """
        pass
```

**輸出格式**:

```python
{
    "status": "success" | "error",
    "url": "https://example.com/article",
    "title": "文章標題",
    "author": "作者名稱",           # 可能為 None
    "published_date": "2025-11-23", # ISO 格式，可能為 None
    "content": "完整正文內容...",   # 純文本，已清理 HTML
    "content_html": "<p>...</p>",   # 保留基本格式的 HTML（可選）
    "images": [                      # 主要圖片列表
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ],
    "word_count": 1234,              # 字數統計
    "language": "en",                # 語言代碼（可能為 None）
    "error_message": None,           # 錯誤時包含錯誤訊息
    "extraction_time": 1.23          # 提取耗時（秒）
}
```

**錯誤處理**:

| 錯誤類型 | 處理方式 | 返回信息 |
|---------|---------|---------|
| URL 無效 | 立即返回錯誤 | "Invalid URL format: {url}" |
| HTTP 404 | 立即返回錯誤 | "Page not found (404): {url}" |
| HTTP 403/401 | 立即返回錯誤 | "Access denied (403/401): {url}" |
| 連接超時 | 重試 3 次後返回錯誤 | "Connection timeout after {n} retries: {url}" |
| 內容提取失敗 | 嘗試備用方案（BeautifulSoup） | "Content extraction failed: {reason}" |
| 無可用內容 | 返回錯誤 | "No extractable content found: {url}" |

---

## 🔧 實作細節

### 步驟 1: HTTP 內容抓取

**目標**: 穩定可靠地抓取 HTML 內容

**實作要點**:
- 使用 `requests` 套件
- 設定合理的 User-Agent 避免被封鎖
- 實現重試機制（指數退避）
- 處理各種 HTTP 錯誤狀態碼
- 檢測並處理重定向

**代碼示例**:

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def _fetch_html(url: str, timeout: int = 30) -> str:
    """抓取 URL 的 HTML 內容"""

    # 配置重試策略
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,  # 1, 2, 4 秒
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = session.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text
```

### 步驟 2: 使用 Trafilatura 提取內容

**目標**: 智能提取文章主體與元數據

**實作要點**:
- 使用 `trafilatura.extract()` 提取主文本
- 使用 `trafilatura.extract_metadata()` 提取元數據
- 配置提取選項（包含格式、圖片等）
- 處理提取失敗情況

**代碼示例**:

```python
import trafilatura

def _extract_with_trafilatura(html: str, url: str) -> dict:
    """使用 trafilatura 提取內容"""

    # 提取主文本
    content = trafilatura.extract(
        html,
        include_images=True,
        include_links=False,
        output_format='txt',  # 或 'xml', 'json'
        url=url
    )

    # 提取元數據
    metadata = trafilatura.extract_metadata(html)

    if content is None:
        raise ValueError("No content extracted")

    return {
        "content": content,
        "title": metadata.title if metadata else None,
        "author": metadata.author if metadata else None,
        "published_date": metadata.date if metadata else None,
        "language": metadata.language if metadata else None
    }
```

### 步驟 3: 備用方案（BeautifulSoup）

**目標**: 當 trafilatura 失敗時提供備用提取方案

**實作要點**:
- 識別常見的內容標籤（article, main, .content, .post）
- 移除無關元素（nav, header, footer, aside, script, style）
- 提取純文本

**代碼示例**:

```python
from bs4 import BeautifulSoup

def _extract_with_beautifulsoup(html: str) -> dict:
    """使用 BeautifulSoup 作為備用方案"""

    soup = BeautifulSoup(html, 'lxml')

    # 移除無關元素
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()

    # 嘗試找到主內容區塊
    content_tag = (
        soup.find('article') or
        soup.find('main') or
        soup.find(class_=['content', 'post', 'article', 'entry-content'])
    )

    if content_tag:
        content = content_tag.get_text(separator='\n', strip=True)
    else:
        # 降級方案：提取 body
        content = soup.body.get_text(separator='\n', strip=True) if soup.body else ""

    # 提取標題
    title = soup.find('title')
    title_text = title.get_text(strip=True) if title else None

    return {
        "content": content,
        "title": title_text,
        "author": None,
        "published_date": None
    }
```

### 步驟 4: 整合與錯誤處理

**目標**: 組合各個組件，提供統一接口

**實作要點**:
- 實現主要的 `extract()` 方法
- 組合 HTTP 抓取與內容提取
- 統一錯誤處理
- 記錄提取時間

---

## 🧪 測試策略

### 單元測試

**測試文件**: `tests/unit/test_content_extractor.py`

**測試案例清單**:

| 測試案例 ID | 測試內容 | 輸入 | 期望輸出 | 優先級 |
|-----------|---------|------|---------|--------|
| TC-6-01 | 提取標準新聞文章 | TechCrunch URL | 成功提取標題、內容、作者 | High |
| TC-6-02 | 提取 Medium 文章 | Medium URL | 成功提取內容 | High |
| TC-6-03 | 處理 404 錯誤 | 不存在的 URL | status="error", 錯誤訊息 | High |
| TC-6-04 | 處理超時 | 模擬超時場景 | 重試 3 次後返回錯誤 | High |
| TC-6-05 | 提取純文本內容 | 任意 URL | content 欄位非空 | High |
| TC-6-06 | 提取元數據 | 包含 metadata 的頁面 | 正確提取 title, author, date | Medium |
| TC-6-07 | 處理無內容頁面 | 空白頁面 | status="error" | Medium |
| TC-6-08 | 批量提取 | 3 個 URL | 返回 3 個結果 | Medium |
| TC-6-09 | 處理無效 URL | "not-a-url" | ValueError | Low |
| TC-6-10 | 統計字數 | 任意文章 | word_count > 0 | Low |

**關鍵測試場景**:

1. **正常場景**: 提取標準新聞網站文章
   ```python
   def test_extract_standard_article():
       """測試提取標準新聞文章"""
       extractor = ContentExtractor()

       # 使用已知的穩定測試 URL
       url = "https://techcrunch.com/..."  # 實際測試時需要真實 URL
       result = extractor.extract(url)

       assert result["status"] == "success"
       assert result["title"] is not None
       assert len(result["content"]) > 100  # 至少 100 字元
       assert result["url"] == url
   ```

2. **邊界場景**: 處理空內容頁面
   ```python
   @patch('requests.Session.get')
   def test_extract_empty_page(mock_get):
       """測試處理無內容頁面"""
       mock_response = Mock()
       mock_response.text = "<html><body></body></html>"
       mock_response.status_code = 200
       mock_get.return_value = mock_response

       extractor = ContentExtractor()
       result = extractor.extract("https://example.com")

       assert result["status"] == "error"
       assert "No extractable content" in result["error_message"]
   ```

3. **異常場景**: 處理 HTTP 錯誤
   ```python
   @patch('requests.Session.get')
   def test_extract_http_404(mock_get):
       """測試處理 404 錯誤"""
       mock_get.side_effect = requests.HTTPError("404 Not Found")

       extractor = ContentExtractor()
       result = extractor.extract("https://example.com/not-found")

       assert result["status"] == "error"
       assert "404" in result["error_message"]
   ```

### 整合測試

**測試場景**: 與 Scout Agent 整合

測試從 Scout Agent 獲取文章列表，然後批量提取內容：

```python
def test_integration_with_scout():
    """測試與 Scout Agent 整合"""
    # 1. 模擬 Scout Agent 輸出
    articles = [
        {"title": "Article 1", "url": "https://example.com/1"},
        {"title": "Article 2", "url": "https://example.com/2"}
    ]

    # 2. 批量提取內容
    extractor = ContentExtractor()
    urls = [a["url"] for a in articles]
    results = extractor.extract_batch(urls)

    # 3. 驗證結果
    assert len(results) == 2
    for result in results:
        assert "content" in result
```

**測試數據**:

創建 `tests/fixtures/test_urls.json`：
```json
{
  "valid_urls": [
    "https://techcrunch.com/...",
    "https://medium.com/...",
    "https://github.com/..."
  ],
  "invalid_urls": [
    "https://example.com/404",
    "not-a-url",
    ""
  ]
}
```

---

## ✅ 驗收標準 (Acceptance Criteria)

### 功能驗收

- [x] 能成功提取標準新聞網站內容（TechCrunch, Medium 等）
- [x] 能提取基本元數據（標題、作者、日期）
- [x] 能處理 HTTP 錯誤（404, 403, 超時等）
- [x] 能處理無內容或提取失敗的情況
- [x] 批量提取功能正常工作

### 質量驗收

- [x] 單元測試通過率 = 100%
- [x] 代碼覆蓋率 >= 80%
- [x] 所有函數有完整 docstring
- [x] 所有函數有類型標註
- [x] 錯誤處理覆蓋主要場景

### 性能驗收

- [x] 單個 URL 提取時間 < 10 秒（95% 情況）
- [x] 重試機制不超過 30 秒總超時
- [x] 記憶體使用合理（< 100MB per extraction）

### 文檔驗收

- [x] 代碼註釋完整清晰
- [x] 實作筆記記錄關鍵決策
- [x] README 包含使用示例

---

## 🚧 風險與挑戰

### 已知風險

| 風險 | 影響 | 緩解方案 |
|------|------|---------|
| 網站反爬蟲機制 | 部分 URL 無法提取 | 使用合理的 User-Agent、請求延遲 |
| JavaScript 渲染頁面 | trafilatura 無法處理 | 記錄失敗 URL，Phase 2 考慮 Playwright |
| 內容格式多樣性 | 提取質量不一致 | 提供備用提取方案（BeautifulSoup） |
| 網路不穩定 | 提取失敗率高 | 實現重試機制與超時控制 |

### 技術挑戰

1. **挑戰 1**: 如何識別主體內容 vs 廣告／導航
   - **解決方案**: 依賴 trafilatura 的演算法，已針對新聞文章優化

2. **挑戰 2**: 如何處理不同網站的結構差異
   - **解決方案**: 使用通用提取演算法（trafilatura），避免針對特定網站的規則

3. **挑戰 3**: 如何平衡提取速度與準確性
   - **解決方案**: 提供可配置的超時與重試參數，允許根據場景調整

---

## 📚 參考資料

### 技術文檔

- [Trafilatura 官方文檔](https://trafilatura.readthedocs.io/) - 主力提取套件
- [BeautifulSoup 文檔](https://www.crummy.com/software/BeautifulSoup/) - 備用解析套件
- [Requests 文檔](https://docs.python-requests.org/) - HTTP 請求

### Context7 查詢結果

根據 Context7 MCP 查詢，獲取以下關鍵資訊：

**Trafilatura** (`/adbar/trafilatura`):
- 專為新聞文章與網頁內容提取設計
- 提供 `extract()` 和 `extract_metadata()` 兩個核心函數
- 支援多種輸出格式（txt, xml, json）
- Code Snippets: 25,379 個（文檔非常豐富）
- Benchmark Score: 72.8（高品質）

**BeautifulSoup4** (`/wention/beautifulsoup4`):
- 通用 HTML/XML 解析器
- 提供 `.get_text()` 方法提取文本
- 支援多種解析器（lxml, html.parser）
- Code Snippets: 176 個
- Benchmark Score: 97.9（非常成熟）

### 內部參考

- `docs/planning/stage3_rss_tool.md` - 類似的網路請求處理模式
- `CLAUDE.md` - 工具設計規範（Section: 程式碼編寫標準）

---

## 📝 開發清單 (Checklist)

### 規劃階段 ✓

- [x] 完成本規劃文檔
- [x] 使用 Context7 查詢技術方案
- [x] 評審通過

### 實作階段

- [ ] 安裝依賴套件（trafilatura, beautifulsoup4, lxml）
- [ ] 建立文件結構（content_extractor.py）
- [ ] 實現 ContentExtractor 類
- [ ] 實現 HTTP 抓取邏輯
- [ ] 實現 trafilatura 提取邏輯
- [ ] 實現 BeautifulSoup 備用方案
- [ ] 實現錯誤處理與重試
- [ ] 實現批量提取功能
- [ ] 編寫單元測試
- [ ] 代碼自測通過
- [ ] 更新 `dev_log.md`

### 驗證階段

- [ ] 單元測試全部通過
- [ ] 手動測試真實 URL（TechCrunch, Medium, GitHub）
- [ ] 整合測試與 Scout Agent
- [ ] 人工驗收提取內容品質
- [ ] 文檔更新完成

---

## 🎯 下一步行動

### 立即開始

1. 安裝必要的 Python 套件
2. 創建 `src/tools/content_extractor.py` 文件
3. 實現 `ContentExtractor` 類的基本框架
4. 實現 HTTP 抓取與 trafilatura 提取邏輯

### 準備工作

- 準備測試 URL 列表（至少 5 個不同來源）
- 確認虛擬環境已啟動
- 確認依賴套件可正常安裝

---

## 📊 時間分配

| 階段 | 預計時間 | 占比 |
|------|---------|------|
| 規劃 | 1.5 小時 | 20% |
| 實作 | 4.5 小時 | 60% |
| 驗證 | 1.5 小時 | 20% |
| **總計** | **7.5 小時** | **100%** |

---

**創建日期**: 2025-11-23
**最後更新**: 2025-11-23
**負責人**: Ray 張瑞涵
**狀態**: Planning → Implementation → Validation → Done
