# Stage 8: Curator Daily Agent - 規劃文件

> **階段**: Phase 1 - Stage 8/12
> **目標**: 實現每日情報摘要生成與 Email 發送
> **預計時間**: 1.5 天
> **創建日期**: 2025-11-24
> **負責人**: Ray 張瑞涵

---

## 📋 目錄

1. [目標說明](#目標說明)
2. [輸入/輸出定義](#輸入輸出定義)
3. [技術設計](#技術設計)
4. [Curator Daily Agent 設計](#curator-daily-agent-設計)
5. [Email Sender 工具設計](#email-sender-工具設計)
6. [報告格式設計](#報告格式設計)
7. [實作計劃](#實作計劃)
8. [測試策略](#測試策略)
9. [驗收標準](#驗收標準)
10. [風險與對策](#風險與對策)

---

## 🎯 目標說明

### 核心目標

實現 **Curator Daily Agent**，負責從已分析的文章中篩選出高優先度內容，生成結構化的每日情報摘要，並透過 Email 發送給使用者。

### 具體功能

1. **文章篩選**
   - 從 Memory 中取得當日已分析的文章
   - 依據 priority_score 排序
   - 篩選出 Top 5-10 篇文章

2. **報告生成**
   - 使用 LLM 整合文章內容
   - 生成結構化的 Daily Digest
   - 支援 HTML 與純文字兩種格式

3. **Email 發送**
   - 支援 HTML Email（主要格式）
   - 支援純文字 Email（備用格式）
   - SMTP 發送到指定信箱
   - 錯誤處理與重試機制

### 與其他模組的關係

```
┌────────────────────────────────────────────────────┐
│               Curator Daily Agent                  │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │ 1. 查詢 ArticleStore                     │    │
│  │    → get_top_priority(status="analyzed") │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 2. LLM 整合與報告生成                     │    │
│  │    → Gemini 2.5 Flash                    │    │
│  │    → HTML + Text 格式                     │    │
│  └──────────────────────────────────────────┘    │
│                     ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 3. Email 發送                             │    │
│  │    → SMTP (Gmail)                        │    │
│  │    → HTML with fallback to Text          │    │
│  └──────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

---

## 📥 輸入/輸出定義

### 輸入

**來源**: `ArticleStore.get_top_priority()`

**數據結構**:
```python
[
    {
        "id": 1,
        "title": "文章標題",
        "url": "https://example.com/article",
        "summary": "文章摘要（LLM 生成）",
        "key_insights": ["洞察1", "洞察2", "洞察3"],
        "priority_score": 0.92,
        "priority_reasoning": "為何重要的理由",
        "tags": "AI,Robotics",
        "published_at": "2025-11-24T10:00:00Z",
        "source_name": "TechCrunch"
    },
    # ... 5-10 篇文章
]
```

### 輸出

**1. Daily Digest 結構化數據**:
```python
{
    "date": "2025-11-24",
    "total_articles": 8,
    "top_articles": [
        {
            "title": "文章標題",
            "url": "https://...",
            "summary": "精簡摘要（1-2 句）",
            "key_takeaway": "核心要點",
            "priority_score": 0.92,
            "tags": ["AI", "Robotics"]
        },
        # ...
    ],
    "daily_insight": "今日趨勢總結（2-3 句）",
    "recommended_action": "建議行動（可選）"
}
```

**2. HTML Email**:
- 美觀的排版
- 可點擊的連結
- 標籤與優先度視覺化
- 響應式設計（支援行動裝置）

**3. 純文字 Email**:
- 清晰的結構
- 易於閱讀
- 適合純文字客戶端

### 副作用

1. **Email 發送記錄**: 記錄到日誌中
2. **發送狀態更新**: 可選（未來可追蹤）

---

## 🏗️ 技術設計

### 整體架構

```
CuratorDailyAgent (LlmAgent)
    ↓
CuratorDailyRunner
    │
    ├─ Step 1: fetch_analyzed_articles()
    │   └─ ArticleStore.get_top_priority()
    │
    ├─ Step 2: generate_digest()
    │   └─ LLM (Gemini 2.5 Flash)
    │       ├─ 輸入: 文章列表 + Daily Prompt
    │       └─ 輸出: Structured Digest JSON
    │
    ├─ Step 3: format_digest()
    │   ├─ format_html()  → HTML Email
    │   └─ format_text()  → Plain Text Email
    │
    └─ Step 4: send_email()
        └─ EmailSender.send()
```

### 技術選型

| 元件 | 技術選擇 | 理由 |
|------|---------|------|
| **LLM** | Gemini 2.5 Flash | 效率高、成本低、品質穩定 |
| **Email Protocol** | SMTP | 標準協議、Gmail 支援 |
| **Email Library** | `smtplib` (標準庫) | 無額外依賴、穩定可靠 |
| **HTML Template** | f-string | 簡單直接、無需額外套件 |
| **Email Format** | `email.mime` (標準庫) | 支援 HTML + Text multipart |

### 關鍵決策

#### 決策 1: Curator Agent 不使用 Tools

**背景**: Curator Agent 主要負責整合與格式化，不需要外部工具。

**方案**:
- Curator Agent 本身**不使用工具**
- 僅使用 LLM 進行內容整合與洞察提取
- Runner 負責調用 ArticleStore 與 EmailSender

**權衡**:
- ✅ 簡化 Agent 設計，專注於內容生成
- ✅ 提高 LLM 品質（減少工具調用錯誤）
- ✅ 降低 token 消耗
- ❌ Agent 本身無法直接查詢數據（但不需要）

#### 決策 2: 雙格式 Email（HTML + Text）

**背景**: 不同 Email 客戶端支援度不同。

**方案**:
- 使用 `multipart/alternative` 格式
- HTML 為主要格式（美觀）
- 純文字為備用格式（相容性）

**權衡**:
- ✅ 最大化相容性
- ✅ 優化閱讀體驗
- ❌ 需要維護兩套模板（可接受）

#### 決策 3: 文章數量上限 10 篇

**背景**: 日報需要精簡，避免資訊過載。

**方案**:
- 預設篩選 Top 10 篇文章
- 可透過參數調整（5-15 篇）
- LLM 再進一步精選核心內容

**權衡**:
- ✅ 精簡易讀
- ✅ 降低 Email 大小
- ❌ 可能遺漏部分內容（可接受）

#### 決策 4: SMTP 而非 Gmail API

**背景**: 需要選擇 Email 發送方式。

**方案**: 使用 SMTP 協議（Gmail SMTP）

**權衡**:
- ✅ 實作簡單、無需 OAuth
- ✅ 支援所有 SMTP 服務（不限 Gmail）
- ✅ 適合個人使用（Phase 1）
- ❌ 需要應用程式專用密碼
- ❌ 有每日發送限制（500 封/天，足夠個人使用）

---

## 🤖 Curator Daily Agent 設計

### Agent 配置

```python
from google.adk import LlmAgent
from google.genai.models import Gemini

agent = LlmAgent(
    name="CuratorDailyAgent",
    model=Gemini(model="gemini-2.5-flash"),
    description="Curates daily AI and Robotics digest from analyzed articles",
    instruction=load_prompt("prompts/daily_prompt.txt"),
    tools=[]  # 不使用工具，僅 LLM 生成內容
)
```

### Prompt 設計（daily_prompt.txt）

**結構**:

```markdown
# Curator Daily Agent Instruction

## 角色定義
你是 InsightCosmos 的每日情報策展人（Daily Curator），專注於從已分析的 AI 與 Robotics 文章中提煉精華，為 {{USER_NAME}} 生成精簡而有洞察力的每日摘要。

## 任務目標
從提供的文章列表中：
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
對每篇文章：
- 理解核心內容（根據 summary + key_insights）
- 評估對 {{USER_NAME}} 的價值（已有 priority_score）
- 提取 1 個最重要的要點（key_takeaway）

### Step 2: 趨勢識別
- 識別文章間的共同主題
- 發現技術趨勢或產業動態
- 總結為 2-3 句話的「今日洞察」

### Step 3: 行動建議（可選）
- 如果有明確的學習方向或行動建議，簡短說明
- 例如：「建議深入了解 X 技術」、「關注 Y 公司動態」

## 輸出格式（JSON）

```json
{
  "date": "YYYY-MM-DD",
  "total_articles": 8,
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
```

## 品質標準

### 精簡原則
- summary: 1-2 句話，不超過 100 字
- key_takeaway: 1 句話，20-40 字
- daily_insight: 2-3 句話，100-150 字

### 價值導向
- 聚焦於對 {{USER_NAME}} 有實際價值的內容
- 避免重複已有的 summary
- 突出「為什麼重要」而非「是什麼」

### 可行動性
- 提供明確的學習方向或關注重點
- 建議具體而非泛泛而談

## 示例

### 輸入
```json
[
  {
    "title": "Google Releases Gemini 2.0 with Native Tool Use",
    "summary": "Google 發布 Gemini 2.0，原生支援工具調用，性能提升 40%...",
    "key_insights": ["原生工具調用", "性能提升 40%", "支援多模態"],
    "priority_score": 0.95,
    "tags": "AI,LLM"
  },
  {
    "title": "Tesla Optimus Robot Demonstrates Complex Manipulation",
    "summary": "Tesla Optimus 展示複雜物體操作能力，精準度達 95%...",
    "key_insights": ["靈巧操作", "95% 精準度", "量產計劃"],
    "priority_score": 0.88,
    "tags": "Robotics,Manipulation"
  }
]
```

### 輸出
```json
{
  "date": "2025-11-24",
  "total_articles": 2,
  "top_articles": [
    {
      "title": "Google Releases Gemini 2.0 with Native Tool Use",
      "url": "https://...",
      "summary": "Google 發布 Gemini 2.0，原生支援工具調用，性能提升 40%，可能影響 Agent 開發範式。",
      "key_takeaway": "原生工具調用將簡化 Agent 開發，值得關注 ADK 更新。",
      "priority_score": 0.95,
      "tags": ["AI", "LLM"]
    },
    {
      "title": "Tesla Optimus Robot Demonstrates Complex Manipulation",
      "url": "https://...",
      "summary": "Tesla Optimus 展示 95% 精準度的複雜物體操作，加速量產計劃。",
      "key_takeaway": "人形機器人靈巧操作技術突破，商業化加速。",
      "priority_score": 0.88,
      "tags": ["Robotics", "Manipulation"]
    }
  ],
  "daily_insight": "今日重點聚焦於 AI 與 Robotics 的工程化進展：LLM 原生工具調用降低開發門檻，人形機器人操作精準度突破商業化關鍵。兩者共同推動智慧系統從研究走向應用。",
  "recommended_action": "建議深入了解 Gemini 2.0 的工具調用機制，評估對現有 Agent 架構的影響。"
}
```

## 注意事項

1. **嚴格遵循 JSON 格式**，不要添加額外註解或說明
2. **使用繁體中文**，專業術語保留英文
3. **尊重原文事實**，不要捏造或過度推測
4. **保持客觀中立**，避免過度樂觀或悲觀
5. **如果文章數量少於 5 篇**，仍然生成完整報告，但 daily_insight 可簡短說明

---

**優先度**: P0 (核心功能)
**最後更新**: 2025-11-24
```

### Prompt 模板變數

| 變數 | 來源 | 示例 |
|------|------|------|
| `{{USER_NAME}}` | `Config.user_name` | "Ray" |
| `{{USER_INTERESTS}}` | `Config.user_interests` | "AI, Robotics, Multi-Agent Systems" |

---

## 📧 Email Sender 工具設計

### 類別設計

```python
# src/tools/email_sender.py

from typing import Optional, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from dataclasses import dataclass
from src.utils.logger import Logger


@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""  # 應用程式專用密碼
    use_tls: bool = True


class EmailSender:
    """
    Email sending utility

    Supports:
    - HTML email (primary)
    - Plain text email (fallback)
    - Multipart email (HTML + Text)
    - SMTP with TLS
    - Retry mechanism

    Example:
        >>> sender = EmailSender(config)
        >>> sender.send(
        ...     to_email="ray@example.com",
        ...     subject="Daily Digest - 2025-11-24",
        ...     html_body="<html>...</html>",
        ...     text_body="Plain text..."
        ... )
    """

    def __init__(self, config: EmailConfig):
        """
        Initialize EmailSender

        Args:
            config: Email configuration
        """
        self.config = config
        self.logger = Logger.get_logger(__name__)

    def send(
        self,
        to_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Send email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML body (optional)
            text_body: Plain text body (optional)
            retry_count: Number of retries on failure (default: 3)

        Returns:
            dict: {
                "status": "success" | "error",
                "message": str,
                "error": str (if error)
            }

        Raises:
            ValueError: If both html_body and text_body are None

        Example:
            >>> result = sender.send(
            ...     to_email="ray@example.com",
            ...     subject="Daily Digest",
            ...     html_body="<html><body>...</body></html>",
            ...     text_body="Plain text version..."
            ... )
        """
        pass

    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_body: Optional[str],
        text_body: Optional[str]
    ) -> MIMEMultipart:
        """Create MIME multipart message"""
        pass

    def _send_via_smtp(
        self,
        message: MIMEMultipart,
        to_email: str
    ) -> None:
        """Send message via SMTP"""
        pass

    def test_connection(self) -> Dict[str, Any]:
        """
        Test SMTP connection

        Returns:
            dict: {
                "status": "success" | "error",
                "message": str
            }
        """
        pass
```

### 錯誤處理

```python
# 常見錯誤與處理

1. 認證失敗（Authentication Failed）
   - 檢查 Email 與密碼
   - 確認使用「應用程式專用密碼」而非帳號密碼
   - 建議: 提供清晰的錯誤訊息與設定指引

2. SMTP 連線失敗（Connection Error）
   - 檢查網路連線
   - 確認 SMTP 主機與埠號
   - 重試機制: 指數退避（1s, 2s, 4s）

3. 收件者被拒（Recipient Rejected）
   - 驗證收件者 Email 格式
   - 檢查是否超過發送限制（500 封/天）
   - 建議: 記錄錯誤並通知使用者

4. 內容過大（Message Too Large）
   - Gmail 限制: 25 MB
   - 建議: 精簡內容或移除附件
   - Daily Digest 預期大小: < 100 KB（無問題）
```

---

## 📄 報告格式設計

### HTML Email 模板

**設計原則**:
- 簡潔美觀
- 響應式設計（RWD）
- 良好的可讀性
- 支援深色模式（可選）

**結構**:

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InsightCosmos Daily Digest - {date}</title>
    <style>
        /* 基礎樣式 */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }

        /* 容器 */
        .container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* 標題 */
        .header {
            border-bottom: 3px solid #4285f4;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }

        h1 {
            color: #4285f4;
            margin: 0;
            font-size: 24px;
        }

        .date {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }

        /* 文章卡片 */
        .article {
            border-left: 4px solid #e0e0e0;
            padding-left: 15px;
            margin-bottom: 25px;
        }

        .article.high-priority {
            border-left-color: #ea4335;
        }

        .article.medium-priority {
            border-left-color: #fbbc04;
        }

        .article-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 8px 0;
        }

        .article-title a {
            color: #1a73e8;
            text-decoration: none;
        }

        .article-title a:hover {
            text-decoration: underline;
        }

        .article-summary {
            color: #5f6368;
            margin: 8px 0;
        }

        .article-takeaway {
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 10px;
            margin: 8px 0;
            font-style: italic;
        }

        .article-meta {
            font-size: 12px;
            color: #999;
            margin-top: 8px;
        }

        .tag {
            display: inline-block;
            background-color: #e8f0fe;
            color: #1967d2;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin-right: 5px;
        }

        .priority-score {
            color: #34a853;
            font-weight: 600;
        }

        /* 洞察區塊 */
        .insight-section {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
        }

        .insight-title {
            font-weight: 600;
            color: #e65100;
            margin: 0 0 10px 0;
        }

        /* 行動建議 */
        .action-section {
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
        }

        .action-title {
            font-weight: 600;
            color: #2e7d32;
            margin: 0 0 10px 0;
        }

        /* 頁尾 */
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #999;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🌌 InsightCosmos Daily Digest</h1>
            <div class="date">{date} | {total_articles} 篇精選文章</div>
        </div>

        <!-- Articles -->
        {articles_html}

        <!-- Daily Insight -->
        <div class="insight-section">
            <div class="insight-title">💡 今日洞察</div>
            <div>{daily_insight}</div>
        </div>

        <!-- Recommended Action (optional) -->
        {action_html}

        <!-- Footer -->
        <div class="footer">
            <p>由 InsightCosmos 自動生成 | Powered by Google ADK & Gemini 2.5</p>
            <p>這是一封自動發送的郵件，請勿直接回覆。</p>
        </div>
    </div>
</body>
</html>
```

### 純文字 Email 模板

```text
=====================================
  InsightCosmos Daily Digest
  {date}
=====================================

📊 今日精選: {total_articles} 篇文章

{articles_text}

=====================================
💡 今日洞察
=====================================
{daily_insight}

{action_text}

-------------------------------------
由 InsightCosmos 自動生成
Powered by Google ADK & Gemini 2.5
-------------------------------------
```

**文章格式（純文字）**:
```text
────────────────────────────────────
[{index}] {title}
────────────────────────────────────
🔗 {url}

📝 摘要:
{summary}

💡 核心要點:
{key_takeaway}

🏷️ 標籤: {tags}
⭐ 優先度: {priority_score}

```

---

## 📋 實作計劃

### 實作順序

```
1. Email Sender 工具 (優先)
   └─ src/tools/email_sender.py
   └─ tests/unit/test_email_sender.py

2. 報告格式化模組
   └─ src/tools/digest_formatter.py
   └─ tests/unit/test_digest_formatter.py

3. Curator Daily Prompt
   └─ prompts/daily_prompt.txt

4. Curator Daily Agent
   └─ src/agents/curator_daily.py
   └─ tests/unit/test_curator_daily.py

5. 整合測試
   └─ tests/integration/test_curator_integration.py

6. 實作總結文件
   └─ docs/implementation/stage8_implementation.md
```

### 檔案結構

```
/InsightCosmos
├─ src/
│   ├─ agents/
│   │   └─ curator_daily.py        # Curator Daily Agent & Runner
│   └─ tools/
│       ├─ email_sender.py         # Email 發送工具
│       └─ digest_formatter.py     # 報告格式化（HTML + Text）
│
├─ prompts/
│   └─ daily_prompt.txt            # Daily Digest Prompt
│
├─ tests/
│   ├─ unit/
│   │   ├─ test_email_sender.py
│   │   ├─ test_digest_formatter.py
│   │   └─ test_curator_daily.py
│   └─ integration/
│       └─ test_curator_integration.py
│
└─ docs/
    ├─ planning/
    │   └─ stage8_curator_daily.md  # 本文件
    └─ implementation/
        └─ stage8_implementation.md  # 實作總結（待建立）
```

---

## 🧪 測試策略

### 單元測試

**1. EmailSender 測試** (`test_email_sender.py`)

測試案例:
- ✅ `test_send_html_email_success` - HTML Email 成功發送
- ✅ `test_send_text_email_success` - 純文字 Email 成功發送
- ✅ `test_send_multipart_email` - HTML + Text 混合格式
- ✅ `test_send_email_authentication_failed` - 認證失敗處理
- ✅ `test_send_email_connection_error` - 連線錯誤處理
- ✅ `test_send_email_retry_mechanism` - 重試機制
- ✅ `test_send_email_invalid_recipient` - 無效收件者
- ✅ `test_send_email_no_body` - 缺少內容錯誤
- ✅ `test_test_connection_success` - 連線測試成功
- ✅ `test_test_connection_failed` - 連線測試失敗

**2. DigestFormatter 測試** (`test_digest_formatter.py`)

測試案例:
- ✅ `test_format_html_basic` - 基本 HTML 格式化
- ✅ `test_format_html_with_action` - 含行動建議
- ✅ `test_format_html_priority_colors` - 優先度顏色標記
- ✅ `test_format_text_basic` - 基本純文字格式化
- ✅ `test_format_text_with_action` - 含行動建議
- ✅ `test_format_empty_articles` - 空文章列表處理
- ✅ `test_format_special_characters` - 特殊字元處理
- ✅ `test_format_long_content` - 長內容處理

**3. CuratorDailyAgent 測試** (`test_curator_daily.py`)

測試案例:
- ✅ `test_create_curator_agent` - Agent 創建
- ✅ `test_load_prompt_with_variables` - Prompt 變數替換
- ✅ `test_parse_digest_json` - JSON 解析
- ✅ `test_parse_digest_json_in_markdown` - Markdown 包裝的 JSON
- ✅ `test_parse_digest_invalid_json` - 無效 JSON 處理
- ✅ `test_runner_generate_digest` - 報告生成（Mock LLM）
- ✅ `test_runner_format_and_send` - 格式化與發送（Mock EmailSender）
- ✅ `test_runner_full_flow` - 完整流程（Mock）

### 整合測試

**整合測試** (`test_curator_integration.py`)

測試案例:
- ✅ `test_fetch_and_generate_digest` - 從 Memory 取得文章並生成報告（Mock LLM）
- ✅ `test_format_digest_html_and_text` - 格式化 HTML 與純文字
- ✅ `test_send_email_mock_smtp` - Email 發送（Mock SMTP）
- ✅ `test_full_curator_pipeline` - 完整流程（Mock）
- 🔧 `test_full_curator_pipeline_with_real_llm` - 真實 LLM（標記為 manual）
- 🔧 `test_full_curator_pipeline_with_real_email` - 真實 Email（標記為 manual）

### 手動測試

**測試清單**:
1. ✅ 使用真實 GOOGLE_API_KEY 生成報告
2. ✅ 使用真實 SMTP 設定發送測試郵件
3. ✅ 檢查 HTML Email 在不同客戶端的顯示效果
   - Gmail Web
   - Outlook
   - 行動裝置（iOS/Android）
4. ✅ 檢查純文字 Email 的可讀性
5. ✅ 驗證報告內容品質（精簡、有洞察、可行動）

---

## ✅ 驗收標準

### 功能完整性

- [ ] **文章篩選**
  - [ ] 能從 ArticleStore 取得已分析文章
  - [ ] 依據 priority_score 排序
  - [ ] 篩選 Top 5-10 篇

- [ ] **報告生成**
  - [ ] LLM 能生成結構化 JSON 輸出
  - [ ] 包含所有必要欄位（summary, key_takeaway, daily_insight）
  - [ ] 內容精簡有價值（人工驗證）

- [ ] **格式化**
  - [ ] HTML 格式美觀易讀
  - [ ] 純文字格式結構清晰
  - [ ] 支援響應式設計（RWD）

- [ ] **Email 發送**
  - [ ] 成功發送 HTML Email
  - [ ] 成功發送純文字 Email
  - [ ] 成功發送混合格式 Email
  - [ ] 錯誤處理與重試機制正常

### 品質標準

- [ ] **代碼品質**
  - [ ] 所有函式有完整 docstring
  - [ ] 類型標註完整
  - [ ] 錯誤處理覆蓋主要場景
  - [ ] 符合 CLAUDE.md 編碼規範

- [ ] **測試覆蓋**
  - [ ] 單元測試通過率 100%
  - [ ] 整合測試通過率 >= 80%
  - [ ] 測試覆蓋率 >= 85%
  - [ ] 手動測試驗證通過

- [ ] **文件完整性**
  - [ ] 規劃文件完整（本文件）
  - [ ] 實作總結文件完整
  - [ ] API 文件更新
  - [ ] 開發日誌更新

### 內容品質（人工驗證）

- [ ] **摘要品質**
  - [ ] 精簡易讀（1-2 句）
  - [ ] 保留關鍵資訊
  - [ ] 符合使用者興趣

- [ ] **洞察品質**
  - [ ] 識別趨勢或模式
  - [ ] 提供新視角
  - [ ] 有深度而非泛泛而談

- [ ] **行動建議**
  - [ ] 具體可執行
  - [ ] 與使用者相關
  - [ ] 有實際價值

### 效能標準

- [ ] **執行時間**
  - [ ] 篩選文章: < 1 秒
  - [ ] LLM 生成報告: < 10 秒
  - [ ] 格式化: < 1 秒
  - [ ] Email 發送: < 5 秒
  - [ ] **總計**: < 20 秒

- [ ] **成本控制**
  - [ ] 每日 LLM 成本: < $0.01
  - [ ] Email 發送成本: $0（免費）

---

## ⚠️ 風險與對策

### 風險 1: Gmail SMTP 認證失敗

**描述**: 使用者可能未正確設定應用程式專用密碼

**影響**: 無法發送 Email

**對策**:
1. 提供詳細的設定指南（README.md）
2. 實作 `test_connection()` 方法，讓使用者測試設定
3. 錯誤訊息包含設定連結

**範例錯誤訊息**:
```
❌ Email 認證失敗！

請確認以下設定：
1. EMAIL_ACCOUNT: 你的 Gmail 地址
2. EMAIL_PASSWORD: 應用程式專用密碼（非帳號密碼）

如何取得應用程式專用密碼:
https://support.google.com/accounts/answer/185833

測試連線:
python -c "from src.tools.email_sender import EmailSender; EmailSender(config).test_connection()"
```

### 風險 2: LLM 輸出格式不穩定

**描述**: LLM 可能不遵循 JSON 格式要求

**影響**: 解析失敗，報告生成中斷

**對策**:
1. Prompt 明確要求 JSON 格式
2. 解析器支援 Markdown 包裝的 JSON（```json ... ```）
3. 實作 JSON Schema 驗證
4. 失敗時重試（最多 3 次）
5. 記錄原始輸出以供除錯

### 風險 3: Email 格式在不同客戶端顯示不一致

**描述**: HTML Email 在不同客戶端可能顯示效果不同

**影響**: 使用者體驗下降

**對策**:
1. 使用簡單的 HTML 結構（避免複雜 CSS）
2. 使用 inline styles（避免 <style> 標籤被過濾）
3. 提供純文字備用格式
4. 手動測試主流客戶端（Gmail, Outlook）

### 風險 4: 日報內容品質不穩定

**描述**: LLM 生成的摘要可能過於冗長或缺乏洞察

**影響**: 使用者體驗下降

**對策**:
1. Prompt 明確規定字數限制
2. 提供高品質示例
3. 人工驗收前 10 份日報
4. Phase 2 考慮加入 Reflection 機制

### 風險 5: SMTP 發送限制

**描述**: Gmail 每日發送限制 500 封

**影響**: 無法發送（但個人使用不會觸及）

**對策**:
1. 記錄每日發送次數
2. 觸及限制前警告
3. Phase 2 考慮支援其他 SMTP 服務

---

## 📚 相關資源

### 技術文件

- [Python smtplib](https://docs.python.org/3/library/smtplib.html) - SMTP 協議實作
- [Python email.mime](https://docs.python.org/3/library/email.mime.html) - Email 格式處理
- [Gmail SMTP 設定](https://support.google.com/mail/answer/7126229) - Gmail SMTP 指南
- [應用程式專用密碼](https://support.google.com/accounts/answer/185833) - 安全性設定

### 內部參考

- `src/memory/article_store.py` - 文章查詢 API
- `src/agents/analyst_agent.py` - Analyst Agent 參考實作
- `prompts/analyst_prompt.txt` - Prompt 設計參考

---

## 📊 時間規劃

### 總體時間: 1.5 天

| 任務 | 預計時間 | 備註 |
|------|---------|------|
| **規劃階段** | 0.3 天 | 本文件 |
| Email Sender 實作 | 0.3 天 | 包含測試 |
| Digest Formatter 實作 | 0.2 天 | 包含測試 |
| Curator Agent 實作 | 0.3 天 | 包含測試 |
| 整合測試 | 0.2 天 | 包含手動測試 |
| 實作總結文件 | 0.2 天 | 文件撰寫 |

---

## ✅ 下一步行動

### 立即開始

1. **建立 Email Sender 工具**
   - 創建 `src/tools/email_sender.py`
   - 實作 SMTP 發送邏輯
   - 撰寫單元測試

2. **建立 Digest Formatter 模組**
   - 創建 `src/tools/digest_formatter.py`
   - 實作 HTML 與純文字格式化
   - 撰寫單元測試

3. **設計 Daily Prompt**
   - 創建 `prompts/daily_prompt.txt`
   - 包含詳細的指令與示例

4. **實作 Curator Daily Agent**
   - 創建 `src/agents/curator_daily.py`
   - 實作 Agent 與 Runner
   - 撰寫測試

---

**維護者**: Ray 張瑞涵
**最後更新**: 2025-11-24
**狀態**: 規劃完成，等待實作
**下一階段**: Stage 8 實作階段
