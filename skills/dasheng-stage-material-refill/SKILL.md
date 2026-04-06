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
python3 scripts/material_execute_pack.py --pack-root "<topic_pack_root>" --steps charts,image_search,video_search,ai_prep
```

并行执行时可使用：

```bash
python3 scripts/material_parallel_launcher.py --pack-root "<pack_root>"
```

## 素材文件结构（2026-04-06 优化）

**扁平化单层目录结构**，所有素材直接存放在 topic 根目录：

```
产物/04_Material/{run_id}/
├── topic-{slug}/
│   ├── 图表_{描述性标题}.csv
│   ├── 图表_{描述性标题}.png
│   ├── 图片_{实体名称}.jpg
│   ├── 视频_{内容描述}.mp4
│   └── material_manifest.json
```

**命名规则**：
- 图表：`图表_{描述性标题}.csv` / `图表_{描述性标题}.png`
- 图片：`图片_{实体名称}.jpg`（基于实体名称，≤30字符）
- 视频：`视频_{内容描述}.mp4`（基于查询词，≤30字符）

**优势**：
- ✅ 单层目录，所有素材在同一文件夹
- ✅ 中文前缀标识类型（图表_、图片_、视频_）
- ✅ 描述性文件名，无需打开即可确认内容
- ✅ 便于编辑人员快速查找和使用

**视频自动下载**：
- 默认每个查询自动下载前 3 个合格视频
- 无需手动指定 `--video-download-limit` 参数

## 交付要求

- `05_MaterialPack.md`
- `05_Material_报告.md`
- `material_manifest.json`
- 每题独立素材目录（扁平化单层结构，中文前缀命名）

## 强约束

1. 仅基于编辑确认终稿补素材，不回填旧 draft。
2. 表格/图表必须有数据来源或可复现 CSV。
3. 无显著差异的数据，不强制画图。

