# Google Search 迁移指南

> **版本**: v1.1
> **日期**: 2025-11-23
> **来源**: 基于 Context7 提供的 googleapis/python-genai v1.33.0 官方文档

---

## 📋 迁移概述

本次迁移将 Google Search 功能从 **Custom Search API** 升级到 **Gemini Search Grounding**，使用 Google 官方的统一 SDK。

### 迁移动机

1. **简化配置** - 不再需要 Search Engine ID
2. **官方支持** - 使用 Google 最新的统一 SDK
3. **成本优化** - Grounding 整合在 Gemini API 中
4. **更好的整合** - 与 LLM 推理无缝结合

---

## 🔄 技术变更对比

### 1. SDK 选择

| 项目 | 旧方案 | 新方案 |
|------|--------|--------|
| **SDK** | `google-generativeai` (旧版) | `google-genai` (官方统一 SDK) |
| **版本** | 0.3.0+ | 1.33.0+ |
| **文档来源** | 非官方 | googleapis/python-genai 官方 |
| **Context7** | ❌ 未验证 | ✅ 已验证 (v1.33.0) |

### 2. API 配置

#### 旧方案（Custom Search API）
```bash
# .env 需要两个独立的配置
GOOGLE_API_KEY=...           # Gemini API
GOOGLE_SEARCH_API_KEY=...    # Custom Search API
GOOGLE_SEARCH_ENGINE_ID=...  # 需要手动创建 PSE
```

#### 新方案（Gemini Grounding）
```bash
# .env 只需一个 API Key
GOOGLE_API_KEY=...           # 统一的 Gemini API
```

### 3. 代码实现

#### 旧方案（HTTP 请求 Custom Search API）

```python
import requests

# 手动构建 HTTP 请求
url = (
    f"https://www.googleapis.com/customsearch/v1?"
    f"key={api_key}&cx={engine_id}&q={query}"
)
response = requests.get(url)
data = response.json()

# 手动解析 JSON 结果
items = data.get('items', [])
```

#### 新方案（官方 SDK + Grounding）

```python
from google import genai
from google.genai import types

# 初始化客户端
client = genai.Client(api_key=api_key)

# 直接调用 Grounding
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Search query here',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ]
    )
)

# 自动获取 Grounding 元数据
articles = response.candidates[0].grounding_metadata.grounding_chunks
```

---

## 📦 文件变更清单

### 新增文件

```
src/tools/google_search_grounding_v2.py   # 基于官方 SDK 的新实现
tests/test_search_v2.py                   # 简化的测试脚本
docs/migration/google_search_migration.md # 本文档
```

### 修改文件

```
requirements.txt    # google-generativeai → google-genai
.env.example        # 移除 Search Engine ID 要求
CLAUDE.md           # 更新环境变量说明
```

### 待弃用文件

```
src/tools/google_search.py                # 旧的 Custom Search API 实现
src/tools/google_search_grounding.py      # 使用旧 SDK 的实现
tests/test_google_search_grounding.py     # 旧测试脚本
```

---

## 🚀 迁移步骤

### Step 1: 安装新 SDK

```bash
# 卸载旧 SDK（可选）
pip uninstall google-generativeai

# 安装新 SDK
pip install google-genai>=1.33.0
```

### Step 2: 更新环境变量

编辑 `.env` 文件：

```bash
# 移除这些（如果存在）
# GOOGLE_SEARCH_API_KEY=...
# GOOGLE_SEARCH_ENGINE_ID=...

# 只保留这个
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Step 3: 更新代码引用

在任何使用搜索功能的地方：

```python
# 旧代码
from src.tools.google_search import GoogleSearchTool
search_tool = GoogleSearchTool()

# 新代码
from src.tools.google_search_grounding_v2 import GoogleSearchGroundingTool
search_tool = GoogleSearchGroundingTool()

