---
name: dasheng-stage-rewrite
description: Use when generating the 4-variant rewrite set per topic with hard word-count validation and final-structure inheritance.
---

# Dasheng Stage: Rewrite

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`

## 阶段目标

每题生成 4 版改写，并继承终稿框架：

- wechat + luxun + hot
- wechat + lemon + normal
- xhs_video + luxun + hot
- xhs_video + lemon + normal

## 推荐命令

```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/rewrite_rerun_with_final_structure.py
node scripts/feishu_rewrite_push.js "$(date +%F)"
```

## 字数硬阈值

- 公众号两版：`>=4000`（且不应无故超过 `8000`）
- 小红书视频两版：`>=1800`

## 强约束

1. 公众号改写必须继承终稿一级结构，不得强制改成固定三段论。
2. 不同题目必须独立目录、独立 bundle、独立 meta。
3. 字数未达标不得推送飞书。

## 交付要求

- `<topic>__rewrite_bundle.md`
- `meta.json`
- `rewrite_manifest.json`

