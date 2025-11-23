# InsightCosmos - Claude Code 项目一致性指南

> **文档版本**: 1.0
> **创建日期**: 2025-11-19
> **项目阶段**: Phase 1 - 个人宇宙版
> **技术框架**: Google ADK (Agent Development Kit)

---

## 📋 文档目的

本文档是 InsightCosmos 项目的**核心一致性指南**，用于：

1. **统一开发理念** - 确保所有开发遵循相同的架构哲学
2. **保持技术一致** - 明确技术选型与实现标准
3. **指导 AI 辅助** - 为 Claude Code 提供项目上下文
4. **文档系统规范** - 建立"规划→实作→验证"的开发节奏
5. **說明文檔語言統一** - 一律使用繁體中文記錄和備註

---

## 🌌 项目核心理念

### 项目定位

InsightCosmos 是一个**个人 AI 情报宇宙引擎**，通过多代理系统自动收集、分析、结构化 AI 与 Robotics 领域的重要信息，并通过 Daily/Weekly 报告形式提供智能洞察。

**核心价值主张**:
- 🔍 **自动探索** - AI Agent 主动扫描宇宙级信息源
- 🧠 **自主推理** - LLM 深度分析与洞察提取
- 🧩 **结构化记忆** - Vector Memory + SQLite 知识库
- 📬 **智能报告** - 个性化的每日/每周情报摘要

### 设计哲学

基于 **Google AI Agent 模型**的三大支柱：

```
┌─────────────────────────────────────┐
│     Google Agent 三大支柱           │
│                                     │
│  Tools    +    Memory    +  Planning│
│  工具使用      记忆管理      规划推理 │
└─────────────────────────────────────┘
```

**关键原则**:

1. **Think-Act-Observe 循环** - 所有 Agent 遵循"思考→行动→观察→迭代"模式
2. **模块化多 Agent** - 单一职责 Agent 协作，而非单一全能 Agent
3. **记忆驱动决策** - Session（短期）+ Memory（长期）双层记忆
4. **工具原子化** - 每个工具职责单一、文档清晰、输出结构化
5. **质量优先** - 从 Day 0 建立可观测性与评估机制
6. **工具正確**  -- 當問題跟「程式庫 / framework 的使用方式、設定步驟、API 文件、版本差異」有關時，
  一律優先呼叫 `context7` 這個 MCP 來查最新官方文件與程式碼範例，再回答我。
- 回答時請標註你是根據 Context7 取得的文件（例如簡短說明來源套件與版本）。
---

## 🏗️ 技术架构总览

### 系统架构图

```
┌───────────────────────────────────────────────────────────┐
│                  InsightCosmos v1.0                       │
│                   (个人宇宙版)                             │
└───────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│            Daily / Weekly Orchestrator                    │
│          (SequentialAgent 顺序编排)                        │
└───────────────────────────────────────────────────────────┘
                            ↓
┌─────────────┬─────────────┬─────────────┬─────────────────┐
│             │             │             │                 │
│  Scout      │  Analyst    │  Curator    │  Email          │
│  Agent      │  Agent      │  Agent      │  Delivery       │
│             │             │             │                 │
│ RSS +       │ LLM 分析    │ Daily/      │ SMTP            │
│ Search      │ + 推理      │ Weekly      │ 发送            │
│             │             │ 报告        │                 │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│                  Memory Universe                          │
│  ┌──────────────────┐      ┌──────────────────┐          │
│  │  SQLite DB       │      │  Vector Store    │          │
│  │  (结构化存储)     │      │  (Embedding)     │          │
│  └──────────────────┘      └──────────────────┘          │
└───────────────────────────────────────────────────────────┘
```

### Agent 职责分工

| Agent | 类型 | 职责 | 输出 |
|-------|------|------|------|
| **Scout Agent** | 信息探索 | RSS + Google Search 收集、去重 | `raw_articles[]` |
| **Analyst Agent** | 技术洞察 | LLM 分析、打分、Embedding | `analyzed_articles[]` |
| **Curator Agent** | 报告生成 | Daily Digest / Weekly Report | `email_content` |

### 技术栈选型

#### 核心框架
- **ADK (Agent Development Kit)** - Google 官方 Agent 开发框架
- **Python 3.10+** - 开发语言
- **Gemini 2.5 Flash** - 主力 LLM（效率优先）
- **Gemini 2.5 Pro** - 复杂分析场景（可选）

