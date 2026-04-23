---
name: dasheng-stage-intake-brief-draft
description: Use when executing the upstream stages (intake, brief, draft) of Dasheng workflow and producing editor-ready topic sets and standard drafts.
---

# Dasheng Stage: Intake + Brief + Draft

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`

## 阶段目标

- `intake`：采集并生成来源底稿/统计报告
- `brief`：生成 8-10 个编辑候选题（人工指定题强制入池）
- `draft`：每题标准初稿（事实稿，不注入平台风格）

## 重要更新

### Brief 环节已升级为 AI 驱动

**旧系统问题**：
- 使用硬编码模板拼接生成选题标题
- 标题生硬，逻辑关系不清
- 例如："外交部、伊朗：事件升级之外，长期秩序成本在怎样上升"

**新系统优势**：
- 使用 AI 理解事件因果关系
- 生成自然语言标题
- 提供完整的论证和证据需求
- 推荐写作框架和内容增强策略

**使用新系统**：
```bash
# 推荐：使用 dasheng-stage-brief-ai skill
# 该 skill 会生成更自然、有洞察力的选题
```

详见：`../dasheng-stage-brief-ai/SKILL.md`

### Draft 环节已集成框架系统

**新增能力**：
- 根据 brief 推荐的框架生成结构化初稿
- 应用内容增强策略（角度发现、密度强化、细节锚定、真实体感）
- 自动验证 draft 质量（字数、结构、引用等）

**使用框架驱动的 draft**：
```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/draft_with_framework.py \
  --brief-dir "产物/02_Brief/2026-04-04_204231_ai" \
  --output-dir "产物/03_Draft/2026-04-04_204231"
```

## 推荐命令

### Intake
```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/run_stage1_intake.py
```

### Brief（推荐使用 AI 系统）
```bash
# 方式 1：通过 skill 调用（推荐）
# 使用 dasheng-stage-brief-ai 从最新的 intake 数据生成选题

# 方式 2：直接运行旧系统（不推荐，标题生硬）
python3 scripts/phase2_rebuilder.py \
  "产物/01_内容采集/2026-04-04_204231/raw/intake_records.json" \
  "产物/02_Brief/2026-04-04_204231"
```

### Draft（推荐使用框架驱动）
```bash
# 方式 1：框架驱动（推荐）
python3 scripts/draft_with_framework.py \
  --brief-dir "产物/02_Brief/2026-04-04_204231_ai" \
  --output-dir "产物/03_Draft/2026-04-04_204231"

# 方式 2：传统方式
# 使用项目内现有的 draft 生成脚本
```

> brief / draft 使用项目内当前控制文件执行；必须遵守：
> `引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`

## 交付要求

- `intake_manifest.json`
- `brief_manifest.json`（新增字段：generation_method, recommended_framework, recommended_strategy）
- `draft_manifest.json`（新增字段：framework, strategy, validation）
- 每篇初稿独立文档，便于编辑并行审核

## 强约束

1. `draft` 仅写标准事实稿，不做 DNA 改写。
2. 数据与引用必须可追溯，不能用内部统计替代外部证据。
3. 不同选题严禁混到同一正文。
4. **Brief 必须使用 AI 系统**：旧的规则系统生成的标题质量不符合要求。
5. **Draft 应遵循推荐框架**：brief 环节推荐的框架和策略应在 draft 中体现。

## 参考文档

- Brief AI 生成指南：`../dasheng-stage-brief-ai/references/ai-generation-guide.md`
- 选题评估框架：`../dasheng-stage-brief-ai/references/topic-evaluation.md`
- 写作框架：`../dasheng-stage-rewrite/references/frameworks.md`
- 内容增强策略：`../dasheng-stage-rewrite/references/content-enhance.md`

