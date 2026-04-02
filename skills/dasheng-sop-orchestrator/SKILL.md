---
name: dasheng-sop-orchestrator
description: Use when running, resuming, or auditing the full Dasheng 7-stage media workflow with strict stage contracts and delivery outputs.
---

# Dasheng SOP Orchestrator

## 目的

统一调度 7 阶段创作流，防止越级、混稿、漏交付。

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`

## 固定主链

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

## 执行规则

1. 先识别当前阶段（用户说“继续/开始某阶段”时不得猜错阶段）。
2. 只调用当前阶段技能，不提前产出下游正式交付。
3. 每阶段必须产出文档 + manifest。
4. 多选题必须分题独立目录，禁止混稿。

## 阶段路由

- `intake/brief/draft` -> `dasheng-stage-intake-brief-draft`
- `material` -> `dasheng-stage-material-refill`
- `rewrite` -> `dasheng-stage-rewrite`
- `publish` -> `dasheng-stage-publish-video`
- `postmortem` -> 按项目复盘约定执行（可沿用现有复盘脚本）

## 入口校验

执行前先检查：

- `${DASHENG_WORKSPACE}/引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`
- `${DASHENG_WORKSPACE}/skills/dasheng-media-sop/SKILL.md`

## 每日首跑自检（强制）

首次运行当天任务前，先执行一次最小自检并记录：

- 自检提示词：`SMOKE_PROMPTS.md` 的“全链路最小自检”
- 交付：`smoke_report.md`（仅状态、风险、阻塞，不产出正式稿件）