#### 工具与服务
- **RSS Parser** - `feedparser` 库
- **Google Search** - ADK 内置 `google_search` 工具
- **Embedding** - ADK 内置 `embedding` 工具
- **SQLite** - 轻量级结构化存储
- **Email** - SMTP (Gmail API 可选)

#### 开发工具
- **Version Control** - Git
- **Environment** - `.env` + `python-dotenv`
- **Testing** - ADK Evaluation Framework
- **Observability** - LoggingPlugin + OpenTelemetry (可选)

---

## 📁 项目结构规范

### 目录组织

```
/InsightCosmos
├─ docs/                        # 文档系统
│   ├─ planning/                # 规划阶段文档
│   │   ├─ phase1_overview.md   # 第一阶段总览
│   │   ├─ agent_design.md      # Agent 设计文档
│   │   └─ tools_spec.md        # 工具规格说明
│   ├─ implementation/          # 实作阶段文档
│   │   ├─ dev_log.md           # 开发日志
│   │   └─ api_reference.md     # API 参考
│   ├─ validation/              # 验证阶段文档
│   │   ├─ test_cases.json      # 测试案例
│   │   └─ eval_config.json     # 评估配置
│   └─ reference/               # 参考资料（已有）
│       ├─ 5D_AI_Agent_Summary.md
│       ├─ adk-速查文檔.html
│       └─ ...
│
├─ src/                         # 源代码
│   ├─ agents/                  # Agent 实现
│   │   ├─ scout_agent.py
│   │   ├─ analyst_agent.py
│   │   └─ curator_agent.py
│   ├─ tools/                   # 工具函数
│   │   ├─ fetcher.py
│   │   ├─ google_search.py
│   │   ├─ embedding.py
│   │   └─ email_sender.py
│   ├─ memory/                  # 记忆层
│   │   ├─ db.py
│   │   └─ schema.sql
│   ├─ orchestrator/            # 编排器
│   │   ├─ daily_runner.py
│   │   └─ weekly_runner.py
│   └─ utils/                   # 工具类
│       ├─ config.py
│       └─ logger.py
│
├─ prompts/                     # Prompt 模板
│   ├─ analyst_prompt.txt
│   ├─ daily_prompt.txt
│   ├─ weekly_prompt.txt
│   └─ reflection_prompt.txt
│
├─ tests/                       # 测试文件
│   ├─ unit/
│   ├─ integration/
│   └─ evaluation/
│
├─ data/                        # 数据存储
│   ├─ insights.db              # SQLite 数据库
│   └─ embeddings/              # Vector 存储
│
├─ .env.example                 # 环境变量模板
├─ .gitignore
├─ requirements.txt             # 依赖清单
├─ README.md                    # 项目说明
├─ claude.md                    # 本文档
└─ main.py                      # 入口文件
```

---

## 🔄 开发节奏：规划→实作→验证

### Phase 1: 规划阶段 (Planning)

**目标**: 在写代码前完成架构设计与文档

**交付物**:
1. `docs/planning/phase1_overview.md` - 第一阶段总览
2. `docs/planning/agent_design.md` - 三大 Agent 详细设计
3. `docs/planning/tools_spec.md` - 工具函数规格
4. `docs/planning/memory_design.md` - Memory 层设计
5. `docs/planning/eval_strategy.md` - 评估策略

**验收标准**:
- [ ] 每个 Agent 的 instruction、tools、output_key 明确
- [ ] 每个工具的输入/输出/错误处理定义清晰
- [ ] Memory schema 完整设计
- [ ] 测试案例清单准备完成

### Phase 2: 实作阶段 (Implementation)

**目标**: 按照规划文档实现代码

**开发顺序**:
1. **Memory Layer** → 先建立数据层
2. **Tools** → 实现工具函数
3. **Scout Agent** → 第一个 Agent
4. **Analyst Agent** → 核心分析逻辑
5. **Curator Agent** → 报告生成
6. **Orchestrator** → 串联整体流程

**开发规范**:
- 每个模块完成后更新 `docs/implementation/dev_log.md`
- 关键代码必须包含 docstring
- 工具函数必须有类型标注

### Phase 3: 验证阶段 (Validation)

**目标**: 确保质量与功能正确性

**验证清单**:
1. **单元测试** - 每个工具函数独立测试
2. **集成测试** - Agent 协作流程测试
3. **ADK Evaluation** - 使用官方评估框架
4. **人工审查** - Sample outputs 质量检查

