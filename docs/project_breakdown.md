# InsightCosmos Phase 1 项目拆解清单

> **目的**: 将 Phase 1 拆解为可独立实作的小阶段
> **原则**: 每个阶段独立完成"规划→实作→验证"循环
> **创建日期**: 2025-11-19

---

## 🎯 拆解原则

1. **独立性** - 每个阶段可以独立规划、实作、验证
2. **可测试** - 每个阶段完成后有明确的验证标准
3. **渐进式** - 后续阶段依赖前面阶段的产出
4. **小而精** - 每个阶段控制在 2-3 天完成

---

## 📦 Phase 1 拆解为 8 个小阶段

### Stage 1: 基础设施层 (Foundation)

**目标**: 建立项目基础框架

**包含内容**:
- 项目目录结构
- 环境配置（.env）
- 依赖管理（requirements.txt）
- 基础工具类（logger, config）

**规划文档**: `docs/planning/stage1_foundation.md`

**实作产出**:
```
/InsightCosmos
├─ src/
│   └─ utils/
│       ├─ config.py
│       └─ logger.py
├─ .env.example
├─ requirements.txt
└─ main.py (入口占位)
```

**验证标准**:
- [ ] 能成功加载 .env 配置
- [ ] Logger 能正常输出日志
- [ ] requirements.txt 能成功安装所有依赖

**预计时间**: 0.5 天

---

### Stage 2: Memory Layer (数据层)

**目标**: 建立数据存储与检索能力

**包含内容**:
- SQLite schema 设计
- 数据库初始化脚本
- CRUD 操作函数
- Embedding 存储机制

**规划文档**: `docs/planning/stage2_memory.md`

**实作产出**:
```
src/
└─ memory/
    ├─ schema.sql
    ├─ db.py
    └─ embedding_store.py
```

**验证标准**:
- [ ] 数据库能成功创建所有表
- [ ] 能插入、查询、更新文章数据
- [ ] Embedding 能成功存储和检索
- [ ] 单元测试通过率 100%

**预计时间**: 1 天

---

### Stage 3: RSS Fetcher Tool (RSS 工具)

**目标**: 实现 RSS 文章抓取功能

**包含内容**:
- RSS feed 解析
- 文章元数据提取
- 错误处理
- 去重逻辑

**规划文档**: `docs/planning/stage3_rss_tool.md`

**实作产出**:
```
src/
└─ tools/
    ├─ fetcher.py
    └─ __init__.py
```

**验证标准**:
- [ ] 能成功解析指定 RSS feeds
- [ ] 返回结构化的文章列表
- [ ] 错误处理覆盖：无效 URL、网络超时、解析失败
- [ ] 工具文档完整（docstring）
- [ ] 单元测试通过

**预计时间**: 1 天

---

### Stage 4: Google Search Tool (搜索工具)

**目标**: 实现 Google Search 功能

**包含内容**:
- Google Custom Search API 集成
- 搜索结果解析
- 配额管理
- 结果去重

**规划文档**: `docs/planning/stage4_search_tool.md`

**实作产出**:
```
src/
└─ tools/
    └─ google_search.py
```

**验证标准**:
- [ ] 能成功调用 Google Search API
- [ ] 返回结构化搜索结果
- [ ] 配额超限时有友好错误提示
- [ ] 与 RSS 结果能合并去重
- [ ] 单元测试通过

**预计时间**: 1 天

---

### Stage 5: Scout Agent (探索代理)

**目标**: 实现信息收集 Agent

**包含内容**:
- Scout Agent 定义
- 工具编排逻辑
- 输出格式化
- 基础测试

**规划文档**: `docs/planning/stage5_scout_agent.md`

**实作产出**:
```
src/
└─ agents/
    ├─ scout_agent.py
    └─ __init__.py

prompts/
└─ scout_prompt.txt
```

**验证标准**:
- [ ] Agent 能调用 RSS + Search 工具
- [ ] 能正确去重和限制数量（30 篇）
- [ ] 输出格式符合规范
- [ ] ADK Evaluation 通过（tool_trajectory >= 0.9）
- [ ] 端到端测试：输入空 → 输出 30 篇文章

**预计时间**: 1.5 天

---

### Stage 6: Content Extraction Tool (内容提取)

**目标**: 抓取文章完整内容

**包含内容**:
- URL 内容抓取
- HTML 解析与清洗
- 主体内容提取
- 反爬虫处理

