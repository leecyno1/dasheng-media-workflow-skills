---
name: dasheng-daily-brief
description: Use only when an old pipeline still explicitly calls the legacy brief step; the current standard merges editor brief generation into dasheng-daily-phase2
---

# dasheng-daily-brief

该 skill 现为兼容层。

## 当前标准

新流程下，`Brief` 已并入第 2 阶段 `dasheng-daily-phase2`，标准交付为：

- `02_编辑Brief库.md`
- `02_编辑Brief_报告.md`
- `brief_manifest.json`

因此，默认不要再把本 skill 当成独立的“单题评分环节”。

## 何时仍可使用

- 历史工作流还在读取旧版 `ContentBrief` JSON
- 某些旧脚本仍依赖 `dasheng-daily-brief/index.js`
- 你在做旧产物回放，需要兼容历史字段

## 不再推荐的旧习惯

- 不再以“多维评分表”作为编辑主交付
- 不再以单题打分替代候选题池
- 不再让 Brief 独立于 Stage 2 聚类结果之外运行

## 推荐替代

- 主入口：`skills/dasheng-daily-phase2/`
- 标准模板：`引擎/03_全链路SOP工作流/02_标准编辑Brief模板.md`
- Stage 2 Prompt：`引擎/03_全链路SOP工作流/02_内容聚合及选题分析_prompt.md`
