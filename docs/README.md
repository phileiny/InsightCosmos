# InsightCosmos 文档系统

> **建立日期**: 2025-11-19
> **文档版本**: 1.0
> **维护者**: Ray 张瑞涵

---

## 📚 文档组织结构

```
docs/
├─ README.md                    # 本文件 - 文档系统说明
├─ project_breakdown.md         # Phase 1 项目拆解清单
│
├─ planning/                    # 规划阶段文档
│   ├─ _template_stage.md      # 规划文档标准模板
│   ├─ stage1_foundation.md    # Stage 1: 基础设施层
│   ├─ stage2_memory.md        # Stage 2: Memory Layer
│   ├─ stage3_rss_tool.md      # Stage 3: RSS Fetcher
│   ├─ ...                     # 其他 Stage 规划文档
│   └─ stage12_qa.md           # Stage 12: QA & Optimization
│
├─ implementation/              # 实作阶段文档
│   ├─ dev_log.md              # 开发日志（持续更新）
│   ├─ stage1_notes.md         # Stage 1 实作笔记
│   ├─ stage2_notes.md         # Stage 2 实作笔记
│   └─ ...                     # 其他 Stage 实作笔记
│
├─ validation/                  # 验证阶段文档
│   ├─ stage1_test_report.md   # Stage 1 测试报告
│   ├─ stage2_test_report.md   # Stage 2 测试报告
│   ├─ ...                     # 其他 Stage 测试报告
│   └─ final_validation.md     # 最终验收报告
│
└─ reference/                   # 参考资料
    ├─ 5D_AI_Agent_Summary.md  # ADK 学习总结
    ├─ adk-速查文檔.html        # ADK 快速参考
    ├─ 智覺_架構圖_v1.md        # 架构图
    ├─ 智覺_Spec_v1.md          # 规格说明
    └─ InsightCosmos – Capstone Full Writeup.md
```

---

## 🔄 开发节奏说明

InsightCosmos 采用**细粒度迭代开发**模式：

```
Phase 1 拆解为 12 个 Stage
                ↓
每个 Stage 遵循：规划 → 实作 → 验证
                ↓
只有通过验证才进入下一个 Stage
```

### 为什么这样做？

1. **降低风险** - 每个小阶段独立可控
2. **快速反馈** - 及时发现和修正问题
3. **持续交付** - 每个阶段都有可用的产出
4. **易于管理** - 清晰的进度追踪

---

## 📋 文档使用指南

### 开始新的 Stage

1. **复制模板**:
   ```bash
   cp docs/planning/_template_stage.md docs/planning/stage{N}_{name}.md
   ```

2. **填写规划文档**:
   - 明确目标与输入输出
   - 设计技术方案
   - 定义测试策略
   - 设定验收标准

3. **评审规划**:
   - 自我检查：是否所有章节都完整？
   - 可行性评估：技术方案是否可行？
   - 依赖确认：前置依赖是否满足？

### 实作阶段

1. **按照规划文档实施**

2. **更新开发日志**:
   ```markdown
   # docs/implementation/dev_log.md

   ## Stage {N}: {Name} - {Date}

   ### 今日进展
   - {具体完成的工作}

   ### 遇到的问题
   - {问题描述 + 解决方案}

   ### 明日计划
   - {下一步工作}
   ```

3. **记录实作笔记**:
   - 关键技术决策
   - 代码设计思路
   - 遇到的坑与解决方案

### 验证阶段

1. **执行所有测试**:
   - 单元测试
   - 集成测试
   - ADK Evaluation（如适用）

2. **编写测试报告**:
   ```markdown
   # docs/validation/stage{N}_test_report.md

   ## 测试执行结果
   - 单元测试: X/Y passed
   - 集成测试: X/Y passed

   ## 验收标准检查
   - [x] 标准 1
   - [x] 标准 2

   ## 发现的问题
   - {问题列表}

   ## 结论
   - [ ] 通过验收，可进入下一阶段
   - [ ] 需要修正后重新验证
   ```

3. **验收通过才进入下一 Stage**

---

## 📊 当前进度跟踪

### Phase 1 总体进度