**规划文档**: `docs/planning/stage6_content_tool.md`

**实作产出**:
```
src/
└─ tools/
    └─ content_extractor.py
```

**验证标准**:
- [ ] 能提取主流网站的文章正文
- [ ] 过滤广告、导航等无关内容
- [ ] 处理常见反爬虫机制（User-Agent, 延迟）
- [ ] 错误处理：404、403、解析失败
- [ ] 单元测试覆盖多种网站类型

**预计时间**: 1 天

---

### Stage 7: Analyst Agent (分析代理)

**目标**: 实现文章深度分析功能

**包含内容**:
- Analyst Agent 定义
- LLM 分析 Prompt 设计
- Reflection 机制
- Priority Scoring 逻辑
- Embedding 生成

**规划文档**: `docs/planning/stage7_analyst_agent.md`

**实作产出**:
```
src/
└─ agents/
    └─ analyst_agent.py

src/
└─ tools/
    ├─ embedding.py
    └─ memory_save.py

prompts/
├─ analyst_prompt.txt
└─ reflection_prompt.txt
```

**验证标准**:
- [ ] 能生成高质量的 TL;DR
- [ ] Key Ideas 提取准确
- [ ] Priority Score 合理（手工验证 10 篇）
- [ ] Reflection 能修正明显错误
- [ ] Embedding 成功存储到 Memory
- [ ] ADK Evaluation 通过（response_match >= 0.8）

**预计时间**: 2 天

---

### Stage 8: Curator Daily Agent (日报生成)

**目标**: 实现每日情报摘要生成

**包含内容**:
- Curator Daily Agent 定义
- 文章筛选与排序逻辑
- 报告格式化（HTML + Text）
- Email 发送工具

**规划文档**: `docs/planning/stage8_curator_daily.md`

**实作产出**:
```
src/
└─ agents/
    └─ curator_daily.py

src/
└─ tools/
    ├─ format_digest.py
    └─ email_sender.py

prompts/
└─ daily_prompt.txt
```

**验证标准**:
- [ ] 能筛选 Top 5-10 篇文章
- [ ] HTML 格式美观易读
- [ ] Text 格式适合纯文本阅读
- [ ] Email 成功发送到指定邮箱
- [ ] 端到端测试：分析结果 → 日报邮件

**预计时间**: 1.5 天

---

### Stage 9: Daily Pipeline 集成 (日报流程)

**目标**: 串联 Scout → Analyst → Curator Daily

**包含内容**:
- SequentialAgent 编排
- Daily Orchestrator
- 错误处理与重试
- 日志与监控

**规划文档**: `docs/planning/stage9_daily_pipeline.md`

**实作产出**:
```
src/
└─ orchestrator/
    └─ daily_runner.py
```

**验证标准**:
- [ ] 端到端流程顺利运行
- [ ] 能处理中间步骤失败（重试机制）
- [ ] 完整日志可追踪
- [ ] 实际运行 7 天无故障
- [ ] 日报内容质量达标（人工验收）

**预计时间**: 1 天

---

### Stage 10: Curator Weekly Agent (周报生成)

**目标**: 实现每周深度报告生成

**包含内容**:
- Memory 查询工具
- Vector Clustering 工具
- Curator Weekly Agent 定义
- 趋势分析 Prompt 设计

**规划文档**: `docs/planning/stage10_curator_weekly.md`

**实作产出**:
```
src/
└─ agents/
    └─ curator_weekly.py

src/
└─ tools/
    ├─ memory_query.py
    └─ clustering.py

prompts/
└─ weekly_prompt.txt
```

**验证标准**:
- [ ] 能检索过去 7 天的文章
- [ ] Clustering 能识别 2-3 个主题
- [ ] 趋势分析有深度洞察
- [ ] 行动建议具体可执行
- [ ] 周报格式清晰美观

**预计时间**: 2 天

---

### Stage 11: Weekly Pipeline 集成 (周报流程)

**目标**: 完成周报自动化流程

**包含内容**:
- SequentialAgent 编排
- Weekly Orchestrator
- 定时任务配置

**规划文档**: `docs/planning/stage11_weekly_pipeline.md`

**实作产出**:
```
src/
└─ orchestrator/
    └─ weekly_runner.py
```

**验证标准**:
- [ ] 端到端流程顺利运行
- [ ] 周报内容质量达标
- [ ] 能在每周日自动触发

