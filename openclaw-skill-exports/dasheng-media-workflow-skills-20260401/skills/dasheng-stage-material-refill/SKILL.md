---
name: dasheng-stage-material-refill
description: Use when running material stage to generate charts, images, videos, and refill assets into the editor-confirmed final documents.
---

# Dasheng Stage: Material Refill

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`

## 阶段目标

把终稿锚点补齐为真实素材：

- 数据图表（CSV + PNG）
- 图片（检索/生图/信息图）
- 视频素材（下载与筛选）
- 回填说明与清单

## 推荐命令

```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/material_execute_pack.py --draft-manifest "<draft_manifest.json>" --steps charts,image_search,video_search,ai_prep
```

并行执行时可使用：

```bash
python3 scripts/material_parallel_launcher.py --draft-manifest "<draft_manifest.json>"
```

## 交付要求

- `05_MaterialPack.md`
- `05_Material_报告.md`
- `material_manifest.json`
- 每题独立素材目录（编辑友好单层结构）

## 强约束

1. 仅基于编辑确认终稿补素材，不回填旧 draft。
2. 表格/图表必须有数据来源或可复现 CSV。
3. 无显著差异的数据，不强制画图。
