# Stage 8 Manual Test Guide

> **文件版本**: 1.0
> **建立日期**: 2025-11-24
> **目的**: 提供 Stage 8 手動測試的完整指南

---

## 📋 概述

本文件提供 Stage 8（每日策展人）的手動測試指南，涵蓋真實 API 與 Email 的測試場景。

**測試範圍**:
- ✅ 真實 LLM (Gemini 2.5 Flash) 測試
- ✅ 真實 SMTP Email 發送測試
- ✅ 端到端 (E2E) 完整流程測試
- ✅ 錯誤處理與邊界條件測試

---

## 🔧 環境準備

### 1. API Key 設定

在 `.env` 檔案中設定以下環境變數：

```bash
# Google Gemini API (必需)
GOOGLE_API_KEY=your_gemini_api_key_here

# Email 設定 (必需)
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true

# Database
DATABASE_PATH=data/insights.db

# 個人配置
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems
```

### 2. 取得 API Keys

#### Gemini API Key
1. 前往 [Google AI Studio](https://aistudio.google.com/apikey)
2. 登入 Google 帳號
3. 點擊「Create API Key」
4. 複製 API Key 到 `.env` 檔案

#### Gmail App Password
1. 前往 [Google App Passwords](https://myaccount.google.com/apppasswords)
2. 登入 Google 帳號
3. 選擇「Mail」和「Other (Custom name)」
4. 輸入「InsightCosmos」
5. 點擊「Generate」
6. 複製 16 位數密碼（無空格）到 `.env`

**注意**: 必須先啟用 Google 帳號的「兩步驟驗證」才能建立 App Password。

### 3. 驗證環境

```bash
# 檢查 .env 檔案
cat .env | grep -E "GOOGLE_API_KEY|EMAIL_ACCOUNT|EMAIL_PASSWORD"

# 啟動虛擬環境
source venv/bin/activate

# 驗證套件安裝
python -c "from google.adk.agents import LlmAgent; print('✅ ADK installed')"
python -c "import smtplib; print('✅ SMTP available')"
```

---

## 🧪 手動測試案例

### 測試 1: 真實 LLM 生成測試

**目的**: 驗證 Curator Daily Agent 能使用真實 Gemini API 生成報告

**前置條件**:
- ✅ GOOGLE_API_KEY 已設定
- ✅ Database 中有已分析的文章

**測試步驟**:

```bash
# 1. 執行測試
source venv/bin/activate
pytest tests/integration/test_curator_integration.py::TestCuratorWithRealLLM::test_generate_digest_with_real_llm -v -s

# 2. 或使用 pytest marker
pytest tests/integration/test_curator_integration.py -v -m manual --run-manual
```

**預期結果**:
```json
{
  "date": "2025-11-24",
  "total_articles": 3,
  "top_articles": [
    {
      "title": "Google Releases Gemini 2.0 with Native Tool Use",
      "url": "https://example.com/gemini-2.0",
      "summary": "Google 發布 Gemini 2.0，原生支援工具調用...",
      "key_takeaway": "原生工具調用將簡化 Agent 開發...",
      "priority_score": 0.95,
      "tags": ["AI", "LLM"]
    }
  ],
  "daily_insight": "今日重點聚焦於 AI 與 Robotics 的工程化進展...",
  "recommended_action": "建議深入了解 Gemini 2.0 的工具調用機制..."
}
```

**驗證項目**:
- [ ] LLM 成功生成 JSON 格式報告
- [ ] `date` 欄位正確
- [ ] `top_articles` 包含至少 1 篇文章
- [ ] `daily_insight` 為中文且有洞察內容
- [ ] `recommended_action` 提供可行動的建議

**測試時間**: ~5-10 秒 (視 LLM 速度而定)

---

### 測試 2: 真實 Email 發送測試

**目的**: 驗證 Email Sender 能透過 SMTP 成功發送郵件

**前置條件**:
- ✅ EMAIL_ACCOUNT 已設定
- ✅ EMAIL_PASSWORD (App Password) 已設定
- ✅ Gmail 帳號已啟用「兩步驟驗證」

**測試步驟**:

```bash
# 1. 執行測試
pytest tests/integration/test_curator_integration.py::TestCuratorWithRealEmail::test_send_real_email -v -s

# 2. 檢查收件匣
# 登入 EMAIL_ACCOUNT 信箱，尋找標題為 "[TEST] InsightCosmos Daily Digest - YYYY-MM-DD" 的郵件
```

**預期結果**:
1. **測試輸出**:
   ```
   ✅ Test email sent successfully!
      Check inbox: your_email@gmail.com
   ```

2. **收到的郵件**:
   - 標題: `[TEST] InsightCosmos Daily Digest - 2025-11-24`
   - 內容格式:
     - HTML 版本：彩色排版、優先度標記、超連結
     - 純文字版本：格式清晰、易讀

**驗證項目**:
- [ ] SMTP 連線成功
- [ ] 郵件發送成功（無錯誤）
- [ ] 收到測試郵件（檢查收件匣與垃圾郵件）
- [ ] HTML 版本渲染正確（顏色、連結、排版）
- [ ] 純文字版本可讀（無 HTML tags）
- [ ] 優先度顏色標記正確：
  - 🔴 高優先度 (score >= 0.9): 紅色
  - 🟡 中優先度 (0.7 <= score < 0.9): 黃色
  - 🔵 低優先度 (score < 0.7): 藍色

**常見問題排除**:

| 錯誤訊息 | 原因 | 解決方式 |
|---------|------|---------|
| `Authentication failed (535)` | App Password 錯誤 | 重新生成 App Password |
| `Username and Password not accepted` | 未啟用兩步驟驗證 | 至 Google 設定啟用 |
| `SMTPServerDisconnected` | SMTP 設定錯誤 | 檢查 SMTP_HOST 與 SMTP_PORT |
| `Connection timeout` | 網路問題或防火牆 | 檢查網路連線 |

**測試時間**: ~3-5 秒

---

### 測試 3: 端到端 (E2E) 完整流程測試

**目的**: 驗證從資料庫讀取 → LLM 生成 → 格式化 → Email 發送的完整流程

**前置條件**:
- ✅ GOOGLE_API_KEY 已設定
- ✅ EMAIL_ACCOUNT 和 EMAIL_PASSWORD 已設定
- ✅ Database 中有已分析的文章

**測試步驟**:

```bash
# 1. 執行端到端測試
pytest tests/integration/test_curator_integration.py::TestCuratorE2E::test_end_to_end_curator_pipeline -v -s

# 2. 等待測試完成（約 10-15 秒）

# 3. 檢查測試輸出
# ✅ End-to-End test completed successfully!
#    Email sent to: your_email@gmail.com
#    Digest date: 2025-11-24
#    Total articles: 3

# 4. 檢查收件匣
# 登入信箱，尋找 "InsightCosmos Daily Digest" 郵件
```

**預期結果**:

1. **測試成功完成**:
   ```python
   {
       "status": "success",
       "digest": {
           "date": "2025-11-24",
           "total_articles": 3,
           "top_articles": [...],
           "daily_insight": "...",
           "recommended_action": "..."
       },
       "email_result": {
           "status": "success",
           "message": "Email sent to your_email@gmail.com"
       }
   }
   ```

2. **收到完整報告郵件**:
   - 包含所有測試文章
   - LLM 生成的洞察與建議
   - 格式化完整且美觀

**驗證項目**:
- [ ] Database 查詢成功（取得已分析文章）
- [ ] LLM 生成成功（JSON 格式正確）
- [ ] HTML 格式化成功（包含所有區塊）
- [ ] 純文字格式化成功（無 HTML tags）
- [ ] Email 發送成功（SMTP 無錯誤）
- [ ] 收到郵件（檢查收件匣）
- [ ] 郵件內容完整（所有文章、洞察、建議）

**測試時間**: ~10-15 秒

---

## 🚨 錯誤處理測試

### 測試 4: LLM 無效回應處理

**測試場景**: LLM 返回無效 JSON

**測試方式**: 在 `curator_daily.py` 中模擬錯誤回應

```python
# 臨時修改 _invoke_llm 方法返回無效 JSON
def _invoke_llm(self, user_input: str) -> Optional[str]:
    return "這不是 JSON"  # 模擬錯誤
```

**預期行為**:
```python
{
    "status": "error",
    "error": "LLM failed to generate valid digest"
}
```

---

### 測試 5: Email 認證失敗處理

**測試場景**: SMTP 認證失敗

**測試方式**: 使用錯誤的 App Password

```bash
# 1. 臨時修改 .env
EMAIL_PASSWORD=wrong_password

# 2. 執行測試
pytest tests/integration/test_curator_integration.py::TestCuratorWithRealEmail::test_send_real_email -v -s
```

**預期行為**:
```python
{
    "status": "error",
    "message": "Authentication failed",
    "error": "SMTP authentication failed...\n\nPlease check...\nGenerate App Password..."
}
```

---

### 測試 6: Database 無文章處理

**測試場景**: Database 中沒有已分析的文章

**測試方式**: 使用空白測試資料庫

```bash
# 1. 建立空白測試資料庫
rm -f data/test_empty.db
DATABASE_PATH=data/test_empty.db python src/memory/database.py

# 2. 執行測試
pytest tests/integration/test_curator_integration.py::TestCuratorFullPipeline::test_full_curator_pipeline_with_error_handling -v -s
```

**預期行為**:
```python
{
    "status": "error",
    "error": "No analyzed articles available for digest"
}
```

---

## 📊 效能基準測試

### 測試 7: LLM 回應時間測試

**測試目的**: 測量 LLM 生成報告的時間

**測試方式**:

```python
import time
from src.agents.curator_daily import CuratorDailyRunner

# 測量時間
start = time.time()
digest = runner.generate_digest(articles)
elapsed = time.time() - start

print(f"LLM Response Time: {elapsed:.2f}s")
```

**效能基準**:
- ✅ 優秀: < 5 秒
- ⚠️ 可接受: 5-10 秒
- ❌ 需優化: > 10 秒

---

### 測試 8: Email 發送時間測試

**測試目的**: 測量 SMTP 發送郵件的時間

**測試方式**:

```python
import time
from src.tools.email_sender import EmailSender

start = time.time()
result = email_sender.send(to_email=..., subject=..., html_body=..., text_body=...)
elapsed = time.time() - start

print(f"Email Send Time: {elapsed:.2f}s")
```

**效能基準**:
- ✅ 優秀: < 3 秒
- ⚠️ 可接受: 3-5 秒
- ❌ 需優化: > 5 秒

---

## ✅ 測試檢查清單

### 功能測試

- [ ] 測試 1: 真實 LLM 生成測試 ✅
- [ ] 測試 2: 真實 Email 發送測試 ✅
- [ ] 測試 3: E2E 完整流程測試 ✅

### 錯誤處理測試

- [ ] 測試 4: LLM 無效回應處理 ✅
- [ ] 測試 5: Email 認證失敗處理 ✅
- [ ] 測試 6: Database 無文章處理 ✅

### 效能測試

- [ ] 測試 7: LLM 回應時間測試 ✅
- [ ] 測試 8: Email 發送時間測試 ✅

### 品質驗證

- [ ] HTML Email 在 Gmail 中渲染正確 ✅
- [ ] HTML Email 在 Outlook 中渲染正確 ⚠️ (可選)
- [ ] 純文字 Email 可讀性良好 ✅
- [ ] 優先度顏色標記正確 ✅
- [ ] 中文內容顯示無亂碼 ✅

---

## 📝 測試記錄模板

```markdown
## 測試執行記錄

**測試日期**: 2025-11-24
**測試人員**: Ray
**環境**: macOS / Python 3.13 / venv

### 測試 1: 真實 LLM 生成測試
- **狀態**: ✅ 通過 / ❌ 失敗
- **執行時間**: X.XX 秒
- **備註**: [記錄任何問題或觀察]

### 測試 2: 真實 Email 發送測試
- **狀態**: ✅ 通過 / ❌ 失敗
- **執行時間**: X.XX 秒
- **收到郵件**: 是 / 否
- **備註**: [記錄任何問題或觀察]

### 測試 3: E2E 完整流程測試
- **狀態**: ✅ 通過 / ❌ 失敗
- **執行時間**: X.XX 秒
- **文章數量**: X 篇
- **備註**: [記錄任何問題或觀察]
```

---

## 🔗 相關文件

- [Stage 8 Test Report](./stage8_test_report.md) - 完整測試報告
- [Email Sender 實作](../../src/tools/email_sender.py) - Email 發送模組
- [Curator Daily Agent](../../src/agents/curator_daily.py) - 每日策展人
- [Digest Formatter](../../src/tools/digest_formatter.py) - 報告格式化

---

**最後更新**: 2025-11-24
**維護者**: Ray 張瑞涵