**预计时间**: 0.5 天

---

### Stage 12: 质量保证与优化 (QA & Optimization)

**目标**: 完善测试、评估、文档

**包含内容**:
- ADK Evaluation 完整配置
- 测试案例补充
- 性能优化
- 文档完善

**规划文档**: `docs/planning/stage12_qa.md`

**实作产出**:
```
tests/
├─ evaluation/
│   ├─ evalset.json
│   └─ eval_config.json
└─ integration/
    └─ test_full_pipeline.py

docs/
├─ implementation/
│   ├─ dev_log.md
│   └─ api_reference.md
└─ validation/
    └─ test_results.md
```

**验证标准**:
- [ ] 所有 Agent 评估通过
- [ ] 集成测试覆盖率 >= 80%
- [ ] 性能符合预期（日报 < 5 分钟）
- [ ] 文档完整且准确

**预计时间**: 2 天

---

## 📋 总体时间表

| 阶段 | 名称 | 预计时间 | 累计时间 |
|------|------|---------|---------|
| Stage 1 | Foundation | 0.5 天 | 0.5 天 |
| Stage 2 | Memory Layer | 1 天 | 1.5 天 |
| Stage 3 | RSS Tool | 1 天 | 2.5 天 |
| Stage 4 | Search Tool | 1 天 | 3.5 天 |
| Stage 5 | Scout Agent | 1.5 天 | 5 天 |
| Stage 6 | Content Extraction | 1 天 | 6 天 |
| Stage 7 | Analyst Agent | 2 天 | 8 天 |
| Stage 8 | Curator Daily | 1.5 天 | 9.5 天 |
| Stage 9 | Daily Pipeline | 1 天 | 10.5 天 |
| Stage 10 | Curator Weekly | 2 天 | 12.5 天 |
| Stage 11 | Weekly Pipeline | 0.5 天 | 13 天 |
| Stage 12 | QA & Optimization | 2 天 | 15 天 |

**总计**: 约 15 天（3 周）

---

## 🔄 每个小阶段的标准流程

### 1. 规划阶段 (Planning)

**输入**: 上一阶段的产出 + 当前阶段目标

**产出**: `docs/planning/stage{N}_{name}.md`

**内容包含**:
- 目标说明
- 输入/输出定义
- 技术设计
- 接口规范
- 测试案例设计
- 验收标准

**时间**: 约 20% 阶段时间

---

### 2. 实作阶段 (Implementation)

**输入**: 规划文档

**产出**: 代码 + 单元测试

**开发规范**:
- 遵循 `claude.md` 编码标准
- 完整的 docstring
- 类型标注
- 错误处理

**时间**: 约 60% 阶段时间

---

### 3. 验证阶段 (Validation)

**输入**: 实作产出

**产出**: 测试报告 + 验证文档

**验证内容**:
- 单元测试通过
- 集成测试通过
- ADK Evaluation（如适用）
- 人工验收（如适用）

**时间**: 约 20% 阶段时间

---

## 📁 文档组织结构

```
docs/
├─ planning/                    # 每个 Stage 的规划文档
│   ├─ stage1_foundation.md
│   ├─ stage2_memory.md
│   ├─ stage3_rss_tool.md
│   ├─ ...
│   └─ stage12_qa.md
│
├─ implementation/              # 实作过程文档
│   ├─ dev_log.md              # 开发日志（持续更新）
│   └─ stage{N}_notes.md       # 各阶段实作笔记
│
├─ validation/                  # 验证结果文档
│   ├─ stage{N}_test_report.md # 各阶段测试报告
│   └─ final_validation.md     # 最终验收报告
│
└─ reference/                   # 参考资料（已有）
    ├─ 5D_AI_Agent_Summary.md
    └─ ...
```

---

## 🎯 下一步行动

1. **立即开始**: Stage 1 - Foundation
   - 创建 `docs/planning/stage1_foundation.md`
   - 规划基础设施层的详细设计

2. **准备工作**:
   - 确认所有必要的 API Keys 已获取
   - 准备测试用的 RSS feeds 列表
   - 准备测试用的 Search 关键词

3. **建立节奏**:
   - 每个 Stage 完成后更新 `dev_log.md`
   - 每个 Stage 通过验证后才开始下一个
   - 保持文档与代码同步

---

**维护者**: Ray 张瑞涵
**最后更新**: 2025-11-19
**当前状态**: 等待开始 Stage 1
