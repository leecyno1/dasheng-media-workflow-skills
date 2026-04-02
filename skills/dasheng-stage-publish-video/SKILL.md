---
name: dasheng-stage-publish-video
description: Use when entering publish stage and needing the mandatory pre-publish video supplement, including interactive chart videos and motion narrative videos.
---

# Dasheng Stage: Publish + Video Supplement

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`
- `FINANCE_MOTION_WORKSPACE=${FINANCE_MOTION_WORKSPACE:-/Volumes/PSSD/Projects/finance-motion-8787}`

## 阶段目标

发布前先补两类视频，再做渠道分发：

1. 互动图表视频（CSV -> finance-motion-8787 -> webm/mp4）
2. motion 叙事视频（改写稿框架精华 + 关键数据 -> 动画场景 -> webm/mp4）

## 一键执行

```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/publish_video_supplement.py
```

## 线程对接

- `codex://threads/019d31c5-bb7f-7a40-a087-9d219e9bd6ab`

## 交付要求

- `publish_video_supplement_report.md`
- `publish_video_supplement_manifest.json`
- 每题目录：
  - `videos/interactive_charts/*.webm|*.mp4`
  - `videos/motion_narrative/*.webm|*.mp4`

## 强约束

1. 视频补充未完成，不进入正式 publish 包。
2. 保证每题独立产物，不混题。
3. 失败必须写入 manifest（命令、错误、返回码）。

