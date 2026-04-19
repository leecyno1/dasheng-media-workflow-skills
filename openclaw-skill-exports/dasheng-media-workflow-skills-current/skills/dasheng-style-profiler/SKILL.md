---
name: dasheng-style-profiler
description: Use when building or refreshing a reusable author DNA from historical articles so rewrite can inherit real style patterns instead of relying only on preset personas.
---

# Dasheng Style Profiler

## 目标

把作者文风沉淀成可复用的 DNA 资产，供 rewrite 阶段调用。

## 输入

- 作者名
- 平台类型
- 3-10 篇参考文章
- 可选样本索引：由抓取或整理脚本提供

## 本地实现

- 统计入口：`/Volumes/PSSD/Projects/公众号文章/scripts/style_ingest.py`
- 风格画像目标目录：`/Volumes/PSSD/Projects/公众号文章/风格库/{作者}/`

## 输出

- `风格画像.md`
- `style_dna.yaml`（如后续扩展）
- 样本分析报告

## 规则

- 至少覆盖 14 维分析
- 必须单独总结：
  - 标点偏好
  - 分块习惯
  - 段落配方
  - 叙述方法体系
  - 内容推进方式
- 必须经过用户校准后再固化

## 参考

- `references/style-14d-framework.md`
- `references/calibration-checklist.md`
- `references/style-dna-default-template.md`
- `references/style-profile-template.md`