**交付物**:
- `docs/validation/test_results.md` - 测试报告
- `docs/validation/eval_metrics.md` - 评估指标
- `docs/validation/known_issues.md` - 已知问题清单

---

## 🎯 Phase 1 实施范围

### ✅ 包含功能

**Core Features**:
1. ✅ **Scout Agent** - RSS + Google Search 自动收集
2. ✅ **Analyst Agent** - LLM 分析与优先级评分
3. ✅ **Curator Agent** - Daily Digest + Weekly Report
4. ✅ **Memory Universe** - SQLite + Embedding
5. ✅ **Email Delivery** - SMTP 推送

**Agent Architecture**:
- Sequential Agent（顺序编排）
- LLM Agent（核心推理）
- Tool Integration（工具使用）
- Session Management（会话管理）

**Quality Assurance**:
- LoggingPlugin（日志记录）
- Basic Evaluation（基础评估）

### ❌ 不包含功能（v2/v3）

**暂不实现**:
- ❌ Hunter / Learner / Coordinator Agent（企业版）
- ❌ 自动来源发现与学习
- ❌ 主题偏好自适应
- ❌ 知识图谱（Knowledge Nebula）
- ❌ Multi-user 支持
- ❌ A2A Protocol（跨 Agent 通讯）
- ❌ Vertex AI 部署（本地优先）

---

## 📐 编码标准

### Agent 设计规范

**强制要求**:

```python
# ✅ 好的 Agent 设计
agent = LlmAgent(
    name="ScoutAgent",  # 清晰命名
    model=Gemini(model="gemini-2.5-flash-lite"),  # 指定模型
    instruction="""
    你的任务是从 RSS 和 Google Search 收集 AI 与 Robotics 相关文章。

    步骤：
    1. 使用 fetch_rss 工具获取 RSS 文章
    2. 使用 google_search 工具搜索关键词
    3. 合并结果并去重
    4. 返回结构化的文章列表
    """,  # 详细指令
    tools=[fetch_rss, google_search],  # 工具列表
    output_key="raw_articles"  # 输出键
)
```

**禁止事项**:
```python
# ❌ 避免的设计
agent = Agent(
    instruction="收集文章",  # 指令过于模糊
    tools=[...]  # 未明确工具用途
)
```

### 工具设计规范

**标准模板**:

```python
def tool_name(param: str, tool_context: ToolContext = None) -> dict:
    """
    工具功能描述（LLM 会读取这个）

    Args:
        param: 参数说明
        tool_context: ADK 上下文（可选）

    Returns:
        dict: {
            "status": "success" | "error",
            "data": {...},  # 成功时返回
            "error_message": str,  # 错误时返回
            "suggestion": str  # 错误时的修正建议
        }

    Example:
        >>> tool_name("test")
        {"status": "success", "data": {...}}
    """
    try:
        # 实现逻辑
        result = do_something(param)
        return {"status": "success", "data": result}
    except SpecificError as e:
        return {
            "status": "error",
            "error_type": "specific_error",
            "error_message": str(e),
            "suggestion": "具体的修正建议"
        }
```

**关键要求**:
1. ✅ 完整的 docstring（LLM 依赖此理解工具）
2. ✅ 类型标注（Python Type Hints）
3. ✅ 结构化返回值（dict 格式）
4. ✅ 错误处理与建议（可恢复性）
5. ✅ Example 示例（帮助理解）

### Prompt 设计规范

**存储位置**: `prompts/` 目录

**命名规范**:
- `{agent_name}_prompt.txt` - Agent 主指令
- `{task}_reflection_prompt.txt` - Reflection 提示

**Prompt 结构**:

```
# {Agent Name} Instruction

## 角色定义
你是一个 {角色描述}，专注于 {核心职责}。

## 任务目标
{具体目标说明}

## 执行步骤
1. {步骤 1}
2. {步骤 2}
3. {步骤 3}

## 可用工具
- tool_1: {用途}
- tool_2: {用途}

## 输出格式
{期望的输出结构}

## 质量标准
- 标准 1
- 标准 2

## 示例
Input: {示例输入}
Output: {示例输出}
```

---

## 🔍 质量保证原则

### 可观测性（Observability）

**必须实施**:

```python
from google.adk.plugins import LoggingPlugin

# 所有 Agent 启用日志
agent = LlmAgent(
    plugins=[LoggingPlugin()]
)
```

**日志级别**:
- `DEBUG` - 开发阶段
- `INFO` - 生产环境
- `ERROR` - 错误追踪

### 评估框架（Evaluation）

**测试案例结构**:

