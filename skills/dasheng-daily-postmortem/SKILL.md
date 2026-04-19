---
name: dasheng-daily-postmortem
description: Use when the workflow enters Stage 7 postmortem and published content needs to be evaluated with performance data, accuracy checks, and knowledge-base writeback suggestions.
---

# dasheng-daily-postmortem

## 状态

`internal module / Stage 7 执行层`

## 当前定位

这是当前主链应保留的内部执行模块。

它负责在发布后接收平台表现数据，形成复盘判断，但不负责总控调度。

## 当前标准入口

- 总控入口：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/SKILL.md`

## 标准职责

- 汇总浏览、互动、传播等数据
- 解释预测偏差与结构性误判
- 输出继续 / 停止 / 测试建议
- 形成可回写的知识条目建议

## 标准交付

- `08_复盘报告.md`
- `08_L1回写建议.md`
- `postmortem_manifest.json`

## 现阶段限制

- 当前可用作原型或半自动复盘层
- 真实平台数据闭环仍需继续增强
