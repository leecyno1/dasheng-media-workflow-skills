---
name: dasheng-daily-draft
description: Use only when replaying a legacy Dasheng draft step; the standard Draft stage is now governed by dasheng-media-sop and the stage interface documents rather than this historical skill entry.
---

# dasheng-daily-draft

## 状态

`historical module / 已退出主链`

## 当前定位

这个 skill 属于旧版 `outline -> draft -> final` 链路中的 Draft 节点。

在当前正式工作流里：

- `draft` 仍然存在
- 但不再通过本历史 skill 作为主入口

## 当前标准入口

- 总控入口：`../dasheng-media-sop/SKILL.md`
- 阶段接口：`../../引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`

## 当前标准 Draft 规则

- 生成标准底稿，不注入平台腔
- 不注入账号 DNA
- 默认字数：`4000-8000`
- 默认结构：`开篇 + 三段论 + 结尾` 或 `开篇 + 4 章 + 结尾`
- 一级标题默认不超过 `4` 个
- 交付物：
  - `03_标准初稿_<topic>.md`
  - `04_初稿_报告.md`
  - `draft_manifest.json`

## 何时仍可使用

- 回放历史产物
- 排查旧飞书链路
- 对照旧版自动化生成行为

除此以外，不再作为新项目入口。