```json
{
  "eval_set_id": "insightcosmos_v1",
  "eval_cases": [
    {
      "eval_id": "scout_basic",
      "description": "Scout Agent 基本收集功能",
      "conversation": [
        {
          "user_content": "收集今日 AI 新闻",
          "expected_tools": ["fetch_rss", "google_search"],
          "final_response": {...}
        }
      ]
    }
  ]
}
```

**评估指标**:
- `tool_trajectory_avg_score` >= 0.9（工具使用正确性）
- `response_match_score` >= 0.8（输出质量）

---

## 🚀 部署与运行

### 环境配置

**.env 必需变量**:

```bash
# Google Gemini API (Required)
# Get API Key from: https://aistudio.google.com/apikey
# This single key is used for:
# - LLM inference (Gemini 2.0 Flash)
# - Google Search Grounding (no additional Search Engine ID needed)
GOOGLE_API_KEY=your_gemini_api_key

# Email
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Database
DATABASE_PATH=data/insights.db

# 个人配置
USER_NAME=Ray
USER_INTERESTS=AI,Robotics,Multi-Agent Systems
```

### 运行命令

```bash
# 初始化数据库
python src/memory/db.py

# 运行日报
python orchestrator/daily_runner.py

# 运行周报
python orchestrator/weekly_runner.py

# 运行评估
adk eval src/agents evalset.json --config_file_path=eval_config.json
```

---

## 📚 学习资源参考

### 官方文档
- [ADK 完整文档](https://google.github.io/adk-docs/)
- [Agents 概述](https://google.github.io/adk-docs/agents/)
- [Tools 开发](https://google.github.io/adk-docs/tools/)
- [Memory 系统](https://google.github.io/adk-docs/sessions/memory/)
- [评估框架](https://google.github.io/adk-docs/evaluate/)

### 内部参考
- `docs/reference/5D_AI_Agent_Summary.md` - ADK 学习总结
- `docs/reference/adk-速查文檔.html` - 快速查阅

---

## 🤖 Claude Code 使用指南

### 角色定位

Claude Code 作为开发助手，应该：

1. **理解上下文** - 阅读本文档理解项目整体架构
2. **遵循规范** - 严格按照编码标准生成代码
3. **文档优先** - 先写文档再写代码
4. **质量保证** - 主动建议测试与评估
5. **增量开发** - 按照 Planning → Implementation → Validation 节奏

### 常见任务模板

**任务 1: 设计新 Agent**
```
请按照 docs/planning/agent_design.md 模板，设计 {AgentName}:
1. 明确职责与目标
2. 定义 instruction
3. 列出需要的 tools
4. 设计输出格式
5. 准备测试案例
```

**任务 2: 实现工具函数**
```
请实现 {tool_name} 工具：
1. 遵循 claude.md 中的工具设计规范
2. 包含完整 docstring
3. 结构化返回值
4. 错误处理与建议
5. 提供使用示例
```

**任务 3: 更新文档**
```
完成 {feature} 后，更新：
1. docs/implementation/dev_log.md
2. docs/implementation/api_reference.md
3. README.md（如有必要）
```

---

## 🎯 成功标准

### Phase 1 完成定义

**功能完整性**:
- [x] Scout Agent 能自动收集文章
- [x] Analyst Agent 能分析并打分
- [x] Curator Agent 能生成日报/周报
- [x] Memory 能持久化存储
- [x] Email 能成功发送

**质量标准**:
- [x] 所有 Agent 有完整文档
- [x] 所有工具有测试案例
- [x] 评估通过率 >= 80%
- [x] 日志可追踪完整流程
- [x] 错误处理覆盖主要场景

**用户体验**:
- [x] 日报内容有价值（5-10 条高质量信息）
- [x] 周报能识别趋势（2-3 个主题）
- [x] 报告格式清晰易读
- [x] 系统能自动运行（无需人工干预）

---

## 📝 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| 1.1 | 2025-11-23 | 迁移到 Gemini Search Grounding，移除 Custom Search Engine ID 要求 |
| 1.0 | 2025-11-19 | 初始版本，定义 Phase 1 规范 |

---

## 🔗 相关文档

- `README.md` - 项目说明与快速开始
- `docs/planning/phase1_overview.md` - 第一阶段详细规划
- `docs/reference/5D_AI_Agent_Summary.md` - ADK 技术学习总结

---

**最后更新**: 2025-11-19
**维护者**: Ray 张瑞涵
**项目仓库**: InsightCosmos