| Stage | 名称 | 状态 | 规划 | 实作 | 验证 |
|-------|------|------|------|------|------|
| 1 | Foundation | 未开始 | ⬜ | ⬜ | ⬜ |
| 2 | Memory Layer | 未开始 | ⬜ | ⬜ | ⬜ |
| 3 | RSS Tool | 未开始 | ⬜ | ⬜ | ⬜ |
| 4 | Search Tool | 未开始 | ⬜ | ⬜ | ⬜ |
| 5 | Scout Agent | 未开始 | ⬜ | ⬜ | ⬜ |
| 6 | Content Extraction | 未开始 | ⬜ | ⬜ | ⬜ |
| 7 | Analyst Agent | 未开始 | ⬜ | ⬜ | ⬜ |
| 8 | Curator Daily | 未开始 | ⬜ | ⬜ | ⬜ |
| 9 | Daily Pipeline | 未开始 | ⬜ | ⬜ | ⬜ |
| 10 | Curator Weekly | 未开始 | ⬜ | ⬜ | ⬜ |
| 11 | Weekly Pipeline | 未开始 | ⬜ | ⬜ | ⬜ |
| 12 | QA & Optimization | 未开始 | ⬜ | ⬜ | ⬜ |

**图例**: ⬜ 未开始 | 🟨 进行中 | ✅ 已完成

（此表格应在每个 Stage 完成后更新）

---

## 🎯 质量标准

### 规划文档质量标准

- [ ] 使用标准模板
- [ ] 所有章节内容完整
- [ ] 输入/输出定义清晰
- [ ] 接口设计具体可实作
- [ ] 测试策略完整
- [ ] 验收标准可衡量

### 实作代码质量标准

- [ ] 遵循 `claude.md` 编码规范
- [ ] 所有函数有 docstring
- [ ] 所有函数有类型标注
- [ ] 错误处理完善
- [ ] 单元测试覆盖率 >= 80%

### 验证文档质量标准

- [ ] 测试结果完整记录
- [ ] 验收标准逐项检查
- [ ] 问题清单详细
- [ ] 结论明确

---

## 🔗 相关文档

### 核心文档

- `../README.md` - 项目说明
- `../claude.md` - 项目一致性指南
- `project_breakdown.md` - 项目拆解清单

### 参考资料

- `reference/5D_AI_Agent_Summary.md` - ADK 完整学习笔记
- `reference/adk-速查文檔.html` - ADK 快速查阅

---

## 📝 文档维护

### 更新频率

| 文档类型 | 更新频率 | 负责人 |
|---------|---------|--------|
| 规划文档 | 每个 Stage 开始前 | 开发者 |
| 开发日志 | 每天 | 开发者 |
| 实作笔记 | 实作阶段完成时 | 开发者 |
| 测试报告 | 验证阶段完成时 | 开发者 |
| 进度跟踪 | 每个 Stage 完成后 | 开发者 |

### 文档评审

- **自我评审**: 完成后检查完整性和准确性
- **定期回顾**: 每周回顾文档与代码的一致性

---

## 💡 最佳实践

### 1. 文档先行

在写代码前完成规划文档，确保思路清晰。

### 2. 同步更新

代码变更时及时更新文档，保持一致性。

### 3. 记录决策

关键技术决策要记录在实作笔记中，包括：
- 为什么选择这个方案？
- 有哪些替代方案？
- 权衡了哪些因素？

### 4. 保存问题

遇到的问题和解决方案要记录下来，避免重复踩坑。

### 5. 持续改进

定期回顾文档模板和流程，不断优化。

---

## 🚀 快速开始

### 立即开始 Stage 1

1. 阅读 `project_breakdown.md` 了解整体规划
2. 创建 `docs/planning/stage1_foundation.md`（使用模板）
3. 填写完整的规划文档
4. 开始实作

### 后续 Stage

每个 Stage 遵循相同流程：
```
规划 (Planning) → 实作 (Implementation) → 验证 (Validation) → 下一 Stage
```

---

**最后更新**: 2025-11-19
**维护者**: Ray 张瑞涵
**版本**: 1.0
