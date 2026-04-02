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

## 推荐命令

```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/run_stage1_intake.py
```

> brief / draft 使用项目内当前控制文件执行；必须遵守：
> `引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`

## 交付要求

- `intake_manifest.json`
- `brief_manifest.json`
- `draft_manifest.json`
- 每篇初稿独立文档，便于编辑并行审核

## 强约束

1. `draft` 仅写标准事实稿，不做 DNA 改写。
2. 数据与引用必须可追溯，不能用内部统计替代外部证据。
3. 不同选题严禁混到同一正文。

