---
name: dasheng-daily-clustering
description: Use only when an old Dasheng pipeline still explicitly calls the legacy clustering wrapper; the current Stage 2 external entry is dasheng-daily-phase2 under dasheng-media-sop.
---

# dasheng-daily-clustering

## 状态

`legacy adapter / 不再对外作为主入口`

## 当前定位

这个 skill 曾经承担“聚类 + Brief 强化”的对外入口职责。

现在它已经降级为：

- 旧流程兼容层
- Stage 2 的历史别名

默认不要再直接从这里进入。

## 当前标准入口

- 总控入口：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/SKILL.md`
- Stage 2 正式入口：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-phase2/SKILL.md`

## 使用规则

只有下面两种情况才保留使用价值：

- 旧脚本还在显式调用 `dasheng-daily-clustering`
- 需要回放历史产物，并保持历史文件名兼容

除此以外，一律转到 `dasheng-daily-phase2`。

## 标准输出应以新接口为准

- `02_编辑Brief库.md`
- `02_编辑Brief_报告.md`
- `brief_manifest.json`

## 备注

本 skill 不再单独定义新的阶段语义。
阶段定义以：

- `/Volumes/PSSD/Projects/公众号文章/引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`

为准。