# API 保持不变
result = search_tool.search_articles("AI news", max_results=10)
```

### Step 4: 测试验证

```bash
# 运行简化测试
python3 tests/test_search_v2.py
```

---

## 🔍 API 兼容性

### ✅ 保持兼容的接口

以下方法**签名不变**，可以无缝迁移：

```python
# search_articles() - 参数和返回值保持一致
result = search_tool.search_articles(
    query="AI news",
    max_results=10,
    date_restrict="past week",  # 现在是提示词而非 API 参数
    language="en"
)

# batch_search() - 完全兼容
result = search_tool.batch_search(
    queries=["AI", "robotics"],
    max_results_per_query=5
)

# validate_api_credentials() - 完全兼容
is_valid = search_tool.validate_api_credentials()
```

### ⚠️ 返回值差异

| 字段 | 旧值 | 新值 |
|------|------|------|
| `source` | `"google_search"` | `"google_search_grounding"` |
| `summary` | 搜索结果摘要 | 使用 `title` 作为摘要 |
| `published_at` | 当前时间 | 当前时间（未变） |

### ❌ 不再需要的功能

```python
# 这些功能已集成到 SDK 中，不再需要手动处理

# ❌ 旧代码需要处理 quota exceeded
if result['quota_exceeded']:
    handle_quota_error()

# ✅ 新代码自动处理，只需检查 status
if result['status'] == 'error':
    handle_error(result['error_message'])
```

---

## 📊 性能对比

| 指标 | Custom Search API | Gemini Grounding |
|------|-------------------|------------------|
| **API 调用** | 独立的 HTTP 请求 | 集成在 LLM 调用中 |
| **响应时间** | ~200-500ms | ~1-2s (含 LLM 推理) |
| **结果质量** | 纯搜索结果 | LLM 过滤后的相关结果 |
| **配置复杂度** | 需要 PSE + API Key | 只需 API Key |
| **免费额度** | 100 次/天 | 取决于 Gemini API 配额 |

---

## 🐛 故障排除

### 问题 1: `ModuleNotFoundError: No module named 'google.genai'`

**解决方案**:
```bash
pip install google-genai>=1.33.0
```

### 问题 2: `AttributeError: 'Client' object has no attribute 'models'`

**原因**: 使用了旧版 SDK 的导入方式

**解决方案**:
```python
# ❌ 错误
import google.generativeai as genai

# ✅ 正确
from google import genai
```

### 问题 3: 搜索结果为空

**排查步骤**:
1. 检查 API Key 是否有效
2. 检查 prompt 是否清晰
3. 查看 `response.candidates[0].grounding_metadata` 是否存在
4. 启用 DEBUG 日志查看详细信息

---

## 📚 参考资料

### 官方文档

- **SDK 仓库**: https://github.com/googleapis/python-genai
- **Context7 文档**: `/googleapis/python-genai` v1.33.0
- **API 参考**: [Gemini API Documentation](https://ai.google.dev/docs)

### 代码示例

官方 Grounding 示例（来自 Context7）:

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What was the score of the latest Olympique Lyonais game?',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ]
    ),
)

# 查看响应
print(f'Response: {response.text}')

# 查看搜索查询
print(f'Search Query: {response.candidates[0].grounding_metadata.web_search_queries}')

# 查看使用的来源
for site in response.candidates[0].grounding_metadata.grounding_chunks:
    print(f"- {site.web.title}: {site.web.uri}")
```

---

## ✅ 迁移检查清单

完成迁移后，请确认：

- [ ] 已安装 `google-genai>=1.33.0`
- [ ] `.env` 文件只包含 `GOOGLE_API_KEY`
- [ ] 代码中已更新 import 语句
- [ ] 测试脚本运行成功
- [ ] 日志中无错误信息
- [ ] 搜索结果符合预期

---

**最后更新**: 2025-11-23
**文档来源**: Context7 - googleapis/python-genai v1.33.0
**维护者**: Ray 张瑞涵
