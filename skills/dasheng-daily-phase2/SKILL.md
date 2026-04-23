---
name: dasheng-daily-phase2
description: Use when the workflow enters Stage 2 Brief and the system must generate 8-10 AI-native candidate topic cards from canonical intake evidence under the current Dasheng mainline.
---

# dasheng-daily-phase2

## 目标

这是本仓库 Stage 2 的唯一正式 Brief skill。

职责只有两层：

- 代码层：读取 intake、整理证据包、做显性噪音隔离、校验结构、落盘
- AI 层：直接生成最终独立题卡

失败就失败，不再回退规则造题。

## canonical 输入

按这个优先级读取：

1. `brief_input.json`
2. `channel_top10.json`
3. `event_clusters.json`
4. `raw/intake_records.json`

默认来源目录：

- `{DASHENG_ROOT}/产物/01_内容采集/{run_id}/`

## canonical 输出

输出目录：

- `{DASHENG_ROOT}/产物/02_内容聚合及选题分析/{run_id}/`

标准产物：

1. `02_编辑Brief库.md`
2. `02_研究Brief库.md`
3. `02_编辑Brief_报告.md`
4. `topic_cards.json`
5. `selected_topics.template.json`
6. `selected_topics.json`
7. `brief_manifest.json`

## 当前规则

- 输出是 **8-10 个平铺独立题卡**
- 不再强制母题 / 变体作为业务主语义
- AI 可以跨渠道、跨事件综合提炼，但不得脱离 intake 证据池
- 高优先证据池按 `信号强度 × 逻辑独立性 × 主题新颖度` 做弱重排
- 不做硬题材配额，但会对同一逻辑链和高重叠签名做边际递减
- AI 返回的 `existing_evidence` 会回贴到 canonical evidence，并自动补齐 `logic_chain_id`
- 如果同一逻辑链占比超过半数，阶段直接失败

## 执行入口

### 指定 run_id，按 canonical intake 衔接

```bash
node ../dasheng-daily-phase2/index.js --run-id <run_id>
```

### 指定 intake 文件

```bash
node ../dasheng-daily-phase2/index.js \
  {DASHENG_ROOT}/产物/01_内容采集/<run_id>/raw/intake_records.json
```

### 带手动指定题

```bash
node ../dasheng-daily-phase2/index.js \
  {DASHENG_ROOT}/产物/01_内容采集/<run_id>/raw/intake_records.json \
  --manual-topic "你的人工题目"
```

## 参考资料

- Prompt 规则：`../../引擎/03_全链路SOP工作流/02_Brief_AI生成规则.md`
- AI 选题指南：`references/ai-generation-guide.md`
- 选题评估：`references/topic-evaluation.md`
- 写作框架：`references/frameworks.md`
- 内容增强：`references/content-enhance.md`

## 实现说明

- 主脚本：`../../scripts/phase2_rebuilder.py`
- 主链入口：`python3 ../../scripts/run_mainline_stage.py brief --run-id <run_id>`
- Schema：`brief_card_schema.json`
- 正式阶段状态：以 `brief_manifest.json` 为准

## 迁移说明

导出仓 `dasheng-stage-brief-ai` 的文档能力已被吸收到这里。

以后不要再把：

- `dasheng-stage-brief-ai`
- `dasheng-daily-brief`
- `dasheng-daily-clustering`

当成正式 Brief 入口。
